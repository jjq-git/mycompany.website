"""店主后台路由. M1: 默认进 site_id=1, 不带登录."""
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, abort, current_app, render_template, send_from_directory

import re

import yaml as _yaml

from . import datasets
from . import menu as menu_lib
from .builder import build_site, build_template_preview
from .models import Site, Template, User
from .site_storage import (copy_seed_data, init_site_folder,
                            list_yaml_files, read_yaml, write_yaml)

bp = Blueprint('core', __name__)


@bp.context_processor
def inject_context():
    """给所有模板注入站点上下文."""
    from flask import request
    site_id = request.args.get('site', type=int)
    if not site_id:
        site = Site.query.order_by(Site.id.desc()).first()
        site_id = site.id if site else None
    else:
        site = Site.query.get(site_id)

    ctx = {'counts': {}, 'left_menu_items': [], 'template_meta': {}}

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
        normalized = menu_lib.normalize_for_render(
            menu_lib.upgrade_old_format(raw_menu, datasets_meta)
        )
        ctx['left_menu_items'] = normalized

    return ctx


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
            return redirect(url_for('core.company', _fragment='1'))
        return redirect(url_for('core.company'))

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

    # 检测格式: modules 数组 vs 旧固定 key
    is_modules_format = 'modules' in page

    if request.method == 'POST':
        if is_modules_format or request.form.get('_format') == 'modules':
            # modules 数组格式保存
            page['modules'] = _parse_modules_form(request.form)
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
        return redirect(url_for('core.page_home'))

    # 准备渲染上下文
    blocks = _get_available_blocks(site.template_name)
    if is_modules_format:
        page.setdefault('modules', [])
    else:
        page.setdefault('hero', {})
        for key in ('featured_section', 'features_section', 'about_brief', 'blog_section', 'subscribe_section'):
            page.setdefault(key, {})

    return render_template('dashboard/page_home.html',
                           user=user, site=site, page=page,
                           is_modules_format=is_modules_format,
                           blocks=blocks,
                           active='pages_home')


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
    is_fragment = request.args.get('_fragment') is not None

    if request.method == 'POST':
        labels = request.form.getlist('label[]')
        types = request.form.getlist('type[]')
        targets_list = request.form.getlist('target_list[]')
        urls_link = request.form.getlist('url_link[]')
        items = [{'label': '首页', 'type': 'home'}]
        for i, label in enumerate(labels):
            label = label.strip()
            if not label:
                continue
            t = types[i] if i < len(types) else 'link'
            if t == 'home':
                items[0]['label'] = label or '首页'
                continue
            it = {'label': label, 'type': t}
            if t in ('list', 'page'):
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
        flash('已保存，首页已保持为固定入口')
        if is_fragment:
            return redirect(url_for('core.menu_edit', _fragment='1'))
        return redirect(url_for('core.menu_edit'))

    # GET: 升级旧格式
    meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
    raw_menu = settings.get('menu') or meta.get('default_menu', [])
    items = menu_lib.upgrade_old_format(raw_menu, meta.get('datasets', []))
    home_items = [it for it in items if it.get('type') == 'home']
    other_items = [it for it in items if it.get('type') != 'home']
    items = (home_items[:1] or [{'label': '首页', 'type': 'home'}]) + other_items

    if is_fragment:
        return render_template('dashboard/panel_menu.html',
                               user=user, site=site, items=items)
    return render_template('dashboard/menu.html',
                           user=user, site=site, items=items, active='menu')


@bp.route('/settings/footer', methods=['GET', 'POST'])
def footer_edit():
    from flask import flash, redirect, request, url_for
    user, site = _current_context()
    is_fragment = request.args.get('_fragment') is not None
    if request.method == 'POST':
        _save_link_list(site.id, 'footer_links')
        flash('已保存')
        if is_fragment:
            return redirect(url_for('core.footer_edit', _fragment='1'))
        return redirect(url_for('core.footer_edit'))
    settings = read_yaml(site.id, 'settings.yaml') or {}
    items = settings.get('footer_links') or []
    if is_fragment:
        return render_template('dashboard/panel_footer.html',
                               user=user, site=site, items=items)
    return render_template('dashboard/footer_links.html',
                           user=user, site=site, items=items, active='footer')


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
            return redirect(url_for('core.social_edit', _fragment='1'))
        return redirect(url_for('core.social_edit'))
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
            return redirect(url_for('core.theme_edit', _fragment='1'))
        return redirect(url_for('core.theme_edit'))

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
    user, site = _current_context()
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
    return redirect(url_for('core.preview_site', site_id=site.id))


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

    if not (out / filepath).exists():
        try:
            build_site(site_id, base_url=f'/preview/{site_id}')
        except Exception:
            pass
    if not out.exists():
        out.mkdir(parents=True, exist_ok=True)
    full = out / filepath
    if full.is_dir():
        full = full / 'index.html'
        filepath = f'{filepath.rstrip("/")}/index.html'
    if not full.exists():
        # 尝试默认语言子目录
        for sub in out.iterdir():
            if sub.is_dir() and (sub / 'index.html').exists():
                return send_from_directory(out, f'{sub.name}/index.html')
        abort(404, '未生成页面，请检查模板数据')
    return send_from_directory(out, filepath)


def _render(template_name, **kwargs):
    """渲染模板，支持 ?_fragment=1 返回右侧面板片段."""
    from flask import request
    if request.args.get('_fragment'):
        return render_template(template_name, **kwargs)
    return render_template(template_name, **kwargs)


@bp.route('/_panel/<path:page_key>')
def page_panel(page_key):
    """动态菜单项面板路由：根据 page_key 分发到对应数据集列表或单页编辑."""
    user, site = _current_context()

    # 尝试匹配数据集
    data_items = datasets.load(site.id, page_key)
    if data_items:
        return _render('dashboard/panel_data_list.html',
                       user=user, site=site,
                       dataset_key=page_key, items=data_items,
                       active=page_key)

    # 尝试匹配单页
    page = read_yaml(site.id, f'pages/{page_key}.yaml')
    if page:
        return _render('dashboard/panel_page_edit.html',
                       user=user, site=site,
                       page_key=page_key, page=page,
                       active=page_key)

    return _render('dashboard/panel_empty.html',
                   user=user, site=site,
                   page_key=page_key, active=page_key)


def _get_available_blocks(template_name):
    """获取模板的可用模块列表."""
    from .template_loader import scan_blocks
    try:
        return scan_blocks(template_name)
    except Exception:
        return []


def _parse_modules_form(form):
    """从 POST 表单解析 modules 数组."""
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

        data = {}
        for key in form:
            prefix = f'{idx}_data_'
            if key.startswith(prefix):
                field = key[len(prefix):]
                data[field] = _parse_value(form.get(key, ''))

        modules.append({
            'type': m_type,
            'order': order,
            'variant': variant,
            'data': data,
        })

    return modules
