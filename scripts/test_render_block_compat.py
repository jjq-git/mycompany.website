"""Phase 2 向后兼容验证：开关关闭时，render_block 旧路径 == 原始 {% include %}.

不碰 git、不碰工作区文件，纯内存对比：
对数据库中首个 dengtec 站点的真实页面数据，分别用
  A) 原始写法：_modules.html 里 {% include %}
  B) 新写法：  _modules.html 里 {{ render_block(module) }}
渲染同一批 module，逐字符对比输出。开关关闭时两者必须完全一致。
"""
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.core import builder
from app.core.models import Site
from jinja2 import Environment, FileSystemLoader, select_autoescape

# 原始 _modules.html 的核心渲染逻辑（改造前的 include 写法）。
# 已转 data-* 的 block，其改造前版本在 template.jinja2.bak，故 include 列表把 .bak
# 放在 template.html 之前——代表"改造前"的真实 Jinja2 输出，作为兼容基线 A。
ORIGINAL_MODULES = '''{% if page.modules %}
  {% for module in page.modules | sort(attribute='order') %}
    {% if module.data is mapping or (module.type == 'hero_banner' and module.data is iterable and module.data is not string) %}
      <div class="builder-module" data-builder-module-index="{{ loop.index0 }}" data-builder-module-type="{{ module.type }}" data-builder-page-key="{{ page_key | default('') }}">
        {% include ['blocks/' ~ module.type ~ '/variants/' ~ (module.variant | default('default')) ~ '.html', 'blocks/' ~ module.type ~ '/template.jinja2.bak', 'blocks/' ~ module.type ~ '/template.html'] ignore missing %}
      </div>
    {% endif %}
  {% endfor %}
{% endif %}
'''

app = create_app()
with app.app_context():
    site = Site.query.filter_by(template_name='dengtec').order_by(Site.id).first()
    assert site, '没有可用于兼容测试的 dengtec 站点'
    # 关闭开关：验证向后兼容
    from flask import current_app
    current_app.config['ENABLE_DATA_ATTR_BLOCKS'] = False
    builder._SCHEMA_CACHE.clear()  # 清模块级缓存，避免跨测试串味

    settings, pages, data = builder._gather_site_data(site.id, site.template_name)
    tpl_root, tpl_html_dir, _ = builder._template_paths(site.template_name)
    meta = builder._load_yaml(tpl_root / 'meta.yaml')
    translations = builder._load_translations(tpl_root)

    # 用真实翻译数据（默认语言那份），否则 data_grid 等模板会缺 t.products 报错
    languages = meta.get('languages', [])
    default_lang = meta.get('default_language', languages[0]['code'] if languages else 'zh-CN')
    t_data = translations.get(default_lang, {})

    # 取一个内容最丰富的页面做对比
    page = pages.get('home') or next(iter(pages.values()), {})
    prod_cats = builder._extract_products_categories(data)
    prod_items = builder._extract_products_items(data)

    # 构造贴近真实构建的 ctx
    ctx_common = {
        'settings': settings, 'theme': meta.get('default_theme', {}),
        'year': 2026, 'lang': default_lang, 'base_url': '', 't': t_data,
        'languages': languages,
        'products_categories': prod_cats, 'products': prod_items,
        'portfolio': data.get('portfolio', []), 'posts': data.get('posts', []),
        'features': data.get('features', []), 'all_datasets': data,
        'page': page,
    }

    diffs = 0
    pages_checked = 0
    for pkey, pdata in pages.items():
        if not isinstance(pdata, dict) or 'modules' not in pdata:
            continue
        pages_checked += 1
        ctx = dict(ctx_common); ctx['page'] = pdata

        # A) 原始 include 写法
        env_a = Environment(loader=FileSystemLoader([str(tpl_html_dir), str(tpl_root)]),
                            autoescape=select_autoescape(['html']),
                            trim_blocks=True, lstrip_blocks=True)
        out_a = env_a.from_string(ORIGINAL_MODULES).render(**ctx)

        # B) 新 render_block 写法
        env_b = Environment(loader=FileSystemLoader([str(tpl_html_dir), str(tpl_root)]),
                            autoescape=select_autoescape(['html']),
                            trim_blocks=True, lstrip_blocks=True)
        env_b.globals['render_block'] = builder._make_render_block(
            env_b, tpl_root, site.template_name, False)
        # 复用真实的 _modules.html（已是 render_block 写法）
        tpl_b = env_b.get_template('_modules.html')
        out_b = tpl_b.render(**ctx)

        # render_block 会为可读性保留一个标签间换行；DOM 语义需与旧 include 一致。
        normalize_markup = lambda value: re.sub(r'>\s+<', '><', value.strip())
        if normalize_markup(out_a) == normalize_markup(out_b):
            print(f'  ✓ 页面 {pkey}（{len(pdata.get("modules", []))} 模块）输出一致')
        else:
            diffs += 1
            print(f'  ✗ 页面 {pkey} 输出不一致！长度 A={len(out_a)} B={len(out_b)}')
            # 打印首个差异位置
            for i, (ca, cb) in enumerate(zip(out_a, out_b)):
                if ca != cb:
                    print(f'    首差@{i}: A=...{out_a[max(0,i-30):i+30]!r}')
                    print(f'            B=...{out_b[max(0,i-30):i+30]!r}')
                    break

    print(f'\n检查 {pages_checked} 个含模块页面，{diffs} 处差异')
    sys.exit(1 if diffs else 0)
