"""端到端：开关打开，构建 site 1，验证 section_title 走 data-* 渲染正确。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.core.builder import build_site, _SCHEMA_CACHE

app = create_app()
with app.app_context():
    from flask import current_app
    current_app.config['ENABLE_DATA_ATTR_BLOCKS'] = True
    _SCHEMA_CACHE.clear()  # 清缓存，确保用最新模板

    out_root = build_site(1)
    print(f'构建输出: {out_root}')

    # about 页（默认语言子目录）。多语言模板输出在 <lang>/about/index.html 或 about.html
    candidates = list(Path(out_root).rglob('about*.html')) + list(Path(out_root).rglob('about/index.html'))
    assert candidates, '没找到 about 页输出'
    about_html = candidates[0].read_text(encoding='utf-8')
    print(f'\n检查 {candidates[0].relative_to(out_root)}')

    # 验证点：section_title 走了 data-* 渲染
    checks = [
        ('标题渲染', '专注展示道具电子化' in about_html),
        ('标签渲染', '关于我们' in about_html),
        ('描述渲染（subtitle→desc 已对齐）', '从方案设计到产品交付' in about_html),
        ('st-title 类保留', 'st-title' in about_html),
        ('无 data-* 残留', 'data-name' not in about_html and 'data-type' not in about_html),
        ('无未填的占位默认文字', '区块描述文字，介绍这一部分的内容' not in about_html),
    ]
    ok = True
    for name, cond in checks:
        print(f'  {"✓" if cond else "✗"} {name}')
        ok = ok and cond

    # 提取 section_title 那段看看
    import re
    m = re.search(r'<section class="section"[^>]*>.*?专注展示道具电子化.*?</section>', about_html, re.S)
    if m:
        print('\n--- 渲染出的 section_title 片段 ---')
        print(m.group(0)[:600])

    sys.exit(0 if ok else 1)
