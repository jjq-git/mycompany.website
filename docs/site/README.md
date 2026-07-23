# site —— 一个用户站点（源 → 产物 → 发布）

一个用户站点从源内容到上线的全过程：填内容 → 构建成静态站 → 发布 → SEO / AI 检索优化。

## 文档

| 文档 | 讲什么 |
| --- | --- |
| [sites.md](sites.md) | 站点源内容模型：`sites/<name>/` 的 settings / pages / data |
| [output.md](output.md) | 生成的静态站：目录结构、页面 URL、列表 / 详情渲染策略 |
| [publish.md](publish.md) | 发布：资源语言策略、字体 / 图片优化、CDN、自定义口子 |
| [aliyun-oss-deployment.md](aliyun-oss-deployment.md) | 阿里云 OSS 人工部署操作手册：构建、检查、备份、上传、验证和回滚 |
| [seo.md](seo.md) | SEO + AI 检索（sitemap、hreflang、llms.txt 等） |
| [LLM.md](LLM.md) | LLM / AI 爬虫检索优化（占位，待补） |
| [module-list.md](module-list.md) | 页面模块列表搜索与分页：适用于 `/functions/`、`/modules/` 这类由多个图文模块组成的页面 |
| [i18n.md](i18n.md) | 多语言 + AI 翻译用户网站内容（Phase 2） |

## 工作流

```mermaid
flowchart LR
    A[源内容<br/>sites.md] --> B[构建渲染]
    A -.->|AI 翻译| M[多语言<br/>i18n.md]
    M -.-> B
    B --> C[静态产物<br/>output.md]
    C --> D[发布 / CDN<br/>publish.md]
    C --> E[SEO / AI 检索<br/>seo.md · LLM.md]
```
