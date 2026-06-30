"""Block 数据注入渲染器：声明式 block 模板 + 数据 → 最终 HTML.

接收 block 原始 HTML、解析出的 schema、店主填的数据 data_dict、以及全局 context
（含 all_datasets），产出可直接写进页面的干净 HTML（不含任何 data-* 属性）。

实现策略：在 block_parser 建好的 _Node DOM 树上做变换，再序列化输出。
不用正则替换 HTML 字符串——那种做法对嵌套结构和转义极易出错（CLAUDE.md 教训）。

5 步后处理管线：
1. 字段注入   —— 按 data-name 把值写进 innerText / src / href
2. 列表展开   —— data-type=list/grid：手动模式从 data_dict 取数组，数据集模式从 all_datasets 取，循环复制项模板
3. 显隐处理   —— data-hideable 检查隐藏标记；叶子空值/空列表自动加 hidden
4. 样式注入   —— 读 data-style 查注册表，按控件白名单校验后写进 style 的 CSS 变量
5. 清理       —— 删掉所有 data-* 属性，输出干净 HTML

安全：所有注入值（文本/src/href/style）统一转义；href 限定安全 scheme；
样式值按注册表 control 类型白名单校验。richtext 按 innerHTML 语义不转义——
其内容必须在**录入侧**做 HTML sanitize（白名单），否则是存储型 XSS 面。
"""
import re
from html import escape as html_escape

from . import block_parser as bp
from . import icon_registry
from . import style_registry

# 媒体类型 → 注入到哪个属性
_MEDIA_SRC_ATTR = {'image': 'src', 'video': 'src', 'audio': 'src', 'embed': 'src'}
_TEXT_TYPES = {'text', 'textarea', 'richtext', 'url'}  # url 也走文本注入（供 JS 读取）；icon 单独处理

# data-href 允许的 URL scheme（其余如 javascript:/data: 一律丢弃，防 XSS）
_SAFE_HREF = re.compile(r'^(https?:|mailto:|tel:|/|#|\./|\.\./|[^:]*$)', re.I)
# 颜色值白名单：#hex、rgb()/rgba()、hsl()/hsla()、css 关键字（字母）
_SAFE_COLOR = re.compile(r'^(#[0-9a-f]{3,8}|rgba?\([\d.,%\s]+\)|hsla?\([\d.,%\s]+\)|[a-z]+)$', re.I)
_IMG_TAG_RE = re.compile(r'<img\b[^>]*>', re.I)
_ALT_ATTR_RE = re.compile(r'\s+alt\s*=\s*("([^"]*)"|\'([^\']*)\'|([^\s>]*))', re.I)
# 检测文本是否包含 HTML 标签（用于判断 textarea 内容是否来自富文本编辑器）
_HTML_TAG_RE = re.compile(r'<(p|div|br|h[1-6]|ul|ol|li|a|img|span|strong|em|b|i|u|s|table|blockquote|hr)\b', re.I)
_BLOCK_HTML_TAG_RE = re.compile(r'<(p|div|h[1-6]|ul|ol|li|table|blockquote|hr)\b', re.I)


def _int_or_none(raw):
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _richtext_with_image_alt(html, alt_text):
    """给富文本里的 img 补 alt；已有非空 alt 不覆盖。"""
    if not html or not alt_text:
        return html
    escaped_alt = html_escape(str(alt_text), quote=True)

    def repl(match):
        tag = match.group(0)
        alt_match = _ALT_ATTR_RE.search(tag)
        if alt_match:
            current_alt = alt_match.group(2) or alt_match.group(3) or alt_match.group(4) or ''
            if current_alt.strip():
                return tag
            return _ALT_ATTR_RE.sub(f' alt="{escaped_alt}"', tag, count=1)
        if tag.endswith('/>'):
            return tag[:-2].rstrip() + f' alt="{escaped_alt}">'
        return tag[:-1].rstrip() + f' alt="{escaped_alt}">'

    return _IMG_TAG_RE.sub(repl, str(html))


def _set_text(node, value, raw_html=False):
    """设置元素的文字内容（替换所有子节点）。

    raw_html=True（richtext）：按 innerHTML 原样注入，序列化不转义。
    否则：作为纯文本，序列化时转义。
    """
    if raw_html and node.tag.lower() == 'p' and _BLOCK_HTML_TAG_RE.search(str(value)):
        node.tag = 'div'
    node.nodes = [bp._Text(str(value), raw=raw_html)]


def _hide(node):
    """给元素加 hidden 属性（原生隐藏，等价 display:none）。"""
    node.attrs['hidden'] = None  # None = 无值属性，序列化为 hidden


# schema 声明用的 data-* 属性（渲染后清理掉）。其余 data-*（如 data-target、
# data-index 等给前端 JS 用的业务属性）保留，否则会破坏 block 内嵌脚本（如数字动画）。
_SCHEMA_DATA_ATTRS = {
    'data-name', 'data-type', 'data-href', 'data-href-template', 'data-fallback',
    'data-style', 'data-hideable', 'data-source', 'data-page-size', 'data-cols',
    'data-from', 'data-i18n', 'data-i18n-placeholder', 'data-show-when',
}


def _field_value(field_def, data_dict):
    """取字段值：本字段名空时按 data-fallback 依次回退（如 title←name、desc←summary/excerpt）。"""
    val = data_dict.get(field_def.name)
    if val in (None, ''):
        for key in field_def.fallback:
            alt = data_dict.get(key)
            if alt not in (None, ''):
                return alt
    return val

# data-href-template 的 {占位符} 语法：从 context['vars'] + 当前项数据填充
_TEMPLATE_RE = re.compile(r'\{([a-zA-Z0-9_]+)\}')


def _fill_template(tmpl, values):
    """填充 {key} 占位符。任一占位符在 values 中无对应（None）→ 返回 None（视为不完整链接）。

    base_url 等上下文变量即使为空串也算"有值"（合法的相对路径前缀）；只有键完全
    缺失（数据集项没有 slug 等）才判为不完整。
    """
    missing = []

    def repl(m):
        v = values.get(m.group(1))
        if v is None:
            missing.append(m.group(1))
            return ''
        return str(v)

    out = _TEMPLATE_RE.sub(repl, tmpl)
    return None if missing else out


def _strip_data_attrs(node):
    """递归删除 schema 声明用的 data-* 属性（管线第 5 步），保留业务用 data-*。"""
    node.attrs = {k: v for k, v in node.attrs.items() if k not in _SCHEMA_DATA_ATTRS}
    for child in node.children:
        _strip_data_attrs(child)


def _resolve_path(data, path):
    node = data
    for part in str(path or '').split('.'):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _apply_i18n(node, context):
    key = node.attrs.get('data-i18n')
    if key:
        value = _resolve_path((context or {}).get('t') or {}, key)
        if value not in (None, ''):
            _set_text(node, value)
    placeholder_key = node.attrs.get('data-i18n-placeholder')
    if placeholder_key:
        placeholder = _resolve_path((context or {}).get('t') or {}, placeholder_key)
        if placeholder not in (None, ''):
            node.attrs['placeholder'] = str(placeholder)
    for child in node.children:
        _apply_i18n(child, context)


def _safe_href(value):
    """校验 href：仅放行安全 scheme，危险的（javascript:/data: 等）返回空。"""
    v = str(value).strip()
    return v if _SAFE_HREF.match(v) else ''


def _is_truthy(value):
    """判断开关值是否为真。表单存的是字符串布尔，'false'/'no'/'0'/'' 均视为假。"""
    if isinstance(value, str):
        return value.strip().lower() in ('true', 'yes', 'on', '1')
    return bool(value)


# 模板中图片/视频占位元素常见的隐藏样式（仅清除纯占位，保留其他合法 style）
_HIDE_STYLE_RE = re.compile(r'^\s*display\s*:\s*none\s*(;\s*)?\s*$', re.I)


def _clean_placeholder_style(node):
    """若 node 的 style 仅为占位隐藏（display:none），清掉它。

    模板中图片/视频默认写 style="display:none" 作为"无数据时隐藏"的占位，
    当真实 URL 注入后应清除此样式，否则图片/视频仍然不可见。
    仅匹配纯 display:none；带其他合法样式（width/height/border 等）则保留。
    """
    style = node.attrs.get('style')
    if style is not None and _HIDE_STYLE_RE.match(str(style)):
        node.attrs.pop('style', None)


def _icon_svg(name):
    """图标名 → SVG 字符串。注册表的 SVG 是可信的（开发者维护），原样注入。"""
    return icon_registry.get_icon_svg(name)


def _inject_leaf(node, field_def, value):
    """把一个值注入到叶子元素。返回 True 表示有内容，False 表示空（应隐藏）。

    语义（对齐规范"空值自动隐藏" + 旧 block 的 {% if md.x %} 行为）：
    模板里的默认文字/src 只是**编辑器占位示意**，不输出到成品站点。
    最终渲染时，字段只有拿到非空真实值才显示；键缺失或空串一律隐藏。
    """
    dtype = field_def.type
    has_content = value not in (None, '')

    if dtype == 'icon':
        # icon：值是图标名，查注册表注入对应 SVG（作为 innerHTML）。
        # 未知图标名或空值 → 当无内容（隐藏），不输出占位。
        svg = _icon_svg(value) if has_content else None
        if svg:
            _set_text(node, svg, raw_html=True)
        else:
            _set_text(node, '')
            has_content = False
    elif dtype in _TEXT_TYPES:
        if has_content:
            # richtext 始终按 innerHTML 注入；textarea 字段如果在
            # 编辑器中使用了富文本（isDescriptionKey 匹配），内容可能
            # 包含 HTML 标签，需要同样按 raw_html 处理，避免标签被转义显示。
            is_html = dtype == 'richtext' or (dtype == 'textarea' and bool(
                _HTML_TAG_RE.search(str(value))
            ))
            _set_text(node, value, raw_html=is_html)
        else:
            # 用户未填 → 清空文字并隐藏。模板内的占位文字（"标签文字"等）是
            # 编辑器示意，不应输出到成品站点。此前 default_text 回退导致
            # 未配置的字段以占位内容出现在预览中。
            _set_text(node, "")
            has_content = False
    elif dtype in _MEDIA_SRC_ATTR:
        attr = _MEDIA_SRC_ATTR[dtype]
        if has_content:
            node.attrs[attr] = str(value)  # 序列化时统一转义
            # 清除模板中的占位隐藏样式（如 style="display:none"），
            # 否则图片/视频有真实 URL 后仍然不可见
            _clean_placeholder_style(node)
        else:
            node.attrs.pop(attr, None)  # 清掉占位 src，元素稍后会被隐藏

    return has_content


def _inject_href(node, data_dict, context=None):
    """处理 data-href / data-href-template，注入 href（空/不安全则跳过，不隐藏仅不可点）。

    - data-href-template：含 {占位符} 的链接模板，从 context['vars']（base_url/lang/
      current_path 等）+ 当前项 data_dict 填充，再过 scheme 校验。优先于 data-href。
    - data-href：值是数据字段名，从 data_dict 取该字段值作 href。
    """
    data_dict = data_dict or {}
    tmpl = node.attrs.get('data-href-template')
    if tmpl:
        merged = {**((context or {}).get('vars') or {}), **data_dict}
        filled = _fill_template(tmpl, merged)
        if filled:
            safe = _safe_href(filled)
            if safe:
                node.attrs['href'] = safe
        return
    href_field = node.attrs.get('data-href')
    if not href_field:
        return
    href_val = data_dict.get(href_field)
    if href_val:
        # 以 / 开头的站内相对路径拼上 base_url/lang，保证预览和发布都正确
        # （与 _base.html 中 menu_href 宏的 base_url/lang/href 拼接模式一致）
        if isinstance(href_val, str) and href_val.startswith('/') and not href_val.startswith('//'):
            vars_ctx = ((context or {}).get('vars') or {})
            base = (vars_ctx.get('base_url') or '').rstrip('/')
            lang = vars_ctx.get('lang') or ''
            if base and lang:
                href_val = f'{base}/{lang}{href_val}'
            elif base:
                href_val = f'{base}{href_val}'
        safe = _safe_href(href_val)
        if safe:
            node.attrs['href'] = safe  # 序列化时统一转义


def _process_field(node, field_def, data_dict, context):
    """处理单个字段节点（叶子 / group / list / grid），就地修改 node。"""
    dtype = field_def.type
    value = _field_value(field_def, data_dict)

    if dtype in bp.LEAF_TYPES:
        if dtype == 'richtext' and value not in (None, ''):
            alt_text = (
                data_dict.get('alt') or data_dict.get('image_alt') or data_dict.get('imageAlt') or
                data_dict.get('cover_alt') or data_dict.get(f'{field_def.name}_alt') or
                data_dict.get('title') or data_dict.get('name') or
                ((context or {}).get('vars') or {}).get('default_alt') or ''
            )
            value = _richtext_with_image_alt(value, alt_text)
        has_content = _inject_leaf(node, field_def, value)
        if has_content and dtype in _MEDIA_SRC_ATTR and dtype == 'image' and node.tag == 'img':
            alt_text = (
                data_dict.get('alt') or data_dict.get('image_alt') or data_dict.get('imageAlt') or
                data_dict.get('cover_alt') or data_dict.get(f'{field_def.name}_alt') or
                data_dict.get('title') or data_dict.get('name') or
                ((context or {}).get('vars') or {}).get('default_alt') or ''
            )
            node.attrs['alt'] = str(alt_text)
        _inject_href(node, data_dict, context)
        if not has_content:
            _hide(node)  # 叶子空值自动隐藏
        return

    if dtype == 'group':
        # group 的数据是一个 dict；子字段递归注入
        sub = value if isinstance(value, dict) else data_dict
        _inject_into_children(node, field_def.children, sub, context)
        _inject_href(node, sub, context)
        return

    # 无语义类型但带有 data-href-template：仅注入链接（如"了解详情"按钮）
    if not dtype and node.attrs.get('data-href-template'):
        _inject_href(node, data_dict, context)
        return

    if dtype in bp.LIST_TYPES:
        _expand_list(node, field_def, data_dict, context)
        return


def _inject_into_children(parent_node, field_defs, data_dict, context):
    """把 field_defs 对应的值注入 parent_node 的子树中匹配的元素（按 data-name 定位）。"""
    by_name = {f.name: f for f in field_defs}
    _walk_and_inject(parent_node, by_name, data_dict, context)


def _append_class(node, class_name):
    current = str(node.attrs.get('class') or '').strip()
    parts = current.split() if current else []
    if class_name not in parts:
        parts.append(class_name)
    node.attrs['class'] = ' '.join(parts)


def _mark_filter_source_tags_visual_hidden(node):
    classes = str(node.attrs.get('class') or '').split()
    if 'filter-source-tags' in classes:
        _append_class(node, 'dg-card-tags--visual-hidden')
    for child in node.nodes:
        if isinstance(child, bp._Node):
            _mark_filter_source_tags_visual_hidden(child)


def _walk_and_inject(node, by_name, data_dict, context):
    """遍历子树，遇到匹配 data-name 的元素就注入。

    命中字段表的元素交给 _process_field 整体处理（叶子/group/list 各自决定是否下钻），
    其余继续往下找。"""
    for child in node.children:
        cname = child.attrs.get('data-name')
        if cname and cname in by_name:
            _process_field(child, by_name[cname], data_dict, context)
        else:
            # 不带名或不在本层字段表：继续往下找
            _walk_and_inject(child, by_name, data_dict, context)


def _resolve_list_items(field_def, data_dict, context):
    """决定列表的数据来源，返回条目数组（list of dict）。

    - 手动模式（source 为 None 或 'manual'）：从 data_dict[name] 取
    - 数据集模式（source 存在）：从 context['all_datasets'] 取
      - source 具名（如 'products'）：限定该数据集
      - source 空串：店主在页面配置里选的数据集（data_dict 里存 dataset 名）
    """
    source = field_def.source
    if source in (None, 'manual'):
        items = data_dict.get(field_def.name)
        return items if isinstance(items, list) else []

    all_datasets = (context or {}).get('all_datasets', {})
    dataset_name = source if source else data_dict.get('dataset')
    if not dataset_name:
        return []
    raw = all_datasets.get(dataset_name)
    # products 这类数据集是 {categories, items}，取 items；纯 list 直接用
    if isinstance(raw, dict):
        return raw.get('items', [])
    if isinstance(raw, list):
        return raw
    return []


def _expand_list(node, field_def, data_dict, context):
    """展开 list/grid：按数据复制项模板，逐条注入。就地替换 node 的项模板槽位。

    数据为空且容器内无其他杂项（标题等）→ 整个容器加 hidden（对齐规范"空数组隐藏"）。
    """
    items = _resolve_list_items(field_def, data_dict, context)
    max_items = _int_or_none(data_dict.get('max_items') if isinstance(data_dict, dict) else None)
    if max_items:
        items = items[:max_items]
    # data-page-size：作为"最多展示条数"上限（数据集驱动如 product_grid 的 max_items）
    if field_def.page_size:
        items = items[:field_def.page_size]

    if not field_def.item_template_html:
        node.nodes = []
        _hide(node)
        return

    new_items = []
    for item in items:
        # 把项模板 HTML 解析成独立节点树（每条一份）
        b = bp._DomBuilder()
        b.feed(field_def.item_template_html)
        b.close()
        item_node = b.root
        if item_node is None:
            continue
        item_type = item_node.attrs.get('data-type', '')
        if item_type == 'group':
            item_data = dict(item) if isinstance(item, dict) else {}
            if not item_data.get('media_type'):
                if item_data.get('embed_url'):
                    item_data['media_type'] = 'embed'
                elif item_data.get('video'):
                    item_data['media_type'] = 'video'
                else:
                    item_data['media_type'] = 'image'
            if isinstance(data_dict, dict):
                for inherited_key in ('show_detail_btn',):
                    if inherited_key not in item_data and inherited_key in data_dict:
                        item_data[inherited_key] = data_dict[inherited_key]
            _inject_into_children(item_node, field_def.children, item_data, context)
            _inject_href(item_node, item_data, context)
            _apply_conditional_visibility(item_node, item_data)
            if item_data.get('tags_visible') is False or str(item_data.get('tags_visible')).lower() == 'false':
                _mark_filter_source_tags_visual_hidden(item_node)
        else:
            # 项模板根直接是叶子：item 可能是 dict（logo 墙 {logo,link}）
            # 或标量（tags 这类字符串列表，值即本身）
            _inject_root_leaf(item_node, item, context)
        new_items.append(item_node)

    # 用展开后的多项替换"项模板那一项"，保留容器内的杂项（标题等）和文本节点（空白）
    node.nodes = _replace_item_slot(node.nodes, new_items)

    # 数据为空 → 若容器内除项模板外无其他元素，整体隐藏（避免渲染出带背景的空带）
    if not new_items and not any(isinstance(n, bp._Node) for n in node.nodes):
        _hide(node)


def _inject_root_leaf(node, item, context=None):
    """项模板根直接是叶子元素时按自己的 data-name 注入。

    item 为 dict（如 logo 墙 {logo,link}）→ 取 item[name]；
    item 为标量（如 tags 的字符串列表）→ 值即标量本身。
    """
    name = node.attrs.get('data-name')
    dtype = node.attrs.get('data-type', '')
    fd = bp.FieldDef(name=name, type=dtype, tag=node.tag,
                     href_field=node.attrs.get('data-href', '') or '')
    value = item.get(name) if isinstance(item, dict) else item
    has = _inject_leaf(node, fd, value)
    _inject_href(node, item if isinstance(item, dict) else {}, context)
    if not has:
        _hide(node)


def _replace_item_slot(nodes, new_items):
    """把 nodes 里"第一个带 data-name 的元素（项模板）"替换为展开后的多项。

    保留：文本节点（空白/缩进）、不带 data-name 的杂项元素（标题等）。
    丢弃：项模板之外的其它带 data-name 的元素（规范要求容器只有一个项模板）。
    """
    result = []
    replaced = False
    for child in nodes:
        if isinstance(child, bp._Node) and 'data-name' in child.attrs:
            if not replaced:
                result.extend(new_items)
                replaced = True
            # 已替换过：跳过多余的同级命名元素（理论上只有一个项模板）
        else:
            result.append(child)  # 文本节点或无名杂项原样保留
    if not replaced:
        result.extend(new_items)
    return result


def _apply_element_visibility(node, data_dict):
    """递归处理元素级 data-hideable：每个带 data-name 且有 data-hideable 的元素，
    检查 data_dict 中的 _hidden_<name> 标记，为 true 则加 hidden 属性。"""
    for child in node.children:
        name = child.attrs.get('data-name')
        if name and 'data-hideable' in child.attrs:
            if _is_truthy(data_dict.get(f'_hidden_{name}')):
                _hide(child)
        _apply_element_visibility(child, data_dict)


def _apply_conditional_visibility(node, data_dict):
    """Remove nodes whose data-show-when condition does not match current data."""
    condition = node.attrs.get('data-show-when')
    if condition and ':' in condition:
        field, raw_values = condition.split(':', 1)
        field = field.strip()
        default_value = 'image' if field == 'media_type' else ''
        raw_actual = data_dict.get(field, default_value)
        actual = 'true' if raw_actual is True else 'false' if raw_actual is False else str(raw_actual).strip()
        allowed = [v.strip() for v in raw_values.split(',') if v.strip()]
        if actual not in allowed:
            return False
        node.attrs.pop('data-show-when', None)

    kept_nodes = []
    for child in node.nodes:
        if isinstance(child, bp._Node) and not _apply_conditional_visibility(child, data_dict):
            continue
        kept_nodes.append(child)
    node.nodes = kept_nodes
    return True


def _resolve_from_source(schema, context):
    """解析 data-from 路径（如 "settings:contact"），从 context 取对应数据。

    格式：<context_key>:<sub_path> —— 冒号前是 context 的一级键，冒号后是
    该键下的子路径。如 "settings:contact" → context['settings']['contact']。
    解析失败（键缺失或中间为 None）返回空 dict。
    """
    raw = schema.from_source
    if not raw:
        return {}
    parts = raw.split(':', 1)
    if len(parts) != 2:
        return {}
    root_key, sub_path = parts
    node = (context or {}).get(root_key)
    if not isinstance(node, dict):
        return {}
    # 子路径可能嵌套，如 "company.address"（预留，当前只用一层）
    for segment in sub_path.split('.'):
        node = node.get(segment)
        if not isinstance(node, dict):
            return {}
    return node


def _apply_style(node, style_tokens, data_dict):
    """管线第 4 步：把用户选的样式值写进 style 的 CSS 变量。

    data_dict 里约定用 'style_<token>' 存用户选值（如 style_cols=4）。
    按注册表 control 类型做白名单校验，防止值逃逸出 style 属性造成 XSS。
    未选/非法的 token 跳过（CSS var() 默认值生效）。
    """
    existing = node.attrs.get('style', '')
    parts = [existing.rstrip('; ')] if existing else []
    for token in style_tokens:
        sdef = style_registry.get_style_def(token)
        if not sdef:
            continue
        val = data_dict.get(f'style_{token}')
        if val in (None, ''):
            continue
        safe = _sanitize_style_value(sdef, str(val))
        if safe is None:
            continue
        parts.append(f'{sdef["css_var"]}: {safe}')
    if parts:
        node.attrs['style'] = '; '.join(parts)  # 序列化时整体再转义引号


def _apply_descendant_styles(node, data_dict):
    """给子孙元素上的 data-style 注入 CSS 变量。

    这让普通包裹层也能声明样式能力，例如 <div class="hl-grid" data-style="bg-color">。
    """
    for child in node.children:
        tokens = [
            t for t in style_registry.parse_style_tokens(child.attrs.get('data-style', ''))
            if style_registry.get_style_def(t)
        ]
        if tokens:
            _apply_style(child, tokens, data_dict)
        _apply_descendant_styles(child, data_dict)


def _append_style(node, prop, value):
    if value in (None, ''):
        return
    safe = _sanitize_style_value({'control': 'text'}, str(value))
    if safe is None:
        return
    existing = node.attrs.get('style', '').rstrip('; ')
    node.attrs['style'] = (existing + '; ' if existing else '') + f'{prop}: {safe}'


def _append_color_style(node, prop, value):
    if value in (None, ''):
        return
    safe = _sanitize_style_value({'control': 'color'}, str(value))
    if safe is None:
        return
    existing = node.attrs.get('style', '').rstrip('; ')
    node.attrs['style'] = (existing + '; ' if existing else '') + f'{prop}: {safe}'


def _find_first_by_class(node, class_name):
    cls = node.attrs.get('class', '') if hasattr(node, 'attrs') else ''
    if class_name in cls.split():
        return node
    for child in getattr(node, 'children', []):
        found = _find_first_by_class(child, class_name)
        if found is not None:
            return found
    return None


def _apply_text_content_config(root, data_dict):
    if not isinstance(data_dict, dict):
        return
    cls = root.attrs.get('class', '') if hasattr(root, 'attrs') else ''
    if root.attrs.get('data-name') != 'text_content' and 'text_content' not in cls:
        return

    container = _find_first_by_class(root, 'container')
    title = _find_first_by_class(root, 'section-title')
    body = _find_first_by_class(root, 'tc-body')
    block = _find_first_by_class(root, 'tc-block')

    _append_color_style(root, 'background-color', data_dict.get('section_bg'))
    _append_style(root, 'width', data_dict.get('outer_width'))
    for key, prop in (
        ('margin_top', 'margin-top'),
        ('margin_right', 'margin-right'),
        ('margin_bottom', 'margin-bottom'),
        ('margin_left', 'margin-left'),
    ):
        _append_style(root, prop, data_dict.get(key))

    if container is not None:
        _append_style(container, 'max-width', data_dict.get('inner_width'))
        for key, prop in (
            ('padding_top', 'padding-top'),
            ('padding_right', 'padding-right'),
            ('padding_bottom', 'padding-bottom'),
            ('padding_left', 'padding-left'),
        ):
            _append_style(container, prop, data_dict.get(key))

    text_align = data_dict.get('text_align')
    if text_align in ('left', 'center', 'right'):
        _append_style(root, 'text-align', text_align)

    if title is not None:
        _append_color_style(title, 'color', data_dict.get('title_color'))
        _append_style(title, 'font-size', data_dict.get('title_size'))

    if body is not None:
        _append_color_style(body, 'color', data_dict.get('body_color'))
        _append_style(body, 'font-size', data_dict.get('body_size'))

    if block is not None and str(data_dict.get('columns') or '') == '2':
        _append_style(block, 'column-count', '2')
        _append_style(block, 'column-gap', '2rem')


def _sanitize_style_value(sdef, val):
    """按控件类型校验样式值，非法返回 None。

    - select/switch：只允许 options 里声明的 value
    - color：只允许颜色语法（#hex / rgb() / 关键字）
    - image：只允许 url(...)，内部不得含引号/括号闭合字符
    """
    control = sdef.get('control')
    val = val.strip()
    if control in ('select', 'switch'):
        allowed = {o['value'] for o in sdef.get('options', [])}
        return val if val in allowed else None
    if control == 'color':
        return val if _SAFE_COLOR.match(val) else None
    if control == 'image':
        # 期望形如 url('/path') 或 url(/path)，禁止值里出现 " ' ) ; 防逃逸
        inner = val
        if inner.startswith('url(') and inner.endswith(')'):
            inner = inner[4:-1].strip('\'"')
        if any(c in inner for c in '"\');'):
            return None
        return f"url('{inner}')"
    # 未知控件：保守拒绝特殊字符
    return val if not any(c in val for c in '"\';') else None


def render(block_html, schema, data_dict, context=None):
    """渲染一个 data-* block，返回干净 HTML 字符串。

    block_html: block 模板原始 HTML
    schema:     block_parser.parse() 的结果
    data_dict:  该模块存的数据（module.data）
    context:    全局上下文，需含 'all_datasets'（数据集驱动列表用）
    """
    data_dict = data_dict or {}
    context = context or {}

    # 0. data-from：若 schema 声明了数据来源（如 settings:contact），
    # 从 context 取对应数据作为基底，module.data 中的值可覆盖（开店者手动调）
    from_data = _resolve_from_source(schema, context)
    if from_data:
        # from_data 作底，data_dict 的值优先
        merged = dict(from_data)
        merged.update(data_dict)
        data_dict = merged

    # 重新解析成可变节点树（不污染传入的 schema）
    b = bp._DomBuilder()
    b.feed(block_html)
    b.close()
    root = b.root
    if root is None:
        return ''

    # 1+2. 字段注入 / 列表展开
    if schema.root_type in bp.LIST_TYPES:
        _expand_list(root, _schema_as_field(schema), data_dict, context)
    else:
        # group 或其他：注入子字段
        _inject_into_children(root, schema.fields, data_dict, context)

    # 根元素自身的 href
    if schema.href_field or root.attrs.get('data-href-template'):
        _inject_href(root, data_dict, context)

    # 3. 显隐处理：data-hideable + 隐藏标记
    # 整块隐藏（根级 data-hideable）
    if schema.hideable and _is_truthy(data_dict.get('_hidden')):
        _hide(root)
    # 元素级隐藏：遍历所有带 data-hideable 的子元素，检查 _hidden_<name> 标记
    _apply_element_visibility(root, data_dict)
    _apply_conditional_visibility(root, data_dict)

    # 4. 样式注入
    if schema.style_tokens:
        _apply_style(root, schema.style_tokens, data_dict)
    _apply_descendant_styles(root, data_dict)

    # 4.5 全树补扫静态 href 模板（"查看全部"等仅依赖 base_url/lang 的链接）；
    # 依赖项字段的链接（含 {slug} 等）已在列表展开时填好，这里因占位无值而跳过，不会被覆盖
    _fill_static_href_templates(root, context)
    # 4.6 补扫业务属性模板（data-filter-id="{dataset}" 等），
    # 将 {dataset} 等变量替换为实际数据集名
    _fill_business_attr_templates(root, context)
    _apply_i18n(root, context)

    # 4.7 卡片配置：card_layout（图文排版）+ card_show_border（边框显隐）
    _apply_card_config(root, data_dict)
    _apply_text_content_config(root, data_dict)

    # 5. 清理 data-*
    _strip_data_attrs(root)

    return bp._serialize(root)


def _add_class(attrs, class_name):
    """给元素 attrs 追加一个 CSS class（不去重，重复对浏览器无害）。"""
    existing = attrs.get('class', '')
    attrs['class'] = (existing + ' ' + class_name).strip()


def _apply_card_config(node, data_dict):
    """卡片配置：根据 card_layout 和 card_show_border 注入 CSS class。

    card_layout:
      - image_top（默认）：不额外加 class
      - image_left：.dg-list 加 dg-list--horizontal，.dg-card 加 dg-card--horizontal
      - image_right：.dg-list 加 dg-list--horizontal，.dg-card 加 dg-card--horizontal-reverse
    card_show_border:
      - false：.dg-card 加 dg-card--no-border
    """
    card_layout = data_dict.get('card_layout', '') if isinstance(data_dict, dict) else ''
    card_show_border = data_dict.get('card_show_border', '') if isinstance(data_dict, dict) else ''

    if not card_layout and not card_show_border:
        return

    _walk_card_config(node, card_layout, card_show_border)


def _walk_card_config(node, card_layout, card_show_border):
    """递归遍历节点树，给 dg-list / dg-card 注入排版和边框 class。"""
    if hasattr(node, 'attrs') and isinstance(node.attrs, dict):
        cls = node.attrs.get('class', '') or ''
        # 列表容器：水平布局时加 dg-list--horizontal（强制单列，全宽卡片）
        if 'dg-list' in cls:
            if card_layout in ('image_left', 'image_right'):
                _add_class(node.attrs, 'dg-list--horizontal')
        # 卡片：图文排版 + 边框
        if 'dg-card' in cls:
            if card_layout == 'image_left':
                _add_class(node.attrs, 'dg-card--horizontal')
            elif card_layout == 'image_right':
                _add_class(node.attrs, 'dg-card--horizontal-reverse')
            if str(card_show_border) == 'false':
                _add_class(node.attrs, 'dg-card--no-border')

    # 递归子节点
    children = getattr(node, 'nodes', None)
    if isinstance(children, list):
        for child in children:
            _walk_card_config(child, card_layout, card_show_border)


# data-filter-* 等业务属性中支持 {变量} 模板替换
_TEMPLATE_ATTRS = {'data-filter-id', 'data-filter-for', 'data-filter-empty', 'data-search-for'}


def _fill_business_attr_templates(node, context):
    """补扫业务属性中的 {变量} 模板（如 data-filter-id="{dataset}"）。

    与 _fill_static_href_templates 类似，但处理的是 data-filter-* 等非 href 属性。
    从 context['vars'] 取值填充；占位符无对应值则跳过（保持原样）。
    """
    vars_dict = (context or {}).get('vars') or {}
    for attr_name in _TEMPLATE_ATTRS:
        tmpl = node.attrs.get(attr_name)
        if tmpl and '{' in tmpl:
            filled = _fill_template(tmpl, vars_dict)
            if filled is not None:
                node.attrs[attr_name] = filled
    for child in node.children:
        _fill_business_attr_templates(child, context)


def _fill_static_href_templates(node, context):
    """全树补扫 data-href-template：填充仅依赖上下文变量的静态链接（如"查看全部"）。

    已有 href（项字段链接已填）的元素跳过；模板里有上下文之外的占位符（如 {slug}）
    时 _fill_template 返回 None 而跳过——故只会命中纯上下文链接。
    """
    tmpl = node.attrs.get('data-href-template')
    if tmpl and 'href' not in node.attrs:
        filled = _fill_template(tmpl, (context or {}).get('vars') or {})
        if filled:
            safe = _safe_href(filled)
            if safe:
                node.attrs['href'] = safe
    for child in node.children:
        _fill_static_href_templates(child, context)


def _schema_as_field(schema):
    """把根级 list/grid 的 schema 包装成 FieldDef，复用 _expand_list。"""
    return bp.FieldDef(
        name=schema.block_name,
        type=schema.root_type,
        tag=schema.root_tag,
        source=schema.source,
        page_size=schema.page_size,
        cols=schema.cols,
        children=schema.fields,
        item_template_html=schema.item_template_html,
    )
