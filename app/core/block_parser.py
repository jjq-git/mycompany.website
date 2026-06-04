"""Block HTML 解析器：把声明式 block 模板解析成 schema.

data-* 改造方案 Phase 1 的核心模块之一。输入一段纯 HTML（block 的 template.html），
输出 BlockSchema —— 编辑器据此生成表单，渲染器据此注入数据。

为什么自己建 DOM 树：stdlib html.parser.HTMLParser 是流式的，只给 start/end/data
回调，拿不到父子关系。而"项模板 = 容器内带 data-name 的直接子元素"这条规范必须靠
父子关系判断，所以先用一个元素栈把 HTML 还原成轻量节点树，再在树上抽 schema。

只用 stdlib（html.parser），不引第三方解析库——遵循"依赖能少则少"。
"""
from dataclasses import dataclass, field
from html import escape
from html.parser import HTMLParser

from . import style_registry

# HTML 空元素（void elements）：没有结束标签，解析时遇到 start 即闭合。
# 不在此列表的标签即使写成自闭合 <x/> 也按需补处理。
VOID_TAGS = {
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
    'link', 'meta', 'param', 'source', 'track', 'wbr',
}

# 叶子内容类型：值直接存在元素上（innerText 或 src）。
LEAF_TYPES = {'text', 'textarea', 'richtext', 'image', 'video', 'audio', 'embed', 'icon'}
# 容器/可重复类型。
LIST_TYPES = {'list', 'grid'}


@dataclass
class _Text:
    """文本节点。data 保存原始片段（含未解码的 HTML 实体，convert_charrefs=False）。

    raw=True 表示富文本注入，序列化时原样输出不转义；否则按文本转义裸 < > &。
    """
    data: str
    raw: bool = False


@dataclass
class _Node:
    """解析中间产物：一棵轻量 DOM 树的节点。仅供 parser 内部使用。

    nodes 是**有序**的混合列表：元素子节点（_Node）和文本节点（_Text）按解析
    顺序排列。这样序列化能精确还原"文本与子元素交错"的原始顺序和空白——
    不能把文本和元素分开存（那会重排，破坏 inline 排版）。
    """
    tag: str
    attrs: dict = field(default_factory=dict)
    nodes: list = field(default_factory=list)  # 有序子节点：_Node | _Text
    self_closing: bool = False

    @property
    def children(self):
        """只取元素子节点（跳过文本），供字段解析遍历。"""
        return [n for n in self.nodes if isinstance(n, _Node)]

    @property
    def text(self):
        """元素内的直接文字（拼接所有文本节点，去首尾空白）。"""
        return ''.join(n.data for n in self.nodes if isinstance(n, _Text)).strip()


@dataclass
class FieldDef:
    """一个字段的定义（对应一个带 data-name 的元素）。"""
    name: str                      # data-name 值
    type: str                      # data-type 值
    tag: str                       # HTML 标签名
    default_text: str = ''         # 标签内默认文字（叶子文本类型用）
    default_src: str = ''          # 默认 src（媒体类型用）
    href_field: str = ''           # data-href 对应的字段名（空串=不可点）
    href_template: str = ''        # data-href-template：含 {占位符} 的链接模板（数据集项用）
    fallback: list = field(default_factory=list)  # data-fallback：本字段空时依次回退的备选 key
    hideable: bool = False         # 是否有 data-hideable
    style_tokens: list = field(default_factory=list)  # data-style 声明的合法 token
    source: str = None             # data-source 值（list/grid 用；None=未声明=手动）
    page_size: int = None          # data-page-size（list 用）
    cols: int = None               # data-cols（grid 用）
    children: list = field(default_factory=list)  # 子字段（group/list/grid 递归）
    item_template_html: str = None  # list/grid 的项模板原始 HTML（供渲染复制）


@dataclass
class BlockSchema:
    """一个 block 的完整 schema。"""
    block_name: str                # 根元素 data-name
    root_tag: str                  # 根标签
    root_type: str                 # 根 data-type（group/list/grid/...）
    hideable: bool = False
    style_tokens: list = field(default_factory=list)
    source: str = None
    page_size: int = None
    cols: int = None
    from_source: str = None            # data-from：数据来源路径（如 "settings:contact"）
    fields: list = field(default_factory=list)         # 顶层字段列表
    item_template_html: str = None                     # 根是 list/grid 时的项模板
    href_field: str = ''                               # 根元素若可点


class _DomBuilder(HTMLParser):
    """把 HTML 流还原成 _Node 树。维护一个元素栈处理父子关系。

    convert_charrefs=False：保留属性/文本里原始的 HTML 实体（&amp; &quot; 等），
    序列化时不会被解码后又裸写出去破坏 HTML（见 _serialize 的转义）。
    """

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = None
        self._stack = []

    def _append(self, child):
        if self._stack:
            self._stack[-1].nodes.append(child)
        elif isinstance(child, _Node) and self.root is None:
            self.root = child

    def handle_starttag(self, tag, attrs):
        node = _Node(tag=tag, attrs=dict(attrs))
        self._append(node)
        # void 元素没有结束标签，不入栈
        if tag.lower() not in VOID_TAGS:
            self._stack.append(node)

    def handle_startendtag(self, tag, attrs):
        # 显式自闭合 <x/>：建节点但不入栈
        self._append(_Node(tag=tag, attrs=dict(attrs), self_closing=True))

    def handle_endtag(self, tag):
        # 容错：找到栈中最近的同名标签弹出（应对未闭合的中间标签）
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i].tag.lower() == tag.lower():
                del self._stack[i:]
                break

    def handle_data(self, data):
        # script/style 内是 CDATA：HTMLParser 给的是原始未解析文本（含 < > &），
        # 必须原样输出不转义，否则会破坏 JS（如 a < b 变 a &lt; b）。
        in_cdata = bool(self._stack) and self._stack[-1].tag.lower() in ('script', 'style')
        self._append(_Text(data, raw=in_cdata))

    def handle_entityref(self, name):
        # convert_charrefs=False 下命名实体走这里：原样保留 &name;
        self._append(_Text(f'&{name};', raw=True))

    def handle_charref(self, name):
        # 数字字符引用：原样保留 &#...;
        self._append(_Text(f'&#{name};', raw=True))


def _serialize_attrs(attrs):
    """序列化属性。值统一转义（quote=True），无值属性输出裸名（如 hidden）。"""
    out = ''
    for k, v in attrs.items():
        if v is None:
            out += f' {k}'
        else:
            out += f' {k}="{escape(str(v), quote=True)}"'
    return out


def _serialize(node):
    """把 _Node 树重新序列化为 HTML 字符串。

    - 子节点按 nodes 的原始顺序输出（文本与元素交错不重排）
    - 属性值转义，无值属性保留（hidden）
    - 文本节点：raw（实体/富文本）原样输出，普通文本转义裸 < > &
    """
    attrs = _serialize_attrs(node.attrs)
    if node.tag.lower() in VOID_TAGS or node.self_closing:
        return f'<{node.tag}{attrs}>'
    inner = ''
    for child in node.nodes:
        if isinstance(child, _Text):
            inner += child.data if child.raw else escape(child.data, quote=False)
        else:
            inner += _serialize(child)
    return f'<{node.tag}{attrs}>{inner}</{node.tag}>'


def _direct_named_children(node):
    """返回 node 的"带 data-name 的直接子元素"。

    规范：list/grid 容器内带 data-name 的直接子元素 = 项模板。
    不带 data-name 的杂项（标题、"加载更多"按钮）会被跳过、不递归进去找。
    """
    result = []
    for child in node.children:
        if 'data-name' in child.attrs:
            result.append(child)
        else:
            # 中间包裹层（无 data-name）：向下找一层，应对 <ul><li data-name>结构
            result.extend(_direct_named_children(child))
    return result


def _int_or_none(raw):
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _item_children(item):
    """解析 list/grid 项模板的可编辑子字段（供编辑器生成条目子表单）。

    两种项形态：
    - 项根是 group（如 feature 卡片）：取其带 data-name 的直接子元素为子字段
    - 项根本身就是 leaf（如 logo 墙的 <img data-name="logo">）：项根自己即唯一子字段，
      渲染器走 _inject_root_leaf 不读 children，这里把它暴露出来纯粹是给编辑器用
    """
    if item.attrs.get('data-type', '') in LEAF_TYPES:
        return [_build_field(item)]
    return [_build_field(child) for child in _direct_named_children(item)]


def _build_field(node):
    """把一个带 data-name 的 _Node 转成 FieldDef，递归处理子字段。"""
    attrs = node.attrs
    dtype = attrs.get('data-type', '')
    fd = FieldDef(
        name=attrs.get('data-name', ''),
        type=dtype,
        tag=node.tag,
        href_field=attrs.get('data-href', '') or '',
        href_template=attrs.get('data-href-template', '') or '',
        fallback=[k.strip() for k in (attrs.get('data-fallback') or '').split(',') if k.strip()],
        hideable='data-hideable' in attrs,
        style_tokens=[
            t for t in style_registry.parse_style_tokens(attrs.get('data-style', ''))
            if style_registry.get_style_def(t)  # 只保留注册表里的合法 token
        ],
    )

    if dtype in LEAF_TYPES:
        # 叶子：文本类型存 innerText，媒体类型存 src
        if dtype in ('text', 'textarea', 'richtext', 'icon'):
            fd.default_text = node.text
        if dtype in ('image', 'video', 'audio', 'embed'):
            fd.default_src = attrs.get('src', '')
        return fd

    if dtype == 'group':
        # 复合项：递归解析子字段
        for child in _direct_named_children(node):
            fd.children.append(_build_field(child))
        return fd

    if dtype in LIST_TYPES:
        # 可重复列表/栅格
        fd.source = attrs.get('data-source', None)
        # data-source 存在但写成属性无值时，HTMLParser 给 None；规范里"存在即数据驱动"
        if 'data-source' in attrs and fd.source is None:
            fd.source = ''
        fd.page_size = _int_or_none(attrs.get('data-page-size'))
        fd.cols = _int_or_none(attrs.get('data-cols'))
        # 项模板 = 第一个带 data-name 的直接子元素
        items = _direct_named_children(node)
        if items:
            item = items[0]
            fd.item_template_html = _serialize(item)
            # 项模板内部的字段也解析出来（编辑器要用）
            fd.children.extend(_item_children(item))
        return fd

    # 未知/未声明 type 的带名元素：当文本叶子兜底
    fd.default_text = node.text
    return fd


def parse(html):
    """解析 block 模板 HTML，返回 BlockSchema。

    html: block 的 template.html 内容（纯 HTML，不含 Jinja2 标记）。
    """
    builder = _DomBuilder()
    builder.feed(html)
    builder.close()
    root = builder.root
    if root is None:
        raise ValueError('block 模板为空或无法解析出根元素')

    attrs = root.attrs
    schema = BlockSchema(
        block_name=attrs.get('data-name', ''),
        root_tag=root.tag,
        root_type=attrs.get('data-type', ''),
        hideable='data-hideable' in attrs,
        href_field=attrs.get('data-href', '') or '',
        style_tokens=[
            t for t in style_registry.parse_style_tokens(attrs.get('data-style', ''))
            if style_registry.get_style_def(t)
        ],
        from_source=attrs.get('data-from', None) or None,
    )

    root_type = schema.root_type
    if root_type in LIST_TYPES:
        schema.source = attrs.get('data-source', None)
        if 'data-source' in attrs and schema.source is None:
            schema.source = ''
        schema.page_size = _int_or_none(attrs.get('data-page-size'))
        schema.cols = _int_or_none(attrs.get('data-cols'))
        items = _direct_named_children(root)
        if items:
            item = items[0]
            schema.item_template_html = _serialize(item)
            schema.fields.extend(_item_children(item))
    else:
        # group 或其他：直接子字段
        for child in _direct_named_children(root):
            schema.fields.append(_build_field(child))

    return schema


def is_data_attr_block(html):
    """判断一段 block 模板是否为 data-* 声明式写法.

    判据（对齐方案 4.2）：含 Jinja2 标记（{% 或 {{）= 旧式命令式；
    否则视为纯 HTML 声明式。空内容当旧式处理（保守）。
    """
    if not html:
        return False
    if '{%' in html or '{{' in html:
        return False
    return 'data-name' in html
