# mycompany.website

多租户静态网站生成系统。Flask + SQLAlchemy + Jinja2，把店主在表单里填的内容渲染成纯静态 HTML，发布到 CDN。

## 技术栈

- 后端：Flask + SQLAlchemy
- 数据库：SQLite（开发）/ PostgreSQL（部署）
- 模板引擎：Jinja2
- 静态资源：图片处理（Pillow，已装）；字体子集化（fonttools）待实现
- 部署：阿里云 OSS + CDN
- 登录：邮箱魔法链接

## 仓库结构

```text
app/                  Flask 应用
  core/               模型、路由、生成器、模板加载
  templates/          Flask 后台模板（不是站点模板）
  static/
site_templates/       站点模板（git 管理，每套一个目录）
sites/                店主数据（每站一个目录，gitignored）
output/               生成的静态文件（gitignored）
docs/                 设计文档
instance/             SQLite 数据库（gitignored）
```

## 本地开发

```bash
# 1. 装依赖
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. 扫描模板（同步 site_templates/ 到数据库）
.venv/bin/flask --app run scan-templates

# 3. 创建测试用户和站点
.venv/bin/flask --app run create-user demo@example.com
.venv/bin/flask --app run create-site demo@example.com testsite

# 4. 启动开发服务器
.venv/bin/python run.py
# 浏览器打开 http://127.0.0.1:5000/
# 要让局域网内其他设备也能访问，加 FLASK_HOST（不加只绑回环）：
# FLASK_HOST=0.0.0.0 FLASK_DEBUG=1 .venv/bin/python run.py

# 其他
.venv/bin/flask --app run list-sites
ls sites/1/
```

## 文档

| 文档 | 说明 |
| --- | --- |
| [docs/architecture.md](docs/architecture.md) | 整体架构、技术决策 |
| [docs/dashboard/database.md](docs/dashboard/database.md) | 数据库表设计 |
| [docs/infrastructure.md](docs/infrastructure.md) | CDN、SSL 自动化 |
| [docs/cloud/domains.md](docs/cloud/domains.md) | 子域、URL 路径、预览、自定义域名 |
| [docs/themes/](docs/themes/README.md) | 模板系统、块、数据集 |
| [docs/dashboard/content.md](docs/dashboard/content.md) | 店主后台（内容管理界面） |
| [docs/site/publish.md](docs/site/publish.md) | 发布、输出结构、字体优化 |
| [docs/site/seo.md](docs/site/seo.md) | SEO + AI 检索（sitemap、llms.txt 等） |
| [docs/themes/i18n.md](docs/themes/i18n.md) | 多语言 + AI 翻译 |
| [docs/site-creation-manual.md](docs/site-creation-manual.md) | 手动建站操作手册（CLI 步骤） |

给 Claude 的工作指引：[CLAUDE.md](CLAUDE.md)
