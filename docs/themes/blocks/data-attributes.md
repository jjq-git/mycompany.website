# data-* 属性速查

| # | 属性 | 用途 |
|---|---|---|
| 1 | [`data-type`](#1-data-type) | 内容类型，决定如何存储、注入、编辑（含 list / grid 等全部枚举值） |
| 2 | [`data-name`](#2-data-name) | 元素命名，字段 key |
| 3 | [`data-href`](#3-data-href) | 链接地址，让任意元素可点击 |
| 4 | [`data-style`](#4-data-style) | CSS 变量通道，开放给用户的结构选择 |
| 5 | [`data-hideable`](#5-data-hideable) | 整块可隐藏（简单开关） |
| 6 | [`data-source`](#6-data-source) | 列表数据来源（手动 / 数据集） |
| 7 | [`data-page-size`](#7-data-page-size) | 列表分页，每页条数 |
| 8 | [`data-cols`](#8-data-cols) | 二维栅格列数 |

---

## 一、核心概念

HTML 模板同时承担 **Schema** 和 **Render** 两个角色。四类关注点分开，互不污染：

| 关注点 | 属性 | 说明 |
|---|---|---|
| **内容** | `data-name` / `data-type` / `data-href` | 元素是什么、存什么、注入到哪 |
| **样式** | `data-style` | 用户可调的结构性样式，改 CSS 变量不改 DOM |
| **行为** | `data-page-size` / `data-cols` / `data-source` | 列表分页、栅格列数、数据从哪来 |
| **能力** | `data-hideable` | 用户控制整块显隐 |

**核心原则：HTML 本身就是数据存储。** 模板里的文字、src、style 值即为默认值——编辑器读取展示，用户修改后写回对应元素。不需要额外的 JSON 或 `<meta>` 声明。

**样式原则：只开放主题作者声明过的 CSS 变量。** 店主通过预设选项（下拉/开关/颜色选择器）调整样式，不输入自由数值。所有可调项在全局注册表集中定义。

**显隐原则：只有一种机制。** 用户手动开关 → `data-hideable` + 原生 `hidden`。字段值为空时元素自动隐藏（由类型驱动，不依赖额外属性）。

---

## 二、`data-type` 内容类型

### 1. `data-type`

`data-type` 是元素的内容类型声明，**同时决定三件事**：内容存哪、编辑器用什么控件、值如何注入。

**叶子类型**（内容直接存在元素上）：

| type | 适用元素 | 内容存哪 | 编辑器控件 | 空值行为 |
|---|---|---|---|---|
| `text` | h1~h6 / p / span / a / div | innerText | 单行文本框 | 自动隐藏 |
| `textarea` | div / p / span | innerText | 多行文本框 | 自动隐藏 |
| `richtext` | div | innerHTML | 富文本编辑器 | 自动隐藏 |
| `image` | img | src | 图片上传 / URL | 自动隐藏 |
| `video` | video | src | 视频 URL | 自动隐藏 |
| `audio` | audio | src | 音频 URL | 自动隐藏 |
| `embed` | iframe | src | 嵌入 URL（地图/第三方视频） | 自动隐藏 |
| `icon` | div | 图标名 | 图标选择器（从预定义图标集选择） | — |

**结构类型**（组织子元素）：

| type | 适用元素 | 含义 | 详见 |
|---|---|---|---|
| `group` | div / li / article / section | 复合项，子元素打包为一条记录 | [§六](#data-typelist--data-typegrid) |
| `list` | div / ul / nav / section | 一维可重复列表，子元素按数据重复 N 份 | [§六](#data-typelist--data-typegrid) |
| `grid` | div / table | 二维可重复栅格，子元素按数据重复行×列 | [§六](#data-typelist--data-typegrid) |

**类型 = 内容是什么；链接 = 能不能点。两件事，两个字段。** 不单独设 `link` 类型：`text + data-href` = 文字链接，`image + data-href` = 图片链接。

**HTML 中的值即默认值：**
- `text` / `textarea` / `richtext`：标签里的文字是默认值
- `image` / `video` / `audio` / `embed`：`src` 属性值是默认值
- `icon`：标签里的默认 SVG 是初始图标
- `list` / `grid`：模板里的那一项即默认样例，用户复制成多份

```html
<!-- 文本 -->
<h1 data-name="title" data-type="text">默认标题</h1>

<!-- 图片（可点击） -->
<img data-name="cover" data-type="image" data-href="/detail" src="default.jpg">

<!-- 视频 -->
<video data-name="intro" data-type="video" src="intro.mp4" autoplay muted loop></video>

<!-- 嵌入（地图） -->
<iframe data-name="map" data-type="embed"
        src="https://map.example/embed?lng=..."></iframe>

<!-- 富文本 -->
<div data-name="body" data-type="richtext"><h2>标题</h2><p>正文……</p></div>

<!-- 图标 -->
<div data-name="service-icon" data-type="icon">
  <svg><!-- 默认图标 --></svg>
</div>

<!-- 复合项（打包多个字段为一条记录） -->
<article data-name="member" data-type="group">
  <img data-name="photo" data-type="image" src="p1.jpg">
  <span data-name="name" data-type="text">李四</span>
</article>

<!-- 可重复列表 -->
<section data-name="features" data-type="list">
  <div data-name="feature" data-type="group">
    <img data-name="icon" data-type="image" src="icon.svg">
    <h3 data-name="title" data-type="text">特性标题</h3>
  </div>
</section>
```

**空值自动隐藏：** 文本类型（`text` / `textarea` / `richtext`）值为空、媒体类型（`image` / `video` / `audio` / `embed`）src 为空时，元素自动加 `hidden`。不需要额外的条件属性。结合 `data-hideable` 可覆盖所有显隐场景。

---

## 三、元素标识

### 2. `data-name`

给元素起名，作为字段 key。同一模板内唯一。

| 适用场景 | 说明 |
|---|---|
| 元素有 `data-type`（任意类型） | **必填**。扫描器和后处理用它定位 |
| 纯结构元素（无任何 data-* 声明） | 不需要 |

---

## 四、链接

### 3. `data-href`

让任意元素变成可点击链接。**独立于 `data-type`**——text + data-href = 文字链接，image + data-href = 图片链接。

字段值为空时元素变为不可点击（不隐藏，仅跳过 href 注入）。如需控制新窗口打开，模板直接写 `target="_blank"`。

```html
<!-- 文字链接 -->
<a data-name="btn" data-type="text" data-href="btnLink">立即咨询</a>

<!-- 图片链接 -->
<img data-name="logo" data-type="image" data-href="logoLink" src="logo.svg">

<!-- 同一个元素既是文字又是链接 -->
<a data-name="cta" data-type="text" data-href="ctaLink">了解更多</a>
```

---

## 五、CSS 样式通道

### 4. `data-style`

主题作者将**可调样式**写成 CSS 变量，在注册表定义控件和可选值，元素上用 `data-style` 声明开放哪些。店主通过预设选项调整——不改代码，不输入自由数值。

**可控类型：**

| 控件 | 适用场景 | 示例 |
|---|---|---|
| `select` | 预设选项 | 列数 (2/3/4) |
| `switch` | 二选一 | 图文方向 (左图右文/右图左文) |
| `image` | 图片选择/上传 | 背景图 (hero banner) |
| `color` | 颜色选择器 | 背景色 (hero banner 底色) |

```html
<!-- 开放：列数 + 图文方向 -->
<section data-name="features" data-type="list"
         data-style="cols, dir"
         style="--cols: 3; --dir: row">
  ...
</section>
```

```css
/* 模板 CSS：用 var() 设默认值 */
.feature-grid {
  display: flex;
  flex-direction: var(--dir, row);
}
```

**约定：**

- `data-style="dir"` ↔ CSS `--dir`（加 `--` 前缀，一一对应）
- 默认值只写在 CSS 的 `var(--dir, row)` 里，HTML 和注册表不重复
- 用户改 → 写到元素 `style`；重置 → 删掉 `style` 里的变量，CSS 自动回落
- 没进 `data-style` 的变量用户碰不到

**样式注册表：** 模板里用到的每个 CSS 变量，在全局注册表定义控件类型、可选值和中文标签：

```js
const STYLE_REGISTRY = {
  dir:  { label: "图文方向", control: "switch", default: "row",
          options: [{ value: "row", text: "图左文右" },
                    { value: "row-reverse", text: "图右文左" }] },
  cols: { label: "每行个数", control: "select", default: "3",
          options: [{ value: "2", text: "2" }, { value: "3", text: "3" }, { value: "4", text: "4" }] },
  bg:   { label: "背景图", control: "image", default: "" },
  "bg-color": { label: "背景色", control: "color", default: "" },
};
```

**该不该开放：** 两条都满足才加——

1. 用户**真的会想改**（列数、图文方向都会）
2. 改了**不会破坏设计**（预设选项保证安全）

→ 按"变量"建表，不是按"block"建表。几个变量就几条，与 block 数量无关。`features` 和 `news` 都用 `cols` → 共用同一条，改选项只改一处。

> **备注：扩展视觉微调。** 如果后续需要让店主调整颜色、字号、间距等视觉细节，同一套机制就能支持——在 STYLE_REGISTRY 里加条目（如 `gap: { label: "间距", control: "select", options: [{ value: "16", text: "紧凑" }, ...] }`），模板元素加 `data-style="gap"`，CSS 用 `var(--gap, 24px)` 取值。店主通过下拉/调色板选预设值，不改代码。是否开放、开哪些，由主题作者决定。

---

## 六、可见性

### 5. `data-hideable`

声明该元素**可被用户隐藏**。编辑器显示"显示/隐藏"开关，用户切换 → 加/删原生 `hidden` 属性。

```html
<!-- 可隐藏的营销块 -->
<section data-name="testimonials" data-type="list" data-hideable>…</section>

<!-- 用户隐藏后 → 加 hidden（= display:none，不留空白） -->
<section data-name="testimonials" data-type="list" data-hideable hidden>…</section>
```

- 隐藏用原生 `hidden`（等价 `display: none`），**不用 `visibility`**（会留空白坑）
- Header / Footer / 文章正文 / 产品正文 → **不加** `data-hideable`（必显块）
- 其余营销/展示块 → 加 `data-hideable`
- 元素级显隐：字段值为空时自动隐藏（由 `data-type` 的类型逻辑驱动，不需要额外属性）

---

## 七、可重复容器

### `data-type="list"` / `data-type="grid"`

| type | 含义 | 列数控制 |
|---|---|---|
| `list` | 一维可重复列表，子元素按数据重复 N 份 | 视觉列数用 CSS `--cols`，不进 data-* |
| `grid` | 二维可重复栅格，位置有意义的真阵列（日历/键盘/参数表） | `data-cols` |

**项模板约定：** 容器内「带 `data-name` 的直接子元素」= 项模板，运行时按数据复制。不靠"第一个子元素"猜——列表里可以有标题、"加载更多"等不带 data-name 的杂项。

```html
<!-- 一维列表：特性展示（列数归样式） -->
<section data-name="features" data-type="list"
         data-style="cols" style="--cols: 3">
  <div data-name="feature" data-type="group">      <!-- 项模板 -->
    <img data-name="icon" data-type="image" src="icon.svg">
    <h3 data-name="title" data-type="text">特性标题</h3>
  </div>
</section>

<!-- 二维栅格：价格表（列数归结构） -->
<table data-name="price-grid" data-type="grid" data-cols="3">
  <td data-name="cell" data-type="text">默认</td>   <!-- 项模板 -->
</table>
```

**约束：**
- 项模板必须是容器的直接子元素（中间不能有包裹层）
- 不支持嵌套 `list`/`grid`
- 数据数组为空 → 整个容器被删除
- 同一 template 内多个容器的 `data-name` 值必须唯一

### 6. `data-source`

`list` / `grid` 用 `data-source` 区分项从哪来：

| 值 | 类型 | 项从哪来 | 用户能干啥 |
|---|---|---|---|
| 省略 / `manual` | 手动 | HTML 写死 | 增/删/改每项 |
| 存在（空值或数据集名） | 动态 | 店主在后台选择数据集 | 选数据集 + 配每行列数 / 最大显示条数 |

存在 `data-source` 属性 = 告诉系统"这个 list/grid 是数据驱动的"。店主在后台把模块加到页面时，系统根据此属性显示**数据集下拉框**（产品 / 文章 / 案例 / 服务）。店主的选择存到页面配置（`pages/<name>.yaml`），构建时从 `sites/<id>/data/<dataset>.yaml` 取数据渲染。

主题作者可通过属性值限定可选数据集：`data-source="products"` 表示该模块只能用产品数据集；`data-source`（空值）表示店主可自由选择。

```html
<!-- 手动：菜单（店主自己增删每一项） -->
<nav data-name="main-menu" data-type="list" data-source="manual">
  <a data-name="item" data-type="text" data-href="/">首页</a>
</nav>

<!-- 动态：店主在后台选择数据集 -->
<section data-name="news" data-type="list" data-source>
  <article data-name="post" data-type="group">
    <img data-name="cover" data-type="image" src="default.jpg">
    <h3 data-name="title" data-type="text" data-href="">文章标题</h3>
  </article>
</section>

<!-- 限定数据集：只能用产品数据 -->
<section data-name="products" data-type="list" data-source="products">
  <div data-name="product" data-type="group">
    <img data-name="img" data-type="image" src="default.jpg">
    <h4 data-name="name" data-type="text" data-href="">产品名</h4>
  </div>
</section>
```

发布后，构建器将数据集转为 `data.json` 放在列表页同级目录，前端 JS 用其做过滤/排序/分页。`data-page-size` 控制每页条数。

### 7. `data-page-size`

`list` 容器专用。每页最多几条，超过则渲染器**自动追加页码**。省略则不分页，全显示。

```html
<!-- 文章列表：每页 9 条 -->
<section data-name="news" data-type="list" data-page-size="9">
  ...
</section>
```

### 8. `data-cols`

`grid` 容器专用。二维栅格列数，用于位置有意义的真阵列（日历/键盘/参数表）。

```html
<!-- 价格表：3 列 -->
<table data-name="price-grid" data-type="grid" data-cols="3">
  <td data-name="cell" data-type="text">默认</td>
</table>
```

> **列数的两种归属**，别混：只是"一行排几个"的视觉流式列表 → CSS `--cols`；位置有意义的真阵列 → `data-cols`。

---

## 附：`data-type` 全部枚举值

| 值 | 分类 | 含义 | 内容存哪 | 编辑器控件 |
|---|---|---|---|---|
| `text` | 叶子 | 单行文本 | innerText | 文本框 |
| `textarea` | 叶子 | 多行文本 | innerText | 多行文本框 |
| `richtext` | 叶子 | 富文本 | innerHTML | 富文本编辑器 |
| `image` | 叶子 | 图片 | src | 图片上传 / URL |
| `video` | 叶子 | 视频 | src | 视频 URL |
| `audio` | 叶子 | 音频 | src | 音频 URL |
| `embed` | 叶子 | 嵌入内容 | src | 嵌入 URL |
| `icon` | 叶子 | 图标选择 | 图标名 | 图标选择器 |
| `group` | 结构 | 复合项 | 子元素集合 | 整体编辑 |
| `list` | 结构 | 一维可重复列表 | 子元素×N | 增删项 + 编辑每项 |
| `grid` | 结构 | 二维可重复栅格 | 子元素×行×列 | 增删 + 编辑单元格 |

叶子类型**自动推断**字段和控件，不需要额外声明。结构类型**组织子元素**，内部的叶子类型各自声明自己的 `data-type`。
