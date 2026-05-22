"""用正则把带方向箭头的 margin 输入框加上 placeholder-light class"""
import re
import os

filepath = r'f:\dengtec\mycompany.website\app\templates\dashboard\panel_page_edit.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 匹配: class="form-control form-control-sm" ... placeholder="↑ 上" (或 →右 ↓下 ←左)
# 把 form-control-sm 替换为 form-control-sm placeholder-light
pattern = re.compile(
    r'class="form-control form-control-sm"'
    r'((?:(?!class=)[\s\S])*?)'   # 中间内容 (非贪婪, 不跨越 class 属性)
    r'placeholder="[↑→↓←] [上下左右]"'
)

def add_light_class(m):
    middle = m.group(1)
    # 在 form-control-sm 后面加 placeholder-light
    return 'class="form-control form-control-sm placeholder-light"' + middle + m.group(0)[m.end(1)+1:]

# 更简单的方式: 用 re.sub 替换
# 匹配 class="form-control form-control-sm" 后面跟着 (任意非贪心) placeholder="↑ 上" 等
new_content = re.sub(
    r'class="form-control form-control-sm"((?:(?!class=)[\s\S])*?placeholder="[↑→↓←] [上下左右]")',
    r'class="form-control form-control-sm placeholder-light"\1',
    content
)

count = len(re.findall(r'class="form-control form-control-sm placeholder-light"', new_content))
print(f'placeholder-light instances after replacement: {count}')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)
print('Done.')
