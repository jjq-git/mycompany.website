# 架构

## 是什么

用户登录后选择喜欢的主题，适当修改布局和设置，替换图片与文字，变成自己需要的网站，然后导出 HTML。

## 当前范围

### 平台提供

- 若干套设计好的主题供选择
- 存储每个用户设计的网站（YAML 文件）
- 构建并导出静态站（ZIP）

### 用户能做（典型流程）

1. 选一套主题。
2. 完善站点基本信息：favicon、主色、logo、菜单、支持的语言、站点名 + slogan。
3. 选 / 自定义各类页面的布局：
   - 1–2 套页眉 / 页脚（产品页与文章页可分开用）
   - 产品详情页、博客详情页布局
   - 产品列表页、博客列表页布局
4. 设计独立页面（如 index、关于我们）。
5. 添加产品、博客文章 —— 布局固定，只填内容。

## 端到端数据流

```mermaid
flowchart TD
    U([用户]) -->|邮箱魔法链接登录| B["后台（Flask）<br/>三栏：导航 ｜ 预览 iframe ｜ 属性面板"]
    B -->|填表编辑| Y[("sites/&lt;name&gt;/*.yaml<br/>网站内容的唯一真相源 · 不进数据库")]
    Y -->|build| O["sites/&lt;name&gt;/output/<br/>纯静态 HTML / CSS / JS · 多语言分子目录"]
    O -->|导出| Z(["下载 ZIP"])
```

## 组件

| 组件 | 职责 |
| --- | --- |
| Flask 应用（`app/`） | 后台 HTTP 入口：登录、内容编辑、触发构建 / 导出 |
| 数据库（SQLAlchemy） | 只存平台级元数据：账号、站点登记、主题登记、登录 token |
| 磁盘 `sites/<name>/` | 一个网站的全部：源内容（YAML）+ 资源 + 构建产物 `output/`；name = 子域名 slug |
| builder | 把 `sites/<name>/` 源文件 + 主题 渲染成 `sites/<name>/output/` 静态站 |
| 主题 `site_templates/` | 访客端外观（HTML + Jinja2 + CSS），git 管理 + 管理员上传 ZIP 安装 |
| 导出 | 把 `sites/<name>/output/` 打包成 ZIP 给用户下载（当前唯一发布方式） |

## 数据存哪里（核心原则）

数据分两层：

- **数据库 = 平台级元数据**：账号、站点登记、主题登记、登录 token。**不存网站内容。**
- **磁盘 `sites/<name>/` = 网站内容**：设置、页面、数据集、翻译、资源，全是 YAML + 文件，是内容的唯一真相源；构建产物放同目录的 `output/`。

`name` = 创建时选定的子域名 slug。导出的静态站 = `sites/<name>/output/`，可直接打包带走。字段细节见 [database.md](dashboard/database.md)（DB 表）与 [sites.md](site/sites.md)（站点磁盘内容）。

## 目录结构

```text
app/
  __init__.py        应用工厂（注册扩展、蓝图、CLI）
  core/              模型、路由、builder、主题加载、菜单、block、翻译
  templates/         后台页面（Flask template，≠ 主题）
  static/            后台 CSS / JS
site_templates/<name>/  一套主题（meta.yaml + layouts/ + blocks/ + seed_data/ + static/）
sites/<name>/        一个网站的全部（name = 子域名 slug，gitignored）
  *.yaml / pages/ …  源内容（设置 / 页面 / 数据集 / 翻译 / 资源）
  output/            该站生成的静态站（build 产物，导出即打包它）
instance/            SQLite 数据库（gitignored）
```

> **术语注**：文档目标是将目录 `site_templates/` 重命名为 `themes/`、内部 `seed_data/` 重组为 `i18n/<lang>/`，代码尚未跟进。详见 [TODO-code.md](TODO-code.md)。

## 关键约束

- 产出永远是静态文件；后台只在编辑 / 构建时运行。
- 主题由开发者写代码（git 管理），也支持管理员上传 ZIP 安装。
- 登录用邮箱魔法链接。
- 网站名（name）= 创建时选定，遵循子域名规则（小写字母数字 + 连字符，3–30 字符，全局唯一，排除保留字），作为站点目录名；创建后 1 个月内不可改，之后改名 = 迁移目录。

## 关键技术决策

### 为什么用 Flask

轻量、Python 生态成熟、Jinja2 直接复用做静态生成。MVP 阶段不需要重武器。

### 为什么静态生成而不是 SSR

定位上就是「发布完不动」的网站。SSR 意味着永远在运行，违背产品理念。

### 为什么 SQLite 起步

MVP 阶段单机就够。每个用户的数据量很小（几十个产品 + 几十张图）。当用户上千、并发上来再换 PostgreSQL。

### 为什么站点数据存文件而不是数据库

- **导出 = 复制文件夹**，无需序列化逻辑
- **schema 弹性**：主题字段变化不需要 ALTER TABLE
- **多语言天然嵌套**：YAML 自然支持
- **AI 友好**：直接读、改、调试
- **平台死了，用户拿到文件夹仍能跑**

代价（在小企业站规模下基本不存在）：

- 跨用户运营报表 → 关键统计回写到 SQL 冗余字段
- 单站搜索产品 → 几百条 YAML 全文扫描足够快
- 并发写入 → 单用户单写者 + 文件锁

### 为什么模板是文件不是数据库

主题少（3-5 套）、变更频率低、需要 review 和版本控制。git 是已经为这种场景设计的最佳工具。

### 为什么不用可视化模板编辑器

3-5 套模板不值得为它建一整套可视化系统（Grapes.js 等）。2026 年 AI 写 HTML / CSS 已经很好用：设计师给 Figma 截图，AI 出 HTML 骨架，开发者微调。主题做完就稳定了，不需要持续可视化编辑。

### 为什么不分前后端

用户端只是表单，复杂度低，Flask + 少量 vanilla JS 足够。避免引入 Vue / React 增加新人上手门槛。

## 子系统文档

- [site/](site/README.md) — 站点：源内容 → 产物 → 发布 → SEO → 多语言
- [dashboard/](dashboard/README.md) — 后台 UI + 数据层（内容管理、后台多语言、数据库）
- [cloud/](cloud/README.md) — 托管设施（子域、自定义域名、CDN / SSL）
- [themes/](themes/README.md) — 主题开发（布局 / block / meta / settings）
