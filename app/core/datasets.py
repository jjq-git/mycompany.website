"""数据集 (products/features/posts) 通用 CRUD 工具.

约定: 每个数据集是 sites/<id>/data/<name>.yaml, 内容是 list[dict],
每条带一个唯一 id (int).

分语言: 指定 lang 参数时，读写 lang/<lang>/data/<name>.yaml，
不指定时读写根 data/<name>.yaml（默认语言）。

写入约束: 同一 site/dataset/lang 的读改写事务使用进程内锁和系统文件锁串行化，
避免多标签页、重复提交或多 WSGI 进程同时创建时重复 ID/丢记录。编辑器另提交内容版本，
update 会在锁内做乐观冲突检查，旧页面不能静默覆盖较新内容。
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import threading
import time

from flask import current_app

from .site_storage import read_yaml, write_yaml


class DatasetConflictError(RuntimeError):
    """The submitted item version is older than the current stored item."""


_THREAD_LOCKS = {}
_THREAD_LOCKS_GUARD = threading.Lock()


def item_version(item):
    """Return a stable opaque version token for optimistic edit checks."""
    payload = json.dumps(item or {}, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _lock_name(dataset, lang=None):
    raw = f'{lang or "root"}-{dataset}'
    return re.sub(r'[^a-zA-Z0-9_.-]+', '-', raw).strip('-') or 'dataset'


@contextmanager
def _dataset_write_lock(site_id, dataset, lang=None, timeout=15):
    """Serialize a complete read-modify-write transaction across threads/processes."""
    key = (str(site_id), str(dataset), str(lang or ''))
    with _THREAD_LOCKS_GUARD:
        thread_lock = _THREAD_LOCKS.setdefault(key, threading.RLock())
    with thread_lock:
        lock_dir = Path(current_app.config['SITES_DIR']) / str(int(site_id)) / '.locks'
        lock_dir.mkdir(parents=True, exist_ok=True)
        lock_path = lock_dir / f'{_lock_name(dataset, lang)}.lock'
        handle = lock_path.open('a+b')
        acquired = False
        try:
            if os.name == 'nt':
                import msvcrt
                if lock_path.stat().st_size == 0:
                    handle.write(b'0')
                    handle.flush()
                deadline = time.monotonic() + timeout
                while not acquired:
                    try:
                        handle.seek(0)
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                        acquired = True
                    except OSError:
                        if time.monotonic() >= deadline:
                            raise TimeoutError(f'数据集写入繁忙: {dataset}')
                        time.sleep(0.05)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                acquired = True
            yield
        finally:
            if acquired:
                if os.name == 'nt':
                    import msvcrt
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()


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


def _save_unlocked(site_id, dataset, items, lang=None):
    write_yaml(site_id, f'data/{dataset}.yaml', items, lang=lang)


def save(site_id, dataset, items, lang=None):
    """Replace a dataset under the same cross-process lock used by CRUD helpers."""
    with _dataset_write_lock(site_id, dataset, lang=lang):
        _save_unlocked(site_id, dataset, items, lang=lang)


def find(site_id, dataset, item_id, lang=None):
    """按 id 查找一条, 不存在返回 None."""
    return next((it for it in load(site_id, dataset, lang=lang) if it.get('id') == item_id), None)


def add(site_id, dataset, defaults=None, lang=None):
    """追加一条新记录, 返回新 id."""
    with _dataset_write_lock(site_id, dataset, lang=lang):
        items = load(site_id, dataset, lang=lang)
        new_id = max((it.get('id', 0) for it in items), default=0) + 1
        new_item = {'id': new_id, **(defaults or {})}
        items.append(new_item)
        _save_unlocked(site_id, dataset, items, lang=lang)
        return new_id


def update(site_id, dataset, item_id, fields, lang=None, remove_fields=None, expected_version=None):
    """合并字段到指定 id 的记录，并可明确删除不再覆盖的字段."""
    with _dataset_write_lock(site_id, dataset, lang=lang):
        items = load(site_id, dataset, lang=lang)
        for it in items:
            if it.get('id') == item_id:
                if expected_version and item_version(it) != expected_version:
                    raise DatasetConflictError('内容已被其他页面修改，请刷新后重新编辑')
                it.update(fields)
                for key in remove_fields or ():
                    it.pop(key, None)
                _save_unlocked(site_id, dataset, items, lang=lang)
                return it
        return None


def remove(site_id, dataset, item_id, lang=None):
    """删除指定 id 的记录."""
    with _dataset_write_lock(site_id, dataset, lang=lang):
        items = load(site_id, dataset, lang=lang)
        filtered = [it for it in items if it.get('id') != item_id]
        if len(filtered) == len(items):
            return False
        _save_unlocked(site_id, dataset, filtered, lang=lang)
        return True


def paste_from(site_id, dataset, target_id, source_id, lang=None):
    """Copy one item over another under one locked transaction."""
    with _dataset_write_lock(site_id, dataset, lang=lang):
        items = load(site_id, dataset, lang=lang)
        source = next((it for it in items if it.get('id') == source_id), None)
        target = next((it for it in items if it.get('id') == target_id), None)
        if not source or not target:
            return None
        import copy
        replacement = copy.deepcopy(source)
        replacement['id'] = target.get('id')
        replacement['slug'] = target.get('slug')
        for index, item in enumerate(items):
            if item.get('id') == target_id:
                items[index] = replacement
                break
        _save_unlocked(site_id, dataset, items, lang=lang)
        return replacement


def replace_template_references(site_id, dataset, old_template_id, new_template_id, lang=None):
    """Move all item references from a deleted detail template to its fallback."""
    with _dataset_write_lock(site_id, dataset, lang=lang):
        items = load(site_id, dataset, lang=lang)
        changed = 0
        for item in items:
            if str(item.get('template_id') or '') == str(old_template_id):
                item['template_id'] = str(new_template_id)
                changed += 1
        if changed:
            _save_unlocked(site_id, dataset, items, lang=lang)
        return changed
