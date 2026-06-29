"""Lightweight smoke checks for dashboard/backend edits.

Run:
    python scripts/smoke_check.py
"""
import py_compile
import subprocess
import sys
from pathlib import Path

from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]


PY_FILES = [
    'app/core/routes.py',
    'app/core/media_service.py',
    'app/core/builder.py',
    'app/core/site_storage.py',
]

TEMPLATE_FILES = [
    'app/templates/base.html',
    'app/templates/dashboard/panel_page_edit.html',
    'app/templates/dashboard/panel_header_footer.html',
    'app/templates/dashboard/panel_footer_variant.html',
    'app/templates/dashboard/seo_workspace.html',
    'app/templates/dashboard/_seo_health_content.html',
]

JS_FILES = [
    'app/static/js/admin_modules.js',
]


def check_python():
    for rel in PY_FILES:
        py_compile.compile(str(ROOT / rel), doraise=True)
        print(f'python ok: {rel}')


def check_templates():
    env = Environment()
    for rel in TEMPLATE_FILES:
        source = (ROOT / rel).read_text(encoding='utf-8')
        env.parse(source)
        print(f'jinja ok: {rel}')


def check_js():
    for rel in JS_FILES:
        result = subprocess.run(
            ['node', '--check', str(ROOT / rel)],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if result.returncode != 0:
            print(result.stdout)
            raise SystemExit(result.returncode)
        print(f'js ok: {rel}')


def main():
    check_python()
    check_templates()
    try:
        check_js()
    except FileNotFoundError:
        print('js skipped: node not found')
    print('smoke ok')


if __name__ == '__main__':
    main()
