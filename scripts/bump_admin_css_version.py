# -*- coding: utf-8 -*-
"""统一升级后台 4 个 CSS 的缓存版本号，让最小字号 12px 的改动在所有引用页面生效。
处理带 ?v=xxx 和不带 ?v= 两种写法，全部改成今天的新号。"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / 'app' / 'templates'
NEW = '20260721-minfont'

# 需要统一版本号的 4 个后台样式表文件名（不含 .css）
NAMES = ['admin', 'admin-account', 'admin-seo', 'admin-media']

total = 0
for html in TPL.rglob('*.html'):
    text = html.read_text(encoding='utf-8')
    orig = text
    for name in NAMES:
        # 形如 css/admin-account.css') }}?v=旧号  或  css/admin-account.css') }}（无版本号）
        # 注意 admin 要避免误伤 admin-account 等，用 (?!-) 断言后面不是连字符
        if name == 'admin':
            filename = r"css/admin\.css"
        else:
            filename = r"css/" + re.escape(name) + r"\.css"
        # 匹配 filename='css/xxx.css' 后面的 }} 到可能存在的 ?v=... 引号前
        pat = re.compile(r"(filename='" + filename + r"'\)\s*\}\})(\?v=[^\"']*)?")
        text = pat.sub(lambda m: m.group(1) + '?v=' + NEW, text)
    if text != orig:
        html.write_text(text, encoding='utf-8')
        n = sum(text.count('?v=' + NEW) for _ in [0])
        print(f'{html.relative_to(ROOT)}: 已更新')
        total += 1

print(f'共更新 {total} 个模板文件')
