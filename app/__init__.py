"""Flask 应用工厂."""
import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect

from .core.config import load_config
from .core.db import db

csrf = CSRFProtect()


def create_app(config_override=None):
    app = Flask(__name__)
    app.config.update(load_config(config_override))
    # 调试模式下确保模板改动即时生效，无需重启服务器
    # Flask 默认不设置 TEMPLATES_AUTO_RELOAD, 只在 app.run(debug=True) 时才启用
    # 这里根据环境变量提前启用, 避免开发时每次改模板都要重启
    if os.environ.get('FLASK_DEBUG', '').strip() in ('1', 'true', 'True'):
        app.config['TEMPLATES_AUTO_RELOAD'] = True

    # 上传体积上限：所有 multipart 请求总大小不能超过 MAX_CONTENT_LENGTH，
    # 防止巨型文件 / 图片炸弹耗尽磁盘和内存。Flask 默认 None=无上限, 这里必须显式赋值.
    # #34: 支持从环境变量 MAX_CONTENT_LENGTH 覆盖, 与 .env.example 注释一一对应。
    if app.config.get('MAX_CONTENT_LENGTH') is None:
        _env_max = os.environ.get('MAX_CONTENT_LENGTH', '').strip()
        # 默认 24MB（视频 multipart 编码膨胀约30%，需要留余量）; 非法值回退默认
        app.config['MAX_CONTENT_LENGTH'] = (
            int(_env_max) if _env_max.isdigit() else 24 * 1024 * 1024
        )

    # #8: Session Cookie 加固。HTTPONLY 默认 True(JS 读不到), 这里再补 SAMESITE(浏览器层
    # 防 CSRF 纵深) 和会话有效期; SECURE 在生产强制(只走 HTTPS 传 cookie, 防明文窃取)。
    # 复用与上面 TEMPLATES_AUTO_RELOAD 相同的 dev 判定: 显式声明开发才放开 SECURE。
    from datetime import timedelta
    _is_dev = os.environ.get('FLASK_DEBUG', '').strip() in ('1', 'true', 'True') \
        or os.environ.get('FLASK_ENV', '').strip().lower() in ('development', 'dev')
    # 直接赋值: Flask Config 默认已含这些键(SAMESITE/SECURE 默认 None/False),
    # setdefault 会被既有 None 挡住不生效, 故强制覆盖。允许 config_override 显式传入时优先。
    app.config['SESSION_COOKIE_HTTPONLY'] = app.config.get('SESSION_COOKIE_HTTPONLY', True)
    if 'SESSION_COOKIE_SAMESITE' not in (config_override or {}):
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    if 'SESSION_COOKIE_SECURE' not in (config_override or {}):
        app.config['SESSION_COOKIE_SECURE'] = not _is_dev
    if 'PERMANENT_SESSION_LIFETIME' not in (config_override or {}):
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

    db.init_app(app)
    csrf.init_app(app)

    # 注册路由
    from .core.routes import bp as core_bp
    from .core.admin_routes import bp as admin_bp
    app.register_blueprint(core_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # 注册 CLI 命令
    from . import commands
    commands.init_app(app)

    # 自动建表（MVP 简化, 规模化后用 Alembic 迁移）
    # #31: 原 _migrate_users_add_columns 是名实不符的半成品(只补 role/display_name 两列,
    # 且这些列已在 initial commit 随模型一起引入, ALTER 分支永不触发)。已删除, 明确依赖
    # db.create_all() 按模型建全表。login_tokens 的兜底建表保留(见 #30)。
    with app.app_context():
        db.create_all()
        _migrate_login_tokens_table()

    _register_context_processors(app)
    return app


def _register_context_processors(app):
    """注入模板上下文: 当前站点的模板 meta, 用于动态渲染侧栏."""
    from pathlib import Path
    import yaml as _yaml

    @app.context_processor
    def inject_template_meta():
        from .core.models import Site
        from .core.translator import is_configured as translator_ready
        from flask import request
        # #32: translation_enabled 与 template_meta 无关, 移出 try ——
        # 原先 meta 读取出错会把 except 兜底成 translation_enabled=False, 误关翻译入口。
        result = {'translation_enabled': translator_ready()}
        try:
            site_id = request.args.get('site', type=int)
            site = Site.query.get(site_id) if site_id else Site.query.order_by(Site.id.desc()).first()
            if site:
                meta_path = Path(app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
                result['template_meta'] = (
                    _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
                )
        except Exception:
            # 不再静默吞: meta 读取失败要留痕, 但不影响 translation_enabled
            app.logger.exception('注入 template_meta 失败')
        return result


def _migrate_login_tokens_table():
    """MVP 临时迁移：旧数据库补 login_tokens 表（db.create_all 不会补已导入前缺失的表以外约束差异）."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    if 'login_tokens' in inspector.get_table_names():
        return
    with db.engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE login_tokens (
                id INTEGER NOT NULL,
                user_id INTEGER,
                email VARCHAR(255) NOT NULL,
                token_hash VARCHAR(64) NOT NULL,
                expires_at DATETIME NOT NULL,
                used_at DATETIME,
                ip_address VARCHAR(45),
                created_at DATETIME NOT NULL,
                PRIMARY KEY (id),
                -- #30: 补 ON DELETE CASCADE, 与模型 LoginToken.user_id 的 ondelete='CASCADE'
                -- 对齐; 否则这条兜底建表路径建出的表删用户时会留下孤儿 token。
                FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """))
        conn.execute(text("CREATE INDEX ix_login_tokens_email ON login_tokens (email)"))
        conn.execute(text("CREATE UNIQUE INDEX ix_login_tokens_token_hash ON login_tokens (token_hash)"))
