"""Verify that every theme exposes its installed map block in the component palette."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.core.routes import _get_available_blocks


app = create_app()

with app.app_context():
    templates_root = Path(app.config['TEMPLATES_DIR'])
    checked = 0

    for template_root in sorted(templates_root.iterdir()):
        map_meta = template_root / 'blocks' / 'contact_form' / 'meta.yaml'
        if not template_root.is_dir() or not map_meta.exists():
            continue

        blocks = _get_available_blocks(template_root.name)
        block_names = {block.get('name') for block in blocks}
        assert 'contact_form' in block_names, (
            f'{template_root.name}: installed map block is missing from the palette'
        )
        checked += 1

    assert checked > 0, 'no templates with an installed map block were found'
    print(f'PASS: map block is available in {checked} template component libraries')
