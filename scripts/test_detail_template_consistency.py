"""Regression checks for detail-template editor, item editor and renderer consistency."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jinja2 import Environment
from werkzeug.datastructures import MultiDict

from app.core import builder, routes


def check(label, condition):
    if not condition:
        raise AssertionError(label)
    print(f"PASS: {label}")


# Palette/category coverage.
component_by_name = {item['name']: item for item in routes.DETAIL_TEMPLATE_COMPONENT_BLOCKS}
check('all palette components use the detail category', all(
    item.get('category') == 'detail' for item in component_by_name.values()
))
check('all exposed component types have a renderer', all(
    name in builder.DETAIL_COMPONENT_TYPES for name in component_by_name
))
for required_type in ('detail_media', 'detail_text', 'detail_table'):
    check(f'{required_type} can be added again after deletion', not component_by_name[required_type].get('palette_hidden'))

# Explicit order is canonical in both admin and renderer paths.
unordered = [
    {'type': 'detail_text', 'order': 3, 'data': {'content_field': 'body'}},
    {'type': 'detail_specs', 'order': 1, 'data': {}},
    {'type': 'detail_link', 'order': 2, 'data': {}},
]
expected_order = ['detail_specs', 'detail_link', 'detail_text']
check('admin detail modules follow explicit order', [
    item['type'] for item in routes._sort_detail_modules(unordered)
] == expected_order)
check('renderer detail modules follow explicit order', [
    item['type'] for item in builder._sort_detail_modules(unordered)
] == expected_order)

# Component classification controls the corresponding item-editor section only.
classification_cases = {
    'detail_media': 'detail_images',
    'detail_specs': 'specs',
    'detail_table': 'detail_tables',
    'detail_link': 'link',
    'detail_features': 'detail_features',
    'detail_columns': 'detail_columns',
    'detail_files': 'detail_files',
    'detail_faq': 'detail_faqs',
    'detail_related': 'detail_related',
    'detail_content_blocks': 'detail_content_blocks',
}
for component_type, section_key in classification_cases.items():
    requirements = routes._detail_template_field_requirements({
        'modules': [{'type': component_type, 'data': {}}],
    })
    check(f'{component_type} maps to {section_key}', requirements[section_key] is True)
summary_requirements = routes._detail_template_field_requirements({
    'modules': [{'type': 'detail_text', 'data': {'content_field': 'summary'}}],
})
check('summary field text does not expose an unrelated body editor', summary_requirements['body'] is False)

# Singleton components cannot create duplicate editor/preview sections.
duplicates = [
    {'type': 'detail_media', 'order': 1, 'data': {}},
    {'type': 'detail_media', 'order': 2, 'data': {}},
    {'type': 'detail_columns', 'order': 3, 'data': {}},
    {'type': 'detail_columns', 'order': 4, 'data': {}},
]
deduped = routes._dedupe_detail_singletons(duplicates)
check('single-source components are deduplicated', [m['type'] for m in deduped].count('detail_media') == 1)
check('positional components remain repeatable', [m['type'] for m in deduped].count('detail_columns') == 2)

# Root visibility is authoritative in preview rendering.
hidden_html = builder._render_detail_component(
    {'item': {'title': 'Hidden title', 'body': 'Hidden body'}},
    {'type': 'detail_text', 'data': {'content_field': 'body', '_hidden': 'true'}},
)
check('hidden detail component renders no HTML', str(hidden_html) == '')
annotated_hidden_media = builder._annotate_detail_modules([
    {'type': 'detail_media', 'order': 1, 'data': {'_hidden': 'true'}},
])
check('hidden media still gets a visible base heading', annotated_hidden_media[0]['type'] == '_detail_base_header')

# Empty positional groups must not fall back to group 1 / legacy fields.
spec_modules = builder._annotate_detail_modules([
    {'type': 'detail_specs', 'order': 1, 'data': {}},
    {'type': 'detail_specs', 'order': 2, 'data': {}},
])
spec_modules = [m for m in spec_modules if m['type'] == 'detail_specs']
spec_item = {
    'specs': [{'name': 'legacy', 'value': 'must not repeat'}],
    'detail_specs': [{'items': [{'name': 'A', 'value': '1'}], 'visible': True}],
}
spec_html = [str(builder._render_detail_specs(spec_item, m['data'])) for m in spec_modules]
check('only populated specs group renders', [bool(value) for value in spec_html] == [True, False])
legacy_spec_html = [str(builder._render_detail_specs({'specs': spec_item['specs']}, m['data'])) for m in spec_modules]
check('legacy specs source renders only in the first component',
      [bool(value) for value in legacy_spec_html] == [True, False])

link_modules = builder._annotate_detail_modules([
    {'type': 'detail_link', 'order': 1, 'data': {'hide_when_empty': 'true'}},
    {'type': 'detail_link', 'order': 2, 'data': {'hide_when_empty': 'true'}},
])
link_modules = [m for m in link_modules if m['type'] == 'detail_link']
link_item = {
    'detail_links': [{'text': 'First', 'url': '/first/'}],
    'download_url': '/must-not-repeat/',
}
link_html = [str(builder._render_detail_link(link_item, m['data'])) for m in link_modules]
check('only populated link group renders', [bool(value) for value in link_html] == [True, False])

# Parsers preserve positional empty groups.
links = routes._parse_detail_links_form(MultiDict([
    ('detail_links_0_text', 'First'), ('detail_links_0_url', '/first/'),
    ('detail_links_2_text', 'Third'), ('detail_links_2_url', '/third/'),
]), 3)
check('link parser preserves middle empty group', len(links) == 3 and not links[1]['url'] and links[2]['url'] == '/third/')

columns_form = [('detail_columns_count', '3')]
for index in range(3):
    columns_form.extend([
        (f'detail_columns_{index}_heading', ''),
        (f'detail_columns_{index}_count', '1' if index == 2 else '0'),
    ])
columns_form.extend([
    ('detail_columns_2_0_title', 'Third'),
    ('detail_columns_2_0_text', 'Only third group'),
    ('detail_columns_2_0_image', ''),
    ('detail_columns_2_0_alt', ''),
])
column_groups = routes._parse_detail_columns_form(MultiDict(columns_form))
check('columns parser preserves leading empty groups',
      len(column_groups) == 3 and not column_groups[0]['items'] and column_groups[2]['items'])
column_modules = builder._annotate_detail_modules([
    {'type': 'detail_columns', 'order': 1, 'data': {}},
    {'type': 'detail_columns', 'order': 2, 'data': {}},
])
column_modules = [m for m in column_modules if m['type'] == 'detail_columns']
legacy_columns = {'detail_columns': {'heading': 'Legacy', 'items': [{'text': 'Once'}]}}
legacy_column_html = [str(builder._render_detail_columns(legacy_columns, m['data'])) for m in column_modules]
check('legacy columns source renders only in the first component',
      [bool(value) for value in legacy_column_html] == [True, False])

# Detail editor uses one independent section per repeated specs/columns component.
panel_path = Path(__file__).resolve().parent.parent / 'app/templates/dashboard/panel_data_list.html'
panel_source = panel_path.read_text(encoding='utf-8')
Environment().parse(panel_source)
check('specs editor groups are independent sections',
      'data-field-section="specs_{{ spec_group_i }}"' in panel_source and 'id="detailSpecsList"' not in panel_source)
check('columns editor groups are independent sections',
      'data-field-section="detail_columns_{{ col_group_i }}"' in panel_source and 'id="detailColumnsList"' not in panel_source)
check('table editor groups are independent sections',
      'data-field-section="detail_tables_{{ table_i }}"' in panel_source and 'id="detailTablesList"' not in panel_source)
check('link editor groups are independent sections',
      'data-field-section="link_{{ i }}"' in panel_source and 'id="detailLinksList"' not in panel_source)

print('All detail-template consistency checks passed.')
