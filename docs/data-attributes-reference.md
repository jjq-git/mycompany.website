# data-* 属性速查

> 设计规范详见 [block-data-attributes.md](block-data-attributes.md)，迁移方案详见 [block-data-attributes-dev-plan.md](block-data-attributes-dev-plan.md)。

| # | 属性 | 用途 |
|---|---|---|
| 1 | [`data-key`](#1-data-key) | 元素命名，CSS 字段 key 前缀 |
| 2 | [`data-label` / `data-label-<prop>`](#2-data-label-data-label-prop) | 声明 CSS 属性可编辑 |
| 3 | [`data-placeholder` / `data-placeholder-<prop>`](#3-data-placeholder-data-placeholder-prop) | 输入框占位提示 |
| 4 | [`data-group-<prop>` / `data-group`](#4-data-group-prop-data-group) | 字段分组 |
| 5 | [`data-content`](#5-data-content) | 替换文本内容，空值自动隐藏 |
| 6 | [`data-src`](#6-data-src) | 设置 src，空值自动隐藏 |
| 7 | [`data-href`](#7-data-href) | 设置 href，空值自动隐藏 |
| 8 | [`data-bg`](#8-data-bg) | 设置背景图，空值自动隐藏 |
| 9 | [`data-target`](#9-data-target) | 设置链接 target 属性 |
| 10 | [`data-when`](#10-data-when) | 条件可见性（字段=值匹配） |
| 11 | [`data-type="default"`](#11-data-typedefault) | 互斥组兜底项 |
| 12 | [`data-type="list"`](#12-data-typelist) | 可重复列表容器 |
| 13 | [`data-type` 枚举值](#七data-type-全部枚举值) | 全部 13 种：text / select / toggle / richtext / color / file 等 |
| 14 | [`data-no-resp`](#14-data-no-resp) | 禁用响应式覆写控件 |
| 15 | [`<meta>` 字段声明](#八meta-字段声明) | `data-field` / `data-options` / `data-default` 等 |
| 16 | [`<meta>` 替代方案](#16-不用-meta-的替代方案不推荐) | 不用 `<meta>`，字段属性挂在引用元素上（不推荐） |

## 一、元素标识

### 1. `data-key`

给元素起名，作为其 CSS 字段的 key 前缀。

```
data-key="title" + style="font-size: 3rem; color: #fff;" → title_font_size、title_color
```

| 适用场景 | 说明 |
|---|---|
| 元素有注入属性（`data-content` / `data-src` / `data-href` / `data-bg` / `data-target`） | **必填**。后处理用它定位目标元素 |
| 元素有 CSS 字段声明（`data-label` / `data-label-*`） | 推荐写。不写则 key 直接用 CSS 属性名 |
| 纯结构元素（无任何 data-* 声明） | 不需要 |

---

## 二、CSS 字段声明

让内联 `style` 中的 CSS 属性变成后台可编辑字段。**核心规则：只有内联 style 中的属性才会成为字段，`<style>` 块和外部 CSS 完全忽略。** 不想编辑的 CSS 属性放到 `<style>` 块即可。

### 2. `data-label` / `data-label-<prop>`

声明 CSS 属性可编辑，并给它中文标签。

| 语法 | 效果 | 适用场景 |
|---|---|---|
| `data-label="卡片"` | **批量**：style 中所有 CSS 属性自动生成字段，标签 = `data-key` 值 + CSS 中文名（内置词典） | 元素 CSS 属性多且都需编辑 |
| `data-label-font-size="标题字号"` | **逐个**：标签 = 指定文字 | 精准到单个属性，自定义标签 |
| 两者共存 | 逐个覆盖批量 | 大部分用批量，个别需自定义标签 |

```html
<!-- 批量 -->
<section style="height: 77vh; max-width: 100%; padding: 0; ..."
         data-key="section" data-label="Banner">

<!-- 逐个 -->
<h1 style="font-size: 3rem; color: #fff;"
    data-key="title"
    data-label-font-size="标题字号"
    data-label-color="标题颜色">
```

### 3. `data-placeholder` / `data-placeholder-<prop>`

输入框占位提示。批量/逐个语法同 `data-label`。

```html
<div data-label="内容区" data-placeholder="如 1200px"
     data-placeholder-max-width="如 900px" ...>
```

### 4. `data-group-<prop>` / `data-group`

将字段归入属性面板的折叠分组。

| 用法 | 位置 | 效果 |
|---|---|---|
| `data-group-font-size="排版"` | CSS 元素上 | `title_font_size` 归入"排版"面板 |
| `data-group="遮罩层"` | `<meta>` 上 | 非 CSS 字段归入"遮罩层"面板 |

---

## 三、内容注入

后处理阶段把字段值写入 HTML 元素，替代 Jinja2 `{{ }}`。

**命名原则：** 每个需要注入的 HTML 属性对应一个专有 `data-*` 属性，不设通用扩展机制。当前注入属性：`data-content`（innerText）、`data-src`、`data-href`、`data-bg`（background-image）、`data-target`。未来如需注入 `download`、`rel` 等，新增对应的 `data-download`、`data-rel`，保持一致的命名规则。

### 5. `data-content`

替换元素的全部文本内容。**字段值为空时元素自动隐藏。**

**适用场景：** 标题、按钮文字、描述。

```html
<h1 data-key="title" data-content="title">默认标题</h1>
```

### 6. `data-src`

设置 `src` 属性。**字段值为空时元素自动隐藏。**

**适用场景：** img / video / audio / source / iframe 的媒体地址。

```html
<img data-key="image" data-src="media" alt="">
<video data-key="video" data-src="media" autoplay muted loop></video>
```

### 7. `data-href`

设置 `href` 属性。**字段值为空时元素自动隐藏。**

**适用场景：** 链接、按钮的跳转地址。

```html
<a data-key="btn" data-content="primaryBtn" data-href="primaryBtnLink">按钮</a>
```

### 8. `data-bg`

追加 `background-image: url(...)` 到元素 style。**字段值为空时元素自动隐藏。**

**适用场景：** 背景图片。与 `data-src` 的区别——`data-src` 用于 img/video，`data-bg` 用于 div 背景。

```html
<div data-key="bg" data-bg="media"></div>
```

### 9. `data-target`

设置链接的 `target` 属性。字段值为空时不设置。

**适用场景：** 按钮链接控制是否新窗口打开。

```html
<a data-key="btn" data-content="primaryBtn" data-href="primaryBtnLink"
   data-target="primaryBtnLinkTarget">按钮</a>
```

---

## 四、条件可见性

### 10. `data-when`

根据字段值决定元素显隐。**不匹配时元素从输出中删除。**

| 写法 | 效果 |
|---|---|
| `data-when="field"` | 字段值非空即显示 |
| `data-when="field=value"` | 字段值等于 value 时显示 |
| `data-when="field=value1,value2"` | 字段值匹配任一逗号分隔值时显示 |

解析规则：按第一个 `=` 拆字段名和值，无 `=` 则为非空检查。

**适用场景：** 媒体类型切换、遮罩开关、联系方式显隐。

```html
<video data-when="type=video"
       data-key="video" data-src="media" ...></video>

<div data-when="type=image,video"
     data-key="image" data-bg="media"></div>
```

### 11. `data-type="default"`

互斥组兜底项。同父元素下多个 `data-when` 引用同字段时构成互斥组，无匹配则保留此项。

**适用场景：** 图标选择器（多个 SVG 互斥，没选中时显示默认图标）。

```html
<div data-key="icon">
  <svg data-when="icon=circuit">...</svg>
  <svg data-when="icon=code">...</svg>
  <svg data-when="icon=shield">...</svg>
  <svg data-when="icon" data-type="default">...</svg>
</div>
```

---

## 五、可重复列表

### 12. `data-type="list"`

容器标 `data-type="list"`，其**直接子元素**即为模板项。**模板只写一份**，构建时根据数据数组长度自动克隆 N 份。替代 `{% for %}` 和 `{% if items %}`。

**适用场景：** 轮播 slide、特色网格、Logo 墙、流程步骤、item_detail 的图片/规格列表等。

```html
<div data-type="list" data-key="slides" data-label="轮播媒体项">
  <div>
    <h1 data-content="title">...</h1>
    <img data-src="image" ...>
  </div>
</div>
```

**约束：**
- 模板项必须是 `data-type="list"` 容器的直接子元素（中间不能有包裹层）
- 不支持嵌套
- 数据数组为空 → 整个容器被删除
- 同一 template 内多个 `data-type="list"` 的 `data-key` 值必须唯一

---

## 六、响应式控制

### 14. `data-no-resp`

标在根元素上，禁用响应式覆写控件（每行列数、每页数量）。

**适用场景：** 有列表但不是网格的 Block——hero_banner（轮播）、item_detail（详情页）。

**自动检测：** 模板有 `data-type="list"` 且无 `data-no-resp` → 显示响应式控件。无列表的 Block 自动不显示。

---

## 七、`data-type` 全部枚举值

| 值 | 含义 | 所在元素 | 详见 |
|---|---|---|---|
| `text` | 单行文本 | `<meta>` | §八 |
| `textarea` | 多行文本 | `<meta>` | §八 |
| `url` | URL 输入框 | `<meta>` | §八 |
| `number` | 数字输入 | `<meta>` | §八 |
| `select` | 下拉选择 | `<meta>` | §八 |
| `toggle` | 布尔下拉 | `<meta>` | §八 |
| `visibility` | 眼球开关 | `<meta>` | §八 |
| `icon` | 图标选择器 | `<meta>` | §八 |
| `richtext` | 富文本编辑器 | `<meta>` | §八 |
| `color` | 颜色选择器 | `<meta>` | §八 |
| `file` | 文件上传 | `<meta>` | §八 |
| `default` | 互斥组兜底 | 互斥组内元素 | §四 |
| `list` | 可重复列表容器 | 容器元素 | §五 |

---

## 八、`<meta>` 字段声明

CSS 表达不了的字段类型用 `<meta>` 声明，构建时自动删除。注意：`data-type="list"` 和 `data-type="default"` 用在普通 HTML 元素上，**不通过 `<meta>` 声明**。

### 15a. `data-field` / `data-label` / `data-type`

| 属性 | 必填 | 作用 |
|---|---|---|
| `data-field` | 是 | 字段 key |
| `data-label` | 是 | 后台中文标签 |
| `data-type` | 是 | 控件类型，取值见 §七（`text` / `textarea` / `url` / `number` / `select` / `toggle` / `visibility` / `icon` / `richtext` / `color` / `file`） |

### 15b. `data-options`

下拉选项，`data-type="select"` 时必填。格式：`标签:值, 标签:值`。值含 `:` 或 `,` 时用全角 `：` `，` 替代。

```html
<meta data-field="type" data-label="媒体类型" data-type="select"
      data-options="图片:image, 视频:video" data-default="image">
```

### 15c. `data-default`

字段默认值，不写则初始数据中无此 key。

### 15d. `data-group`

字段分组，将字段归入属性面板的折叠分组。效果同 §二 `data-group`，但用在 `<meta>` 上：

```html
<meta data-field="overlay_enabled" data-label="启用遮罩"
      data-type="select" data-options="启用:true, 不启用:false"
      data-default="true" data-group="遮罩层">
```

### 15e. `data-placeholder`

输入框占位提示，仅 `text` / `url` / `textarea` / `number` 类型生效：

```html
<meta data-field="primaryBtn" data-label="按钮文字"
      data-type="text" data-placeholder="如 了解更多">
```

---

### 16. 不用 `<meta>` 的替代方案（不推荐）

将 `data-type`、`data-label`、`data-options`、`data-default` 等字段声明直接写在引用该字段的元素上，以 `data-field-*` 前缀区分：

```html
<!-- 方案 A（推荐）：<meta> 集中声明 -->
<meta data-field="type" data-label="媒体类型" data-type="select"
      data-options="图片:image, 视频:video" data-default="image">

<video data-when="type=video"
       data-key="video" data-src="media" ...></video>
<div data-when="type=image"
     data-key="image" data-bg="media"></div>
```

```html
<!-- 方案 B（不推荐）：字段属性挂在首个引用元素上 -->
<video data-when="type=video"
       data-field-type="select"
       data-field-label="媒体类型"
       data-field-options="图片:image, 视频:video"
       data-field-default="image"
       data-key="video" data-src="media" ...></video>
<div data-when="type=image"
     data-key="image" data-bg="media"></div>
```

| 对比 | 方案 A `<meta>` | 方案 B 挂在元素上 |
|---|---|---|
| 字段声明位置 | 集中在 `<meta>` 区域 | 散落在各引用元素上 |
| 多元素引用同字段 | 声明一次即可 | 需选一个"主元素"承载声明，其余只引用，容易遗漏 |
| 扫描器实现 | 直接解析 `<meta>` | 需从引用处反向提取字段定义 |
| 可读性 | 字段列表一目了然 | 混在业务元素中，不易找全 |
| 构建输出 | `<meta>` 自动删除 | 额外的 `data-field-*` 属性需 strip，与注入属性混在一起，正则更复杂 |

**结论：** 方案 B 可行但不推荐。`<meta>` 更符合"Schema 与 Render 分离（但同文件）"的设计意图——字段定义集中在 `meta` 区域，注入引用在元素上，职责清晰。开发时保留方案 B 为备选。
