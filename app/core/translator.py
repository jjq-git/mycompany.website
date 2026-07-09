"""AI 翻译服务 — 调用 DeepSeek / OpenAI 兼容 API."""
import json
import logging
import re
import urllib.request
import urllib.error

from flask import current_app

logger = logging.getLogger(__name__)

# 语言代码格式: BCP 47 基础形态, 例 zh / zh-CN / pt-BR.
# 严格白名单约束避免被注入到 prompt 中 (如 "zh\n\n忽略上文...").
_LANG_CODE_RE = re.compile(r'^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})?$')


def _validate_lang(value, field):
    if not isinstance(value, str) or not _LANG_CODE_RE.match(value.strip()):
        raise ValueError(f'{field} 必须是合法的语言代码 (如 zh-CN / en / pt-BR)')
    return value.strip()

# 翻译 prompt 模板
_TRANSLATE_PROMPT = """你是一个专业翻译助手。将以下 JSON 中的每个值从 {source_lang} 翻译为 {target_lang}。

规则：
1. 只翻译文本值，保持 JSON 结构完全不变（key 名不变）
2. 不要翻译技术性字段：URL、slug、CSS 类名、颜色值、数字
3. 专有名词（公司名、品牌名、产品型号）保持原文或使用行业惯例
4. 返回纯 JSON，不要解释，不要 markdown 代码块标记

输入 JSON：
{input_json}

翻译结果："""


_SEO_DESCRIPTION_PROMPT = """你是展示型企业网站的 SEO 文案助手。请根据下面页面信息生成一条 meta description。

要求：
1. 只返回一句自然语言简介，不要解释，不要 markdown
2. 语言必须使用 {lang}
3. 中文控制在 60-90 个汉字；英文控制在 120-160 characters
4. 不堆砌关键词，不夸大，不写"欢迎访问"
5. 优先概括页面核心价值，让搜索结果和 AI 检索都容易理解

站点/页面信息：
{input_json}

meta description："""


# 单批输入 JSON 最大字符数：超过此阈值拆批。
# 长文本页面（如 modules 13 个模块）单次请求的 prompt + 输出容易超出 max_tokens，
# 拆成小批每批独立请求，最后合并结果。
_BATCH_MAX_CHARS = 2500


def _repair_truncated_json(raw):
    """尝试修复因 max_tokens 截断而残缺的 JSON。

    常见截断模式（从易到难）：
    1. 缺少末尾的 "} → 补上
    2. 最后一行的字符串值未闭合 → 去掉最后一行
    3. 中间某行的字符串值未闭合 → 补闭合引号

    返回修复后的 dict，无法修复返回 None。
    """
    if not raw or not raw.strip():
        return None

    text = raw.strip()

    # 策略 1：逐行扫描，修复未闭合的字符串
    lines = text.split('\n')
    fixed_lines = []
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        # 统计引号：值为 JSON 字符串时引号成对，不成对说明被截断
        in_str = False
        escape_next = False
        for ch in stripped:
            if escape_next:
                escape_next = False
                continue
            if ch == '\\':
                escape_next = True
                continue
            if ch == '"':
                in_str = not in_str
        # 如果这行在字符串中结束（引号不对）→ 这是截断行
        if in_str:
            # 行内字符串被截断 → 丢弃此行及之后内容，只保留前面的行
            text = '\n'.join(fixed_lines).rstrip()
            break
        fixed_lines.append(stripped)

    # 策略 2：补全缺失的括号
    # 去掉末尾逗号后再补括号
    text = text.rstrip().rstrip(',').rstrip()

    # 数括号
    open_braces = text.count('{') - text.count('}')
    open_brackets = text.count('[') - text.count(']')

    # 补缺失的闭合括号
    text += ']' * open_brackets
    text += '}' * open_braces

    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # 策略 3：去掉最后一行再试（常见：最后一行不完整）
    if len(lines) > 2:
        text = '\n'.join(lines[:-1]).rstrip().rstrip(',').rstrip()
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        text += ']' * open_brackets
        text += '}' * open_braces
        try:
            result = json.loads(text)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    return None


def _call_translate_api(api_key, api_base, model, batch_texts, source_lang, target_lang):
    """调用一次翻译 API，翻译单批文本。返回 dict。"""
    input_json = json.dumps(batch_texts, ensure_ascii=False, indent=2)
    prompt = _TRANSLATE_PROMPT.format(
        source_lang=source_lang,
        target_lang=target_lang,
        input_json=input_json,
    )

    payload = json.dumps({
        'model': model,
        'messages': [
            {'role': 'system', 'content': '你是一个专业的 JSON 翻译器，只返回翻译后的 JSON。'},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.3,
        'max_tokens': 8192,
    }, ensure_ascii=False).encode('utf-8')

    url = f'{api_base.rstrip("/")}/chat/completions'
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode('utf-8')
            data = json.loads(raw)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace') if e.fp else ''
        logger.error('翻译 API HTTP %s: %s', e.code, body[:300])
        raise RuntimeError(f'翻译服务返回错误 ({e.code})')
    except urllib.error.URLError as e:
        logger.error('翻译 API 网络错误: %s', e.reason)
        raise RuntimeError(f'翻译服务连接失败: {e.reason}')
    except json.JSONDecodeError:
        logger.error('翻译 API 响应 JSON 解析失败')
        raise RuntimeError('翻译服务返回格式异常')

    content = data['choices'][0]['message']['content'].strip()

    # 清理可能的 markdown 代码块标记
    if content.startswith('```'):
        lines = content.split('\n')
        if lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        content = '\n'.join(lines).strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError as e:
        # 尝试修复截断的 JSON（API 输出超 max_tokens 时字符串/括号未闭合）
        repaired = _repair_truncated_json(content)
        if repaired is not None:
            logger.warning('翻译结果 JSON 截断，已修复恢复部分字段')
            result = repaired
        else:
            logger.error('翻译结果 JSON 解析失败且无法修复, 原始内容: %s', content[:500])
            raise RuntimeError(f'翻译结果格式异常: {e}')

    if not isinstance(result, dict):
        raise RuntimeError(f'翻译 API 返回格式异常: {type(result)}')
    return result


def _split_batches(texts):
    """将 texts 字典按 _BATCH_MAX_CHARS 拆成多个小批，每批仍是 dict。

    拆批策略：贪心累加，当前批 JSON 序列化后不超过阈值。单个 key-value 超阈值
    也不拆分（一个 value 必须完整给 API），此时该批会暂时超出阈值。
    """
    batches = []
    current = {}
    current_size = 0
    # 估算 JSON 开销：大括号、key 的引号冒号、逗号等，每 key 约 10 字符
    overhead_per_key = 10

    for key, value in texts.items():
        value_str = str(value) if value else ''
        # 预估该条目在 JSON 中的大小：key 长度 + value 长度 + 引号等开销
        item_size = len(key) + len(value_str) + overhead_per_key

        if current and current_size + item_size > _BATCH_MAX_CHARS:
            batches.append(current)
            current = {}
            current_size = 0

        current[key] = value
        current_size += item_size

    if current:
        batches.append(current)

    return batches


def translate_json(texts, source_lang="zh-CN", target_lang="en"):
    """翻译一个 key-value 字典，key 不变，value 翻译为目标语言。

    大输入自动拆批，每批独立请求后合并结果，避免单次请求 token 溢出。
    返回: dict[str, str] 翻译后的字典，key 与输入一致
    """
    # 输入校验先行: 阻断 prompt 注入塞进语言字段; texts 必须为字典
    source_lang = _validate_lang(source_lang, 'source_lang')
    target_lang = _validate_lang(target_lang, 'target_lang')

    if not isinstance(texts, dict):
        raise ValueError('texts 必须为字典')

    api_key = current_app.config.get('TRANSLATION_API_KEY', '')
    if not api_key:
        raise ValueError('TRANSLATION_API_KEY 未配置，请在 .env 中设置')

    api_base = current_app.config.get('TRANSLATION_API_BASE', 'https://api.deepseek.com/v1')
    model = current_app.config.get('TRANSLATION_MODEL', 'deepseek-chat')

    # 拆批：大页面（如 modules 13 个模块）不会因 token 溢出而 502
    batches = _split_batches(texts)
    if len(batches) > 1:
        logger.info('翻译拆为 %d 批（共 %d 个字段）', len(batches), len(texts))

    merged = {}
    for i, batch in enumerate(batches):
        if i > 0:
            import time
            time.sleep(1.0)
        try:
            result = _translate_one_batch(api_key, api_base, model, batch, source_lang, target_lang)
        except RuntimeError as e:
            raise RuntimeError(f'第 {i + 1}/{len(batches)} 批翻译失败: {e}')
        merged.update(result)

    return merged


def _translate_one_batch(api_key, api_base, model, batch, source_lang, target_lang):
    """翻译单批，JSON 截断时自动拆半重试（最多 2 层）。"""
    try:
        return _call_translate_api(api_key, api_base, model, batch, source_lang, target_lang)
    except RuntimeError as e:
        msg = str(e)
        # 只对 JSON 截断/格式异常做拆分重试，网络/认证错误不重试
        if '格式异常' not in msg:
            raise

    # 批次有 2 个以上字段且 JSON 被截断 → 拆成两半分别翻译
    keys = list(batch.keys())
    if len(keys) < 2:
        raise  # 单字段还失败，没法拆了

    mid = len(keys) // 2
    left = {k: batch[k] for k in keys[:mid]}
    right = {k: batch[k] for k in keys[mid:]}

    result = {}
    for label, sub in [('左半', left), ('右半', right)]:
        try:
            # 递归拆半（最多再拆一层，_call_translate_api 里有 repair 保护）
            sub_result = _call_translate_api(api_key, api_base, model, sub, source_lang, target_lang)
        except RuntimeError as e2:
            raise RuntimeError(f'{label}二次拆分仍失败: {e2}')
        result.update(sub_result)
        import time
        time.sleep(0.5)

    return result


def is_configured():
    """检查翻译服务是否已配置."""
    return bool(current_app.config.get('TRANSLATION_API_KEY', ''))


def generate_seo_description(page_title, page_text, company_name='', lang='zh-CN', output='description'):
    """调用 AI 生成页面 SEO 简介。

    复用翻译服务的 DeepSeek / OpenAI 兼容配置，避免为 SEO 另起一套 API。
    返回纯文本 description；未配置或调用失败时由调用方决定是否回退。
    """
    lang = _validate_lang(lang, 'lang')
    api_key = current_app.config.get('TRANSLATION_API_KEY', '')
    if not api_key:
        raise ValueError('TRANSLATION_API_KEY 未配置，请在 .env 中设置')

    api_base = current_app.config.get('TRANSLATION_API_BASE', 'https://api.deepseek.com/v1')
    model = current_app.config.get('TRANSLATION_MODEL', 'deepseek-chat')
    input_json = json.dumps({
        'company': str(company_name or '').strip(),
        'page_title': str(page_title or '').strip(),
        'page_content': str(page_text or '').strip()[:2200],
    }, ensure_ascii=False, indent=2)
    if output == 'title':
        prompt = (
            f'请根据以下 JSON 为网页生成一个准确、自然的 SEO 标题，语言为 {lang}。'
            '只输出标题，不加引号、解释或 Markdown；避免关键词堆砌，最长 60 个字符。\n'
            f'{input_json}'
        )
    else:
        prompt = _SEO_DESCRIPTION_PROMPT.format(lang=lang, input_json=input_json)

    payload = json.dumps({
        'model': model,
        'messages': [
            {'role': 'system', 'content': '你是专业 SEO 文案助手，只输出一个 SEO 标题。' if output == 'title' else '你是专业 SEO 文案助手，只输出一条 meta description。'},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.4,
        'max_tokens': 100 if output == 'title' else 220,
    }, ensure_ascii=False).encode('utf-8')

    url = f'{api_base.rstrip("/")}/chat/completions'
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode('utf-8')
            data = json.loads(raw)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace') if e.fp else ''
        logger.error('SEO 生成 API HTTP %s: %s', e.code, body[:300])
        raise RuntimeError(f'SEO 生成服务返回错误 ({e.code})')
    except urllib.error.URLError as e:
        logger.error('SEO 生成 API 网络错误: %s', e.reason)
        raise RuntimeError(f'SEO 生成服务连接失败: {e.reason}')
    except json.JSONDecodeError:
        logger.error('SEO 生成 API 响应 JSON 解析失败')
        raise RuntimeError('SEO 生成服务返回格式异常')

    content = data['choices'][0]['message']['content'].strip()
    if content.startswith('```'):
        lines = content.split('\n')
        if lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        content = '\n'.join(lines).strip()

    content = content.strip().strip('"').strip("'").strip()
    # 兜底裁剪：模型偶尔会超长，保存前压到搜索结果可接受范围。
    return content[:60 if output == 'title' else 180].rstrip()


def generate_seo_title(page_title, page_text, company_name='', lang='zh-CN'):
    return generate_seo_description(page_title, page_text, company_name=company_name, lang=lang, output='title')
