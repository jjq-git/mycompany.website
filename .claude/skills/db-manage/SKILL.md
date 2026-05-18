---
description: "数据库管理(备份/查看/修复/重置开发库)"
---

当用户说"备份数据库"、"查看数据库"、"数据库表结构"、"重置开发库"时触发.
管理 SQLite 数据库的安全操作:备份、查看表结构、检查数据、修复常见问题.

CLAUDE.md 禁止"删除或重建 SQLite 数据库文件"——本技能提供安全的替代方案.

## 确认操作类型

先询问用户要做什么,常见操作:

| 操作 | 命令 | 风险 |
|------|------|------|
| 备份数据库 | 复制 `instance/app.db` 到带时间戳的文件 | 无 |
| 查看表列表 | `flask shell` → 遍历 db.Model | 无 |
| 查看表结构和记录数 | SQL 查询 | 无 |
| 查看某用户/站点详情 | `flask --app run list-users` / `list-sites` | 无 |
| 修复:模板不同步 | `flask --app run scan-templates` | 无 |
| 修复:站点数据损坏 | 检查 `sites/<id>/*.yaml` 文件 | 无 |
| 重置开发库(清空重来) | 先备份,再重建 | **高**,需用户确认 |

## 备份数据库

数据库位置:`instance/app.db`(SQLite,在 .gitignore 中).

备份操作:
- 确认 `instance/` 目录存在
- 复制 `instance/app.db` → `instance/app.db.backup-YYYYMMDD-HHMMSS`
- 只保留最近 5 个备份,其余提示用户清理
- 备份不用 git 追踪(已在 .gitignore)

注意:
- SQLite 文件在 Flask 运行时可以直接复制(WAL 模式会自动处理)
- 不要在服务器高负载时备份(不过 MVP 阶段无并发问题)

## 查看数据库信息

方式一:CLI 命令(优先)
- 用户列表:`flask --app run list-users`
- 站点列表:`flask --app run list-sites`
- 模板列表:`flask --app run scan-templates`

方式二:flask shell(深入查看)
```python
flask shell
>>> from app.core.models import User, Site, Template, LoginToken
>>> User.query.count()
>>> Site.query.filter_by(status='published').all()
>>> Template.query.all()
>>> # 查看建表 SQL(SQLite)
>>> from sqlalchemy import inspect
>>> from app.core.db import db
>>> insp = inspect(db.engine)
>>> insp.get_table_names()
>>> insp.get_columns('users')
```

方式三:sqlite3 命令行
```
sqlite3 instance/app.db ".tables"
sqlite3 instance/app.db "SELECT id, email, role, status FROM users;"
sqlite3 instance/app.db ".schema users"
```

## 修复常见问题

**模板数据库不同步**
症状:`create-site` 报"数据库里没有模板"或模板列表不完整
修复:`flask --app run scan-templates`

**用户邮箱重复**
症状:`create-user` 报"用户已存在"
处理:先 `list-users` 确认,再决定是复用还是用新邮箱

**slug 被占用**
症状:`create-site` 报"slug 已被占用"
处理:先 `list-sites` 查看,选未占用的 slug

**站点数据库记录存在但文件夹缺失**
症状:构建时报文件找不到
处理:
- `list-sites` 确认 site_id
- 检查 `sites/<id>/` 是否存在
- 如不存在:用 `create-site` 重新创建,或手动建目录 + `copy_seed_data`

**SQLite 数据库锁定**
症状:`database is locked`
处理:
- 检查是否有其他 Flask 进程在运行
- 关闭其他终端窗口或终止残留进程
- SQLite 不支持高并发,MVP 阶段单进程即可

## 重置开发数据库(需用户确认)

**仅在开发早期、数据结构大改、seed 数据混乱时考虑.**

步骤:
1. 先备份:复制 `instance/app.db` → `instance/app.db.backup-<时间戳>`
2. 关闭 Flask 服务器
3. 删除 `instance/app.db`
4. 重启 Flask:`python run.py`(会自动建表)
5. 重新扫描模板:`flask --app run scan-templates`
6. 重新创建用户和站点

**警告:这会丢失所有用户数据!生产环境绝对不能做!**
必须等用户明确说"确认重置"后再执行.

## 数据库文件位置约定

```
instance/
└── app.db                        ← SQLite 数据库文件(gitignore)
```
配置文件位置:`app/core/config.py`,数据库 URI 由 `DATABASE_URL` 环境变量控制.
默认值:`sqlite:///instance/app.db`

相关模型文件:`app/core/models.py`
- User(店主账号)
- LoginToken(魔法链接 token)
- Template(模板缓存)
- Site(站点元信息)

提醒:店主网站的内容不存数据库,存在 `sites/<id>/*.yaml`.
详见 `docs/architecture.md` 第四节.
