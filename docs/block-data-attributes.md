# Block data-* 字段声明系统

用 HTML `data-*` 属性替代 `meta.yaml` 声明 Block 的可配置字段。template.html 同时承担 Schema 和 Render 两个角色。

## 一、核心机制

### 1.1 一句话原则

> `data-key` 给元素起名，`data-label-<css属性>` 声明可编辑的 CSS 字段，`<meta data-field>` 声明非 CSS 字段。系统扫描 template.html 自动生成后台表单。

### 1.2 字段 key 的生成规则

每个可编辑字段需要一个**全局唯一的 key**（对应 `module.data.<key>` 或 `item.<key>`）。

| 场景 | key 生成方式 | 示例 |
|---|---|---|
| 元素有 `data-key` | `<data-key>_<css属性>`（中划线转下划线） | `data-key="title"` + `font-size` → `title_font_size` |
| 元素有 `data-key`，CSS 属性含中划线 | 中划线全部转下划线 | `data-key="btn"` + `background-color` → `btn_background_color` |
| 元素无 `data-key` | 直接用 CSS 属性名（中划线转下划线） | `data-label-height` → `height` |
| `<meta data-field>` | 直接用 `data-field` 的值（不做转换） | `data-field="overlay_enabled"` → `overlay_enabled` |
| `data-repeat-item` 内部 | 同上（自动归入列表项的 item_fields） | `data-field="title"` → 列表项属性 `title` |

**冲突检查**（扫描时执行，冲突则报错）：
1. section 级所有 key 必须唯一（含 CSS 字段和 `<meta>` 字段之间）
2. 同一 `data-repeat` 内的 item 级 key 必须唯一
3. 不同 `data-repeat` 之间的 item 级 key 允许重复

### 1.3 字段归属：section 级 vs. item 级

归属由 `data-repeat-item` 决定，和 `{% for %}` 循环无关：

- **`data-repeat-item` 外部**的字段 → section 级（存于 `module.data.<key>`）
- **`data-repeat-item` 内部**的字段 → item 级（存于列表中每项的 `<key>`）

**`data-repeat-item` 的 DOM 深度规则**：`data-repeat-item` 必须是 `data-repeat` 容器的**直接子元素**（不包括被 Jinja2 `{% if %}` / `{% for %}` 包裹的情况——扫描器会跳过 Jinja2 控制标签，检查其内部的第一个 HTML 元素）。

```
正确：
<div data-repeat="slides">
  <div data-repeat-item> ... </div>
</div>

正确（含 Jinja2）：
<div data-repeat="slides">
  {% for item in items %}
  <div data-repeat-item> ... </div>
  {% endfor %}
</div>

错误：
<div data-repeat="slides">
  <div class="wrapper">
    <div data-repeat-item> ... </div>   ← 不是直接子元素，扫描器报错
  </div>
</div>
```

### 1.4 字段值回退规则

构建时，字段值的采用优先级：

```
用户保存的值（非空字符串） > 模板 style 中的默认值 > 空字符串（不输出该 CSS 属性）
```

具体行为：
- 用户填了值 → 用用户的值
- 用户从未编辑过该字段（key 不在 `module.data` 中）→ 用模板默认值
- 用户**主动清空**了字段（key 存在但值为 `""`）→ 该 CSS 属性不出现在输出中（不是回退到默认值）

实现方式：不使用 `or` 操作符（它会将空字符串视为 falsy），改用显式的 `get` + 判断：

```python
value = module_data.get(field_key)
if value is None:
    value = field_default  # 从未编辑过，用默认值
# value 可能是 ""（用户主动清空），保留它
```

模板侧（item 级）用 Jinja2 `default` filter：
```jinja2
{{ item.title_font_size | default('3rem') }}
```
`default` filter 只在变量为 `None` 或 `undefined` 时回退，不会把空字符串误判。

---

## 二、属性语法规范

### 2.1 data-key —— 元素标识符

给元素命名，作为其 CSS 字段的 key 前缀。

```html
<h1 data-key="title"
    style="font-size: 3rem; color: #ffffff;"
    data-label-font-size="标题字号"
    data-label-color="标题颜色">
```

→ 生成两个字段：`title_font_size`、`title_color`

**规则：**
- 值必须是合法的 Python 标识符（`[a-zA-Z_][a-zA-Z0-9_]*`），不能数字开头
- 同一 template.html 内 section 级的 `data-key` 值必须唯一
- `data-repeat-item` 内部的 `data-key` 只在其所属的 repeat 容器内要求唯一（不同 repeat 容器之间可以重复）
- 可选：不写 `data-key` 则 key 只用 CSS 属性名（仅适合全模板唯一的属性）

### 2.2 CSS 属性字段 —— `data-label-<css属性>`

标在已有 `style` 属性的 HTML 元素上，声明此 CSS 属性可编辑。

```html
<h1 data-key="title"
    style="font-size: 3rem; color: #ffffff;"
    data-label-font-size="标题字号"
    data-label-color="标题颜色"
    data-group-font-size="配色"
    data-group-color="配色"
    data-placeholder-font-size="如 3.5rem">
```

**属性列表：**

| 属性 | 必填 | 说明 |
|---|---|---|
| `data-label-<prop>` | **是** | 中文标签。有此属性才生成字段，没有则是固定样式 |
| `data-group-<prop>` | 否 | 分组名，同组属性归入同一折叠面板 |
| `data-placeholder-<prop>` | 否 | 输入框占位提示文字 |

**从 style 提取默认值：**

扫描器解析元素的 `style` 属性字符串，以 `;` 分隔后按 `:` 拆分为属性名和值。

```
style="font-size: 3rem; color: #ffffff;"
       ↓ 解析
{"font-size": "3rem", "color": "#ffffff"}
       ↓ 匹配 data-label-*
"font-size" → default="3rem"
"color"     → default="#ffffff"
```

- CSS 属性名匹配**大小写不敏感**
- 如果 `data-label-*` 对应的 CSS 属性在 `style` 中**找不到** → 扫描器报错，输出明确信息：`元素 <h1 data-key="title"> 的 style 中缺少 CSS 属性 "font-size"（data-label-font-size 要求）`
- 值可以包含空格（如 `rgba(255, 255, 255, 0.9)`）
- 值**不支持包含 `;` 字符**（分号是 CSS 分隔符）。如果确实需要（极少见），用 `<meta data-type="text">` 代替

**CSS 属性 → 表单控件类型映射：**

| CSS 属性 | 输出 type | 对应 admin JS 控件 |
|---|---|---|
| `color` | `color` | 颜色选择器 |
| `background-color` | `color` | 颜色选择器 |
| `border-color` | `color` | 颜色选择器 |
| `font-size` | `text` | 文本输入 |
| `font-weight` | `select` | 下拉（选项: normal, bold, 100~900 百位递增） |
| `line-height` | `text` | 文本输入 |
| `letter-spacing` | `text` | 文本输入 |
| `text-align` | `select` | 下拉（选项: left, center, right, justify） |
| `background-image` | `url` | URL 输入（配合图片预览） |
| `width`, `min-width`, `max-width` | `text` | 文本输入 |
| `height`, `min-height`, `max-height` | `text` | 文本输入 |
| `padding`, `padding-top`, `padding-right`, `padding-bottom`, `padding-left` | `text` | 文本输入 |
| `margin`, `margin-top`, `margin-right`, `margin-bottom`, `margin-left` | `text` | 文本输入 |
| `border-radius` | `text` | 文本输入 |
| `border-width` | `text` | 文本输入 |
| `background` | `text` | 文本输入（复合值整体作为一个字符串） |
| `display` | `select` | 下拉（选项: block, flex, grid, inline, inline-block, none） |
| 其他任意 CSS 属性 | `text` | 文本输入（兜底） |

**重要：** CSS 简写属性（如 `padding`）和其子属性（如 `padding-top`）是**独立字段**。声明了 `data-label-padding` 又声明 `data-label-padding-top` → 生成两个独立字段 `padding` 和 `padding_top`，互不干扰。模板作者自行保证不同时声明以避免混淆。

### 2.3 非 CSS 字段 —— `<meta data-field>`

用 `<meta>` 标签声明 CSS 无法表达的字段（URL、开关、下拉、文本内容）。`<meta>` 标签不参与页面渲染，构建时自动从输出中移除。

```html
<meta data-field="overlay_enabled"
      data-label="启用遮罩"
      data-type="select"
      data-options="启用:true, 不启用:false"
      data-default="true"
      data-group="遮罩层">
```

**属性列表：**

| 属性 | 必填 | 说明 |
|---|---|---|
| `data-field` | **是** | 字段 key |
| `data-label` | **是** | 中文标签 |
| `data-type` | **是** | 表单控件类型（见下表） |
| `data-default` | 否 | 默认值。不写则 key 不在初始数据中出现 |
| `data-group` | 否 | 分组名 |
| `data-placeholder` | 否 | 占位提示（仅 text / url / textarea / number 类型生效） |
| `data-options` | select 必填 | 格式见下方说明 |

**data-type 枚举及输出 type：**

| data-type | 输出 type | 表单控件 | 说明 |
|---|---|---|---|
| `text` | `text` | 单行文本输入 | |
| `textarea` | `textarea` | 多行文本输入 | |
| `url` | `url` | URL 输入 | |
| `number` | `number` | 数字输入 | |
| `select` | `select` | 下拉选择 | 必须配合 `data-options` |
| `toggle` | `select` | 下拉选择（true/false） | 本质上输出为 select，与现有 admin JS 兼容。如 admin JS 后续支持 toggle 开关控件，可升级 |
| `visibility` | `visibility` | 眼球开关按钮 | 用于控制页面元素的显隐（如"显示电话""显示邮箱"）。生成 visToggle 眼球图标 UI，值存储为 `"true"` / `"false"` |

**data-options 格式：**

```
data-options="显示文字1:值1, 显示文字2:值2"
```

- 每项格式：`显示文字:值`
- 项之间用 `, ` 分隔（逗号+一个空格）
- 标签和值中**不能包含 `:` 或 `, ` 字符**。如确实需要，用 Unicode 全角替代：`：`（U+FF1A）和 `，`（U+FF0C），扫描器自动还原
- 示例：`data-options="居中:center, 居左:left, 居右:right"` → 输出 `[{"label": "居中", "value": "center"}, ...]`

**`<meta>` 标签放置规则：**

- Section 级：放在 `<section>` 等根元素**之后**，`{% endif %}` 之前
- Item 级：放在 `data-repeat-item` 元素内部的**末尾**（所有可见 HTML 之后）
- 扫描器仅根据 DOM 位置（是否在 `data-repeat-item` 内）判断归属，`<meta>` 在 HTML 树中的具体顺序不影响字段排序

### 2.4 可重复列表 —— `data-repeat` + `data-repeat-item`

容器标记 `data-repeat`，模板项标记 `data-repeat-item`。`data-repeat-item` 内部的字段自动成为列表项的属性。

```html
<div data-repeat="slides"
     data-repeat-label="轮播媒体项"
     data-repeat-group="轮播内容">
  <div data-repeat-item>
    <div data-key="media_bg"
         style="background-image: url('');"
         data-label-background-image="媒体图片"></div>
    <meta data-field="type" data-label="媒体类型" data-type="select"
          data-options="图片:image, 视频:video" data-default="image">
    <meta data-field="media" data-label="媒体地址" data-type="url">
    <meta data-field="title" data-label="主标题" data-type="text">
  </div>
</div>
```

→ 生成一个列表字段 `slides`，每项的 `item_fields` 包含：`media_bg_background_image`、`type`、`media`、`title`

**规则：**
- `data-repeat` 值 = 列表字段 key（如 `slides` → `module.data.slides`）
- `data-repeat-label` = 列表的中文标签
- `data-repeat-group` = 分组名（可选）
- `data-repeat-item` 必须是 `data-repeat` 容器的直接子元素（见 1.3 的 DOM 深度规则）
- `data-repeat-item` 只能有一层（列表字段不支持嵌套子列表）
- `data-repeat-item` 内部的 `data-key` 命名空间独立，不会和 section 级或其他 repeat 容器冲突
- `<meta>` 标签在构建输出中自动移除

**多列表支持：** 一个 template.html 可以包含多个 `data-repeat` 容器（如 item_detail 同时有 images 列表和 specs 列表）。每个 `data-repeat` 有独立的 `data-repeat-item` 和字段命名空间，扫描器通过 `data-repeat` 的值（listKey）区分它们。同一 template 内不同 `data-repeat` 的值必须唯一。

### 2.5 响应式控件声明 —— `data-no-resp`

部分 Block（如 hero_banner 轮播）虽有列表但不适合展示"每行列数""每页数量"等响应式网格控件。在根元素上声明 `data-no-resp` 即可禁用：

```html
<section data-no-resp ...>
```

**自动检测规则：**

```
模板中存在 data-repeat 容器？
├── 是 → 根元素有 data-no-resp？
│        ├── 是 → 不显示响应式覆写控件
│        └── 否 → 显示响应式覆写控件（columns + items_per_page）
└── 否 → 不显示响应式覆写控件
```

当前需要 `data-no-resp` 的 Block 仅 hero_banner 一个（它有 slides 列表但是轮播，不是网格）。其余无 `data-repeat` 的 Block（section_title、text_content、highlight_card、item_detail）自动不显示响应式控件，无需声明。

扫描器将 `data-no-resp` 的存在记录为字段定义中的一个布尔标记（`"no_responsive": true`），传给前端。这不是用户可编辑的字段。

---

## 三、扫描器实现规范

### 3.1 文件：`app/core/block_scanner.py`

### 3.2 解析策略

扫描器读取**原始 template.html**（含 Jinja2 标签），用 Python 标准库 `html.parser` 解析。

**对待 Jinja2 的策略：**

`html.parser` 将 `{% %}` 和 `{{ }}` 视为未知标签。测试表明：
- `{% for %}`, `{% if %}` 等 → 解析器将其作为未知开始标签，内部节点正常解析
- `{% endif %}`, `{% endfor %}` 等 → 解析器将其作为未知结束标签
- `{{ variable }}` → 解析器将其作为 data 节点（文本）
- `{# comment #}` → 解析器将其作为注释（忽略）

这意味着 `{% for %}` 内部的 `data-*` 属性可以被正常提取，无需特殊处理。

**扫描步骤：**

```
1. 读入 template.html 全文
2. 用 html.parser 构建 DOM 树
3. 第一遍遍历：定位所有 data-repeat 容器
4. 第二遍遍历：定位 data-repeat 的直接子元素中的 data-repeat-item
   - 中间隔着 {% for %} / {% if %} 等 Jinja2 控制标签的，跳过它们检查其内部
5. 第三遍遍历：对每个 HTML 元素
   a. 判断归属（section 级 / 哪个 data-repeat 的 item 级）
   b. 有 data-key + 有 data-label-* → 收集 CSS 字段
   c. 无 data-key 但有 data-label-* → CSS 字段，key 直接是 CSS 属性名
   d. 是 <meta data-field> → 收集非 CSS 字段
6. 第四遍：生成字段 key 并去重
   - 同 scope 内 key 不得重复
   - 不同 scope 重复是合法的
7. 输出字段定义 dict
```

### 3.3 输出格式

扫描器返回与现有 `meta.yaml` **完全兼容**的 dict：

```python
{
    "name": "Hero Banner",
    "category": "content",
    "icon": "hero_banner.svg",
    "description": "首页轮播大图模块，支持图片/视频",
    "fields": [
        # --- section 级 CSS 字段 ---
        {"key": "section_height", "label": "Banner 整体高度", "type": "text",
         "group": "外层样式", "default": "77vh",
         "placeholder": "如 500px 或 77vh", "_css_prop": "height", "_data_key": "section"},
        {"key": "section_max_width", "label": "Banner 最大宽度", "type": "text",
         "group": "外层样式", "default": "100%",
         "placeholder": "如 100%", "_css_prop": "max-width", "_data_key": "section"},

        # --- section 级非 CSS 字段 ---
        {"key": "overlay_enabled", "label": "启用遮罩", "type": "select",
         "group": "遮罩层", "default": "true",
         "options": [{"value": "true", "label": "启用"}, {"value": "false", "label": "不启用"}]},
        {"key": "banner_align", "label": "内容排版", "type": "select",
         "group": "外层样式", "default": "center",
         "options": [{"value": "center", "label": "居中"},
                     {"value": "left", "label": "居左"},
                     {"value": "right", "label": "居右"}]},

        # --- 列表字段 ---
        {"key": "slides", "label": "轮播媒体项", "type": "list",
         "group": "轮播内容", "item_label": "媒体项",
         "item_fields": [
             # item 级 CSS 字段
             {"key": "title_font_size", "label": "标题字号", "type": "text",
              "default": "3rem", "placeholder": "如 3.5rem", "_css_prop": "font-size", "_data_key": "title"},
             {"key": "title_color", "label": "标题颜色", "type": "color",
              "default": "#ffffff", "_css_prop": "color", "_data_key": "title"},
             # item 级非 CSS 字段
             {"key": "type", "label": "媒体类型", "type": "select",
              "default": "image",
              "options": [{"value": "image", "label": "图片"},
                          {"value": "video", "label": "视频"}]},
             {"key": "media", "label": "媒体地址", "type": "url"},
             {"key": "title", "label": "主标题", "type": "text"},
         ]},
    ]
}
```

**输出格式说明：**
- `_css_prop`：内部标记，记录原始 CSS 属性名（中划线格式，如 `max-width`），供 `styles()` 在拼接 style 字符串时使用。不传给前端
- `_data_key`：内部标记，记录该字段所属的 `data-key` 值（如 `content`、`section`、`title`），供 `styles()` 按元素分组样式。不传给前端。**扫描器直接从 HTML 元素的 `data-key` 属性读取，不靠字符串推导**（因为 `rsplit('_', 1)` 对 `max-width`、`background-color` 等多段 CSS 属性名会拆分错误）
- 字段顺序：section 级字段按模板中出现顺序，然后是列表字段
- `name` 提取：从 template.html 中第一个 `{# ... #}` Jinja2 注释提取；兜底用目录名（`hero_banner` → `Hero Banner`）
- `description` 提取：同上注释的第二句；兜底为空字符串
- `category` 和 `icon`：从同级目录结构继承（`blocks/<name>/` 下的 svg 文件），兜底 `"content"` 和空字符串
- `no_responsive`：布尔标记，当根元素有 `data-no-resp` 时为 `true`，否则省略

### 3.4 默认值提取细节

```python
def parse_style_defaults(style_str: str, target_props: list[str]) -> dict[str, str]:
    """
    style="font-size: 3rem; color: #fff;"
    target_props=["font-size", "color"]
    → {"font-size": "3rem", "color": "#fff"}
    """
```

- 以 `;` 切分，再以 `:` 拆 key/value（仅拆分第一个 `:`）
- 属性名 trim 后**小写化**再匹配
- 值 trim 后保留原样（不去引号、不展开简写）
- `data-label-*` 对应的 CSS 属性在 `style` 中不存在 → 扫描器报错
- 属性值中**不能包含 `;`**（CSS 分隔符），但可以包含 `:`（如 `url('https://...')`）

---

## 四、构建器注入规范

### 4.1 涉及文件

`app/core/builder.py` —— 修改 `build_site()` 和 `build_template_preview()` 两个函数，各自注册 Jinja2 全局函数
`app/core/block_styles.py` —— 新增，样式预计算 + 输出清理
`app/core/template_loader.py` —— 新增 `load_all_block_fields()` 方法，加载模板下所有 block 的字段定义

### 4.2 设计原则

| 样式类型 | 注入方式 | 原因 |
|---|---|---|
| Section 级 CSS | Python `styles(module)` 预计算，`{{ s.<data_key> }}` | 一次计算，所有迭代共享 |
| Item 级 CSS | 模板内 `{{ item.<key> \| default('默认值') }}` | 每项数据独立 |
| 非 CSS 字段 | 模板内 `{{ }}` 直接输出 | 本就是数据，不是样式 |

### 4.3 `styles(module)` —— Section 级样式预计算

**注册机制：**

builder.py 在创建 Jinja2 Environment 后，从 `template_loader` 加载当前模板所有 block 的字段定义，缓存到模块级变量，再注册 `styles` 和 `strip_schema` 全局函数。

```python
# builder.py
from app.core.block_styles import (
    set_block_fields_cache,
    compute_section_styles,
    strip_schema_output,
)

# 在 build_site() 和 build_template_preview() 中：
block_fields = template_loader.load_all_block_fields(template_name)
set_block_fields_cache(block_fields)
# lambda 捕获当前模板的 settings，传给 compute_section_styles
env.globals['styles'] = lambda md: compute_section_styles(md, settings)
env.globals['strip_schema'] = lambda html: strip_schema_output(html)
```

**`compute_section_styles` 实现：**

```python
# block_styles.py
_block_fields_cache: dict[str, list[dict]] = {}

def set_block_fields_cache(cache: dict[str, list[dict]]):
    _block_fields_cache.clear()
    _block_fields_cache.update(cache)

def compute_section_styles(module: dict, settings: dict = None) -> 'StyleProxy':
    """
    输入: module 对象（含 type 和 data）+ 全局 settings（可选，用于 global_width 回退）
    输出: StyleProxy，支持 .<element_data_key> 访问完整 style 字符串
    
    module = {"type": "hero_banner", "data": {"section_height": "80vh", ...}}
    s = compute_section_styles(module, settings)
    s.section → "height: 80vh; max-width: 100%; padding: 2rem 0; background: transparent;"
    """
    block_type = module.get('type', '')
    data = module.get('data', {}) if isinstance(module, dict) else {}
    fields = _block_fields_cache.get(block_type, [])
    
    # 按 data_key 分组 section 级 CSS 字段
    groups: dict[str, list[dict]] = {}
    for f in fields:
        if f.get('type') == 'list':
            continue  # 跳过列表字段
        css_prop = f.get('_css_prop')
        if not css_prop:
            continue  # 非 CSS 字段
        data_key = f.get('_data_key', '')  # 由扫描器在解析时从 HTML data-key 属性读取
        if not data_key:
            data_key = '__root__'  # 无 data-key 的元素归入 root 组
        if data_key not in groups:
            groups[data_key] = []
        groups[data_key].append((css_prop, f))
    
    # 拼接 style 字符串
    styles: dict[str, str] = {}
    for data_key, props in groups.items():
        parts = []
        for css_prop, field in props:
            value = data.get(field['key'])
            if value is None:
                value = field.get('default', '')
            if value:
                parts.append(f'{css_prop}: {value};')
        styles[data_key] = ' '.join(parts)
    
    return StyleProxy(styles)


class StyleProxy:
    def __init__(self, styles: dict[str, str]):
        self._styles = styles
    
    def __getattr__(self, key: str) -> str:
        return self._styles.get(key, '')
    
    def __getitem__(self, key: str) -> str:
        return self._styles.get(key, '')
```

**关键设计：`_data_key` 由扫描器在解析时从 HTML 元素的 `data-key` 属性直接读取**，不靠 `rsplit` 反推。这避免了多段 CSS 属性名（如 `max-width` → `max_width`）被错误拆分的问题。

例如：`<div data-key="content" style="max-width: 900px;" data-label-max-width="内容区宽度">` → 字段 key = `content_max_width`，`_data_key` = `"content"`，`_css_prop` = `"max-width"`。

由于 `_data_key` 直接从 `data-key` 属性复制，**`data-key` 值不再受"不能含下划线"的限制**。但为保持一致性和可读性，仍建议使用纯字母数字命名。

### 4.4 Item 级样式 —— 模板内 default filter

```jinja2
{% for item in items %}
<h1 style="font-size: {{ item.title_font_size | default('3rem') }};
           color: {{ item.title_color | default('#ffffff') }};">
  {{ item.title }}
</h1>
{% endfor %}
```

用 `| default(...)` 而非 `or`，因为 `default` 只在变量为 `None`/`undefined` 时回退，不会把空字符串吃掉的。默认值手写，与元素 `style` 属性中的值保持一致（模板作者自行负责对齐）。

**注意事项：**
- `default` 过滤器**不处理空字符串**：用户主动清空字段 → `item.<key>` 为空字符串 → `default` 不触发 → 输出空值（CSS 属性不生效）。这是正确的行为——与 §1.4 的字段值回退规则一致
- `default` 过滤器**不处理布尔 false**：`{{ item.show_phone | default('true') }}` 中，如果 `show_phone` 是字符串 `"false"`，`default` 不触发（字符串非空）；如果 `show_phone` 存储为布尔 `false`，Jinja2 认为 `false` 是已定义的值，`default` 也不触发。`visibility` 类型存储字符串 `"true"` / `"false"`，因此用 `{% if item.show_phone != 'false' %}` 做条件判断而非 `| default`
- URL 字段用 `| default('')` 防止输出 `None`：`{{ item.media | default('') }}` 确保未填写时 URL 为空字符串而非 `"None"`

### 4.5 输出清理

渲染完成后对整页 HTML 做两轮正则清理：

```python
import re

# 第一轮：移除 <meta data-field> 标签
META_FIELD_RE = re.compile(r'<meta\s+data-field[^>]*/?>', re.IGNORECASE)

# 第二轮：移除有值的 Schema 专用属性
SCHEMA_ATTR_RE = re.compile(
    r'\s+('
    r'data-label-[a-zA-Z0-9\-]+|'
    r'data-group-[a-zA-Z0-9\-]+|'
    r'data-placeholder-[a-zA-Z0-9\-]+|'
    r'data-key|'
    r'data-repeat|'
    r'data-repeat-item|'
    r'data-repeat-label|'
    r'data-repeat-group'
    r')="[^"]*"',
    re.IGNORECASE
)

# 第三轮：移除无值的布尔 Schema 属性
SCHEMA_BOOL_ATTR_RE = re.compile(r'\s+data-no-resp\b', re.IGNORECASE)

def strip_schema_output(html: str) -> str:
    html = META_FIELD_RE.sub('', html)
    html = SCHEMA_ATTR_RE.sub('', html)
    html = SCHEMA_BOOL_ATTR_RE.sub('', html)
    return html
```

调用位置：`builder.py` 的 `_render_for_language()` 中，`rendered = tpl.render(**ctx)` 之后、写入文件之前。

### 4.6 `load_all_block_fields()` —— 加载模板全部 block 字段定义

`template_loader.py` 新增方法，builder.py 调用它获取当前模板所有 block 的字段定义，用于初始化 `_block_fields_cache`。

```python
# app/core/template_loader.py

def load_all_block_fields(self, template_name: str) -> dict[str, list[dict]]:
    """
    加载指定模板下所有 block 的字段定义。
    
    返回: {block_type: [field_dict, ...], ...}
    例: {"hero_banner": [...], "feature_grid": [...], ...}
    
    流程:
    1. 遍历 site_templates/<template_name>/blocks/ 下的所有子目录
    2. 对每个 block，读取 template.html
    3. 检测是否有 data-label-* 或 <meta data-field>：
       - 是 → 调用 block_scanner.scan_template(html_path) 提取字段
       - 否 → 读取 meta.yaml（旧方式）
    4. 汇总为 {block_type: fields} dict
    """
    blocks_dir = os.path.join(self.template_dir, 'blocks')
    result = {}
    for block_name in os.listdir(blocks_dir):
        block_path = os.path.join(blocks_dir, block_name)
        if not os.path.isdir(block_path):
            continue
        html_path = os.path.join(block_path, 'template.html')
        if not os.path.exists(html_path):
            continue
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()
        if _has_data_attributes(html):
            fields = scan_template_html(html, block_name)
        else:
            fields = self._read_meta_yaml(block_path)
        result[block_name] = fields
    return result
```

**缓存策略：** builder.py 在每个 build 周期开始时调用一次 `load_all_block_fields()`，结果缓存到 `block_styles._block_fields_cache`。同一模板的不同页面构建复用此缓存。切换模板时重新加载。

### 4.7 Section 级样式注入模式

Section 级样式在 template.html 中采用 **"默认值 + `{{ s.<data_key> }}` 追加"** 模式：

```html
<section style="height: 77vh; max-width: 100%; {{ s.section }}"
         data-key="section"
         data-label-height="Banner 整体高度"
         data-label-max-width="Banner 最大宽度">
```

**为什么是追加而非替换：**
- 扫描器需要从 `style` 属性中读取 CSS 默认值（`height: 77vh` → default=`"77vh"`）
- 如果用 `style="{{ s.section }}"` 完全替换，扫描器无法从 Jinja2 表达式提取默认值
- 追加模式：`{{ s.section }}` 输出用户修改的值，CSS 级联使后面的值覆盖前面的默认值
- 用户未修改字段时，`s.section` 返回空字符串（`StyleProxy` 只在有非空值时才输出），不产生覆盖

**Item 级样式不用此模式** —— Item 级数据每项独立，直接用 `{{ item.<key> | default('默认值') }}` 逐属性输出即可。

---

## 五、完整示例：hero_banner 改造

### 5.1 改造后的 template.html

```html
{# Hero Banner 模块 - 全屏轮播。支持图片/视频，可配置标题、副标题、按钮。 #}
{% set items = module.data.slides or [] %}
{% if items %}

{% set s = styles(module) %}

<section class="section hero-banner" id="heroBanner"
         style="height: 77vh; max-width: 100%;
                padding: 0; background: transparent;
                {{ s.section }}"
         data-no-resp
         data-key="section"
         data-label-height="Banner 整体高度"
         data-label-max-width="Banner 最大宽度"
         data-label-padding-top="上内边距"
         data-label-padding-right="右内边距"
         data-label-padding-bottom="下内边距"
         data-label-padding-left="左内边距"
         data-label-background="Banner 背景"
         data-placeholder-height="如 500px 或 77vh"
         data-placeholder-background="如 #f5f5f5 或 url(...)">

  <div class="container" style="height: 100%; max-width: none;">
    <div class="hero-banner-slides"
         data-repeat="slides"
         data-repeat-label="轮播媒体项"
         data-repeat-group="轮播内容">

      {% for item in items %}
      <div class="hero-banner-slide{% if loop.first %} active{% endif %}"
           data-repeat-item>

        <div class="hero-banner-media">
          {% if item.type == 'video' %}
          <video class="hero-banner-video"
                 src="{{ item.media | default('') }}"
                 autoplay muted loop playsinline></video>
          {% else %}
          <div class="hero-banner-image"
               style="background-image: url('{{ item.media | default('') }}')"></div>
          {% endif %}
        </div>

        {% if module.data.overlay_enabled != 'false' %}
        <div class="hero-banner-overlay"></div>
        {% endif %}

        <div class="hero-banner-content"
             style="max-width: {{ item.content_max_width | default('900px') }};
                    {% if module.data.banner_align == 'left' -%}
                    left: 5%; transform: translateY(-50%); text-align: left;
                    {%- elif module.data.banner_align == 'right' -%}
                    left: auto; right: 5%; transform: translateY(-50%); text-align: right;
                    {%- else -%}
                    left: 50%; transform: translate(-50%, -50%); text-align: center;
                    {%- endif %}"
             data-key="content"
             data-label-max-width="内容区宽度"
             data-placeholder-max-width="如 1200px">

          {% if item.title %}
          <h1 class="hero-banner-title"
              style="font-size: {{ item.title_font_size | default('3rem') }};
                     color: {{ item.title_color | default('#ffffff') }};"
              data-key="title"
              data-label-font-size="标题字号"
              data-label-color="标题颜色">{{ item.title }}</h1>
          {% endif %}

          {% if item.subtitle %}
          <p class="hero-banner-subtitle"
             style="font-size: {{ item.subtitle_font_size | default('1.25rem') }};
                    color: {{ item.subtitle_color | default('rgba(255,255,255,0.9)') }};"
             data-key="subtitle"
             data-label-font-size="副标题字号"
             data-label-color="副标题颜色">{{ item.subtitle }}</p>
          {% endif %}

          <div class="hero-banner-actions">
            {% if item.primaryBtn %}
            <a href="{{ item.primaryBtnLink | default('#') }}"
               {% if item.primaryBtnLinkTarget == '_blank' %}target="_blank" rel="noopener"{% endif %}
               class="btn btn-primary btn-lg"
               style="font-size: {{ item.btn_font_size | default('1rem') }};
                      color: {{ item.btn_text_color | default('#ffffff') }};
                      background-color: {{ item.btn_bg | default('#067a7a') }};"
               data-key="btn"
               data-label-font-size="按钮字号"
               data-label-color="按钮文字色"
               data-label-background-color="按钮背景色">{{ item.primaryBtn }}</a>
            {% endif %}
            {% if item.secondaryBtn %}
            <a href="{{ item.secondaryBtnLink | default('#') }}"
               class="btn btn-secondary btn-lg">{{ item.secondaryBtn }}</a>
            {% endif %}
          </div>
        </div>

        <meta data-field="type" data-label="媒体类型" data-type="select"
              data-options="图片:image, 视频:video" data-default="image">
        <meta data-field="media" data-label="媒体地址" data-type="url">
        <meta data-field="title" data-label="主标题" data-type="text">
        <meta data-field="subtitle" data-label="副标题" data-type="text">
        <meta data-field="primaryBtn" data-label="主按钮文字" data-type="text">
        <meta data-field="primaryBtnLink" data-label="主按钮链接" data-type="url">
        <meta data-field="primaryBtnLinkTarget" data-label="新窗口打开" data-type="select"
              data-options="是:_blank, 否:" data-default="">
        <meta data-field="secondaryBtn" data-label="副按钮文字" data-type="text">
        <meta data-field="secondaryBtnLink" data-label="副按钮链接" data-type="url">
      </div>
      {% endfor %}
    </div>
  </div>

  {% if items|length > 1 %}
  <div class="hero-banner-dots">
    {% for item in items %}
    <button class="hero-banner-dot{% if loop.first %} active{% endif %}"
            data-slide="{{ loop.index0 }}"
            aria-label="Slide {{ loop.index }}"></button>
    {% endfor %}
  </div>
  <button class="hero-banner-nav hero-banner-nav-prev" aria-label="Previous">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="2">
      <polyline points="15 18 9 12 15 6"/>
    </svg>
  </button>
  <button class="hero-banner-nav hero-banner-nav-next" aria-label="Next">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="2">
      <polyline points="9 18 15 12 9 6"/>
    </svg>
  </button>
  {% endif %}
</section>

<meta data-field="overlay_enabled" data-label="启用遮罩"
      data-type="select" data-options="启用:true, 不启用:false"
      data-default="true" data-group="遮罩层">
<meta data-field="banner_align" data-label="内容排版"
      data-type="select" data-options="居中:center, 居左:left, 居右:right"
      data-default="center" data-group="外层样式">

{% endif %}

<script>
(function() {
  var banner = document.getElementById('heroBanner');
  if (!banner) return;
  var slides = banner.querySelectorAll('.hero-banner-slide');
  var dots = banner.querySelectorAll('.hero-banner-dot');
  var prevBtn = banner.querySelector('.hero-banner-nav-prev');
  var nextBtn = banner.querySelector('.hero-banner-nav-next');
  var current = 0;
  var total = slides.length;
  if (total <= 1) return;

  function showSlide(index) {
    slides.forEach(function(s, i) { s.classList.toggle('active', i === index); });
    dots.forEach(function(d, i) { d.classList.toggle('active', i === index); });
    current = index;
  }
  function next() { showSlide((current + 1) % total); }
  function prev() { showSlide((current - 1 + total) % total); }
  if (prevBtn) prevBtn.addEventListener('click', prev);
  if (nextBtn) nextBtn.addEventListener('click', next);
  dots.forEach(function(dot) {
    dot.addEventListener('click', function() {
      showSlide(parseInt(dot.getAttribute('data-slide')));
    });
  });
  setInterval(next, 8000);
})();
</script>
```

### 5.2 与当前模板的对比

| 指标 | 当前 template.html | 改造后 |
|---|---|---|
| 行数 | 141 | ~100 |
| `{% set %}` 样式拼接 | 15+ 处 | 0 处（全部移到 Python 或 eliminated） |
| `{% if %}` / `{% for %}` | 各 3 处 | 各 4~5 处（轻微增加，仅用于控制流） |
| 样式计算逻辑 | Jinja2 中拼接字符串 | Section 级：Python `styles()`；Item 级：`\| default(...)` |
| 字段定义位置 | meta.yaml（142 行，独立文件） | template.html 内 data-* 属性 |
| 文件数量 | 2 | 1 |
| 新增字段成本 | 改 template.html + 改 meta.yaml | 只在元素上加 `data-label-*` |

### 5.3 改造要点总结

1. **Section 级样式**：`<section data-key="section">` 上的 height / max-width / padding / background → `styles(module).section` 返回完整 style 字符串
2. **Item 级 CSS 样式**：`data-key="title"` 在 `data-repeat-item` 内 → 每项独立存储 `title_font_size`、`title_color`
3. **Item 级内容字段**：`<meta data-field="title">`、`<meta data-field="media">` 等声明在 `data-repeat-item` 内末尾
4. **Section 级非 CSS 字段**：`overlay_enabled`、`banner_align` 用 `<meta>` 声明在 `</section>` 之后
5. **复杂条件样式（banner_align）**：保留在模板中用最小 Jinja2 `{% if %}` 处理（控制多个 CSS 属性，不适合简化为单个 text-align）

---

## 六、错误处理规范

扫描器遇到以下情况时**必须报错**（抛出 `BlockScannerError`），给出文件路径 + 行号 + 明确信息：

| 错误场景 | 错误信息格式 |
|---|---|
| `data-label-*` 对应的 CSS 属性不在元素 `style` 中 | `hero_banner/template.html L42: <h1 data-key="title"> 的 style 中缺少 "line-height"（data-label-line-height 要求）` |
| section 级 `data-key` 值重复 | `hero_banner/template.html L10 和 L35: data-key "title" 重复（section 级必须唯一）` |
| section 级字段 key 重复（含 CSS vs meta 冲突） | `hero_banner/template.html: 字段 key "overlay_enabled" 在 L52 <meta> 和 L15 <div data-key="overlay"> 产生冲突` |
| data-repeat-item 内 `data-key` 值重复 | `hero_banner/template.html L60: data-repeat-item 内 data-key "title" 重复` |
| `data-repeat-item` 不是 `data-repeat` 的直接子元素 | `hero_banner/template.html L30: data-repeat-item 必须是 data-repeat 的直接子元素（当前嵌套在 <div class="wrapper"> 内）` |
| `data-repeat` 内找不到 `data-repeat-item` | `hero_banner/template.html L25: data-repeat="slides" 容器内缺少 data-repeat-item` |
| `<meta data-type="select">` 缺少 `data-options` | `hero_banner/template.html L80: <meta data-field="type" data-type="select"> 缺少 data-options` |
| `data-options` 格式无法解析 | `hero_banner/template.html L80: data-options 格式错误，期望 "标签:值, 标签:值"，得到 "图片image,视频"` |
| `<meta>` 缺少必填属性 | `hero_banner/template.html L55: <meta data-field="xxx"> 缺少 data-type` |
| CSS 属性值包含 `;` | `hero_banner/template.html L42: <h1 data-key="title"> 的 style 值包含 ";" 字符，不支持` |

---

## 七、向后兼容策略

### 7.1 检测逻辑

```python
def _has_data_attributes(html: str) -> bool:
    """检测 template.html 是否使用 data-* 声明方式。"""
    return bool(
        re.search(r'data-label-[a-zA-Z0-9\-]+\s*=', html)
        or re.search(r'<meta\s+data-field\s*=', html)
    )
```

### 7.2 回退规则

```
template.html 存在？
├── 是 → 含 data-label-* 或 <meta data-field>？
│        ├── 是 → 用 block_scanner 扫描（新方式），忽略 meta.yaml
│        └── 否 → meta.yaml 存在？
│                  ├── 是 → 读 meta.yaml（旧方式）
│                  └── 否 → fields = []（纯静态 block）
└── 否 → meta.yaml 存在？
          ├── 是 → 读 meta.yaml
          └── 否 → fields = []
```

### 7.3 渐进迁移

- 新旧方式可在同一模板的不同 block 中共存
- 一个 block 迁移后删除其 `meta.yaml`
- 如果同时存在 data-* 和 `meta.yaml`：**只用 data-*，不合并**，并在日志中输出 info 提示忽略 meta.yaml

### 7.4 `template_loader.py` 修改清单

现有 `scan_blocks()` 方法（`app/core/template_loader.py`）只读 meta.yaml。需要修改为兼容新方式：

**1. `scan_blocks()` 方法改造：**

```python
def scan_blocks(self, template_name: str) -> dict:
    """
    扫描模板下所有 block，返回 {block_type: {name, category, icon, fields, ...}, ...}
    
    改造点：
    - 读取 template.html 后调用 _has_data_attributes() 检测
    - 有 data-* → 调用 block_scanner.scan_template_html() 提取字段
    - 无 data-* → 按原逻辑读 meta.yaml
    """
```

**2. 新增 `load_all_block_fields()` 方法**（详见 §4.6），供 builder.py 调用。

**3. 新增 `_has_data_attributes()` 辅助函数**（见 §7.1），放在 template_loader.py 模块级别。

**4. 导入 block_scanner：**
```python
from app.core.block_scanner import scan_template_html, BlockScannerError
```

**修改原则：** `scan_blocks()` 的调用方（routes.py 的 `scan_templates` 命令等）不感知新旧方式差异——它们只拿到字段定义 dict，不关心来源是 data-* 还是 meta.yaml。

---

## 八、迁移操作清单

### 8.1 迁移前备份（必须第一步执行）

备份分两阶段：**基础设施备份**（一次性）和 **Block 模板备份**（每个 Block 迁移前）。

#### 阶段一：基础设施备份（开始写任何代码之前，一次性完成）

以下 6 个共享文件会被大幅修改，**必须在开始任何迁移代码之前一次性全部备份**：

| 文件 | 改动内容 | 风险 |
|---|---|---|
| `app/static/js/admin_modules.js` | 删除 per-block 硬编码分支，新增 `renderListEditor()`，增强 `renderField()` | 高：影响所有 14 个 Block 的后台编辑 |
| `app/templates/dashboard/panel_page_edit.html` | 删除 per-block Jinja2 分支 (~1144行) + `addModule()` 分支 (~850行) | 高：影响页面编辑的渲染和新增模块 |
| `app/core/routes.py` | `_parse_modules_form()` 改为数据驱动，删除 6 种 Block 的硬编码列表解析 | 高：影响所有模块的表单提交 |
| `app/core/builder.py` | 注册 `styles()` / `strip_schema` 全局函数，添加 `_normalize_module_data()` 调用 | 中：影响所有站点的构建输出 |
| `app/core/template_loader.py` | `scan_blocks()` 改造，新增 `load_all_block_fields()` | 中：影响模板扫描和字段加载 |
| `site_templates/dengtec/templates/_modules.html` | 简化 `module.type == 'hero_banner'` 硬编码兼容判断 | 低：单行改动，但影响所有模块渲染 |

备份命令（在项目根目录执行）：

```bash
cp app/static/js/admin_modules.js app/static/js/admin_modules.js.bak
cp app/templates/dashboard/panel_page_edit.html app/templates/dashboard/panel_page_edit.html.bak
cp app/core/routes.py app/core/routes.py.bak
cp app/core/builder.py app/core/builder.py.bak
cp app/core/template_loader.py app/core/template_loader.py.bak
cp site_templates/dengtec/templates/_modules.html site_templates/dengtec/templates/_modules.html.bak
```

**基础设施回滚：** 如果基础设施改动导致问题，用 `.bak` 文件覆盖回原文件即可恢复。git 也可用，但 `.bak` 保证拿到的是迁移前的精确版本（不受后续 git 操作影响）。

#### 阶段二：Block 模板备份（每个 Block 迁移前）

```
blocks/<block名>/template.html      →  blocks/<block名>/template.html.bak
blocks/<block名>/meta.yaml           →  blocks/<block名>/meta.yaml.bak
```

```bash
# 在 block 目录下执行
cp template.html template.html.bak
cp meta.yaml meta.yaml.bak
```

**备份纪律（硬约束）：**

| 规则 | 说明 |
|---|---|
| 阶段一备份必须在任何代码改动前完成 | 6 个基础设施文件缺一不可 |
| 阶段二备份必须在每个 Block 迁移前完成 | 两个文件都必须有 .bak 副本 |
| .bak 文件不可修改 | 备份后只读，作为原始状态的锚点 |
| **绝不主动删除 .bak 文件** | 除非用户明确说"删除备份文件"，否则 .bak 文件永久保留 |
| git 中忽略 .bak | `*.bak` 已加入 `.gitignore`，不提交到仓库 |
| 整个模板迁移完成后再统一清理 | 全部 13 个 Block 迁移验证通过后，由用户决定是否批量删除所有 .bak |

### 8.2 迁移步骤（每个 Block 独立执行）

0. **备份**：`cp template.html template.html.bak && cp meta.yaml meta.yaml.bak`
1. **对照 meta.yaml**，确认所有字段的类型和默认值
2. **CSS 字段**：找到对应 HTML 元素 → 加 `data-key` → 加 `data-label-*` → 确认 style 中有对应 CSS 属性及默认值
3. **非 CSS 字段**：Section 级放 `</section>` 后，item 级放 `data-repeat-item` 内末尾 → 加 `<meta data-field ...>`
4. **列表字段**：容器加 `data-repeat` + `data-repeat-label`，模板项加 `data-repeat-item`
5. **样式引用替换**：Section 级 → `{{ s.<data_key> }}`（通过 `styles(module)` 计算）；Item 级 → `{{ item.<key> | default('默认值') }}`
6. **URL 处理**：item 级 URL 字段用 `| default('')` 回退，避免输出 `None`
7. **验证**：运行 `flask --app run scan-templates`，检查无报错，字段列表与 meta.yaml.bak 一致
8. **对比输出**：用旧模板和新模板各构建一次站点，diff output/ 确认渲染结果一致

### 8.3 回滚机制

每个 Block 迁移后必须可以独立回滚，不影响其他 Block。回滚利用 .bak 文件（优先级高于 git，因为 git 中可能有多轮修改）。

**回滚步骤（单 Block）：**

```
1. cp template.html.bak template.html    # 恢复原始模板
2. cp meta.yaml.bak meta.yaml            # 恢复原始 Schema
3. flask --app run scan-templates        # 验证扫描正常
4. 启动 dev server 检查后台页面编辑功能正常
```

**回滚原理：**
- template.html.bak 是迁移前的 Jinja2 版本，直接覆盖即可恢复
- meta.yaml.bak 是原始字段声明，恢复后扫描器走旧方式
- 扫描器检测到 template.html 中没有 `data-label-*`，自动回退到读 meta.yaml
- 其他 Block 不受影响（新旧方式可在同一模板中共存）

**安全规则：**
- 迁移一个 Block 期间**不提交 git**，直到该 Block 验证通过
- 验证不通过 → 立即执行回滚步骤，排查问题后重试
- 验证通过 → 提交该 Block 的改动（commit message: `refactor: <block名> 迁移到 data-* 字段声明`）
- .bak 文件**不删除**，继续保留作为原始参照

### 8.4 渐进式迁移顺序

按 Block 复杂度从低到高排列，每个 Block 验证通过后再迁移下一个：

| 优先级 | Block | 复杂度 | 说明 |
|---|---|---|---|
| 1 | hero_banner | 高 | 含 CSS 字段 + select + toggle + 列表，作为样板 |
| 2 | section_title | 低 | 纯 CSS 字段，无列表 |
| 3 | text_content | 低 | 纯 CSS 字段 |
| 4 | contact_info | 低 | 纯文本字段，无列表 |
| 5 | highlight_card | 中 | CSS 字段 + 列表 + 变体 |
| 6 | stat_counter | 中 | CSS 字段 + 列表 |
| 7 | logo_cloud | 中 | CSS 字段 + 列表 |
| 8 | feature_grid | 中 | CSS 字段 + 列表 |
| 9 | process_steps | 中 | CSS 字段 + 列表 |
| 10 | contact_form | 中 | 混合字段 |
| 11 | data_grid | 高 | 数据集绑定 + 复杂列表渲染 |
| 12 | product_grid | 高 | 数据集绑定 + 卡片布局 |
| 13 | item_detail | 高 | 数据集绑定 + 详情页面渲染 |
| — | item_data | — | **暂不迁移**：含 `isDatasetMode`/`editItem` 特殊上下文，与 data-repeat 机制不同，保留其 `specialEditor` 硬编码（详见 §10-15） |

先迁移 hero_banner 作为样板，验证整套机制跑通后推进低复杂度 Block。**数据集绑定的 3 个 Block（data_grid / product_grid / item_detail）排在最后**，因为它们涉及 `all_datasets` 数据源绑定、动态字段映射、`_modules.html` 的 `detail` 路由等额外复杂度，需要基础设施在简单 Block 上充分验证后再处理。item_data 因其特殊的条目编辑上下文（`isDatasetMode` / `editItem`）暂不迁移。

### 8.5 完成后更新 Skill 文档

**触发条件（全部满足后才执行）：**
1. 全部 13 个 Block 迁移完成（item_data 暂不迁移，详见 §10-15）
2. 店主后台（admin 面板）每个 Block 的属性编辑、保存、数据回显均正常
3. 模板预览（`flask --app run build-site` 或预览模式）构建无报错
4. 静态站点输出与迁移前 diff 一致（或仅有预期的空格/换行差异）
5. 开发者用新方式新建一个测试 Block，从扫描到构建全链路跑通

**需更新的 Skill：**

| Skill | 改动内容 |
|---|---|
| `template-new-block` | 新增 Block 的流程从"创建 meta.yaml + template.html"改为"创建 template.html（含 data-* 属性）" |
| `template-new-template` | 如果模板脚手架中引用了 meta.yaml 示例，同步更新为 data-* 示例 |

**更新前必须确认：** 上述 5 个条件全部通过，且用户明确指令"更新 skill"。

**在更新 Skill 之前：** 新旧两种方式共存，`template-new-block` 等 skill 继续按 meta.yaml 方式指导。开发文档（本文档）是 data-* 新方式的唯一权威参考。

---

## 九、消除"四处同步" —— data-* 模式的核心优势

### 9.1 当前痛点

在 meta.yaml 模式下，新增或修改一个 Block 的样式编辑表单，必须手动同步**四处**代码：

| # | 文件 | 位置 | 用途 |
|---|------|------|------|
| 1 | `app/templates/dashboard/panel_page_edit.html` | Jinja2 模板 (~112-1017行) | 已保存模块的服务端渲染 |
| 2 | `app/templates/dashboard/panel_page_edit.html` | `addModule()` 函数 | 新增模块的客户端 JS 生成 |
| 3 | `app/static/js/admin_modules.js` | `buildModuleHTML()` 函数 | 数据集编辑器的模块表单 |
| 4 | `app/core/routes.py` | `_parse_modules_form()` 函数 | 表单提交后的数据解析 |

**漏改任何一处，用户会看到不一致的界面，或提交的数据丢失。** 四处代码风格不同（Jinja2 vs JS 字符串拼接 vs JS DOM 操作 vs Python 字典解析），字段顺序、分组标签、单位数组必须完全一致。这是当前系统最大的维护负担。

根本原因：admin_modules.js 中存在**按 block type 硬编码的样式编辑器**（`specialEditor` / `styleEditor`），routes.py 中存在**按 block type 硬编码的列表字段解析逻辑**（如 hero_banner slides 的 `module_N_slide_count` / `module_N_slide_S_*` 前缀解析，约 1834-1902 行），它们覆盖/绕过了动态字段机制，破坏了数据驱动的渲染。

### 9.2 data-* 模式的解决方案

data-* 模式将字段定义下沉到 template.html，渲染完全由字段列表驱动：

```
template.html（data-* 属性）
    │
    ▼
block_scanner 提取字段定义
    │
    ▼
字段列表 → admin_modules.js 的 renderField() 动态渲染
    │
    ▼
所有表单控件均由字段类型决定，无需手动写三处 HTML
```

**核心目标：template.html 是唯一需要修改的文件。** 加字段 = 在 HTML 元素上加 `data-label-*`；改字段 = 改 `data-label-*` 的值；删字段 = 删 `data-label-*` 属性。扫描器和 admin JS 自动跟进。

### 9.3 实现时的硬约束

为实现"零硬编码"目标，基础设施搭建阶段必须做到以下 11 点：

**A. 增强 `renderField()` 的控件类型支持**

当前 `renderField()` 只区分 `textarea` / `select` / `number` 三种，其余全部回退为 `<input type="text">`。必须新增以下类型支持：

| 新增 type | 生成控件 | 说明 |
|---|---|---|
| `color` | `color` | 颜色选择器（复合控件：颜色输入框 + 文本输入框，与现有 `cn()` 函数等效） |
| `url` | `<input type="url">` + 图片预览 | 输入框 + 小缩略图（若值为图片 URL） |

现有行为保留并文档化：`renderField()` 在字段 key 匹配 `/image|cover|background|media|photo|logo/i` 时自动追加 `<input type="file">` 上传控件。**这个行为不变**，意味着 key 中包含 `image`、`media` 等关键词的字段会自动获得上传能力。模板作者在为 `data-label-background-image` 之类的字段起名时，key 中自然会包含 `media` 或 `image`，无需额外处理。

施工顺序：在迁移 hero_banner **之前**完成 renderField() 增强，并回归验证其他 13 个 Block 的旧模式渲染不受影响。

**B. 单位选择器改为 `renderField()` 的通用能力**

当前单位选择器由 `un()` 辅助函数生成 `input + select.unit-picker` 复合控件，但 `un()` 是硬编码在各处调用的。必须将其集成到 `renderField()` 中：

渲染逻辑：
```
如果 field 定义中包含 units 列表 →
  生成 <div class="input-group-sm">
    <input type="text" value="...">
    <select class="unit-picker" onchange="...">
      <option>px</option> ...（第一个为默认单位）
    </select>
  </div>
```

`renderField()` 的调用方（panel_page_edit.html 的 Jinja2 部分、addModule()、admin_modules.js 的 buildModuleHTML()）全部改为调用同一个 `renderField()`，不再各自硬编码单位选择器。

扫描器在 field 定义中附加 `units` 字段，`renderField()` 据此决定是否渲染单位选择器。

**单位推断表（CSS 属性 → 可选单位列表）：**

| CSS 属性 | 可选单位 | 默认单位 |
|---|---|---|
| `width`, `min-width`, `max-width` | px, %, rem, vw | px |
| `height`, `min-height`, `max-height` | px, vh, rem, % | px |
| `font-size` | px, rem, em | rem |
| `padding`, `padding-*` | px, rem, % | px |
| `margin`, `margin-*` | px, rem, % | px |
| `border-radius` | px, rem, % | px |
| `border-width` | px, rem | px |
| `line-height` | rem, — (无单位) | rem |
| `letter-spacing` | px, rem, em | px |
| `gap`, `row-gap`, `column-gap` | px, rem | px |
| 其他 | px, rem | px |

推断规则：扫描器根据 `_css_prop` 查找上表，将 `units` 列表写入字段定义。上表未列出的 CSS 属性默认使用 `["px", "rem"]`。第一个单位为默认单位。

**C. `_parse_modules_form()` 改为数据驱动**

当前 routes.py 的 `_parse_modules_form()` 对 6 种 Block 的列表字段有硬编码解析（hero_banner 的 slides、feature_grid 的 features、stat_counter 的 stats、logo_cloud 的 logos、process_steps 的 steps、item_detail 的 images/specs）。必须改为通用逻辑：

```
解析流程（数据驱动）：
1. 遍历请求中的 module_N_data_* 键，构建扁平 dict
2. 对照 block 的字段定义，找到 type=list 的字段
3. 对于列表字段，从 form 中有序提取每项的 item_fields
4. 输出与 YAML 存储格式一致的结构
```

**统一序列化格式：**

列表字段的 form 命名统一为 `module_N_data_<listKey>_<index>_<itemField>`：

```
module_0_data_slides_0_type     → slides[0].type
module_0_data_slides_0_media    → slides[0].media
module_0_data_slides_0_title    → slides[0].title
module_0_data_slides_1_type     → slides[1].type
...
```

- `listKey` 使用 `data-repeat` 的值（如 `slides`，不是 `slide`）
- `data_` 前缀与非列表字段的 `module_N_data_<field>` 命名保持一致
- `index` 从 0 开始，连续递增
- `itemField` 使用扫描器输出的字段 key

**与现有格式的差异（仅改 JS 端，不影响已存储数据）：**

| Block | 现有 form 前缀 | 迁移后 |
|---|---|---|
| hero_banner | `module_N_slide_S_` | `module_N_data_slides_S_` |
| feature_grid | `module_N_feature_S_` | `module_N_data_features_S_` |
| stat_counter | `module_N_stat_S_` | `module_N_data_stats_S_` |
| logo_cloud | `module_N_logo_S_` | `module_N_data_logos_S_` |
| process_steps | `module_N_step_S_` | `module_N_data_steps_S_` |
| item_detail | `module_N_data_images_S_` | 不变（已使用 data_ 前缀） |

列表项计数器的隐藏字段也统一为 `module_N_data_<listKey>_count`，替代当前的 `module_N_slide_count`、`module_N_feature_count` 等。

**D. `styles()` 需要访问全局 settings**

当前模板中的 `outer_width` 回退链：
```
md.get('outer_width', '') or settings.get('layout', {}).get('global_width', '')
```

在 data-* 模式中，`styles()` 只接收 `module.data`，无法访问 `settings.layout.global_width`。必须扩展：

```python
# styles() 扩展签名
def compute_section_styles(module: dict, settings: dict = None) -> 'StyleProxy':
```

builder.py 注册时传入 settings：
```python
env.globals['styles'] = lambda md: compute_section_styles(md, settings)
```

StyleProxy 内部对 `width` / `max-width` 类属性做回退：字段值为空时查 `settings.layout.global_width`。

模板中同时也保留通过 `module.data` 直接访问 settings 的能力（因为 module 在 Jinja2 上下文中可访问），用于 item 级样式的回退。

**E. 文件上传控件触发规则（隐式行为，模板作者须知）**

`renderField()` 中有一项**现有行为**需要保留：字段 key 匹配 `/image|cover|background|media|photo|logo/i` 时自动追加 `<input type="file">`。这意味着：

- `data-key="media_bg"` + `data-label-background-image` → key = `media_bg_background_image` → 匹配 `image` → 自动带上文件上传
- `data-key="btn"` + `data-label-background-color` → key = `btn_background_color` → 匹配 `background` → 也会带上文件上传（误触发）

**模板作者注意事项：** 如果某个颜色字段的 key 意外包含了上述关键词（如 `section_background` 因为包含 `background` 而触发上传控件），可以通过 `<meta data-field>` 声明同名字段来覆盖 type，或者接受多一个上传按钮（无害）。

**F. `data-unit-<prop>` 覆盖（Phase 2，v1 不实现）**

如果某个 Block 的 width 字段不需要 vw 单位，可以加 `data-unit-max-width="px,%,rem"` 覆盖。v1 先用自动推断，遇到特殊需求再打开此能力。

**G. 字段顺序由扫描器输出顺序决定**

扫描器按 template.html 中字段的出现顺序输出，admin JS 按此顺序渲染。模板作者通过调整 `data-label-*` 在 HTML 中的位置来控制后台属性面板的字段排列。

**H. 列表项编辑器 —— 通用 `renderListEditor()`**

当前每个含列表的 Block 有自己的一套 JS 函数生成列表项编辑 HTML：

| Block | 添加函数 | 项 HTML 函数 |
|---|---|---|
| hero_banner | `_addHeroSlide()` | `_heroSlideHtml()` |
| feature_grid | `_addFeatureItem()` | `_featureItemHtml()` |
| stat_counter | `_addStatItem()` | `_statItemHtml()` |
| logo_cloud | `_addLogoItem()` | `_logoItemHtml()` |
| process_steps | `_addStepItem()` | `_stepItemHtml()` |

data-* 模式统一为一个通用函数：

```javascript
// admin_modules.js 新增
function renderListEditor(moduleIdx, listKey, itemFields, existingItems) {
  // itemFields: 扫描器输出的 item_fields 列表
  // existingItems: 已保存的列表数据（编辑模式回填）
  // 返回: 完整的列表编辑器 HTML（含添加按钮 + 项列表容器）
  //
  // 每项渲染：遍历 itemFields，对每个 field 调用 renderField()
  // 表单 name 格式：module_{idx}_data_{listKey}_{itemIndex}_{fieldKey}
  // 每项一个删除按钮，onclick 时移除该 .list-item 并触发重编号
}
```

`renderListEditor()` 替换 panel_page_edit.html 中 5 套重复的列表编辑器代码（addModule 中的 ~180 行 + Jinja2 模板中的 ~120 行），也替换 admin_modules.js buildModuleHTML() 中对应的 `specialEditor` 分支。

**I. `visibility` 字段类型 —— 眼球开关控件**

`data-type="visibility"` 生成眼球图标开关（与当前 `visToggle()` 函数等效）。

```html
<meta data-field="show_phone" data-label="电话" data-type="visibility" data-default="true">
```

渲染输出：
- 眼球开/关 SVG 图标按钮
- 隐藏的 `<input type="hidden">` 存储 `"true"` / `"false"`
- 点击按钮切换图标 + 更新 hidden input 值

与 `toggle` 的区别：
- `toggle` → `<select>` 下拉，适用于通用布尔选择（启用/禁用、左/右）
- `visibility` → 眼球开关，适用于控制页面元素的显隐

`renderField()` 中新增 `visibility` 分支，等价于调用现有 `visToggle()` 函数。contact_info 的 `show_phone` / `show_mobile` / `show_email` / `show_address` / `show_business_hours` 和 contact_form 的 `show_name` / `show_email` / `show_phone` / `show_company` / `show_message` / `show_map` / `show_form` 使用此类型。

**J. `data-no-resp` —— 响应式控件自动检测**

扫描器根据以下规则判断是否显示响应式覆写控件（每行列数、每页数量）：

1. 模板中存在 `data-repeat` 容器 → 默认显示响应式控件
2. 根元素有 `data-no-resp` 属性 → 强制不显示（hero_banner 是唯一例外）
3. 模板中无 `data-repeat` → 不显示（section_title、text_content、highlight_card、item_detail）

当前 `admin_modules.js:140` 和 `panel_page_edit.html:2866` 的硬编码 `needsResp` 判断由扫描器输出的字段定义标记替代。

实现方式：`renderField()` 不需要改动 —— 响应式覆写控件不在字段级别，而在模块编辑器的外层框架（平板端/手机端 tabs）。admin JS 根据字段定义中的 `no_responsive` 标记决定是否渲染这些 tabs。

**K. `_modules.html` 旧数据格式兼容**

当前 `_modules.html` 第 3 行有硬编码：

```jinja2
{% if module.data is mapping or (module.type == 'hero_banner' and module.data is iterable and module.data is not string) %}
```

这是为了兼容旧站点中 hero_banner 的 data 直接存为列表（`[{type: image, ...}]`）而非 `{slides: [...]}` 的情况。

在 data-* 模式中，此兼容逻辑移到 builder.py 的渲染准备阶段：

```python
# builder.py 在 _render_for_language() 中，渲染前做数据格式标准化
def _normalize_module_data(module: dict) -> dict:
    """旧格式兼容：列表数据 → {listKey: [...]}"""
    block_type = module.get('type', '')
    data = module.get('data', {})
    if isinstance(data, list):
        # 查找该 block 的列表字段 key
        fields = _block_fields_cache.get(block_type, [])
        list_fields = [f for f in fields if f.get('type') == 'list']
        if list_fields:
            list_key = list_fields[0]['key']
            return {list_key: data}
    return data
```

`_modules.html` 随之简化为 `{% if module.data is mapping %}`，不再引用具体 block type。

**调用位置**（`builder.py` 的 `_render_for_language()` 方法）：

```python
# _render_for_language() 中，遍历页面模块时：
for module in page.get('modules', []):
    module['data'] = _normalize_module_data(module, block_fields_cache)
    # 此后 module.data 保证是 dict 格式，模板和 styles() 无需再做兼容判断
```

`_normalize_module_data()` 应在构建模块上下文（ctx）之前调用，确保传给模板的 `module.data` 始终是 dict。

### 9.4 验证标准（hero_banner 迁移时必须全部通过）

1. 后台新建 hero_banner 模块 → 属性面板表单正确渲染所有字段（含颜色选择器、单位选择器）
2. 填写字段值 → 保存 → 刷新页面 → 已保存模块打开属性面板，表单与新建时一致
3. 数据集编辑器（如有 hero_banner 的数据绑定）中表单也一致
4. **admin_modules.js 中不存在 `case 'hero_banner':` 或类似硬编码分支**
5. **routes.py 的 `_parse_modules_form()` 中不存在 `hero_banner` 特殊解析分支**
6. **panel_page_edit.html 的 Jinja2 部分不存在 `hero_banner` 硬编码分支**
7. **panel_page_edit.html 的 `addModule()` 中不存在 `hero_banner` 硬编码分支**
8. 构建站点 → 输出 HTML 与迁移前 diff 一致（或仅有预期的空格/换行/属性顺序差异）

如果验证不通过（某个字段类型 renderField() 不支持，或解析逻辑无法通用化），则先增强基础设施的通用能力，再继续迁移。**不准为 data-* 模式新增任何 per-block 硬编码代码。**

---

## 十、限制与边界

1. **`data-repeat` 不支持嵌套** —— 列表项内部不能有子列表
2. **同一个 `data-repeat-item` 内的 `data-key` 必须唯一** —— 不同 scope 之间允许重复。`data-key` 推荐用纯字母数字命名（可读性），但技术上允许下划线
3. **CSS 简写属性和子属性是独立字段** —— `padding` 和 `padding-top` 不会自动关联，模板作者自行保证不重复声明
4. **`data-options` 分隔符不转义** —— 标签和值中不能包含 `:` 或 `, `。必要时用全角 `：` `，` 替代，扫描器自动还原
5. **`font-weight` 和 `text-align` 的下拉选项固定** —— 如需自定义选项，用 `<meta data-type="select">` 声明同名 key 覆盖（meta 优先级高于 CSS 自动推断）
6. **复杂条件样式（一个字段控制多个 CSS 属性）需在模板中保留 Jinja2 `{% if %}`** —— 如 `banner_align`。后续可在 `block_styles.py` 中为特定 block_type 注册转换器来消除
7. **`html.parser` 对畸形 HTML 的容忍度有限** —— template.html 必须是合法的 HTML（可以含 Jinja2 标签，但 HTML 标签必须正确闭合）
8. **变体（variants）暂不支持** —— 当前 meta.yaml 的 `variants:` 机制（如 highlight_card 的 default/right 布局变体）在 data-* 模式中没有对应的声明方式。v1 迁移时保留 `meta.yaml.bak` 中的变体定义，如该 block 实际使用了变体功能，迁移时需先讨论替代方案
9. **文件上传控件的触发依赖 key 命名约定** —— `renderField()` 根据 key 是否匹配 `/image|cover|background|media|photo|logo/i` 来决定是否追加上传控件。如果 CSS 字段 key 中意外包含这些关键词（如 `section_background` 触发上传），会多出一个无害但多余的按钮。模板作者命名 `data-key` 时需注意
10. **数据集绑定 Block（data_grid / product_grid / item_detail）的迁移复杂度高** —— 它们涉及 `all_datasets` 数据源、动态字段映射、`_modules.html` 的 `detail` 路由、模板中的 `{% for item in dataset_key %}` 等特殊逻辑。这些 Block 排在迁移顺序最后，确保基础设施在简单 Block 上充分验证后再处理
11. **旧数据格式兼容** —— 部分旧站点的 hero_banner data 直接存储为列表（`data: [{type: image, ...}]`），而非 `data: {slides: [...]}`。扫描器和 `styles()` 不需要处理此兼容（由 builder 在渲染前做格式标准化，详见 § 9.3-K），但迁移验证时必须用新旧两种数据格式各构建一次确保输出一致
12. **`_modules.html` 的 `module.type` 硬编码** —— 当前 `_modules.html` 第 3 行有 `module.type == 'hero_banner'` 判断（旧数据格式兼容）。标准化在 builder.py 的 `_normalize_module_data()` 中完成（§ 9.3-K），`_modules.html` 简化为 `{% if module.data is mapping %}`
13. **`admin_modules.js` 的动态字段渲染已存在** —— `buildModuleHTML()` 第 145 行的 `desktopFields` 已经用 `fields.map(renderField)` 做数据驱动渲染。迁移的核心工作是**删除 `specialEditor` / `styleEditor` 中的 per-block 硬编码分支**，让 `desktopFields` 覆盖所有字段。列表字段（data-repeat）的编辑器通过 `renderListEditor()` 插入到 `specialEditor` 位置
14. **`panel_page_edit.html` 的 Jinja2 模板和 `addModule()` 函数** —— 两者各有 ~1144 行和 ~850 行 per-block 硬编码分支。消除策略与 admin_modules.js 相同：Jinja2 侧用 `{% for field in fields %}` + `renderField()` 宏替代 `{% if module.type == 'xxx' %}`；`addModule()` 侧用 `fields.forEach(renderField)` + `renderListEditor()` 替代 `if (type === 'xxx')` 分支
15. **`item_data` Block 暂不迁移** —— `item_data` 不是普通 Block，它是数据集的条目编辑界面（含 slug、date、body 等固定字段 + 动态自定义字段）。它使用 `isDatasetMode` 和 `editItem` 上下文，与 `data-repeat` 列表机制完全不同。**`item_data` 的 `specialEditor` 硬编码保留**，不在 data-* 迁移计划中。其余 13 个 Block 完成迁移后视情况决定是否跟进
