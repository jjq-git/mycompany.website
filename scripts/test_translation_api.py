"""Regression checks for page-sized AI translation requests.

Run from the repository root:
    python scripts/test_translation_api.py
"""
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app
from app.core.db import db
from app.core.models import User


passed = 0


def check(name, condition, detail=''):
    global passed
    if not condition:
        raise AssertionError(f'{name}: {detail}')
    passed += 1
    print(f'PASS {name}')


with tempfile.TemporaryDirectory(prefix='translation-api-', ignore_cleanup_errors=True) as temp_dir:
    base = Path(temp_dir)
    app = create_app({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{(base / 'test.db').as_posix()}",
        'SITES_DIR': str(base / 'sites'),
        'OUTPUT_DIR': str(base / 'output'),
        'TEMPLATES_DIR': str(ROOT / 'site_templates'),
        'SECRET_KEY': 'translation-api-test',
        'TRANSLATION_API_KEY': 'test-key',
    })

    with app.app_context():
        user = User(email='translate@example.test', role='admin')
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    client = app.test_client()
    with client.session_transaction() as session:
        session['user_id'] = user_id

    page_texts = {f'module_{i}_data_title': f'待翻译内容 {i}' for i in range(75)}
    with patch('app.core.routes.translate_json', side_effect=lambda texts, *_: {
        key: f'EN: {value}' for key, value in texts.items()
    }) as translate_mock:
        response = client.post('/api/translate', json={
            'texts': page_texts,
            'source_lang': 'zh-CN',
            'target_lang': 'en',
        })
    payload = response.get_json() or {}
    check('accept more than 50 page fields', response.status_code == 200, payload)
    check('return every translated field', len(payload.get('translated', {})) == 75, payload)
    check('submit the complete page as one translation task', translate_mock.call_count == 1)

    too_many = {f'field_{i}': 'text' for i in range(501)}
    response = client.post('/api/translate', json={'texts': too_many})
    check('reject unreasonable field count', response.status_code == 400, response.get_json())

    response = client.post('/api/translate', json={'texts': {'body': 'x' * 50_001}})
    check('reject unreasonable total text size', response.status_code == 400, response.get_json())

print(f'All translation API regression checks passed: {passed}')
