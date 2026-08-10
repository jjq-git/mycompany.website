"""Isolated regression for detail templates and content CRUD.

Run from the repository root:
    python scripts/test_content_workflow.py
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import tempfile

from werkzeug.datastructures import MultiDict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app
from app.core import datasets, menu as menu_lib
from app.core.db import db
from app.core.models import Site, Template, User
from app.core.routes import _apply_detail_template_autofill
from app.core.site_storage import copy_seed_data, read_yaml, write_yaml


passed = 0


def check(name, condition, detail=''):
    global passed
    if not condition:
        raise AssertionError(f'{name}: {detail}')
    passed += 1
    print(f'PASS {name}')


tmp = tempfile.TemporaryDirectory(prefix='content-workflow-', ignore_cleanup_errors=True)
base = Path(tmp.name)
app = create_app({
    'TESTING': True,
    'WTF_CSRF_ENABLED': False,
    'SQLALCHEMY_DATABASE_URI': f"sqlite:///{(base / 'test.db').as_posix()}",
    'SITES_DIR': str(base / 'sites'),
    'OUTPUT_DIR': str(base / 'output'),
    'TEMPLATES_DIR': str(ROOT / 'site_templates'),
    'SECRET_KEY': 'content-workflow-test',
})
ctx = app.app_context()
ctx.push()

user = User(email='content@example.test', role='admin')
template = Template(name='dengtec', display_name='Dengtec', industry='test', is_public=True)
db.session.add_all([user, template])
db.session.commit()
site = Site(
    owner_id=user.id, name='内容回归', slug='content-regression', folder_path='sites/pending',
    template_name='dengtec', default_language='zh-CN', enabled_languages=['zh-CN', 'en'],
)
db.session.add(site)
db.session.commit()
site.folder_path = f'sites/{site.id}'
db.session.commit()
copy_seed_data(site.id, 'dengtec')
settings = read_yaml(site.id, 'settings.yaml') or {}
base_labels = menu_lib.extract_labels(settings.get('menu') or [])
products_label_key = next(key for key, value in base_labels.items() if value == '产品')
settings.setdefault('menu_labels', {}).setdefault('zh-CN', {})[products_label_key] = '产品中心'
write_yaml(site.id, 'settings.yaml', settings)
uid, sid = user.id, site.id

client = app.test_client()
with client.session_transaction() as session:
    session['user_id'] = uid
    session['current_site_id'] = sid
query = '?site=content-regression&lang=zh-CN'

# Persist defaults and add a custom template.
response = client.post('/content/templates/products' + query, data={
    '_template_action': 'add', 'name': '回归模板',
})
page = read_yaml(sid, 'pages/products.yaml') or {}
custom = next(item for item in page['detail_templates'] if item.get('name') == '回归模板')
custom_id = custom['id']
check('create detail template', response.status_code == 302)

# Backend whitelist rejects a general page block and leaves template unchanged.
response = client.post('/content/templates/products' + query, data={
    '_template_action': 'save_modules', 'template_id': custom_id,
    'module_count': '1', 'module_0_type': 'hero_banner', 'module_0_order': '1',
})
page = read_yaml(sid, 'pages/products.yaml') or {}
custom = next(item for item in page['detail_templates'] if item.get('id') == custom_id)
check('reject out-of-scope template component', response.status_code == 400 and not custom.get('modules'))

# Field rules and SEO are editable and persisted.
response = client.post('/content/templates/products' + query, data=MultiDict([
    ('_template_action', 'save_modules'), ('template_id', custom_id), ('name', '回归模板'),
    ('module_count', '1'), ('module_0_type', 'detail_faq'), ('module_0_variant', 'list'),
    ('module_0_order', '1'), ('required_fields', 'slug'), ('required_fields', 'title'),
    ('required_fields', 'summary'), ('optional_fields', 'media'),
    ('seo_title', '{title} | 回归'), ('seo_description', '{summary}'), ('seo_image', 'cover'),
]))
custom = next(item for item in (read_yaml(sid, 'pages/products.yaml') or {})['detail_templates']
              if item.get('id') == custom_id)
check('persist template field contract', response.status_code == 302 and custom['required_fields'] == ['slug', 'title', 'summary'])
check('persist editable SEO contract', custom['seo']['title'] == '{title} | 回归')

# Custom template requires summary; the default template only requires slug/title.
new_url = '/content/edit/products/0' + query
response = client.post(new_url, data={'template_id': custom_id, 'slug': 'custom-one', 'title': 'Custom'})
check('template-required summary enforced', response.status_code == 400)
response = client.post(new_url, data={
    'template_id': custom_id, 'slug': 'custom-one', 'title': 'Custom', 'summary': 'Required',
})
custom_item = next(item for item in datasets.load(sid, 'products') if item.get('slug') == 'custom-one')
check('valid custom content created', response.status_code == 302 and custom_item['template_id'] == custom_id)

response = client.post(new_url, data={'template_id': 'default', 'slug': 'minimal-one', 'title': 'Minimal'})
minimal = next(item for item in datasets.load(sid, 'products') if item.get('slug') == 'minimal-one')
check('default contract allows optional summary/media', response.status_code == 302 and minimal is not None)

# Template preview uses saved builder rendering without changing the content item.
response = client.get(
    f'/content/templates/products/preview{query}&template_id={custom_id}&item_id={custom_item["id"]}'
)
check('saved detail template preview renders', response.status_code == 200 and b'Custom' in response.data)

# Existing edits require a valid template, core fields and the current content version.
edit_url = f'/content/edit/products/{minimal["id"]}' + query
version = datasets.item_version(minimal)
response = client.post(edit_url, data={
    '_content_version': version, 'template_id': 'missing-template',
    'slug': 'minimal-one', 'title': 'Minimal',
})
check('reject dangling template on existing content', response.status_code == 400)
response = client.post(edit_url, data={
    '_content_version': version, 'template_id': 'default', 'slug': '', 'title': '',
})
check('reject clearing existing core fields', response.status_code == 400)
response = client.post(edit_url, data={
    '_content_version': version, 'template_id': 'default', 'slug': 'minimal-one', 'title': 'Minimal v2',
})
check('valid existing edit succeeds', response.status_code == 302)
response = client.post(edit_url, data={
    '_content_version': version, 'template_id': 'default', 'slug': 'minimal-one', 'title': 'Stale overwrite',
})
check('stale editor cannot overwrite newer content', response.status_code == 409)

# Upload UI switches are transport controls, not dataset fields.
current = datasets.find(sid, 'products', minimal['id'])
response = client.post(edit_url, data={
    '_content_version': datasets.item_version(current), 'template_id': 'default',
    'slug': 'minimal-one', 'title': 'Minimal v2', 'cover_convert_webp': 'false',
})
current = datasets.find(sid, 'products', minimal['id'])
check('upload conversion switch never pollutes dataset YAML',
      response.status_code == 302 and 'cover_convert_webp' not in current)

# Unchanged tags remain automatic when structured specs change; actual tag edits lock them.
auto_fields = {
    'detail_specs': [{'items': [{'name': '输入电压', 'value': '24V'}]}],
    'tags': ['voltage-12v'],
}
_apply_detail_template_autofill(auto_fields, {}, original_tags='voltage-12v')
check('unchanged automatic tags follow changed specs',
      auto_fields.get('tags') == ['voltage-24v'] and auto_fields.get('tags_auto') is True,
      auto_fields)
manual_fields = {
    'detail_specs': [{'items': [{'name': '输入电压', 'value': '24V'}]}],
    'tags': ['用户标签'],
}
_apply_detail_template_autofill(manual_fields, {}, original_tags='voltage-12v')
check('real tag edits retain manual lock', manual_fields.get('tags_auto') is False, manual_fields)

# Deleting a used template migrates item references to the current default.
response = client.post('/content/templates/products' + query, data={
    '_template_action': 'delete', 'template_id': custom_id,
})
custom_after_delete = datasets.find(sid, 'products', custom_item['id'])
check('delete used template migrates references', response.status_code == 302 and custom_after_delete['template_id'] == 'default')

# Legacy endpoints no longer create placeholders or report fake deletion success.
before = len(datasets.load(sid, 'products'))
response = client.post('/_dataset/products/new' + query)
check('legacy creator retired without writes', response.status_code == 410 and len(datasets.load(sid, 'products')) == before)
response = client.post('/_dataset/products/999999/delete' + query)
check('legacy delete missing item is 404', response.status_code == 404)

# Older public dashboard URLs stay useful but no longer execute duplicate CRUD implementations.
response = client.get('/products' + query)
check('legacy product list redirects to content center',
      response.status_code == 302 and '/content/workspace' in response.location)
response = client.get(f'/products/{minimal["id"]}/edit' + query)
check('legacy product editor redirects instead of raising 500',
      response.status_code == 303 and f'/content/edit/products/{minimal["id"]}' in response.location)

# Chromium-compatible pattern and optimistic version token are present in the editor HTML.
current = datasets.find(sid, 'products', minimal['id'])
response = client.get(edit_url)
html = response.get_data(as_text=True)
check('editor exposes content version token', datasets.item_version(current) in html)
check('slug pattern escapes v-mode hyphen', 'pattern="[a-z0-9][a-z0-9\\-]{1,28}[a-z0-9]"' in html)
check('dataset editor uses localized menu label', '产品中心' in html and '>Products<' not in html)

# Concurrent add calls are serialized and preserve both records with unique IDs.
def add_race(title):
    with app.app_context():
        return datasets.add(sid, 'race', {'title': title})

with ThreadPoolExecutor(max_workers=2) as executor:
    ids = list(executor.map(add_race, ['A', 'B']))
race_items = datasets.load(sid, 'race')
check('concurrent adds keep unique IDs', sorted(ids) == [1, 2], ids)
check('concurrent adds preserve both records', len(race_items) == 2, race_items)

print(f'All content-workflow regression checks passed: {passed}')
db.session.remove()
db.engine.dispose()
ctx.pop()
tmp.cleanup()
