# 开发指南

本文件面向开发者和 AI，介绍项目的整体规划、架构设计、技术栈和开发约定。

> 产品定位、核心价值观、不做的事等，详见 [../../CLAUDE.md](../../CLAUDE.md)。

> 本指南已按主题拆分为多个分册，本文件是总入口（含技术栈、整体架构、代码约定）。

---

## 分册索引

| 分册 | 内容 |
|---|---|
| 本文 · [一、技术栈](#一技术栈) | 选型理由（Flask / Bootstrap / 字体子集化 / CDN） |
| 本文 · [二、整体架构](#二整体架构) | 角色、数据流、两层数据模型、核心实体 |
| [模板系统.md](模板系统.md) | 模板定义、文件结构、三种块类型、参数化能力 |
| [模块系统.md](模块系统.md) | 模块库、变体、配置面板、Header/Footer、共享范围 |
| [店主后台.md](店主后台.md) | 布局、菜单驱动页面、预览面板、CMS 对比 |
| [发布流程.md](发布流程.md) | 构建步骤、输出结构、字体子集化、图片处理 |
| [域名与基础设施.md](域名与基础设施.md) | 域名规划、URL 结构、CDN 部署、SSL 证书 |
| [数据库设计.md](数据库设计.md) | 表全景、详细字段、关系图、MVP 子集、索引 |
| [SEO.md](SEO.md) | SEO 实施清单、性能指标、AI 爬虫策略 |
| [多语言与AI翻译.md](多语言与AI翻译.md) | 多语言架构、三层翻译策略、Hash 缓存、构建注入 |
| [AI助手.md](AI助手.md) | DeepSeek 助手：System Prompt、入口位置、对话场景、数据安全 |
| 本文 · [本地开发](#四本地开发) 等 | 目录结构、本地开发、基本原则 |

---
## 一、技术栈

| 层面 | 选型 | 理由 |
| --- | --- | --- |
| 后端 | Flask + Jinja2 | 轻量、Python 生态成熟、Jinja2 直接复用做静态生成 |
| 数据库 | SQLite（MVP）→ PostgreSQL（规模化后） | MVP 阶段单机够用 |
| 店主后台界面 | Bootstrap 5.3 CDN | 不引入 Vue / React，降低新人上手门槛 |
| 站点模板（访客端） | HTML + Jinja2 + 自定义 CSS，`site_templates/` 文件夹，git 管理 | 开发者 + AI 编写，每个模板自带 `main.css`，自行控制视觉风格。最终渲染为纯静态 HTML/CSS/JS 发布到 CDN |
| 静态生成 | Python（Jinja2 渲染） | 与后端同一套模板引擎，无翻译成本 |
| 字体子集化 | fonttools / pyftsubset + brotli（WOFF2 压缩） | 中文字体从 5-10MB 压到 10-30KB |
| 图片处理 | Pillow（多尺寸 + WebP） | 上传时立即处理 |
| CDN / 域名 / SSL | 阿里云 OSS + CDN + 云解析 + Let's Encrypt | 国内最快，SSL 无配额限制 |
| 登录 | 邮箱魔法链接（不要密码） | 低频用户友好 |

**访客端站点模板不使用 Bootstrap**，每个模板自带自定义 CSS（`site_templates/<name>/static/css/main.css`），由模板开发者自由控制视觉风格，不依赖任何前端框架。

## 二、整体架构

### 参与角色

| 角色 | 是谁 | 做什么 |
| --- | --- | --- |
| 开发者 / 设计师 | 平台方（你 + AI + 设计师） | 用代码 + AI 制作模板，提交到 git |
| 店主 | 小企业老板 | 选模板、填表、发布、看数据 |
| 访客 | 店主网站的浏览者 | 浏览静态 HTML（看不到平台的存在） |

关键洞察：**店主一辈子不接触代码，模板始终是代码（git 管理）。**

### 数据流

```text
[开发者 + AI]   设计模板 → 写 HTML / Jinja2 / CSS → git push
                               ↓
                         模板加入模板库
                               ↓
[店主]    选模板 → 表单填数据 → 上传图片 → 点击「发布」
                               ↓
[系统]    数据 + 模板 → 渲染 → 字体子集化 → 静态文件
                               ↓
                           上传到 CDN
                               ↓
[访客]    浏览器访问 → CDN 直接返回 HTML（< 1 秒）
```

### 模块概览

```text
                 模板库（site_templates/，git 管理的文件夹）
                         │
                         ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  店主后台          │─▶│ Flask 后端 API    │─▶│ 静态生成器         │
│ (表单 + 数据管理)  │  │ (路由 / 业务逻辑)  │  │ (渲染 + 优化)      │
└──────────────────┘  └────────┬─────────┘  └────────┬─────────┘
                               │                      │
                               ▼                      ▼
                         数据库（用户数据）          CDN（静态文件）
                                                     │
                                                     ▼
                                                 访客的浏览器
```

注意：**没有「设计师后台」模块**。模板由开发者写代码做，工具就是 IDE + git + AI。

### 数据分两层（重要架构决策）

```text
              ┌───────────────────────────┐
              │  数据库（平台级）           │
              │  - User（账号）             │
              │  - Site（站点元信息）       │
              │  - PublishVersion（发布历史）│
              │  - Billing（计费）          │
              └───────────────────────────┘
                          │
                          │  Site.folder_path → 指向
                          ▼
              ┌───────────────────────────┐
              │  文件系统（站点级）         │
              │  sites/<site_id>/          │
              │  - settings.yaml           │
              │  - pages/*.yaml            │
              │  - data/*.yaml             │
              │  - translations/*.yaml     │
              │  - assets/                 │
              └───────────────────────────┘
```

**店主网站的核心数据存为文件，不存数据库。**

为什么：

- "导出 ZIP" = 复制一个文件夹，不需要序列化逻辑
- 平台关停时把文件夹给店主，整站还能跑
- schema 弹性：模板换字段不用 ALTER TABLE
- AI 友好：可直接读 YAML 调试、修复
- 跟"模板是文件夹"心智模型统一

### 核心数据模型

| 实体 | 存在哪里 | 说明 |
| --- | --- | --- |
| Template | `site_templates/<name>/` 文件夹 | 模板（代码 + 资源），git 管理 |
| User | 数据库 | 店主账号（邮箱魔法链接登录） |
| Site | 数据库 | 站点元信息（id、owner、template、folder_path、custom_domain） |
| PublishVersion | 数据库 | 一次发布的快照（version、cdn_url、timestamp） |
| Billing | 数据库 | 计费记录 |
| SiteSettings | `sites/<id>/settings.yaml` | 站点配置（菜单项、主题变量、开关、启用的语言） |
| Page 字段值 | `sites/<id>/pages/*.yaml` | 每个页面的内容 |
| Dataset | `sites/<id>/data/<name>.yaml` | 数据集（产品 / 案例 / 博客） |
| DataItem | 同上文件中的一项 | 数据条目（一个产品 / 一篇案例） |
| Translations | `sites/<id>/translations/<lang>.yaml` | 多语言翻译缓存 |
| Glossary | `sites/<id>/glossary.yaml` | 翻译词汇表 |
| Asset | `sites/<id>/assets/` 文件 | 上传的图片 / 文件 |

## 三、目录结构

完整目录树见 **[目录结构.md](../目录结构.md)**，含 git 追踪状态和设计决策说明。

## 四、本地开发

### 环境要求

- Python 3.10+
- Git
- （可选）阿里云 OSS + CDN 账号（发布功能需要）

### 初始化

```bash
# 1. 克隆仓库
git clone <repo-url> mycompany.website
cd mycompany.website

# 2. 创建虚拟环境
python -m venv .venv

# 3. 激活虚拟环境
#    Windows:
.venv\Scripts\activate
#    macOS / Linux:
source .venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 复制环境变量（按需修改）
cp .env.example .env

# 6. 初始化数据库
python -m flask --app run init-db

# 7. 扫描模板（同步 site_templates/ 到数据库）
python -m flask --app run scan-templates
```

### 创建测试数据

```bash
# 创建用户（开发期跳过邮件验证）
python -m flask --app run create-user demo@example.com

# 创建站点（--template 指定模板名）
python -m flask --app run create-site demo@example.com testsite --template dengtec

# 提升为管理员（可选）
python -m flask --app run promote-admin demo@example.com
```

### 启动开发服务器

```bash
python run.py
# 浏览器打开 http://127.0.0.1:5000/
```

### 其他常用命令

| 命令 | 用途 |
|---|---|
| `python -m flask --app run list-users` | 列出所有用户 |
| `python -m flask --app run list-sites` | 列出所有站点 |
| `python -m flask --app run build-site <site_id>` | 生成静态站点到 `output/<site_id>/` |

## 五、基本原则总结

产品决策犹豫时问自己一句：**"如果我自己用这个产品，这样做合理吗？"**

保持「自己也会用」的视角 —— 这是它最大的护城河。
