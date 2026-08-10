"""CLI 建用户/建站隔离回归。"""
from pathlib import Path
import sys
import tempfile

import yaml
from werkzeug.security import check_password_hash

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app
from app.core.db import db
from app.core.models import (AccountEntitlement, AccountIdentity,
                             PasswordCredential, Site, User)
from app.core.site_storage import read_yaml


tmp = tempfile.TemporaryDirectory(prefix='cli-workflow-', ignore_cleanup_errors=True)
base = Path(tmp.name)
app = create_app({
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': f"sqlite:///{(base / 'test.db').as_posix()}",
    'SITES_DIR': str(base / 'sites'),
    'OUTPUT_DIR': str(base / 'output'),
    'TEMPLATES_DIR': str(ROOT / 'site_templates'),
    'SECRET_KEY': 'cli-workflow-test',
})
runner = app.test_cli_runner()


def check(name, condition, detail=''):
    if not condition:
        raise AssertionError(f'{name}: {detail}')
    print(f'PASS {name}')


with app.app_context():
    scan = runner.invoke(args=['scan-templates'])
    check('scan templates', scan.exit_code == 0, scan.output)

    password = 'Cli-Test-Password-2026!'
    created = runner.invoke(args=['create-user', 'CLI@Example.Test', '--password', password])
    check('create-user succeeds', created.exit_code == 0, created.output)
    user = User.query.filter_by(email='cli@example.test').one()
    identity = AccountIdentity.query.filter_by(
        identity_type='email', identifier='cli@example.test'
    ).one()
    credential = PasswordCredential.query.filter_by(user_id=user.id).one()
    entitlement = AccountEntitlement.query.filter_by(user_id=user.id).one()
    check('create-user creates verified primary identity',
          identity.user_id == user.id and identity.is_primary and identity.verified_at is not None)
    check('create-user creates usable password credential',
          check_password_hash(credential.password_hash, password))
    check('create-user grants site entitlement', entitlement.can_create_sites is True)

    generated = runner.invoke(args=['create-user', 'generated@example.test'])
    generated_user = User.query.filter_by(email='generated@example.test').one()
    check('create-user without password prints a one-time password',
          generated.exit_code == 0 and '一次性登录密码:' in generated.output,
          generated.output)
    check('generated-password account also has a credential',
          PasswordCredential.query.filter_by(user_id=generated_user.id).count() == 1)

    made_site = runner.invoke(args=[
        'create-site', 'cli@example.test', 'cli-regression',
        '--template', 'dengtec', '--name', 'CLI 回归站点',
    ])
    check('create-site succeeds', made_site.exit_code == 0, made_site.output)
    site = Site.query.filter_by(slug='cli-regression').one()
    meta = yaml.safe_load((ROOT / 'site_templates' / 'dengtec' / 'meta.yaml').read_text(encoding='utf-8')) or {}
    expected_languages = [item['code'] for item in meta.get('languages', [])]
    settings = read_yaml(site.id, 'settings.yaml') or {}
    header = settings.get('header') or {}
    check('create-site persists template language model',
          site.default_language == meta.get('default_language')
          and site.enabled_languages == expected_languages,
          site.enabled_languages)
    check('create-site synchronizes header languages',
          header.get('enabled_languages') == expected_languages
          and (header.get('language_switcher') or {}).get('enabled') is True,
          header)

    db.session.remove()
    db.engine.dispose()

tmp.cleanup()
print('All CLI workflow regression checks passed')
