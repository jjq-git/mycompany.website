---
description: "启动 Flask 开发服务器"
---

当用户说"启动服务器"、"跑起来"、"启动开发环境"时触发.
用于本地开发调试,启动 Flask 开发服务器.

## 前置检查

启动前确认以下三项:

1. **检查 .env 文件**
   `instance/app.db` 在 `.env` 中通过 `DATABASE_URL` 配置,
   但实际上数据库路径在 `app/core/config.py` 中默认为 `sqlite:///instance/app.db`.
   如果 `.env` 不存在,复制 `.env.example`:
   ```
   copy .env.example .env
   ```
   然后生成随机 SECRET_KEY(可用 Python `secrets.token_hex(32)`).

2. **检查依赖**
   ```
   pip install -r requirements.txt
   ```

3. **确认数据库存在**
   SQLite 数据库在 `instance/app.db`.如果不存在,Flask 首次启动会自动建表.
   如果数据库存在但表结构不对,参考 `db-manage` 技能.

4. **确认端口未被占用**
   默认端口 5000.如果被占用:
   ```
   netstat -ano | findstr :5000
   ```
   或改用其他端口:`flask run --port 5001`

## 启动服务器

执行命令:
```
python run.py
```

服务器启动后输出类似:
```
* Running on http://127.0.0.1:5000
```

## 验证服务器

启动后验证:
1. 浏览器访问 `http://localhost:5000`
2. 应该看到登录页面(如果没有用户,显示模板库引导页)
3. 如果出现 500 错误,检查控制台输出的错误信息
4. 如果数据库为空,先执行 `flask --app run create-user <email>` 创建用户

## 常见启动错误

| 错误 | 原因 | 修复 |
|------|------|------|
| `ModuleNotFoundError: No module named 'flask'` | 未安装依赖 | `pip install -r requirements.txt` |
| `Address already in use` | 端口 5000 被占用 | 关闭其他进程或换端口 |
| `sqlalchemy.exc.OperationalError` | 数据库文件损坏 | 参考 `db-manage` 技能 |
| `TemplateNotFound: auth/login.html` | 模板文件缺失 | 检查 `app/templates/auth/` 目录 |
| `KeyError: 'SECRET_KEY'` | .env 缺少 SECRET_KEY | 复制 .env.example 并设置值 |
| `ImportError: attempted relative import` | 当前目录不对 | 确保在项目根目录执行 |

## 开发热重载

Flask 开发服务器默认启用热重载:
- 修改 Python 文件 → 服务器自动重启
- 修改模板文件 (HTML/Jinja2) → 刷新浏览器即可
- 修改静态文件 (CSS/JS) → 刷新浏览器即可(注意浏览器缓存,按 Ctrl+Shift+R)

不需要自动重启的情况(重启较慢时可关闭):
设置环境变量 `FLASK_DEBUG=0` 或修改 `run.py` 中 `debug=True` 为 `False`.

## 关联技能

- `db-manage`:数据库备份和检查
- `scan-templates`:同步模板到数据库
- `create-user`:创建登录账号
- `debug-site`:站点问题诊断
