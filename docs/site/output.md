# 输出（生成的静态站）

构建器把 `sites/<name>/` 的源内容（见 [sites.md](sites.md)）加主题渲染成纯静态站，放在 `sites/<name>/output/`，导出即打包它。本文讲**产物长什么样**；怎么发布出去见 [publish.md](publish.md)。

## 一、目录结构（CDN 上的样子）

每个用户网站发布后在 CDN 上的样子（多语言示例）：

```text
company_a.com/
├── index.html              ← 根：JS 读 navigator.language 智能跳转；JS 禁用时展示手动语言选择页
│
├── en/                     ← 英文整站（自包含）
│   ├── index.html
│   ├── contact_us.html
│   ├── products.html       ← 产品列表页（全部条目已渲进 HTML，JS 做筛选/分页显隐）
│   ├── products/           ← 产品详情页（每条一个，按 slug）
│   │   ├── abc.html
│   │   └── ...
│   ├── asset/              ← 主题资源：css / js / fonts（子集化字体）
│   └── files/              ← 用户资源，可随意创建子目录
│       ├── image/
│       ├── datasheet/      ← 图纸 / 规格书
│       └── videos/
│
├── de/                     ← 德文整站（同样结构，资源完全独立）
│   └── ...
│
├── sitemap.xml             ← 含所有语言所有 URL + hreflang 信息
└── robots.txt
```

**核心原则：每个语言目录是自包含的整站，没有共享资源目录**。
单语言导出 = 复制 `/en/` 一个文件夹就能跑。资源按语言完全复制的理由见 [publish.md](publish.md)。

## 二、生成的页面与 URL

| 内容 | 生成路径 | 来源 |
| --- | --- | --- |
| 首页 | `/index.html` | `pages/home` |
| 独立页 | `/<页面>.html`，如 `/contact_us.html` | `pages/<页面>` |
| 产品列表 | `/products.html` | 数据集 `products` |
| 产品详情 | `/products/<slug>.html`，如 `/products/abc.html` | `products` 每条（按 `slug`） |
| 主题资源 | `/asset/`（css / js / fonts） | 主题 `static/` + 子集化字体 |
| 用户资源 | `/files/<自建目录>/`，如 `/files/image/`、`/files/datasheet/` | 用户上传，可随意建子目录 |

> `files/` 下用户可随意创建子目录（`image/`、`datasheet/`、`videos/`…），构建时原样带进静态站。

## 三、列表页 vs 详情页：渲染策略

数据块（产品列表、案例集等）输出**两种 HTML**：

| 输出       | 形式                                    | 用途                          |
| ---------- | --------------------------------------- | ----------------------------- |
| **详情页** | 每个条目一个预生成 HTML                 | SEO 关键，被搜索引擎抓取      |
| **列表页** | 一个 HTML，全部条目已渲进去 + 浏览器 JS | JS 只对 DOM 做筛选 / 排序 / 分页显隐 |

### 为什么这样分

- **详情页必须预生成**：访客通过 Google 搜"智能门锁 Pro"应直接命中详情页，JS 渲染抓不到内容
- **列表页也全量渲进 HTML**：早先打算用 `data.json` + JS 渲染，但那样列表页 HTML 是空壳、爬虫抓不到条目，伤 SEO，还多一个 json 产物。现在改成**构建期把所有条目直接渲进同一个列表 HTML**，JS 只对已有 DOM 做显隐——SEO 和交互都拿到，且更简单（少一个文件、少一套 JS 渲染器）。

### 列表页怎么不卡（几百条 + 图片）

- **分页**：JS 每页显示 N 条（`data-page-size`），其余置 `hidden`；翻页只是切换显隐，零网络请求。
- **筛选**：构建期把每条的可筛字段盖到 `data-f-*`（如 `data-f-tags`，tag 是用户建产品时自定义打的），JS 读它显隐，不取 json；筛选条按 distinct tag 自动生成，MVP 单选。
- **图片**：条目图片用原生 `loading="lazy"`（首屏除外）；被分页 / 筛选隐藏的条目，其图片不下载——所以即使几百条全在 DOM 里，首屏也只下当前可见的那几张。
- **降级**：关 JS → 列表展示全部条目、不分页，内容完整。

### 页面模块列表的搜索与分页

`/functions/`、`/modules/` 这类页面可能不是数据集列表，而是由很多页面模块组成：每个条目本身就是一个 `highlight_card` 等模块。此时不要把内容强行迁移到 `data_grid`，而是在页面 YAML 顶层启用 `module_list`。

`module_list` 的产物策略和数据集列表一致：全部模块已经在 HTML 里，浏览器 JS 只做搜索过滤和分页显隐，不请求后端、不取 JSON、不生成 `/page/2/`。关 JS 时全部模块可见。

区别在于作用对象：

| 能力 | 内容来源 | JS 作用对象 |
| --- | --- | --- |
| `data_grid` | `data/*.yaml` 数据集 | 数据集卡片，如 `.dg-card` |
| `module_list` | `pages/*.yaml` 的 `modules` 数组 | 页面模块 wrapper，如 `.builder-module[data-module-list-item]` |

编辑说明见 [module-list.md](module-list.md)，开发实现约定见 [../themes/layouts/module-list.md](../themes/layouts/module-list.md)。

### 这还算"静态网站"吗？算

「静态」指的是 **没有后端运行时**，不是「没 JS」：

- 内容（含全部列表条目）都在 HTML 里，CDN 直接给、爬虫直接抓
- JS 是静态资源，只做 DOM 显隐增强
- 平台死了，整套照样跑

### 一份数据，两份输出

数据源只有一份 `products.yaml`（含全部字段）。生成器**按需挑字段**：

```text
sites/<id>/data/products.yaml （含全部字段）
        │
        ├── 精简字段（name / image / summary / price / tags）
        │   → 全部渲进 /en/products.html（列表页，一个文件）
        │
        └── 全部字段 → /en/products/<slug>.html（每条一个详情页）
            含 description / specs / gallery 等完整内容
```

50 个产品 → 1 个列表 HTML（含 50 条）+ 50 个详情 HTML = **51 个文件**，
无论用户怎么筛、访客怎么翻页都在这一个列表页里搞定。

### 访客体验

```text
访客访问 /en/products.html
    ↓
浏览器加载（已含全部条目；首屏图懒加载、其余暂不下）
    ↓ 立即可见，且能被爬虫抓取
列表显示，含筛选 / 分页 UI
    ↓
点「下一页」 → JS 切换显隐 → 立刻显示，零网络请求
点某 tag   → JS 过滤显隐 → 立刻显示，零网络请求
点某产品   → 跳转 /products/<slug>.html → CDN 给 SEO 友好的详情页
```
