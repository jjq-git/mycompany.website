"""验证 section_title 转 data-* 后的解析与渲染。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.core import block_parser as bp, block_renderer as br, template_loader

app = create_app()
with app.app_context():
    # 1. scan_blocks 应把 section_title 识别为 data-*
    blocks = {b['name']: b for b in template_loader.scan_blocks('dengtec')}
    st = blocks['section_title']
    print(f"section_title is_data_attr = {st['is_data_attr']}")
    assert st['is_data_attr'], 'section_title 应被识别为 data-* 声明式'
    schema = st['schema']
    print(f"  根类型={schema.root_type}, hideable={schema.hideable}, style={schema.style_tokens}")
    print(f"  字段: {[(f.name, f.type, f.href_field) for f in schema.fields]}")
    assert schema.root_type == 'group'
    assert schema.hideable
    assert schema.style_tokens == ['text-align']
    names = {f.name for f in schema.fields}
    assert names == {'tag', 'title', 'desc', 'btn'}, f'字段不对: {names}'

    # 2. 完整数据渲染
    html = (Path(app.config['TEMPLATES_DIR']) / 'dengtec' / 'blocks'
            / 'section_title' / 'template.html').read_text(encoding='utf-8')
    out = br.render(html, schema, {
        'tag': '关于我们', 'title': '德恩基电子科技',
        'desc': '提供展示道具行业的电子产品解决方案',
        'btn': '联系我们', 'btn_url': '/contact',
        'style_text-align': 'left',
    })
    print('\n--- 完整数据渲染 ---')
    print(out)
    assert '关于我们' in out and '德恩基电子科技' in out
    assert 'href="/contact"' in out and '联系我们' in out
    assert '--text-align: left' in out
    assert 'data-' not in out, 'data-* 未清理干净'

    # 3. 部分字段为空 → 自动隐藏（无标签、无按钮）
    out2 = br.render(html, schema, {'title': '只有标题'})
    print('\n--- 仅标题（tag/desc/btn 应隐藏）---')
    print(out2)
    assert '只有标题' in out2
    # tag/desc/btn 元素应带 hidden
    assert out2.count('hidden') >= 3, f'空字段应隐藏，实际 hidden 数={out2.count("hidden")}'

    # 4. 整块隐藏
    out3 = br.render(html, schema, {'title': 'X', '_hidden': True})
    assert '<section' in out3 and ' hidden' in out3.split('>')[0]
    print('\n✓ section_title data-* 全部验证通过')
