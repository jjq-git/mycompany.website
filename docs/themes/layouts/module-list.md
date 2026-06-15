# module_list: Page Module Search And Pagination

`module_list` is an optional page-level behavior for pages where the list items are page modules themselves, such as `/functions/` or `/modules/` pages made from repeated `highlight_card` blocks.

It is not a replacement for `data_grid`.

| Page Type | Use | Search/Pagination Target |
| --- | --- | --- |
| Product, blog, portfolio, or other dataset pages | `data_grid` | dataset cards such as `.dg-card` |
| Function directories, module directories, service lists built from page modules | `module_list` | `.builder-module` wrappers rendered by `_modules.html` |

## Page YAML

Enable it from the page YAML top level. Pages without `module_list.enabled: true` keep the normal module rendering behavior.

```yaml
title: Functions

module_list:
  enabled: true
  search: true
  pagination: true
  page_size: 6
  target_types:
    - highlight_card
  search_placeholder: Search functions...
  empty_text: No matching items.
  results_label: results
  prev_label: Previous
  next_label: Next

modules:
  - type: section_title
    order: 1
    data:
      title: Functions

  - type: highlight_card
    order: 2
    data:
      title: Resistor Decoder
      desc: Decode resistor color bands.
```

## Template Contract

`_modules.html` owns the structural markup:

- Read `page.module_list`.
- If `enabled: true`, wrap the module sequence in `.module-list-region`.
- Render the search toolbar, result count, empty state, and pagination container.
- Add `data-module-list-item="true"` only to modules whose `module.type` is listed in `target_types`.
- Render all other modules normally. A `section_title` heading should usually stay outside the searchable/paged item set.

Recommended shape:

```jinja2
{% set module_list = page.module_list | default({}) %}
{% set module_list_enabled = module_list.enabled | default(false) %}
{% set target_types = module_list.target_types | default([]) %}

{% if module_list_enabled %}
  <div class="module-list-region"
       data-module-list-page-size="{{ module_list.page_size | default(6) }}"
       data-module-list-results-label="{{ module_list.results_label | default('results') }}"
       data-module-list-empty-text="{{ module_list.empty_text | default('No matching items.') }}"
       data-module-list-prev-label="{{ module_list.prev_label | default('Previous') }}"
       data-module-list-next-label="{{ module_list.next_label | default('Next') }}">
    {% if module_list.search | default(true) %}
      <div class="module-list-toolbar">
        <input class="module-list-search" type="search"
               placeholder="{{ module_list.search_placeholder | default('Search...') }}">
        <span class="module-list-count"></span>
      </div>
    {% endif %}
{% endif %}

{% for module in page.modules | sort(attribute='order') %}
  {% set is_list_item = module_list_enabled and module.type in target_types %}
  <div class="builder-module"
       data-builder-module-index="{{ loop.index0 }}"
       data-builder-module-type="{{ module.type }}"
       {% if is_list_item %}data-module-list-item="true"{% endif %}>
    {{- render_block(module) }}
  </div>
{% endfor %}

{% if module_list_enabled %}
    <p class="module-list-empty" hidden>{{ module_list.empty_text | default('No matching items.') }}</p>
    {% if module_list.pagination | default(true) %}
      <nav class="module-list-pagination" aria-label="Pagination"></nav>
    {% endif %}
  </div>
{% endif %}
```

## JavaScript Contract

Put shared behavior in the theme `_base.html` or a theme JS file loaded by `_base.html`.

The script should initialize each `.module-list-region` independently:

- Cache searchable text for each `[data-module-list-item]` on load.
- Match against visible module text: title, tag, description, bullet points, and button text.
- Reset to page 1 after every search.
- Paginate only the filtered result set.
- Use separate hidden classes so search and pagination do not overwrite each other:
  - `.module-list-filter-hidden` for search misses.
  - `.module-list-page-hidden` for items outside the current page.
- Show `.module-list-empty` for zero matches.
- Hide pagination when there are zero matches or only one page.
- Do not call the backend, do not fetch JSON, and do not generate `/page/2/` routes.
- With JavaScript disabled, all modules remain visible.

## CSS Contract

Use the `module-list-*` namespace so the behavior stays separate from block-specific CSS such as `dg-*`, `fp-*`, or `hl-*`.

Expected classes:

- `.module-list-region`
- `.module-list-toolbar`
- `.module-list-search`
- `.module-list-count`
- `.module-list-empty`
- `.module-list-pagination`
- `.module-list-page-btn`
- `.module-list-filter-hidden`
- `.module-list-page-hidden`

At minimum:

```css
.module-list-filter-hidden,
.module-list-page-hidden {
  display: none !important;
}
```

## Implementation Scope

For `/functions/` and `/modules/`, prefer `module_list` when each entry is a repeated page module such as `highlight_card`.

If a page contains one `featured_picks` block with many internal `.fp-card` items, this feature will treat the whole `featured_picks` block as one item. Card-level search and pagination inside `featured_picks` is a different feature and should be implemented inside that block.
