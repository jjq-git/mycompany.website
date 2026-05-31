# 数据库（平台级元数据）

数据库只存**平台级元数据**——账号、站点登记、主题登记、登录 token，仅此 4 张表（SQLAlchemy）。
网站内容（设置 / 页面 / 数据集 / 翻译 / 资源）不进数据库，全部存磁盘 YAML，结构见 [sites.md](../site/sites.md)。

## 一、四张表（ER 图）

```mermaid
erDiagram
    USERS ||--o{ SITES : "拥有"
    USERS ||--o{ SITES : "审核"
    USERS ||--o{ LOGIN_TOKENS : "请求"
    THEMES ||--o{ SITES : "被使用"

    USERS {
        int id PK
        string email UK "唯一"
        datetime email_verified_at "邮箱验证时间"
        string phone "手机号"
        datetime phone_verified_at "手机验证时间"
        string status "active / suspended / deleted"
        string role "owner / admin"
        int level "会员等级，越高越高级；≥ 主题 level 才能选用该主题"
        string display_name "昵称"
        string preferred_lang "后台界面语言，默认 zh"
        datetime last_login_at
        datetime created_at
        datetime updated_at
    }

    LOGIN_TOKENS {
        int id PK
        int user_id FK "可空，新用户登录前未绑定"
        string email "请求链接的邮箱"
        string token_hash UK "SHA-256，明文不入库"
        datetime expires_at "默认 15 分钟"
        datetime used_at "一次性，用后置位"
        string ip_address "IPv6 最长 45"
        datetime created_at
    }

    SITES {
        int id PK
        int owner_id FK
        string name "站点显示名"
        string slug UK "子域名 / 目录名，3-30 位小写字母数字连字符"
        string domain "用户自定义域名，自己申请并绑定；空则用 slug 子域名"
        string folder_path "站点目录路径"
        string theme_name FK "外键指向 themes.name"
        string theme_version "建站时主题版本，build 比对"
        string default_language "源语言，默认 zh"
        json enabled_languages "已启用语言数组"
        string storage_mode "shared / dedicated"
        string bucket_name
        string bucket_path_prefix
        string bucket_region
        string cdn_provider "默认 aliyun"
        string status "draft / published / suspended"
        string review_status "审核状态：pending / approved / rejected"
        datetime reviewed_at "审核时间"
        int reviewed_by FK "审核管理员 → users.id"
        string review_note "审核备注 / 驳回原因"
        datetime expires_at "服务到期时间"
        datetime last_published_at
        datetime soft_deleted_at "软删除"
        datetime created_at
        datetime updated_at
    }

    THEMES {
        int id PK
        string name UK "slug，目录名，如 tech-product"
        string theme_name "展示名（英文）"
        json description "多语言，zh / en"
        json industry "行业数组"
        json tags "风格标签数组，受控词表"
        json languages "提供整套 seed 的语言数组"
        int level "会员门槛，默认 1"
        string version "语义版本，来自 meta"
        string author
        boolean is_public "默认 true"
        date created "主题制作日期，手写于 meta"
        date updated "主题更新日期，手写于 meta"
        datetime created_at "DB 扫描登记时间"
        datetime updated_at "DB 登记更新时间"
    }
```

要点：

- **登录**：无密码列（只用魔法链接）。
  - `token_hash` 存哈希，明文不入库；
  - `LoginToken.user_id` 可空——新用户先用 `email` 发链接，登录后再绑定 `User`。
- **Site 标识**：
  - `slug`：全局唯一的子域名 / 目录名（建站后 1 个月内不可改）；
  - `name`：可改的显示名；`id` 仅内部主键；
  - `theme_name`：外键指向 `themes.name`（主题 slug）。
- **审核 / 域名 / 到期**（均为 `Site` 字段）：
  - `review_status`：平台对站点内容的审核——pending / approved / rejected；
  - `reviewed_by`：指向管理员（`users.role = admin`）；`review_note` 记驳回原因；
  - `domain`：用户自己申请并绑定的自定义域名（证书 / 绑定自动化走后期 `domains` 表，见 §二）；
  - `expires_at`：服务到期时间。
- **账号联系方式**：
  - `User.email`：登录主键（魔法链接）；
  - `User.phone`：手机号（联系 / 后续实名或通知用）。
- **用户权限**：
  - `User.role`：平台角色（owner / admin）；
  - `User.level`：会员等级，与主题 `level` 比较决定可选用哪些主题（[meta.yaml.md](../themes/meta.yaml.md) §四）；
  - 能开几种语言等配额由 `level` 决定，**分级待定**（[i18n.md](../i18n.md) §〇）；
  - 计费 / 到期不在 `User`，按站点走 `Site.expires_at`。
- **主题多值字段**：
  - `industry` / `tags` / `languages`：数组（JSON 列）；
  - `description`：多语言（zh / en，JSON 列）。
- **两种时间**（主题）：
  - `created` / `updated`：手写在 `meta.yaml` 的制作 / 更新日期；
  - `created_at` / `updated_at`：DB 扫描登记时间。
- **写入时机**：主题在管理员上传 ZIP 时由 `meta.yaml` 解析写入；字段逐项说明见 [themes/meta.yaml.md](../themes/meta.yaml.md)。

## 二、后期表（暂未实现）

自定义域名 / SSL 自动化上线后会增加云资源自动化相关的表（`domains`、`provisioning_jobs` 等），属基础设施层，后期再设计。MVP 阶段不建。

## 三、代码现状（与本文目标的差异）

本文（含上面的 ER 图）是**目标 schema**。代码 [app/core/models.py](../../app/core/models.py) 尚未对齐，差异已记入 [TODO-code.md](../TODO-code.md)：

- 主题表模型仍叫 `Template`（表名 `templates`），待改 `Theme` / `themes`；`Site.template_name` / `template_version` 待改 `theme_*`。
- 主题表缺 `languages` / `level` / `tags` / `author` 字段；`industry` 现为单值字符串（目标为数组）；`description` 等多语言 / 多值字段的 JSON 存法待定。
- 表由 `db.create_all()` 启动时建（[app/__init__.py](../../app/__init__.py)），**无迁移文件**；字段定稿后再决定迁移方式。
