"""Flask 应用工厂."""
from flask import Flask
from flask_wtf.csrf import CSRFProtect

from .core.config import load_config
from .core.db import db

csrf = CSRFProtect()


def create_app(config_override=None):
    app = Flask(__name__)
    app.config.update(load_config(config_override))

    # 上传体积上限：所有 multipart 请求总大小不能超过 MAX_CONTENT_LENGTH，
    # 防止巨型文件 / 图片炸弹耗尽磁盘和内存。Flask 默认 None=无上限, 这里必须显式赋值.
    if app.config.get('MAX_CONTENT_LENGTH') is None:
        app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

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
    with app.app_context():
        db.create_all()
        _migrate_users_add_columns()
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
        try:
            site_id = request.args.get('site', type=int)
            site = Site.query.get(site_id) if site_id else Site.query.order_by(Site.id.desc()).first()
            if not site:
                return {'translation_enabled': translator_ready()}
            meta_path = Path(app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
            meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
            return {'template_meta': meta, 'translation_enabled': translator_ready()}
        except Exception:
            return {'translation_enabled': False}


def _migrate_users_add_columns():
    """M1 临时迁移: 给已存在的 users 表补新增列. SQLite 兼容."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    existing = {c['name'] for c in inspector.get_columns('users')}
    stmts = []
    if 'role' not in existing:
        stmts.append("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'owner'")
    if 'display_name' not in existing:
        stmts.append("ALTER TABLE users ADD COLUMN display_name VARCHAR(80)")
    if stmts:
        with db.engine.begin() as conn:
            for s in stmts:
                conn.execute(text(s))


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
                FOREIGN KEY(user_id) REFERENCES users (id)
            )
        """))
        conn.execute(text("CREATE INDEX ix_login_tokens_email ON login_tokens (email)"))
        conn.execute(text("CREATE UNIQUE INDEX ix_login_tokens_token_hash ON login_tokens (token_hash)"))
