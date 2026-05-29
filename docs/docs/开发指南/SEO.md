# SEO

> 本文是《开发指南》的第十章。返回总目录见 [README.md](README.md)。

---

## SEO 与 AI 检索

**小企业网站的搜索流量很关键。SEO 不是后期附加功能，是模板和发布器的默认行为。店主不需要懂 SEO，但模板和系统必须默认做对。**

本节是 SEO 的实施规划，按开发阶段分解。

### SEO 实施清单（按开发阶段）

#### M3 阶段：模板开发时就要做

这些由模板开发者（+AI）在写 HTML/CSS 时顺手完成，**店主无感知**：

| 任务 | 位置 | 说明 |
| --- | --- | --- |
| 语义化 HTML 标签 | `templates/*.html` | `<header>` `<nav>` `<main>` `<article>` `<section>` `<footer>`，不用全 `<div>` |
| `<title>` 模板 | `templates/_base.html` | `{% block title %}{{ page.title }} - {{ company.name }}{% endblock %}` |
| `<meta description>` | 同上 | 从页面 yaml 取，fallback 到公司简介 |
| OG / Twitter 卡片 | 同上 | `og:title` `og:description` `og:image` `twitter:card`，字段来源同上 |
| `<link rel="canonical">` | 同上 | 发布时自动填入完整 URL |
| 图片默认带 alt | 所有 `<img>` 标签 | `alt="{{ item.title | default(company.name) }}"`，即使店主没填也有兜底 |
| 图片带 width/height | 所有 `<img>` 标签 | 防 CLS（布局偏移），Google 排名因素 |
| 面包屑导航 | `templates/_base.html` 或各页面 | 每个页面都要有（SEO + 用户体验） |
| JSON-LD 结构化数据 | 每页 `</body>` 前 | Organization / Product / Article / LocalBusiness / BreadcrumbList，按页面类型选用 |
| 语义化 heading 层级 | 全部页面 | 每页只有一个 `<h1>`，`<h2>` `<h3>` 不跳级 |
| 移动端友好 | CSS（响应式） | Google Mobile-First Indexing |
| 关键 CSS 内联 | `_base.html` `<style>` | 首屏渲染的 CSS 内联到 HTML，减少渲染阻塞 |
| 字体子集化支持 | 模板不引用完整字体 | 字体路径通过模板变量注入，由 builder 替换为子集化后的字体 |

#### M4 阶段：Builder/发布时自动生成

这些由 `builder.py` 在渲染产出时自动生成（详见 [发布流程.md](发布流程.md)），**店主无感知**：

| 任务 | 说明 |
| --- | --- |
| `sitemap.xml` | 含所有语言所有页面 URL + `<lastmod>` + `hreflang`，自动提交到 Google/Bing |
| `robots.txt` | 默认 Allow 所有爬虫（含 AI 爬虫：GPTBot/ClaudeBot/PerplexityBot/Bytespider），Disallow `/_preview/` |
| `llms.txt` | 给 LLM 看的结构化网站说明书（公司简介 + 产品列表 + 页面链接），自动从 settings.yaml + dataset 汇总 |
| 根域语言选择首页 | 含真实链接 + `hreflang` + JS 跳转 + `<meta refresh>` 兜底，**不能纯 JS 跳转**（LLM 爬虫不跑 JS） |
| `canonical_url` 自动填入 | 根据站点域名 + 路径自动计算 |
| 图片自动压缩转 WebP | 上传时已处理，发布时按语言复制 |

#### M3-M4 阶段：店主可见的 SEO 相关项

店主在后台表单中看到的字段，**顺手引导填对**但不强制：

| 表单字段（模板引导） | 对应 SEO 用途 | 优先级 |
| --- | --- | --- |
| 公司名称 | `<title>` fallback、Organization schema | 必填 |
| 一句话公司简介 | `<meta description>` fallback | 建议填 |
| 默认 OG 封面图 | 社交分享时显示 | 建议填 |
| 每个页面的标题 | `<title>` + `og:title` | 建议填 |
| 每个页面的简介 | `<meta description>` + `og:description` | 建议填 |
| 每个产品/文章的标题 + 简介 + 封面图 | Product/Article schema | 建议填 |
| 图片 alt 文本 | SEO + 无障碍 | 建议填 |

**店主不需要接触的概念**（由模板和 builder 自动处理）：`sitemap`、`robots.txt`、`hreflang`、`canonical`、`JSON-LD`、`OG标签`。

#### 性能指标（Google 排名因素）

| 指标 | 目标 | 保证方式 |
| --- | --- | --- |
| LCP（最大内容绘制） | < 2.5s | 字体子集化、首屏图片预加载、关键 CSS 内联 |
| CLS（布局偏移） | < 0.1 | `<img>` 必须带 `width` `height` |
| INP（交互响应） | < 200ms | 模板 JS 极少（`< 50KB`），不引大框架 |

#### AI 爬虫策略

默认**全部 Allow**（让 AI 能检索到店主网站，最大化曝光）。需要屏蔽的店主可在后台"SEO 设置"中单独关。

```
GPTBot: Allow | ClaudeBot: Allow | PerplexityBot: Allow | Bytespider: Allow
Google-Extended: Allow | OAI-SearchBot: Allow
```

所有爬虫统一 Disallow `/_preview/`，防止未发布内容泄漏。
