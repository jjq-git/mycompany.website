"""Static regression checks for the inline page-translation controller.

Run from the repository root:
    python scripts/test_page_translation_ui.py
"""
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
template = (ROOT / 'app/templates/dashboard/panel_page_edit.html').read_text(encoding='utf-8')
anchor = template.index("var STORAGE_KEY = 'pending_translation_")
script_start = template.rfind('<script>', 0, anchor) + len('<script>')
script_end = template.index('</script>', anchor)
script = template[script_start:script_end]

# Replace the two Jinja expressions that are JavaScript values, then let Node
# validate the complete inline controller syntax.
checkable_script = re.sub(
    r"var SOURCE_PAGE = \{\{.*?\| tojson \}\};",
    'var SOURCE_PAGE = {};',
    script,
)
checkable_script = checkable_script.replace('{{ languages | tojson }}', '[]')
syntax = subprocess.run(
    ['node', '--check', '-'],
    input=checkable_script,
    text=True,
    capture_output=True,
)
if syntax.returncode:
    sys.stderr.write(syntax.stderr)
    raise SystemExit(syntax.returncode)

checks = {
    'rich editor uses backing field name': "textarea[name]:not(.rte-source-ta)" in script,
    'duplicate rich editor field is skipped': "hasOwnProperty.call(texts, key)" in script,
    'translation result keeps its original key': 'translatedMap[key] = t[key]' in script,
    'visible rich editor receives translated html': 'editor.innerHTML = String(value)' in script,
    'backing textarea stays synchronized': 'backing.value = editor.innerHTML' in script,
    'page loading overlay starts with translation': 'setTranslationLoading(true' in script,
    'page loading overlay always stops': 'setTranslationLoading(false' in script,
}

for name, passed in checks.items():
    if not passed:
        raise AssertionError(name)
    print(f'PASS {name}')

print(f'All page translation UI regression checks passed: {len(checks)}')
