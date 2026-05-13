"""静态站点生成器.

读取 sites/<id>/*.yaml + site_templates/<name>/templates/*.html,
渲染输出到 output/<id>/.
支持多语言: 每种语言一个子目录 (/zh-CN/, /zh-TW/, /en/).
根路径生成语言选择首页.
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


def _deep_merge(default, override):
    """递归合并 dict，用模板 seed 作为缺省，站点数据覆盖。"""
    if not isinstance(default, dict) or not isinstance(override, dict):
        return override if override not in (None, {}) else default
    result = dict(default)
    for key, value in override.items():
        if isinstance(result.get(key), dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _gather_site_data(site_id, template_name=None):
    """收集店主网站的全部内容."""
    sites_dir = Path(current_app.config['SITES_DIR'])
    root = sites_dir / str(site_id)

    settings = _load_yaml(root / 'settings.yaml')
    if template_name:
        seed_root = Path(current_app.config['TEMPLATES_DIR']) / template_name / 'seed_data'
        seed_settings = _load_yaml(seed_root / 'settings.yaml')
        settings = _deep_merge(seed_settings, settings)
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


def _load_translations(tpl_root):
    """加载多语言翻译文件."""
    seed = tpl_root / 'seed_data'
    translations_file = seed / 'translations.yaml'
    if translations_file.exists():
        return _load_yaml(translations_file)
    return {}


def _build_language_selector_page(output_root, base_url, settings, theme, year, meta, translations):
    """在根路径生成语言选择首页."""
    languages = meta.get('languages', [])
    if not languages:
        return

    html = '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
    html += '<meta charset="UTF-8">\n'
    html += '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    html += '<title>Language - ' + settings.get('company', {}).get('name', '') + '</title>\n'
    html += '<meta http-equiv="refresh" content="0;url=' + base_url.rstrip('/') + '/' + languages[0]['code'] + '/">\n'
    html += '<link rel="stylesheet" href="' + base_url.rstrip('/') + '/static/css/main.css">\n'
    html += '</head>\n<body style="display:flex;align-items:center;justify-content:center;min-height:100vh;flex-direction:column;gap:2rem;">\n'
    html += '<h1>' + settings.get('company', {}).get('name', '') + '</h1>\n'
    html += '<p>Select your language / 選擇語言 / 选择语言</p>\n'
    html += '<div style="display:flex;gap:1rem;">\n'
    for lang in languages:
        html += '<a href="' + base_url.rstrip('/') + '/' + lang['code'] + '/" '
        html += 'style="padding:1rem 2rem;border:1px solid #e5e7eb;border-radius:8px;text-decoration:none;font-size:1.2rem;">'
        html += lang.get('flag', '') + ' ' + lang['name'] + '</a>\n'
    html += '</div>\n</body>\n</html>'

    (output_root / 'index.html').write_text(html, encoding='utf-8')


def _render_for_language(env, tpl_html_dir, output_root, lang_code, common, pages, data, meta):
    """为一种语言渲染所有页面 (菜单驱动)."""
    lang_output = output_root / lang_code

    _common = dict(common)
    _common['lang'] = lang_code

    # 收集渲染任务 (菜单驱动)
    menu_items = _common.get('settings', {}).get('menu', [])
    tasks = menu_lib.collect_render_tasks(menu_items, tpl_html_dir, data, pages)

    for task in tasks:
        try:
            tpl = env.get_template(task['template'])

            # 准备渲染上下文
            ctx = dict(_common)
            ctx['current_path'] = task['current_path']

            if task['type'] == 'home':
                ctx['page'] = pages.get('home', {})
            elif task['type'] == 'list':
                ctx['page'] = pages.get(task['page_key'], {})
            elif task['type'] in ('page',):
                ctx['page'] = pages.get(task['page_key'], {})
            elif task['type'] == 'detail':
                ctx['page'] = pages.get(task['page_key'], {})
                ctx[task['var_name']] = task['item']

            rendered = tpl.render(**ctx)
            out = lang_output / task['output_path']
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(rendered, encoding='utf-8')
        except Exception as e:
            current_app.logger.error(
                '页面 %s (type=%s, lang=%s) 渲染失败: %s',
                task.get('template'), task.get('type'), lang_code, e,
            )


def build_site(site_id, base_url=''):
    """生成站点到 output/<site_id>/. 返回输出根目录.

    支持多语言: 每种语言一个子目录, 根路径生成语言选择首页.

    base_url: 站内链接和静态资源的前缀.
              发布到 CDN 时为 '' (站点在根),
              本地预览时为 '/preview/<id>'.
    """
    site = Site.query.get(site_id)
    if not site:
        raise ValueError(f'站点不存在: {site_id}')

    settings, pages, data = _gather_site_data(site_id, site.template_name)

    # 模板默认值兜底
    tpl_root, tpl_html_dir, tpl_static_dir = _template_paths(site.template_name)
    meta = _load_yaml(tpl_root / 'meta.yaml')
    translations = _load_translations(tpl_root)

    current_version = meta.get('version')
    if site.template_version and current_version and site.template_version != current_version:
        current_app.logger.warning(
            '站点 %s 记录的模板版本 %s 与磁盘上 %s 的当前版本 %s 不一致',
            site_id, site.template_version, site.template_name, current_version,
        )
    if 'menu' not in settings or not settings.get('menu'):
        settings['menu'] = meta.get('default_menu', [])
    settings['menu'] = menu_lib.ensure_home(
        menu_lib.normalize_for_render(
            menu_lib.upgrade_old_format(settings['menu'], meta.get('datasets', []))
        )
    )
    theme_default = meta.get('default_theme', {})
    theme = {**theme_default, **(settings.get('theme') or {})}

    # Jinja: 搜索 templates/ 目录 + 父目录 (供 blocks/ include 使用)
    env = Environment(
        loader=FileSystemLoader([str(tpl_html_dir), str(tpl_root)]),
        autoescape=select_autoescape(['html']),
        trim_blocks=True, lstrip_blocks=True,
    )

    output_root = Path(current_app.config['OUTPUT_DIR']) / str(site_id)
    if output_root.exists():
        shutil.rmtree(output_root, ignore_errors=True)
    output_root.mkdir(parents=True, exist_ok=True)

    # 复制 static/
    if tpl_static_dir.exists():
        shutil.copytree(tpl_static_dir, output_root / 'static')

    # 复制店主上传的 assets/
    site_assets = Path(current_app.config['SITES_DIR']) / str(site_id) / 'assets'
    if site_assets.exists():
        shutil.copytree(site_assets, output_root / 'assets', dirs_exist_ok=True)

    languages = meta.get('languages', [])
    # 提取 product_categories 和 products 供导航用
    products_categories = _extract_products_categories(data)
    products_items = _extract_products_items(data)

    year = datetime.now().year

    if languages:
        # 多语言模式
        _build_language_selector_page(output_root, base_url, settings, theme, year, meta, translations)

        for lang_opt in languages:
            lang_code = lang_opt['code']
            t_data = translations.get(lang_code, {})

            common = {
                'settings': settings,
                'theme': theme,
                'year': year,
                'lang': lang_code,
                'base_url': base_url.rstrip('/'),
                't': t_data,
                'languages': languages,
                'products_categories': products_categories,
                'products': products_items,
                'portfolio': data.get('portfolio', []),
                'posts': data.get('posts', []),
                'features': data.get('features', []),
                'all_datasets': data,
            }

            _render_for_language(env, tpl_html_dir, output_root, lang_code, common, pages, data, meta)
    else:
        # 单语言模式 (兼容旧模板)
        common = {
            'settings': settings,
            'theme': theme,
            'year': year,
            'lang': site.default_language,
            'base_url': base_url.rstrip('/'),
            't': {},
            'languages': [],
            'products_categories': products_categories,
            'products': products_items,
            'portfolio': data.get('portfolio', []),
            'posts': data.get('posts', []),
            'features': data.get('features', []),
        }
        _render_for_language(env, tpl_html_dir, output_root, '', common, pages, data, meta)

    return output_root


def _extract_products_categories(data):
    """从 data.products 中提取 categories."""
    raw = data.get('products') or {}
    if isinstance(raw, dict):
        return raw.get('categories', [])
    return []


def _extract_products_items(data):
    """从 data.products 中提取产品条目."""
    raw = data.get('products') or {}
    if isinstance(raw, dict):
        return raw.get('items', [])
    if isinstance(raw, list):
        return raw
    return []


def build_template_preview(template_name, base_url=''):
    """用模板的 seed_data 构建一个预览站点 (不需要真实 site).

    输出到 output/_preview/<template_name>/.
    支持多语言模板.
    """
    tpl_root, tpl_html_dir, tpl_static_dir = _template_paths(template_name)
    if not tpl_html_dir.exists():
        raise ValueError(f'模板没有 HTML: {template_name}')

    seed = tpl_root / 'seed_data'
    settings = _load_yaml(seed / 'settings.yaml')
    pages = {f.stem: _load_yaml(f) for f in (seed / 'pages').glob('*.yaml')}
    data = {f.stem: _load_yaml(f) for f in (seed / 'data').glob('*.yaml')}
    meta = _load_yaml(tpl_root / 'meta.yaml')
    translations = _load_translations(tpl_root)

    if not settings.get('menu'):
        settings['menu'] = meta.get('default_menu', [])
    settings['menu'] = menu_lib.ensure_home(
        menu_lib.normalize_for_render(
            menu_lib.upgrade_old_format(settings['menu'], meta.get('datasets', []))
        )
    )
    theme = {**meta.get('default_theme', {}), **(settings.get('theme') or {})}

    env = Environment(
        loader=FileSystemLoader([str(tpl_html_dir), str(tpl_root)]),
        autoescape=select_autoescape(['html']),
        trim_blocks=True, lstrip_blocks=True,
    )

    output_root = Path(current_app.config['OUTPUT_DIR']) / '_preview' / template_name
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    if tpl_static_dir.exists():
        shutil.copytree(tpl_static_dir, output_root / 'static')

    languages = meta.get('languages', [])
    products_categories = _extract_products_categories(data)
    products_items = _extract_products_items(data)
    year = datetime.now().year

    if languages:
        _build_language_selector_page(output_root, base_url, settings, theme, year, meta, translations)
        for lang_opt in languages:
            lang_code = lang_opt['code']
            t_data = translations.get(lang_code, {})
            common = {
                'settings': settings, 'theme': theme,
                'year': year, 'lang': lang_code,
                'base_url': base_url.rstrip('/'),
                't': t_data, 'languages': languages,
                'products_categories': products_categories,
                'products': products_items,
                'portfolio': data.get('portfolio', []),
                'posts': data.get('posts', []),
                'features': data.get('features', []),
            }
            _render_for_language(env, tpl_html_dir, output_root, lang_code, common, pages, data, meta)
    else:
        common = {
            'settings': settings, 'theme': theme,
            'year': year, 'lang': 'zh',
            'base_url': base_url.rstrip('/'),
            't': {}, 'languages': [],
            'products_categories': products_categories,
            'products': products_items,
            'portfolio': data.get('portfolio', []),
            'posts': data.get('posts', []),
            'features': data.get('features', []),
        }
        _render_for_language(env, tpl_html_dir, output_root, '', common, pages, data, meta)

    return output_root
