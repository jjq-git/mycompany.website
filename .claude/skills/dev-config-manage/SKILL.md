---
name: dev-config-manage
description: "管理系统配置(.env 环境变量 / config.py 设置 / 基础设施切换)"
---

当用户说"修改配置"、"设置环境变量"、"改 .env"、"切换 CDN"时触发.
管理系统运行所需的环境变量和配置项.

配置加载链(`app/core/config.py`):
`.env` 文件 → 环境变量 → `load_config()` → Flask `app.config`

## 配置文件位置

```
项目根目录/
├── .env              ← 环境变量(不提交到 git,在 .gitignore 中)
├── .env.example      ← 配置模板(提交到 git,供参考)
└── app/core/config.py ← 配置加载逻辑 + 默认值
```

## 查看当前配置

在 flask shell 中查看:
```python
flask shell
>>> from flask import current_app
>>> dict(current_app.config)
```

查看关键配置项:
```python
>>> current_app.config['SECRET_KEY']
>>> current_app.config['DATABASE_URL']  # SQLALCHEMY_DATABASE_URI
>>> current_app.config['SITES_DIR']
>>> current_app.config['TEMPLATES_DIR']
>>> current_app.config['OUTPUT_DIR']
>>> current_app.config['PLATFORM_DOMAIN']
```

## 完整配置项说明

`.env.example` 中的所有配置项:

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SECRET_KEY` | `dev-key-change-me` | Flask session 加密密钥,**生产必须换强随机值** |
| `DATABASE_URL` | `sqlite:///instance/app.db` | 数据库连接串.SQLite 默认,规模化后改 PostgreSQL |
| `PLATFORM_DOMAIN` | `mycompany.website` | 平台主域名 |
| `TRANSLATION_API_KEY` | 空 | DeepSeek API Key(不填则翻译功能不可用) |
| `TRANSLATION_API_BASE` | `https://api.deepseek.com/v1` | AI 翻译 API 地址(OpenAI 兼容格式) |
| `TRANSLATION_MODEL` | `deepseek-chat` | AI 翻译使用的模型 |

`config.py` 中的默认值(无需 .env 设置):
| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///instance/app.db` | 数据库位置 |
| `SITES_DIR` | `<ROOT>/sites` | 站点数据目录 |
| `TEMPLATES_DIR` | `<ROOT>/site_templates` | 模板目录 |
| `UPLOADS_DIR` | `<ROOT>/uploads` | 上传文件目录 |
| `OUTPUT_DIR` | `<ROOT>/output` | 构建输出目录 |

## 修改配置

**方式一:修改 .env 文件**(推荐,持久化)
```
# 编辑 .env
SECRET_KEY=新的强随机值
PLATFORM_DOMAIN=example.com
TRANSLATION_API_KEY=sk-xxx
```
修改后需要**重启 Flask 服务器**才能生效.

**方式二:设置环境变量**(临时,仅当前终端)
```
$env:SECRET_KEY = "临时值"
$env:FLASK_HOST='0.0.0.0'; $env:FLASK_DEBUG='1'; python run.py
```

**方式三:修改 config.py**(修改默认值)
直接编辑 `app/core/config.py` 中的 `load_config()` 函数.
注意:config.py 中的值会被 .env 中的同名变量覆盖.

## 生成安全的 SECRET_KEY

```python
python -c "import secrets; print(secrets.token_hex(32))"
```

输出示例:`a1b2c3d4e5f6...64个十六进制字符`

复制这个值到 `.env`:
```
SECRET_KEY=a1b2c3d4e5f6...
```

**安全提醒**:
- 默认值 `dev-key-change-me` 仅用于开发
- 生产环境必须用强随机值
- 泄露 SECRET_KEY 等于泄露所有用户 session
- `.env` 已在 `.gitignore` 中,不要提交

## 切换数据库

**SQLite → PostgreSQL**(规模化后):

`.env` 中设置:
```
DATABASE_URL=postgresql://user:password@localhost:5432/mycompany
```

需要额外安装驱动:
```
pip install psycopg2-binary
```

迁移步骤:
1. 备份 SQLite 数据:`copy instance\app.db instance\app.db.backup`
2. 创建 PostgreSQL 数据库
3. 修改 `DATABASE_URL`
4. 重启 Flask(自动建表,但数据不会自动迁移)
5. 手动迁移数据或从头开始

## 配置 AI 翻译

翻译功能使用 DeepSeek API(OpenAI 兼容格式).

1. 获取 API Key:访问 https://platform.deepseek.com
2. 设置环境变量:
   ```
   TRANSLATION_API_KEY=sk-your-key
   TRANSLATION_API_BASE=https://api.deepseek.com/v1
   TRANSLATION_MODEL=deepseek-chat
   ```
3. 重启服务器
4. 在后台多语言编辑页面可以看到"AI 翻译"按钮

不设置 `TRANSLATION_API_KEY` 时翻译功能不可用(不报错,只是不显示翻译按钮).

## 常见问题

| 问题 | 原因 | 修复 |
|------|------|------|
| 改了 .env 不生效 | 未重启 Flask | 停止并重新 `$env:FLASK_HOST='0.0.0.0'; $env:FLASK_DEBUG='1'; python run.py` |
| SECRET_KEY 太弱 | 用了默认值 | 生成强随机值替换 |
| 数据库找不到 | DATABASE_URL 路径不对 | 检查 SQLite 文件路径 |
| 翻译功能不显示 | TRANSLATION_API_KEY 为空 | 设置 API Key 并重启 |
| .env 被提交了 | .gitignore 配置有误 | 确认 .env 在 .gitignore 中 |

## 关联技能

- `db-manage`:数据库管理和备份
- `dev-server`:启动服务器
