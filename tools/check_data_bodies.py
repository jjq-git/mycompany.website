"""检查各数据文件的 body 结构和翻译缺失情况"""
import yaml, re, os, sys
sys.stdout.reconfigure(encoding='utf-8')

files = [
    r'f:\dengtec\mycompany.website11\sites\6\lang\zh-CN\data\led-strip.yaml',
    r'f:\dengtec\mycompany.website11\sites\6\lang\zh-CN\data\spot-light.yaml',
    r'f:\dengtec\mycompany.website11\sites\6\lang\zh-CN\data\cable-connector.yaml',
    r'f:\dengtec\mycompany.website11\sites\6\lang\zh-CN\data\powerptrack.yaml',
    r'f:\dengtec\mycompany.website11\sites\6\lang\zh-CN\data\projects.yaml',
]

for f in files:
    with open(f, encoding='utf-8') as fp:
        data = yaml.safe_load(fp)
    items = data if isinstance(data, list) else data.get('items', [])
    name = os.path.basename(f)
    print(f'\n{"="*60}')
    print(f'FILE: {name} ({len(items)} items)')
    print(f'{"="*60}')
    for it in items[:2]:
        body = it.get('body', '') or ''
        title = it.get('title', '')
        desc = it.get('description', '') or ''
        category = it.get('category', '') or ''
        tags = it.get('tags', '') or ''
        print(f'  title: {title}')
        print(f'  desc: {desc[:100]}')
        print(f'  category: {category}')
        print(f'  tags: {tags}')
        if body:
            # Extract text between HTML tags for preview
            text = re.sub(r'<[^>]+>', '\n    ', body)
            text = re.sub(r'\n\s*\n', '\n', text)
            # Get first 500 chars
            preview = text[:500].strip()
            print(f'  body: {preview[:400]}')
        print()
