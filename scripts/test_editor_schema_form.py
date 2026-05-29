"""端到端：用 Flask test client 验证 schema 驱动表单的完整链路。

1. 登录 site 1 owner，访问页面编辑器，确认 schema 表单 JS + styleRegistry 下发
2. 模拟 POST 保存一个 section_title 模块（schema 表单字段命名），确认 YAML 正确写入
3. 开关开构建，确认渲染正确
不需起真实服务器（test client 直接打路由）。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.core.models import Site
from app.core.site_storage import read_yaml

app = create_app()
app.config['ENABLE_DATA_ATTR_BLOCKS'] = True
app.config['WTF_CSRF_ENABLED'] = False  # 测试夹具：跳过 CSRF（真实浏览器表单自带 token）
PASS = FAIL = 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1; print(f'  ✓ {name}')
    else:
        FAIL += 1; print(f'  ✗ {name}  {detail}')


with app.app_context():
    site = Site.query.get(1)
    owner_id = site.owner_id

client = app.test_client()
with client.session_transaction() as sess:
    sess['user_id'] = owner_id
    sess['current_site_id'] = 1

# ---- 1. GET 页面编辑器，确认 schema 基础设施下发 ----
print('=== 1. 页面编辑器下发 schema 基础设施 ===')
resp = client.get('/_panel/_schematest?site=1')
html = resp.get_data(as_text=True)
check('页面返回 200', resp.status_code == 200, f'实际 {resp.status_code}')
check('下发 generateSchemaForm 函数', 'function generateSchemaForm' in html)
check('下发 generateSchemaStyleForm 函数', 'function generateSchemaStyleForm' in html)
check('下发 styleRegistryJson', 'styleRegistryJson' in html)
check('addModule 有 is_data_attr 拦截', 'meta.is_data_attr && meta.schema' in html)
check('blockLibrary 含 is_data_attr 标记', '"is_data_attr": true' in html or '"is_data_attr":true' in html)

# ---- 2. POST 保存 section_title（schema 表单字段命名）----
print('\n=== 2. 保存 section_title 模块（schema 表单 → YAML）===')
# 模拟 schema 表单提交：module_0_data_<field>，整块显隐 module_0_data__hidden
form = {
    'module_count': '1',
    'module_0_type': 'section_title',
    'module_0_order': '1',
    'module_0_variant': 'default',
    'module_0_data_tag': '测试标签',
    'module_0_data_title': '测试标题ABC',
    'module_0_data_desc': '测试描述内容',
    'module_0_data_btn': '点我',
    'module_0_data_btn_url': '/contact',
    'module_0_data_style_text-align': 'center',
    'module_0_data__hidden': 'false',
}
resp2 = client.post('/_panel/_schematest?site=1', data=form)
check('POST 返回 2xx/3xx', resp2.status_code in (200, 302), f'实际 {resp2.status_code}')

with app.app_context():
    saved = read_yaml(1, 'pages/_schematest.yaml') or {}
    mods = saved.get('modules', [])
    st = next((m for m in mods if m.get('type') == 'section_title'), None)
    check('section_title 模块已保存', st is not None)
    if st:
        d = st.get('data', {})
        check('tag 正确', d.get('tag') == '测试标签', repr(d.get('tag')))
        check('title 正确', d.get('title') == '测试标题ABC', repr(d.get('title')))
        check('desc 正确', d.get('desc') == '测试描述内容')
        check('btn 正确', d.get('btn') == '点我')
        check('btn_url(链接) 正确', d.get('btn_url') == '/contact')
        check('style_text-align 正确', d.get('style_text-align') == 'center', repr(d.get('style_text-align')))
        check('_hidden=false 已存', str(d.get('_hidden')) == 'false', repr(d.get('_hidden')))

# ---- 3. 用保存的数据直接渲染该 block，确认 schema 表单数据→渲染闭环 ----
print('\n=== 3. 保存的数据渲染确认 ===')
with app.app_context():
    from app.core import block_parser as bp, block_renderer as br
    html = (Path(app.config['TEMPLATES_DIR']) / 'dengtec' / 'blocks'
            / 'section_title' / 'template.html').read_text(encoding='utf-8')
    schema = bp.parse(html)
    out = br.render(html, schema, (st or {}).get('data', {}))
    check('保存的标题已渲染', '测试标题ABC' in out)
    check('保存的标签已渲染', '测试标签' in out)
    check('text-align 样式注入', '--text-align: center' in out)
    check('btn 链接注入', 'href="/contact"' in out)
    check('无 data-* 残留', 'data-name' not in out and 'data-type' not in out)

# ---- 清理测试污染 ----
test_file = Path(app.config['SITES_DIR']) / '1' / 'pages' / '_schematest.yaml'
if test_file.exists():
    test_file.unlink()
    print('\n（已清理测试文件 _schematest.yaml）')

print(f'\n{"="*40}\n通过 {PASS}，失败 {FAIL}')
sys.exit(1 if FAIL else 0)
