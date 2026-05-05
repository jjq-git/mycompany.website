"""菜单项工具.

菜单项数据结构:
    {label: 显示名, type: 类型, target: 目标 (按 type 不同), url: 外链}

type 取值:
    home  - 首页, 无 target, URL = /
    list  - 数据集列表页, target = 数据集名, URL = /<target>
    link  - 外链或自定义 URL, url = 完整 URL
    page  - (预留) 单页, target = 页面 key
"""

DATASET_LABELS = {
    'products': '产品',
    'features': '功能',
    'posts': '博客',
    'cases': '案例',
}


def url_of(item):
    """从菜单项计算最终 URL."""
    t = item.get('type')
    if t == 'home':
        return '/'
    if t == 'list':
        return f'/{item.get("target", "")}'
    if t == 'link':
        return item.get('url', '#')
    if t == 'page':
        target = item.get('target', '')
        return '/' if target == 'home' else f'/{target}'
    # 兜底: 旧格式 (只有 url 字段)
    return item.get('url', '#')


def normalize_for_render(items):
    """给每个菜单项加上 url 字段, 模板渲染用. 返回新 list, 不改原数据."""
    result = []
    for it in items or []:
        new = dict(it)
        new['url'] = url_of(it)
        result.append(new)
    return result


def upgrade_old_format(items, datasets):
    """把旧菜单 [{label, url}] 升级到新格式. 返回新 list.

    规则:
      url == '/'          → home
      url 是 http(s)://    → link
      url == /<dataset>    → list, target=dataset
      其他                 → link, url 保留
    """
    upgraded = []
    for it in items or []:
        if 'type' in it:
            upgraded.append(it)  # 已是新格式
            continue
        url = (it.get('url') or '').strip()
        label = it.get('label', '')
        if url == '/' or url == '':
            upgraded.append({'label': label, 'type': 'home'})
        elif url.startswith('http://') or url.startswith('https://'):
            upgraded.append({'label': label, 'type': 'link', 'url': url})
        else:
            ds_name = url.lstrip('/').split('/')[0]
            if ds_name in (datasets or []):
                upgraded.append({'label': label, 'type': 'list', 'target': ds_name})
            else:
                upgraded.append({'label': label, 'type': 'link', 'url': url})
    return upgraded
