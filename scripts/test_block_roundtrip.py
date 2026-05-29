"""Phase 1 往返测试：用 Block 示例库 mock HTML 验证 parse → render.

方案七节要求：确认输出与输入语义一致。
直接跑 python scripts/test_block_roundtrip.py，无需起 Flask。

测试用例覆盖：text/image/data-href、group、list(手动)、list(数据集)、grid、
data-style 注入、data-hideable、叶子空值自动隐藏、data-* 全部清理。
"""
import sys
from pathlib import Path

# 让脚本能 import app.core
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core import block_parser as bp
from app.core import block_renderer as br

PASS, FAIL = 0, 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  ✓ {name}')
    else:
        FAIL += 1
        print(f'  ✗ {name}  {detail}')


def render(html, data, ctx=None):
    schema = bp.parse(html)
    return schema, br.render(html, schema, data, ctx or {})


print('=== 1. Hero（group + text + data-href + data-style=bg + hideable）===')
hero = '''<section data-name="hero" data-type="group" data-style="bg" data-hideable style="--bg: url('hero.jpg')">
  <h1 data-name="title" data-type="text">用技术驱动未来</h1>
  <p data-name="subtitle" data-type="text">一句话价值主张</p>
  <a data-name="cta" data-type="text" data-href="ctaLink">立即咨询</a>
</section>'''
schema, out = render(hero, {
    'title': '德恩基电子', 'subtitle': '展示道具行业电子产品',
    'cta': '联系我们', 'ctaLink': '/contact', 'style_bg': "url('/assets/bg.jpg')",
})
check('schema 根类型 group', schema.root_type == 'group')
check('schema 含 3 个字段', len(schema.fields) == 3, f'实际 {len(schema.fields)}')
check('schema 识别 hideable', schema.hideable)
check('schema 识别 style token bg', schema.style_tokens == ['bg'])
check('标题注入', '德恩基电子' in out)
check('副标题注入', '展示道具行业电子产品' in out)
check('CTA href 注入', 'href="/contact"' in out)
check('CTA 文字注入', '联系我们' in out)
check('样式 CSS 变量注入', '--bg:' in out and '/assets/bg.jpg' in out)
check('输出无 data-* 残留', 'data-' not in out, out)

print('\n=== 2. Features（list 手动 + group 项 + data-style=cols）===')
features = '''<section data-name="features" data-type="list" data-hideable data-style="cols" style="--cols: 3">
  <div data-name="feature" data-type="group">
    <img data-name="icon" data-type="image" src="icon1.svg">
    <h3 data-name="title" data-type="text">高性能</h3>
    <p data-name="desc" data-type="text">说明文字</p>
  </div>
</section>'''
schema, out = render(features, {
    'features': [
        {'icon': '/a.svg', 'title': '稳定', 'desc': '5年不坏'},
        {'icon': '/b.svg', 'title': '快速', 'desc': '首屏1秒'},
    ],
    'style_cols': '4',
})
check('schema 根类型 list', schema.root_type == 'list')
check('schema 手动模式（source 为 None）', schema.source is None)
check('项模板字段数 3', len(schema.fields) == 3, f'实际 {len(schema.fields)}')
check('展开 2 条', out.count('data-type') == 0 and out.count('<div') == 2, out)
check('第1条标题', '稳定' in out)
check('第2条标题', '快速' in out)
check('第1条图片src', '/a.svg' in out)
check('cols 样式注入为4', '--cols: 4' in out)
check('无 data-* 残留', 'data-' not in out)

print('\n=== 3. Logo 墙（grid + 项模板根直接是 image 叶子）===')
logos = '''<section data-name="logo-wall" data-type="grid" data-cols="6" data-hideable>
  <img data-name="logo" data-type="image" data-href="logoLink" src="c1.png">
</section>'''
schema, out = render(logos, {
    'logo-wall': [
        {'logo': '/c1.png', 'logoLink': 'https://a.com'},
        {'logo': '/c2.png'},
    ],
})
check('schema 根类型 grid', schema.root_type == 'grid')
check('schema cols=6', schema.cols == 6)
check('展开 2 张图', out.count('<img') == 2, out)
check('第1张 href', 'https://a.com' in out)
check('第1张 src', '/c1.png' in out)
check('无 data-* 残留', 'data-' not in out)

print('\n=== 4. News（list 数据集驱动 data-source）===')
news = '''<section data-name="news" data-type="list" data-source data-page-size="9" data-style="cols" style="--cols: 3">
  <article data-name="post" data-type="group">
    <img data-name="cover" data-type="image" data-href="url">
    <h3 data-name="title" data-type="text" data-href="url">新闻标题</h3>
    <span data-name="date" data-type="text">2026-05-27</span>
  </article>
</section>'''
schema, out = render(news, {'dataset': 'posts'}, ctx={
    'all_datasets': {'posts': {'items': [
        {'cover': '/n1.jpg', 'title': '公司动态1', 'date': '2026-01-01', 'url': '/news/1'},
        {'cover': '/n2.jpg', 'title': '公司动态2', 'date': '2026-02-02', 'url': '/news/2'},
    ]}},
})
check('schema source 为空串（数据集驱动）', schema.source == '')
check('schema page_size=9', schema.page_size == 9)
check('数据集展开 2 条', out.count('<article') == 2, out)
check('标题来自数据集', '公司动态1' in out and '公司动态2' in out)
check('详情链接注入', '/news/1' in out)
check('无 data-* 残留', 'data-' not in out)

print('\n=== 5. 叶子空值自动隐藏 ===')
contact = '''<section data-name="contact" data-type="group">
  <span data-name="addr" data-type="text">地址</span>
  <span data-name="phone" data-type="text">电话</span>
  <span data-name="email" data-type="text" data-href="emailLink">email</span>
</section>'''
schema, out = render(contact, {'addr': '北京', 'phone': '', 'email': 'hi@x.com', 'emailLink': 'mailto:hi@x.com'})
check('地址注入', '北京' in out)
check('空电话加 hidden', 'hidden' in out, out)
check('email 注入+href', 'hi@x.com' in out and 'mailto:hi@x.com' in out)

print('\n=== 6. data-source="products"（限定数据集）===')
prod = '''<section data-name="products" data-type="list" data-source="products" data-style="cols" style="--cols: 4">
  <div data-name="product" data-type="group">
    <img data-name="img" data-type="image" data-href="url">
    <h4 data-name="name" data-type="text" data-href="url">产品名</h4>
  </div>
</section>'''
schema, out = render(prod, {}, ctx={
    'all_datasets': {'products': {'categories': [], 'items': [
        {'img': '/p1.jpg', 'name': '静音舱A', 'url': '/p/a'},
    ]}},
})
check('schema source=products', schema.source == 'products')
check('限定数据集展开', '静音舱A' in out and '/p1.jpg' in out)
check('无 data-* 残留', 'data-' not in out)

print('\n=== 7. hideable 隐藏标记 ===')
schema, out = render(hero, {'title': 'X', '_hidden': True})
check('hideable=True 且 _hidden → 加 hidden', 'hidden' in out, out)
schema, out2 = render(hero, {'title': 'X'})
check('hideable 但未隐藏 → 无 hidden', '<section' in out2 and ' hidden' not in out2.split('>')[0])

print('\n=== 8. P0-2 回归：文本与子元素交错不重排 ===')
# 注：富文本/含内联标签的文本字段，渲染应保持原始顺序
mixed = '<div data-name="m" data-type="group"><p data-name="body" data-type="richtext">x</p></div>'
schema, out = render(mixed, {'body': '前文<a>链接</a>后文'})
check('richtext 内联顺序保持', '前文<a>链接</a>后文' in out, out)

print('\n=== 9. P0-3 回归：模板静态属性里的 HTML 实体不被破坏 ===')
# 注入 map（裸 & 的真实 URL），验证注入值里的 & 被正确转义为 &amp;（一次，不双重）
ent = '<section data-name="s" data-type="group"><iframe data-name="map" data-type="embed" title="say &quot;hi&quot;" src="placeholder"></iframe></section>'
schema, out = render(ent, {'map': 'https://m.x/e?a=1&b=2'})
check('注入 src 的裸 & 转义为 &amp;（不双重）', 'a=1&amp;b=2' in out and '&amp;amp;' not in out, out)
# 另测：静态 title 的实体保留
ent2 = '<span data-name="t" data-type="text" title="say &quot;hi&quot;">x</span>'
s2 = bp.parse('<section data-name="s" data-type="group">' + ent2 + '</section>')
out2 = br.render('<section data-name="s" data-type="group">' + ent2 + '</section>', s2, {'t': 'hello'})
check('静态 title 的 &quot; 实体保留', '&quot;hi&quot;' in out2, out2)

print('\n=== 10. P0-1 回归：样式值 XSS 被白名单挡掉 ===')
xss = '<section data-name="s" data-type="group" data-style="bg-color"><span data-name="t" data-type="text">hi</span></section>'
schema, out = render(xss, {'t': 'hi', 'style_bg-color': 'red"; onload="alert(1)'})
check('非法颜色值被拒绝（无 onload 注入）', 'onload' not in out, out)
schema, out2 = render(xss, {'t': 'hi', 'style_bg-color': '#ff0000'})
check('合法颜色值放行', '--bg-color: #ff0000' in out2, out2)
# select 白名单
sel = '<section data-name="s" data-type="list" data-style="cols" style="--cols:3"><div data-name="i" data-type="group"><span data-name="t" data-type="text">x</span></div></section>'
schema, out3 = render(sel, {'s': [{'t': 'a'}], 'style_cols': '99; evil'})
check('非法 cols 值被拒绝', 'evil' not in out3, out3)

print('\n=== 11. P1-5 回归：data-href 危险 scheme 被拦 ===')
hrefblk = '<section data-name="s" data-type="group"><a data-name="x" data-type="text" data-href="u">go</a></section>'
schema, out = render(hrefblk, {'x': 'go', 'u': 'javascript:alert(1)'})
check('javascript: 被拦', 'javascript:' not in out, out)
schema, out2 = render(hrefblk, {'x': 'go', 'u': '/contact'})
check('正常相对链接放行', 'href="/contact"' in out2, out2)

print('\n=== 12. P1-1 回归：空列表容器自动隐藏 ===')
emptylist = '<section data-name="news" data-type="list"><article data-name="post" data-type="group"><h3 data-name="t" data-type="text">x</h3></article></section>'
schema, out = render(emptylist, {'news': []})
check('空列表容器加 hidden', 'hidden' in out.split('>')[0], out)

print(f'\n{"="*40}\n通过 {PASS}，失败 {FAIL}')
sys.exit(1 if FAIL else 0)
