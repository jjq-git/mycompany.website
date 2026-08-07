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

    # 安全（M1）：只信任 TRUSTED_PROXY_COUNT 层反向代理传来的 X-Forwarded-For。
    # 默认 0 = 不信任任何代理头，request.remote_addr 用真实 TCP 源 IP，杜绝客户端伪造
    # X-Forwarded-For 绕过按 IP 的登录限流。生产部署在 Nginx/CDN 后时，按实际反代层数
    # 在 .env 设 TRUSTED_PROXY_COUNT（如单层 Nginx 设 1），ProxyFix 才据此还原真实客户端 IP。
    _proxy_count = os.environ.get('TRUSTED_PROXY_COUNT', '0').strip()
    _proxy_count = int(_proxy_count) if _proxy_count.isdigit() else 0
    if _proxy_count > 0:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=_proxy_count, x_proto=_proxy_count)
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

    # 表单“分段数”上限：multipart 请求里每个表单字段算一个 part。Werkzeug 3.x 默认仅 1000，
    # 超过就抛 413 RequestEntityTooLarge——与请求体大小无关，纯计数。富文本详情编辑页
    # (specs/features/gallery 多组重复字段 + 多语言隐藏字段)字段数很容易破千，导致店主
    # “只加一段文字”也保存失败。放宽到 5000（仍受 MAX_CONTENT_LENGTH 总量约束，不影响
    # 文件上传防护）。支持 env 覆盖。
    # 注意：Flask 默认已把这两个键初始化为 1000 / 500KB（非 None），故不能用 "is None" 守卫，
    # 否则我方默认值永远被跳过——必须无条件覆盖。
    _env_parts = os.environ.get('MAX_FORM_PARTS', '').strip()
    app.config['MAX_FORM_PARTS'] = (
        int(_env_parts) if _env_parts.isdigit() else 5000
    )

    # 表单“文本字段总内存”上限：Werkzeug 3.x 默认仅 500KB，是限制非文件字段累计大小的
    # 独立阈值。富文本正文将来变长同样会撞它，顺手放宽到 16MB（远低于 64MB 总上限，
    # 不放行大文件）。支持 env 覆盖。
    _env_mem = os.environ.get('MAX_FORM_MEMORY_SIZE', '').strip()
    app.config['MAX_FORM_MEMORY_SIZE'] = (
        int(_env_mem) if _env_mem.isdigit() else 16 * 1024 * 1024
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

    @app.url_defaults
    def _use_site_slugs_in_urls(endpoint, values):
        """Keep internal IDs in storage while emitting readable site slugs in public URLs."""
        from .core.models import Site
        site_value = values.get('site')
        if isinstance(site_value, int):
            site = db.session.get(Site, site_value)
            if site:
                values['site'] = site.slug
        if endpoint in {'core.preview', 'core.live_preview', 'core.preview_site', 'core.preview_or_build'}:
            preview_value = values.get('site_id')
            if isinstance(preview_value, int):
                site = db.session.get(Site, preview_value)
                if site:
                    values['site_id'] = site.slug

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
        tpl_name = session.get('current_template_preview')
        tpl_version = session.get('current_template_preview_version')
        site_id = session.get('current_site_id')

        # 1. 模板预览 Referer 优先（公共模板资源，不用于定位任何私有站点）
        m = re.search(r'/templates/([a-zA-Z0-9_-]+)/preview/', request.headers.get('Referer', ''))
        if m:
            referer_template = m.group(1)
            version = tpl_version if tpl_name == referer_template else None
            candidates = []
            if version:
                candidates.append(Path(app.config['OUTPUT_DIR']) / '_preview_versions' / referer_template / version / 'static')
            else:
                version_root = Path(app.config['OUTPUT_DIR']) / '_preview_versions' / referer_template
                if version_root.exists():
                    candidates.extend(
                        path / 'static' for path in sorted(
                            (item for item in version_root.iterdir() if item.is_dir()),
                            key=lambda item: item.stat().st_mtime_ns,
                            reverse=True,
                        )
                    )
            candidates.append(Path(app.config['OUTPUT_DIR']) / '_preview' / referer_template / 'static')
            for d in candidates:
                if (d / filename).exists():
                    return send_from_directory(str(d.resolve()), filename)

        # 2. 站点预览/后台 session；不能被另一个标签页残留的模板 session 覆盖。
        if site_id:
            d = Path(app.config['OUTPUT_DIR']) / str(site_id) / 'static'
            if (d / filename).exists():
                return send_from_directory(str(d.resolve()), filename)

        # 3. 无站点匹配时再使用模板预览 session，支持直接打开资源。
        if tpl_name:
            d = (Path(app.config['OUTPUT_DIR']) / '_preview_versions' / tpl_name / tpl_version / 'static'
                 if tpl_version else Path(app.config['OUTPUT_DIR']) / '_preview' / tpl_name / 'static')
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
        _migrate_platform_roles()
        _migrate_sites_add_custom_domain()

    _register_context_processors(app)
    _register_template_filters(app)
    return app


def _register_template_filters(app):
    """注册模板过滤器。"""
    from datetime import timedelta, timezone

    # 数据库里存的是 UTC（见 models.utcnow()），且 SQLite 读回来是不带 tzinfo 的 naive 值。
    # 模板若直接 strftime，等于把 UTC 当本地时间显示，中国用户看到的时间会早 8 小时
    # （老板下午改完内容，"最近更新"却显示上午，会以为没保存成功）。
    #
    # 这里用固定偏移而不是 ZoneInfo('Asia/Shanghai')，原因有两个：
    #   1. 中国自 1991 年起不再实行夏令时，UTC+8 恒定，固定偏移的结果完全正确；
    #   2. Windows 没有系统 tzdata，ZoneInfo 要额外装 tzdata 包，与"依赖能少则少"冲突。
    CN_TZ = timezone(timedelta(hours=8))

    @app.template_filter('localtime')
    def localtime(value, fmt='%Y-%m-%d %H:%M'):
        """把 UTC 时间转成东八区再格式化；空值返回空串，交给模板自己兜底文案。"""
        if not value:
            return ''
        # naive 值一律按 UTC 解释；已带时区的值直接换算 —— 两种来源都能正确处理
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(CN_TZ).strftime(fmt)

    # 审计日志的 action 是稳定的机器码（写库、检索、对账都靠它，不能改），
    # 但直接显示给店主等于让老板读 "site.content.update"。这里只做展示层映射，
    # 库里存什么不变。覆盖当前库中出现过的全部事件码。
    ACTION_LABELS = {
        'site.content.update': '更新站点内容',
        'site.identity.update': '修改站点信息',
        'site.create': '创建站点',
        'site.trash': '删除站点',
        'site.restore': '恢复站点',
        'site.publish': '发布站点',
        'account.profile.update': '更新账户资料',
        'organization.update': '更新组织信息',
        'organization.member.role': '调整成员角色',
        'organization.site.add': '站点加入组织',
        'organization.site.remove': '站点移出组织',
        'organization.invitation.create': '创建团队邀请',
        'organization.invitation.accept': '接受团队邀请',
        'organization.invitation.revoke': '撤销团队邀请',
        'platform.user.delete': '删除平台用户',
        'platform.user.suspend': '停用平台用户',
        'platform.user.activate': '启用平台用户',
        'platform.user.role.update': '调整平台角色',
        'security.identity.bind': '绑定登录方式',
        'security.identity.unbind': '解绑登录方式',
        'security.identity.primary': '设为主登录方式',
        'security.session.revoke': '退出登录设备',
        'billing.order.create': '创建订单',
        'wechat.bind.mock': '绑定微信',
        'wechat.unbind': '解绑微信',
    }

    @app.template_filter('action_label')
    def action_label(value):
        """审计事件码转中文；未收录的码原样返回，便于发现遗漏而不是显示空白。"""
        if not value:
            return ''
        return ACTION_LABELS.get(value, value)


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
        result = {
            'translation_enabled': translator_ready(),
            'platform_domain': app.config.get('PLATFORM_DOMAIN', '') or 'mycompany.website',
            'content_count': 0,
        }
        try:
            site_ref = request.args.get('site', '').strip().lower()
            if site_ref:
                site = Site.query.filter_by(slug=site_ref).filter(Site.soft_deleted_at.is_(None)).first()
                if site is None and site_ref.isdigit():
                    site = Site.query.filter_by(id=int(site_ref)).filter(Site.soft_deleted_at.is_(None)).first()
            else:
                site = Site.query.filter(Site.soft_deleted_at.is_(None)).order_by(Site.id.desc()).first()
            if site:
                meta_path = Path(app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
                result['template_meta'] = (
                    _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
                )
                # 内容中心统计来自站点菜单声明的列表数据集，侧栏在所有后台页面保持一致。
                from .core.routes import _content_catalog, _get_panel_lang
                lang, _languages, default_lang = _get_panel_lang(site)
                result['content_count'] = sum(
                    len(entry.get('items') or [])
                    for entry in _content_catalog(site, lang, default_lang)
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


def _migrate_platform_roles():
    """把历史平台普通角色 owner 迁移为 user；组织 owner 不在 users 表，不受影响。"""
    from sqlalchemy import text
    with db.engine.begin() as conn:
        conn.execute(text("UPDATE users SET role = 'user' WHERE role = 'owner'"))


def _migrate_sites_add_custom_domain():
    """MVP 临时迁移：旧库的 sites 表补 custom_domain 列（db.create_all 不改已存在表的列）。

    自定义域名功能(方案A)新增列。SQLite 的 ADD COLUMN 不支持直接建唯一索引，
    因此列本身用 ALTER 补，唯一性再单独 CREATE UNIQUE INDEX（IF NOT EXISTS 幂等）。
    """
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    columns = {c['name'] for c in inspector.get_columns('sites')}
    with db.engine.begin() as conn:
        if 'custom_domain' not in columns:
            conn.execute(text('ALTER TABLE sites ADD COLUMN custom_domain VARCHAR(253)'))
        # 唯一索引兜底：新库由 create_all 建，旧库由这里补；IF NOT EXISTS 保证重复启动安全
        conn.execute(text(
            'CREATE UNIQUE INDEX IF NOT EXISTS ix_sites_custom_domain ON sites (custom_domain)'
        ))
