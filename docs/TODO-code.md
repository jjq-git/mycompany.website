# 待改代码清单

> 文档先行，代码暂不动。文档里已经确定的设计 / 术语变更，凡是需要改代码的，先记在这里，之后一起改。

## 术语：模板 → 主题（Template → Theme）

文档已统一用「主题（Theme）」指代生成用户网站的那套皮肤，`template` 一词只留给后台 Flask 模板（`app/templates/`）。代码里仍是 `Template`，待一起改：

- [ ] `Template` 模型类 → `Theme`（`app/core/models.py`，`__tablename__ = 'templates'` → `themes`，涉及数据库迁移）
- [ ] 配置键 `TEMPLATES_DIR` → `THEMES_DIR`（`app/core/config.py`）
- [ ] CLI 命令 `scan-templates` → `scan-themes`（`app/commands.py`）
- [ ] `scan_templates()` 函数 / `template_loader.py` 文件名 → theme 命名（`app/core/template_loader.py`）
- [ ] `Site.template_name` / `Site.template_version` 字段 → `theme_name` / `theme_version`（涉及数据库迁移）
- [ ] 其余引用 `template` 的变量名、路由参数：`app/core/builder.py`、`app/core/routes.py`、`app/core/admin_routes.py`、`app/__init__.py`、`app/core/site_storage.py`
- [ ] 目录名 `site_templates/` → `themes/`

## 主题内容按语言分目录：i18n/<lang>/

文档已把主题的初始内容（含 `settings.yaml` 与 pages/data）从 `seed_data/` 改成每语言一份的 `site_templates/<name>/i18n/<lang>/`（如 `i18n/zh/`、`i18n/en/`，各自含自己的 `settings.yaml`）。不再有主题根目录的 `settings.yaml`，也不再有 `seed_data/` 目录。代码待跟进：

- [ ] `copy_seed_data()` 现在是 `shutil.copytree` 整个 `seed_data/`（`app/core/site_storage.py`）。改成：按用户选的语言，把 `site_templates/<name>/i18n/<lang>/` 整套（settings.yaml + pages/ + data/）拷进 `sites/<id>/`
- [ ] 现有主题 `site_templates/dengtec/` 的实际文件要把 `seed_data/` 重组成 `i18n/<lang>/`（每语言一份，含各自的 settings.yaml）

## 主题表字段补全（与 database.md 的 ER 图对齐）

`app/core/models.py` 的 `Template` 模型待补：

- [ ] 加 `languages`（数组，JSON 列）—— 主题提供整套 seed 的语言
- [ ] 加 `level`（int，会员门槛）、`tags`（数组，JSON 列）、`author`（string）
- [ ] `industry` 由单值 `String(50)` 改为数组（JSON 列）
- [ ] `description` 改多语言（zh / en，JSON 列）
- [ ] `cover_image` 列与「约定路径 `preview/cover.webp`」二选一（文档倾向约定路径，可去列）
- [ ] `current_version` 命名与 database.md 的 `version` 对齐

## Site / User 表字段补全

- [ ] `Site`：`domain`（用户自定义域名）、`expires_at`（服务到期时间）
- [ ] `Site`：审核字段 `review_status`（pending/approved/rejected）、`reviewed_at`、`reviewed_by`（FK→users）、`review_note`
- [ ] `User`：`phone`（手机号）、`phone_verified_at`（手机验证时间）、`level`（会员等级）

## 后台界面多语言（Flask-Babel）

- [ ] 安装 Flask-Babel，配置语言检测（按 `User.preferred_lang` + 浏览器 `Accept-Language`）
- [ ] 后台界面文案（导航、按钮、提示）标记为可翻译字符串
- [ ] 提供中 / 英两套翻译文件

## settings.yaml schema 拍扁

文档已将 `settings.company.*` 拍扁为顶层字段：

- [ ] `settings.company.name` → `settings.title`
- [ ] `settings.company.tagline` → `settings.slogan`
- [ ] `settings.company.default_og_image` → 改为回退 `settings.logo`（不新增独立 og_image 字段）
- [ ] 涉及文件：所有主题的 `seed_data/settings.yaml`、`app/core/builder.py` 的 settings 读取逻辑、所有布局模板中的 `settings.company.*` 引用

## 文档结构整理

- [ ] 清理 `docs/docs/` 子目录（中文名文件），内容合并到对应子系统文档后删除
- [ ] 删除被替换的旧文件：`index.md`（已改为 `README.md`）、`templates.md`（内容并入 `themes/`）、`content.md`（内容并入 `dashboard/content.md`）、`database.md`（内容并入 `dashboard/database.md`）、`domains.md`（内容并入 `cloud/domains.md`）、`infrastructure.md`（内容并入 `cloud/`）、`publish.md`（内容并入 `site/publish.md`）、`seo.md`（内容并入 `site/seo.md`）、`i18n.md`（内容并入 `site/i18n.md`）

## 其他

- [ ] `translations.yaml` 机制：主题 UI 文案（`t.*`）的多语言翻译文件——builder 已支持渲染上下文注入 `t`，需确认所有主题布局模板中的硬编码文字已改用 `t.*`
- [ ] `meta.yaml` 的 `languages` 字段：声明主题提供哪些语言的整套 seed，需与 `i18n/<lang>/` 目录结构改造一起做
