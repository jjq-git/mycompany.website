"""Flask 应用工厂."""
from flask import Flask

from .core.config import load_config
from .core.db import db


def create_app(config_override=None):
    app = Flask(__name__)
    app.config.update(load_config(config_override))

    db.init_app(app)

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

    _register_context_processors(app)
    return app


def _register_context_processors(app):
    """注入模板上下文: 当前站点的模板 meta, 用于动态渲染侧栏."""
    from pathlib import Path
    import yaml as _yaml

    @app.context_processor
    def inject_template_meta():
        from .core.models import Site
        from flask import request
        try:
            site_id = request.args.get('site', type=int)
            site = Site.query.get(site_id) if site_id else Site.query.order_by(Site.id.desc()).first()
            if not site:
                return {}
            meta_path = Path(app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
            meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
            return {'template_meta': meta}
        except Exception:
            return {}


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
