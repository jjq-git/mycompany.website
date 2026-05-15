"""店主后台路由.

MVP 登录：邮箱魔法链接，不存密码。开发环境默认把登录链接打印到控制台，
并在页面提示中展示，方便本地调试；接入邮件服务后替换发送逻辑即可。
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import (Blueprint, abort, current_app, flash, redirect, render_template,
                   request, send_from_directory, session, url_for)
from werkzeug.utils import secure_filename

import re

import yaml as _yaml

from . import datasets
from . import menu as menu_lib
from .translator import is_configured as translation_configured, translate_json
from .builder import build_site, build_template_preview
from .db import db
from .models import LoginToken, Site, Template, User
from .site_storage import (copy_seed_data, init_site_folder,
                            list_yaml_files, read_yaml, write_yaml)

bp = Blueprint('core', __name__)

ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov'}


AUTH_EXEMPT_ENDPOINTS = {
    'core.login',
    'core.magic_login',
    'core.template_preview',
    'core.preview_site',
    'core.preview_or_build',
    'core.preview',
}


def _hash_token(raw_token):
    """对魔法链接 token 做 SHA-256；数据库不保存明文 token."""
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


def _normalize_email(email):
    return (email or '').strip().lower()


def _save_uploaded_image(site_id, file_storage, prefix='image'):
    """保存上传图片到 sites/<id>/assets/uploads/ 并转换为 WebP，返回站点内绝对路径.

    返回示例: /assets/uploads/product-cover-20260509153000.webp
    """
    if not file_storage or not file_storage.filename:
        return ''

    original = secure_filename(file_storage.filename)
    suffix = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError('仅支持 JPG、PNG、GIF、WebP 图片')

    try:
        from PIL import Image, ImageSequence
    except ImportError as exc:
        raise RuntimeError('缺少 Pillow 依赖，请先安装 requirements.txt') from exc

    uploads_dir = Path(current_app.config['SITES_DIR']) / str(site_id) / 'assets' / 'uploads'
    uploads_dir.mkdir(parents=True, exist_ok=True)

    safe_prefix = secure_filename(prefix or 'image') or 'image'
    filename = f"{safe_prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}.webp"
    output_path = uploads_dir / filename

    image = Image.open(file_storage.stream)
    first_frame = next(ImageSequence.Iterator(image)).convert('RGBA')
    background = Image.new('RGBA', first_frame.size, (255, 255, 255, 0))
    background.alpha_composite(first_frame)
    background.save(output_path, 'WEBP', quality=86, method=6)
    return f'/assets/uploads/{filename}'


def _save_uploaded_media(site_id, file_storage, prefix='media'):
    """保存图片或视频；图片转 WebP，视频原样保存到 assets/uploads。"""
    if not file_storage or not file_storage.filename:
        return ''
    original = secure_filename(file_storage.filename)
    if not original:
        return ''
    suffix = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    if suffix in ALLOWED_IMAGE_EXTENSIONS:
        try:
            return _save_uploaded_image(site_id, file_storage, prefix=prefix)
        except Exception as exc:
            current_app.logger.warning('图片保存失败: %s', exc)
            return ''
    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        current_app.logger.warning('不支持的文件类型: %s', suffix)
        return ''

    uploads_dir = Path(current_app.config['SITES_DIR']) / str(site_id) / 'assets' / 'uploads'
    uploads_dir.mkdir(parents=True, exist_ok=True)
    safe_prefix = secure_filename(prefix or 'media') or 'media'
    filename = f"{safe_prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}.{suffix}"
    output_path = uploads_dir / filename
    file_storage.save(output_path)
    return f'/assets/uploads/{filename}'


def _uploaded_image_or_form(site_id, form_field, file_field=None, prefix='image'):
    """若上传了图片则返回 WebP URL，否则返回文本框中的原 URL。"""
    from flask import request
    upload = request.files.get(file_field or f'{form_field}_file')
    if upload and upload.filename:
        return _save_uploaded_image(site_id, upload, prefix=prefix)
    return request.form.get(form_field, '').strip()


def _field_looks_like_image(field):
    name = (field or '').lower()
    return any(part in name for part in ('image', 'cover', 'background', 'media', 'photo', 'logo'))


def _field_looks_like_uploadable_media(field):
    """判断字段是否适合展示上传控件。

    Banner 的媒体字段既可能是图片也可能是视频；后端当前只处理图片转 WebP，
    所以前端可展示文件入口，但保存时仍以图片字段为准。
    """
    name = (field or '').lower()
    return any(part in name for part in ('image', 'cover', 'background', 'media', 'photo', 'logo'))


def _current_user():
    """从 session 读取当前用户；无效 session 自动清理."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    user = User.query.get(user_id)
    if not user or user.status != 'active':
        session.pop('user_id', None)
        return None
    return user


@bp.before_request
def require_login():
    """保护后台页面：除登录和静态预览外都需要登录."""
    from flask import request
    if request.endpoint in AUTH_EXEMPT_ENDPOINTS:
        return None
    if request.endpoint and request.endpoint.startswith('static'):
        return None
    if not _current_user():
        return redirect(url_for('core.login', next=request.full_path if request.query_string else request.path))
    return None


@bp.context_processor
def inject_context():
    """给所有模板注入站点上下文."""
    from flask import request
    user = _current_user()
    site_id = request.args.get('site', type=int)
    if not site_id:
        if user and user.role == 'admin':
            site = Site.query.order_by(Site.id.desc()).first()
        elif user:
            site = Site.query.filter_by(owner_id=user.id).order_by(Site.id.desc()).first()
        else:
            site = None
        site_id = site.id if site else None
    else:
        site = Site.query.get(site_id)
        if site and user and user.role != 'admin' and site.owner_id != user.id:
            site = None

    ctx = {'counts': {}, 'left_menu_items': [], 'template_meta': {}, 'available_sites': []}

    if user:
        query = Site.query
        if user.role != 'admin':
            query = query.filter_by(owner_id=user.id)
        ctx['available_sites'] = query.order_by(Site.id.desc()).all()

    if site and site_id:
        ctx['counts']['products'] = len(datasets.load(site_id, 'products') or [])
        ctx['counts']['posts'] = len(datasets.load(site_id, 'posts') or [])
        ctx['counts']['features'] = len(datasets.load(site_id, 'features') or [])

        # 左栏动态菜单：从 settings.yaml 读取 menu 列表
        settings = read_yaml(site_id, 'settings.yaml') or {}
        meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
        if meta_path.exists():
            ctx['template_meta'] = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {}

        raw_menu = settings.get('menu') or ctx['template_meta'].get('default_menu', [])
        datasets_meta = ctx['template_meta'].get('datasets', [])
        normalized = menu_lib.ensure_home(
            menu_lib.normalize_for_render(
                menu_lib.upgrade_old_format(raw_menu, datasets_meta)
            )
        )
        ctx['left_menu_items'] = normalized

        # 收集所有层级中 type=list 的菜单项（供数据网格模块选择数据源）
        def _collect_list_targets(items, result=None):
            if result is None:
                result = []
            for it in (items or []):
                if it.get('type') == 'list' and it.get('target'):
                    result.append({'target': it['target'], 'label': it.get('label', it['target'])})
                if it.get('children'):
                    _collect_list_targets(it['children'], result)
            return result
        ctx['all_list_datasets'] = _collect_list_targets(normalized)

    return ctx


def _current_context():
    """取当前登录用户和站点；普通用户只能访问自己的站点，admin 可访问全部."""
    from flask import request
    user = _current_user()
    if not user:
        abort(401)
    site_id = request.args.get('site', type=int)
    if site_id:
        site = Site.query.get(site_id)
    else:
        query = Site.query
        if user.role != 'admin':
            query = query.filter_by(owner_id=user.id)
        site = query.order_by(Site.id.desc()).first()
    if not site:
        abort(404, "尚无站点，请先从模板库创建站点")
    if user.role != 'admin' and site.owner_id != user.id:
        abort(403, "无权访问该站点")
    return user, site


def _create_magic_link(email, request):
    """创建一次性魔法链接 token，返回完整登录 URL."""
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, status='active')
        db.session.add(user)
        db.session.flush()

    raw_token = secrets.token_urlsafe(32)
    token = LoginToken(
        user_id=user.id,
        email=email,
        token_hash=_hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        ip_address=request.headers.get('X-Forwarded-For', request.remote_addr or '')[:45],
    )
    db.session.add(token)
    db.session.commit()
    return url_for('core.magic_login', token=raw_token, _external=True)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """邮箱魔法链接登录入口."""
    from flask import request
    if _current_user() and request.method == 'GET':
        return redirect(request.args.get('next') or url_for('core.overview'))

    magic_link = None
    email = ''
    if request.method == 'POST':
        email = _normalize_email(request.form.get('email'))
        if not email or '@' not in email:
            flash('请输入有效邮箱地址', 'danger')
        else:
            magic_link = _create_magic_link(email, request)
            current_app.logger.info('Magic login link for %s: %s', email, magic_link)
            flash('登录链接已生成。开发环境中可直接点击下方链接；生产环境将通过邮件发送。', 'success')
    return render_template('auth/login.html', email=email, magic_link=magic_link)


@bp.route('/auth/magic/<token>')
def magic_login(token):
    """消费一次性 token 并写入 session."""
    now = datetime.now(timezone.utc)
    login_token = LoginToken.query.filter_by(token_hash=_hash_token(token)).first()
    if not login_token or login_token.used_at:
        flash('登录链接无效或已使用，请重新获取。', 'danger')
        return redirect(url_for('core.login'))
    expires_at = login_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        flash('登录链接已过期，请重新获取。', 'danger')
        return redirect(url_for('core.login'))

    user = User.query.get(login_token.user_id) or User.query.filter_by(email=login_token.email).first()
    if not user or user.status != 'active':
        flash('账号不可用，请联系管理员。', 'danger')
        return redirect(url_for('core.login'))

    login_token.used_at = now
    user.email_verified_at = user.email_verified_at or now
    user.last_login_at = now
    db.session.commit()

    session.clear()
    session['user_id'] = user.id
    flash('已登录', 'success')
    if user.role == 'admin':
        if Site.query.first():
            return redirect(url_for('core.overview'))
        else:
            flash("尚无站点，请先从模板库创建站点", "warning")
            return redirect(url_for('core.templates_gallery'))
    if Site.query.filter_by(owner_id=user.id).first():
        return redirect(url_for('core.overview'))
    return redirect(url_for('core.templates_gallery'))


@bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('已退出登录', 'success')
    return redirect(url_for('core.login'))


@bp.route('/assets/<path:filename>')
def site_asset(filename):
    """后台/预览使用的站点上传资源入口。静态导出时由 output/assets 直接承载。"""
    _, site = _current_context()
    assets_root = Path(current_app.config['SITES_DIR']) / str(site.id) / 'assets'
    return send_from_directory(assets_root, filename)


@bp.errorhandler(404)
def not_found(error):
    """捕获 404，无站点时重定向到模板库."""
    from flask import request
    desc = error.description if hasattr(error, 'description') else str(error)
    if '尚无站点' in str(desc):
        flash("尚无站点，请先从模板库创建站点", "warning")
        return redirect(url_for('core.templates_gallery'))
    return f"<h1>404 Not Found</h1><p>{desc}</p>", 404


@bp.route('/')
def index():
    return overview()


@bp.route('/overview')
def overview():
    from flask import request
    user, site = _current_context()
    products = datasets.load(site.id, 'products')
    pages = list_yaml_files(site.id, 'pages')
    counts = {'products': len(products), 'pages': len(pages)}
    if request.args.get('_fragment'):
        return render_template('dashboard/panel_overview.html',
                               user=user, site=site, counts=counts)
    return render_template('dashboard/overview.html',
                           user=user, site=site, counts=counts, active='overview')


@bp.route('/company', methods=['GET', 'POST'])
def company():
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}

    is_fragment = request.args.get('_fragment') is not None

    if request.method == 'POST':
        settings.setdefault('company', {})
        settings.setdefault('contact', {})
        for field in ('name', 'short_name', 'icp'):
            settings['company'][field] = request.form.get(f'company.{field}', '').strip()
        for field in ('phone', 'email', 'address', 'wechat'):
            settings['contact'][field] = request.form.get(f'contact.{field}', '').strip()
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        if is_fragment:
            return redirect(url_for('core.company', _fragment='1', site=site.id))
        return redirect(url_for('core.company', site=site.id))

    if is_fragment:
        return render_template('dashboard/panel_company.html',
                               user=user, site=site,
                               company=settings.get('company', {}),
                               contact=settings.get('contact', {}))
    return render_template('dashboard/company.html',
                           user=user, site=site,
                           company=settings.get('company', {}),
                           contact=settings.get('contact', {}),
                           active='company')


@bp.route('/products')
def products():
    from flask import request
    user, site = _current_context()
    products = datasets.load(site.id, 'products')
    if request.args.get('_fragment'):
        return render_template('dashboard/panel_data_list.html',
                               user=user, site=site,
                               dataset_key='products', items=products)
    return render_template('dashboard/products.html',
                           user=user, site=site, products=products, active='products')


@bp.route('/products/new', methods=['POST'])
def product_new():
    from flask import redirect, url_for
    _, site = _current_context()
    n = len(datasets.load(site.id, 'products')) + 1
    new_id = datasets.add(site.id, 'products', {
        'name': '新产品', 'slug': f'product-{n}',
        'summary': '', 'description': '', 'cover': '', 'category': '', 'specs': {},
    })
    return redirect(url_for('core.product_edit', product_id=new_id, site=site.id))


@bp.route('/products/<int:product_id>/delete', methods=['POST'])
def product_delete(product_id):
    from flask import flash, redirect, url_for
    _, site = _current_context()
    datasets.remove(site.id, 'products', product_id)
    flash('已删除')
    return redirect(url_for('core.products', site=site.id))


@bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def product_edit(product_id):
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    product = datasets.find(site.id, 'products', product_id)
    if not product:
        abort(404, f'产品不存在: id={product_id}')

    if request.method == 'POST':
        fields = {f: request.form.get(f, '').strip()
                  for f in ('name', 'slug', 'category', 'summary', 'description', 'cover')}
        fields['cover'] = _uploaded_image_or_form(site.id, 'cover', 'cover_file', 'product-cover')
        # specs: 多行 "键: 值"
        specs = {}
        for line in request.form.get('specs', '').strip().splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                if k.strip():
                    specs[k.strip()] = v.strip()
        fields['specs'] = specs
        datasets.update(site.id, 'products', product_id, fields)
        flash('已保存')
        return redirect(url_for('core.product_edit', product_id=product_id, site=site.id))

    return render_template('dashboard/product_edit.html',
                           user=user, site=site, product=product, active='products')


# ----- 功能 -----

@bp.route('/features')
def features():
    from flask import request
    user, site = _current_context()
    items = datasets.load(site.id, 'features')
    if request.args.get('_fragment'):
        return render_template('dashboard/panel_data_list.html',
                               user=user, site=site,
                               dataset_key='features', items=items)
    return render_template('dashboard/features.html',
                           user=user, site=site, items=items, active='features')


@bp.route('/features/new', methods=['POST'])
def feature_new():
    from flask import redirect, url_for
    _, site = _current_context()
    new_id = datasets.add(site.id, 'features',
                          {'icon': '', 'title': '新功能', 'desc': ''})
    return redirect(url_for('core.feature_edit', item_id=new_id, site=site.id))


@bp.route('/features/<int:item_id>/delete', methods=['POST'])
def feature_delete(item_id):
    from flask import flash, redirect, url_for
    _, site = _current_context()
    datasets.remove(site.id, 'features', item_id)
    flash('已删除')
    return redirect(url_for('core.features', site=site.id))


@bp.route('/features/<int:item_id>/edit', methods=['GET', 'POST'])
def feature_edit(item_id):
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    item = datasets.find(site.id, 'features', item_id)
    if not item:
        abort(404)
    if request.method == 'POST':
        fields = {f: request.form.get(f, '').strip() for f in ('icon', 'title', 'desc')}
        datasets.update(site.id, 'features', item_id, fields)
        flash('已保存')
        return redirect(url_for('core.feature_edit', item_id=item_id, site=site.id))
    return render_template('dashboard/feature_edit.html',
                           user=user, site=site, item=item, active='features')


# ----- 博客 -----

@bp.route('/blog')
def blog():
    from flask import request
    user, site = _current_context()
    items = datasets.load(site.id, 'posts')
    if request.args.get('_fragment'):
        return render_template('dashboard/panel_data_list.html',
                               user=user, site=site,
                               dataset_key='posts', items=items)
    return render_template('dashboard/blog.html',
                           user=user, site=site, items=items, active='blog')


@bp.route('/blog/new', methods=['POST'])
def post_new():
    from flask import redirect, url_for
    from datetime import date as _date
    _, site = _current_context()
    n = len(datasets.load(site.id, 'posts')) + 1
    new_id = datasets.add(site.id, 'posts', {
        'slug': f'post-{n}', 'title': '新文章', 'date': str(_date.today()),
        'cover': '', 'excerpt': '', 'body': '',
    })
    return redirect(url_for('core.post_edit', item_id=new_id, site=site.id))


@bp.route('/blog/<int:item_id>/delete', methods=['POST'])
def post_delete(item_id):
    from flask import flash, redirect, url_for
    _, site = _current_context()
    datasets.remove(site.id, 'posts', item_id)
    flash('已删除')
    return redirect(url_for('core.blog', site=site.id))


@bp.route('/blog/<int:item_id>/edit', methods=['GET', 'POST'])
def post_edit(item_id):
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    item = datasets.find(site.id, 'posts', item_id)
    if not item:
        abort(404)
    if request.method == 'POST':
        fields = {f: request.form.get(f, '').strip()
                  for f in ('title', 'slug', 'date', 'cover', 'excerpt', 'body')}
        fields['cover'] = _uploaded_image_or_form(site.id, 'cover', 'cover_file', 'post-cover')
        datasets.update(site.id, 'posts', item_id, fields)
        flash('已保存')
        return redirect(url_for('core.post_edit', item_id=item_id, site=site.id))
    return render_template('dashboard/post_edit.html',
                           user=user, site=site, item=item, active='blog')


@bp.route('/pages/home', methods=['GET', 'POST'])
def page_home():
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    page = read_yaml(site.id, 'pages/home.yaml') or {}

    # 检测格式: modules 数组 vs 旧固定 key
    is_modules_format = 'modules' in page

    if request.method == 'POST':
        if is_modules_format or request.form.get('_format') == 'modules':
            # modules 数组格式保存
            existing_modules = page.get('modules', [])
            page['modules'] = _parse_modules_form(request.form, existing_modules)
            page.pop('hero', None)
            for k in ('featured_section', 'features_section', 'about_brief', 'blog_section', 'subscribe_section'):
                page.pop(k, None)
        else:
            # 旧固定 key 格式保存
            page.setdefault('hero', {})
            for f in ('title', 'subtitle', 'badge', 'cta_text', 'cta_url', 'video_url', 'background_image'):
                page['hero'][f] = request.form.get(f'hero.{f}', '').strip()
            for key in ('featured_section', 'features_section', 'about_brief', 'blog_section', 'subscribe_section'):
                page.setdefault(key, {})
                page[key]['enabled'] = bool(request.form.get(f'{key}.enabled'))
                for f in ('title', 'subtitle', 'body', 'cta_text', 'cta_url'):
                    v = request.form.get(f'{key}.{f}')
                    if v is not None:
                        page[key][f] = v.strip()
                limit = request.form.get(f'{key}.limit')
                if limit:
                    try:
                        page[key]['limit'] = int(limit)
                    except ValueError:
                        pass
        write_yaml(site.id, 'pages/home.yaml', page)
        flash('已保存')
        if request.args.get('_fragment'):
            return redirect(url_for('core.page_home', _fragment='1', site=site.id))
        return redirect(url_for('core.page_home', site=site.id))

    # 准备渲染上下文
    lang, languages, default_lang = _get_panel_lang(site)
    blocks = _get_available_blocks(site.template_name)
    if is_modules_format:
        page.setdefault('modules', [])
    else:
        page.setdefault('hero', {})
        for key in ('featured_section', 'features_section', 'about_brief', 'blog_section', 'subscribe_section'):
            page.setdefault(key, {})

    return render_template('dashboard/panel_page_edit.html',
                           user=user, site=site, page=page,
                           page_key='home',
                           is_modules_format=is_modules_format,
                           blocks=blocks,
                           active='pages_home',
                           current_lang=lang,
                           languages=languages,
                           default_lang=default_lang)


@bp.route('/pages')
def pages():
    user, site = _current_context()
    files = list_yaml_files(site.id, 'pages')
    rows = []
    for f in files:
        rows.append({
            'label': f.stem,  # home, about, contact...
            'path': f'pages/{f.name}',
            'mtime': datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc),
        })
    return render_template('dashboard/pages.html',
                           user=user, site=site, pages=rows, active='pages')


@bp.route('/account')
def account():
    from flask import request
    user, site = _current_context()
    site_count = Site.query.filter_by(owner_id=user.id).count() if user else 0
    if request.args.get('_fragment'):
        return render_template('dashboard/panel_account.html',
                               user=user, site=site, site_count=site_count)
    return render_template('dashboard/account.html',
                           user=user, site=site, site_count=site_count, active='account')


@bp.route('/sites/delete', methods=['POST'])
def site_delete():
    """删除当前站点：清除数据库记录 + 站点文件夹 + output 文件."""
    from flask import flash, jsonify, redirect, request, url_for
    from .db import db

    import shutil as _shutil

    user, site = _current_context()
    site_id = site.id
    site_name = site.name

    # 删除站点文件夹
    site_folder = Path(current_app.config['SITES_DIR']) / str(site_id)
    if site_folder.exists():
        try:
            _shutil.rmtree(site_folder)
        except OSError as exc:
            current_app.logger.warning('删除站点文件夹 %s 失败: %s', site_folder, exc)

    # 删除 output
    output_dir = Path(current_app.config['OUTPUT_DIR']) / str(site_id)
    if output_dir.exists():
        try:
            _shutil.rmtree(output_dir)
        except OSError as exc:
            current_app.logger.warning('删除 output 目录 %s 失败: %s', output_dir, exc)

    # 删除数据库记录
    db.session.delete(site)
    db.session.commit()

    flash(f'站点 "{site_name}" 已删除', 'success')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.args.get('_fragment'):
        return jsonify({'ok': True, 'redirect': url_for('core.overview')})
    return redirect(url_for('core.overview'))
def _save_link_list(site_id, settings_key):
    """收集表单 label[] 和 url[], 写回 settings.yaml[settings_key]."""
    from flask import request
    settings = read_yaml(site_id, 'settings.yaml') or {}
    labels = request.form.getlist('label[]')
    urls = request.form.getlist('url[]')
    items = []
    for label, url in zip(labels, urls):
        label, url = label.strip(), url.strip()
        if label or url:
            items.append({'label': label, 'url': url})
    settings[settings_key] = items
    write_yaml(site_id, 'settings.yaml', settings)


@bp.route('/settings/header', methods=['GET', 'POST'])
def header_edit():
    """网站头部变体选择 + 语言切换按钮配置."""
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    is_fragment = request.args.get('_fragment') is not None

    # Header 变体列表（模板 meta 中定义）
    tpl_meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    tpl_meta = _yaml.safe_load(tpl_meta_path.read_text(encoding='utf-8')) if tpl_meta_path.exists() else {}
    header_variants = tpl_meta.get('header_variants', [
        {'key': 'logo_left_menu_right', 'label': 'Logo 左 + 菜单右', 'description': '经典布局，适合大多数企业网站'},
        {'key': 'logo_center_menu_below', 'label': 'Logo 居中 + 菜单下方', 'description': '对称布局，适合品牌展示'},
        {'key': 'minimal_hamburger', 'label': '极简（汉堡菜单）', 'description': 'Logo 左 + 汉堡菜单，移动端友好'},
        {'key': 'top_bar_social', 'label': '顶栏 + 社交图标', 'description': '带电话 + 社交图标的双层顶栏'},
    ])

    # 语言切换按钮样式列表
    lang_switcher_styles = [
        {'key': 'inline_row', 'label': '水平行内（中文 | EN | JP）'},
        {'key': 'vertical_dropdown', 'label': '垂直下拉'},
        {'key': 'flag_icon', 'label': '旗帜 + 简称'},
    ]

    if request.method == 'POST':
        header = settings.setdefault('header', {})
        header['variant'] = request.form.get('header_variant', header_variants[0]['key'])
        header['language_switcher'] = {
            'enabled': bool(request.form.get('lang_switcher_enabled')),
            'style': request.form.get('lang_switcher_style', 'vertical_dropdown'),
        }
        # 社交链接（整合到头部面板）
        social = settings.setdefault('social', {})
        social['enabled'] = bool(request.form.get('social_enabled'))
        for platform in ('github', 'twitter', 'facebook', 'linkedin', 'youtube'):
            social[platform] = request.form.get(f'social_{platform}', '').strip()
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        if is_fragment:
            return redirect(url_for('core.header_edit', _fragment='1', site=site.id))
        return redirect(url_for('core.header_edit', site=site.id))

    current_header = settings.get('header') or {}
    if is_fragment:
        return render_template('dashboard/panel_header.html',
                               user=user, site=site,
                               header_variants=header_variants,
                               lang_switcher_styles=lang_switcher_styles,
                               current_header=current_header,
                               settings=settings)
    return render_template('dashboard/header_edit.html',
                           user=user, site=site,
                           header_variants=header_variants,
                           lang_switcher_styles=lang_switcher_styles,
                           current_header=current_header,
                           active='header')


@bp.route('/settings/footer_variant', methods=['GET', 'POST'])
def footer_variant_edit():
    """网站底部变体选择."""
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    is_fragment = request.args.get('_fragment') is not None

    # Footer 变体列表
    tpl_meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    tpl_meta = _yaml.safe_load(tpl_meta_path.read_text(encoding='utf-8')) if tpl_meta_path.exists() else {}
    footer_variants = tpl_meta.get('footer_variants', [
        {'key': 'four_columns', 'label': '四栏链接', 'description': '产品、快速链接、联系方式、关于我们四栏布局'},
        {'key': 'three_columns_subscribe', 'label': '三栏 + 订阅', 'description': '带邮件订阅框的三栏布局'},
        {'key': 'minimal_single_line', 'label': '极简单行', 'description': '仅显示版权信息和备案号'},
        {'key': 'map_contact', 'label': '地图 + 联系方式', 'description': '带地图和详细联系方式的底部'},
    ])

    if request.method == 'POST':
        footer = settings.setdefault('footer', {})
        footer['variant'] = request.form.get('footer_variant', 'columns')
        footer['copyright'] = request.form.get('copyright', '').strip()
        footer['icp'] = request.form.get('icp', '').strip()

        # 解析底部栏目
        col_count = 0
        try:
            col_count = int(request.form.get('footer_column_count', '0'))
        except (ValueError, TypeError):
            pass
        columns = []
        for ci in range(col_count):
            col = {
                'type': request.form.get(f'footer_col_{ci}_type', 'menu').strip(),
                'title': request.form.get(f'footer_col_{ci}_title', '').strip(),
            }
            link_count = 0
            try:
                link_count = int(request.form.get(f'footer_col_{ci}_link_count', '0'))
            except (ValueError, TypeError):
                pass
            links = []
            for li in range(link_count):
                label = request.form.get(f'footer_col_{ci}_link_{li}_label', '').strip()
                url = request.form.get(f'footer_col_{ci}_link_{li}_url', '').strip()
                if label or url:
                    links.append({'label': label, 'url': url})
            col['links'] = links
            columns.append(col)
        if columns:
            footer['columns'] = columns
        else:
            footer.pop('columns', None)

        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        if is_fragment:
            return redirect(url_for('core.footer_variant_edit', _fragment='1', site=site.id))
        return redirect(url_for('core.footer_variant_edit', site=site.id))

    current_footer = settings.get('footer') or {}

    if is_fragment:
        return render_template('dashboard/panel_footer_variant.html',
                               user=user, site=site,
                               footer_variants=footer_variants,
                               current_footer=current_footer)
    return render_template('dashboard/footer_variant.html',
                           user=user, site=site,
                           footer_variants=footer_variants,
                           current_footer=current_footer,
                           active='footer_variant')


@bp.route('/settings/menu', methods=['GET', 'POST'])
def menu_edit():
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    is_fragment = request.args.get('_fragment') is not None

    # 语言特定菜单: 默认语言用 menu 键，其他用 menu_<lang>
    lang, languages, default_lang = _get_panel_lang(site)
    menu_key = 'menu' if lang == default_lang else f'menu_{lang}'

    if request.method == 'POST':
        menu_json = request.form.get('menu_json', '').strip()
        if menu_json:
            try:
                raw_items = _yaml.safe_load(menu_json) or []
            except _yaml.YAMLError:
                raw_items = []
            items = menu_lib.clean_for_storage(raw_items)
        else:
            labels = request.form.getlist('label[]')
            types = request.form.getlist('type[]')
            targets_list = request.form.getlist('target_list[]')
            urls_link = request.form.getlist('url_link[]')
            dropdown_styles = request.form.getlist('dropdown_style[]')
            children_values = request.form.getlist('children_json[]')
            raw_items = [{'label': '首页', 'type': 'home'}]
            for i, label in enumerate(labels):
                label = label.strip()
                if not label:
                    continue
                t = types[i] if i < len(types) else 'link'
                raw = {'label': label, 'type': t}
                if t in ('list', 'page'):
                    target = targets_list[i].strip() if i < len(targets_list) else ''
                    if target:
                        raw['target'] = target
                elif t == 'link':
                    url = urls_link[i].strip() if i < len(urls_link) else ''
                    if url:
                        raw['url'] = url
                dropdown_style = dropdown_styles[i].strip() if i < len(dropdown_styles) else ''
                if dropdown_style:
                    raw['dropdown_style'] = dropdown_style
                children_raw = children_values[i].strip() if i < len(children_values) else ''
                if children_raw:
                    try:
                        children = _yaml.safe_load(children_raw) or []
                    except _yaml.YAMLError:
                        children = []
                    if isinstance(children, list):
                        raw['children'] = children
                raw_items.append(raw)
            items = menu_lib.clean_for_storage(raw_items)
        settings[menu_key] = items
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存，首页已保持为固定入口')
        if is_fragment:
            return redirect(url_for('core.menu_edit', _fragment='1', site=site.id, lang=lang))
        return redirect(url_for('core.menu_edit', site=site.id, lang=lang))

    # GET: 升级旧格式
    meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
    # 语言特定菜单优先，回退到默认菜单
    raw_menu = settings.get(menu_key) or settings.get('menu') or meta.get('default_menu', [])
    items = menu_lib.ensure_home(
        menu_lib.upgrade_old_format(raw_menu, meta.get('datasets', []))
    )

    if is_fragment:
        return render_template('dashboard/panel_menu.html',
                               user=user, site=site, items=items,
                               current_lang=lang, languages=languages, default_lang=default_lang)
    return render_template('dashboard/menu.html',
                           user=user, site=site, items=items, active='menu',
                           current_lang=lang, languages=languages, default_lang=default_lang)


@bp.route('/settings/footer', methods=['GET', 'POST'])
def footer_edit():
    """旧页脚链接页面 —— 已迁移至 footer_variant_edit，自动转换旧数据格式"""
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}

    # 迁移旧的 footer_links 数据到新 footer.columns 格式
    old_links = settings.pop('footer_links', None)
    if old_links:
        footer = settings.setdefault('footer', {})
        existing_cols = footer.get('columns', [])
        if not existing_cols:
            footer['variant'] = 'columns'
            footer['columns'] = [{
                'type': 'menu',
                'title': '快速链接',
                'links': old_links
            }]
            write_yaml(site.id, 'settings.yaml', settings)
            flash('页脚链接数据已自动迁移到新版格式')

    return redirect(url_for('core.footer_variant_edit', site=site.id))


@bp.route('/settings/social', methods=['GET', 'POST'])
def social_edit():
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    is_fragment = request.args.get('_fragment') is not None
    if request.method == 'POST':
        social = settings.setdefault('social', {})
        for platform in ('github', 'twitter', 'facebook', 'linkedin', 'youtube'):
            social[platform] = request.form.get(platform, '').strip()
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        if is_fragment:
            return redirect(url_for('core.social_edit', _fragment='1', site=site.id))
        return redirect(url_for('core.social_edit', site=site.id))
    social = settings.get('social') or {}
    if is_fragment:
        return render_template('dashboard/panel_social.html',
                               user=user, site=site, social=social)
    return render_template('dashboard/social.html',
                           user=user, site=site, social=social, active='social')


@bp.route('/settings/theme', methods=['GET', 'POST'])
def theme_edit():
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    is_fragment = request.args.get('_fragment') is not None
    tpl_meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    tpl_meta = _yaml.safe_load(tpl_meta_path.read_text(encoding='utf-8')) if tpl_meta_path.exists() else {}
    default_theme = tpl_meta.get('default_theme') or {}

    if request.method == 'POST':
        theme = settings.setdefault('theme', {})
        for key in ('accent', 'bg', 'surface', 'text', 'text_muted', 'border'):
            v = request.form.get(key, '').strip()
            if v:
                theme[key] = v
            else:
                theme.pop(key, None)
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        if is_fragment:
            return redirect(url_for('core.theme_edit', _fragment='1', site=site.id))
        return redirect(url_for('core.theme_edit', site=site.id))

    theme = settings.get('theme') or {}
    if is_fragment:
        return render_template('dashboard/panel_theme.html',
                               user=user, site=site, theme=theme, default_theme=default_theme)
    return render_template('dashboard/theme.html',
                           user=user, site=site, theme=theme, default_theme=default_theme, active='theme')


SLUG_PATTERN = re.compile(r'^[a-z0-9][a-z0-9-]{1,28}[a-z0-9]$')


@bp.route('/templates')
def templates_gallery():
    from flask import request
    user = _current_user()
    query = Site.query
    if user and user.role != 'admin':
        query = query.filter_by(owner_id=user.id)
    site = query.order_by(Site.id.desc()).first()
    templates = Template.query.order_by(Template.name).all()
    if request.args.get('_fragment'):
        return render_template('dashboard/panel_templates.html',
                               user=user, site=site, templates=templates)
    return render_template('dashboard/templates_gallery.html',
                           user=user, site=site, templates=templates, active='templates')


@bp.route('/templates/<template_name>/preview/')
@bp.route('/templates/<template_name>/preview/<path:filepath>')
def template_preview(template_name, filepath='index.html'):
    if not Template.query.filter_by(name=template_name).first():
        abort(404)
    out = build_template_preview(
        template_name,
        base_url=f'/templates/{template_name}/preview',
    )
    full = out / filepath
    if full.is_dir():
        full = full / 'index.html'
        filepath = f'{filepath.rstrip("/")}/index.html'
    return send_from_directory(out, filepath)


@bp.route('/sites/new', methods=['GET', 'POST'])
def site_new():
    from flask import flash, redirect, request, url_for
    from .models import SLUG_RESERVED
    template_name = request.args.get('template')
    template = Template.query.filter_by(name=template_name).first() if template_name else None
    templates = Template.query.order_by(Template.name).all()

    user = _current_user()
    if not user:
        return redirect(url_for('core.login'))

    is_fragment = request.args.get('_fragment') is not None

    form = {'name': '', 'slug': '', 'template_name': template.name if template else ''}
    error = None

    if request.method == 'POST':
        form['name'] = request.form.get('name', '').strip()
        form['slug'] = request.form.get('slug', '').strip().lower()
        form['template_name'] = request.form.get('template_name', '').strip()

        # 解析模板：未选时使用第一个可用模板
        selected_template = Template.query.filter_by(name=form['template_name']).first()
        if not selected_template:
            selected_template = Template.query.order_by(Template.name).first()
        if not selected_template:
            error = '暂无可用模板，请联系管理员'
        elif not form['name']:
            error = '请填写站点名'
        elif not SLUG_PATTERN.match(form['slug']):
            error = 'Slug 不合法（要求 3–30 字符，[a-z 0-9 -]，不以 - 开头/结尾）'
        elif form['slug'] in SLUG_RESERVED:
            error = f'Slug "{form["slug"]}" 是保留字'
        elif Site.query.filter_by(slug=form['slug']).first():
            error = f'Slug "{form["slug"]}" 已被占用'
        else:
            from .db import db
            site = Site(
                owner_id=user.id, name=form['name'], slug=form['slug'],
                folder_path='', template_name=selected_template.name,
                template_version=selected_template.current_version, cdn_provider='aliyun',
            )
            db.session.add(site)
            db.session.flush()
            site.folder_path = f'sites/{site.id}'
            db.session.commit()
            init_site_folder(site.id)
            copy_seed_data(site.id, selected_template.name)
            flash(f'已创建站点 #{site.id} ({form["slug"]})')
            if is_fragment:
                from flask import jsonify
                return jsonify({'ok': True, 'redirect': url_for('core.overview', site=site.id)})
            return redirect(url_for('core.overview', site=site.id))

        # POST 验证失败 -> fragment 模式返回 JSON，普通模式重渲染页面
        if is_fragment:
            from flask import jsonify
            return jsonify({'ok': False, 'error': error})

    current_site = Site.query.filter_by(owner_id=user.id).order_by(Site.id.desc()).first()
    if is_fragment:
        return render_template('dashboard/panel_site_new.html',
                               user=user,
                               site=current_site,
                               template=template, templates=templates, form=form, error=error,
                               active='templates')
    return render_template('dashboard/site_new.html',
                           user=user,
                           site=current_site,
                           template=template, templates=templates, form=form, error=error,
                           active='templates')


@bp.route('/build', methods=['GET', 'POST'])
def build():
    """触发构建当前站点, 跳到预览首页."""
    from flask import jsonify, request
    _, site = _current_context()
    try:
        build_site(site.id, base_url=f'/preview/{site.id}')
    except Exception as exc:
        current_app.logger.exception('站点 %s 构建失败', site.id)
        if request.method == 'POST' or request.args.get('_fragment'):
            return jsonify({'ok': False, 'error': str(exc)}), 500
        abort(500, f'构建失败: {exc}')

    if request.method == 'POST' or request.args.get('_fragment'):
        return jsonify({'ok': True, 'preview_url': f'/preview_site/{site.id}'})

    from flask import redirect, url_for
    return redirect(url_for('core.preview_site', site_id=site.id))


@bp.route('/export.zip')
def export_zip():
    """导出当前站点的静态文件 ZIP."""
    from io import BytesIO
    from zipfile import ZIP_DEFLATED, ZipFile

    from flask import send_file

    _, site = _current_context()
    output_root = build_site(site.id, base_url='')

    buffer = BytesIO()
    with ZipFile(buffer, 'w', ZIP_DEFLATED) as zf:
        for path in output_root.rglob('*'):
            if path.is_file():
                zf.write(path, path.relative_to(output_root).as_posix())
    buffer.seek(0)

    filename = f'{site.slug or "site"}-static.zip'
    return send_file(
        buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=filename,
    )


def _default_lang_code(site):
    """取模板默认语言."""
    tpl_meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    if tpl_meta_path.exists():
        tpl_meta = _yaml.safe_load(tpl_meta_path.read_text(encoding='utf-8')) or {}
        languages = tpl_meta.get('languages', [])
        if languages:
            return languages[0].get('code', 'zh-CN')
    return 'zh-CN'


@bp.route('/preview_site/<int:site_id>')
def preview_site(site_id):
    """确保已构建，重定向到默认语言首页."""
    from flask import redirect, request, url_for
    site = Site.query.get_or_404(site_id)
    out = Path(current_app.config['OUTPUT_DIR']) / str(site_id)
    lang_code = _default_lang_code(site)
    lang_index = out / lang_code / 'index.html'
    if request.args.get('_') or not lang_index.exists():
        build_site(site_id, base_url=f'/preview/{site_id}')

    if (out / lang_code / 'index.html').exists():
        return redirect(url_for('core.preview', site_id=site_id, filepath=f'{lang_code}/index.html'))
    return redirect(url_for('core.preview', site_id=site_id))


@bp.route('/preview_or_build/<int:site_id>')
def preview_or_build(site_id):
    """确保已构建，直接返回默认语言的首页."""
    site = Site.query.get_or_404(site_id)
    out = Path(current_app.config['OUTPUT_DIR']) / str(site_id)
    lang_code = _default_lang_code(site)
    lang_index = out / lang_code / 'index.html'
    if not lang_index.exists():
        build_site(site_id, base_url=f'/preview/{site_id}')

    # 查找默认语言子目录下的 index.html，跳过语言选择页
    lang_index = out / lang_code / 'index.html'
    if lang_index.exists():
        return send_from_directory(out / lang_code, 'index.html')

    # 回退：返回根目录的 index.html（可能是单语言站点）
    return send_from_directory(out, 'index.html')


@bp.route('/preview/<int:site_id>/')
@bp.route('/preview/<int:site_id>/<path:filepath>')
def preview(site_id, filepath='index.html'):
    """预览 output/<site_id>/ 下的静态文件，自动构建."""
    site = Site.query.get_or_404(site_id)
    out = Path(current_app.config['OUTPUT_DIR']) / str(site_id)
    if filepath == 'index.html':
        lang_code = _default_lang_code(site)
        lang_index = out / lang_code / 'index.html'
        if not lang_index.exists():
            try:
                build_site(site_id, base_url=f'/preview/{site_id}')
            except Exception:
                pass
        if lang_index.exists():
            return send_from_directory(out, f'{lang_code}/index.html')

    # 先解析出最终目标文件，再判断是否需要重建
    full = out / filepath
    if full.is_dir():
        full = full / 'index.html'
        filepath = f'{filepath.rstrip("/")}/index.html'
    if not full.exists():
        try:
            build_site(site_id, base_url=f'/preview/{site_id}')
        except Exception:
            pass
    if not out.exists():
        out.mkdir(parents=True, exist_ok=True)
    if not full.exists():
        # 尝试默认语言子目录
        for sub in out.iterdir():
            if sub.is_dir() and (sub / 'index.html').exists():
                return send_from_directory(out, f'{sub.name}/index.html')
        abort(404, '未生成页面，请检查模板数据')
    return send_from_directory(out, filepath)


def _get_panel_lang(site):
    """从请求参数获取面板当前编辑语言, 默认返回模板的默认语言."""
    from flask import request
    meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    languages = []
    default_lang = 'zh-CN'
    if meta_path.exists():
        meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {}
        languages = meta.get('languages', [])
        default_lang = meta.get('default_language', languages[0]['code'] if languages else 'zh-CN')

    lang = request.args.get('lang', '').strip()
    valid_codes = {l['code'] for l in languages}
    if lang and lang in valid_codes:
        return lang, languages, default_lang
    return default_lang, languages, default_lang


def _render(template_name, **kwargs):
    """渲染模板，支持 ?_fragment=1 返回右侧面板片段."""
    from flask import request
    if request.args.get('_fragment'):
        return render_template(template_name, **kwargs)
    return render_template(template_name, **kwargs)


@bp.route('/api/translate', methods=['POST'])
def api_translate():
    """AI 翻译端点 — 接受 JSON 文本字典，返回翻译后的字典."""
    data = request.get_json(silent=True) or {}
    texts = data.get('texts', {})
    source_lang = data.get('source_lang', 'zh-CN')
    target_lang = data.get('target_lang', 'en')

    if not texts or not isinstance(texts, dict):
        return {'error': '请提供 texts 字典'}, 400
    if len(texts) > 50:
        return {'error': '单次最多翻译 50 个字段'}, 400

    try:
        translated = translate_json(texts, source_lang, target_lang)
        return {'ok': True, 'translated': translated}
    except ValueError as e:
        return {'error': str(e)}, 400
    except RuntimeError as e:
        return {'error': str(e)}, 502
    except Exception as e:
        current_app.logger.error('翻译失败: %s', e)
        return {'error': '翻译失败，请稍后重试'}, 500


@bp.route('/_dataset/<path:dataset_key>')
def dataset_panel(dataset_key):
    """通用数据集管理面板 — 支持 ?lang= 参数编辑不同语言版本."""
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = lang if lang != default_lang else None
    items = datasets.load(site.id, dataset_key, lang=storage_lang)
    return _render('dashboard/panel_data_list.html',
                   user=user, site=site,
                   dataset_key=dataset_key, items=items,
                   edit_prefix=f'_dataset/{dataset_key}',
                   current_lang=lang, languages=languages, default_lang=default_lang,
                   active=dataset_key)

@bp.route('/_dataset/<path:dataset_key>/new', methods=['POST'])
def dataset_new(dataset_key):
    """通用数据集新建条目 — 支持 ?lang= 参数保存到对应语言."""
    from flask import redirect, url_for
    _, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = lang if lang != default_lang else None
    n = len(datasets.load(site.id, dataset_key, lang=storage_lang)) + 1
    new_id = datasets.add(site.id, dataset_key, {
        'title': f'新条目 {n}', 'slug': f'item-{n}',
    }, lang=storage_lang)
    return redirect(url_for('core.dataset_panel', dataset_key=dataset_key, _fragment='1', site=site.id, lang=lang))

@bp.route('/_dataset/<path:dataset_key>/<int:item_id>/edit', methods=['GET', 'POST'])
def dataset_edit(dataset_key, item_id):
    """通用数据集编辑 — 支持 ?lang= 参数编辑不同语言版本."""
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = lang if lang != default_lang else None

    item = datasets.find(site.id, dataset_key, item_id, lang=storage_lang)
    if not item:
        abort(404, f'数据不存在: {dataset_key}#{item_id}')

    if request.method == 'POST':
        fields = {}
        for key in request.form:
            # 跳过模块配置字段 (module_N_*)
            if key.startswith('module_') or key == 'module_count':
                continue
            val = request.form.get(key, '').strip()
            if val:
                fields[key] = val
        # slug 唯一性校验
        new_slug = fields.get('slug', '').strip() or None
        if new_slug:
            all_items = datasets.load(site.id, dataset_key, lang=storage_lang)
            dup = next((it for it in all_items
                        if it.get('slug') == new_slug and it.get('id') != item_id), None)
            if dup:
                flash(f'Slug "{new_slug}" 已被 #{dup["id"]} 使用，请换一个', 'error')
                return redirect(url_for('core.dataset_edit', dataset_key=dataset_key,
                                        item_id=item_id, _fragment='1', site=site.id, lang=lang))
        # tags: 逗号/空格分隔的字符串 → 列表
        if 'tags' in fields and fields['tags']:
            raw_tags = fields['tags']
            tags_list = [t.strip() for t in raw_tags.replace(',', ' ').split() if t.strip()]
            fields['tags'] = tags_list
        # 处理图片上传
        for field_name in ('cover', 'image', 'photo', 'logo'):
            upload = request.files.get(field_name)
            if upload and upload.filename:
                try:
                    fields[field_name] = _save_uploaded_image(site.id, upload, prefix=f'{dataset_key}-{field_name}')
                except Exception as exc:
                    current_app.logger.warning('数据集图片上传失败 %s: %s', field_name, exc)
        # 保存模块配置到数据项 (item) 中
        module_count_str = request.form.get('module_count')
        if module_count_str and module_count_str.isdigit():
            try:
                existing_modules = item.get('modules', [])
                modules = _parse_modules_form(request.form, existing_modules)
                # 保留 item_data 模块用于排序，但清除敏感数据字段
                for m in modules:
                    if m.get('type') == 'item_data':
                        m['data'] = {}  # 清空数据（已在 fields 中保存）
                fields['modules'] = modules
            except Exception as exc:
                current_app.logger.warning('数据集编辑保存模块配置失败: %s', exc)
        else:
            fields['modules'] = []

        datasets.update(site.id, dataset_key, item_id, fields, lang=storage_lang)
        flash('已保存')
        return redirect(url_for('core.dataset_panel', dataset_key=dataset_key, _fragment='1', site=site.id, lang=lang))

    blocks = _get_available_blocks(site.template_name)
    # 中间预览 URL
    slug = item.get('slug', '')
    settings = read_yaml(site.id, 'settings.yaml') or {}
    menu_items = settings.get('menu') or []
    is_list_page = any(
        mi.get('type') == 'list' and mi.get('target') == dataset_key
        for mi in menu_items
    )
    return _render('dashboard/panel_data_list.html',
                   user=user, site=site,
                   dataset_key=dataset_key, items=[item],
                   edit_prefix=f'_dataset/{dataset_key}',
                   edit_item=item, edit_item_id=item_id,
                   current_lang=lang, languages=languages, default_lang=default_lang,
                   active=dataset_key,
                   blocks=blocks,
                   is_list_page=is_list_page,
                   page_key=dataset_key,
                   preview_slug=slug)

@bp.route('/_dataset/<path:dataset_key>/<int:item_id>/delete', methods=['POST'])
def dataset_delete(dataset_key, item_id):
    """通用数据集删除 — 支持 ?lang= 参数删除指定语言版本."""
    from flask import flash, redirect, url_for
    _, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = lang if lang != default_lang else None
    datasets.remove(site.id, dataset_key, item_id, lang=storage_lang)
    flash('已删除')
    return redirect(url_for('core.dataset_panel', dataset_key=dataset_key, _fragment='1', site=site.id, lang=lang))


@bp.route('/_panel/<path:page_key>', methods=['GET', 'POST'])
def page_panel(page_key):
    """动态菜单项面板路由：根据 page_key 分发到对应数据集列表或单页编辑.

    模块库是公用的——所有菜单页面都可以从同一个 blocks/ 中选择模块，
    只是每个页面填不同的数据，保存在 pages/<page_key>.yaml 的 modules 数组中。

    支持语言参数 ?lang=en 来编辑特定语言版本的页面内容。
    """
    from flask import flash, redirect, request, url_for
    user, site = _current_context()

    lang, languages, default_lang = _get_panel_lang(site)
    # 非默认语言时使用 lang 参数进行读写；默认语言读写根目录
    storage_lang = lang if lang != default_lang else None

    # POST：保存模块配置
    if request.method == 'POST':
        page = read_yaml(site.id, f'pages/{page_key}.yaml', lang=storage_lang) or {}
        existing_modules = page.get('modules', [])
        page['modules'] = _parse_modules_form(request.form, existing_modules)
        for k in list(page.keys()):
            if k not in ('modules',):
                page.pop(k, None)
        write_yaml(site.id, f'pages/{page_key}.yaml', page, lang=storage_lang)
        flash('已保存')
        return redirect(url_for('core.page_panel', page_key=page_key, _fragment='1', site=site.id, lang=lang))

    # 判断 page_key 是否为 list 类型菜单
    settings = read_yaml(site.id, 'settings.yaml') or {}
    menu_items = settings.get('menu') or []
    if not menu_items:
        meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
        if meta_path.exists():
            template_meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {}
            menu_items = template_meta.get('default_menu', [])

    def _find_list_in_menu(items, target_key):
        for item in (items or []):
            if item.get('type') == 'list' and item.get('target') == target_key:
                return True
            if item.get('children'):
                if _find_list_in_menu(item['children'], target_key):
                    return True
        return False

    is_list_page = _find_list_in_menu(menu_items, page_key)

    page = read_yaml(site.id, f'pages/{page_key}.yaml', lang=storage_lang)
    if page:
        blocks = _get_available_blocks(site.template_name)
        is_modules_format = 'modules' in page
        return _render('dashboard/panel_page_edit.html',
                       user=user, site=site,
                       page_key=page_key, page=page,
                       blocks=blocks, is_modules_format=is_modules_format,
                       is_list_page=is_list_page,
                       current_lang=lang, languages=languages, default_lang=default_lang,
                       active=page_key)

    # 没有匹配任何已有内容：自动初始化
    new_page = {'modules': []}
    write_yaml(site.id, f'pages/{page_key}.yaml', new_page, lang=storage_lang)
    blocks = _get_available_blocks(site.template_name)
    return _render('dashboard/panel_page_edit.html',
                   user=user, site=site,
                   page_key=page_key, page=new_page,
                   blocks=blocks, is_modules_format=True,
                   is_list_page=is_list_page,
                   current_lang=lang, languages=languages, default_lang=default_lang,
                   active=page_key)


def _get_available_blocks(template_name):
    """获取模板的可用模块列表."""
    from .template_loader import scan_blocks
    try:
        return scan_blocks(template_name)
    except Exception:
        return []


def _parse_modules_form(form, existing_modules=None):
    """从 POST 表单解析 modules 数组（含 responsive 字段）.

    如果提供 existing_modules，表单未涉及的字段（如 items、features 等嵌套数组）
    会从已有数据中保留，防止编辑器保存时丢失表单不表达的数据。
    """
    # 构建已有模块查找索引：(type, order) → existing_data
    # 注意：旧格式数据中 hero_banner 的 data 可能是直接列表（slides），
    # 需要包装为 dict 才能安全使用 .items()
    existing_by_key = {}
    if existing_modules:
        for em in existing_modules:
            if isinstance(em, dict) and em.get('type'):
                key = (em.get('type', ''), em.get('order', 0))
                raw_data = em.get('data', {})
                if isinstance(raw_data, dict):
                    existing_by_key[key] = raw_data
                elif isinstance(raw_data, list):
                    existing_by_key[key] = {'slides': raw_data}
                else:
                    existing_by_key[key] = {}

    def _parse_value(value):
        value = (value or '').strip()
        if not value:
            return ''
        try:
            parsed = _yaml.safe_load(value)
        except _yaml.YAMLError:
            return value
        return value if parsed is None else parsed

    count = 0
    try:
        count = int(form.get('module_count', '0'))
    except (ValueError, TypeError):
        pass

    modules = []
    for i in range(count):
        idx = f'module_{i}'
        m_type = form.get(f'{idx}_type', '').strip()
        if not m_type:
            continue
        variant = form.get(f'{idx}_variant', '').strip() or 'default'
        order_str = form.get(f'{idx}_order', str(i + 1))
        try:
            order = int(order_str)
        except (ValueError, TypeError):
            order = i + 1

        # 第一步：从表单构建 data，同时记录表单涉及的字段集合
        data = {}
        form_fields_for_module = set()  # 记录表单实际涉及的字段名（不含子字段后缀）
        for key in form:
            prefix = f'{idx}_data_'
            if key.startswith(prefix) and '_resp_' not in key:
                field = key[len(prefix):]
                if not any(k in key for k in ('_resp_tablet_', '_resp_mobile_', '_resp_columns', '_resp_max_items')):
                    # 去掉子字段后缀（如 images_0_url → images）
                    base_field = field.split('_')[0] if '_' in field else field
                    form_fields_for_module.add(base_field)
                    form_fields_for_module.add(field)
                    data[field] = _parse_value(form.get(key, ''))

        from flask import request
        if m_type == 'hero_banner':
            slide_count = 0
            try:
                slide_count = int(form.get(f'{idx}_slide_count', '0'))
            except (ValueError, TypeError):
                slide_count = 0

            slides = []
            for slide_i in range(slide_count):
                slide_prefix = f'{idx}_slide_{slide_i}_'
                slide = {}
                for field in (
                    'type', 'media', 'title', 'subtitle', 'badge',
                    'primaryBtn', 'primaryBtnLink', 'primaryBtnLinkTarget',
                    'secondaryBtn', 'secondaryBtnLink',
                    'cta_text', 'cta_url', 'video_url', 'background_image'
                ):
                    value = form.get(f'{slide_prefix}{field}', '').strip()
                    if value:
                        slide[field] = _parse_value(value)

                upload = request.files.get(f'{slide_prefix}file')
                if upload and upload.filename:
                    media_url = _save_uploaded_media(
                        _current_context()[1].id,
                        upload,
                        prefix=f'{m_type}-slide-{slide_i + 1}',
                    )
                    suffix = upload.filename.rsplit('.', 1)[-1].lower() if '.' in upload.filename else ''
                    slide['type'] = 'video' if suffix in ALLOWED_VIDEO_EXTENSIONS else 'image'
                    slide['media'] = media_url

                if slide.get('media') or slide.get('title') or slide.get('subtitle'):
                    slides.append(slide)

            if slides:
                data['slides'] = slides
            else:
                slides_value = data.get('slides')
                if isinstance(slides_value, list):
                    data['slides'] = slides_value
                elif isinstance(slides_value, str) and slides_value.strip():
                    parsed_slides = _parse_value(slides_value)
                    if isinstance(parsed_slides, list):
                        data['slides'] = parsed_slides

            uploaded_slides = []
            for upload in request.files.getlist(f'{idx}_data_slides_files'):
                if upload and upload.filename:
                    media_url = _save_uploaded_media(
                        _current_context()[1].id,
                        upload,
                        prefix=f'{m_type}-slide',
                    )
                    suffix = upload.filename.rsplit('.', 1)[-1].lower() if '.' in upload.filename else ''
                    uploaded_slides.append({
                        'type': 'video' if suffix in ALLOWED_VIDEO_EXTENSIONS else 'image',
                        'media': media_url,
                        'title': data.get('title', ''),
                        'subtitle': data.get('subtitle', ''),
                        'primaryBtn': data.get('primaryBtn') or data.get('cta_text', ''),
                        'primaryBtnLink': data.get('primaryBtnLink') or data.get('cta_url', ''),
                        'cta_text': data.get('cta_text', ''),
                        'cta_url': data.get('cta_url', ''),
                        'badge': data.get('badge', ''),
                    })
            if uploaded_slides:
                existing = data.get('slides') if isinstance(data.get('slides'), list) else []
                data['slides'] = existing + uploaded_slides

        if m_type == 'item_detail':
            images_count = 0
            try:
                images_count = int(form.get(f'{idx}_data_images_count', '0'))
            except (ValueError, TypeError):
                pass
            images = []
            for ii in range(images_count):
                url = form.get(f'{idx}_data_images_{ii}_url', '').strip()
                upload = request.files.get(f'{idx}_data_images_{ii}_url_file')
                if upload and upload.filename:
                    try:
                        url = _save_uploaded_image(
                            _current_context()[1].id, upload,
                            prefix=f'{m_type}-img-{ii + 1}'
                        )
                    except Exception as exc:
                        current_app.logger.warning('模块图片上传失败: %s', exc)
                if url:
                    images.append({'url': url})
            if images:
                data['images'] = images
            else:
                data.pop('images', None)

            specs_count = 0
            try:
                specs_count = int(form.get(f'{idx}_data_specs_count', '0'))
            except (ValueError, TypeError):
                pass
            specs = []
            for si in range(specs_count):
                name = form.get(f'{idx}_data_specs_{si}_name', '').strip()
                value = form.get(f'{idx}_data_specs_{si}_value', '').strip()
                if name or value:
                    specs.append({'name': name, 'value': value})
            if specs:
                data['specs'] = specs
            else:
                data.pop('specs', None)

        if m_type == 'feature_grid':
            feature_count = 0
            try:
                feature_count = int(form.get(f'{idx}_feature_count', '0'))
            except (ValueError, TypeError):
                feature_count = 0

            features = []
            for fi in range(feature_count):
                prefix = f'{idx}_feature_{fi}_'
                item = {}
                for field in ('icon', 'title', 'desc'):
                    value = form.get(f'{prefix}{field}', '').strip()
                    if value:
                        item[field] = value
                if item.get('title') or item.get('desc') or item.get('icon'):
                    features.append(item)

            if features:
                data['features'] = features
            else:
                features_value = data.get('features')
                if isinstance(features_value, list):
                    data['features'] = features_value
                elif isinstance(features_value, str) and features_value.strip():
                    parsed_features = _parse_value(features_value)
                    if isinstance(parsed_features, list):
                        data['features'] = parsed_features

        # 解析 stat_counter 的统计项列表
        if m_type == 'stat_counter':
            stat_count = 0
            try:
                stat_count = int(form.get(f'{idx}_stat_count', '0'))
            except (ValueError, TypeError):
                stat_count = 0
            stats = []
            for si in range(stat_count):
                prefix = f'{idx}_stat_{si}_'
                item = {}
                for field in ('icon', 'number', 'suffix', 'label'):
                    value = form.get(f'{prefix}{field}', '').strip()
                    if value:
                        item[field] = value
                if item.get('label') or item.get('number'):
                    stats.append(item)
            if stats:
                data['stats'] = stats

        # 解析 logo_cloud 的 Logo 列表
        if m_type == 'logo_cloud':
            logo_count = 0
            try:
                logo_count = int(form.get(f'{idx}_logo_count', '0'))
            except (ValueError, TypeError):
                logo_count = 0
            logos = []
            for li in range(logo_count):
                prefix = f'{idx}_logo_{li}_'
                item = {}
                for field in ('image', 'name', 'link'):
                    value = form.get(f'{prefix}{field}', '').strip()
                    if value:
                        item[field] = value
                upload = request.files.get(f'{prefix}image_file')
                if upload and upload.filename:
                    try:
                        item['image'] = _save_uploaded_image(
                            _current_context()[1].id,
                            upload,
                            prefix=f'logo-{li + 1}',
                        )
                    except Exception as exc:
                        current_app.logger.warning('Logo 图片上传失败: %s', exc)
                if item.get('image') or item.get('name'):
                    logos.append(item)
            if logos:
                data['logos'] = logos

        # 解析 process_steps 的步骤列表
        if m_type == 'process_steps':
            step_count = 0
            try:
                step_count = int(form.get(f'{idx}_step_count', '0'))
            except (ValueError, TypeError):
                step_count = 0
            steps = []
            for si in range(step_count):
                prefix = f'{idx}_step_{si}_'
                item = {}
                for field in ('title', 'desc', 'icon'):
                    value = form.get(f'{prefix}{field}', '').strip()
                    if value:
                        item[field] = value
                if item.get('title') or item.get('desc'):
                    steps.append(item)
            if steps:
                data['steps'] = steps

        for field in list(data.keys()):
            if _field_looks_like_image(field):
                upload = request.files.get(f'{idx}_data_{field}_file')
                if upload and upload.filename:
                    try:
                        data[field] = _save_uploaded_image(
                            _current_context()[1].id,
                            upload,
                            prefix=f'{m_type}-{field}',
                        )
                    except Exception as exc:
                        current_app.logger.warning('模块图片保存失败 %s: %s', field, exc)

        # 解析电脑端的 columns 和 max_items
        columns_val = form.get(f'{idx}_resp_columns', '').strip()
        if columns_val:
            try:
                data['columns'] = int(columns_val)
            except ValueError:
                pass
        max_items_val = form.get(f'{idx}_resp_max_items', '').strip()
        if max_items_val:
            try:
                data['max_items'] = int(max_items_val)
            except ValueError:
                pass

        # 解析响应式配置
        responsive = {}
        for device in ('tablet', 'mobile'):
            device_data = {}
            # 设备独立数据字段
            for key in form:
                prefix = f'{idx}_resp_{device}_data_'
                if key.startswith(prefix):
                    field = key[len(prefix):]
                    val = form.get(key, '').strip()
                    if val:
                        device_data[field] = _parse_value(val)

            # 设备 columns
            dev_columns = form.get(f'{idx}_resp_{device}_columns', '').strip()
            if dev_columns:
                try:
                    device_data['columns'] = int(dev_columns)
                except ValueError:
                    pass

            # 设备 max_items
            dev_max = form.get(f'{idx}_resp_{device}_max_items', '').strip()
            if dev_max:
                try:
                    device_data['max_items'] = int(dev_max)
                except ValueError:
                    pass

            # 设备 hidden
            if form.get(f'{idx}_resp_{device}_hidden'):
                device_data['hidden'] = True

            if device_data:
                responsive[device] = device_data

        # 第二步：从已有数据中保留表单未涉及的字段（防止嵌套数组丢失）
        existing_key = (m_type, order)
        if existing_key in existing_by_key and isinstance(existing_by_key[existing_key], dict):
            for ek, ev in existing_by_key[existing_key].items():
                if ek not in form_fields_for_module and ek not in data:
                    data[ek] = ev

        module = {
            'type': m_type,
            'order': order,
            'variant': variant,
            'data': data,
        }
        if responsive:
            module['responsive'] = responsive

        modules.append(module)

    return modules
