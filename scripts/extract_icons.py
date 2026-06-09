"""从现有 block 模板里抽取 icon 名→SVG 映射，生成 app/core/icon_registry.py.

一次性脚本。原样提取 SVG（不改写），处理别名（icon == 'a' or icon == 'b'）。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOCKS = ROOT / 'site_templates' / 'dengtec' / 'blocks'
SOURCES = ['feature_grid', 'stat_counter', 'process_steps']

# 匹配一段 {% if/elif icon == 'x' [or icon == 'y'] %} <svg...>...</svg>
# 分两步：先按 {% ... %} 切块，提取每个分支的图标名集合 + 紧随的 SVG
BRANCH_RE = re.compile(
    r"\{%\s*(?:el)?if\s+(icon\s*==\s*'[^']+'(?:\s+or\s+icon\s*==\s*'[^']+')*)\s*%\}"
    r"\s*(<svg.*?</svg>)",
    re.S,
)
NAME_RE = re.compile(r"icon\s*==\s*'([^']+)'")

icons = {}  # name → svg（首次出现优先，后面同名跳过）

for block in SOURCES:
    tpl = (BLOCKS / block / 'template.html').read_text(encoding='utf-8')
    for m in BRANCH_RE.finditer(tpl):
        cond, svg = m.group(1), m.group(2).strip()
        names = NAME_RE.findall(cond)
        # 原样提取 SVG, 不改写尺寸。
        # 历史教训(#7): 这里曾用全文 re.sub(r'\s(width|height)="..."') 想剥掉根 <svg>
        # 的写死尺寸, 但正则对全文生效, 把 <rect>/<circle> 等内部元素的内在 width/height
        # 也删了, 导致 briefcase/cpu/camera 等 11 个图标的零面积图形不渲染、显示残缺。
        # 现成 icon_registry.py 的根 <svg> 本就保留 24×24(由 CSS 覆盖), 故这里原样保留,
        # 既复现现状成品, 又彻底杜绝误删内部元素尺寸。
        svg_norm = svg
        for name in names:
            if name not in icons:
                icons[name] = svg_norm

# 生成 icon_registry.py
lines = [
    '"""图标注册表：图标名 → SVG 字符串.',
    '',
    'data-* 改造方案 Phase 3：data-type="icon" 字段存图标名，渲染器据此查表注入 SVG。',
    '由 scripts/extract_icons.py 从原 block 模板的硬编码 SVG 分支自动抽取生成。',
    'SVG 根标签保留 width="24" height="24"，可由 CSS 覆盖（.service-icon/.sc-icon/.ps-icon）。',
    '',
    '新增图标：在 ICON_REGISTRY 加一条 名→SVG 即可，全部 block 共用。',
    '"""',
    '',
    '# 名 → SVG。别名（如 zap/lightning）各占一条，指向同一 SVG。',
    'ICON_REGISTRY = {',
]
for name in sorted(icons):
    svg = icons[name].replace('\\', '\\\\').replace("'", "\\'")
    # 单行化 SVG（去多余空白）
    svg = re.sub(r'\s+', ' ', svg).strip()
    lines.append(f"    '{name}': '{svg}',")
lines.append('}')
lines.append('')
lines.append('')
lines.append('def get_icon_svg(name):')
lines.append('    """按图标名取 SVG；未注册返回 None（渲染器据此隐藏或留空）。"""')
lines.append('    return ICON_REGISTRY.get((name or \'\').strip())')
lines.append('')
lines.append('')
lines.append('def icon_names():')
lines.append('    """全部图标名（供编辑器图标选择器列出）。"""')
lines.append('    return sorted(ICON_REGISTRY.keys())')
lines.append('')

out = ROOT / 'app' / 'core' / 'icon_registry.py'
out.write_text('\n'.join(lines), encoding='utf-8')
print(f'✓ 生成 {out}，共 {len(icons)} 个图标:')
print('  ' + ' '.join(sorted(icons)))
