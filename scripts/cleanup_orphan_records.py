"""清理指向缺失模板的孤儿数据库记录（一次性脚本）。

删除 3 个孤儿 Site（template 在磁盘不存在 + 无 sites/ 真实数据）+ 3 个孤儿 Template。
安全保障：
- 删前双重校验：模板目录确实不存在 + sites/<id> 无真实 yaml 数据，任一不满足则跳过
- 先删 Site 再删 Template（满足 Site.template_name → templates.name 外键顺序）
- 不碰 sites/ 目录；只清理已删站点对应的 output/<id> 构建缓存
- 已先备份 instance/app.db.backup-20260529-orphan-cleanup
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.core.db import db
from app.core.models import Site, Template

ORPHAN_SITE_IDS = [2, 3, 4]
ORPHAN_TEMPLATE_NAMES = ['globex', 'serveco', 'tasty']

app = create_app()
with app.app_context():
    tdir = Path(app.config['TEMPLATES_DIR'])
    sdir = Path(app.config['SITES_DIR'])
    odir = Path(app.config['OUTPUT_DIR'])

    # 1. 删孤儿 Site（双重校验后）
    for sid in ORPHAN_SITE_IDS:
        site = db.session.get(Site, sid)
        if not site:
            print(f'site {sid}: 已不存在，跳过')
            continue
        # 校验 a：模板确实不存在
        tpl_exists = (tdir / site.template_name / 'meta.yaml').exists()
        # 校验 b：sites/<id> 无真实数据
        site_folder = sdir / str(sid)
        has_data = site_folder.exists() and any(site_folder.rglob('*.yaml'))
        if tpl_exists or has_data:
            print(f'✗ site {sid} (slug={site.slug}) 不满足删除条件 '
                  f'(模板存在={tpl_exists}, 有数据={has_data})，跳过保护')
            continue
        db.session.delete(site)
        # 清理对应 output 构建缓存（不碰 sites/）
        out_sub = odir / str(sid)
        if out_sub.exists():
            shutil.rmtree(out_sub)
            print(f'  清理 output/{sid}/')
        print(f'✓ 删除 site {sid} (slug={site.slug}, template={site.template_name})')

    db.session.commit()  # 先提交 Site 删除，再删 Template（外键顺序）

    # 2. 删孤儿 Template（确认磁盘无对应目录）
    for name in ORPHAN_TEMPLATE_NAMES:
        tpl = Template.query.filter_by(name=name).first()
        if not tpl:
            print(f'template {name}: 已不存在，跳过')
            continue
        if (tdir / name / 'meta.yaml').exists():
            print(f'✗ template {name} 磁盘上存在，跳过保护')
            continue
        # 确认没有 Site 还在引用它
        refs = Site.query.filter_by(template_name=name).count()
        if refs:
            print(f'✗ template {name} 仍被 {refs} 个站点引用，跳过')
            continue
        db.session.delete(tpl)
        print(f'✓ 删除孤儿 template {name}')

    db.session.commit()

    # 3. 验证清理结果
    print('\n===== 清理后剩余记录 =====')
    print('Templates:', [t.name for t in Template.query.all()])
    print('Sites:', [(s.id, s.slug, s.template_name) for s in Site.query.all()])
