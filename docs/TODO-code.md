# 待改代码清单

> 文档先行，代码暂不动。文档里已经确定的设计 / 术语变更，凡是需要改代码的，先记在这里，之后一起改。

## 术语：模板 → 主题（Template → Theme）

文档已统一用「主题（theme）」指代生成用户网站的那套皮肤，`template` 一词只留给后台 Flask 模板（`app/templates/`）。详见 [themes/README.md](themes/README.md)。代码里仍是 `Template`，待一起改：

- [ ] `Template` 模型类 → `Theme`（[app/core/models.py](../app/core/models.py)，`__tablename__ = 'templates'` → `themes`，涉及数据库迁移）
- [ ] 配置键 `TEMPLATES_DIR` → `THEMES_DIR`（[app/core/config.py](../app/core/config.py)）
- [ ] CLI 命令 `scan-templates` → `scan-themes`（[app/commands.py](../app/commands.py)）
- [ ] `scan_templates()` 函数 / `template_loader.py` 文件名 → theme 命名（[app/core/template_loader.py](../app/core/template_loader.py)）
- [ ] `Site.template_name` / `Site.template_version` 字段 → `theme_*`（涉及数据库迁移）
- [ ] 其余引用 `template`（变量名、路由）的点：[app/core/builder.py](../app/core/builder.py)、[app/core/routes.py](../app/core/routes.py)、[app/core/admin_routes.py](../app/core/admin_routes.py)、[app/__init__.py](../app/__init__.py)、[app/core/site_storage.py](../app/core/site_storage.py)

> 注：目录名 `site_templates/` → `themes/` 已改完（含 config 路径常量与注释），这里只剩代码符号层面的重命名。

## 主题内容按语言分目录：i18n/<lang>/

文档已把主题的初始内容（含 `settings.yaml` 与 pages/data）从 `seed_data/` 改成每语言一份的 `themes/<name>/i18n/<lang>/`（如 `i18n/zh/`、`i18n/en/`，各自含自己的 `settings.yaml`）。不再有主题根目录的 `settings.yaml`，也不再有 `seed_data/` 目录。代码待跟进：

- [ ] `copy_seed_data()` 现在是 `shutil.copytree` 整个 `seed_data/`（[app/core/site_storage.py](../app/core/site_storage.py)）。改成：按用户选的语言，把 `themes/<name>/i18n/<lang>/` 整套（settings.yaml + pages/data）拷进 `sites/<id>/`
- [ ] 现有主题 `themes/tech-product/` 的实际文件要把 `seed_data/` 重组成 `i18n/<lang>/`（每语言一份，含各自的 settings.yaml；文件搬移，不在"只改文档"范围，留待一起做）

## 主题表字段补全（与 database.md 的 ER 图对齐）

[database.md](database.md) 的 ER 图把主题表定为目标 schema，代码 `Template` 待补：

- [ ] 加 `languages`（数组）—— 主题提供整套 seed 的语言（[meta.yaml.md](themes/meta.yaml.md) §五）
- [ ] 加 `level`（int，会员门槛）、`tags`（数组，受控词表）、`author`
- [ ] `industry` 由单值 `String(50)` 改为数组（JSON 列）
- [ ] `description` 改多语言（zh / en，JSON）；数组 / 多语言字段统一用 JSON 列
- [ ] `cover_image` 列与「约定路径 `preview/cover.webp`」二选一（meta.yaml.md 倾向约定路径，可去列）
- [ ] `current_version` 命名与 database.md 的 `version` 对齐

## 其他

（暂无）
