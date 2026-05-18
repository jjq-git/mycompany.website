import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

print("开始检查模板...")
for template in ['dengtec']:
    root = Path('site_templates') / template
    if not root.exists():
        print(f"⚠️ 跳过: {root} 不存在")
        continue
        
    loader_paths = [str(root/'templates'), str(root)]
    env = Environment(loader=FileSystemLoader(loader_paths), autoescape=select_autoescape(['html']))
    
    for name in ['index.html', 'about.html', '_modules.html']:
        target = root/'templates'/name
        if target.exists():
            try:
                env.get_template(name)
                print(f"✅ {template}/{name}")
            except Exception as e:
                print(f"❌ {template}/{name}: {e}")
                sys.exit(1)
    print(f"✅ {template} 检查完成")

print("🎉 所有模板检查通过")
