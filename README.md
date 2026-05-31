# mycompany.website

多租户静态网站生成系统。Flask + SQLAlchemy + Jinja2，把店主在表单里填的内容渲染成纯静态 HTML，发布到 CDN。

## 使用步骤

### 一、用户登录

| 步骤                         | 说明                              |
| ---------------------------- | --------------------------------- |
| 邮箱魔法链接登录             | 无密码；token 一次性、15 分钟过期 |
| 平台按浏览器语言显示后台界面 | 自动判读 Accept-Language          |
| 可手动切换界面语言           | 显示语言不满意时切换              |

### 二、创建网站

| 环节              | 操作                              | 说明                    |
| ----------------- | --------------------------------- | ----------------------- |
| 选模板 + 通用设置 | 选择主题（模板）                  | 按行业 / 风格筛选       |
|                   | 选第一网站语言（源语言）          | 用它填真实内容          |
|                   | 设置配色 / LOGO / Favicon 等      | 站点级设置              |
|                   | 设置菜单结构并创建对应页面        | 菜单项 → 页面           |
|                   | 给页面选 block 并编排             | 在 block 允许范围内调整 |
|                   | 选页脚排版                        | 页脚变体                |
| 设计页面          | 设计独立页（Index、联系我们等）   | `pages/`                |
|                   | 设计产品列表页                    | 数据集列表              |
|                   | 设计产品详情页                    | 数据集详情              |
| 添加内容          | 按产品 / 博客页面格式填字段与资源 | 图片、图纸、视频等      |
| 优化 SEO          | 只编辑必要的 SEO 信息             | 标题 / 描述等           |


### 三、多语言与发布

| 步骤 | 操作               | 说明                              |
| ---- | ------------------ | --------------------------------- |
| 1    | AI 翻译            | 把源语言所有页面文本译成第二语言  |
| 2    | 优化 SEO           | 校对 / 优化译文页面的 SEO         |
| 3    | 管理员审核         | 等待平台审核通过                  |
| 4    | 子域名发布         | 发布到 `<slug>.mycompany.website` |
| 5    | （可选）自定义域名 | 有自己的域名则切换过去            |


## 技术栈

- 后端：Flask + SQLAlchemy
- 数据库：SQLite（开发）/ PostgreSQL（部署）
- 模板引擎：Jinja2
- 静态资源：字体子集化（fonttools）、图片处理（Pillow）
- 登录：邮箱魔法链接

## 仓库结构

```text
app/                  Flask 应用
  core/               模型、路由、生成器、模板加载
  templates/          Flask 后台模板（不是站点模板）
  static/
themes/               站点模板（git 管理，每套一个目录）
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

# 2. 扫描模板（同步 themes/ 到数据库）
.venv/bin/flask --app run scan-templates

# 3. 创建测试用户和站点
.venv/bin/flask --app run create-user demo@example.com
.venv/bin/flask --app run create-site demo@example.com testsite

# 4. 启动开发服务器
.venv/bin/python run.py
# 浏览器打开 http://127.0.0.1:5000/

# 其他
.venv/bin/flask --app run list-sites
ls sites/1/
```

## 文档

| 文档                                             | 说明                                  |
| ------------------------------------------------ | ------------------------------------- |
| [docs/README.md](docs/README.md)                 | 文档索引（从这里开始）                |
| [docs/architecture.md](docs/architecture.md)     | 整体架构、技术决策                    |
| [docs/data-model.md](docs/data-model.md)         | 数据库表 + 磁盘 YAML 结构             |
| [docs/infrastructure.md](docs/infrastructure.md) | CDN、SSL 自动化                       |
| [docs/domains.md](docs/domains.md)               | 子域、URL 路径、预览、自定义域名      |
| [docs/themes/README.md](docs/themes/README.md)   | 主题开发（目录结构、布局、block）     |
| [docs/content.md](docs/content.md)               | 店主后台（内容管理界面）              |
| [docs/publish.md](docs/publish.md)               | 发布、输出结构、字体优化              |
| [docs/seo.md](docs/seo.md)                       | SEO + AI 检索（sitemap、llms.txt 等） |
| [docs/i18n.md](docs/i18n.md)                     | 多语言 + AI 翻译                      |

给 Claude 的工作指引：[CLAUDE.md](CLAUDE.md)
