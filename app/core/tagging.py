"""Automatic filter tags derived from structured content fields."""

import copy
import re


_TAG_PREFIX_RULES = (
    ('chip', ('灯珠封装', '封装型号', '芯片型号', 'chip', 'package')),
    ('color', ('白光灯珠', '非白光灯珠', '色温', '颜色', '灯光颜色', 'color temperature', 'colour temperature', 'color', 'colour')),
    ('pitch', ('灯珠数', '灯珠数量', '每米灯珠', '每米数量', '密度', 'pitch', 'led count', 'led density')),
    ('voltage', ('输入电压', '额定电压', '工作电压', '电压', 'voltage')),
    ('width', ('灯条宽度', '板宽', '宽度', 'width')),
)


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
    if prefix == 'width':
        match = re.search(r'\d+(?:\.\d+)?', text)
        return match.group(0) if match else re.sub(r'\s+', '', text).lower()
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
    for prefix in ('chip', 'color', 'pitch', 'voltage', 'width'):
        result.extend(grouped[prefix])
    return result[:limit]


def with_generated_tags(data):
    """Return render data with automatic tags applied without changing stored YAML."""
    enriched = copy.deepcopy(data)

    def walk(value):
        if isinstance(value, dict):
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
