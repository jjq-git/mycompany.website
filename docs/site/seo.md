# SEO 与 AI 检索

小企业网站的搜索流量很关键 —— 主题要默认产出**搜索引擎友好** + **大模型友好**的产物，用户不用懂 SEO 也能拿到正确的输出。

## 一、整体策略：默认全部做对

用户不该看到任何"SEO 设置"开关。主题和发布器要做到：

- 每个页面有 `<title>` `<meta description>` `<link rel="canonical">`
- 每个页面有 OG / Twitter 卡片标签（社交分享好看）
- 站点级 `sitemap.xml`、`robots.txt`、`llms.txt` 自动生成
- 多语言用 `hreflang` 互链
- 结构化数据用 JSON-LD（Organization、Product、Article、BreadcrumbList）
- 图片有 `alt` 属性 + 优化尺寸（WebP / AVIF）
- 静态 HTML 直接含正文（不依赖 JS 渲染），LLM 爬虫无 JS 也能拿到完整内容
- 首屏 < 1 秒（影响 Core Web Vitals 排名）

这些不是"加分项"，是主题的及格线。

## 二、页面级 meta

每个页面 head 里固定模板：

```html
<title>{{ page.title }} - {{ company.name }}</title>
<meta name="description" content="{{ page.description }}">
<link rel="canonical" href="{{ canonical_url }}">

<!-- 多语言互链 -->
<link rel="alternate" hreflang="en" href="{{ url_en }}">
<link rel="alternate" hreflang="zh" href="{{ url_zh }}">
<link rel="alternate" hreflang="x-default" href="{{ url_en }}">

<!-- Open Graph (Facebook / LinkedIn / 微信预览) -->
<meta property="og:type" content="website">
<meta property="og:title" content="{{ page.title }}">
<meta property="og:description" content="{{ page.description }}">
<meta property="og:image" content="{{ og_image_url }}">
<meta property="og:url" content="{{ canonical_url }}">
<meta property="og:site_name" content="{{ company.name }}">

<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image">
```

字段来源：

| 字段 | 来源 |
| --- | --- |
| `page.title` | 页面 yaml 的 `title`，没填就用主题默认（如 "About - {company}"）|
| `page.description` | 页面 yaml 的 `description`，没填就用 `settings.company.tagline` |
| `og_image_url` | 页面 yaml 的 `og_image`，没填就用 `settings.company.default_og_image` |
| `canonical_url` | 发布时根据站点域名 + 路径自动算出 |

用户只填业务字段（标题、简介、封面图），SEO 标签由主题组合。

## 三、站点级文件

发布时自动生成：

### `sitemap.xml`

包含所有语言的所有页面（含数据集生成的详情页）。例：

```xml
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>https://com-a.mycompany.website/en/</loc>
    <xhtml:link rel="alternate" hreflang="en" href="https://com-a.mycompany.website/en/"/>
    <xhtml:link rel="alternate" hreflang="zh" href="https://com-a.mycompany.website/zh/"/>
  </url>
  <url>
    <loc>https://com-a.mycompany.website/en/products/foo</loc>
    <lastmod>2026-05-01</lastmod>
  </url>
  ...
</urlset>
```

### `robots.txt`

```text
# 主流 AI 检索爬虫显式放开 (默认策略)
User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Bytespider
Allow: /

# 通用规则
User-agent: *
Allow: /
Disallow: /_preview/

Sitemap: https://com-a.mycompany.website/sitemap.xml
```

**关于 AI 爬虫为什么显式放开**：

AI 模型本身不会"记住"小公司网站（小站很难进入训练集）。但 ChatGPT / Claude / Perplexity / Gemini 等在有人提问时会**实时联网检索**——能不能被检索到，取决于这些 bot 能不能爬。

很多公司因版权焦虑一刀切屏蔽 AI 爬虫，结果有人问相关问题时 AI 永远找不到他们。我们主题默认全部 Allow，让小企业最大化曝光。需要屏蔽的用户可以在后台单独关。

`_preview/` 路径对所有爬虫屏蔽，避免泄漏未发布内容。

### `llms.txt`（AI 检索友好）

[llms.txt](https://llmstxt.org/) 是给 LLM 看的"网站说明书"，结构化总结整站，让 AI 在不爬全站的情况下了解公司。

```markdown
# Company A

> 一句话公司介绍（来自 settings.company.tagline）

## About
- [About](https://com-a.mycompany.website/en/about): 公司简介
- [Contact](https://com-a.mycompany.website/en/contact): 联系方式

## Products
- [Product Foo](https://com-a.mycompany.website/en/products/foo): 短描述
- [Product Bar](https://com-a.mycompany.website/en/products/bar): 短描述

## Blog
- [How we built X](https://com-a.mycompany.website/en/blog/x): 摘要
```

发布器从 `settings.yaml` + 各 dataset 自动汇总，无需用户填写。

## 四、结构化数据（JSON-LD）

放在每页 `</body>` 前。主题按页面类型选用：

| 页面类型 | Schema |
| --- | --- |
| 任何页 | `Organization`（公司信息，名字、Logo、社交链接） |
| 产品详情 | `Product`（名称、图片、品牌、价格） |
| 博客详情 | `Article`（标题、作者、发布时间、封面图） |
| 联系页 | `LocalBusiness`（地址、电话、营业时间） |
| 列表页 / 详情页 | `BreadcrumbList`（面包屑） |

例（产品详情）：

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{{ product.name }}",
  "image": "{{ product.image_url }}",
  "description": "{{ product.intro }}",
  "brand": { "@type": "Brand", "name": "{{ company.name }}" }
}
</script>
```

字段都是主题从 yaml 拿，不要用户写 JSON。

## 五、根域语言选择首页（关键 SEO 点）

根路径 `/` 必须返回**真实可读 HTML**，含两个语言版本的链接，别只放 JS 跳转 —— 大多数 LLM 爬虫（GPTBot / ClaudeBot / PerplexityBot）不跑 JS，纯 JS 跳转的根页对它们来说是空页面。

详见 [domains.md 第三节](../domains.md)。

## 六、性能指标（也是排名因素）

Google Core Web Vitals 直接进搜索排名：

| 指标 | 目标 | 主题怎么保证 |
| --- | --- | --- |
| LCP（最大内容绘制） | < 2.5s | 字体子集化、首屏图片预加载、HTML 内联关键 CSS |
| CLS（布局偏移） | < 0.1 | 图片必须带 `width` `height`，避免后加载推动布局 |
| INP（交互响应） | < 200ms | 主题 JS 极少（`< 50KB`），不引大框架 |

详见 [publish.md](publish.md) 的字体 / 图片优化章节。

## 七、用户不用做的事 vs 应该填的内容

**用户不用做：** 写 `<title>`、写 sitemap、配 robots、写 JSON-LD、改 hreflang。

**用户应该填（主题表单引导）：**

- 公司名、一句话简介（用作很多页的 fallback description）
- 默认 OG 封面图（社交分享时用）
- 每个页面 / 产品 / 文章的标题 + 简介 + 封面图
- 图片的 alt 文本（无障碍 + SEO）

主题表单要把这些字段标成"建议填写"，但不强制。
