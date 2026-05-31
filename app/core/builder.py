"""静态站点生成器.

读取 sites/<id>/*.yaml + themes/<name>/templates/*.html,
渲染输出到 output/<id>/.
"""
import shutil
from datetime import datetime
from pathlib import Path

import yaml
from flask import current_app
from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import menu as menu_lib
from .models import Site


def _load_yaml(path):
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding='utf-8')) or {}


def _gather_site_data(site_id):
    """收集店主网站的全部内容."""
    sites_dir = Path(current_app.config['SITES_DIR'])
    root = sites_dir / str(site_id)

    settings = _load_yaml(root / 'settings.yaml')
    pages = {}
    for f in (root / 'pages').glob('*.yaml'):
        pages[f.stem] = _load_yaml(f)
    data = {}
    for f in (root / 'data').glob('*.yaml'):
        data[f.stem] = _load_yaml(f)

    return settings, pages, data


def _template_paths(template_name):
    base = Path(current_app.config['TEMPLATES_DIR']) / template_name
    return base, base / 'templates', base / 'static'


def build_site(site_id, base_url=''):
    """生成站点到 output/<site_id>/. 返回输出根目录.

    base_url: 站内链接和静态资源的前缀.
              发布到 CDN 时为 '' (站点在根),
              本地预览时为 '/preview/<id>'.
    """
    site = Site.query.get(site_id)
    if not site:
        raise ValueError(f'站点不存在: {site_id}')

    settings, pages, data = _gather_site_data(site_id)

    # 模板默认值兜底
    tpl_root, tpl_html_dir, tpl_static_dir = _template_paths(site.template_name)
    meta = _load_yaml(tpl_root / 'meta.yaml')
    # 模板版本对比: 站点固定的版本 vs 磁盘上模板当前版本
    # 不一致只警告, 不阻塞 — 真要冻结老版本时再做版本目录 (见 docs/templates.md 第九节)
    current_version = meta.get('version')
    if site.template_version and current_version and site.template_version != current_version:
        current_app.logger.warning(
            '站点 %s 记录的模板版本 %s 与磁盘上 %s 的当前版本 %s 不一致',
            site_id, site.template_version, site.template_name, current_version,
        )
    if 'menu' not in settings or not settings.get('menu'):
        settings['menu'] = meta.get('default_menu', [])
    # 升级旧菜单格式 + 计算每项的 url, 给模板用
    settings['menu'] = menu_lib.normalize_for_render(
        menu_lib.upgrade_old_format(settings['menu'], meta.get('datasets', []))
    )
    theme_default = meta.get('default_theme', {})
    theme = {**theme_default, **(settings.get('theme') or {})}

    # Jinja
    env = Environment(
        loader=FileSystemLoader(str(tpl_html_dir)),
        autoescape=select_autoescape(['html']),
        trim_blocks=True, lstrip_blocks=True,
    )

    output_root = Path(current_app.config['OUTPUT_DIR']) / str(site_id)
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    # 复制 static/
    if tpl_static_dir.exists():
        shutil.copytree(tpl_static_dir, output_root / 'static')

    # 复制店主上传的 assets/
    site_assets = Path(current_app.config['SITES_DIR']) / str(site_id) / 'assets'
    if site_assets.exists():
        shutil.copytree(site_assets, output_root / 'assets', dirs_exist_ok=True)

    common = {
        'settings': settings,
        'theme': theme,
        'year': datetime.now().year,
        'lang': site.default_language,
        'base_url': base_url.rstrip('/'),
        **data,  # products, features, posts 等数据集直接暴露
    }

    # 页面映射: 模板文件 -> 输出路径, 用哪份 page 数据
    page_map = [
        ('index.html', 'index.html', 'home'),
        ('products.html', 'products/index.html', 'products'),
        ('blog.html', 'blog/index.html', 'blog'),
    ]

    for tpl_file, out_path, page_key in page_map:
        if not (tpl_html_dir / tpl_file).exists():
            continue
        tpl = env.get_template(tpl_file)
        rendered = tpl.render(page=pages.get(page_key, {}), **common)
        out = output_root / out_path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding='utf-8')

    # 详情页: 每条数据生成一个独立页面
    detail_map = [
        ('product_detail.html', 'products', 'product', 'slug'),
        ('post_detail.html', 'posts', 'post', 'slug'),
    ]
    for tpl_file, dataset_key, var_name, slug_field in detail_map:
        if not (tpl_html_dir / tpl_file).exists():
            continue
        items = data.get(dataset_key) or []
        tpl = env.get_template(tpl_file)
        for item in items:
            slug = item.get(slug_field)
            if not slug:
                continue
            rendered = tpl.render(**{var_name: item}, **common)
            out = output_root / dataset_key / slug / 'index.html'
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(rendered, encoding='utf-8')

    return output_root


def build_template_preview(template_name, base_url=''):
    """用模板的 seed_data 构建一个预览站点 (不需要真实 site).

    输出到 output/_preview/<template_name>/.
    """
    tpl_root, tpl_html_dir, tpl_static_dir = _template_paths(template_name)
    if not tpl_html_dir.exists():
        raise ValueError(f'模板没有 HTML: {template_name}')

    seed = tpl_root / 'seed_data'
    settings = _load_yaml(seed / 'settings.yaml')
    pages = {f.stem: _load_yaml(f) for f in (seed / 'pages').glob('*.yaml')}
    data = {f.stem: _load_yaml(f) for f in (seed / 'data').glob('*.yaml')}
    meta = _load_yaml(tpl_root / 'meta.yaml')
    if not settings.get('menu'):
        settings['menu'] = meta.get('default_menu', [])
    settings['menu'] = menu_lib.normalize_for_render(
        menu_lib.upgrade_old_format(settings['menu'], meta.get('datasets', []))
    )
    theme = {**meta.get('default_theme', {}), **(settings.get('theme') or {})}

    env = Environment(
        loader=FileSystemLoader(str(tpl_html_dir)),
        autoescape=select_autoescape(['html']),
        trim_blocks=True, lstrip_blocks=True,
    )

    output_root = Path(current_app.config['OUTPUT_DIR']) / '_preview' / template_name
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    if tpl_static_dir.exists():
        shutil.copytree(tpl_static_dir, output_root / 'static')

    common = {
        'settings': settings, 'theme': theme,
        'year': datetime.now().year, 'lang': 'zh',
        'base_url': base_url.rstrip('/'),
        **data,
    }

    page_map = [
        ('index.html', 'index.html', 'home'),
        ('products.html', 'products/index.html', 'products'),
        ('blog.html', 'blog/index.html', 'blog'),
    ]
    for tpl_file, out_path, page_key in page_map:
        if not (tpl_html_dir / tpl_file).exists():
            continue
        rendered = env.get_template(tpl_file).render(page=pages.get(page_key, {}), **common)
        out = output_root / out_path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding='utf-8')

    return output_root
