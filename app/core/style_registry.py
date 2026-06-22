"""CSS 变量全局注册表.

data-* 改造方案的样式通道：模板作者把"可调样式"写成 CSS 变量，店主通过
预设选项（下拉/开关/调色板）调整，不输入自由数值、不碰代码。

设计要点（对齐 docs/docs/data-attributes-reference.md 第五节）：
- 按"变量"建表，不是按"block"建表。features 和 news 都用 cols → 共用一条。
- 默认值只写在模板 CSS 的 var(--xxx, 默认) 里，这里和 HTML 都不重复声明默认值。
  （理由：默认值多处声明必然不同步；CSS 是唯一真相源。）
- token 名 ↔ CSS 变量名一一对应，加 -- 前缀。data-style="dir" ↔ --dir。

后端用途：渲染器读元素的 data-style → 查本表确认是合法 token → 注入用户选的值
到 style 属性。前端用途：编辑器读本表生成对应控件（select/switch/color/image）。
"""

# 每个 token 一条。control 决定编辑器控件类型；css_var 是注入到 style 的变量名。
# select/switch 类型带 options（可选值），image/color 类型不需要 options。
STYLE_REGISTRY = {
    'cols': {
        'label': '每行个数',
        'control': 'select',
        'css_var': '--cols',
        'options': [
            {'value': '2', 'text': '2'},
            {'value': '3', 'text': '3'},
            {'value': '4', 'text': '4'},
            {'value': '5', 'text': '5'},
            {'value': '6', 'text': '6'},
        ],
    },
    'dir': {
        'label': '图文方向',
        'control': 'switch',
        'css_var': '--dir',
        'options': [
            {'value': 'row', 'text': '图左文右'},
            {'value': 'row-reverse', 'text': '图右文左'},
            {'value': 'column', 'text': '上图下文'},
        ],
    },
    'bg': {
        'label': '背景图',
        'control': 'image',
        'css_var': '--bg',
    },
    'bg-color': {
        'label': '背景色',
        'control': 'color',
        'css_var': '--bg-color',
    },
    'text-align': {
        'label': '文字对齐',
        'control': 'select',
        'css_var': '--text-align',
        'options': [
            {'value': 'left', 'text': '左对齐'},
            {'value': 'center', 'text': '居中'},
            {'value': 'right', 'text': '右对齐'},
        ],
    },
    # ── featured_picks（精选推荐）专用样式令牌（卡片布局已合并到 dir）──
    'card-gap': {
        'label': '卡片间距',
        'control': 'select',
        'css_var': '--card-gap',
        'options': [
            {'value': '0.75rem', 'text': '紧凑 (0.75rem)'},
            {'value': '1rem', 'text': '标准 (1rem)'},
            {'value': '1.5rem', 'text': '宽松 (1.5rem)'},
            {'value': '2rem', 'text': '特大 (2rem)'},
        ],
    },
    'card-bg': {
        'label': '卡片背景色',
        'control': 'color',
        'css_var': '--card-bg',
    },
    'font-color': {
        'label': '文字颜色',
        'control': 'color',
        'css_var': '--font-color',
    },
    'card-radius': {
        'label': '卡片圆角',
        'control': 'select',
        'css_var': '--card-radius',
        'options': [
            {'value': '0px', 'text': '无圆角'},
            {'value': '4px', 'text': '小 (4px)'},
            {'value': '8px', 'text': '中 (8px)'},
            {'value': '12px', 'text': '大 (12px)'},
            {'value': '16px', 'text': '特大 (16px)'},
        ],
    },
    'badge-bg': {
        'label': '角标背景色',
        'control': 'color',
        'css_var': '--badge-bg',
    },
    'badge-color': {
        'label': '角标文字色',
        'control': 'color',
        'css_var': '--badge-color',
    },
}


def get_style_def(token):
    """按 token 取注册表定义；未注册的 token 返回 None（渲染器据此跳过，不报错）。"""
    return STYLE_REGISTRY.get(token)


def css_var_for(token):
    """token → CSS 变量名（如 'cols' → '--cols'）。未注册返回 None。"""
    d = STYLE_REGISTRY.get(token)
    return d['css_var'] if d else None


def parse_style_tokens(raw):
    """解析 data-style 属性值（逗号分隔）为 token 列表，去空白。

    'cols, dir' → ['cols', 'dir']
    """
    if not raw:
        return []
    return [t.strip() for t in raw.split(',') if t.strip()]
