---
description: "安全清理(删除测试用户/站点/构建输出)"
---

当用户说"清理数据"、"删除测试站点"、"清理 output"、"重置开发环境"时触发.

CLAUDE.md 禁止事项明确说不能随意删除 `sites/` 和 `output/` 目录.
本技能提供安全的清理方式——通过 CLI 命令和受控的操作来清理,
避免 `rm -rf` 误删.

## 安全原则

**永远不要直接 `rm -rf sites/` 或 `rm -rf output/`** —— 这违反 CLAUDE.md 禁止事项.

安全的清理方式:
1. 删除站点:用后台的删除功能或通过 flask shell 操作(会同时清理数据库 + 文件)
2. 删除用户:通过 flask shell 操作
3. 清理构建输出:删除 output/ 下特定站点的子目录

清理前必须:
- 先用 `list-sites` / `list-users` 确认要删除的目标
- 向用户确认(列出将要删除的内容和影响范围)
- 如果用户不确定,先备份数据库

## 删除站点

**方式一:通过后台界面**(推荐)
登录后台 → 站点设置 → 删除站点(如果有此功能)
或者直接访问 `/sites/delete` 路由(POST 请求).

后台删除逻辑(`routes.py:658-693`):
1. 删除站点文件夹 `sites/<id>/`
2. 删除构建输出 `output/<id>/`
3. 删除数据库 Site 记录
4. 显示 flash 消息 "站点已删除"

**方式二:flask shell**
```python
flask shell
>>> from app.core.models import Site
>>> from app.core.db import db
>>> import shutil
>>> from pathlib import Path
>>> from flask import current_app

>>> site_id = 1  # 要删除的站点 id
>>> site = Site.query.get(site_id)
>>> if site:
...     # 删除文件夹
...     site_folder = Path(current_app.config['SITES_DIR']) / str(site_id)
...     if site_folder.exists():
...         shutil.rmtree(site_folder)
...     # 删除 output
...     output_dir = Path(current_app.config['OUTPUT_DIR']) / str(site_id)
...     if output_dir.exists():
...         shutil.rmtree(output_dir)
...     # 删除数据库记录
...     db.session.delete(site)
...     db.session.commit()
...     print(f'已删除站点 #{site_id}')
```

## 删除用户

**flask shell 方式**:
```python
flask shell
>>> from app.core.models import User, Site
>>> from app.core.db import db
>>> import shutil
>>> from pathlib import Path
>>> from flask import current_app

>>> user_id = 1  # 要删除的用户 id
>>> user = User.query.get(user_id)
>>> if user:
...     # 先删除该用户的所有站点
...     for site in Site.query.filter_by(owner_id=user.id).all():
...         site_folder = Path(current_app.config['SITES_DIR']) / str(site.id)
...         if site_folder.exists():
...             shutil.rmtree(site_folder)
...         output_dir = Path(current_app.config['OUTPUT_DIR']) / str(site.id)
...         if output_dir.exists():
...             shutil.rmtree(output_dir)
...         db.session.delete(site)
...     # 删除用户
...     db.session.delete(user)
...     db.session.commit()
...     print(f'已删除用户 #{user_id} 及其所有站点')
```

注意:`LoginToken` 表通过 `user_id` 外键关联,SQLite 默认不级联删除,
可能需要先删除相关 token:
```python
>>> from app.core.models import LoginToken
>>> LoginToken.query.filter_by(user_id=user.id).delete()
```

## 清理构建输出

构建输出在 `output/<site_id>/`,每个站点独立.

清理特定站点的构建输出:
```python
flask shell
>>> from pathlib import Path
>>> from flask import current_app

>>> site_id = 1
>>> output_dir = Path(current_app.config['OUTPUT_DIR']) / str(site_id)
>>> if output_dir.exists():
...     import shutil
...     shutil.rmtree(output_dir)
...     print(f'已清理 output/{site_id}/')
```

清理所有构建输出(保留 output 目录本身):
```python
flask shell
>>> from pathlib import Path
>>> from flask import current_app
>>> import shutil

>>> output_root = Path(current_app.config['OUTPUT_DIR'])
>>> for item in output_root.iterdir():
...     if item.is_dir():
...         shutil.rmtree(item)
...         print(f'已清理 {item.name}')
```

注意:`output/` 通过 `.gitignore` 排除,不会提交到 git.

## 清理测试模板

`site_templates/` 由 git 管理.删除测试模板:
```
# 先确认是否在 git 追踪中
git status site_templates/<name>/

# 如果是未追踪的测试模板
Remove-Item -Recurse -Force site_templates\<name>

# 如果已提交,用 git rm
git rm -r site_templates/<name>/
```

删除后同步数据库:
```
flask --app run scan-templates
```

注意:删除的模板如果有站点在使用,那些站点会找不到模板,
构建时会报错.先确保没有站点依赖该模板.

## 软删除 vs 硬删除

Site 模型有 `soft_deleted_at` 字段,支持软删除.
软删除的站点数据还在,只是标记为已删除.

当前路由 `site_delete()` 是硬删除(直接删记录 + 文件夹).

如果你只是想暂时隐藏站点:
```python
flask shell
>>> from app.core.models import Site
>>> from app.core.db import db
>>> from datetime import datetime, timezone

>>> site = Site.query.get(site_id)
>>> site.soft_deleted_at = datetime.now(timezone.utc)
>>> db.session.commit()
```

## 清理前检查和确认

清理前执行:
1. `flask --app run list-sites` → 确认要删除的站点
2. `flask --app run list-users` → 确认要删除的用户及其站点数
3. 备份数据库:`copy instance\app.db instance\app.db.backup-<date>`
4. 向用户展示将删除的内容清单,等待确认

## 关联技能

- `db-manage`:数据库备份
- `list-info`(本批创建中):查看系统状态
- `create-user` / `create-site`:重新创建清理后的测试数据
