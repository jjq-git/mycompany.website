"""静态站点生成器.

读取 sites/<id>/*.yaml + site_templates/<name>/templates/*.html,
渲染输出到 output/<id>/.
支持多语言: 每种语言一个子目录 (/zh-CN/, /zh-TW/, /en/).
根路径生成语言选择首页.
"""
import json
import copy
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urljoin

import yaml
from flask import current_app
from jinja2 import Environment, FileSystemLoader, select_autoescape, pass_context
from markupsafe import Markup, escape

from . import block_parser, block_renderer
from . import menu as menu_lib
from .models import Site


# block schema 解析缓存：同一次构建里一个 block 只解析一次。
# key = (template_name, block_name, variant)，value = (html, schema) 或 None（旧式 Jinja2）。
_SCHEMA_CACHE = {}
_YAML_CACHE = {}
_YAML_CACHE_MAX = 512

_LANGUAGE_FLAG_FALLBACKS = {
    'zh': '🇨🇳',
    'zh-cn': '🇨🇳',
    'zh-hans': '🇨🇳',
    'zh-tw': '🇹🇼',
    'zh-hant': '🇹🇼',
    'en': '🇺🇸',
    'en-us': '🇺🇸',
    'en-gb': '🇬🇧',
    'ja': '🇯🇵',
    'jp': '🇯🇵',
    'ko': '🇰🇷',
    'fr': '🇫🇷',
    'de': '🇩🇪',
    'es': '🇪🇸',
    'it': '🇮🇹',
    'pt': '🇵🇹',
    'ru': '🇷🇺',
}

_LANGUAGE_COUNTRY_FALLBACKS = {
    'zh': 'cn',
    'zh-cn': 'cn',
    'zh-hans': 'cn',
    'zh-tw': 'tw',
    'zh-hant': 'tw',
    'en': 'us',
    'en-us': 'us',
    'en-gb': 'gb',
    'ja': 'jp',
    'jp': 'jp',
    'ko': 'kr',
    'fr': 'fr',
    'de': 'de',
    'es': 'es',
    'it': 'it',
    'pt': 'pt',
    'ru': 'ru',
}


def _country_code_to_flag(value):
    """Convert two-letter country codes such as CN/US to flag emoji."""
    if not isinstance(value, str):
        return ''
    code = value.strip().upper()
    if len(code) != 2 or not code.isalpha():
        return ''
    return ''.join(chr(0x1F1E6 + ord(ch) - ord('A')) for ch in code)


def _language_flag(lang):
    raw_flag = str(lang.get('flag') or '').strip()
    if raw_flag:
        from_country_code = _country_code_to_flag(raw_flag)
        return from_country_code or raw_flag

    code = str(lang.get('code') or '').strip()
    lowered = code.lower().replace('_', '-')
    fallback = _LANGUAGE_FLAG_FALLBACKS.get(lowered)
    if fallback:
        return fallback
    parts = lowered.split('-')
    if len(parts) > 1:
        return _country_code_to_flag(parts[-1])
    return _LANGUAGE_FLAG_FALLBACKS.get(parts[0], '')


def _language_country_code(lang):
    raw_flag = str(lang.get('flag') or '').strip()
    if len(raw_flag) == 2 and raw_flag.isalpha():
        return raw_flag.lower()

    code = str(lang.get('code') or '').strip().lower().replace('_', '-')
    fallback = _LANGUAGE_COUNTRY_FALLBACKS.get(code)
    if fallback:
        return fallback
    parts = code.split('-')
    if len(parts) > 1 and len(parts[-1]) == 2 and parts[-1].isalpha():
        return parts[-1]
    return _LANGUAGE_COUNTRY_FALLBACKS.get(parts[0], parts[0][:2] if parts and parts[0] else '')


def _flag_svg(country_code):
    code = (country_code or '').lower()
    if code == 'cn':
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 40"><rect width="60" height="40" fill="#de2910"/><polygon points="10,6 11.8,11.5 17.6,11.5 12.9,14.9 14.7,20.4 10,17 5.3,20.4 7.1,14.9 2.4,11.5 8.2,11.5" fill="#ffde00"/><circle cx="23" cy="8" r="2.2" fill="#ffde00"/><circle cx="29" cy="14" r="2.2" fill="#ffde00"/><circle cx="29" cy="23" r="2.2" fill="#ffde00"/><circle cx="23" cy="29" r="2.2" fill="#ffde00"/></svg>'
    if code == 'tw':
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 40"><rect width="60" height="40" rx="4" fill="#f8fafc"/><rect width="60" height="40" rx="4" fill="none" stroke="#cbd5e1"/><text x="30" y="29" text-anchor="middle" font-family="Arial, Noto Sans TC, sans-serif" font-size="27" font-weight="800" fill="#334155">繁</text></svg>'
    if code == 'us':
        stripes = ''.join(f'<rect y="{i * 40 / 13:.3f}" width="60" height="{40 / 13:.3f}" fill="#b22234"/>' for i in range(0, 13, 2))
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 40"><rect width="60" height="40" fill="#fff"/>{stripes}<rect width="27" height="21.5" fill="#3c3b6e"/><g fill="#fff"><circle cx="5" cy="4" r="1"/><circle cx="11" cy="4" r="1"/><circle cx="17" cy="4" r="1"/><circle cx="23" cy="4" r="1"/><circle cx="8" cy="9" r="1"/><circle cx="14" cy="9" r="1"/><circle cx="20" cy="9" r="1"/><circle cx="5" cy="14" r="1"/><circle cx="11" cy="14" r="1"/><circle cx="17" cy="14" r="1"/><circle cx="23" cy="14" r="1"/></g></svg>'
    if code == 'gb':
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 40"><rect width="60" height="40" fill="#012169"/><path d="M0 0l60 40M60 0L0 40" stroke="#fff" stroke-width="8"/><path d="M0 0l60 40M60 0L0 40" stroke="#c8102e" stroke-width="4"/><path d="M30 0v40M0 20h60" stroke="#fff" stroke-width="12"/><path d="M30 0v40M0 20h60" stroke="#c8102e" stroke-width="7"/></svg>'
    if code == 'jp':
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 40"><rect width="60" height="40" fill="#fff"/><circle cx="30" cy="20" r="11" fill="#bc002d"/></svg>'
    if code == 'kr':
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 40"><rect width="60" height="40" fill="#fff"/><path d="M30 9a11 11 0 0 1 0 22a5.5 5.5 0 0 1 0-11a5.5 5.5 0 0 0 0-11z" fill="#cd2e3a"/><path d="M30 31a11 11 0 0 1 0-22a5.5 5.5 0 0 1 0 11a5.5 5.5 0 0 0 0 11z" fill="#0047a0"/></svg>'
    if code == 'fr':
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 40"><rect width="20" height="40" fill="#0055a4"/><rect x="20" width="20" height="40" fill="#fff"/><rect x="40" width="20" height="40" fill="#ef4135"/></svg>'
    if code == 'de':
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 40"><rect width="60" height="13.333" fill="#000"/><rect y="13.333" width="60" height="13.333" fill="#dd0000"/><rect y="26.666" width="60" height="13.334" fill="#ffce00"/></svg>'
    if code == 'es':
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 40"><rect width="60" height="40" fill="#aa151b"/><rect y="10" width="60" height="20" fill="#f1bf00"/></svg>'
    if code == 'it':
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 40"><rect width="20" height="40" fill="#009246"/><rect x="20" width="20" height="40" fill="#fff"/><rect x="40" width="20" height="40" fill="#ce2b37"/></svg>'
    if code == 'pt':
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 40"><rect width="24" height="40" fill="#006600"/><rect x="24" width="36" height="40" fill="#ff0000"/><circle cx="24" cy="20" r="6" fill="#ffcc00"/></svg>'
    if code == 'ru':
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 40"><rect width="60" height="13.333" fill="#fff"/><rect y="13.333" width="60" height="13.333" fill="#0039a6"/><rect y="26.666" width="60" height="13.334" fill="#d52b1e"/></svg>'
    label = escape((code or '--').upper())
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 40"><rect width="60" height="40" rx="4" fill="#eef2f7"/><rect width="60" height="40" rx="4" fill="none" stroke="#cbd5e1"/><text x="30" y="25" text-anchor="middle" font-family="Arial,sans-serif" font-size="15" font-weight="700" fill="#475569">{label}</text></svg>'


def _language_flag_image(lang):
    country_code = _language_country_code(lang)
    svg = _flag_svg(country_code)
    return 'data:image/svg+xml,' + quote(svg, safe='')


def _normalize_language_flags(languages):
    normalized = []
    for lang in languages or []:
        if not isinstance(lang, dict):
            normalized.append(lang)
            continue
        lang_copy = dict(lang)
        lang_copy['flag'] = _language_flag(lang_copy)
        lang_copy['flag_image'] = _language_flag_image(lang_copy)
        normalized.append(lang_copy)
    return normalized


def _get_platform_base_url():
    """返回平台后端的基础 URL, 供静态站点 contact_form 表单提交.

    开发环境始终回退 localhost, 避免把表单指到生产域名.
    生产环境从 PLATFORM_DOMAIN 配置拼 https 地址.
    """
    if current_app.debug:
        return 'http://localhost:5000'
    domain = current_app.config.get('PLATFORM_DOMAIN', '')
    if domain:
        return f'https://{domain}'
    return 'http://localhost:5000'


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
        # product_grid → data_grid 别名（向后兼容已有站点的旧模块配置）
        if block_type == 'product_grid':
            block_type = 'data_grid'
        variant = module.get('variant') or 'default'
        if not block_type:
            return Markup('')

        html, schema = _load_block_for_render(tpl_root, template_name, block_type, variant)
        if html is None:
            return Markup('')  # 模板缺失，静默跳过（与 include ignore missing 一致）

        # 新路径：开关开 + 是 data-* 声明式
        if enable_data_attr and schema is not None:
            data_dict = module.get('data') if isinstance(module.get('data'), dict) else {}
            # contact_form 内置留言：注入平台 API 地址和站点 ID, 供模板 JS 使用
            if block_type == 'contact_form':
                data_dict['platform_api_url'] = jinja_ctx.get('platform_api_url', '')
                data_dict['site_id'] = str(jinja_ctx.get('site_id', ''))
            dataset_name = data_dict.get('dataset', '')
            dataset_path = ((jinja_ctx.get('dataset_paths') or {}).get(dataset_name) or '')
            base_prefix = (jinja_ctx.get('base_url', '') or '').rstrip('/')
            if base_prefix and dataset_path.startswith('/') and not dataset_path.startswith(base_prefix + '/'):
                dataset_path = base_prefix + dataset_path
            if block_type == 'item_data':
                # 数据集详情页的上下文变量名因数据集而异（product / post / feature / item 等），
                # 优先取 item，找不到再依次尝试 product / post / feature 等常见命名
                item_data = jinja_ctx.get('item')
                if not isinstance(item_data, dict):
                    for _var in ('product', 'post', 'feature', 'portfolio'):
                        _candidate = jinja_ctx.get(_var)
                        if isinstance(_candidate, dict):
                            item_data = _candidate
                            break
                if isinstance(item_data, dict):
                    merged_item = dict(item_data)
                    tags = merged_item.get('tags')
                    if isinstance(tags, str):
                        merged_item['tags'] = [t.strip() for t in tags.split(',') if t.strip()]
                    if merged_item.get('section_bg') and not merged_item.get('style_bg-color'):
                        merged_item['style_bg-color'] = merged_item.get('section_bg')
                    detail_gallery = merged_item.get('detail_gallery')
                    if isinstance(detail_gallery, dict):
                        detail_visible = detail_gallery.get('visible')
                        detail_images = detail_gallery.get('images')
                        if detail_visible is False or str(detail_visible).lower() == 'false':
                            merged_item['_hidden_detail_images'] = True
                            merged_item['detail_images'] = []
                        elif isinstance(detail_images, list):
                            merged_item['detail_images'] = detail_images
                    if not merged_item.get('detail_images'):
                        merged_item['_hidden_detail_images'] = True
                    media_type = merged_item.get('media_type') or (
                        'embed' if merged_item.get('embed_url') else
                        ('video' if merged_item.get('video') else 'image')
                    )
                    # cover 不计入 media_area 自动显示（模板层默认隐藏 Cover，用户可显式设 media_type 覆盖）
                    has_image_media = any(merged_item.get(k) for k in ('image', 'photo', 'logo'))
                    has_selected_media = (
                        (media_type == 'image' and has_image_media) or
                        (media_type == 'video' and merged_item.get('video')) or
                        (media_type == 'embed' and merged_item.get('embed_url'))
                    )
                    if has_selected_media and not merged_item.get('media_type'):
                        merged_item['media_type'] = media_type
                    if not has_selected_media:
                        merged_item['_hidden_media_area'] = True
                    if merged_item.get('tags_visible') is False or str(merged_item.get('tags_visible')).lower() == 'false':
                        merged_item['_hidden_tags'] = True
                    # 模块 data 覆盖产品字段，但空值不覆盖已有字段
                    for k, v in data_dict.items():
                        if v not in (None, '', [], {}):
                            merged_item[k] = v
                    data_dict = merged_item
            context = {
                'all_datasets': jinja_ctx.get('all_datasets', {}),
                # data-from 用：settings（含 contact 等全局配置）
                'settings': jinja_ctx.get('settings', {}),
                't': jinja_ctx.get('t', {}),
                # data-href-template 及 data-filter-* 用：站内链接前缀 + 数据集名
                'vars': {
                    'base_url': jinja_ctx.get('base_url', '') or '',
                    'lang': jinja_ctx.get('lang', '') or '',
                    'current_path': jinja_ctx.get('current_path', '') or '',
                    'dataset': dataset_name,
                    'dataset_path': dataset_path,
                    'default_alt': data_dict.get('alt') or data_dict.get('image_alt') or data_dict.get('cover_alt')
                                   or data_dict.get('title') or data_dict.get('name') or '',
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
    try:
        stat = path.stat()
        cache_key = (str(path.resolve()), stat.st_mtime_ns, stat.st_size)
        cached = _YAML_CACHE.get(cache_key)
        if cached is not None:
            return copy.deepcopy(cached)
        data = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
        if len(_YAML_CACHE) >= _YAML_CACHE_MAX:
            _YAML_CACHE.pop(next(iter(_YAML_CACHE)), None)
        _YAML_CACHE[cache_key] = data
        return copy.deepcopy(data)
    except OSError:
        return {}


def _is_content_yaml(path):
    """Return true for real content YAML files, excluding atomic-write leftovers."""
    name = Path(path).name
    return name.endswith(('.yaml', '.yml')) and not name.startswith('.tmp-')


def _first_text(*values):
    """返回第一个非空字符串，用于 SEO 字段的多来源兜底。"""
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ''


def _site_base_url(site=None, base_url=''):
    """计算 SEO 使用的站点根 URL。

    预览构建只有相对 base_url，不能伪造成正式域名；发布构建 base_url 为空时，
    先用 slug.platform_domain 兜底，等自定义域名链路上线后这里再接真实域名。
    """
    base = (base_url or '').strip().rstrip('/')
    if base.startswith('http://') or base.startswith('https://'):
        return base
    if base:
        return base
    if site is not None and getattr(site, 'slug', None):
        domain = current_app.config.get('PLATFORM_DOMAIN', '').strip().strip('/')
        return f'https://{site.slug}.{domain}'
    return ''


def _seo_url(site_base_url, lang_code, path):
    """拼出页面 URL；支持正式域名和预览相对路径两种场景。"""
    clean_path = path if path.startswith('/') else f'/{path}'
    if lang_code:
        clean_path = f'/{lang_code}{clean_path}'
    if not site_base_url:
        return clean_path
    if site_base_url.startswith('http://') or site_base_url.startswith('https://'):
        return urljoin(site_base_url.rstrip('/') + '/', clean_path.lstrip('/'))
    return site_base_url.rstrip('/') + clean_path


def _seo_asset_url(site_base_url, asset_path):
    """把 Logo / 分享图转成可用于 OG 的 URL，外链原样保留。"""
    asset = (asset_path or '').strip()
    if not asset:
        return ''
    if asset.startswith('http://') or asset.startswith('https://') or asset.startswith('data:'):
        return asset
    if not asset.startswith('/'):
        asset = '/' + asset
    if not site_base_url:
        return asset
    if site_base_url.startswith('http://') or site_base_url.startswith('https://'):
        return urljoin(site_base_url.rstrip('/') + '/', asset.lstrip('/'))
    return site_base_url.rstrip('/') + asset


def _company_name(settings, t=None):
    company = settings.get('company') or {}
    return _first_text(company.get('name'), settings.get('title'), (t or {}).get('company'), 'Website')


def _company_description(settings):
    company = settings.get('company') or {}
    return _first_text(
        settings.get('slogan'),
        company.get('slogan'),
        company.get('description'),
        company.get('intro'),
        company.get('name'),
    )


def _seo_title_description(task, ctx, settings, t):
    """按页面类型推导 title/description，避免让店主手写 SEO。"""
    company_name = _company_name(settings, t)
    page = ctx.get('page') if isinstance(ctx.get('page'), dict) else {}
    page_key = task.get('page_key', '')
    t_pages = (t or {}).get('pages') if isinstance((t or {}).get('pages'), dict) else {}

    item = task.get('item') if isinstance(task.get('item'), dict) else {}
    if task.get('type') == 'detail':
        title = _first_text(item.get('seo_title'), item.get('title'), item.get('name'), page.get('title'), page_key)
        description = _first_text(item.get('seo_description'), item.get('summary'), item.get('description'), item.get('excerpt'))
    elif task.get('type') == 'home':
        title = _first_text(page.get('title'), company_name)
        description = _first_text(page.get('description'), _company_description(settings))
    else:
        title = _first_text(page.get('title'), t_pages.get(page_key), page_key.replace('_', ' ').title())
        description = _first_text(page.get('description'), _company_description(settings))

    if company_name and company_name not in title:
        title = f'{title} - {company_name}'
    return title, description


def _json_ld_for_task(task, seo, ctx, settings):
    """生成基础 JSON-LD。字段不足时宁可少写，也不让用户维护结构化数据。"""
    company = settings.get('company') or {}
    contact = settings.get('contact') or {}
    company_name = _company_name(settings)
    logo = seo.get('image', '')

    nodes = [{
        '@context': 'https://schema.org',
        '@type': 'Organization',
        'name': company_name,
        'url': seo.get('site_url') or seo.get('canonical_url'),
    }]
    if logo:
        nodes[0]['logo'] = logo

    item = task.get('item') if isinstance(task.get('item'), dict) else {}
    dataset_key = task.get('dataset_key')
    if task.get('type') == 'detail' and dataset_key == 'products':
        product = {
            '@context': 'https://schema.org',
            '@type': 'Product',
            'name': _first_text(item.get('name'), item.get('title')),
            'description': _first_text(item.get('summary'), item.get('description')),
            'brand': {'@type': 'Brand', 'name': company_name},
        }
        image = _first_text(item.get('image'), item.get('image_url'), item.get('cover'), item.get('thumbnail'))
        if image:
            product['image'] = _seo_asset_url(seo.get('site_url', ''), image)
        nodes.append(product)
    elif task.get('type') == 'detail' and dataset_key in ('posts', 'blog', 'articles'):
        nodes.append({
            '@context': 'https://schema.org',
            '@type': 'Article',
            'headline': _first_text(item.get('title'), item.get('name')),
            'description': _first_text(item.get('summary'), item.get('description'), item.get('excerpt')),
            'author': {'@type': 'Organization', 'name': company_name},
        })
    elif task.get('page_key') == 'contact':
        local = {
            '@context': 'https://schema.org',
            '@type': 'LocalBusiness',
            'name': company_name,
            'url': seo.get('canonical_url'),
        }
        if contact.get('phone'):
            local['telephone'] = contact.get('phone')
        if contact.get('email'):
            local['email'] = contact.get('email')
        if contact.get('address'):
            local['address'] = contact.get('address')
        nodes.append(local)

    if task.get('type') != 'home':
        nodes.append({
            '@context': 'https://schema.org',
            '@type': 'BreadcrumbList',
            'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': seo.get('home_url')},
                {'@type': 'ListItem', 'position': 2, 'name': seo.get('title'), 'item': seo.get('canonical_url')},
            ],
        })
    return nodes


def _build_seo_context(task, ctx, common, meta):
    """为模板和站点级文件构建统一 SEO 上下文。"""
    settings = common.get('settings') or {}
    t = common.get('t') or {}
    lang_code = common.get('lang') or ''
    site_base_url = common.get('site_base_url') or common.get('base_url') or ''
    languages = common.get('languages') or []
    title, description = _seo_title_description(task, ctx, settings, t)
    company = settings.get('company') or {}
    page = ctx.get('page') if isinstance(ctx.get('page'), dict) else {}
    image = _first_text(
        page.get('og_image'),
        page.get('cover'),
        company.get('og_image'),
        company.get('logo'),
    )

    canonical_url = _seo_url(site_base_url, lang_code, task.get('current_path', '/'))
    site_url = site_base_url or _seo_url('', '', '/')
    alternate_urls = []
    for lang in languages:
        code = lang.get('code')
        if not code:
            continue
        alternate_urls.append({
            'lang': code,
            'url': _seo_url(site_base_url, code, task.get('current_path', '/')),
        })
    if languages:
        default_lang = meta.get('default_language') or languages[0].get('code')
        alternate_urls.append({
            'lang': 'x-default',
            'url': _seo_url(site_base_url, default_lang, task.get('current_path', '/')),
        })

    seo = {
        'title': title,
        'description': description,
        'canonical_url': canonical_url,
        'alternate_urls': alternate_urls,
        'image': _seo_asset_url(site_base_url, image),
        'site_name': _company_name(settings, t),
        'site_url': site_base_url,
        'home_url': _seo_url(site_base_url, lang_code, '/'),
        'type': 'article' if task.get('dataset_key') in ('posts', 'blog', 'articles') else 'website',
    }
    seo['json_ld'] = _json_ld_for_task(task, seo, ctx, settings)
    return seo


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


def _merge_page_content(default, override):
    """Merge language-specific page text without dropping inherited modules."""
    if not isinstance(default, dict) or not isinstance(override, dict):
        return override if override not in (None, {}) else default
    clean_override = dict(override)
    if clean_override.get('modules') == [] and default.get('modules'):
        clean_override.pop('modules')
    return _deep_merge(default, clean_override)


def _merge_language_settings_section(shared, override):
    """Merge shared settings with language-specific text overrides."""
    if not isinstance(shared, dict):
        shared = {}
    if not isinstance(override, dict):
        override = {}
    shared_first_fields = {'logo', 'favicon', 'icp', 'phone', 'mobile', 'email', 'wechat'}
    result = dict(shared)
    for key, value in override.items():
        if key in shared_first_fields and result.get(key):
            continue
        if value not in (None, ''):
            result[key] = value
    return result


def _language_override(settings, base_key, lang_code, default_lang, fallback_to_default=True):
    """Return current language override, falling back to the real default language."""
    settings = settings or {}
    current = settings.get(f'{base_key}_{lang_code}')
    if current:
        return current
    if fallback_to_default and lang_code != default_lang:
        return settings.get(f'{base_key}_{default_lang}') or {}
    return {}


def _language_label_map(settings, lang_code, default_lang, fallback_to_default=True):
    """Merge menu labels from default language and current language."""
    labels = (settings or {}).get('menu_labels') or {}
    default_labels = labels.get(default_lang) if isinstance(labels.get(default_lang), dict) else {}
    current_labels = labels.get(lang_code) if isinstance(labels.get(lang_code), dict) else {}
    if lang_code == default_lang:
        return dict(default_labels or current_labels or {})
    if not fallback_to_default:
        return dict(current_labels or {})
    merged = dict(default_labels or {})
    merged.update(current_labels or {})
    return merged


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
                if not _is_content_yaml(f):
                    continue
                rel = f.relative_to(seed_pages_dir).as_posix()
                page_key = rel[:-5] if rel.endswith('.yaml') else rel
                pages[page_key] = _load_yaml(f)
    # 站点页面数据覆盖种子数据
    pages_dir = root / 'pages'
    if pages_dir.exists():
        for f in pages_dir.rglob('*.yaml'):
            if not _is_content_yaml(f):
                continue
            # 相对于 pages/ 的路径作为 key，如 'about'、'products/silent-booth'
            rel = f.relative_to(pages_dir).as_posix()
            page_key = rel[:-5] if rel.endswith('.yaml') else rel  # 去掉 .yaml 后缀
            pages[page_key] = _deep_merge(pages.get(page_key, {}), _load_yaml(f))
    data = {}
    data_dir = root / 'data'
    if data_dir.exists():
        for f in data_dir.rglob('*.yaml'):
            if not _is_content_yaml(f):
                continue
            rel = f.relative_to(data_dir).as_posix()
            dataset_key = rel[:-5] if rel.endswith('.yaml') else rel
            data[dataset_key] = _load_yaml(f)

    return settings, pages, data


def _load_lang_overrides(site_id, lang_code, default_lang, default_pages, default_data):
    """加载语言特定 pages 和 data, 回退到默认语言.

    非默认语言: 先读 lang/<code>/ 下的文件, 不存在的 key 用默认语言数据.
    默认语言: 若存在 lang/<code>/, 也优先用该目录覆盖；否则直接用默认数据.
    """
    from .site_storage import lang_root, read_yaml, list_yaml_files

    # Some imported sites keep the default language content under lang/<code>/
    # while the root pages/data hold another language. Prefer the explicit
    # language folder whenever it exists, even for the default language.
    if lang_code == default_lang and not lang_root(site_id, lang_code).exists():
        return default_pages, default_data

    # 加载语言特定 pages
    lang_pages = dict(default_pages)
    for f in list_yaml_files(site_id, 'pages', lang=lang_code):
        # 只取语言特定目录中的文件 (list_yaml_files 返回去重列表, 需要判断来源)
        if f'lang/{lang_code}' in f.as_posix():
            page_key = f.stem
            content = read_yaml(site_id, f'pages/{f.name}', lang=lang_code)
            if content:
                lang_pages[page_key] = _merge_page_content(lang_pages.get(page_key, {}), content)

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


def _create_template_env(tpl_root, tpl_html_dir, template_name):
    env = Environment(
        loader=FileSystemLoader([str(tpl_html_dir), str(tpl_root)]),
        autoescape=select_autoescape(['html']),
        trim_blocks=True, lstrip_blocks=True,
    )
    _enable_da = current_app.config.get('ENABLE_DATA_ATTR_BLOCKS', False)
    env.globals['render_block'] = _make_render_block(env, tpl_root, template_name, _enable_da)
    return env


def _load_translations(tpl_root):
    """加载多语言翻译文件."""
    seed = tpl_root / 'seed_data'
    translations_file = seed / 'translations.yaml'
    if translations_file.exists():
        return _load_yaml(translations_file)
    return {}


def _load_seed_lang_overrides(seed, lang_code, default_lang, default_pages, default_data):
    """从 seed_data/lang/<code>/ 加载语言特定的 pages 和 data.

    非默认语言: 先加载默认数据, 再用 lang/<code>/ 下的同名文件覆盖.
    默认语言: 直接用默认数据.
    """
    lang_dir = seed / 'lang' / lang_code
    if lang_code == default_lang and not lang_dir.exists():
        return default_pages, default_data

    # 加载语言特定 pages (覆盖同名 key)
    lang_pages = dict(default_pages)
    pages_dir = lang_dir / 'pages'
    if pages_dir.exists():
        for f in pages_dir.glob('*.yaml'):
            lang_pages[f.stem] = _merge_page_content(lang_pages.get(f.stem, {}), _load_yaml(f))

    # 加载语言特定 data (覆盖同名 key)
    lang_data = dict(default_data)
    data_dir = lang_dir / 'data'
    if data_dir.exists():
        for f in data_dir.glob('*.yaml'):
            lang_data[f.stem] = _load_yaml(f)

    return lang_pages, lang_data


def _build_language_selector_page(output_root, base_url, settings, theme, year, meta, translations, languages=None):
    """在根路径生成语言选择首页.

    languages: 已过滤的启用语言列表，若不传则从 meta 读取全部.
    """
    if languages is None:
        languages = meta.get('languages', [])
    languages = _normalize_language_flags(languages)
    if not languages:
        return

    # 本页不走 Jinja2（手工字符串拼接），自动转义不生效。
    # 公司名/语言名等值都可能含用户输入，必须显式 escape，否则
    # 公司名填 <script>... 会在生成的根 index.html 里执行（存储型 XSS）。
    company_name = escape(settings.get('company', {}).get('name', ''))
    safe_base = escape(base_url.rstrip('/'))
    # 语言代码列表 JSON，供 JS 做浏览器语言匹配
    lang_codes_json = json.dumps([lang['code'] for lang in languages])
    default_lang_json = json.dumps(meta.get('default_language') or (languages[0].get('code') if languages else ''))

    html = '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
    html += '<meta charset="UTF-8">\n'
    html += '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    html += '<title>Language - ' + str(company_name) + '</title>\n'
    # 客户端 JS 读 navigator.language 智能跳转：精确匹配优先，前缀兜底，无匹配停留选择页
    # 用相对路径重定向（不用 base_url），兼容预览 /preview/<id>/ 和 CLI 构建 /
    html += '<script>'
    html += 'var L=' + lang_codes_json + ';'
    html += 'var D=' + default_lang_json + ';'
    html += '(function(){'
    html += 'if(D&&L.indexOf(D)!==-1){window.location.replace(D+"/");return;}'
    html += 'var u=(navigator.language||navigator.userLanguage||"");'
    html += 'var m=null;'
    html += 'for(var i=0;i<L.length;i++){if(L[i]===u){m=L[i];break;}}'
    html += 'if(!m){var p=u.split("-")[0];'
    html += 'for(var i=0;i<L.length;i++){if(L[i].indexOf(p)===0){m=L[i];break;}}}'
    html += 'if(m)window.location.replace(m+"/");'
    html += '})();'
    html += '</script>\n'
    html += '<link rel="stylesheet" href="' + str(safe_base) + '/static/css/main.css">\n'
    html += '</head>\n<body style="display:flex;align-items:center;justify-content:center;min-height:100vh;flex-direction:column;gap:2rem;">\n'
    html += '<h1>' + str(company_name) + '</h1>\n'
    html += '<p>Select your language / 選擇語言 / 选择语言</p>\n'
    html += '<div style="display:flex;gap:1rem;">\n'
    for lang in languages:
        html += '<a href="' + str(safe_base) + '/' + str(escape(lang['code'])) + '/" '
        html += 'style="padding:1rem 2rem;border:1px solid #e5e7eb;border-radius:8px;text-decoration:none;font-size:1.2rem;">'
        html += str(escape(lang.get('flag', ''))) + ' ' + str(escape(lang['name'])) + '</a>\n'
    html += '</div>\n</body>\n</html>'

    (output_root / 'index.html').write_text(html, encoding='utf-8')


def _write_site_seo_files(output_root, seo_records, settings, site_base_url):
    """写出 sitemap.xml / robots.txt / llms.txt。

    这些文件属于发布器职责，不能要求店主进入后台逐项配置。
    """
    today = datetime.now().date().isoformat()

    sitemap = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    seen = set()
    for record in seo_records:
        loc = record.get('loc')
        if not loc or loc in seen:
            continue
        seen.add(loc)
        sitemap.append('  <url>')
        sitemap.append(f'    <loc>{escape(loc)}</loc>')
        sitemap.append(f'    <lastmod>{today}</lastmod>')
        for alt in record.get('alternates') or []:
            sitemap.append(
                '    <xhtml:link rel="alternate" '
                f'hreflang="{escape(alt.get("lang", ""))}" '
                f'href="{escape(alt.get("url", ""))}"/>'
            )
        sitemap.append('  </url>')
    sitemap.append('</urlset>')
    (output_root / 'sitemap.xml').write_text('\n'.join(str(x) for x in sitemap) + '\n', encoding='utf-8')

    sitemap_url = _seo_url(site_base_url, '', '/sitemap.xml')
    robots = [
        '# AI 检索友好：小企业网站默认允许主流搜索与 AI 爬虫抓取。',
        'User-agent: GPTBot',
        'Allow: /',
        '',
        'User-agent: OAI-SearchBot',
        'Allow: /',
        '',
        'User-agent: ChatGPT-User',
        'Allow: /',
        '',
        'User-agent: ClaudeBot',
        'Allow: /',
        '',
        'User-agent: Claude-Web',
        'Allow: /',
        '',
        'User-agent: PerplexityBot',
        'Allow: /',
        '',
        'User-agent: Google-Extended',
        'Allow: /',
        '',
        'User-agent: Bytespider',
        'Allow: /',
        '',
        'User-agent: *',
        'Allow: /',
        'Disallow: /_preview/',
        '',
        f'Sitemap: {sitemap_url}',
    ]
    (output_root / 'robots.txt').write_text('\n'.join(robots) + '\n', encoding='utf-8')

    company_name = _company_name(settings)
    company_desc = _company_description(settings)
    llms = [f'# {company_name}', '']
    if company_desc:
        llms.extend([f'> {company_desc}', ''])
    grouped = {}
    for record in seo_records:
        group = 'Pages'
        if record.get('dataset_key') == 'products':
            group = 'Products'
        elif record.get('dataset_key') in ('posts', 'blog', 'articles'):
            group = 'Blog'
        elif record.get('dataset_key'):
            group = record.get('dataset_key').replace('_', ' ').title()
        grouped.setdefault(group, []).append(record)

    for group, records in grouped.items():
        llms.extend([f'## {group}', ''])
        for record in records:
            desc = record.get('description') or ''
            suffix = f': {desc}' if desc else ''
            llms.append(f'- [{record.get("title", "Untitled")}]({record.get("loc")}){suffix}')
        llms.append('')
    (output_root / 'llms.txt').write_text('\n'.join(llms).strip() + '\n', encoding='utf-8')


def _normalize_preview_filepath(filepath):
    rel = str(filepath or 'index.html').replace('\\', '/').lstrip('/')
    if not rel or rel == '.':
        return 'index.html'
    if rel.endswith('/'):
        return rel + 'index.html'
    if '.' not in rel.rsplit('/', 1)[-1]:
        return rel.rstrip('/') + '/index.html'
    return rel


def _default_detail_template(dataset_key):
    label = (dataset_key or 'item').replace('_', ' ').replace('-', ' ').title()
    return {
        'id': 'default',
        'name': f'默认{label}详情',
        'is_default': True,
        'modules': [{'type': 'item_data', 'variant': 'default', 'data': {}}],
        'required_fields': ['title', 'slug'],
        'optional_fields': ['cover', 'summary', 'body', 'detail_images', 'specs', 'category', 'tags'],
        'seo': {
            'title': '{title} - {site_name}',
            'description': '{summary}',
            'image': 'cover',
        },
    }


def _detail_templates_for_page(page, dataset_key):
    templates = page.get('detail_templates') if isinstance(page, dict) else None
    if not isinstance(templates, list) or not templates:
        return [_default_detail_template(dataset_key)]
    return [tpl for tpl in templates if isinstance(tpl, dict)] or [_default_detail_template(dataset_key)]


def _find_detail_template(page, dataset_key, template_id=None):
    templates = _detail_templates_for_page(page, dataset_key)
    if template_id:
        for tpl in templates:
            if str(tpl.get('id') or '') == str(template_id):
                return tpl
    for tpl in templates:
        if tpl.get('is_default') is True or str(tpl.get('is_default')).lower() == 'true':
            return tpl
    return templates[0] if templates else _default_detail_template(dataset_key)


def _resolve_detail_item_modules(item, page, dataset_key):
    """Return an item copy with effective detail modules injected.

    Existing item.modules stays highest priority so old per-item custom detail
    pages keep rendering exactly as before. When absent, fall back to the
    selected list-level detail template, then the default template, then the
    system item_data block.
    """
    item_copy = dict(item or {})
    existing_modules = item_copy.get('modules')
    if isinstance(existing_modules, list) and existing_modules:
        return item_copy

    tpl = _find_detail_template(page or {}, dataset_key, item_copy.get('template_id'))
    modules = tpl.get('modules') if isinstance(tpl, dict) else None
    if not isinstance(modules, list) or not modules:
        modules = [{'type': 'item_data', 'variant': 'default', 'data': {}}]
    item_copy['modules'] = copy.deepcopy(modules)
    item_copy['_detail_template_id'] = tpl.get('id', 'default') if isinstance(tpl, dict) else 'default'
    return item_copy


def _render_task_html(env, task, common, pages, data, meta, dataset_paths):
    tpl = env.get_template(task['template'])
    ctx = dict(common)
    lang_code = ctx.get('lang') or ''
    ctx['current_path'] = task['current_path']
    ctx['dataset_paths'] = {
        key: _seo_url(ctx.get('base_url', ''), lang_code, path)
        for key, path in dataset_paths.items()
    }
    ctx['page_key'] = task['page_key']
    ctx['lang_switch_path'] = task['current_path']

    if task['type'] == 'home':
        ctx['page'] = pages.get('home', {})
    elif task['type'] == 'list':
        ctx['page'] = pages.get(task['page_key'], {})
    elif task['type'] in ('page',):
        ctx['page'] = pages.get(task['page_key'], {})
    elif task['type'] == 'detail':
        ctx['page'] = pages.get(task['page_key'], {})
        ctx[task['var_name']] = _resolve_detail_item_modules(
            task['item'], ctx['page'], task.get('dataset_key') or task.get('page_key')
        )
        ctx['item'] = ctx[task['var_name']]
        current = task['current_path'].rstrip('/')
        ctx['lang_switch_path'] = current.rsplit('/', 1)[0] + '/' if '/' in current else '/'

    ctx['seo'] = _build_seo_context(task, ctx, common, meta)
    return tpl.render(**ctx)


def _render_for_language(env, tpl_html_dir, output_root, lang_code, common, pages, data, meta, seo_records=None):
    """为一种语言渲染所有页面 (菜单驱动).

    返回失败任务列表 [{lang, template, type, error}], 供 build_site 汇总,
    避免渲染失败被逐页静默吞掉、导致店主拿到缺页 ZIP/发布缺页站点而不自知。
    """
    lang_output = output_root / lang_code

    _common = dict(common)
    _common['lang'] = lang_code

    # 收集渲染任务 (菜单驱动). cap_menu_depth 防御深嵌套递归栈溢出.
    full_menu = menu_lib.cap_menu_depth(_common.get('settings', {}).get('menu', []))
    nav_menu = menu_lib.filter_hidden_for_nav(full_menu)
    _common = dict(_common)
    _common['settings'] = dict(_common.get('settings') or {})
    _common['settings']['menu'] = nav_menu
    menu_items = full_menu
    tasks = menu_lib.collect_render_tasks(menu_items, tpl_html_dir, data, pages)
    dataset_paths = {
        task.get('dataset_key'): task.get('current_path')
        for task in tasks
        if task.get('type') == 'list' and task.get('dataset_key') and task.get('current_path')
    }

    failures = []
    for task in tasks:
        try:
            tpl = env.get_template(task['template'])

            # 准备渲染上下文
            ctx = dict(_common)
            ctx['current_path'] = task['current_path']
            ctx['dataset_paths'] = {
                key: _seo_url(ctx.get('base_url', ''), lang_code, path)
                for key, path in dataset_paths.items()
            }

            ctx['page_key'] = task['page_key']
            # #27: 语言切换器默认把当前 current_path 拼到目标语言, 但详情页的 slug 是
            # 按语言各自生成的(zh 的 slug ≠ en 的 slug), 直接拼会 404。这里给详情页提供
            # 降级到"列表页"的 lang_switch_path; 其它页就用自身路径。模板的语言切换器改用它。
            ctx['lang_switch_path'] = task['current_path']
            if task['type'] == 'home':
                ctx['page'] = pages.get('home', {})
            elif task['type'] == 'list':
                ctx['page'] = pages.get(task['page_key'], {})
            elif task['type'] in ('page',):
                ctx['page'] = pages.get(task['page_key'], {})
            elif task['type'] == 'detail':
                ctx['page'] = pages.get(task['page_key'], {})
                ctx[task['var_name']] = _resolve_detail_item_modules(
                    task['item'], ctx['page'], task.get('dataset_key') or task.get('page_key')
                )
                ctx['item'] = ctx[task['var_name']]
                # 详情页降级: 去掉末尾 slug 段, 退到列表页(各语言都有列表页, 不会 404)
                _p = task['current_path'].rstrip('/')
                ctx['lang_switch_path'] = _p.rsplit('/', 1)[0] + '/' if '/' in _p else '/'

            ctx['seo'] = _build_seo_context(task, ctx, common, meta)

            rendered = tpl.render(**ctx)
            out = lang_output / task['output_path']
            # 越界兜底: detail 页的 output_path 含店主可编辑的 slug,
            # 若 slug 形如 ../../ 会逃出 output 根写到任意位置。即便 routes
            # 层已校验新 slug, 历史脏数据仍可能存在, 这里写文件前强制断言。
            try:
                out.resolve().relative_to(output_root.resolve())
            except ValueError:
                current_app.logger.error(
                    '跳过越界输出路径 %s (lang=%s): 解析后逃出 output 根',
                    task.get('output_path'), lang_code,
                )
                failures.append({'lang': lang_code, 'template': task.get('template'),
                                 'type': task.get('type'), 'error': '输出路径越界, 已跳过'})
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(rendered, encoding='utf-8')
            if seo_records is not None:
                seo_records.append({
                    'lang': lang_code,
                    'type': task.get('type'),
                    'page_key': task.get('page_key'),
                    'dataset_key': task.get('dataset_key'),
                    'loc': ctx['seo'].get('canonical_url'),
                    'alternates': ctx['seo'].get('alternate_urls') or [],
                    'title': ctx['seo'].get('title'),
                    'description': ctx['seo'].get('description'),
                })
        except Exception as e:
            current_app.logger.error(
                '页面 %s (type=%s, lang=%s) 渲染失败: %s',
                task.get('template'), task.get('type'), lang_code, e,
            )
            failures.append({'lang': lang_code, 'template': task.get('template'),
                             'type': task.get('type'), 'error': str(e)})
    return failures


def render_site_page(site_id, filepath='index.html', base_url='', lang_code=None,
                     draft_page_key=None, draft_page=None, draft_settings=None, draft_data=None):
    """Render a single page for editor live preview without writing output files."""
    site = Site.query.get(site_id)
    if not site:
        raise ValueError(f'站点不存在: {site_id}')

    settings, pages, data = _gather_site_data(site_id, site.template_name)
    if isinstance(draft_settings, dict):
        settings = _deep_merge(settings, draft_settings)
    if isinstance(draft_data, dict):
        data = _deep_merge(data, draft_data)

    site_base_url = _site_base_url(site, base_url)
    tpl_root, tpl_html_dir, _tpl_static_dir = _template_paths(site.template_name)
    meta = _load_yaml(tpl_root / 'meta.yaml')
    translations = _load_translations(tpl_root)

    if 'menu' not in settings or not settings.get('menu'):
        settings['menu'] = meta.get('default_menu', [])
    settings['menu'] = menu_lib.ensure_home(
        menu_lib.normalize_for_render(
            menu_lib.upgrade_old_format(settings['menu'], meta.get('datasets', []))
        )
    )
    theme_default = meta.get('default_theme', {})
    theme = {**theme_default, **(settings.get('theme') or {})}
    env = _create_template_env(tpl_root, tpl_html_dir, site.template_name)

    languages = _normalize_language_flags(meta.get('languages', []))
    enabled_codes = site.enabled_languages or [l['code'] for l in languages]
    languages = [l for l in languages if l['code'] in enabled_codes] or languages
    default_lang = meta.get('default_language', languages[0]['code'] if languages else (site.default_language or ''))

    rel = _normalize_preview_filepath(filepath)
    if languages:
        if not lang_code:
            first = rel.split('/', 1)[0]
            if first in [l['code'] for l in languages]:
                lang_code = first
                rel = rel.split('/', 1)[1] if '/' in rel else 'index.html'
        lang_code = lang_code or default_lang

        default_pages, default_data = _load_lang_overrides(site_id, default_lang, default_lang, pages, data)
        if lang_code == default_lang:
            lang_pages, lang_data = default_pages, default_data
        else:
            lang_pages, lang_data = _load_lang_overrides(site_id, lang_code, default_lang, default_pages, default_data)
        if isinstance(draft_data, dict):
            lang_data = _deep_merge(lang_data, draft_data)
        if isinstance(draft_page, dict) and draft_page_key:
            lang_pages[draft_page_key] = _merge_page_content(lang_pages.get(draft_page_key, {}), draft_page)

        fallback_settings_to_default = lang_code == default_lang
        lang_settings = dict(settings)
        label_map = _language_label_map(settings, lang_code, default_lang, fallback_settings_to_default)
        menu_override_key = f'menu_{lang_code}'
        if menu_override_key in settings and settings.get(menu_override_key) and not label_map:
            lang_settings['menu'] = menu_lib.ensure_home(
                menu_lib.normalize_for_render(
                    menu_lib.upgrade_old_format(settings[menu_override_key], meta.get('datasets', []))
                )
            )
        elif label_map:
            lang_settings['menu'] = menu_lib.apply_labels(settings.get('menu', []), label_map)

        footer_override = _language_override(settings, 'footer', lang_code, default_lang, fallback_settings_to_default)
        if footer_override:
            lang_settings['footer'] = footer_override
        company_override = _language_override(settings, 'company', lang_code, default_lang, fallback_settings_to_default)
        if company_override:
            lang_settings['company'] = _merge_language_settings_section(settings.get('company'), company_override)
        contact_override = _language_override(settings, 'contact', lang_code, default_lang, fallback_settings_to_default)
        if contact_override:
            lang_settings['contact'] = _merge_language_settings_section(settings.get('contact'), contact_override)

        render_pages = lang_pages
        render_data = lang_data
        render_settings = lang_settings
        render_lang = lang_code
        t = translations.get(lang_code, {})
    else:
        if isinstance(draft_page, dict) and draft_page_key:
            pages[draft_page_key] = _merge_page_content(pages.get(draft_page_key, {}), draft_page)
        render_pages = pages
        render_data = data
        render_settings = settings
        render_lang = site.default_language or ''
        t = {}

    full_menu = menu_lib.cap_menu_depth(render_settings.get('menu', []))
    nav_menu = menu_lib.filter_hidden_for_nav(full_menu)
    common_settings = dict(render_settings)
    common_settings['menu'] = nav_menu
    common = {
        'settings': common_settings,
        'theme': theme,
        'year': datetime.now().year,
        'lang': render_lang,
        'base_url': base_url.rstrip('/'),
        'site_base_url': site_base_url,
        't': t,
        'languages': languages,
        'products_categories': _extract_products_categories(render_data),
        'products': _extract_products_items(render_data),
        'portfolio': render_data.get('portfolio', []),
        'posts': render_data.get('posts', []),
        'features': render_data.get('features', []),
        'all_datasets': render_data,
        'site_id': site_id,
        'platform_api_url': _get_platform_base_url(),
    }

    tasks = menu_lib.collect_render_tasks(full_menu, tpl_html_dir, render_data, render_pages)
    dataset_paths = {
        task.get('dataset_key'): task.get('current_path')
        for task in tasks
        if task.get('type') == 'list' and task.get('dataset_key') and task.get('current_path')
    }
    task = next((item for item in tasks if item.get('output_path') == rel), None)
    if task is None and rel == 'index.html':
        task = next((item for item in tasks if item.get('type') == 'home'), None)
    if task is None:
        raise FileNotFoundError(rel)
    return _render_task_html(env, task, common, render_pages, render_data, meta, dataset_paths)


def build_site(site_id, base_url='', report=None):
    """生成站点到 output/<site_id>/. 返回输出根目录.

    支持多语言: 每种语言一个子目录, 根路径生成语言选择首页.

    base_url: 站内链接和静态资源的前缀.
              发布到 CDN 时为 '' (站点在根),
              本地预览时为 '/preview/<id>'.
    report:   #13 可选 list, 传入则收集所有渲染失败任务 [{lang,template,type,error}]。
              零侵入: 现有调用方不传即忽略; export/发布传入后可据此提示店主"N 页缺失",
              避免缺页 ZIP/缺页站点被静默发布。失败也会统一记 warning 日志。
    """
    site = Site.query.get(site_id)
    if not site:
        raise ValueError(f'站点不存在: {site_id}')

    settings, pages, data = _gather_site_data(site_id, site.template_name)
    site_settings = _load_yaml(Path(current_app.config['SITES_DIR']) / str(site_id) / 'settings.yaml')
    site_base_url = _site_base_url(site, base_url)

    _all_failures = []  # #13: 收集各语言渲染失败任务
    seo_records = []

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
    # Windows 下 rmtree 极易因文件锁定/目录竞态抛异常；
    # 清理失败无所谓，后面 copytree(dirs_exist_ok=True) 会原地覆盖写入。
    if output_root.exists():
        try:
            shutil.rmtree(output_root, ignore_errors=True)
        except Exception:
            pass
    output_root.mkdir(parents=True, exist_ok=True)

    # 复制 static/
    if tpl_static_dir.exists():
        shutil.copytree(tpl_static_dir, output_root / 'static', dirs_exist_ok=True)

    # 复制店主上传的 assets/
    site_assets = Path(current_app.config['SITES_DIR']) / str(site_id) / 'assets'
    if site_assets.exists():
        shutil.copytree(site_assets, output_root / 'assets', dirs_exist_ok=True)

    languages = _normalize_language_flags(meta.get('languages', []))
    # 按站点启用的语言过滤（从 DB enabled_languages 读取，兜底显示全部）
    enabled_codes = site.enabled_languages or [l['code'] for l in languages]
    languages = [l for l in languages if l['code'] in enabled_codes]
    # 兜底：如果过滤后为空（旧站点 enabled_languages 可能与模板不一致），使用全部语言
    if not languages:
        languages = _normalize_language_flags(meta.get('languages', []))
    # 提取 product_categories 和 products 供导航用
    default_lang = meta.get('default_language', languages[0]['code'] if languages else 'zh-CN')
    default_pages_for_lang = pages
    default_data_for_lang = data
    if languages:
        default_pages_for_lang, default_data_for_lang = _load_lang_overrides(
            site_id, default_lang, default_lang, pages, data
        )

    year = datetime.now().year

    if languages:
        # 多语言模式
        _build_language_selector_page(output_root, base_url, settings, theme, year, meta, translations, languages)

        for lang_opt in languages:
            lang_code = lang_opt['code']
            t_data = translations.get(lang_code, {})
            fallback_settings_to_default = lang_code == default_lang

            # 加载语言特定数据，回退到默认语言
            lang_pages, lang_data = _load_lang_overrides(
                site_id, lang_code, default_lang, default_pages_for_lang, default_data_for_lang
            )

            # 语言特定菜单：menu_labels（新格式）优先于 menu_<lang>（旧格式）
            # 当两者同时存在时用新格式，否则旧格式向后兼容。
            lang_settings = dict(settings)
            menu_override_key = f'menu_{lang_code}'
            label_map = _language_label_map(settings, lang_code, default_lang, fallback_settings_to_default)
            if menu_override_key in settings and settings.get(menu_override_key) and not label_map:
                # 旧格式: 语言独立的完整菜单树（仅当该语言没有 menu_labels 时才用）
                lang_settings['menu'] = menu_lib.ensure_home(
                    menu_lib.normalize_for_render(
                        menu_lib.upgrade_old_format(settings[menu_override_key], meta.get('datasets', []))
                    )
                )
            elif label_map:
                # 新格式: 共享 menu 结构 + menu_labels 覆盖标签
                shared_menu = settings.get('menu', [])
                lang_settings['menu'] = menu_lib.apply_labels(shared_menu, label_map)
            # else: 没有语言特定菜单, 保持 shared_menu 不变 (已在 settings['menu'] 中)
            footer_override_key = f'footer_{lang_code}'
            footer_override = _language_override(settings, 'footer', lang_code, default_lang, fallback_settings_to_default)
            if footer_override:
                lang_settings['footer'] = footer_override
            company_override = _language_override(settings, 'company', lang_code, default_lang, fallback_settings_to_default)
            if company_override:
                lang_settings['company'] = _merge_language_settings_section(
                    settings.get('company'), company_override
                )
            contact_override = _language_override(settings, 'contact', lang_code, default_lang, fallback_settings_to_default)
            if contact_override:
                lang_settings['contact'] = _merge_language_settings_section(
                    settings.get('contact'), contact_override
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
                'site_base_url': site_base_url,
                't': t_data,
                'languages': languages,
                'products_categories': lang_products_categories,
                'products': lang_products_items,
                'portfolio': lang_data.get('portfolio', []),
                'posts': lang_data.get('posts', []),
                'features': lang_data.get('features', []),
                'all_datasets': lang_data,
                # contact_form 内置留言所需：平台 API 地址 + 站点 ID
                'site_id': site_id,
                'platform_api_url': _get_platform_base_url(),
            }

            _all_failures.extend(
                _render_for_language(env, tpl_html_dir, output_root, lang_code, common, lang_pages, lang_data, meta, seo_records)
            )
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
            'site_base_url': site_base_url,
            't': {},
            'languages': [],
            'products_categories': products_categories,
            'products': products_items,
            'portfolio': data.get('portfolio', []),
            'posts': data.get('posts', []),
            'features': data.get('features', []),
            'all_datasets': data,
            # contact_form 内置留言所需：平台 API 地址 + 站点 ID
            'site_id': site_id,
            'platform_api_url': _get_platform_base_url(),
        }
        _all_failures.extend(
            _render_for_language(env, tpl_html_dir, output_root, '', common, pages, data, meta, seo_records)
        )

    _write_site_seo_files(output_root, seo_records, settings, site_base_url)

    # #13: 汇总缺页。有失败时统一记 warning, 并填入调用方传入的 report。
    if _all_failures:
        current_app.logger.warning(
            '站点 %s 构建完成但有 %d 个页面渲染失败(已缺页): %s',
            site_id, len(_all_failures),
            '; '.join(f"{f['lang'] or '默认'}:{f['template']}" for f in _all_failures),
        )
        if report is not None:
            report.extend(_all_failures)

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
    # Windows 下 rmtree 极易因文件锁定/目录竞态抛异常；
    # 清理失败无所谓，后面 copytree(dirs_exist_ok=True) 会原地覆盖写入。
    if output_root.exists():
        try:
            shutil.rmtree(output_root, ignore_errors=True)
        except Exception:
            pass
    output_root.mkdir(parents=True, exist_ok=True)

    if tpl_static_dir.exists():
        shutil.copytree(tpl_static_dir, output_root / 'static', dirs_exist_ok=True)

    # 复制种子数据中的上传资源（如 /assets/uploads/xxx.webp），
    # 否则模板预览页中引用的图片/video 全部 404
    seed_assets = seed / 'assets'
    if seed_assets.exists():
        shutil.copytree(seed_assets, output_root / 'assets', dirs_exist_ok=True)

    languages = _normalize_language_flags(meta.get('languages', []))
    products_categories = _extract_products_categories(data)
    products_items = _extract_products_items(data)
    year = datetime.now().year
    site_base_url = _site_base_url(None, base_url)
    seo_records = []

    if languages:
        _build_language_selector_page(output_root, base_url, settings, theme, year, meta, translations)
        default_lang = meta.get('default_language', languages[0]['code'] if languages else 'zh-CN')
        for lang_opt in languages:
            lang_code = lang_opt['code']
            t_data = translations.get(lang_code, {})
            fallback_settings_to_default = lang_code == default_lang

            # 加载语言特定 pages/data（seed_data/lang/<code>/ 覆盖默认）
            lang_pages, lang_data = _load_seed_lang_overrides(
                seed, lang_code, default_lang, pages, data
            )

            # 语言特定 settings 覆盖（menu_en, footer_en, company_en, contact_en）
            lang_settings = dict(settings)
            menu_override_key = f'menu_{lang_code}'
            label_map = _language_label_map(settings, lang_code, default_lang, fallback_settings_to_default)
            if menu_override_key in settings and settings[menu_override_key] and not label_map:
                lang_settings['menu'] = menu_lib.ensure_home(
                    menu_lib.normalize_for_render(
                        menu_lib.upgrade_old_format(settings[menu_override_key], meta.get('datasets', []))
                    )
                )
            elif label_map:
                shared_menu = settings.get('menu', [])
                lang_settings['menu'] = menu_lib.apply_labels(shared_menu, label_map)
            footer_override = _language_override(settings, 'footer', lang_code, default_lang, fallback_settings_to_default)
            if footer_override:
                lang_settings['footer'] = footer_override
            company_override = _language_override(settings, 'company', lang_code, default_lang, fallback_settings_to_default)
            if company_override:
                lang_settings['company'] = _merge_language_settings_section(
                    settings.get('company'), company_override
                )
            contact_override = _language_override(settings, 'contact', lang_code, default_lang, fallback_settings_to_default)
            if contact_override:
                lang_settings['contact'] = _merge_language_settings_section(
                    settings.get('contact'), contact_override
                )

            # 提取语言特定的产品分类和列表
            lang_products_categories = _extract_products_categories(lang_data)
            lang_products_items = _extract_products_items(lang_data)

            common = {
                'settings': lang_settings, 'theme': theme,
                'year': year, 'lang': lang_code,
                'base_url': base_url.rstrip('/'),
                'site_base_url': site_base_url,
                't': t_data, 'languages': languages,
                'products_categories': lang_products_categories,
                'products': lang_products_items,
                'portfolio': lang_data.get('portfolio', []),
                'posts': lang_data.get('posts', []),
                'features': lang_data.get('features', []),
                'all_datasets': lang_data,
                'site_id': 0,  # 预览无真实站点, 留 0
                'platform_api_url': _get_platform_base_url(),
            }
            _render_for_language(env, tpl_html_dir, output_root, lang_code, common, lang_pages, lang_data, meta, seo_records)
    else:
        common = {
            'settings': settings, 'theme': theme,
            'year': year, 'lang': 'zh-CN',
            'base_url': base_url.rstrip('/'),
            'site_base_url': site_base_url,
            't': {}, 'languages': [],
            'products_categories': products_categories,
            'products': products_items,
            'portfolio': data.get('portfolio', []),
            'posts': data.get('posts', []),
            'features': data.get('features', []),
            'site_id': 0,  # 预览无真实站点
            'platform_api_url': _get_platform_base_url(),
        }
        _render_for_language(env, tpl_html_dir, output_root, '', common, pages, data, meta, seo_records)

    _write_site_seo_files(output_root, seo_records, settings, site_base_url)

    return output_root
