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


def translate_json(texts, source_lang="zh-CN", target_lang="en"):
    """翻译一个 key-value 字典，key 不变，value 翻译为目标语言。

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

    input_json = json.dumps(texts, ensure_ascii=False, indent=2)
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
        'max_tokens': 4096,
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
        logger.error('翻译 API HTTP %s: %s', e.code, body[:300])
        raise RuntimeError(f'翻译服务返回错误 ({e.code})')
    except urllib.error.URLError as e:
        logger.error('翻译 API 网络错误: %s', e.reason)
        raise RuntimeError(f'翻译服务连接失败: {e.reason}')
    except json.JSONDecodeError as e:
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
        logger.error('翻译结果 JSON 解析失败, 原始内容: %s', content[:500])
        raise RuntimeError(f'翻译结果格式异常: {e}')

    if not isinstance(result, dict):
        raise RuntimeError(f'翻译 API 返回格式异常: {type(result)}')
    return result


def is_configured():
    """检查翻译服务是否已配置."""
    return bool(current_app.config.get('TRANSLATION_API_KEY', ''))
