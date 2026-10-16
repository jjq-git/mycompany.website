# 部署与初始化（新机器 / 云服务器）

> 本文档讲**怎么把应用在一台新机器上跑起来、并建好能登录的管理员**。
> 站点产物去哪、CDN/SSL 见 [infrastructure.md](infrastructure.md)。

> [!CAUTION]
> **当前版本尚未通过生产验收，不得按本文现有步骤直接暴露到公网。**
> 2026-08-03 验收发现的 P0/P1 配置、安全、依赖、Git 数据和测试问题，必须先按
> [全项目验收报告（2026-08-03）](acceptance-20260803.md) 修复并完成正式复验。

## 零、正式部署门禁

部署操作开始前，负责人必须逐项确认：

- [ ] [验收报告](acceptance-20260803.md) 中所有 P0/P1 已修复并复验通过。
- [ ] [建站至发布专项验收](acceptance-site-lifecycle-20260803.md) 中所有 LIFE-P0/P1 已修复并复验通过。
- [x] [内容模板与内容 CRUD 专项验收](acceptance-content-workflow-20260803.md) 中本轮全部 CONTENT-P1 已修复，并通过隔离后端与真实 Chromium 复验。
- [ ] `/publish` 已完成持久化版本、OSS/CDN 上传、公网回读和原子切换；不得只改数据库状态。
- [ ] `FLASK_ENV=production`、`FLASK_DEBUG=0`。
- [ ] `PREVIEW_REQUIRE_LOGIN=1`、`EXPORT_SKIP_LINK_CHECK=0`。
- [ ] `PLATFORM_DOMAIN`、`DATABASE_URL`、可信代理层数已按生产环境配置。
- [ ] Session Cookie 带 `Secure`、`HttpOnly`、`SameSite=Lax`。
- [ ] CSRF 外部 Referer 不会产生外部重定向。
- [ ] WSGI 服务和数据库驱动已经纳入部署依赖；全新机器从零安装成功。
- [ ] `sites/` 已解除 Git 跟踪并建立独立备份/恢复流程。
- [ ] 修复后的自动化测试全部通过。
- [ ] 真实浏览器、SMTP/短信、OSS/CDN、DNS、SSL、备份恢复已复验。
- [ ] 发布后编辑能显示“有未发布变更”，发布历史和回滚已完成故障演练。

任一项未通过，都不能进入正式发布步骤。

## 一、为什么需要这份文档

代码部署 ≠ 能登录。这两件事是分开的：

- **代码**跟着 git 走（`git pull` 就有最新版本）。
- **数据库**不跟着 git 走 —— `instance/app.db` 已停止跟踪（运行时数据不进版本库）。
  所以每台机器有**自己独立的数据库**，账号、站点数据不会从别的机器同步过来。

后果：一台新部署的机器，数据库是空的，**没有任何能登录的管理员**。
必须在这台机器上手动初始化一个。这就是本文档要解决的。

> 真实踩过的坑：在 A 机改了管理员邮箱/密码，部署到 B 机后登录不了 ——
> 因为那些改动只写进了 A 机的库，B 机的库一无所知。

## 二、首次部署一台新机器

在项目根目录，按顺序执行：

```bash
# 1. 拉取代码
git pull                          # 或首次 git clone

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量：复制模板后填真实值
cp .env.example .env
#    .env 绝不进 git（含密钥），每台机器单独配。
#    至少要设 SECRET_KEY；发短信/邮件验证码还要配 SMTP / 阿里云短信那几项。

# 4. 首次启动会自动建表（SQLite）
python run.py                     # 确认能起来后 Ctrl+C 停掉，继续下一步

# 5. 扫描模板进数据库
flask --app run scan-templates

# 6. 【关键】创建一个能密码登录的平台管理员
flask --app run ensure-admin <你的邮箱> <你的密码>

# 7. 当前仅用于本机验证启动，不是获准的生产启动方式
python run.py
# 正式部署前必须先按“零、正式部署门禁”补齐并验证 WSGI 服务；
# 生产启动命令在确定 Linux/Windows 部署方案后写入本文，禁止临时沿用 Flask 开发服务器。
```

完成后，用第 6 步的邮箱 + 密码即可登录后台。

## 三、`ensure-admin` 命令说明

登录改为账号密码后，一个能登录的账号需要**三件套**：
`User` + `AccountIdentity`（身份）+ `PasswordCredential`（密码）。
老的 `create-user` 命令只建 `User`（魔法链接时代遗留），**不足以密码登录**。

`ensure-admin` 一次把三件套建全，并设为 `active` + `admin`：

```bash
flask --app run ensure-admin mw_admin@dengtec.com <密码>
```

特性：

- **幂等**：账号已存在则只重置密码（不重复建），可放心重复跑。
- 忘记密码 / 要改密码时，也用它重置：再跑一次，填新密码即可。
- admin 天然有建站资格，命令会补齐资格记录。

## 四、常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| 新机器上管理员登录不了 | 该机数据库没有带密码的管理员 | 在该机跑 `ensure-admin` |
| 改了邮箱/密码，另一台机器没变 | 数据库不跟 git 同步，各机独立 | 在目标机各自 `ensure-admin` |
| 忘记管理员密码 | —— | 重跑 `ensure-admin` 同邮箱 + 新密码 |
| 提示"邮箱身份属于 user_id=X" | 该邮箱已绑在别的账号上 | 人工核对，别用已被占用的邮箱 |

## 五、上云服务器时的注意

- **换强密码**：`ensure-admin` 支持任意密码，别用 `qq123456` 这类弱密码上生产。
  密码只存哈希（werkzeug），不明文落库。
- **`.env` 单独配**：生产的 SECRET_KEY、短信/邮件密钥都放生产机的 `.env`，绝不提交。
- **`FLASK_DEBUG` 不要开**：生产环境关闭调试模式。
- 把第二节的步骤 6（`ensure-admin`）写进你的部署脚本，避免每次手动忘记。
- **不要用 `python run.py` 承担公网生产流量**：当前命令只用于初始化和本机验证；正式方案必须使用已纳入依赖和服务管理的 WSGI 服务。
- **不要跳过验收门禁**：每次正式部署都要回到本文第零节和 [2026-08-03 验收报告](acceptance-20260803.md) 逐项复核。
