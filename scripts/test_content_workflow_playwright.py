"""Playwright regression for content templates and content CRUD.

Install once:
    pip install -r requirements-dev.txt
    playwright install chromium

Run from the repository root:
    python scripts/test_content_workflow_playwright.py
"""
from pathlib import Path
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from flask import redirect, session
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

from app import create_app
from app.core.builder import build_site
from app.core.db import db
from app.core.models import Site, Template, User
from app.core.site_storage import copy_seed_data


passed = 0


def check(name, condition, detail=''):
    global passed
    if not condition:
        raise AssertionError(f'{name}: {detail}')
    passed += 1
    print(f'PASS {name}')


tmp = tempfile.TemporaryDirectory(prefix='content-playwright-', ignore_cleanup_errors=True)
base = Path(tmp.name)
app = create_app({
    'TESTING': False,
    'WTF_CSRF_ENABLED': True,
    'SQLALCHEMY_DATABASE_URI': f"sqlite:///{(base / 'test.db').as_posix()}",
    'SITES_DIR': str(base / 'sites'),
    'OUTPUT_DIR': str(base / 'output'),
    'TEMPLATES_DIR': str(ROOT / 'site_templates'),
    'SECRET_KEY': 'content-playwright-test',
    'SESSION_COOKIE_SECURE': False,
    'EXPORT_SKIP_LINK_CHECK': True,
})

with app.app_context():
    user = User(email='playwright@example.test', role='admin')
    template = Template(name='dengtec', display_name='Dengtec', industry='test', is_public=True)
    db.session.add_all([user, template])
    db.session.commit()
    site = Site(
        owner_id=user.id, name='浏览器内容回归', slug='content-browser', folder_path='sites/pending',
        template_name='dengtec', default_language='zh-CN', enabled_languages=['zh-CN', 'en'],
    )
    db.session.add(site)
    db.session.commit()
    site.folder_path = f'sites/{site.id}'
    domain_site = Site(
        owner_id=user.id, name='已绑定域名站点', slug='domain-browser', folder_path='sites/domain-browser',
        template_name='dengtec', default_language='zh-CN', enabled_languages=['zh-CN'],
        custom_domain='browser.example.test',
    )
    db.session.add(domain_site)
    db.session.commit()
    copy_seed_data(site.id, 'dengtec')
    user_id, site_id = user.id, site.id


@app.get('/__content_e2e_login')
def content_e2e_login():
    session['user_id'] = user_id
    session['current_site_id'] = site_id
    return redirect('/content/workspace?site=content-browser&lang=zh-CN')


server = make_server('127.0.0.1', 0, app, threaded=True)
port = server.server_port
base_url = f'http://127.0.0.1:{port}'
server_thread = threading.Thread(target=server.serve_forever, daemon=True)
server_thread.start()

try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        browser_context = browser.new_context(viewport={'width': 1440, 'height': 1000})
        page = browser_context.new_page()
        page_errors = []
        console_errors = []
        server_errors = []
        page.on('pageerror', lambda error: page_errors.append(str(error)))
        page.on('console', lambda message: console_errors.append(message.text) if message.type == 'error' else None)
        page.on('response', lambda response: server_errors.append((response.status, response.url))
                if response.status >= 500 else None)

        page.goto(base_url + '/__content_e2e_login', wait_until='networkidle')
        check('open content list', page.locator('h1').inner_text() == '内容列表')

        page.goto(base_url + '/overview?site=content-browser', wait_until='domcontentloaded')
        domain_action = page.get_by_role('link', name='绑定域名')
        domain_action.wait_for()
        check('overview keeps domain settings in site facts',
              page.locator('.overview-hero .overview-domain-action').count() == 0
              and page.locator('.overview-facts .overview-domain-action').count() == 1
              and page.locator('.overview-address-fact dt').inner_text() == '访问地址'
              and page.locator('.overview-domain-fact dt').inner_text() == '独立域名')
        check('domain action targets current site editor',
              f'edit={site_id}' in (domain_action.get_attribute('href') or ''))
        overview_url = page.url
        domain_action.click()
        account_frame = page.frame_locator('#accountWorkspaceFrame')
        account_frame.get_by_role('heading', name='编辑站点信息').wait_for()
        check('domain action opens account workspace overlay',
              page.locator('#accountWorkspaceOverlay').is_visible())
        check('domain action keeps workbench page in place', page.url == overview_url, page.url)
        page.evaluate('closeAccountWorkspace()')
        page.set_viewport_size({'width': 390, 'height': 844})
        overview_overflow = page.evaluate(
            'document.documentElement.scrollWidth > document.documentElement.clientWidth + 2')
        check('mobile overview domain status has no page overflow', not overview_overflow)
        page.set_viewport_size({'width': 1440, 'height': 1000})

        page.goto(base_url + '/account?section=sites', wait_until='networkidle')
        site_cards = page.locator('.site-card')
        check('domain status stays inside site metadata', site_cards.count() == 2
              and page.locator('.site-domain-row').count() == 2
              and page.locator('.site-domain-hint').count() == 0)
        action_tops = site_cards.locator(':scope > .site-actions').evaluate_all(
            'elements => elements.map(element => element.getBoundingClientRect().top)')
        check('site card action rows remain aligned', len(action_tops) == 2
              and abs(action_tops[0] - action_tops[1]) <= 1, action_tops)
        check('unbound domain action remains available',
              page.get_by_role('link', name='去绑定').count() == 1)
        page.set_viewport_size({'width': 390, 'height': 844})
        account_overflow = page.evaluate(
            'document.documentElement.scrollWidth > document.documentElement.clientWidth + 2')
        check('mobile site cards have no page overflow', not account_overflow)
        check('mobile domain action remains visible', page.get_by_role('link', name='去绑定').is_visible())
        page.set_viewport_size({'width': 1440, 'height': 1000})

        page.goto(base_url + '/content/workspace?mode=new&dataset=products&site=content-browser&lang=zh-CN',
                  wait_until='networkidle')
        product = page.locator('[data-choice="dataset"]:has(input[value="products"])')
        check('legacy dataset handoff preselects category', product.evaluate('element => element.classList.contains("selected")'))
        check('preselected category enables next step', page.locator('#toTemplates').is_enabled())
        page.locator('#toTemplates').click()
        visible_product_templates = page.locator('[data-dataset-template="products"]:visible')
        if visible_product_templates.count() == 1:
            check('single detail template is selected automatically',
                  visible_product_templates.locator('input:checked').count() == 1)
            check('automatic template selection enables editor step', page.locator('#createContent').is_enabled())
        else:
            visible_product_templates.first.click()
        page.locator('#createContent').click()
        page.wait_for_url('**/content/edit/products/0**')
        page.wait_for_load_state('networkidle')

        slug = page.locator('input[name="slug"]')
        slug.fill('UPPER')
        check('Chromium enforces slug pattern', slug.evaluate('element => element.validity.patternMismatch === true'))
        slug.fill('browser-minimal')
        page.locator('input[name="title"]').fill('浏览器最小内容')
        check('summary follows default optional contract', not page.locator('textarea[name="summary"]').evaluate('element => element.required'))
        check('media follows default optional contract', page.locator('input[name="cover"]').get_attribute('aria-required') == 'false')
        page.get_by_role('button', name='创建并保存').click()
        page.wait_for_url('**/content/edit/products/*')
        page.wait_for_load_state('networkidle')
        created_url = page.url
        check('minimal content created with formal ID', '/content/edit/products/0' not in created_url)
        check('edit form contains optimistic version token', page.locator('input[name="_content_version"]').count() == 1)

        stale_page = browser_context.new_page()
        stale_page.goto(created_url, wait_until='networkidle')
        page.locator('input[name="title"]').fill('浏览器内容 v2')
        page.get_by_role('button', name='保存', exact=True).click()
        page.wait_for_load_state('networkidle')
        check('valid existing edit persists', page.locator('input[name="title"]').input_value() == '浏览器内容 v2')
        stale_page.locator('input[name="title"]').fill('旧页面覆盖')
        stale_response = stale_page.expect_response(lambda response: '/content/edit/products/' in response.url and response.request.method == 'POST')
        stale_page.get_by_role('button', name='保存', exact=True).click()
        with stale_response as response_info:
            conflict_status = response_info.value.status
        stale_page.wait_for_load_state('networkidle')
        check('stale browser edit receives 409', conflict_status == 409, conflict_status)
        check('stale browser shows conflict message', '内容已被其他页面修改' in stale_page.locator('body').inner_text())
        stale_page.close()

        page.goto(base_url + '/content/templates/products?site=content-browser&lang=zh-CN', wait_until='networkidle')
        page.locator('.dt-create-form input[name="name"]').fill('浏览器模板')
        page.locator('.dt-create-form button').click()
        page.wait_for_load_state('networkidle')
        card = page.locator('.dt-template-card:has-text("浏览器模板")').first
        card.click(position={'x': 30, 'y': 30})
        page.wait_for_load_state('networkidle')
        check('template field rules are editable', page.locator('input[name="required_fields"][value="summary"]').count() == 1)
        page.locator('input[name="required_fields"][value="summary"]').check()
        page.locator('input[name="seo_title"]').fill('{title} | Browser')
        page.get_by_role('button', name='保存详情模板').click()
        page.wait_for_load_state('networkidle')
        check('template SEO remains visible after save', page.locator('input[name="seo_title"]').input_value() == '{title} | Browser')
        check('template preview action exists', page.get_by_role('link', name='预览已保存版本').count() == 1)
        with page.expect_popup() as popup_info:
            page.get_by_role('link', name='预览已保存版本').click()
        preview = popup_info.value
        preview.wait_for_load_state('networkidle')
        check('template preview renders saved template', preview.locator('body').count() == 1 and preview.locator('h1').count() >= 1)
        preview.close()

        page.set_viewport_size({'width': 390, 'height': 844})
        page.goto(created_url, wait_until='networkidle')
        overflow = page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth + 2')
        check('mobile editor has no page overflow', not overflow)
        check('mobile save remains operable', page.get_by_role('button', name='保存', exact=True).is_visible())

        invalid_pattern_errors = [message for message in console_errors if 'Pattern attribute value' in message]
        check('no Chromium pattern errors', not invalid_pattern_errors, invalid_pattern_errors)
        check('no uncaught browser errors', not page_errors, page_errors)
        check('no business 5xx responses', not server_errors, server_errors)
        browser_context.close()
        browser.close()

    with app.app_context():
        report = []
        output = build_site(site_id, report=report)
        matches = list(output.rglob('browser-minimal/index.html'))
        check('static build contains edited content', bool(matches) and '浏览器内容 v2' in matches[0].read_text(encoding='utf-8'))
        check('static build report is clean', not report, report)

    print(f'All Playwright content-workflow checks passed: {passed}')
finally:
    server.shutdown()
    server.server_close()
    server_thread.join(timeout=5)
    with app.app_context():
        db.session.remove()
        db.engine.dispose()
    tmp.cleanup()
