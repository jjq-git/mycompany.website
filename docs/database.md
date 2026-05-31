# 数据库（平台级元数据）

数据库只存**平台级元数据**——账号、站点登记、主题登记、登录 token，仅此 4 张表（SQLAlchemy）。
网站内容（设置 / 页面 / 数据集 / 翻译 / 资源）不进数据库，全部存磁盘 YAML，结构见 [data-model.md](data-model.md)。

## 一、四张表

| 表 | 作用 | 关键字段 |
| --- | --- | --- |
| `User` | 账号 | `id`、`email`(唯一)、`role`(user/admin)、`status`、`created_at`、`last_login_at` |
| `LoginToken` | 邮箱魔法链接 | `id`、`user_id`、`token_hash`(SHA-256，唯一)、`expires_at`(15 分钟)、`used_at` |
| `Site` | 站点登记 | `id`、`name`(唯一，= slug/子域名/目录名)、`owner_id`、`theme_name`、`created_at` |
| `Theme` | 主题登记 | `id`、`name`(唯一)、`theme_name`、`industry`、`languages`、`version`、`uploaded_at` |

要点：

- 无密码列（只用魔法链接）。`token_hash` 存哈希，明文 token 不入库。
- `Site.name` = 用户创建时选的名字，遵循子域名规则，全局唯一，既是目录名 `sites/<name>/` 也是将来的子域名。数据库 `id` 仅作内部主键。
- `Site` 不含价格 / 会员 / 到期 / 发布历史 / 存储桶等字段。站点的显示名、slogan 等是**内容**，存 `settings.yaml`，不在这张表。
- `Theme` 在管理员上传主题 ZIP 时，由包内 `meta.yaml` 解析写入；完整字段说明见 [themes/meta.yaml.md](themes/meta.yaml.md)。

## 二、后期表（暂未实现）

自定义域名 / SSL 自动化上线后会增加云资源自动化相关的表（`domains`、`provisioning_jobs` 等），属基础设施层，定义与用途见 [infrastructure.md](infrastructure.md)。MVP 阶段不建。

## 三、代码现状（与本文的差异）

本文是**目标定义**。代码 [app/core/models.py](../app/core/models.py) 当前与之尚未对齐，已知差异（改名计划见 [TODO-code.md](TODO-code.md)）：

- 主题表的模型类仍叫 `Template`（表名 `templates`），未改为 `Theme`；`Site` 用 `template_name` / `template_version`，未改为 `theme_*`。
- 表由 `db.create_all()` 启动时建（[app/__init__.py](../app/__init__.py)），**无迁移文件**；字段定稿后再决定迁移方式。
