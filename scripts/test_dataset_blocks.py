"""Phase 4 数据集驱动 block 回归：data_grid / product_grid 用真实 seed 数据集渲染。

锁住渲染器新增能力：
- data-source 数据集绑定（具名 products / 空串选 dataset）
- data-href-template（按项字段 + base_url/lang/current_path 拼链接）
- data-fallback（title←name、desc←summary/excerpt/description 字段回退）
- 标量列表项（tags 字符串列表）
- data-page-size（最多展示条数）
- 静态 href 模板（"查看全部"仅依赖上下文变量）
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml
from app import create_app
from app.core import block_parser as bp, block_renderer as br

app = create_app()
PASS = FAIL = 0
def chk(name, cond, detail=''):
    global PASS, FAIL
    if cond: PASS += 1; print(f'  ✓ {name}')
    else: FAIL += 1; print(f'  ✗ {name}  {detail}')

with app.app_context():
    bdir = Path(app.config['TEMPLATES_DIR']) / 'dengtec' / 'blocks'
    seed = Path(app.config['TEMPLATES_DIR']) / 'dengtec' / 'seed_data' / 'data'
    ds = {n: yaml.safe_load((seed / f'{n}.yaml').read_text(encoding='utf-8'))
          for n in ('products', 'portfolio', 'posts')}
    ctx = {'all_datasets': ds, 'vars': {'base_url': '', 'lang': 'zh-CN', 'current_path': '/portfolio/'}}

    def render(block, data):
        html = (bdir / block / 'template.html').read_text(encoding='utf-8')
        return br.render(html, bp.parse(html), data, ctx)

    print('=== product_grid（data-source=products 固定数据集）===')
    out = render('product_grid', {'title': '产品展示'})
    chk('5 张产品卡', out.count('class="dg-card"') == 5, out.count('class="dg-card"'))
    chk('产品名注入（fallback 无关）', '静音仓 V2' in out)
    chk('每项 href 模板化', 'href="/zh-CN/products/silent-booth/"' in out)
    chk('静态"查看全部"链接', 'href="/zh-CN/products/"' in out)
    chk('无 data-* 残留', 'data-name' not in out and 'data-href-template' not in out and 'data-fallback' not in out)

    print('\n=== data_grid（data-source="" → 选 portfolio）===')
    out = render('data_grid', {'title': '近期项目', 'dataset': 'portfolio'})
    chk('6 张案例卡', out.count('class="dg-card"') == 6, out.count('class="dg-card"'))
    chk('标题 fallback（portfolio 用 title）', '苏州博物馆静音展示项目' in out)
    chk('current_path 链接', 'href="/zh-CN/portfolio/museum-2024/"' in out)
    chk('日期注入', '2024-08' in out)
    chk('标量列表 tags', '博物馆' in out and '静音仓' in out)
    chk('portfolio 无 category → 不渲染分类', 'dg-card-category">展示道具' not in out)

    print('\n=== data_grid → posts（desc fallback 到 excerpt）===')
    out = render('data_grid', {'title': '最新动态', 'dataset': 'posts'})
    chk('4 张文章卡', out.count('class="dg-card"') == 4, out.count('class="dg-card"'))
    chk('desc 走 fallback（excerpt/description）', 'dg-card-desc' in out)
    chk('无 data-* 残留', 'data-name' not in out and 'data-fallback' not in out)

    print('\n=== page_size 上限 + 空数据集隐藏 ===')
    out = render('product_grid', {'title': 'x'})  # products 仅 5 条 < page-size 6 → 全显示
    chk('page_size=6 不截断 5 条', out.count('class="dg-card"') == 5)
    out_empty = render('data_grid', {'title': '空', 'dataset': 'nonexistent'})
    chk('数据集不存在 → 0 卡片', out_empty.count('class="dg-card"') == 0)

print(f'\n{"="*40}\n通过 {PASS}，失败 {FAIL}')
sys.exit(1 if FAIL else 0)
