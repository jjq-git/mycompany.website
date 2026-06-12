"""扫描 site_templates/ 目录, 同步元信息到数据库.

每个模板必须有 meta.yaml, 字段:
    display_name: "制造业-标准版"
    industry: manufacturing
    description: "..."
    cover_image: "/static/templates/manufacturing-standard.png"
    version: "1.0.0"
    is_public: true
"""
from dataclasses import asdict
from pathlib import Path

import yaml
from flask import current_app

from . import block_parser, style_registry
from .db import db
from .models import Template


def scan_templates():
    """扫描 site_templates/, 把每个含 meta.yaml 的子目录登记到数据库.

    返回: 同步后所有 Template 实例的列表.
    """
    templates_dir = Path(current_app.config['TEMPLATES_DIR'])
    if not templates_dir.exists():
        return []

    found = []
    for folder in sorted(templates_dir.iterdir()):
        if not folder.is_dir() or folder.name.startswith('.'):
            continue
        meta_path = folder / 'meta.yaml'
        if not meta_path.exists():
            continue

        meta = yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {}

        template = Template.query.filter_by(name=folder.name).first()
        if template is None:
            template = Template(name=folder.name)
            db.session.add(template)

        template.display_name = meta.get('display_name', folder.name)
        template.industry = meta.get('industry', 'other')
        template.description = meta.get('description', '')
        template.cover_image = meta.get('cover_image', '')
        template.current_version = meta.get('version', '1.0.0')
        template.is_public = meta.get('is_public', True)
        found.append(template)

    db.session.commit()
    return found


def scan_blocks(template_name):
    """扫描模板的 blocks/ 目录, 返回模块列表.

    返回: list of dict, 每个模块:
        name, category, icon, description, fields, variants, is_data_attr, schema

    is_data_attr / schema: 若 template.html 为 data-* 声明式写法（不含 Jinja2 标记），
    附加解析出的 schema（供编辑器 schema 驱动表单）；旧 Jinja2 block 这两项为 False/None。
    """
    blocks_dir = Path(current_app.config['TEMPLATES_DIR']) / template_name / 'blocks'
    if not blocks_dir.exists():
        return []

    blocks = []
    for block_dir in sorted(blocks_dir.iterdir()):
        if not block_dir.is_dir() or block_dir.name.startswith('.'):
            continue
        meta_path = block_dir / 'meta.yaml'
        if not meta_path.exists():
            continue

        meta = yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {}

        # 检测 template.html 是否为 data-* 声明式，是则解析 schema。
        # 解析失败（如旧式 Jinja2）静默降级，不影响扫描——混合模式共存。
        is_data_attr = False
        schema = None
        tpl_path = block_dir / 'template.html'
        if tpl_path.exists():
            html = tpl_path.read_text(encoding='utf-8')
            if block_parser.is_data_attr_block(html):
                try:
                    schema = block_parser.parse(html)
                    is_data_attr = True
                except Exception:
                    is_data_attr = False
                    schema = None

        # 自动从 data-style 派生样式变体（select/switch 类 control），
        # 与 meta.yaml 声明的结构变体合并：meta.yaml 优先（供手动覆盖）。
        meta_variants = meta.get('variants', [])
        meta_variant_keys = {v['key'] for v in meta_variants if isinstance(v, dict)}
        style_variants = []
        if schema is not None:
            all_tokens = list(schema.style_tokens or [])
            for t in getattr(schema, 'element_style_tokens', []) or []:
                if t not in all_tokens:
                    all_tokens.append(t)
            for token in all_tokens:
                sdef = style_registry.get_style_def(token)
                if not sdef or sdef.get('control') not in ('select', 'switch'):
                    continue
                for opt in sdef.get('options', []):
                    style_variants.append({
                        'key': f'{token}_{opt["value"]}',
                        'label': opt.get('text', opt['value']),
                        'source': 'style',
                        'data_preset': {f'style_{token}': opt['value']},
                    })
        all_variants = meta_variants + [
            v for v in style_variants if v['key'] not in meta_variant_keys
        ]

        blocks.append({
            'name': block_dir.name,
            'display_name': meta.get('name', block_dir.name),
            'category': meta.get('category', 'content'),
            'icon': meta.get('icon', ''),
            'description': meta.get('description', ''),
            'fields': meta.get('fields', []),
            'variants': all_variants,
            'is_data_attr': is_data_attr,
            'schema': asdict(schema) if schema is not None else None,
        })

    return blocks


def scan_block_schema(template_name, block_name):
    """只解析单个 block 的 schema（不扫描整个目录）。

    用于 API 端点按需取 schema。block 非 data-* 写法或解析失败返回 None。
    """
    tpl_path = (Path(current_app.config['TEMPLATES_DIR']) / template_name
                / 'blocks' / block_name / 'template.html')
    if not tpl_path.exists():
        return None
    html = tpl_path.read_text(encoding='utf-8')
    if not block_parser.is_data_attr_block(html):
        return None
    try:
        schema = block_parser.parse(html)
        return asdict(schema)
    except Exception:
        return None
