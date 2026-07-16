"""
软著源代码文档生成器。

功能：从 app/core/ 选取核心 Python 文件，生成规范格式的源代码文档。
规格：前 30 页 + 后 30 页 = 60 页，每页 50 行。
输出：软著申请/02-源代码文档/源代码文档.txt

用法：在项目根目录执行
    python 软著申请/02-源代码文档/generate_source_doc.py
"""

import os
import sys

# ---------- 配置 ----------
LINES_PER_PAGE = 50
TOTAL_PAGES = 60
FRONT_PAGES = 30
BACK_PAGES = 30

# 软件信息（出现在页眉）
SOFTWARE_NAME = "小企业静态网站生成与管理平台"
VERSION = "V1.0"

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 输出路径
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "软著申请", "02-源代码文档")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "源代码文档.txt")

# ---------- 前 30 页：核心 Python 文件（按重要性排序）----------
# routes.py 是主要路由（7261 行），models.py 含完整认证数据模型（302 行）
FRONT_FILES = [
    "app/core/routes.py",           # 7261 行 - 全部路由（认证/账户中心/页面编辑/构建）
    "app/core/models.py",           # 302 行  - 数据模型（AccountIdentity/PasswordCredential/VerificationCode/UserSession）
    "app/core/builder.py",          # 2678 行 - 静态生成核心
    "app/core/block_renderer.py",   # 855 行  - Block 渲染
    "app/core/menu.py",             # 580 行  - 菜单系统
    "app/core/site_storage.py",     # 511 行  - 站点存储
]

# ---------- 后 30 页：辅助 Python 文件 ----------
BACK_FILES = [
    "app/core/translator.py",       # 392 行  - AI 翻译
    "app/core/block_parser.py",     # 381 行  - Block 解析
    "app/core/media_service.py",    # 332 行  - 媒体服务
    "app/core/template_loader.py",  # 200 行  - 模板加载
    "app/core/icon_registry.py",    # 138 行  - 图标注册
    "app/core/style_registry.py",   # 127 行  - 样式注册
    "app/core/config.py",           # 94 行   - 配置
    "app/core/datasets.py",         # 74 行   - 数据集
    "app/core/admin_routes.py",     # 34 行   - 管理员路由
    "app/core/db.py",               # 17 行   - 数据库初始化
    "app/static/js/admin_modules.js",  # 后台 JS（补充到后 30 页）
]


def read_file_lines(filepath):
    """读取文件所有行，UTF-8 编码。"""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        return f.readlines()


def format_page_header(page_num):
    """生成页眉。"""
    header = "=" * 70
    title = "{}  {}".format(SOFTWARE_NAME, VERSION)
    title_line = "{:^70}".format(title)
    page_line = "{:>70}".format("第 {} 页 / 共 {} 页".format(page_num, TOTAL_PAGES))
    return "{}\n{}\n{}\n{}\n".format(header, title_line, page_line, header)


def generate_pages(file_list, start_page, max_pages, label):
    """
    从文件列表中逐行读取，生成 max_pages 页。

    返回:
        (pages_text, remaining_lines_info)
    """
    pages = []
    page_num = start_page
    all_lines = []
    file_boundaries = []
    for fname in file_list:
        fpath = os.path.join(PROJECT_ROOT, fname)
        if not os.path.isfile(fpath):
            print("  [警告] 文件不存在，跳过: {}".format(fname))
            continue
        lines = read_file_lines(fpath)
        file_boundaries.append((fname, len(all_lines)))
        all_lines.append("// ====== {} ======\n".format(fname))
        all_lines.append("\n")
        all_lines.extend(lines)
        all_lines.append("\n")

    total_lines = len(all_lines)
    lines_used = 0
    page_idx = 0

    while page_idx < max_pages and lines_used < total_lines:
        chunk_start = lines_used
        chunk_end = min(lines_used + LINES_PER_PAGE, total_lines)
        chunk = all_lines[chunk_start:chunk_end]

        page_text = format_page_header(page_num)
        for line in chunk:
            page_text += line
        while len(chunk) < LINES_PER_PAGE:
            page_text += "\n"
            chunk.append("\n")

        pages.append(page_text)
        lines_used = chunk_end
        page_num += 1
        page_idx += 1

    remaining = total_lines - lines_used
    return pages, remaining


def main():
    print("=" * 60)
    print("软著源代码文档生成器")
    print("软件: {} {}".format(SOFTWARE_NAME, VERSION))
    print("规格: 前 {} 页 + 后 {} 页 = {} 页，每页 {} 行".format(
        FRONT_PAGES, BACK_PAGES, TOTAL_PAGES, LINES_PER_PAGE))
    print("=" * 60)
    print()

    # 生成前 30 页
    print("[1/2] 生成前 {} 页（核心模块）...".format(FRONT_PAGES))
    front_pages, front_remaining = generate_pages(FRONT_FILES, 1, FRONT_PAGES, "前")
    print("  实际生成: {} 页".format(len(front_pages)))
    if front_pages:
        last_page = front_pages[-1]
        line_count = last_page.count('\n')
        print("  最后一页行数: {}".format(line_count))
    print()

    # 生成后 30 页
    print("[2/2] 生成后 {} 页（辅助模块）...".format(BACK_PAGES))
    back_start_page = len(front_pages) + 1
    back_pages, back_remaining = generate_pages(BACK_FILES, back_start_page, BACK_PAGES, "后")
    print("  实际生成: {} 页".format(len(back_pages)))
    print()

    # 合并并写入
    all_pages = front_pages + back_pages
    output = ""
    for pg in all_pages:
        output += pg
        output += "\f\n"  # 分页符（Word/WPS 可识别）

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(output)

    # 统计信息
    total_lines = sum(pg.count('\n') for pg in all_pages)
    print("=" * 60)
    print("生成完成！")
    print("  输出文件: {}".format(OUTPUT_FILE))
    print("  总页数: {} 页".format(len(all_pages)))
    print("  总行数: ~{} 行".format(total_lines))
    print("  文件大小: {:.1f} KB".format(os.path.getsize(OUTPUT_FILE) / 1024.0))
    print()
    print("下一步：")
    print("  1. 用 Word / WPS 打开 源代码文档.txt")
    print("  2. 设置页边距（上下 2.54cm，左右 3.17cm）")
    print("  3. 字体设为等宽字体（Courier New / SimSun，小四号 / 10pt）")
    print("  4. 导出为 PDF")
    print("=" * 60)


if __name__ == '__main__':
    main()
