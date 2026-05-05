"""扫描 site_templates/ 目录, 同步元信息到数据库.

每个模板必须有 meta.yaml, 字段:
    display_name: "制造业-标准版"
    industry: manufacturing
    description: "..."
    cover_image: "/static/templates/manufacturing-standard.png"
    version: "1.0.0"
    is_public: true
"""
from pathlib import Path

import yaml
from flask import current_app

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
