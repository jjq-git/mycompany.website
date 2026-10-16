"""Automatic filter tags derived from structured content fields."""

import copy
import re


# 别名匹配用 substring + lower()，需同时覆盖简体/繁体/英文，否则多语言站点（en/zh-TW）
# 的规格字段名匹配不到，导致同一产品各语言版本标签维度残缺、不一致（曾出过 zh-TW 只剩 height 的 bug）。
# 英文别名统一小写；含空格的短语（led board width）也用 substring 命中。
_TAG_PREFIX_RULES = (
    ('chip', ('灯珠封装', '封装型号', '芯片型号', '燈珠封裝', '封裝型號', '晶片型號', 'chip', 'package')),
    ('color', ('白光灯珠', '非白光灯珠', '色温', '颜色', '灯光颜色', '白光燈珠', '色溫', '顏色', '燈光顏色', 'color temperature', 'colour temperature', 'color', 'colour')),
    ('pitch', ('灯珠数', '灯珠数量', '每米灯珠', '每米数量', '密度', '燈珠數', '燈珠數量', '每米燈珠', '每米數量', '密度', 'pitch', 'led count', 'led density')),
    ('voltage', ('输入电压', '额定电压', '工作电压', '电压', '輸入電壓', '額定電壓', '工作電壓', '電壓', 'voltage')),
    # width/height/lswidth 走区间分桶（见 _BUCKET_PREFIXES）：几十种精确值会让筛选栏爆炸，
    # 归入 4 个区间桶（<10 / 10-20 / 20-30 / ≥30）才是可用的筛选维度。
    # 顺序上 lswidth（灯板宽度）必须排在 width 前面，否则含“宽度/width”的它会被 width 规则先命中。
    # 英文 'stripwidth'、繁体 '燈板寬度' 都要在 width 之前拦下。
    ('lswidth', ('灯板宽度', '灯板宽', '燈板寬度', '燈板寬', 'lswidth', 'stripwidth', 'strip width', 'led board width', 'board width')),
    ('width', ('灯条宽度', '板宽', '宽度', '燈條寬度', '闆寬', '寬度', 'width')),
    ('height', ('高度', '高', '高度', '高', 'height')),
)

# 需要按数值区间分桶的前缀：桶边界为 10 / 20 / 30，与最初批量导入脚本口径一致。
_BUCKET_PREFIXES = ('width', 'height', 'lswidth')


def _iter_structured_specs(fields):
    """Yield ``(name, value)`` pairs from all supported structured spec fields."""
    detail_specs = fields.get('detail_specs')
    if isinstance(detail_specs, list):
        for group in detail_specs:
            if not isinstance(group, dict):
                continue
            items = group.get('items') or group.get('rows') or []
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        yield item.get('name') or item.get('label') or '', item.get('value') or ''

    for field_name in ('specs', 'parameters', 'attributes'):
        items = fields.get(field_name)
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                yield item.get('name') or item.get('label') or item.get('key') or '', item.get('value') or ''


def _prefix_for_name(name):
    normalized = str(name or '').strip().lower()
    for prefix, aliases in _TAG_PREFIX_RULES:
        if any(alias in normalized for alias in aliases):
            return prefix
    return None


def _split_values(value):
    if isinstance(value, (list, tuple)):
        parts = value
    else:
        parts = re.split(r'[,，;；|\n\r]+', str(value or ''))
    return [str(part).strip() for part in parts if str(part).strip()]


def _normalize_tag_value(prefix, value):
    text = str(value or '').strip()
    if not text:
        return ''
    if prefix == 'voltage':
        match = re.search(r'\d+(?:\.\d+)?\s*[vV]', text)
        return re.sub(r'\s+', '', match.group(0)).lower() if match else re.sub(r'\s+', '', text).lower()
    if prefix == 'pitch':
        match = re.search(r'\d+(?:\.\d+)?', text)
        return match.group(0) if match else re.sub(r'\s+', '', text).lower()
    if prefix in _BUCKET_PREFIXES:
        # 尺寸类归入区间桶：<10 → '10'，10-20 → '1020'，20-30 → '2030'，≥30 → '30'。
        # 桶命名沿用最初脚本（width-1020 等），保证新旧标签一致、筛选栏干净。
        match = re.search(r'\d+(?:\.\d+)?', text)
        if not match:
            return re.sub(r'\s+', '', text).lower()
        num = float(match.group(0))
        if num < 10:
            return '10'
        if num < 20:
            return '1020'
        if num < 30:
            return '2030'
        return '30'
    if prefix == 'color':
        kelvin = re.fullmatch(r'(\d+(?:\.\d+)?)\s*[kK]', text)
        if kelvin:
            return f'{kelvin.group(1)}K'
        return re.sub(r'\s+', '-', text).lower()
    return re.sub(r'\s+', '', text)


def generated_technical_tags(fields, limit=24):
    """Generate stable filter tags from recognized structured specifications."""
    grouped = {prefix: [] for prefix, _aliases in _TAG_PREFIX_RULES}
    seen = set()
    for name, raw_value in _iter_structured_specs(fields or {}):
        prefix = _prefix_for_name(name)
        if not prefix:
            continue
        for value in _split_values(raw_value):
            normalized = _normalize_tag_value(prefix, value)
            if not normalized:
                continue
            tag = f'{prefix}-{normalized}'
            key = tag.lower()
            if key in seen:
                continue
            seen.add(key)
            grouped[prefix].append(tag)

    result = []
    # 输出顺序决定筛选栏里标签的排列；尺寸类放最后。
    for prefix in ('chip', 'color', 'pitch', 'voltage', 'width', 'height', 'lswidth'):
        result.extend(grouped[prefix])
    return result[:limit]


def _should_autofill_tags(item):
    """判断渲染时是否用自动标签覆盖该条目的 tags。

    只有“明确归自动管理”或“完全没有标签”的条目才自动生成，其余一律保留已存标签。
    这样才不会把各品类脚本精心生成的多维标签（如 led-strip 的 color/pitch、holograms
    的 bt/remote）在渲染时冲成自动逻辑的误判值，也尊重用户的手改（tags_auto=False）。
    """
    tags_auto = item.get('tags_auto')
    # 手改锁定：用户接管过，永不覆盖
    if tags_auto is False or str(tags_auto).lower() == 'false':
        return False
    # 明确归自动管理（如重算过的铝型材）：刷新
    if tags_auto is True or str(tags_auto).lower() == 'true':
        return True
    existing = item.get('tags')
    # 无 tags_auto 标记时：已有非空标签视为“别处生成/手填”，保留；空则可自动补
    if isinstance(existing, (list, tuple)) and len(existing) > 0:
        return False
    return True


def with_generated_tags(data):
    """Return render data with automatic tags applied without changing stored YAML."""
    enriched = copy.deepcopy(data)

    def walk(value):
        if isinstance(value, dict):
            if _should_autofill_tags(value):
                generated = generated_technical_tags(value)
                if generated:
                    value['tags'] = generated
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(enriched)
    return enriched
