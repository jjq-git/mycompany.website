"""店主后台路由. M1: 默认进 site_id=1, 不带登录."""
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, abort, current_app, render_template, send_from_directory

import re

from . import datasets
from . import menu as menu_lib
from .builder import build_site, build_template_preview
from .models import Site, Template, User
from .site_storage import (copy_seed_data, init_site_folder,
                            list_yaml_files, read_yaml, write_yaml)

bp = Blueprint('core', __name__)


def _current_context():
    """M1 占位: 取当前站点 (默认最新创建的). M2 接入登录后改为 session.

    支持 ?site=<id> 切换 (一次性, 不持久).
    """
    from flask import request
    site_id = request.args.get('site', type=int)
    if site_id:
        site = Site.query.get(site_id)
    else:
        site = Site.query.order_by(Site.id.desc()).first()
    user = User.query.first()
    if not site:
        abort(404, "尚无站点, 请先 .venv/bin/flask --app run create-site EMAIL SLUG")
    return user, site


@bp.route('/')
def index():
    return overview()


@bp.route('/overview')
def overview():
    user, site = _current_context()
    products = read_yaml(site.id, 'data/products.yaml') or []
    pages = list_yaml_files(site.id, 'pages')
    counts = {'products': len(products), 'pages': len(pages)}
    return render_template('dashboard/overview.html',
                           user=user, site=site, counts=counts, active='overview')


@bp.route('/company', methods=['GET', 'POST'])
def company():
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}

    if request.method == 'POST':
        settings.setdefault('company', {})
        settings.setdefault('contact', {})
        for field in ('name', 'short_name', 'icp'):
            settings['company'][field] = request.form.get(f'company.{field}', '').strip()
        for field in ('phone', 'email', 'address', 'wechat'):
            settings['contact'][field] = request.form.get(f'contact.{field}', '').strip()
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        return redirect(url_for('core.company'))

    return render_template('dashboard/company.html',
                           user=user, site=site,
                           company=settings.get('company', {}),
                           contact=settings.get('contact', {}),
                           active='company')


@bp.route('/products')
def products():
    user, site = _current_context()
    products = read_yaml(site.id, 'data/products.yaml') or []
    return render_template('dashboard/products.html',
                           user=user, site=site, products=products, active='products')


@bp.route('/products/new', methods=['POST'])
def product_new():
    from flask import redirect, url_for
    _, site = _current_context()
    new_id = datasets.add(site.id, 'products', {
        'name': '新产品', 'slug': f'product-{datasets.load(site.id, "products")|length + 1}',
        'summary': '', 'description': '', 'cover': '', 'category': '', 'specs': {},
    })
    return redirect(url_for('core.product_edit', product_id=new_id))


@bp.route('/products/<int:product_id>/delete', methods=['POST'])
def product_delete(product_id):
    from flask import flash, redirect, url_for
    _, site = _current_context()
    datasets.remove(site.id, 'products', product_id)
    flash('已删除')
    return redirect(url_for('core.products'))


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
        return redirect(url_for('core.product_edit', product_id=product_id))

    return render_template('dashboard/product_edit.html',
                           user=user, site=site, product=product, active='products')


# ----- 功能 -----

@bp.route('/features')
def features():
    user, site = _current_context()
    return render_template('dashboard/features.html',
                           user=user, site=site,
                           items=datasets.load(site.id, 'features'),
                           active='features')


@bp.route('/features/new', methods=['POST'])
def feature_new():
    from flask import redirect, url_for
    _, site = _current_context()
    new_id = datasets.add(site.id, 'features',
                          {'icon': '', 'title': '新功能', 'desc': ''})
    return redirect(url_for('core.feature_edit', item_id=new_id))


@bp.route('/features/<int:item_id>/delete', methods=['POST'])
def feature_delete(item_id):
    from flask import flash, redirect, url_for
    _, site = _current_context()
    datasets.remove(site.id, 'features', item_id)
    flash('已删除')
    return redirect(url_for('core.features'))


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
        return redirect(url_for('core.feature_edit', item_id=item_id))
    return render_template('dashboard/feature_edit.html',
                           user=user, site=site, item=item, active='features')


# ----- 博客 -----

@bp.route('/blog')
def blog():
    user, site = _current_context()
    return render_template('dashboard/blog.html',
                           user=user, site=site,
                           items=datasets.load(site.id, 'posts'),
                           active='blog')


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
    return redirect(url_for('core.post_edit', item_id=new_id))


@bp.route('/blog/<int:item_id>/delete', methods=['POST'])
def post_delete(item_id):
    from flask import flash, redirect, url_for
    _, site = _current_context()
    datasets.remove(site.id, 'posts', item_id)
    flash('已删除')
    return redirect(url_for('core.blog'))


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
        datasets.update(site.id, 'posts', item_id, fields)
        flash('已保存')
        return redirect(url_for('core.post_edit', item_id=item_id))
    return render_template('dashboard/post_edit.html',
                           user=user, site=site, item=item, active='blog')


@bp.route('/pages/home', methods=['GET', 'POST'])
def page_home():
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    page = read_yaml(site.id, 'pages/home.yaml') or {}

    if request.method == 'POST':
        # Hero
        page.setdefault('hero', {})
        for f in ('title', 'subtitle', 'badge', 'cta_text', 'cta_url', 'video_url', 'background_image'):
            page['hero'][f] = request.form.get(f'hero.{f}', '').strip()
        # 各区块
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
        return redirect(url_for('core.page_home'))

    # 兜底默认, 避免模板里访问空字段炸
    page.setdefault('hero', {})
    for key in ('featured_section', 'features_section', 'about_brief', 'blog_section', 'subscribe_section'):
        page.setdefault(key, {})
    return render_template('dashboard/page_home.html',
                           user=user, site=site, page=page, active='pages')


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
    user, site = _current_context()
    site_count = Site.query.filter_by(owner_id=user.id).count() if user else 0
    return render_template('dashboard/account.html',
                           user=user, site=site, site_count=site_count, active='account')


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


@bp.route('/settings/menu', methods=['GET', 'POST'])
def menu_edit():
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}

    if request.method == 'POST':
        labels = request.form.getlist('label[]')
        types = request.form.getlist('type[]')
        targets_list = request.form.getlist('target_list[]')
        urls_link = request.form.getlist('url_link[]')
        items = []
        for i, label in enumerate(labels):
            label = label.strip()
            if not label:
                continue
            t = types[i] if i < len(types) else 'link'
            it = {'label': label, 'type': t}
            if t == 'list':
                target = targets_list[i].strip() if i < len(targets_list) else ''
                if target:
                    it['target'] = target
            elif t == 'link':
                url = urls_link[i].strip() if i < len(urls_link) else ''
                if url:
                    it['url'] = url
            items.append(it)
        settings['menu'] = items
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        return redirect(url_for('core.menu_edit'))

    # GET: 升级旧格式
    from pathlib import Path
    import yaml as _yaml
    meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
    items = menu_lib.upgrade_old_format(settings.get('menu') or [], meta.get('datasets', []))
    return render_template('dashboard/menu.html',
                           user=user, site=site, items=items, active='menu')


@bp.route('/settings/footer', methods=['GET', 'POST'])
def footer_edit():
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    if request.method == 'POST':
        _save_link_list(site.id, 'footer_links')
        flash('已保存')
        return redirect(url_for('core.footer_edit'))
    settings = read_yaml(site.id, 'settings.yaml') or {}
    return render_template('dashboard/footer_links.html',
                           user=user, site=site,
                           items=settings.get('footer_links') or [],
                           active='footer')


@bp.route('/settings/social', methods=['GET', 'POST'])
def social_edit():
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    if request.method == 'POST':
        social = settings.setdefault('social', {})
        for platform in ('github', 'twitter', 'facebook', 'linkedin', 'youtube'):
            social[platform] = request.form.get(platform, '').strip()
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        return redirect(url_for('core.social_edit'))
    return render_template('dashboard/social.html',
                           user=user, site=site,
                           social=settings.get('social') or {},
                           active='social')


@bp.route('/settings/theme', methods=['GET', 'POST'])
def theme_edit():
    from flask import flash, redirect, request, url_for
    from pathlib import Path
    import yaml as _yaml
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    # 模板默认主题, 用于占位提示
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
                theme.pop(key, None)  # 留空 = 删除, 用模板默认
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        return redirect(url_for('core.theme_edit'))

    return render_template('dashboard/theme.html',
                           user=user, site=site,
                           theme=settings.get('theme') or {},
                           default_theme=default_theme,
                           active='theme')


SLUG_PATTERN = re.compile(r'^[a-z0-9][a-z0-9-]{1,28}[a-z0-9]$')


@bp.route('/templates')
def templates_gallery():
    user, site = _current_context()
    return render_template('dashboard/templates_gallery.html',
                           user=user, site=site,
                           templates=Template.query.order_by(Template.name).all(),
                           active='templates')


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
    template_name = request.args.get('template')
    template = Template.query.filter_by(name=template_name).first() if template_name else None
    if not template:
        return redirect(url_for('core.templates_gallery'))

    user = User.query.first()
    if not user:
        abort(403, '尚无用户. 先创建一个: flask --app run create-user EMAIL')

    form = {'name': '', 'slug': ''}
    error = None

    if request.method == 'POST':
        form['name'] = request.form.get('name', '').strip()
        form['slug'] = request.form.get('slug', '').strip().lower()

        from .models import SLUG_RESERVED
        if not form['name']:
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
                folder_path='', template_name=template.name,
                template_version=template.current_version, cdn_provider='aliyun',
            )
            db.session.add(site)
            db.session.flush()
            site.folder_path = f'sites/{site.id}'
            db.session.commit()
            init_site_folder(site.id)
            copy_seed_data(site.id, template.name)
            flash(f'已创建站点 #{site.id} ({form["slug"]})')
            return redirect(url_for('core.overview', site=site.id))

    return render_template('dashboard/site_new.html',
                           user=user, site=Site.query.first(),
                           template=template, form=form, error=error,
                           active='templates')


@bp.route('/build')
def build():
    """触发构建当前站点, 跳到预览首页."""
    _, site = _current_context()
    build_site(site.id, base_url=f'/preview/{site.id}')
    from flask import redirect, url_for
    return redirect(url_for('core.preview', site_id=site.id, filepath='index.html'))


@bp.route('/preview/<int:site_id>/')
@bp.route('/preview/<int:site_id>/<path:filepath>')
def preview(site_id, filepath='index.html'):
    """预览 output/<site_id>/ 下的静态文件."""
    out = Path(current_app.config['OUTPUT_DIR']) / str(site_id)
    if not out.exists():
        abort(404, f'尚未构建. 先访问 /build 或运行 flask --app run build-site {site_id}')
    full = out / filepath
    if full.is_dir():
        full = full / 'index.html'
        filepath = f'{filepath.rstrip("/")}/index.html'
    return send_from_directory(out, filepath)
