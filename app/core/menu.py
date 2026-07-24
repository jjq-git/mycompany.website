"""菜单项工具.

菜单项数据结构:
    {label: 显示名, type: 类型, target: 目标 (按 type 不同), url: 外链,
     children: [子菜单项...], dropdown_style: 下拉样式}

type 取值:
    home  - 首页, 无 target, URL = /
    list  - 数据集列表页, target = 数据集名, URL = /<target>
    link  - 外链或自定义 URL, url = 完整 URL
    page  - 单页, target = 页面 key
"""

import re

DATASET_LABELS = {
    'products': '产品',
    'features': '功能',
    'posts': '博客',
    'cases': '案例',
}

# 数据集详情页自动推导规则: dataset_name → (detail_template, var_name, slug_field)
# 未在此表中的自动按规则推导: 去尾 s + _detail.html
DATASET_DETAIL_MAP = {
    'products': ('product_detail.html', 'product', 'slug'),
    'cases': ('case_detail.html', 'case', 'slug'),
    'features': ('feature_detail.html', 'feature', 'slug'),
}

VALID_TYPES = {'home', 'list', 'page', 'link', 'group'}
VALID_MENU_ICONS = {
    'alert-circle', 'alert-triangle', 'arrow-down', 'arrow-left', 'arrow-right',
    'arrow-up', 'audio', 'award', 'bar-chart', 'bluetooth', 'bookmark',
    'briefcase', 'calendar', 'camera', 'clock', 'cpu', 'external-link',
    'file-text', 'folder', 'globe', 'grid', 'heart', 'image', 'info',
    'mail', 'map-pin', 'package', 'phone', 'search', 'settings', 'star',
    'user', 'users',
}

# 菜单嵌套深度上限. 超出部分的 children 会被裁掉.
# 防御恶意 settings.yaml 通过深嵌套触发 Python 递归栈溢出 / 渲染期 OOM.
MAX_MENU_DEPTH = 8


def cap_menu_depth(items, depth=0, max_depth=MAX_MENU_DEPTH):
    """递归裁剪菜单深度: 超过 max_depth 的子树直接 children=[].
    返回新列表, 不修改原数据."""
    if not isinstance(items, list):
        return []
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        new_it = dict(it)
        if depth + 1 >= max_depth:
            new_it['children'] = []
        else:
            new_it['children'] = cap_menu_depth(it.get('children') or [], depth + 1, max_depth)
        out.append(new_it)
    return out


def url_of(item, parent_path=''):
    """从菜单项计算最终 URL.

    parent_path: 父级路径前缀, 用于生成层级 URL.
                 group 类型自身无页面, 但其 target 会参与子级路径构建.
    """
    t = item.get('type')
    if t == 'home':
        return '/'
    if t == 'list':
        target = item.get('target', '')
        if not target:
            return '/'
        path = f'{parent_path}/{target}' if parent_path else target
        return f'/{path}'
    if t == 'link':
        return item.get('url', '#')
    if t == 'page':
        target = item.get('target', '')
        if target == 'home' or not target:
            return '/'
        path = f'{parent_path}/{target}' if parent_path else target
        return f'/{path}'
    if t == 'group':
        return ''  # 容器无独立页面
    # 兜底: 旧格式 (只有 url 字段)
    return item.get('url', '#')


def normalize_for_render(items, parent_path=''):
    """给每个菜单项加上 url 字段, 递归处理 children. 返回新 list, 不改原数据.

    parent_path: 父级路径前缀.
                 group 类型自身无页面, 但其 target 会参与子级路径构建.
    """
    result = []
    for it in items or []:
        if not isinstance(it, dict):  # #14: 同 upgrade_old_format, 防脏项
            continue
        new = dict(it)
        new['url'] = url_of(it, parent_path)

        # 计算子菜单的父路径: group/page/list 贡献其 target
        child_parent = parent_path
        t = it.get('type')
        target = it.get('target', '')
        if t in ('page', 'list', 'group') and target:
            child_parent = f'{parent_path}/{target}' if parent_path else target

        if it.get('children'):
            new['children'] = normalize_for_render(it['children'], child_parent)
        else:
            new['children'] = []
        result.append(new)
    return result


def filter_hidden_for_nav(items):
    """返回导航可见菜单树；hidden=True 的项仍可构建页面，但不进入 Header/Footer 导航。"""
    result = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        if it.get('hidden') is True:
            continue
        new = dict(it)
        if it.get('children'):
            new['children'] = filter_hidden_for_nav(it.get('children') or [])
        else:
            new['children'] = []
        result.append(new)
    return result


def collect_list_targets(items, result=None, parent_targets=None):
    """递归收集菜单里所有 list 类型项的 {target, label, path}。

    #22: 此前 routes.py 里以 _collect_list_targets/_collect_targets 内联复制了 3 份
    (逻辑逐字相同, 命名还不一致), 统一抽到这里。

    parent_targets: 上级 group 类型的 target 列表，用于构建完整菜单路径。
    如 产品(group, target=products) > Led灯条(list, target=led-strip)
    → target='led-strip', path='products/led-strip'
    """
    if result is None:
        result = []
    for it in (items or []):
        if not isinstance(it, dict):
            continue
        if it.get('type') == 'list' and it.get('target'):
            # 将父级 group target 与当前 list target 拼接成完整菜单路径
            path_parts = (parent_targets or []) + [it['target']]
            result.append({
                'target': it['target'],
                'label': it.get('label', it['target']),
                'path': '/'.join(path_parts),
            })
        if it.get('children'):
            # 递归进入子级时，若当前项是 group 且有 target，则追加到父路径
            child_parents = list(parent_targets or [])
            if it.get('type') == 'group' and it.get('target'):
                child_parents.append(it['target'])
            collect_list_targets(it['children'], result, child_parents)
    return result


def ensure_home(items):
    """确保首页固定为第一项. 返回新 list, 不改原数据."""
    normalized = [it for it in (items or []) if isinstance(it, dict)]  # #14: 防脏项
    home_items = [it for it in normalized if it.get('type') == 'home']
    other_items = [it for it in normalized if it.get('type') != 'home']
    home = dict(home_items[0]) if home_items else {'label': '首页', 'type': 'home'}
    home['type'] = 'home'
    home['url'] = '/'
    return [home] + other_items


def clean_for_storage(items):
    """清洗后台提交的菜单树, 只保留模板渲染需要的字段."""
    cleaned = []

    def _clean(raw_items, allow_home=False):
        result = []
        for raw in raw_items or []:
            if not isinstance(raw, dict):
                continue
            label = str(raw.get('label') or '').strip()
            item_type = str(raw.get('type') or 'link').strip()
            if item_type not in VALID_TYPES:
                item_type = 'link'
            if item_type == 'home' and not allow_home:
                item_type = 'link'
            if not label:
                label = '首页' if item_type == 'home' else ''
            if not label:
                continue

            item = {'label': label, 'type': item_type}
            item_id = str(raw.get('id') or '').strip()
            if re.fullmatch(r'[a-z0-9]{8,32}', item_id):
                item['id'] = item_id
            icon = str(raw.get('icon') or '').strip().lower()
            if icon in VALID_MENU_ICONS:
                item['icon'] = icon
            if raw.get('hidden') is True:
                item['hidden'] = True
            if item_type in ('list', 'page', 'group'):
                target = str(raw.get('target') or '').strip().strip('/')
                if target:
                    item['target'] = target
            elif item_type == 'link':
                url = str(raw.get('url') or '').strip()
                if url:
                    item['url'] = url

            children = _clean(raw.get('children') or [], allow_home=False)
            if children:
                item['children'] = children

            result.append(item)
        return result

    cleaned = _clean(items, allow_home=True)
    return ensure_home(cleaned)


def find_menu_path(menu_items, target):
    """在菜单树中递归查找 target 的完整层级路径.

    返回路径如 'parent/target'，找不到返回 target 本身。
    """
    def _walk(items, parent_path=''):
        for item in items or []:
            t = item.get('type')
            item_target = item.get('target', '')
            if t in ('page', 'list') and item_target == target:
                return f'{parent_path}/{item_target}' if parent_path else item_target
            if item.get('children'):
                child_parent = parent_path
                if t in ('page', 'list', 'group') and item_target:
                    child_parent = f'{parent_path}/{item_target}' if parent_path else item_target
                result = _walk(item['children'], child_parent)
                if result:
                    return result
        return None
    return _walk(menu_items) or target


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
        # #14: 防御非 dict 菜单项(手工编辑 yaml 或模板作者写错塞进标量/None)。
        # upgrade_old_format 是 menu 渲染链(upgrade→normalize→ensure_home)的第一站,
        # 在此过滤掉非 dict, 后续两步就拿不到脏项, 不会再抛 AttributeError 中断整站构建。
        if not isinstance(it, dict):
            continue
        if 'type' in it:
            # 已是新格式, 递归处理 children
            new_it = dict(it)
            if it.get('children'):
                new_it['children'] = upgrade_old_format(it['children'], datasets)
            upgraded.append(new_it)
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


def derive_detail_info(target, tpl_html_dir):
    """根据数据集名自动推导详情页模板和变量名.

    返回: (detail_template, var_name, slug_field) 或 (None, None, None)
    """
    # 先查显式映射表
    if target in DATASET_DETAIL_MAP:
        tmpl, var, slug = DATASET_DETAIL_MAP[target]
        if (tpl_html_dir / tmpl).exists():
            return tmpl, var, slug

    # 自动推导: 尝试 <target>_detail.html
    detail_tmpl = f'{target}_detail.html'
    if (tpl_html_dir / detail_tmpl).exists():
        # #17: 用 [:-1] 只去末尾一个 s; rstrip('s') 会剥掉所有尾部 s
        # (address→addre, process→proce), 与下方 246 行的 [:-1] 也不一致。
        var_name = target[:-1] if target.endswith('s') else target
        return detail_tmpl, var_name, 'slug'

    # 尝试去尾 s: products → product_detail.html
    if target.endswith('s'):
        singular = target[:-1]
        detail_tmpl = f'{singular}_detail.html'
        if (tpl_html_dir / detail_tmpl).exists():
            return detail_tmpl, singular, 'slug'

    # 尝试去尾 ies → y_detail.html (如 categories → category_detail.html)
    if target.endswith('ies'):
        singular = target[:-3] + 'y'
        detail_tmpl = f'{singular}_detail.html'
        if (tpl_html_dir / detail_tmpl).exists():
            return detail_tmpl, singular, 'slug'

    # 通用回退: _generic_detail.html
    generic = '_generic_detail.html'
    if (tpl_html_dir / generic).exists():
        return generic, 'item', 'slug'

    return None, None, None


def collect_render_tasks(menu_items, tpl_html_dir, data, pages=None):
    """从菜单树收集所有需要渲染的页面任务 (递归).

    返回: list of dict, 每个 dict:
        type: 'home' | 'list' | 'page' | 'detail'
        template: Jinja2 模板文件名
        output_path: 输出相对路径 (语言目录内)
        current_path: 页面路径 (模板内用)
        page_key: 页面数据 key (pages/*.yaml 的 stem)
        dataset_key: 数据集名 (仅 list/detail)
        var_name: 模板变量名 (仅 detail)
        item: 数据条目 (仅 detail)
    """
    from pathlib import Path

    tasks = []

    # 首页固定
    tasks.append({
        'type': 'home',
        'template': 'index.html',
        'output_path': 'index.html',
        'current_path': '/',
        'page_key': 'home',
    })

    def _walk(items, parent_path=''):
        for item in items or []:
            t = item.get('type')
            target = item.get('target', '')

            # 计算当前项的 URL 路径 (含父级层级)
            # group/page/list 贡献其 target 到 item_path
            if parent_path and target:
                item_path = f'{parent_path}/{target}'
            elif target:
                item_path = target
            else:
                item_path = parent_path

            # 计算子菜单的父路径: page/list/group 传递其 target
            child_parent = parent_path
            if t in ('page', 'list', 'group') and target:
                child_parent = item_path

            # 详情页收集：只要菜单项带 target 且能解析出详情模板，就为数据集每个条目
            # 生成 /<path>/<slug>/ 详情页。list 与 group 共用此逻辑——老板在后台常把
            # 产品栏配成"分组(group)"做下拉菜单，此前只有 list 才生成详情页，group 会
            # 静默跳过，导致导航/列表里指向 /<target>/<slug>/ 的链接全部变死链、导出被拦。
            def _collect_detail_tasks():
                # derive_detail_info 内部已覆盖"预定义映射 + 通用推导 + <target>_detail.html"
                # 三种情况(见该函数)。
                dt_tmpl, var_name, slug_field = derive_detail_info(target, tpl_html_dir)
                if not (dt_tmpl and var_name):
                    return
                items_data = data.get(target, [])
                if isinstance(items_data, dict):
                    items_data = items_data.get('items', [])
                for entry in items_data:
                    slug = entry.get(slug_field, entry.get('slug', ''))
                    if slug:
                        tasks.append({
                            'type': 'detail',
                            'template': dt_tmpl,
                            'output_path': f'{item_path}/{slug}/index.html',
                            'current_path': f'/{item_path}/{slug}/',
                            'page_key': target,
                            'dataset_key': target,
                            'var_name': var_name,
                            'item': entry,
                        })

            # list 与带 target 的 group 一视同仁：都生成列表页 + 详情页。
            # 老板在后台常把产品栏配成"分组(group)"做下拉菜单，若 group 不落地，
            # 导航/详情页里指向 /<target>/ 和 /<target>/<slug>/ 的链接会全部变死链、
            # 导出被拦。带 target 的 group 实质就是"带下拉导航的列表栏目"，列表页正是
            # 它该有的落地页；只有纯分组容器（无 target）才不落地（走末尾递归子菜单）。
            if t in ('list', 'group') and target:
                # 所有列表页统一使用模块库配置（index.html → _modules.html）
                tasks.append({
                    'type': 'list',
                    'template': 'index.html',
                    'output_path': f'{item_path}/index.html',
                    'current_path': f'/{item_path}/',
                    'page_key': target,
                    'dataset_key': target,
                })
                _collect_detail_tasks()

            elif t == 'page' and target:
                page_tmpl = f'{target}.html'
                if not (tpl_html_dir / page_tmpl).exists():
                    page_tmpl = '_page.html' if (tpl_html_dir / '_page.html').exists() else 'index.html'
                page_key = item_path if pages and item_path in pages else target
                tasks.append({
                    'type': 'page',
                    'template': page_tmpl,
                    'output_path': f'{item_path}/index.html',
                    'current_path': f'/{item_path}/',
                    'page_key': page_key,
                })

            # 递归子菜单
            if item.get('children'):
                _walk(item['children'], child_parent)

    _walk(menu_items)
    return tasks


def _item_id(item):
    """为菜单项生成稳定的跨语言标识符。

    - home        → '__home__'
    - page/list/group with target → target 值
    - link        → url 值
    """
    t = item.get('type', '')
    if t == 'home':
        return '__home__'
    if t in ('page', 'list', 'group'):
        target = (item.get('target') or '').strip()
        if target:
            return target
    if t == 'link':
        url = (item.get('url') or '').strip()
        if url:
            return url
    # 兜底: label 做 key (极少数情况, 如无 target 的 page)
    return '__fallback__' + (item.get('label') or '')


def apply_labels(menu_tree, label_map):
    """递归遍历菜单树, 用 label_map 覆盖每个 item 的 label。

    label_map: {item_id: translated_label, ...}
    返回新列表, 不修改原数据。
    """
    if not menu_tree or not label_map:
        return list(menu_tree or [])

    result = []
    for it in (menu_tree or []):
        new_it = dict(it)
        key = _item_id(it)
        if key in label_map and label_map[key]:
            new_it['label'] = label_map[key]
        if new_it.get('children'):
            new_it['children'] = apply_labels(new_it['children'], label_map)
        result.append(new_it)
    return result


def extract_labels(menu_tree):
    """从菜单树提取 {item_id: label} 映射。

    用于保存时把当前语言的标签写入 menu_labels.<lang>。
    """
    result = {}
    def walk(items):
        for it in (items or []):
            key = _item_id(it)
            if key and not key.startswith('__fallback__'):
                result[key] = it.get('label', '')
            if it.get('children'):
                walk(it['children'])
    walk(menu_tree)
    return result


def merge_structure(existing_menu, submitted):
    """把 submitted 的结构变更合并到 existing_menu，保留 existing 的标签。

    - submitted 有但 existing 无 → 新项，用 submitted 的 label
    - submitted 和 existing 都有 → 保留 existing 的 label，更新结构（target/children等）
    - existing 有但 submitted 无 → 删除
    返回新列表，不修改原数据。
    """
    existing_by_id = {}

    def index(tree):
        for item in (tree or []):
            key = _item_id(item)
            if key and not key.startswith('__fallback__'):
                existing_by_id[key] = item
            if item.get('children'):
                index(item['children'])

    index(existing_menu or [])

    def merge(items):
        result = []
        for sub in (items or []):
            key = _item_id(sub)
            old = existing_by_id.get(key)
            new_item = dict(sub)
            if old:
                # 保留已有标签，其余字段（target/type/children）更新
                new_item['label'] = old.get('label', sub.get('label', ''))
            # else: 新项，直接用 submitted 的 label
            if sub.get('children'):
                new_item['children'] = merge(sub.get('children', []))
            result.append(new_item)
        return result

    return merge(submitted or [])


def check_deletion_impact(item, site_id, all_menu_items):
    """检查删除菜单项的关联影响.

    返回: dict {warnings: [...], affected_pages: [...], affected_datasets: [...],
              affected_children: int, affected_references: int}
    """
    from pathlib import Path
    from flask import current_app

    warnings = []
    affected_pages = []
    affected_datasets = []
    affected_children = len(item.get('children', []))
    affected_references = 0

    t = item.get('type')
    target = item.get('target', '')

    # 检查页面数据
    sites_dir = Path(current_app.config['SITES_DIR'])
    site_root = sites_dir / str(site_id)
    if t in ('list', 'page') and target:
        page_file = site_root / 'pages' / f'{target}.yaml'
        if page_file.exists():
            affected_pages.append(str(page_file.relative_to(site_root)))
            if t == 'list':
                warnings.append(f'页面 /{target}/ 将被移除')
            else:
                warnings.append(f'页面 /{target}/ 将被移除')

        data_file = site_root / 'data' / f'{target}.yaml'
        if data_file.exists():
            import yaml
            raw = yaml.safe_load(data_file.read_text(encoding='utf-8')) or []
            count = len(raw) if isinstance(raw, list) else len(raw.get('items', []))
            affected_datasets.append({
                'name': target,
                'path': str(data_file.relative_to(site_root)),
                'count': count,
            })
            warnings.append(f'数据集"{target}"（{count} 条）保留但不再显示')

    # 检查其他数据集中的引用
    data_dir = site_root / 'data'
    if data_dir.exists():
        import yaml
        for df in data_dir.glob('*.yaml'):
            raw = yaml.safe_load(df.read_text(encoding='utf-8')) or []
            items_list = raw if isinstance(raw, list) else raw.get('items', [])
            for entry in items_list:
                # 检查可能有链接到被删页面的字段
                for field in ('link', 'url', 'primaryBtnLink', 'secondaryBtnLink',
                              'primaryLink', 'secondaryLink', 'cta_url'):
                    val = entry.get(field, '')
                    if val and f'/{target}' in str(val):
                        affected_references += 1
                        break
        if affected_references:
            warnings.append(f'有 {affected_references} 条数据引用了 /{target} 下的链接，这些链接将失效')

    if affected_children:
        warnings.append(f'该菜单下有 {affected_children} 个子菜单项，将一并被删除')

    return {
        'warnings': warnings,
        'affected_pages': affected_pages,
        'affected_datasets': affected_datasets,
        'affected_children': affected_children,
        'affected_references': affected_references,
    }
