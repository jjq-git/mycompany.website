"""数据集 (products/features/posts) 通用 CRUD 工具.

约定: 每个数据集是 sites/<id>/data/<name>.yaml, 内容是 list[dict],
每条带一个唯一 id (int).
"""
from .site_storage import read_yaml, write_yaml


def load(site_id, dataset):
    """读取整个数据集列表."""
    return read_yaml(site_id, f'data/{dataset}.yaml') or []


def save(site_id, dataset, items):
    write_yaml(site_id, f'data/{dataset}.yaml', items)


def find(site_id, dataset, item_id):
    """按 id 查找一条, 不存在返回 None."""
    return next((it for it in load(site_id, dataset) if it.get('id') == item_id), None)


def add(site_id, dataset, defaults=None):
    """追加一条新记录, 返回新 id."""
    items = load(site_id, dataset)
    new_id = max((it.get('id', 0) for it in items), default=0) + 1
    new_item = {'id': new_id, **(defaults or {})}
    items.append(new_item)
    save(site_id, dataset, items)
    return new_id


def update(site_id, dataset, item_id, fields):
    """合并字段到指定 id 的记录."""
    items = load(site_id, dataset)
    for it in items:
        if it.get('id') == item_id:
            it.update(fields)
            save(site_id, dataset, items)
            return it
    return None


def remove(site_id, dataset, item_id):
    """删除指定 id 的记录."""
    items = [it for it in load(site_id, dataset) if it.get('id') != item_id]
    save(site_id, dataset, items)
