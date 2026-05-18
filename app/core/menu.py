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
VALID_DROPDOWN_STYLES = {'vertical', 'horizontal', 'grid', 'cards'}


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


def ensure_home(items):
    """确保首页固定为第一项. 返回新 list, 不改原数据."""
    normalized = list(items or [])
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
            if item_type in ('list', 'page', 'group'):
                target = str(raw.get('target') or '').strip().strip('/')
                if target:
                    item['target'] = target
            elif item_type == 'link':
                url = str(raw.get('url') or '').strip()
                if url:
                    item['url'] = url

            dropdown_style = str(raw.get('dropdown_style') or '').strip()
            if dropdown_style in VALID_DROPDOWN_STYLES:
                item['dropdown_style'] = dropdown_style

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
        var_name = target.rstrip('s') if target.endswith('s') else target
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

            if t == 'list' and target:
                # 所有 list 页面统一使用模块库配置（index.html → _modules.html）
                tasks.append({
                    'type': 'list',
                    'template': 'index.html',
                    'output_path': f'{item_path}/index.html',
                    'current_path': f'/{item_path}/',
                    'page_key': target,
                    'dataset_key': target,
                })
                # 详情页：先用预定义映射，回退通用推导
                dt_tmpl = None
                var_name = None
                slug_field = 'slug'
                dt_tmpl, var_name, slug_field = derive_detail_info(target, tpl_html_dir)
                if not dt_tmpl and (tpl_html_dir / f'{target}_detail.html').exists():
                    dt_tmpl = f'{target}_detail.html'
                    var_name = 'item'
                if dt_tmpl and var_name:
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

            elif t == 'page' and target:
                page_tmpl = f'{target}.html'
                if not (tpl_html_dir / page_tmpl).exists():
                    page_tmpl = '_page.html' if (tpl_html_dir / '_page.html').exists() else 'index.html'
                tasks.append({
                    'type': 'page',
                    'template': page_tmpl,
                    'output_path': f'{item_path}/index.html',
                    'current_path': f'/{item_path}/',
                    'page_key': target,
                })

            # 递归子菜单
            if item.get('children'):
                _walk(item['children'], child_parent)

    _walk(menu_items)
    return tasks


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
