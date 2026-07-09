"""Flask 应用工厂."""
import os
import re
from pathlib import Path

from flask import Flask, jsonify, request, session, send_from_directory
from flask_wtf.csrf import CSRFProtect

from .core.config import load_config
from .core.db import db

csrf = CSRFProtect()


def create_app(config_override=None):
    # 修正 Windows 上 Python mimetypes 对静态媒体类型识别不完整的问题。
    # 浏览器在 <img>/<video> 标签中遇到错误 MIME 时可能拒绝渲染。
    import mimetypes
    mimetypes.add_type('image/svg+xml', '.svg')
    mimetypes.add_type('image/webp', '.webp')
    mimetypes.add_type('video/mp4', '.mp4')
    mimetypes.add_type('video/webm', '.webm')
    mimetypes.add_type('video/ogg', '.ogg')

    # static_folder=None 阻止 Werkzeug SharedDataMiddleware 在 WSGI 层拦截 /static/
    # 改为自定义路由接管，优先从模板目录 serve，兜底 app/static/
    app = Flask(__name__, static_folder=None)
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
        # 默认 64MB（视频 multipart 编码膨胀约30%，需要留余量）; 非法值回退默认
        app.config['MAX_CONTENT_LENGTH'] = (
            int(_env_max) if _env_max.isdigit() else 64 * 1024 * 1024
        )

    # #8: Session Cookie 加固。HTTPONLY 默认 True(JS 读不到), 这里再补 SAMESITE(浏览器层
    # 防 CSRF 纵深) 和会话有效期; SECURE 在生产强制(只走 HTTPS 传 cookie, 防明文窃取)。
    # 判定逻辑：只有显式设 FLASK_ENV=production 才开 Secure；未设置或设 dev 均关 Secure。
    # 旧逻辑用 "not FLASK_DEBUG" 反推生产，FLASK_DEBUG 忘了设就锁死所有 HTTP 表单(CSRF 400)。
    from datetime import timedelta
    _is_dev = os.environ.get('FLASK_DEBUG', '').strip() in ('1', 'true', 'True') \
        or os.environ.get('FLASK_ENV', '').strip().lower() in ('development', 'dev')
    _is_prod = os.environ.get('FLASK_ENV', '').strip().lower() in ('production', 'prod')
    # 直接赋值: Flask Config 默认已含这些键(SAMESITE/SECURE 默认 None/False),
    # setdefault 会被既有 None 挡住不生效, 故强制覆盖。允许 config_override 显式传入时优先。
    app.config['SESSION_COOKIE_HTTPONLY'] = app.config.get('SESSION_COOKIE_HTTPONLY', True)
    if 'SESSION_COOKIE_SAMESITE' not in (config_override or {}):
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    if 'SESSION_COOKIE_SECURE' not in (config_override or {}):
        # 只对显式声明的生产环境开 Secure；未配置 / dev 模式均走 HTTP cookie
        app.config['SESSION_COOKIE_SECURE'] = _is_prod and not _is_dev
    if 'PERMANENT_SESSION_LIFETIME' not in (config_override or {}):
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

    db.init_app(app)
    csrf.init_app(app)

    # CSRF 校验失败时重定向回来源页并给出提示，而不是返回空白 400
    # 常见触发场景：服务器重启导致浏览器 session cookie 与当前 CSRF token 不匹配
    from flask_wtf.csrf import CSRFError
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        from flask import flash, redirect, request
        app.logger.warning('CSRF 校验失败: %s (referrer=%s)', e.description, request.referrer)
        flash('页面已过期，请重新提交。', 'warning')
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Page expired. Please refresh and try again.'}), 400
        return redirect(request.referrer or request.url)

    # 注册路由
    @app.errorhandler(401)
    def handle_unauthorized(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Please log in again.'}), 401
        return e

    @app.errorhandler(404)
    def handle_not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'API endpoint not found. Please restart the server and refresh the page.'}), 404
        return e

    @app.errorhandler(413)
    def handle_request_too_large(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Uploaded file is too large.'}), 413
        return e

    from .core.routes import bp as core_bp
    from .core.admin_routes import bp as admin_bp
    app.register_blueprint(core_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.route('/favicon.ico', endpoint='favicon')
    def _serve_favicon():
        return send_from_directory(str((Path(__file__).parent / 'static').resolve()), 'icon.svg',
                                   mimetype='image/svg+xml')

    # 自定义 /static/ 路由（static_folder=None，Werkzeug 不拦截，请求会到达这里）
    # 搜索优先级：
    #   1. 模板预览 session → output/_preview/<tpl>/static/
    #   2. 站点预览 session → output/<site_id>/static/
    #   3. Referer 推断模板 → output/_preview/<tpl>/static/
    #   4. 模板源目录 site_templates/*/static/
    #   5. 兜底：app/static/
    _app_static = Path(__file__).parent / 'static'

    @app.route('/static/<path:filename>', endpoint='static')
    def _serve_static(filename):
        # 1. 模板预览 session（最优先）
        tpl_name = session.get('current_template_preview')
        if tpl_name:
            d = Path(app.config['OUTPUT_DIR']) / '_preview' / tpl_name / 'static'
            if (d / filename).exists():
                return send_from_directory(str(d.resolve()), filename)

        # 2. 站点预览 session
        site_id = session.get('current_site_id')
        if site_id:
            d = Path(app.config['OUTPUT_DIR']) / str(site_id) / 'static'
            if (d / filename).exists():
                return send_from_directory(str(d.resolve()), filename)

        # 3. Referer 推断模板
        if tpl_name is None and site_id is None:
            m = re.search(r'/templates/([a-zA-Z0-9_-]+)/preview/', request.headers.get('Referer', ''))
            if m:
                d = Path(app.config['OUTPUT_DIR']) / '_preview' / m.group(1) / 'static'
                if (d / filename).exists():
                    return send_from_directory(str(d.resolve()), filename)

        # 4. 搜索模板源目录
        for tpl_dir in sorted(Path(app.config['TEMPLATES_DIR']).iterdir()):
            if not tpl_dir.is_dir() or tpl_dir.name.startswith('.'):
                continue
            d = tpl_dir / 'static'
            if (d / filename).exists():
                return send_from_directory(str(d.resolve()), filename)

        # 5. 兜底：app/static/
        if (_app_static / filename).exists():
            return send_from_directory(str(_app_static.resolve()), filename)

        from flask import abort
        abort(404)

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
        from .core.models import ContactMessage, Site
        from .core.translator import is_configured as translator_ready
        from flask import request
        # #32: translation_enabled 与 template_meta 无关, 移出 try ——
        # 原先 meta 读取出错会把 except 兜底成 translation_enabled=False, 误关翻译入口。
        result = {
            'translation_enabled': translator_ready(),
            'platform_domain': app.config.get('PLATFORM_DOMAIN', '') or 'mycompany.website',
        }
        try:
            site_id = request.args.get('site', type=int)
            site = Site.query.get(site_id) if site_id else Site.query.order_by(Site.id.desc()).first()
            if site:
                meta_path = Path(app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
                result['template_meta'] = (
                    _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
                )
                # 留言未读数, 供侧边栏 badge 使用
                result['unread_count'] = ContactMessage.query.filter_by(
                    site_id=site.id, is_read=False, is_spam=False
                ).count()
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
