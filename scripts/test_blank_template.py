"""Regression checks for the blank template component library."""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.core import block_parser, block_renderer
from app.core.routes import _get_available_blocks, _parse_modules_form


ROOT = Path(__file__).resolve().parent.parent
BLOCKS_DIR = ROOT / "site_templates" / "blank" / "blocks"


def _schema_names(fields):
    return {field.name for field in fields}


def _href_names(fields):
    names = set()
    for field in fields:
        if field.href_field:
            names.add(field.href_field)
        names.update(_href_names(field.children))
    return names


def _parse(path):
    html = path.read_text(encoding="utf-8")
    assert block_parser.is_data_attr_block(html), f"{path}: not a data-* block"
    return html, block_parser.parse(html)


app = create_app()

with app.app_context():
    blocks = _get_available_blocks("blank")
    block_names = {block["name"] for block in blocks}
    assert "contact_form" in block_names, "blank palette does not expose the map block"
    assert len(block_names) == len(list(BLOCKS_DIR.iterdir())), (
        "blank palette and installed block directories are inconsistent"
    )

    parsed_count = 0
    for block_dir in sorted(BLOCKS_DIR.iterdir()):
        if not block_dir.is_dir():
            continue
        meta_path = block_dir / "meta.yaml"
        assert meta_path.exists(), f"{block_dir.name}: missing meta.yaml"
        yaml.safe_load(meta_path.read_text(encoding="utf-8"))

        templates = [block_dir / "template.html"]
        variants_dir = block_dir / "variants"
        if variants_dir.exists():
            templates.extend(sorted(variants_dir.glob("*.html")))
        for template_path in templates:
            html, schema = _parse(template_path)
            rendered = block_renderer.render(html, schema, {}, {})
            assert "data-name=" not in rendered and "data-type=" not in rendered, (
                f"{template_path}: schema attributes leaked into preview output"
            )
            parsed_count += 1

    process_dir = BLOCKS_DIR / "process_steps"
    process_schemas = [
        _parse(process_dir / "template.html")[1],
        _parse(process_dir / "variants" / "numbered.html")[1],
        _parse(process_dir / "variants" / "vertical.html")[1],
    ]
    expected_process_fields = {"heading", "subheading", "steps"}
    for schema in process_schemas:
        assert _schema_names(schema.fields) == expected_process_fields
        steps = next(field for field in schema.fields if field.name == "steps")
        assert _schema_names(steps.children) == {"icon", "title", "desc"}
        desc = next(field for field in steps.children if field.name == "desc")
        assert desc.type == "textarea"

    hero_dir = BLOCKS_DIR / "hero_banner"
    _, hero_schema = _parse(hero_dir / "template.html")
    slides = next(field for field in hero_schema.fields if field.name == "slides")
    render_fields = _schema_names(slides.children) | _href_names(slides.children)
    hero_meta = yaml.safe_load((hero_dir / "meta.yaml").read_text(encoding="utf-8"))
    meta_slides = next(field for field in hero_meta["fields"] if field["key"] == "slides")
    editor_fields = {field["key"] for field in meta_slides["item_fields"]}
    assert editor_fields == render_fields, (
        f"hero editor fields {sorted(editor_fields)} do not match rendered fields "
        f"{sorted(render_fields)}"
    )

    hero_data = {
        "slides": [{
            "image": "/static/test-hero.jpg",
            "video": "",
            "title": "Blank template hero",
            "subtitle": "Hero field roundtrip",
            "primaryBtn": "Primary",
            "primaryLink": "/primary",
            "secondaryBtn": "Secondary",
            "secondaryLink": "/secondary",
        }]
    }
    hero_html = block_renderer.render(
        (hero_dir / "template.html").read_text(encoding="utf-8"),
        hero_schema,
        hero_data,
        {},
    )
    for expected in (
        "/static/test-hero.jpg",
        "Blank template hero",
        'href="/primary"',
        'href="/secondary"',
    ):
        assert expected in hero_html, f"hero roundtrip lost {expected}"

    data_grid_dir = BLOCKS_DIR / "data_grid"
    data_grid_html, data_grid_schema = _parse(data_grid_dir / "template.html")
    numeric_dataset_html = block_renderer.render(
        data_grid_html,
        data_grid_schema,
        {"dataset": 333},
        {
            "all_datasets": {
                "333": [{
                    "slug": "item-22",
                    "title": "Numeric dataset item",
                    "summary": "Numeric dataset targets must remain selectable",
                }]
            },
            "vars": {"dataset": "333", "dataset_path": "/zh-CN/333/"},
        },
    )
    assert "Numeric dataset item" in numeric_dataset_html, (
        "numeric dataset target did not resolve its string-keyed dataset"
    )

    form_data = {
        "module_count": "1",
        "module_0_type": "data_grid",
        "module_0_variant": "default",
        "module_0_order": "1",
        "module_0_data_dataset": "333",
    }
    with app.test_request_context(method="POST", data=form_data):
        with patch(
            "app.core.routes._current_context",
            return_value=(None, SimpleNamespace(id=11, template_name="blank")),
        ):
            saved_modules = _parse_modules_form(
                __import__("flask").request.form,
                existing_modules=[],
            )
    assert saved_modules[0]["data"]["dataset"] == "333", (
        "numeric dataset target was not preserved as a string during save"
    )

    print(
        f"PASS: blank template exposes {len(block_names)} blocks; "
        f"{parsed_count} block/variant templates parsed and rendered"
    )
