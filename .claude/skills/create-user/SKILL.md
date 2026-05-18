---
description: "创建用户账号(邮箱魔法链接登录)"
---

当用户说"创建用户"、"新建账号"、"加个用户"时触发.
系统使用邮箱魔法链接登录(无密码),开发阶段跳过邮件发送,链接打印到控制台.

核心代码:`app/commands.py` → `create_user_cmd()`
登录逻辑:`app/core/routes.py` → `_create_magic_link()` → `magic_login()`

## 前置条件

1. 服务器未启动或已启动均可(CLI 命令直接操作数据库)
2. 数据库已初始化(`instance/app.db` 存在)
3. 如果是首次使用,项目至少初始化过一次(Flask 运行过)

## 创建用户

运行命令:
```
flask --app run create-user <email>
```

示例:
```
flask --app run create-user admin@test.com
```

输出:
```
已创建用户: id=1, email=admin@test.com
```

如果用户已存在:
```
用户已存在: admin@test.com
```

创建逻辑(`commands.py:43-54`):
- 检查邮箱是否已注册
- 如果未注册:创建 User 记录,status='active', role='owner'
- 开发阶段 email_verified_at 不自动设置(首次登录时设置)

## 模型字段说明

`User` 模型(`app/core/models.py:15-28`):

| 字段 | 说明 | 默认值 |
|------|------|--------|
| email | 登录邮箱(唯一) | - |
| status | active / suspended / deleted | active |
| role | owner / admin | owner |
| display_name | 显示名称 | 空 |
| preferred_lang | 偏爱语言 | zh |
| email_verified_at | 邮箱验证时间 | 首次登录时设置 |
| last_login_at | 最后登录时间 | 登录时更新 |

## 设为管理员

如果需要平台管理员权限(可以管理所有站点):
```
flask --app run promote-admin <email>
```

输出:
```
已将 admin@test.com 提升为 admin
```

已经是 admin 时:
```
已经是 admin: admin@test.com
```

admin vs owner 权限区别:
- `owner`:只看自己的站点,只能管理自己的内容
- `admin`:看所有站点,可访问任意站点的后台

## 列出所有用户

```
flask --app run list-users
```

输出:
```
共 2 个用户:
  id=1  email=admin@test.com  role=admin  status=active  sites=1
  id=2  email=owner@test.com  role=owner  status=active  sites=0
```

## 登录流程

1. 访问 `http://localhost:5000/login`
2. 输入邮箱 → 提交
3. 开发环境:控制台打印魔法链接,同时页面上显示可点击链接
4. 点击链接 → 自动登录 → 跳转到后台概览

魔法链接有效期:15 分钟
一次性使用:token 使用后标记 `used_at`,不可复用

## 常见问题

| 问题 | 原因 | 修复 |
|------|------|------|
| 用户已存在 | 该邮箱已注册 | 用 `list-users` 查看,或换邮箱 |
| 登录链接无效 | token 已使用或过期 | 重新获取(再填一次邮箱) |
| 登录后空白页 | 该用户没有站点 | 引导用户创建站点 |
| 无法访问某站点 | 用户不是 owner 也不是 admin | 确认站点 owner 或提升为 admin |

## 关联技能

- `create-site`:为用户创建站点
- `db-manage`:查看和管理数据库
- `list-info`(规划中):批量查看系统信息
- `dev-server`:启动服务器后测试登录
