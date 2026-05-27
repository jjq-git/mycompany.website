# data-* 属性速查

> 设计规范详见 [block-data-attributes.md](block-data-attributes.md)，迁移方案详见 [block-data-attributes-dev-plan.md](block-data-attributes-dev-plan.md)。

| # | 属性 | 用途 |
|---|---|---|
| 1 | [`data-type`](#1-data-type) | 内容类型，决定如何存储、注入、编辑（含 list / grid / default 等全部枚举值） |
| 2 | [`data-name`](#2-data-name) | 元素命名，字段 key |
| 3 | [`data-href`](#3-data-href) | 链接地址，让任意元素可点击 |
| 4 | [`data-style`](#4-data-style) | CSS 变量通道，开放给用户的结构选择 |
| 5 | [`data-hideable`](#5-data-hideable) | 整块可隐藏（简单开关） |
| 6 | [`data-when`](#6-data-when) | 条件可见性（字段=值匹配） |
| 7 | [`data-source`](#7-data-source) | 列表数据来源（手动 / 动态 URL） |
| 8 | [`data-page-size` / `data-cols`](#8-data-page-size--data-cols) | 分页条数 / 栅格列数 |

---

## 一、核心概念

HTML 模板同时承担 **Schema** 和 **Render** 两个角色。四类关注点分开，互不污染：

| 关注点 | 属性 | 说明 |
|---|---|---|
| **内容** | `data-name` / `data-type` / `data-href` | 元素是什么、存什么、注入到哪 |
| **样式** | `data-style` | 用户可调的结构性样式，改 CSS 变量不改 DOM |
| **行为** | `data-page-size` / `data-cols` / `data-source` | 列表如何分页、栅格列数、数据从哪来 |
| **能力** | `data-hideable` / `data-when` | 用户能对这块做什么（隐藏、条件显隐） |

**核心原则：HTML 本身就是数据存储。** 模板里的文字、src、style 值即为默认值——编辑器读取展示，用户修改后写回对应元素。不需要额外的 JSON 或 `<meta>` 声明。

**样式原则：只开放结构性选择给用户。** 字号、颜色、间距等设计细节固定在 `.css` 里，不暴露编辑。开放项通过 CSS 变量 + `data-style` 声明，每个变量在全局注册表定义控件和可选值。

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
| `icon` | div（含 SVG 子元素） | 选中的图标名 | 图标选择器 | — |

**结构类型**（组织子元素）：

| type | 适用元素 | 含义 | 详见 |
|---|---|---|---|
| `group` | div / li / article / section | 复合项，子元素打包为一条记录 | [§七](#data-typelist--data-typegrid) |
| `list` | div / ul / nav / section | 一维可重复列表，子元素按数据重复 N 份 | [§七](#data-typelist--data-typegrid) |
| `grid` | div / table | 二维可重复栅格，子元素按数据重复行×列 | [§七](#data-typelist--data-typegrid) |

**类型 = 内容是什么；链接 = 能不能点。两件事，两个字段。** 不单独设 `link` 类型：`text + data-href` = 文字链接，`image + data-href` = 图片链接。

**HTML 中的值即默认值：**
- `text` / `textarea` / `richtext`：标签里的文字是默认值
- `image` / `video` / `audio` / `embed`：`src` 属性值是默认值
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

**图标类型**（`data-type="icon"`）：元素内含多个 SVG，配合 [`data-when`](#6-data-when) 互斥组定义可选图标集。编辑器显示图标选择器，用户选中的值驱动互斥组显隐。

```html
<div data-name="service-icon" data-type="icon">
  <svg data-when="icon=circuit"><!-- 电路图标 --></svg>
  <svg data-when="icon=code"><!-- 代码图标 --></svg>
  <svg data-when="icon=shield"><!-- 盾牌图标 --></svg>
  <svg data-when="icon" data-type="default"><!-- 默认图标 --></svg>
</div>
```

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

开放**结构性 CSS 变量**给用户调整。字号、颜色、间距等设计细节固定在 `.css` 里，不暴露编辑。想开放给用户的结构选择（列数、图文方向），用 CSS 变量 + `data-style` 声明 + 全局注册表。

```html
<!-- 开放列数 + 图文方向 -->
<section data-name="features" data-type="list"
         data-style="cols,dir"
         style="--cols: 3; --dir: row">
  ...
</section>
```

**约定：**
- `data-style="dir"` ↔ CSS `--dir`（加 `--` 前缀，一一对应）
- 默认值只写在 CSS 的 `var(--dir, row)` 里，HTML 和注册表不重复
- 用户改 → 写到元素 `style`；重置 → 删掉 `style` 里的变量，CSS 自动回落
- 没进 `data-style` 的变量用户碰不到

**样式注册表：** `data-style` 只列开放了哪些变量，每个变量的控件类型、可选值、标签集中维护在一份全局 JS 注册表中：

```js
const STYLE_REGISTRY = {
  dir:  { label: "图文方向", control: "switch", default: "row",
          options: [{ value: "row", text: "图左文右" },
                    { value: "row-reverse", text: "图右文左" }] },
  cols: { label: "每行个数", control: "select", default: "3",
          options: [{ value: "2", text: "2" }, { value: "3", text: "3" }, { value: "4", text: "4" }] },
};
```

**该不该开放某个样式：** 两条标准都满足才加：
1. 用户**真的会想改**（`cols`/`dir` 会；`gap` 很少）
2. 改了**不会破坏一致性**（`cols`/`dir` 安全；`gap`/`padding`/字号 容易乱）

→ 只开放结构性选择；设计细节固定在 `.css`。按"变量"建表，不是按"block"建表——几个变量就几条，与 block 数量无关。

---

## 六、可见性控制

两种粒度的可见性控制：

| 机制 | 粒度 | 触发方式 | 不匹配时 |
|---|---|---|---|
| `data-hideable` | 整块 | 用户手动开关 | 加/删 `hidden` 属性 |
| `data-when` | 元素级 | 字段值自动判断 | 从输出中删除 |

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

### 6. `data-when`

根据字段值决定元素显隐。**不匹配时元素从输出中删除。**

| 写法 | 效果 |
|---|---|
| `data-when="field"` | 字段值非空即显示 |
| `data-when="field=value"` | 字段值等于 value 时显示 |
| `data-when="field=value1,value2"` | 字段值匹配任一逗号分隔值时显示 |

解析规则：按第一个 `=` 拆字段名和值，无 `=` 则为非空检查。

**适用场景：** 媒体类型切换、遮罩开关、联系方式显隐。

```html
<!-- 根据 type 字段值切换媒体类型 -->
<video data-when="type=video"
       data-name="video" data-type="video" src="..."></video>

<img data-when="type=image"
     data-name="cover" data-type="image" src="default.jpg">
```

### `data-type="default"`

互斥组兜底项。同父元素下多个 `data-when` 引用同名字段时构成**互斥组**——后处理只保留匹配的那一个。无匹配则保留 `data-type="default"` 项。

```html
<div data-name="icon" data-type="icon">
  <svg data-when="icon=circuit">...</svg>
  <svg data-when="icon=code">...</svg>
  <svg data-when="icon=shield">...</svg>
  <svg data-when="icon" data-type="default">...</svg>
</div>
```

| 规则 | 说明 |
|---|---|
| 互斥组判定 | 同一父元素下，`data-when` 值相同的所有元素构成一个互斥组 |
| 匹配逻辑 | 找到 `data-when` 值匹配当前字段值的 → 保留，删除组内其余 |
| 兜底逻辑 | 无匹配时保留 `data-type="default"`，删除其余；无 default 则全部删除 |
| 删除方式 | 从 HTML 中移除元素（不是 `hidden`），输出中不留痕迹 |

**section 级条件：** `data-when` 也可用于 section 级元素，从 section 级数据取值：

```html
<div class="hero-banner-overlay"
     data-when="overlay_enabled=true"></div>
```

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

### 7. `data-source`

`list` / `grid` 用 `data-source` 区分项从哪来：

| 值 | 类型 | 项从哪来 | 用户能干啥 |
|---|---|---|---|
| 省略 / `manual` | 手动 | HTML 写死 | 增/删/改每项 |
| 一个 URL | 动态 | fetch 该 URL 的 JSON | 只配查询（写在 URL 里） |

```html
<!-- 手动：菜单 -->
<nav data-name="main-menu" data-type="list" data-source="manual">
  <a data-name="item" data-type="text" data-href="/">首页</a>
</nav>

<!-- 动态：文章列表（查询写进 URL query，前端渲染器解释） -->
<section data-name="news" data-type="list"
         data-source="/data/articles.json?category=news&sort=date_desc&limit=9">
  <article data-name="post" data-type="group">
    <img data-name="cover" data-type="image" src="default.jpg">
    <h3 data-name="title" data-type="text" data-href="">文章标题</h3>
  </article>
</section>
```

**静态站要点：** 静态服务器忽略 `?` 参数，`articles.json?category=news` 返回的是整个文件。query 是给前端渲染器的指令——过滤/排序/截断在前端 JS 做。

### 8. `data-page-size` / `data-cols`

| 属性 | 适用 | 用途 | 默认 |
|---|---|---|---|
| `data-page-size` | `list` | 每页最多几条，超过则渲染器**自动追加页码** | 无（不分页） |
| `data-cols` | `grid` | 二维栅格列数 | — |

```html
<!-- 文章列表：3 列、每页 9 条 -->
<section data-name="news" data-type="list"
         data-page-size="9"
         data-style="cols" style="--cols: 3">
  ...
</section>
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
| `icon` | 叶子 | 图标选择 | data-when 互斥组 | 图标选择器 |
| `group` | 结构 | 复合项 | 子元素集合 | 整体编辑 |
| `list` | 结构 | 一维可重复列表 | 子元素×N | 增删项 + 编辑每项 |
| `grid` | 结构 | 二维可重复栅格 | 子元素×行×列 | 增删 + 编辑单元格 |
| `default` | 标记 | 互斥组兜底 | — | — |

叶子类型**自动推断**字段和控件，不需要额外声明。结构类型**组织子元素**，内部的叶子类型各自声明自己的 `data-type`。
