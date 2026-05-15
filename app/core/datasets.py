"""数据集 (products/features/posts) 通用 CRUD 工具.

约定: 每个数据集是 sites/<id>/data/<name>.yaml, 内容是 list[dict],
每条带一个唯一 id (int).

分语言: 指定 lang 参数时，读写 lang/<lang>/data/<name>.yaml，
不指定时读写根 data/<name>.yaml（默认语言）。
"""
from .site_storage import read_yaml, write_yaml


def load(site_id, dataset, lang=None):
    """读取整个数据集列表.

    自动标准化格式:
    - 如果顶层是 {items: [...], ...} dict, 提取 items 列表
    - 给没有 id 的条目自动分配 id (种子数据兼容)
    """
    raw = read_yaml(site_id, f'data/{dataset}.yaml', lang=lang) or []
    if isinstance(raw, dict) and 'items' in raw:
        items = raw['items']
    elif isinstance(raw, list):
        items = raw
    else:
        return []

    for i, it in enumerate(items):
        if 'id' not in it:
            it['id'] = i + 1
        else:
            it['id'] = int(it['id'])
    return items


def save(site_id, dataset, items, lang=None):
    write_yaml(site_id, f'data/{dataset}.yaml', items, lang=lang)


def find(site_id, dataset, item_id, lang=None):
    """按 id 查找一条, 不存在返回 None."""
    return next((it for it in load(site_id, dataset, lang=lang) if it.get('id') == item_id), None)


def add(site_id, dataset, defaults=None, lang=None):
    """追加一条新记录, 返回新 id."""
    items = load(site_id, dataset, lang=lang)
    new_id = max((it.get('id', 0) for it in items), default=0) + 1
    new_item = {'id': new_id, **(defaults or {})}
    items.append(new_item)
    save(site_id, dataset, items, lang=lang)
    return new_id


def update(site_id, dataset, item_id, fields, lang=None):
    """合并字段到指定 id 的记录."""
    items = load(site_id, dataset, lang=lang)
    for it in items:
        if it.get('id') == item_id:
            it.update(fields)
            save(site_id, dataset, items, lang=lang)
            return it
    return None


def remove(site_id, dataset, item_id, lang=None):
    """删除指定 id 的记录."""
    items = [it for it in load(site_id, dataset, lang=lang) if it.get('id') != item_id]
    save(site_id, dataset, items, lang=lang)
