"""Migrate legacy per-item detail modules to category detail templates.

The old editor stored an ``item_data`` layout (and occasionally
``image_carousel``/``featured_picks``) on every dataset item.  The component
editor stores layout on the dataset page's ``detail_templates`` instead.

This migration deliberately keeps every item content field untouched.  It
only removes legacy layout overrides and makes sure templates render the
existing rich-text ``body`` field.
"""

from __future__ import annotations

import argparse
import copy
import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml
from bs4 import BeautifulSoup, NavigableString, Tag


LEGACY_ITEM_MODULES = {"item_data", "image_carousel", "featured_picks"}
BODY_COMPONENTS = {"detail_text", "item_data", "item_detail"}
PRODUCT_SPEC_DATASETS = {"aluminum-profile", "holograms", "led-strip", "powerptrack"}
DOWNLOAD_EXTENSIONS = {"pdf", "dxf", "stp", "step", "dwg", "zip", "doc", "docx", "xls", "xlsx"}


def _load(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _dump(path: Path, value: Any) -> None:
    path.write_text(
        yaml.safe_dump(value, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )


def _module_types(modules: Any) -> set[str]:
    if not isinstance(modules, list):
        return set()
    return {
        str(module.get("type") or "")
        for module in modules
        if isinstance(module, dict)
    }


def _without_modules(items: list[Any]) -> list[Any]:
    result = copy.deepcopy(items)
    for item in result:
        if isinstance(item, dict):
            item.pop("modules", None)
    return result


def _remove_top_level_item_modules(text: str) -> str:
    """Remove two-space ``modules`` keys without reformatting large YAML files."""
    lines = text.splitlines(keepends=True)
    output: list[str] = []
    index = 0
    while index < len(lines):
        if lines[index].rstrip("\r\n") != "  modules:":
            output.append(lines[index])
            index += 1
            continue
        index += 1
        while index < len(lines):
            line = lines[index]
            stripped = line.rstrip("\r\n")
            if line.startswith("- ") or (
                line.startswith("  ")
                and not line.startswith("   ")
                and not line.startswith("  -")
                and ":" in stripped
            ):
                break
            index += 1
    return "".join(output)


def _detail_text_module() -> dict[str, Any]:
    return {
        "type": "detail_text",
        "variant": "plain",
        "data": {
            "title": "",
            "content_field": "body",
            "empty_behavior": "hide_module",
            "text_align": "left",
            "section_bg": "",
            "text_color": "",
        },
    }


def _default_migration_template(dataset: str) -> dict[str, Any]:
    label = dataset.replace('-', ' ').replace('_', ' ').strip() or 'item'
    return {
        "id": "default",
        "name": f"默认{label}详情",
        "is_default": True,
        "modules": [
            {
                "type": "detail_media", "variant": "gallery_top",
                "data": {"source": "cover_and_gallery", "layout": "gallery_top", "max_images": 6,
                         "empty_behavior": "hide_module", "image_ratio": "4/3", "image_radius": "8px"},
            },
            {
                "type": "detail_intro", "variant": "default",
                "data": {"title_field": "title", "summary_field": "summary", "show_category": "true",
                         "show_tags": "true", "show_price": "false", "text_align": "left"},
            },
            _detail_text_module(),
        ],
        "required_fields": ["title", "slug"],
        "optional_fields": ["cover", "summary", "body", "detail_images", "category", "tags"],
        "seo": {"title": "{title} - {site_name}", "description": "{summary}", "image": "cover"},
    }


def _modernize_template_modules(modules: Any) -> tuple[list[Any], bool]:
    if not isinstance(modules, list):
        return [], False
    types = _module_types(modules)
    changed = False

    # Convert the remaining old custom-template building blocks.  Their
    # content lives on the item, so modern components can read it directly.
    modern: list[Any] = []
    for module in modules:
        if not isinstance(module, dict):
            modern.append(module)
            continue
        module_type = module.get("type")
        data = module.get("data") if isinstance(module.get("data"), dict) else {}
        if module_type == "item_data":
            modern.extend([
                {
                    "type": "detail_media",
                    "variant": "gallery_left",
                    "data": {
                        "source": "cover_and_gallery",
                        "layout": "gallery_left",
                        "max_images": data.get("detail_images_max", 6),
                        "empty_behavior": "hide_module",
                        "image_ratio": "4/3",
                        "image_radius": data.get("image_radius") or "8px",
                        "section_bg": data.get("section_bg") or "",
                    },
                },
                _detail_text_module(),
                {
                    "type": "detail_specs",
                    "variant": "list",
                    "data": {
                        "title": "",
                        "source_field": "specs",
                        "max_rows": data.get("specs_max_rows", 10),
                        "columns": str(data.get("specs_columns") or 1),
                        "hide_empty_rows": data.get("hide_empty_rows", "true"),
                        "border_color": "#e5e7eb",
                        "section_bg": "",
                    },
                },
                {
                    "type": "detail_link",
                    "variant": "button",
                    "data": {
                        "label": data.get("link_text") or "了解更多",
                        "url_field": "link_url",
                        "style": "button",
                        "hide_when_empty": "true",
                        "link_color": data.get("link_color") or "",
                        "section_bg": "",
                    },
                },
            ])
            changed = True
        elif module_type == "text_content":
            # item_data conversion above already added the item body.  A
            # non-empty static text block is retained because it is template
            # content rather than item content.
            if data.get("title") or data.get("body"):
                modern.append(module)
            changed = True
        else:
            modern.append(module)

    if "item_data" not in types:
        modern = list(modules)

    return modern, changed


def _ensure_body_component(template: dict[str, Any]) -> bool:
    modules = template.get("modules")
    if not isinstance(modules, list) or not modules:
        return False
    modules, changed = _modernize_template_modules(modules)
    template["modules"] = modules
    if _module_types(modules) & BODY_COMPONENTS:
        return changed

    insert_at = 0
    for index, module in enumerate(modules):
        if isinstance(module, dict) and module.get("type") in {"detail_media", "detail_intro"}:
            insert_at = index + 1
    modules.insert(insert_at, _detail_text_module())
    optional = template.get("optional_fields")
    if isinstance(optional, list) and "body" not in optional:
        optional.append("body")
    return True


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\xa0", " ")).strip()


def _table_rows(table: Tag) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in table.find_all("tr"):
        cells = [_clean_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"], recursive=False)]
        if any(cells):
            rows.append(cells)
    return rows


def _previous_heading(table: Tag) -> Tag | None:
    heading = table.find_previous(["h1", "h2", "h3", "h4"])
    if heading is None:
        return None
    intervening_table = heading.find_next("table")
    return heading if intervening_table is table else None


def _download_type(url: str, label: str) -> str:
    match = re.search(r"\.([a-z0-9]+)(?:[?#].*)?$", url, re.I)
    if match:
        return match.group(1).upper()
    for extension in DOWNLOAD_EXTENSIONS:
        if extension in label.lower():
            return extension.upper()
    return ""


def _is_download(url: str, label: str, dataset: str) -> bool:
    kind = _download_type(url, label).lower()
    return kind in DOWNLOAD_EXTENSIONS or dataset in PRODUCT_SPEC_DATASETS or dataset in {"cable-connector", "spot-light"}


def _append_text_block(blocks: list[dict[str, Any]], text: str) -> None:
    text = _clean_text(text)
    if not text:
        return
    if blocks and blocks[-1].get("type") == "text":
        blocks[-1]["text"] = _clean_text(str(blocks[-1].get("text") or "") + "\n" + text)
    else:
        blocks.append({"type": "text", "text": text})


def _walk_content(node: Any, blocks: list[dict[str, Any]]) -> None:
    if isinstance(node, NavigableString):
        _append_text_block(blocks, str(node))
        return
    if not isinstance(node, Tag):
        return
    if node.name in {"script", "style", "colgroup", "tbody", "hr", "br", "source"}:
        return
    if node.name in {"h1", "h2", "h3", "h4"}:
        title = _clean_text(node.get_text(" ", strip=True))
        if title:
            blocks.append({"type": "heading", "title": title})
        for media in node.find_all(["img", "video"], recursive=True):
            _walk_content(media, blocks)
        return
    if node.name == "table":
        rows = _table_rows(node)
        if rows:
            blocks.append({"type": "table", "table": rows})
        for media in node.find_all(["img", "video"], recursive=True):
            _walk_content(media, blocks)
        return
    if node.name == "img":
        url = node.get("src") or ""
        if url:
            blocks.append({"type": "image", "image": url, "alt": node.get("alt") or ""})
        return
    if node.name == "video":
        source = node.get("src") or ""
        if not source:
            child_source = node.find("source")
            source = child_source.get("src") if child_source else ""
        if source:
            blocks.append({"type": "video", "video": source, "text": _clean_text(node.get_text(" ", strip=True))})
        return
    if node.name in {"ul", "ol"}:
        lines = [_clean_text(entry.get_text(" ", strip=True)) for entry in node.find_all("li", recursive=False)]
        _append_text_block(blocks, "\n".join(f"• {line}" for line in lines if line))
        return
    if node.name == "p":
        media = node.find_all(["img", "video"], recursive=True)
        text = _clean_text(node.get_text(" ", strip=True))
        if text:
            style = str(node.get("style") or "")
            font = node.find("font")
            color = (font.get("color") if font else "") or ("color" if "color" in style.lower() else "")
            if color and len(text) <= 300:
                blocks.append({"type": "note", "text": text, "style": "info"})
            else:
                _append_text_block(blocks, text)
        for entry in media:
            _walk_content(entry, blocks)
        return
    for child in node.children:
        _walk_content(child, blocks)


def _coverage_tokens(value: str) -> Counter[str]:
    return Counter(token.casefold() for token in re.findall(r"[\w\u4e00-\u9fff]+", value or "", re.UNICODE))


def _structured_text(blocks: list[dict[str, Any]], specs: list[dict[str, Any]], files: list[dict[str, Any]], links: list[dict[str, Any]]) -> str:
    values: list[str] = []
    for block in blocks:
        for key in ("title", "text", "caption", "alt"):
            values.append(str(block.get(key) or ""))
        for row in block.get("table") or []:
            if isinstance(row, list):
                values.extend(str(cell or "") for cell in row)
    for group in specs:
        values.append(str(group.get("title") or ""))
        for item in group.get("items") or []:
            if isinstance(item, dict):
                values.extend(str(item.get(key) or "") for key in ("name", "desc", "value"))
    for entry in files:
        values.extend(str(entry.get(key) or "") for key in ("title", "desc", "type"))
    for entry in links:
        values.extend(str(entry.get(key) or "") for key in ("text", "label"))
    return " ".join(values)


def _structured_urls(blocks: list[dict[str, Any]], files: list[dict[str, Any]], links: list[dict[str, Any]]) -> set[str]:
    urls = {str(entry.get("url") or "") for entry in files}
    urls.update(str(entry.get("url") or "") for entry in links)
    for block in blocks:
        urls.update(str(block.get(key) or "") for key in ("image", "video", "embed_url"))
    return {url for url in urls if url}


def _convert_body(item: dict[str, Any], dataset: str, source: str) -> bool:
    body = str(item.get("body") or "")
    if not body.strip():
        return False
    soup = BeautifulSoup(body, "html.parser")
    specs = copy.deepcopy(item.get("detail_specs")) if isinstance(item.get("detail_specs"), list) else []
    files = copy.deepcopy(item.get("detail_files")) if isinstance(item.get("detail_files"), list) else []
    links = copy.deepcopy(item.get("detail_links")) if isinstance(item.get("detail_links"), list) else []
    blocks = copy.deepcopy(item.get("detail_content_blocks")) if isinstance(item.get("detail_content_blocks"), list) else []

    if dataset in PRODUCT_SPEC_DATASETS and not specs:
        for table in list(soup.find_all("table")):
            rows = _table_rows(table)
            if not rows:
                continue
            heading = _previous_heading(table)
            title = _clean_text(heading.get_text(" ", strip=True)) if heading else ""
            items = []
            for row in rows:
                padded = (row + ["", ""])[:3]
                items.append({"name": padded[0], "desc": padded[1], "value": padded[2]})
            specs.append({"title": title, "items": items, "visible": True})
            if heading:
                heading.decompose()
            table.decompose()

    if not files:
        for anchor in list(soup.find_all("a")):
            url = str(anchor.get("href") or "").strip()
            label = _clean_text(anchor.get_text(" ", strip=True)) or url
            if not url or not _is_download(url, label, dataset):
                continue
            kind = _download_type(url, label)
            files.append({"title": label, "url": url, "desc": label, "type": kind})
            parent = anchor.find_parent("li")
            (parent or anchor).decompose()
        for listing in list(soup.find_all(["ul", "ol"])):
            if not _clean_text(listing.get_text(" ", strip=True)):
                listing.decompose()

    for anchor in list(soup.find_all("a")):
        url = str(anchor.get("href") or "").strip()
        label = _clean_text(anchor.get_text(" ", strip=True)) or url
        if not url:
            continue
        links.append({"text": label, "url": url})
        if anchor.find(["img", "video"]):
            anchor.unwrap()
        else:
            anchor.decompose()

    parsed_blocks: list[dict[str, Any]] = []
    for child in list(soup.contents):
        _walk_content(child, parsed_blocks)
    blocks.extend(parsed_blocks)

    original_text = _clean_text(BeautifulSoup(body, "html.parser").get_text(" ", strip=True))
    original_tokens = _coverage_tokens(original_text)
    migrated_tokens = _coverage_tokens(_structured_text(blocks, specs, files, links))
    missing = original_tokens - migrated_tokens
    if missing:
        sample = ", ".join(f"{token}:{count}" for token, count in list(missing.items())[:8])
        raise RuntimeError(f"{source}: text coverage failed ({sample})")
    original_urls = {
        str(tag.get(attr) or "")
        for tag, attr in [(tag, "href") for tag in BeautifulSoup(body, "html.parser").find_all("a")]
        + [(tag, "src") for tag in BeautifulSoup(body, "html.parser").find_all(["img", "video", "source"])]
        if tag.get(attr)
    }
    missing_urls = original_urls - _structured_urls(blocks, files, links)
    if missing_urls:
        raise RuntimeError(f"{source}: URL coverage failed ({sorted(missing_urls)[:3]})")

    item["body"] = ""
    item["detail_content_blocks"] = blocks
    if specs:
        item["detail_specs"] = specs
    if files:
        item["detail_files"] = files
    if links:
        item["detail_links"] = links
    return True


def _component_module(module_type: str) -> dict[str, Any]:
    if module_type == "detail_content_blocks":
        return {
            "type": "detail_content_blocks", "variant": "blocks",
            "data": {"title": "", "empty_behavior": "hide_module", "section_bg": "", "text_color": ""},
        }
    if module_type == "detail_files":
        return {
            "type": "detail_files", "variant": "list",
            "data": {"title": "资料下载", "empty_behavior": "hide_module", "link_color": "", "section_bg": ""},
        }
    return {
        "type": "detail_specs", "variant": "list",
        "data": {"title": "", "source_field": "specs", "max_rows": 50, "columns": 3,
                 "hide_empty_rows": "true", "border_color": "#e5e7eb", "section_bg": ""},
    }


def _modernize_content_template(template: dict[str, Any], spec_count: int, has_files: bool, link_count: int) -> bool:
    modules = template.get("modules")
    if not isinstance(modules, list) or not modules:
        return False
    before = copy.deepcopy(modules)
    modules = [module for module in modules if not (isinstance(module, dict) and module.get("type") == "detail_text")]
    content_modules = [module for module in modules if isinstance(module, dict) and module.get("type") == "detail_content_blocks"]
    modules = [module for module in modules if not (isinstance(module, dict) and module.get("type") == "detail_content_blocks")]
    insert_at = max(
        (i + 1 for i, module in enumerate(modules) if isinstance(module, dict) and module.get("type") in {"detail_media", "detail_intro"}),
        default=0,
    )
    modules.insert(insert_at, content_modules[0] if content_modules else _component_module("detail_content_blocks"))
    existing_specs = sum(1 for module in modules if isinstance(module, dict) and module.get("type") == "detail_specs")
    while existing_specs < spec_count:
        modules.append(_component_module("detail_specs"))
        existing_specs += 1
    if has_files and not any(isinstance(module, dict) and module.get("type") == "detail_files" for module in modules):
        modules.append(_component_module("detail_files"))
    existing_links = sum(1 for module in modules if isinstance(module, dict) and module.get("type") == "detail_link")
    while existing_links < link_count:
        modules.append({
            "type": "detail_link", "variant": "text_link",
            "data": {"title": "", "label": "了解更多", "url_field": "link_url", "style": "text_link",
                     "hide_when_empty": "true", "link_color": "", "section_bg": ""},
        })
        existing_links += 1
    template["modules"] = modules
    optional = template.get("optional_fields")
    if isinstance(optional, list):
        for field in ("detail_content_blocks", "detail_specs", "detail_files", "detail_links"):
            if field not in optional:
                optional.append(field)
    return modules != before


def convert_bodies(site_root: Path, apply: bool) -> dict[str, int]:
    stats = {"data_files": 0, "items": 0, "content_blocks": 0, "spec_groups": 0, "files": 0, "links": 0, "page_files": 0, "templates": 0}
    requirements: dict[str, dict[str, Any]] = {}
    for path in sorted((site_root / "lang").glob("*/data/*.yaml")):
        items = _load(path)
        if not isinstance(items, list):
            continue
        changed = False
        for item in items:
            if not isinstance(item, dict):
                continue
            req = requirements.setdefault(path.stem, {"spec_count": 0, "files": False, "link_count": 0})
            req["spec_count"] = max(req["spec_count"], len(item.get("detail_specs") or []))
            req["files"] = req["files"] or bool(item.get("detail_files"))
            req["link_count"] = max(req["link_count"], len(item.get("detail_links") or []) if isinstance(item.get("detail_links"), list) else 0)
            if not item.get("body"):
                continue
            if _convert_body(item, path.stem, f"{path}:{item.get('slug') or item.get('id')}"):
                changed = True
                stats["items"] += 1
                stats["content_blocks"] += len(item.get("detail_content_blocks") or [])
                stats["spec_groups"] += len(item.get("detail_specs") or [])
                stats["files"] += len(item.get("detail_files") or [])
                stats["links"] += len(item.get("detail_links") or []) if isinstance(item.get("detail_links"), list) else 0
                req["spec_count"] = max(req["spec_count"], len(item.get("detail_specs") or []))
                req["files"] = req["files"] or bool(item.get("detail_files"))
                req["link_count"] = max(req["link_count"], len(item.get("detail_links") or []) if isinstance(item.get("detail_links"), list) else 0)
        if changed:
            stats["data_files"] += 1
            if apply:
                _dump(path, items)

    page_paths = list(sorted((site_root / "pages").glob("*.yaml")))
    page_paths.extend(sorted((site_root / "lang").glob("*/pages/*.yaml")))
    for path in page_paths:
        req = requirements.get(path.stem)
        if not req:
            continue
        page = _load(path)
        templates = page.get("detail_templates") if isinstance(page, dict) else None
        if not isinstance(templates, list):
            continue
        changed = False
        for template in templates:
            if isinstance(template, dict) and _modernize_content_template(template, req["spec_count"], req["files"], req["link_count"]):
                changed = True
                stats["templates"] += 1
        if changed:
            stats["page_files"] += 1
            if apply:
                _dump(path, page)
    return stats


def migrate(site_root: Path, apply: bool) -> dict[str, int]:
    stats = {
        "data_files": 0,
        "items": 0,
        "legacy_modules": 0,
        "page_files": 0,
        "templates": 0,
    }
    datasets_with_body: set[str] = set()

    for path in sorted((site_root / "lang").glob("*/data/*.yaml")):
        items = _load(path)
        if not isinstance(items, list):
            continue
        changed_items = 0
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("body") not in (None, ""):
                datasets_with_body.add(path.stem)
            modules = item.get("modules")
            if not isinstance(modules, list) or not modules:
                continue
            types = _module_types(modules)
            unsupported = types - LEGACY_ITEM_MODULES
            if unsupported:
                raise RuntimeError(f"{path}: unsupported per-item modules: {sorted(unsupported)}")
            changed_items += 1
            stats["legacy_modules"] += len(modules)

        if not changed_items:
            continue
        stats["data_files"] += 1
        stats["items"] += changed_items
        if apply:
            original = path.read_text(encoding="utf-8")
            migrated = _remove_top_level_item_modules(original)
            parsed = yaml.safe_load(migrated)
            if parsed != _without_modules(items):
                raise RuntimeError(f"{path}: surgical YAML migration verification failed")
            path.write_text(migrated, encoding="utf-8")

    page_paths = list(sorted((site_root / "pages").glob("*.yaml")))
    page_paths.extend(sorted((site_root / "lang").glob("*/pages/*.yaml")))
    for path in page_paths:
        if path.stem not in datasets_with_body:
            continue
        page = _load(path)
        if not isinstance(page, dict):
            continue
        templates = page.get("detail_templates")
        created_templates = False
        if not isinstance(templates, list) or not templates:
            # Layout is shared from the base page. Language page overrides
            # should keep inheriting it instead of receiving duplicate copies.
            if path.parent == site_root / "pages":
                page["detail_templates"] = [_default_migration_template(path.stem)]
                templates = page["detail_templates"]
                created_templates = True
            else:
                continue
        changed = created_templates
        for template in templates:
            if not isinstance(template, dict):
                continue
            # Empty custom templates are intentionally empty.  All populated
            # templates must expose the historical body field.
            if _ensure_body_component(template):
                changed = True
                stats["templates"] += 1
        if changed:
            stats["page_files"] += 1
            if apply:
                _dump(path, page)

    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True, help="site id, for example 6")
    parser.add_argument("--apply", action="store_true", help="write changes; otherwise audit only")
    parser.add_argument("--convert-body", action="store_true", help="split legacy body HTML into component fields")
    args = parser.parse_args()

    site_root = Path(__file__).resolve().parents[1] / "sites" / str(args.site)
    if not site_root.is_dir():
        raise SystemExit(f"site not found: {site_root}")
    stats = convert_bodies(site_root, args.apply) if args.convert_body else migrate(site_root, args.apply)
    mode = "migrated" if args.apply else "audit"
    print(f"{mode}: " + ", ".join(f"{key}={value}" for key, value in stats.items()))


if __name__ == "__main__":
    main()
