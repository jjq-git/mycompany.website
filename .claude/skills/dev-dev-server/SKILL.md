---
name: dev-dev-server
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

执行命令(必须带这两个环境变量,原因见下):
```
$env:FLASK_HOST='0.0.0.0'; $env:FLASK_DEBUG='1'; python run.py
```

- `FLASK_HOST=0.0.0.0` —— 不设就只绑回环(`.env` 里这项是注释掉的),
  局域网地址 http://192.168.1.31:5000 会断掉,别人正在看的服务会被弄停.
- `FLASK_DEBUG=1` —— 不设则 `TEMPLATES_AUTO_RELOAD` 为 False,改模板不生效.
  对外暴露时 `run.py` 会自动关掉 Werkzeug 交互式调试器(RCE 风险),模板热重载不受影响.

启动前必须先杀光 5000 端口上的所有进程(含 Flask reloader 的父进程,
只杀监听端口的子进程会留下父进程重新 fork 抢端口).

服务器启动后输出类似:
```
提示: host=0.0.0.0 对外暴露, 已自动关闭 Werkzeug 调试器(RCE 风险); 模板热重载仍生效。
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:5000
* Running on http://192.168.1.31:5000
```

## 验证服务器

启动后验证:
1. 浏览器访问 `http://127.0.0.1:5000`(命令行工具尤其别用 `localhost`,
   它在本机先解析到 IPv6 `::1`,而服务只监听 IPv4,每个请求要白等约 2 秒)
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

热重载**不是默认开启的**——`run.py` 默认 `FLASK_DEBUG=0`,必须显式设 `FLASK_DEBUG=1`.

按上面的推荐命令(`FLASK_HOST=0.0.0.0` + `FLASK_DEBUG=1`)启动时:
- 修改模板文件 (HTML/Jinja2) → 刷新浏览器即可,**不用重启**
- 修改静态文件 (CSS/JS) → 刷新浏览器即可(注意浏览器缓存,按 Ctrl+Shift+R)
- 修改 Python 文件 → **需要手动重启**.对外暴露时 Werkzeug reloader 随调试器
  一起关闭了,不会自动重启进程

只在回环地址(不设 `FLASK_HOST`)且 `FLASK_DEBUG=1` 时,Python 文件才会触发自动重启,
此时交互式调试器也会打开.

## 关联技能

- `db-manage`:数据库备份和检查
- `scan-templates`:同步模板到数据库
- `create-user`:创建登录账号
- `debug-site`:站点问题诊断
