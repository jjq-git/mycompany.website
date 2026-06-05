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
from jinja2 import Environment, FileSystemLoader, select_autoescape, pass_context
from markupsafe import Markup

from . import block_parser, block_renderer
from . import menu as menu_lib
from .models import Site


# block schema 解析缓存：同一次构建里一个 block 只解析一次。
# key = (template_name, block_name, variant)，value = (html, schema) 或 None（旧式 Jinja2）。
_SCHEMA_CACHE = {}


def _load_block_for_render(tpl_root, template_name, block_type, variant):
    """加载 block 模板并判断走新/旧路径，带缓存。

    返回 (html, schema)：schema 非 None → data-* 声明式；schema 为 None → 旧 Jinja2。
    找不到模板返回 (None, None)。
    """
    blocks_dir = tpl_root / 'blocks' / block_type
    # 与 _modules.html 的 include 列表一致：优先变体，回退默认 template.html
    candidates = []
    if variant and variant != 'default':
        candidates.append(blocks_dir / 'variants' / f'{variant}.html')
    candidates.append(blocks_dir / 'template.html')

    html = None
    source_path = None
    for path in candidates:
        if path.exists():
            source_path = path
            cache_key = (str(tpl_root), block_type, variant, str(path), path.stat().st_mtime_ns)
            if cache_key in _SCHEMA_CACHE:
                return _SCHEMA_CACHE[cache_key]
            html = path.read_text(encoding='utf-8')
            break

    if html is None:
        result = (None, None)
    elif block_parser.is_data_attr_block(html):
        try:
            result = (html, block_parser.parse(html))
        except Exception as e:
            current_app.logger.warning('block %s 解析失败，回退 Jinja2: %s', block_type, e)
            result = (html, None)
    else:
        result = (html, None)

    if source_path is not None:
        _SCHEMA_CACHE[cache_key] = result
    return result


def _make_render_block(env, tpl_root, template_name, enable_data_attr):
    """工厂：生成注册到 Jinja2 的 render_block 全局函数.

    _modules.html 中对每个 module 调用 render_block(module)，本函数全权决定渲染路径：
    - data-* 声明式 block 且开关开 → 用 block_renderer 渲染，返回安全 HTML
    - 否则 → 走旧 Jinja2 include 逻辑（加载子模板渲染），行为与改造前完全一致
    """
    @pass_context
    def render_block(jinja_ctx, module):
        block_type = module.get('type')
        variant = module.get('variant') or 'default'
        if not block_type:
            return Markup('')

        html, schema = _load_block_for_render(tpl_root, template_name, block_type, variant)
        if html is None:
            return Markup('')  # 模板缺失，静默跳过（与 include ignore missing 一致）

        # 新路径：开关开 + 是 data-* 声明式
        if enable_data_attr and schema is not None:
            data_dict = module.get('data') if isinstance(module.get('data'), dict) else {}
            if block_type == 'item_data':
                item_data = jinja_ctx.get('item')
                if isinstance(item_data, dict):
                    merged_item = dict(item_data)
                    tags = merged_item.get('tags')
                    if isinstance(tags, str):
                        merged_item['tags'] = [t.strip() for t in tags.split(',') if t.strip()]
                    if merged_item.get('section_bg') and not merged_item.get('style_bg-color'):
                        merged_item['style_bg-color'] = merged_item.get('section_bg')
                    merged_item.update(data_dict)
                    data_dict = merged_item
            context = {
                'all_datasets': jinja_ctx.get('all_datasets', {}),
                # data-from 用：settings（含 contact 等全局配置）
                'settings': jinja_ctx.get('settings', {}),
                # data-href-template 用：站内链接前缀（base_url/lang/current_path）
                'vars': {
                    'base_url': jinja_ctx.get('base_url', '') or '',
                    'lang': jinja_ctx.get('lang', '') or '',
                    'current_path': jinja_ctx.get('current_path', '') or '',
                },
            }
            try:
                out = block_renderer.render(html, schema, data_dict, context)
                return Markup(out)
            except Exception as e:
                current_app.logger.error('block %s 渲染失败: %s', block_type, e)
                return Markup('')

        # 旧路径：用 Jinja2 渲染子模板，复用当前 ctx + 注入 module 变量
        sub_ctx = dict(jinja_ctx)
        sub_ctx['module'] = module
        names = []
        if variant and variant != 'default':
            names.append(f'blocks/{block_type}/variants/{variant}.html')
        # 若 template.html 已是 data-* 写法（schema 非 None），但开关关 →
        # 不能把 data-* HTML 当 Jinja2 渲染（会原样吐出脏属性），优先回退到旧版备份。
        if schema is not None:
            names.append(f'blocks/{block_type}/template.jinja2.bak')
        names.append(f'blocks/{block_type}/template.html')
        try:
            tpl = env.select_template(names)
        except Exception:
            return Markup('')
        # rstrip 尾换行，对齐 {% include %} 的 trim_blocks 行为（消除纯空白 diff）
        return Markup(tpl.render(**sub_ctx).rstrip('\n'))

    return render_block


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
    # 加载种子页面数据作为缺省值
    if template_name:
        seed_pages_dir = Path(current_app.config['TEMPLATES_DIR']) / template_name / 'seed_data' / 'pages'
        if seed_pages_dir.exists():
            for f in seed_pages_dir.rglob('*.yaml'):
                rel = f.relative_to(seed_pages_dir).as_posix()
                page_key = rel[:-5] if rel.endswith('.yaml') else rel
                pages[page_key] = _load_yaml(f)
    # 站点页面数据覆盖种子数据
    pages_dir = root / 'pages'
    if pages_dir.exists():
        for f in pages_dir.rglob('*.yaml'):
            # 相对于 pages/ 的路径作为 key，如 'about'、'products/silent-booth'
            rel = f.relative_to(pages_dir).as_posix()
            page_key = rel[:-5] if rel.endswith('.yaml') else rel  # 去掉 .yaml 后缀
            pages[page_key] = _deep_merge(pages.get(page_key, {}), _load_yaml(f))
    data = {}
    data_dir = root / 'data'
    if data_dir.exists():
        for f in data_dir.rglob('*.yaml'):
            rel = f.relative_to(data_dir).as_posix()
            dataset_key = rel[:-5] if rel.endswith('.yaml') else rel
            data[dataset_key] = _load_yaml(f)

    return settings, pages, data


def _load_lang_overrides(site_id, lang_code, default_lang, default_pages, default_data):
    """加载语言特定 pages 和 data, 回退到默认语言.

    非默认语言: 先读 lang/<code>/ 下的文件, 不存在的 key 用默认语言数据.
    默认语言: 直接用默认数据.
    """
    if lang_code == default_lang:
        return default_pages, default_data

    from .site_storage import read_yaml, list_yaml_files

    # 加载语言特定 pages
    lang_pages = dict(default_pages)
    for f in list_yaml_files(site_id, 'pages', lang=lang_code):
        # 只取语言特定目录中的文件 (list_yaml_files 返回去重列表, 需要判断来源)
        if f'lang/{lang_code}' in f.as_posix():
            page_key = f.stem
            content = read_yaml(site_id, f'pages/{f.name}', lang=lang_code)
            if content:
                lang_pages[page_key] = content

    # 加载语言特定 data
    lang_data = dict(default_data)
    for f in list_yaml_files(site_id, 'data', lang=lang_code):
        if f'lang/{lang_code}' in f.as_posix():
            dataset_key = f.stem
            content = read_yaml(site_id, f'data/{f.name}', lang=lang_code)
            if content:
                lang_data[dataset_key] = content

    return lang_pages, lang_data


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


def _build_language_selector_page(output_root, base_url, settings, theme, year, meta, translations, languages=None):
    """在根路径生成语言选择首页.

    languages: 已过滤的启用语言列表，若不传则从 meta 读取全部.
    """
    if languages is None:
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

    # 收集渲染任务 (菜单驱动). cap_menu_depth 防御深嵌套递归栈溢出.
    menu_items = menu_lib.cap_menu_depth(_common.get('settings', {}).get('menu', []))
    tasks = menu_lib.collect_render_tasks(menu_items, tpl_html_dir, data, pages)

    for task in tasks:
        try:
            tpl = env.get_template(task['template'])

            # 准备渲染上下文
            ctx = dict(_common)
            ctx['current_path'] = task['current_path']

            ctx['page_key'] = task['page_key']
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
    # 注册 data-* block 双路径渲染入口（开关关时等价旧 Jinja2 include）
    _enable_da = current_app.config.get('ENABLE_DATA_ATTR_BLOCKS', False)
    env.globals['render_block'] = _make_render_block(env, tpl_root, site.template_name, _enable_da)

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
    # 按站点启用的语言过滤（从 DB enabled_languages 读取，兜底显示全部）
    enabled_codes = site.enabled_languages or [l['code'] for l in languages]
    languages = [l for l in languages if l['code'] in enabled_codes]
    # 兜底：如果过滤后为空（旧站点 enabled_languages 可能与模板不一致），使用全部语言
    if not languages:
        languages = meta.get('languages', [])
    # 提取 product_categories 和 products 供导航用
    default_lang = meta.get('default_language', languages[0]['code'] if languages else 'zh-CN')

    year = datetime.now().year

    if languages:
        # 多语言模式
        _build_language_selector_page(output_root, base_url, settings, theme, year, meta, translations, languages)

        for lang_opt in languages:
            lang_code = lang_opt['code']
            t_data = translations.get(lang_code, {})

            # 加载语言特定数据，回退到默认语言
            lang_pages, lang_data = _load_lang_overrides(site_id, lang_code, default_lang, pages, data)

            # 语言特定菜单（settings 中 menu_<lang> 覆盖 menu）
            lang_settings = dict(settings)
            menu_override_key = f'menu_{lang_code}'
            if menu_override_key in settings and settings[menu_override_key]:
                lang_settings['menu'] = menu_lib.ensure_home(
                    menu_lib.normalize_for_render(
                        menu_lib.upgrade_old_format(settings[menu_override_key], meta.get('datasets', []))
                    )
                )

            # 提取语言特定的产品分类和列表
            lang_products_categories = _extract_products_categories(lang_data)
            lang_products_items = _extract_products_items(lang_data)

            common = {
                'settings': lang_settings,
                'theme': theme,
                'year': year,
                'lang': lang_code,
                'base_url': base_url.rstrip('/'),
                't': t_data,
                'languages': languages,
                'products_categories': lang_products_categories,
                'products': lang_products_items,
                'portfolio': lang_data.get('portfolio', []),
                'posts': lang_data.get('posts', []),
                'features': lang_data.get('features', []),
                'all_datasets': lang_data,
            }

            _render_for_language(env, tpl_html_dir, output_root, lang_code, common, lang_pages, lang_data, meta)
    else:
        # 单语言模式 (兼容旧模板)
        # 修复：原先引用了未定义的 products_categories/products_items 导致单语言站点构建崩溃。
        # 从 data 提取（与多语言分支的 lang_data 提取逻辑对齐），并补 all_datasets。
        products_categories = _extract_products_categories(data)
        products_items = _extract_products_items(data)
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
            'all_datasets': data,
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
    # 注册 data-* block 双路径渲染入口（开关关时等价旧 Jinja2 include）
    _enable_da = current_app.config.get('ENABLE_DATA_ATTR_BLOCKS', False)
    env.globals['render_block'] = _make_render_block(env, tpl_root, template_name, _enable_da)

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
            'year': year, 'lang': 'zh-CN',
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
