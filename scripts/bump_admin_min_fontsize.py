# -*- coding: utf-8 -*-
"""后台文字最小 12px：把后台 CSS / 模板内联 style 里所有 font-size:11px 提到 12px。
只动 font-size 属性值，不碰 line-height/width 等其它 11px；兼容有无空格两种写法。"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 待处理文件：后台样式表 + 带内联 <style> 的后台模板
TARGETS = [
    'app/static/css/admin.css',
    'app/static/css/admin-account.css',
    'app/static/css/admin-seo.css',
    'app/static/css/admin-media.css',
    'app/templates/dashboard/content_workspace.html',
    'app/templates/dashboard/overview.html',
]

# 只匹配 font-size 后紧跟的 11px（允许冒号后有空格），替换为 12px
pattern = re.compile(r'(font-size:\s*)11px')

total = 0
for rel in TARGETS:
    p = ROOT / rel
    text = p.read_text(encoding='utf-8')
    new_text, n = pattern.subn(lambda m: m.group(1) + '12px', text)
    if n:
        p.write_text(new_text, encoding='utf-8')
    total += n
    print(f'{rel}: {n} 处')

print(f'合计 {total} 处')
