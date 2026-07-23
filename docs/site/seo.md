# SEO 与 AI 检索

使用 AI 来生成 SEO 需要的内容，无需用户逐个完善。

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
<title>{{ page.title }} - {{ settings.title }}</title>
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
<meta property="og:site_name" content="{{ settings.title }}">

<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image">
```

字段来源：

| 字段 | 来源 |
| --- | --- |
| `page.title` | 页面 yaml 的 `title`，没填就用主题默认（如 "About - {settings.title}"）|
| `page.description` | 页面 yaml 的 `description`，没填就用 `settings.slogan` |
| `og_image_url` | 页面 yaml 的 `og_image`，没填就用 `settings.logo` |
| `canonical_url` | 发布时根据站点域名 + 路径自动算出 |

用户只填业务字段（标题、简介、封面图），SEO 标签由主题组合。

标题和简介长度只能作为搜索结果展示建议，不能作为 SEO 硬限制。Google 会根据设备宽度截取标题和摘要，因此后台应允许保存完整、自然的文本；超过约 60 个标题字符或 180 个简介字符时给出提示即可，不得截断英文单词、专有名词或未结束的句子。输入框可以保留较宽的防误输入上限，但不能把 60/180 当成搜索引擎规则。

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

> 一句话公司介绍（来自 settings.slogan）

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
  "brand": { "@type": "Brand", "name": "{{ settings.title }}" }
}
</script>
```

字段都是主题从 yaml 拿，不要用户写 JSON。

## 五、根域语言选择首页（关键 SEO 点）

根路径 `/` 返回**真实可读 HTML**，含所有启用语言的手动选择链接。JS 启用时读 `navigator.language` 智能跳转到匹配的语言版本；JS 禁用时（多数 LLM 爬虫：GPTBot / ClaudeBot / PerplexityBot）停留在选择页，仍能爬取到所有语言入口链接。不要只放 JS 跳转而不留可读兜底。

详见 [domains.md 第三节](../cloud/domains.md)。

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

## 八、多语言 SEO 健康检查实施基线

### 8.1 产品目标

SEO 内容按语言独立生成，后台按整个站点统一检查：

- 用户不需要切换语言逐个检查；
- 一个逻辑页面在 SEO 工作台中只显示一行；
- 系统自动扫描全部启用语言；
- 默认只展开存在异常的语言；
- 技术问题由系统处理，内容问题跳转到对应语言编辑器。

第一版只支持 `claude` 和 `dengtec` 两套正式模板。`airbnb`、`apple`、`notion` 等其他模板不在第一版修改和验收范围内。

第一版不做完整内容指纹、单页增量构建、NLP 语言识别、批量 AI 翻译、批量覆盖现有 SEO 内容，也不修改数据库结构。

### 8.2 实施前只读排查结论

现有有效站点的数据集共有 593 条记录，其中 362 条有稳定 `id`，231 条旧记录没有 `id`。缺少 `id` 的记录主要来自 `products`、`posts` 和 `portfolio`，但均有 slug，且现有多语言版本的 slug 保持一致。

现有 canonical 有两个边界问题：

- 预览构建会把 `/preview/<site>/...` 写进 canonical；
- 正式构建在既无自定义域名、也无平台域名时会生成相对 canonical。

HTML hreflang 与 sitemap alternate 已经同源，均来自 builder 的 `seo.alternate_urls`。现有产物中带 canonical 的 499 个页面逐项一致。因此不需要分别维护两套 URL 逻辑，真正需要修复的是共同的跨语言页面映射源。

### 8.3 正式地址与部署地址分离

builder 必须区分：

| 地址 | 职责 |
| --- | --- |
| `base_url` | 预览资源、站内导航和预览路由前缀 |
| `public_site_url` | canonical、hreflang、sitemap、OG URL 和 JSON-LD |

`public_site_url` 的取值顺序：

1. 站点自定义域名；
2. 站点的平台子域名；
3. 两者均不可用时产生明确的构建诊断，不把相对地址当成正常 canonical。

即使检查的是预览产物，SEO 标签也必须使用正式公开地址，预览路径不能进入 canonical、hreflang 或 sitemap。

后台的 `custom_domain` 只告诉 builder 网站的正式公开地址，不负责上传 OSS、配置 CDN、配置 DNS、部署 HTTPS 证书或刷新缓存。阿里云部署链路与 SEO 地址生成是两个独立职责。

站点 6 的正式地址是 `https://www.dengtec.com`，应保留 `custom_domain = www.dengtec.com`。删除或改错该配置后重新导出，可能导致 canonical、hreflang 和 sitemap 指向平台域名或相对路径。

### 8.4 跨语言页面身份与 URL 映射

builder 在渲染前收集所有语言的页面任务，建立统一映射。普通页面使用 `page_key`，详情页采用兼容身份：

```text
有稳定 id
→ dataset_key + id

没有 id，但各语言 slug 完全一致
→ dataset_key + slug

没有 id，且各语言 slug 不一致
→ 不猜测对应关系，不生成该详情页 hreflang，并记录构建诊断
```

第一版不批量回填旧记录的 `id`，避免为了 SEO 检查引入数据迁移。有稳定 `id` 的新内容可以支持各语言使用不同 slug；旧内容继续使用一致 slug 兼容。

页面映射示例：

```text
product:128
├── zh-CN → https://example.com/zh-CN/products/静音舱/
├── zh-TW → https://example.com/zh-TW/products/靜音艙/
└── en    → https://example.com/en/products/silent-booth/
```

映射规则：

- canonical 指向当前语言页面自身；
- canonical 必须是绝对地址；
- hreflang 只包含真实存在的对应页面；
- hreflang 必须双向对应；
- `x-default` 指向真实存在的默认语言页面；
- HTML hreflang、canonical 与 sitemap alternate 共用同一映射；
- 页面缺失、身份重复、路径冲突进入构建报告；
- 构建存在页面失败时，不继续给出正常 SEO 结论。

### 8.5 builder 显式记录语言回退

语言回退由 builder 判断，SEO 检查器不复制 YAML 合并逻辑，也不直接读取源 YAML。

builder 记录以下明确、可证明的回退：

- 当前语言页面不存在，使用默认语言页面；
- 当前语言数据集不存在，使用默认语言数据；
- 当前语言最终 SEO 标题或简介来自默认语言；
- 当前语言公司简介来自默认语言。

以下情况不视为语言错误：

- 共享菜单结构和页面模板；
- Logo、图片等非文本资源；
- 公司品牌名保持原文；
- 没有手写 description，但能从当前语言正文生成。

诊断记录至少包含：

```json
{
  "page_id": "page:about",
  "lang": "en",
  "field": "page_content",
  "source_lang": "zh-CN",
  "reason": "localized_page_missing",
  "severity": "error"
}
```

最近成功构建时间和回退诊断保存在内部状态目录，例如 `instance/build_meta/<site_id>.json`。该文件不进入导出 ZIP、OSS、CDN 或公开站点。

语言回退诊断使用独立通道，不复用当前会阻止发布的构建失败 `report`，避免普通回退警告直接导致发布失败。

### 8.6 模板输出契约

第一版只统一 `claude` 和 `dengtec`。builder 向模板提供：

```text
seo.title
seo.description
seo.canonical_url
seo.alternate_urls
seo.image
seo.site_name
seo.type
seo.json_ld
```

模板只负责输出 title、description、canonical、hreflang、Open Graph、Twitter Card 和 JSON-LD，不自行推算正式 URL 或跨语言关系。

### 8.7 构建产物新鲜度

第一版使用递归 mtime 粗比较，不提前实现完整内容指纹。

比较范围：

- `sites/<site_id>/` 下的站点内容和资源；
- 当前 `claude` 或 `dengtec` 模板目录；
- builder 及直接构建依赖；
- SQLite 文件修改时间；
- 最近一次成功构建时间。

处理规则：

```text
产物缺失或任一输入更新
→ 标记为脏
→ 全量构建全部启用语言
→ 构建成功后执行检查

产物未过期
→ 直接检查现有产物

构建失败
→ 显示“产物不可检查”
→ 不使用旧产物给出 SEO 结果
```

完整构建指纹、精确依赖追踪和页面级增量构建属于后续优化。

### 8.8 多语言只读检查器

检查器只读取最新 HTML、`sitemap.xml`、`robots.txt`、`llms.txt` 和 builder 构建诊断，不修改用户内容。

“需要处理”的问题：

- 页面不存在或构建失败；
- title 缺失；
- canonical 缺失、错误、不是绝对地址或没有指向自身；
- hreflang 指向不存在页面或没有双向对应；
- sitemap 缺少实际页面，或 sitemap alternate 与 HTML hreflang 不一致；
- 页面意外包含 `noindex`；
- `robots.txt` 屏蔽全站；
- 当前语言明确回退到其他语言内容；
- 详情数据无法建立稳定语言对应。

“建议优化”的问题：

- description 缺失或长度不理想；
- title 长度不理想或重复；
- H1 数量异常；
- 标题层级跳级；
- 内容图片缺少 alt；
- OG / Twitter 信息不完整；
- JSON-LD 缺失、无法解析或字段不足；
- `llms.txt` 内容不足。

页面综合状态由最严重问题决定，不用平均分掩盖某个语言的问题。普通优化建议不阻止发布。

### 8.9 后台前端对接

SEO 工作台不再由顶部当前语言过滤。每个逻辑页面显示一行：

| 页面 | 综合状态 | 语言覆盖 |
| --- | --- | --- |
| 首页 | 可发布 | 3/3 |
| 产品中心 | 建议优化 | 3/3 |
| 联系我们 | 需要处理 | 2/3 |

展开页面后显示各语言明细，默认只展开异常语言。问题项可以直接进入对应语言的页面编辑器、详情编辑器或 SEO 编辑区。

统一检查接口：

```text
POST /seo/check?site=<site>
```

接口负责：

1. 判断模板是否受支持；
2. 判断产物是否新鲜；
3. 必要时执行全量构建；
4. 检查所有启用语言；
5. 返回统一 JSON 报告。

`GET /seo/workspace` 只渲染工作台外壳。现有按语言的 SEO 保存和生成接口继续复用。后端为每个语言结果直接提供 `save_url`、`generate_url`、`edit_url` 和 `preview_url`，前端不自行拼接地址。

后台继续使用 Flask、Jinja2 和 vanilla JS，不引入新的前端框架。

### 8.10 已有站点兼容与阿里云部署

修改本地 builder 或后台代码不会自动改变已经部署到 OSS/CDN 的静态文件。只有重新导出并上传后，线上站点才会采用新逻辑。

站点 6 当前三种语言的 109 个详情内容均能对应，未发现语言间 slug 差异或缺少对应记录，因此新版构建原则上不会改变其页面 URL。

站点 6 再次部署前必须：

1. 在独立临时目录构建新版；
2. 比较新旧文件路径和 sitemap URL 集合；
3. 比较 canonical 与 hreflang；
4. 验证三种语言的首页、列表页和详情页；
5. 保留旧版完整 ZIP；
6. 上传阿里云后检查线上 HTML 和 sitemap；
7. 验证完成后再刷新 CDN 缓存。

没有自定义域名的站点仍可生成和部署静态文件，但必须有可用的平台子域名才能输出正确的绝对 canonical。没有任何正式公开地址时，应显示配置错误，而不是静默生成相对 SEO URL。

### 8.11 实施顺序

1. 分离预览地址与正式 SEO 地址；
2. 建立多语言页面身份和 URL 映射；
3. 修复 canonical、hreflang 与 sitemap；
4. 增加 builder 回退诊断；
5. 统一 `claude`、`dengtec` 模板输出；
6. 增加 mtime 新鲜度判断；
7. 实现多语言只读检查器；
8. 实现统一检查接口和 SEO 工作台；
9. 接入发布前严重问题校验；
10. 后续再实现完整指纹、增量构建和安全自动修复。

构建器、模板、检查器、后台界面和发布校验应分别实施和验证，不混成一次大改。

### 8.12 验收标准

- 同一逻辑页面的全部语言只显示一行汇总；
- 产物未变化时检查不会重复构建；
- 源数据变化后检查会先全量构建；
- 构建失败时不会检查旧产物；
- canonical 使用正式绝对地址；
- sitemap 与 HTML hreflang 一致；
- hreflang 不指向不存在页面；
- 旧数据没有 `id` 时仍可通过一致 slug 正常工作；
- 站点 6 原有页面路径和 URL 数量不变；
- 问题能够跳转到正确语言编辑器；
- 普通 SEO 建议不阻止发布。
