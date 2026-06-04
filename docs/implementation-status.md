# 功能实现状态

> 本文对比**参考文档目标**与**当前代码实际**，逐项标注实现状态。最后更新：2026-06-03。

---

## 一、Block 系统（data-* 声明式）

### 已实现

| 功能 | 状态 | 说明 |
|------|------|------|
| data-* 属性解析 | 完成 | `block_parser.py` 用 Python stdlib HTMLParser + 自定义 _DomBuilder 栈解析 |
| 14 个 data-* 属性支持 | 完成 | 比参考文档的 8 个多 6 个：`data-href-template`、`data-fallback`、`data-from`、`data-bg`、`data-bg-color`、`data-text-align` |
| 双路径渲染 | 完成 | `builder.py` 支持 data-* 块（Python 渲染器）和旧 Jinja2 块，`ENABLE_DATA_ATTR_BLOCKS` 配置开关 |
| 5 步后处理管线 | 完成 | 字段注入 → 列表展开 → 可见性 → 样式注入 → 清理 |
| 数据集驱动渲染 | 完成 | `data-source` 属性支持，构建期把数据集条目渲进 HTML |
| Schema 缓存 | 完成 | `_SCHEMA_CACHE` 按构建周期缓存，避免重复解析 |
| 安全 href 校验 | 完成 | 正则白名单防 XSS |
| 样式注册表 | 完成 | 5 个 CSS 变量 token（cols, dir, bg, bg-color, text-align） |
| 图标注册表 | 完成 | 39 个 SVG 图标 |

### 部分实现

| 功能 | 状态 | 说明 |
|------|------|------|
| Block 转换覆盖率 | 14/15 | `item_detail` 有 data-* 模板但未完全转换，`header` 仍为 Jinja2 |

### 额外（超出参考文档）

| 功能 | 说明 |
|------|------|
| `data-href-template` | URL 模板支持占位符 `{key}`，如 `{slug}` |
| `data-fallback` | 字段回退链，如 `title←name` |
| `data-from` | 上下文路径解析，如 `settings:contact` 从 settings 读取 |

---

## 二、后台 Dashboard

### 已实现

| 功能 | 状态 | 说明 |
|------|------|------|
| 三栏布局 | 完成 | 左导航(240px) + 中预览(iframe) + 右面板(380px) |
| 拖拽分隔条 | 完成 | 左栏 60-480px 范围拖拽，右面板 240-900px 范围拖拽 |
| 拖拽遮罩 | 完成 | `#dragOverlay` (position:fixed, z-index:9999) 解决 iframe 吞鼠标事件 |
| 设备模拟器 | 完成 | 桌面/平板/手机三档切换，改变 iframe 宽度 |
| 侧栏折叠 | 完成 | 240px→60px，localStorage 记忆 + hover tooltip |
| Fragment 渲染 | 完成 | `?_fragment=1` 参数，46 个路由支持，`loadPanel()` AJAX 加载 |
| Schema 驱动表单 | 完成 | `panel_page_edit.html` 对 data-* 块自动生成编辑表单 |
| Block 模板库 | 完成 | 弹窗式模板选择器，按类型筛选 |
| 内容/样式分 tab | 完成 | 编辑面板左右 tab 切换 |
| 表单 AJAX 提交 | 完成 | fetch 拦截 + CSRF 包装 |
| 颜色选择器 | 完成 | 自定义实现 |
| 数据集面板 | 完成 | `panel_data_list.html` 通用 CRUD |
| 图片上传 | 完成 | WebP 自动转换 |

### 未实现（参考文档目标）

| 功能 | 说明 |
|------|------|
| 浏览器风格多 tab 预览 | 参考 `base.html.md` 描述的多 tab 切换，当前只有单页预览 |
| 后台界面多语言 | Flask-Babel 中/英双语，当前界面文案写死中文 |
| 平台管理员用户管理 | 参考 `users.html.md`，当前 M1 占位鉴权 |

---

## 三、数据层

### 已实现

| 功能 | 状态 | 说明 |
|------|------|------|
| 数据分两层 | 完成 | 数据库（平台元数据）+ 磁盘 YAML（网站内容） |
| 站点磁盘存储 | 完成 | `sites/<name>/` 下 settings.yaml + pages/ + data/ + assets/ |
| 魔法链接登录 | 完成 | 邮箱 → token 哈希 → 邮件 → 自动登录 |
| 种子数据拷贝 | 完成 | 建站时 `shutil.copytree` 整个 `seed_data/` |

### 未实现（参考文档目标）

| 功能 | 说明 |
|------|------|
| Template → Theme 术语重命名 | 模型类、表名、配置键、CLI 命令、目录名全部待改 |
| i18n/<lang>/ seed 结构 | 当前为 `seed_data/` 单套，目标为每语言独立一套 `i18n/<lang>/` |
| Theme 表字段补全 | `languages`、`level`、`tags`(数组)、`author` 等字段待加 |
| Site 表字段补全 | `domain`、`expires_at`、`review_status` 等字段待加 |
| User 表字段补全 | `phone`、`level` 待加 |
| settings schema 拍扁 | `company.name`→`title`、`company.tagline`→`slogan` 待改 |

---

## 四、构建与发布

### 已实现

| 功能 | 状态 | 说明 |
|------|------|------|
| Jinja2 静态渲染 | 完成 | builder 渲染所有页面为静态 HTML |
| 模块排序 | 完成 | `page.modules` 按 `order` 排序后渲染 |
| 菜单解析 | 完成 | `menu.py` 解析 `settings.menu` 的 `{type, target}` 为含 `url`/`active` 的导航 |

### 未实现

| 功能 | 说明 |
|------|------|
| 多语言站点构建 | 每语言独立目录（`/en/`、`/zh/`）的渲染 |
| 字体子集化 | fonttools/pyftsubset，按语言提取用到的字符 |
| CDN 上传 | 阿里云 OSS + CDN 增量上传 |
| 发布历史与回滚 | 版本快照 + 回滚机制 |
| sitemap.xml 生成 | 含 hreflang 的多语言 sitemap |
| robots.txt 生成 | 含 AI 爬虫显式放开的 robots |
| llms.txt 生成 | AI 检索友好的结构化摘要 |
| JSON-LD 结构化数据 | Organization/Product/Article/BreadcrumbList |
| 导出 ZIP | 整站打包下载 |
| 自定义 HTML 块 | 用户粘贴第三方代码 |
| head 注入 | 百度统计/Google Analytics |
| 全站自定义 CSS | 用户微调样式 |
| 预览 token | `_preview/<token>/` 一次性预览链接 |

---

## 五、主题系统

### 已实现

| 功能 | 状态 | 说明 |
|------|------|------|
| 主题目录结构 | 完成 | `site_templates/<name>/` 含 layouts/ + blocks/ + seed_data/ + static/ |
| 主题扫描 | 完成 | `template_loader.py` 扫描目录同步到数据库 |
| Block 扫描 | 完成 | `scan_blocks()` 识别 data-* 块并预解析 schema |
| meta.yaml 解析 | 完成 | 基本字段（name, version, industry 等） |

### 未实现

| 功能 | 说明 |
|------|------|
| translations.yaml 机制 | 主题 UI 文案（`t.*`）的多语言翻译文件 |
| `meta.yaml` 字段补全 | `languages`、`level`、`tags`(数组)、多语言 `description` 等 |
| `preview/cover.webp` 约定 | 后台列表缩略图 |
| Header/Footer 作为 block | header 仍是 Jinja2 模板，未转为 data-* block |
| 变体系统 | header/footer 按 `settings.header.variant` 切换排版 |
| 主题上传 ZIP 安装 | 管理员后台上传主题包 |

---

## 六、多语言与 AI 翻译（Phase 2）

### 状态：全部未实现

| 功能 | 说明 |
|------|------|
| 多语言站点构建 | 按语言分目录输出静态站 |
| AI 翻译管线 | 源语言→目标语言逐条翻译 |
| 三层翻译策略 | glossary → override → AI 翻译 |
| hash 缓存 | 源文 hash 作 key，避免重复翻译 |
| HTML 保护 | BeautifulSoup 抠文本节点翻译后注回 |
| 词汇表 glossary.yaml | 品牌词/术语的翻译规则 |
| 语言切换器 | 访客端语言选择 UI |
| hreflang 标签 | 多语言页面互链 |
| 语言选择首页 | 根路径的可读 HTML（非纯 JS 跳转） |

---

## 七、托管与基础设施

### 部分实现

| 功能 | 状态 | 说明 |
|------|------|------|
| 子域规划 | 已设计 | `slug.mycompany.website` 方案已定，代码有 `SLUG_RESERVED` |
| SSL/ACME 流程 | 已设计 | `infrastructure.md` 详细设计了 DNS-01 + acme.sh 流程 |
| 阿里云 OSS + CDN | 已设计 | 共享 bucket 策略、CNAME 委派等已设计 |

### 未实现

| 功能 | 说明 |
|------|------|
| 实际发布到 CDN | 当前只生成 output/ 目录，未上传 |
| SSL 证书自动签发 | ACME DNS-01 自动化 |
| 自定义域名绑定 | 用户自带域名的 CNAME + 证书 |
| 预览 token 系统 | `_preview/<token>/` URL 机制 |

---

## 八、汇总

| 子系统 | 已完成 | 部分完成 | 未开始 |
|--------|--------|----------|--------|
| Block 系统 | 90% | 10% | 0% |
| 后台 Dashboard | 85% | 10% | 5% |
| 数据层 | 60% | 15% | 25% |
| 构建与发布 | 30% | 0% | 70% |
| 主题系统 | 50% | 0% | 50% |
| 多语言/AI 翻译 | 0% | 0% | 100% |
| 托管/基础设施 | 10% | 0% | 90% |

> **总体进度**：核心编辑闭环（block 系统 + 后台 dashboard + 基本构建）已基本完成，可以跑通"选主题→填内容→预览→构建静态 HTML"的完整流程。剩余工作主要集中在：术语重命名、i18n seed 重组、发布管线（CDN/字体/SEO）、多语言+AI 翻译。
