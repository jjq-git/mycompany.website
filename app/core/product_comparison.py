"""产品参数对比页的数据标准化。

该模块只负责把现有产品 YAML 转成稳定的对比视图，不写回数据。旧站点可以继续
使用 specs 字典/列表；新内容逐步补充 key 后会自动得到更可靠的跨语言参数对应。
"""
import re


_HEX_COLOR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')


def _hex_color(value):
    value = str(value or '').strip()
    return value if _HEX_COLOR_RE.fullmatch(value) else ''


_KEY_CLEAN_RE = re.compile(r'[^a-z0-9\u4e00-\u9fff]+', re.IGNORECASE)


def _truthy(value, default=True):
    if value in (None, ''):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in {'0', 'false', 'no', 'off'}


def _int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _stable_key(value, fallback='parameter'):
    """把历史参数名转为可比较的稳定键，不改变保存的数据。"""
    cleaned = _KEY_CLEAN_RE.sub('_', str(value or '').strip().lower()).strip('_')
    return cleaned or fallback


def stable_parameter_key(value, fallback='parameter'):
    """后台保存参数时使用的公开入口，与只读兼容层保持同一规则。"""
    return _stable_key(value, fallback)


def _items(value):
    if isinstance(value, dict):
        value = value.get('items', [])
    return value if isinstance(value, list) else []


def _template_for_page(page, template_id=''):
    templates = page.get('detail_templates') if isinstance(page, dict) else []
    templates = templates if isinstance(templates, list) else []
    if template_id:
        found = next((tpl for tpl in templates if str(tpl.get('id') or '') == template_id), None)
        if found:
            return found
    return next((tpl for tpl in templates if _truthy(tpl.get('is_default'), False)), None) or (templates[0] if templates else {})


def _schema_groups(detail_template):
    """读取详情模板中的参数分组；没有 fields 的旧模板仍由产品数据补齐行。"""
    groups = []
    spec_index = 0
    for module in detail_template.get('modules', []) if isinstance(detail_template, dict) else []:
        if not isinstance(module, dict) or module.get('type') != 'detail_specs':
            continue
        data = module.get('data') if isinstance(module.get('data'), dict) else {}
        group_key = str(data.get('key') or module.get('key') or f'group_{spec_index}')
        title = str(data.get('title') or module.get('title') or '规格参数')
        fields = data.get('fields') if isinstance(data.get('fields'), list) else module.get('fields')
        rows = []
        for row_index, field in enumerate(fields if isinstance(fields, list) else []):
            if not isinstance(field, dict) or not _truthy(field.get('compare'), True):
                continue
            label = str(field.get('label') or field.get('name') or field.get('key') or '')
            key = str(field.get('key') or _stable_key(label, f'row_{row_index}'))
            rows.append({'key': key, 'label': label or key, 'unit': str(field.get('unit') or '')})
        groups.append({
            'key': group_key,
            'title': title,
            'rows': rows,
            'source_field': str(data.get('source_field') or 'specs'),
        })
        spec_index += 1
    return groups


def _legacy_group_items(value):
    if isinstance(value, dict):
        return [
            {'key': _stable_key(name), 'name': name, 'value': item_value}
            for name, item_value in value.items()
        ]
    return value if isinstance(value, list) else []


def _product_groups(product, schema_groups=None):
    """统一分组 detail_specs 与根级 specs/parameters/attributes 旧格式。"""
    detail_specs = product.get('detail_specs')
    if isinstance(detail_specs, list) and detail_specs:
        result = []
        for group_index, group in enumerate(detail_specs):
            if not isinstance(group, dict) or group.get('visible') is False:
                continue
            result.append({
                'key': str(group.get('key') or f'group_{group_index}'),
                'title': str(group.get('title') or ''),
                'items': _items(group.get('items')),
            })
        if result:
            return result

    # 旧产品可能把不同参数保存在根级 specs / parameters / attributes。
    # 模板的 source_field 只在这里作为兼容映射使用；同一来源只读取一次，
    # 与旧详情页“首个同来源组件消费数据”的行为保持一致。
    legacy_groups = []
    seen_sources = set()
    for group_index, schema_group in enumerate(schema_groups or []):
        source_field = str(schema_group.get('source_field') or 'specs')
        if source_field in seen_sources:
            continue
        seen_sources.add(source_field)
        items = _legacy_group_items(product.get(source_field))
        if items:
            legacy_groups.append({
                'key': str(schema_group.get('key') or f'group_{group_index}'),
                'title': str(schema_group.get('title') or '规格参数'),
                'items': items,
            })
    if legacy_groups:
        return legacy_groups

    specs = _legacy_group_items(product.get('specs'))
    if specs:
        return [{'key': 'group_0', 'title': '规格参数', 'items': specs}]
    return []


def _normalize_products(products, schema_groups):
    """构建参数并集并为每个产品建立 group:key → value 映射。"""
    groups = [
        {'key': group['key'], 'title': group['title'], 'rows': [dict(row) for row in group['rows']]}
        for group in schema_groups
    ]
    group_index = {group['key']: group for group in groups}
    normalized = []

    for product_index, product in enumerate(products):
        values = {}
        for raw_group_index, raw_group in enumerate(_product_groups(product, schema_groups)):
            group_key = raw_group.get('key') or f'group_{raw_group_index}'
            # 旧数据按分组位置与详情模板对应；有显式 key 时始终以 key 为准。
            if group_key not in group_index and raw_group_index < len(groups) and group_key.startswith('group_'):
                group_key = groups[raw_group_index]['key']
            if group_key not in group_index:
                group = {'key': group_key, 'title': raw_group.get('title') or '其他参数', 'rows': []}
                groups.append(group)
                group_index[group_key] = group
            group = group_index[group_key]
            row_index = {row['key']: row for row in group['rows']}
            label_index = {_stable_key(row['label']): row for row in group['rows']}

            for item_index, item in enumerate(raw_group.get('items') or []):
                if isinstance(item, dict):
                    label = str(item.get('name') or item.get('label') or item.get('key') or '')
                    explicit_key = str(item.get('key') or '')
                    key = explicit_key or _stable_key(label, f'row_{item_index}')
                    existing = row_index.get(key) or label_index.get(_stable_key(label))
                    if existing:
                        key = existing['key']
                    else:
                        row = {'key': key, 'label': label or key, 'unit': str(item.get('unit') or '')}
                        group['rows'].append(row)
                        row_index[key] = row
                        label_index[_stable_key(row['label'])] = row
                    value = item.get('value')
                    if value in (None, ''):
                        value = item.get('text') or item.get('desc') or item.get('description') or ''
                else:
                    key = f'row_{item_index}'
                    if key not in row_index:
                        group['rows'].append({'key': key, 'label': f'参数 {item_index + 1}', 'unit': ''})
                        row_index[key] = group['rows'][-1]
                    value = item
                values[f'{group_key}:{key}'] = str(value or '')

        normalized.append({
            'id': str(product.get('id') or product.get('slug') or product_index + 1),
            'slug': str(product.get('slug') or ''),
            'title': str(product.get('title') or product.get('name') or '未命名产品'),
            'subtitle': str(product.get('model') or product.get('subtitle') or product.get('summary') or ''),
            'category': str(product.get('category') or ''),
            'image': str(product.get('cover') or product.get('image') or product.get('photo') or ''),
            'price': str(product.get('price') or ''),
            'price_note': str(product.get('price_note') or product.get('meta_label') or ''),
            'values': values,
        })
    return groups, normalized


def _collect_comparison_pages(all_pages, dataset_paths):
    """扫描全站页面，收集所有含 product_comparison 模块的对比页（标题 + 链接）。

    下拉框用它列出“对比分类”，选中后跳转到对应对比页。链接直接取
    dataset_paths[page_key]（已按当前语言/base_url 处理），保证与站内导航一致。
    只收录能拿到 URL 的页面，避免生成跳到空链接的死项。
    """
    result = []
    seen_urls = set()
    for page_key, page in (all_pages or {}).items():
        if not isinstance(page, dict):
            continue
        modules = page.get('modules') if isinstance(page.get('modules'), list) else []
        module = next((m for m in modules if isinstance(m, dict) and m.get('type') == 'product_comparison'), None)
        if module is None:
            continue
        url = str((dataset_paths or {}).get(page_key) or '')
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        module_data = module.get('data') if isinstance(module.get('data'), dict) else {}
        # 标题优先用模块自定义标题，其次页面标题，最后回落到 page_key
        title = str(module_data.get('title') or page.get('title') or page_key)
        result.append({'key': str(page_key), 'title': title, 'url': url})
    result.sort(key=lambda item: item['title'])
    return result


def build_product_comparison(all_datasets, all_pages, data, dataset_paths, base_url=''):
    """生成模板可直接消费的产品对比视图模型。"""
    data = data if isinstance(data, dict) else {}
    dataset_key = str(data.get('dataset') or 'products')
    raw_dataset = (all_datasets or {}).get(dataset_key, [])
    products = _items(raw_dataset)
    template_id = str(data.get('detail_template_id') or '')
    canonical_page = (all_pages or {}).get(dataset_key, {})
    detail_template = _template_for_page(canonical_page, template_id)
    effective_template_id = template_id or str(detail_template.get('id') or '')

    candidates = []
    for product in products:
        if not isinstance(product, dict) or not _truthy(product.get('compare_enabled'), True):
            continue
        product_template = str(product.get('template_id') or '')
        if effective_template_id and product_template and product_template != effective_template_id:
            continue
        candidates.append(product)
    candidates.sort(key=lambda item: (_int(item.get('compare_order'), 999999), str(item.get('name') or item.get('title') or '')))
    candidates = candidates[:200]

    groups, normalized = _normalize_products(candidates, _schema_groups(detail_template))
    detail_prefix = str((dataset_paths or {}).get(dataset_key) or f'/{dataset_key}/')
    if base_url and detail_prefix.startswith('/') and not detail_prefix.startswith(base_url.rstrip('/') + '/'):
        detail_prefix = base_url.rstrip('/') + detail_prefix
    detail_prefix = detail_prefix.rstrip('/') + '/'
    for product in normalized:
        product['detail_url'] = detail_prefix + product['slug'] + '/' if product['slug'] else ''

    # 产品总数与视觉槽位分开：旧字段 max_products 不再是选择上限，也不能继续
    # 决定占位列数。对比表默认补到 5 个视觉槽位；选中超过 5 个时由前端自然扩展。
    configured_slots = max(1, min(10, _int(data.get('display_slots'), 5) or 5))
    total_products = len(normalized)
    display_slots = configured_slots
    raw_default_ids = data.get('default_product_ids') or []
    if isinstance(raw_default_ids, str):
        raw_default_ids = [part.strip() for part in raw_default_ids.split(',') if part.strip()]
    default_ids = [str(value) for value in raw_default_ids if str(value)] if isinstance(raw_default_ids, list) else []
    if not default_ids:
        default_ids = [product['id'] for product in normalized]

    # 收集全站对比页供“对比分类”下拉框跳转；当前页用 dataset_key 匹配高亮
    comparison_pages = _collect_comparison_pages(all_pages, dataset_paths)
    return {
        'dataset': dataset_key,
        'title': str(data.get('title') or '产品参数对比'),
        'subtitle': str(data.get('subtitle') or ''),
        'groups': groups,
        'products': normalized,
        'comparison_pages': comparison_pages,
        'current_page_key': dataset_key,
        'default_ids': default_ids,
        'total_products': total_products,
        'display_slots': display_slots,
        # 兼容已发布的旧版前端；该值现在等于真实总数，不再表示选择上限。
        'max_products': total_products,
        'empty_text': str(data.get('empty_text') or '—'),
        'show_search': _truthy(data.get('show_search'), True),
        'show_hide_same': _truthy(data.get('show_hide_same'), True),
        'show_image': _truthy(data.get('show_image'), True),
        'show_price': _truthy(data.get('show_price'), True),
        'section_bg': _hex_color(data.get('section_bg')),
    }
