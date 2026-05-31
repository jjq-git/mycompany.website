# 企业静态官网 — Block 示例库

> 全部遵循 [data-attributes.md](data-attributes.md) 规范：
> 内容 `data-name`/`data-type`/`data-href` · 样式 CSS 变量 `--xxx`（+ `data-style` 声明）· 行为 `data-page-size` · 能力 `data-hideable`。
> `list`/`grid` 内「带 `data-name` 的直接子元素」= 项模板，渲染时按数据复制。

**对齐约定**：

- **必显块**（Header / Footer / 文章正文 / 产品正文 / Contact）→ **不加** `data-hideable`
- 其余营销/展示块 → 加 `data-hideable`（用户可开关）
- 流式多列块 → 加 `data-style="cols"`（开放列数）；图文块 → `data-style="dir"`（开放左右对调）；需背景图 → `data-style="bg"`；需背景色 → `data-style="bg-color"`

---

## 一、全局

> Header / Footer 是 block（写在 `blocks/header/`、`blocks/footer/`，必显）。导航菜单用保留数据源 `data-source="menu"`（builder 从 `settings.menu` 注入 label/url/active），语言切换用 `data-source="languages"`——不靠用户在 block 里手填。页眉 / 页脚的不同排版走 block 变体（`variants/*.html`）。详见 [data-attributes.md](data-attributes.md#6-data-source)。

### Header 顶部导航（必显）

```html
<header data-name="header" data-type="group">
  <img data-name="logo" data-type="image" data-href="/" src="logo.svg">
  <nav data-name="nav" data-type="list" data-source="menu">   <!-- 导航来自 settings.menu，builder 注入 label/url/active -->
    <a data-name="item" data-type="text">首页</a>
  </nav>
  <nav data-name="lang-switcher" data-type="list" data-source="languages">  <!-- 语言切换，builder 注入已启用语言；单语言时自动不渲染 -->
    <a data-name="lang" data-type="text">中文</a>
  </nav>
  <a data-name="cta" data-type="text" data-href="/contact">联系我们</a>
</header>
```

### Footer 页脚（必显）

```html
<footer data-name="footer" data-type="group">
  <img data-name="logo" data-type="image" src="logo.svg">

  <div data-name="link-cols" data-type="list" data-style="cols" style="--cols: 4">
    <div data-name="col" data-type="group">
      <span data-name="col-title" data-type="text">产品</span>
      <a data-name="link" data-type="text" data-href="/p1">产品一</a>
    </div>
  </div>

  <ul data-name="social" data-type="list">
    <a data-name="icon" data-type="image" data-href="https://weibo.com" src="weibo.svg"></a>
  </ul>

  <span data-name="copyright" data-type="text">© 2026 公司名 版权所有</span>
</footer>
```

### Breadcrumb 面包屑

```html
<nav data-name="breadcrumb" data-type="list" data-hideable>
  <a data-name="crumb" data-type="text" data-href="/">首页</a>
</nav>
```

---

## 二、首页 / 落地页

### Hero 首屏

```html
<section data-name="hero" data-type="group" data-style="bg" data-hideable
         style="--bg: url('hero.jpg')">
  <h1 data-name="title" data-type="text">用技术驱动未来</h1>
  <p  data-name="subtitle" data-type="text">一句话价值主张</p>
  <a  data-name="cta" data-type="text" data-href="">立即咨询</a>
</section>
```

### Carousel 轮播图

```html
<div data-name="carousel" data-type="list" data-hideable>
  <div data-name="slide" data-type="group">
    <img  data-name="img"  data-type="image" data-href="/promo" src="s1.jpg">
    <span data-name="text" data-type="text">活动标题</span>
  </div>
</div>
```

### Features 核心优势 / 服务

```html
<section data-name="features" data-type="list"
         data-hideable data-style="cols" style="--cols: 3">
  <div data-name="feature" data-type="group">
    <img data-name="icon"  data-type="image" src="icon1.svg">
    <h3  data-name="title" data-type="text">高性能</h3>
    <p   data-name="desc"  data-type="text">说明文字……</p>
  </div>
</section>
```

### Stats 数据统计

```html
<section data-name="stats" data-type="list"
         data-hideable data-style="cols" style="--cols: 4">
  <div data-name="stat" data-type="group">
    <span data-name="num"   data-type="text">1000+</span>
    <span data-name="label" data-type="text">服务客户</span>
  </div>
</section>
```

### About 关于简介（图文，可左右对调）

```html
<section class="media"
         data-name="about" data-type="group"
         data-hideable data-style="dir" style="--dir: row">
  <img data-name="pic"  data-type="image" src="about.jpg">
  <div data-name="text" data-type="text">公司简介文字……</div>
</section>
```

### CTA 行动召唤

```html
<section data-name="cta-band" data-type="group" data-hideable>
  <h2 data-name="title" data-type="text">准备好开始了吗？</h2>
  <a  data-name="btn" data-type="text" data-href="/contact">免费试用</a>
</section>
```

### Logo 墙 客户 / 合作

```html
<section data-name="logo-wall" data-type="grid" data-cols="6" data-hideable>
  <img data-name="logo" data-type="image" data-href="https://x.com" src="c1.png">
</section>
```

### Testimonials 客户评价

```html
<section data-name="testimonials" data-type="list"
         data-hideable data-style="cols" style="--cols: 3">
  <div data-name="item" data-type="group">
    <img  data-name="avatar" data-type="image" src="u1.jpg">
    <p    data-name="quote"  data-type="text">很好用……</p>
    <span data-name="name"   data-type="text">张三 · CEO</span>
  </div>
</section>
```

---

## 三、信息展示

### Team 团队成员

```html
<section data-name="team" data-type="grid" data-cols="4" data-hideable>
  <div data-name="member" data-type="group">
    <img  data-name="photo" data-type="image" src="p1.jpg">
    <span data-name="name"  data-type="text">李四</span>
    <span data-name="role"  data-type="text">技术总监</span>
  </div>
</section>
```

### Timeline 发展历程

```html
<section data-name="timeline" data-type="list" data-hideable>
  <div data-name="event" data-type="group">
    <span data-name="year" data-type="text">2020</span>
    <p    data-name="desc" data-type="text">公司成立</p>
  </div>
</section>
```

### Steps 流程步骤

```html
<section data-name="steps" data-type="list"
         data-hideable data-style="cols" style="--cols: 4">
  <div data-name="step" data-type="group">
    <span data-name="no"    data-type="text">1</span>
    <h4   data-name="title" data-type="text">需求沟通</h4>
    <p    data-name="desc"  data-type="text">说明……</p>
  </div>
</section>
```

### Pricing 价格方案

```html
<section data-name="pricing" data-type="grid" data-cols="3" data-hideable>
  <div data-name="plan" data-type="group">
    <h3   data-name="name"  data-type="text">基础版</h3>
    <span data-name="price" data-type="text">¥99/月</span>
    <!-- 功能点用 richtext 叶子，不嵌套 list（满足"不支持嵌套 list/grid"约束），用户自己写带勾/划线的列表 -->
    <div  data-name="feats" data-type="richtext"><ul><li>功能一</li><li>功能二</li></ul></div>
    <a data-name="btn" data-type="text" data-href="/buy">购买</a>
  </div>
</section>
```

### FAQ 常见问题

```html
<section data-name="faq" data-type="list" data-hideable>
  <details data-name="qa" data-type="group">
    <summary data-name="q" data-type="text">问题？</summary>
    <p       data-name="a" data-type="text">答案……</p>
  </details>
</section>
```

### Honors 资质 / 证书

```html
<section data-name="honors" data-type="grid" data-cols="5" data-hideable>
  <img data-name="cert" data-type="image" src="cert1.jpg">
</section>
```

---

## 四、列表 / 内容型（带分页）

> 列表全量渲进**一个 HTML 页**，JS 对 DOM 做分页 / 筛选显隐（不生成 data.json，内容在 HTML 里、SEO 吃得到）。条目图片加 `loading="lazy"`（首屏除外），被分页 / 筛选隐藏的条目不下载图。筛选维度 = 用户自定义 tag，构建期盖到条目的 `data-f-tags`。详见 [data-attributes.md](data-attributes.md#6-data-source)。

### News 新闻 / 动态列表

```html
<section data-name="news" data-type="list"
         data-source
         data-hideable data-style="cols" data-page-size="9" style="--cols: 3">
  <article data-name="post" data-type="group" data-f-tags="">   <!-- 项模板；data-f-tags 由 builder 注入，供 JS 筛选 -->
    <img  data-name="cover"   data-type="image" data-href="" loading="lazy">   <!-- ← 记录.cover/.url -->
    <h3   data-name="title"   data-type="text" data-href="">新闻标题</h3>
    <span data-name="date"    data-type="text">2026-05-27</span>
    <p    data-name="excerpt" data-type="text">摘要……</p>
  </article>
</section>
```

### Products 产品 / 案例列表

```html
<section data-name="products" data-type="list"
         data-source
         data-hideable data-style="cols" data-page-size="12" style="--cols: 4">
  <div data-name="product" data-type="group" data-f-tags="">   <!-- 项模板；data-f-tags 由 builder 注入，供 JS 按 tag 筛选 -->
    <img data-name="img"  data-type="image" data-href="" loading="lazy">   <!-- ← 记录.img/.url -->
    <h4  data-name="name" data-type="text" data-href="">产品名</h4>
  </div>
</section>
```

### Article 文章详情（必显，页面主体）

```html
<article data-name="article" data-type="group">
  <h1   data-name="title" data-type="text">文章标题</h1>
  <span data-name="meta"  data-type="text">2026-05-27 · 作者</span>
  <img  data-name="cover" data-type="image" src="cover.jpg">
  <div  data-name="body"  data-type="richtext">正文（富文本）……</div>
</article>
```

### Product 产品详情（必显，页面主体）

```html
<section data-name="product-detail" data-type="group">
  <div data-name="gallery" data-type="grid" data-cols="4">
    <img data-name="thumb" data-type="image" src="g1.jpg">
  </div>
  <h1 data-name="name" data-type="text">产品名</h1>
  <p  data-name="desc" data-type="text">描述……</p>
  <table data-name="spec" data-type="grid" data-cols="2">
    <td data-name="cell" data-type="text">参数</td>
  </table>
</section>
```

### Gallery 图片画廊

```html
<section data-name="gallery" data-type="grid" data-cols="4" data-hideable>
  <img data-name="photo" data-type="image" data-href="big1.jpg" src="thumb1.jpg">
</section>
```

### Video 视频展示

```html
<section data-name="video-block" data-type="group" data-hideable>
  <h2    data-name="title" data-type="text">公司宣传片</h2>
  <video data-name="clip"  data-type="video" src="intro.mp4"></video>
</section>
```

---

## 五、联系 / 转化

### Contact 联系方式（必显）

```html
<section data-name="contact" data-type="group">
  <span  data-name="addr"  data-type="text">地址：XX 市 XX 路 1 号</span>
  <span  data-name="phone" data-type="text">电话：400-000-0000</span>
  <span  data-name="email" data-type="text" data-href="mailto:hi@x.com">hi@x.com</span>
  <iframe data-name="map"  data-type="embed" src="https://map.example/embed?lng=..."></iframe>
</section>
```

### Map 单独地图

```html
<iframe data-name="map" data-type="embed" data-hideable
        src="https://map.example/embed?lng=..."></iframe>
```

---

## 速查表

### 类型使用

| 类型        | 哪些 block 用到                                  |
|-------------|--------------------------------------------------|
| `text`      | 几乎全部                                         |
| `image`     | logo / hero / 头像 / 封面 / 证书 / logo 墙       |
| `video`     | 视频展示                                         |
| `embed`     | 联系页地图 / 第三方视频                          |
| `group`     | 复合块（hero / 卡片 / 成员 / 计划…）             |
| `list`      | 导航 / 轮播 / 特性 / 评价 / 新闻 / 步骤          |
| `grid`      | 团队 / logo 墙 / 价格 / 画廊 / 资质 / 参数表     |

### 能力 / 配置

| 属性                    | 哪些 block 用到                                                        |
|-------------------------|------------------------------------------------------------------------|
| `data-href`             | 可点的 logo / 菜单 / 封面 / 标题 / 社交图标                            |
| `data-style="cols"`     | footer / features / stats / steps / testimonials / news / products     |
| `data-style="dir"`      | about 图文左右对调                                                     |
| `data-style="bg"`       | hero / cta-band / 任何需要背景图的区块                                 |
| `data-style="bg-color"` | 任何需要背景色的区块                                                    |
| `data-cols`             | logo 墙 / 团队 / 价格 / 画廊 / 资质 / 参数表（真阵列）                 |
| `data-page-size`        | news / products 列表分页                                               |
| `data-source`           | header nav=`menu`、语言切换=`languages`（保留源，builder 注入）；news/products 空值 = 数据驱动（后台选数据集）；其它手动列表=`manual` |
| `data-hideable`         | 除 Header / Footer / 文章正文 / 产品正文 / Contact 外的展示块          |
