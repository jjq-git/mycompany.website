"""
软著申请 Word 文档批量生成器。
生成 5 个 .docx 文件到 软著申请/ 目录。
"""

import os
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ---------- 公司信息 ----------
COMPANY_NAME = "昆山德恩基电子科技有限公司"
COMPANY_CREDIT_CODE = "91320583301852194E"
COMPANY_ADDRESS = "昆山开发区郭泽路15号E栋厂房二楼"
COMPANY_LEGAL_REP = "谷永林"
COMPANY_TEL = "0512-50133094"

SOFTWARE_FULL_NAME = "小企业静态网站生成与管理平台"
SOFTWARE_SHORT_NAME = "静站宝"
SOFTWARE_VERSION = "V1.0"

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))


def set_cell_border(cell, **kwargs):
    """设置单元格边框"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('start', 'top', 'end', 'bottom', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            element = OxmlElement('w:{}'.format(edge))
            for attr in ['sz', 'val', 'color', 'space']:
                if attr in edge_data:
                    element.set(qn('w:{}'.format(attr)), str(edge_data[attr]))
            tcBorders.append(element)
    tcPr.append(tcBorders)


def add_table_cell_text(cell, text, bold=False, font_size=10.5, font_name='宋体', alignment=None):
    """在表格单元格中添加格式化文本"""
    # 清除默认空段落
    for p in cell.paragraphs:
        p.clear()
    p = cell.paragraphs[0]
    run = p.add_run(str(text))
    run.bold = bold
    run.font.size = Pt(font_size)
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
    if alignment is not None:
        p.alignment = alignment


def add_paragraph(doc, text, font_name='宋体', font_size=12, bold=False,
                  alignment=None, space_after=6, first_line_indent=None, color=None):
    """添加段落"""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
    run.font.size = Pt(font_size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)
    if alignment is not None:
        p.alignment = alignment
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    if first_line_indent:
        pf.first_line_indent = Pt(first_line_indent)
    return p


def add_heading_styled(doc, text, level=1, font_name='黑体'):
    """添加带中文字体的标题"""
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = font_name
        run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
    return h


def make_table(doc, headers, rows, col_widths=None):
    """创建格式化表格"""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers), style='Table Grid')
    # 表头
    for i, h in enumerate(headers):
        add_table_cell_text(table.rows[0].cells[i], h, bold=True, font_size=10.5, font_name='黑体',
                            alignment=WD_ALIGN_PARAGRAPH.CENTER)
    # 数据行
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            add_table_cell_text(table.rows[r + 1].cells[c], val, font_size=10.5)
    if col_widths:
        for row in table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph()
    return table


def set_page_margin(doc, top=2.54, bottom=2.54, left=3.17, right=3.17):
    """设置页边距（cm）"""
    for section in doc.sections:
        section.top_margin = Cm(top)
        section.bottom_margin = Cm(bottom)
        section.left_margin = Cm(left)
        section.right_margin = Cm(right)


def add_page_header_footer(doc, header_text):
    """添加页眉页脚"""
    for section in doc.sections:
        header = section.header
        header.is_linked_to_previous = False
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = hp.add_run(header_text)
        run.font.size = Pt(9)
        run.font.name = '宋体'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
        # 页脚 - 页码
        footer = section.footer
        footer.is_linked_to_previous = False
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = fp.add_run('— {} —'.format(COMPANY_NAME))
        run.font.size = Pt(9)
        run.font.name = '宋体'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')


# ================================================================
# 文件 01：申请信息采集及确认表
# ================================================================
def generate_01_application_form():
    doc = Document()
    set_page_margin(doc)

    # 标题
    add_paragraph(doc, '计算机软件著作权登记', font_name='黑体', font_size=22,
                  bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    add_paragraph(doc, '申请信息采集及确认表', font_name='黑体', font_size=18,
                  bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=16)

    # ---- 一、软件基本信息 ----
    add_heading_styled(doc, '一、软件基本信息', level=1)

    info_table = [
        ['软件全称', SOFTWARE_FULL_NAME, '版本号', SOFTWARE_VERSION],
        ['软件简称', SOFTWARE_SHORT_NAME, '分类号', '30200-0000'],
        ['软件类型', '应用软件', '开发完成日期', '2026年07月16日'],
        ['首次发表日期', '未发表', '发表状态', '未发表'],
    ]
    make_table(doc, ['项目', '内容', '项目', '内容'], info_table, col_widths=[2.8, 4.8, 2.8, 4.8])

    add_paragraph(doc, '软件用途简述：', font_name='黑体', font_size=12, bold=True)
    add_paragraph(doc,
        '本软件是面向小企业主的网站搭建与管理平台。用户无需编写代码，通过填表方式即可创建、'
        '编辑和发布企业展示型网站。软件将用户填写的内容生成为纯静态 HTML/CSS/JS 文件，'
        '可部署到任何 CDN 或 Web 服务器，不依赖后端运行时环境。目标用户为制造业、贸易、'
        '服务业、餐饮业等不会编程的小企业老板。', first_line_indent=21)

    # ---- 二、著作权人信息 ----
    add_heading_styled(doc, '二、著作权人信息', level=1)

    owner_table = [
        ['著作权人名称', COMPANY_NAME],
        ['统一社会信用代码', COMPANY_CREDIT_CODE],
        ['注册地址', COMPANY_ADDRESS],
        ['法定代表人', COMPANY_LEGAL_REP],
        ['联系电话', COMPANY_TEL],
        ['证件类型', '统一社会信用代码证书'],
        ['著作权人类型', '法人'],
    ]
    make_table(doc, ['项目', '内容'], owner_table, col_widths=[3.5, 12.5])

    # ---- 三、开发者信息 ----
    add_heading_styled(doc, '三、开发者信息', level=1)
    dev_table = [
        ['开发者名称', COMPANY_NAME],
        ['开发者类型', '法人——与著作权人相同'],
    ]
    make_table(doc, ['项目', '内容'], dev_table, col_widths=[3.5, 12.5])

    # ---- 四、运行环境 ----
    add_heading_styled(doc, '四、运行环境', level=1)

    add_paragraph(doc, '1. 硬件环境（服务器端）', font_name='黑体', font_size=11, bold=True)
    add_paragraph(doc,
        'CPU：Intel Xeon / AMD EPYC 或同等性能云服务器（2 核以上）；'
        '内存：2 GB 以上；硬盘：20 GB 以上可用空间；网络：公网 IP + 域名。', first_line_indent=21)

    add_paragraph(doc, '2. 硬件环境（客户端）', font_name='黑体', font_size=11, bold=True)
    add_paragraph(doc,
        '普通 PC / Mac，支持现代浏览器（Chrome 90+ / Firefox 90+ / Edge 90+），'
        '屏幕分辨率 1280×720 以上。', first_line_indent=21)

    add_paragraph(doc, '3. 软件环境（服务器端）', font_name='黑体', font_size=11, bold=True)
    add_paragraph(doc,
        '操作系统：Ubuntu 20.04+ / CentOS 7+ / Windows Server 2016+；'
        'Python 3.9 及以上；Web 服务器：Nginx（反向代理）+ Gunicorn；'
        '数据库：SQLite 3。', first_line_indent=21)

    add_paragraph(doc, '4. 软件环境（客户端）', font_name='黑体', font_size=11, bold=True)
    add_paragraph(doc,
        '操作系统：Windows 10+ / macOS 11+ / Linux；'
        '浏览器：Chrome 90+ / Firefox 90+ / Edge 90+。', first_line_indent=21)

    # ---- 五、开发信息 ----
    add_heading_styled(doc, '五、开发信息', level=1)

    dev_info_table = [
        ['编程语言', 'Python 3.9+（后端核心）、JavaScript（前端交互）、HTML+CSS（模板与样式）、YAML（数据存储）'],
        ['代码行数',
         '总计约 128,000 行（Python 21,598 行 / HTML 31,505 行 / CSS 24,357 行 / JavaScript 4,358 行 / YAML 20,666 行）'],
        ['开发工具', 'Visual Studio Code、Git、Flask CLI、Chrome DevTools'],
        ['开发起止日期', '2026年05月05日 — 2026年07月16日'],
        ['开发周期', '约 2.5 个月，共 291 次提交'],
    ]
    make_table(doc, ['项目', '内容'], dev_info_table, col_widths=[3.5, 12.5])

    # ---- 六、技术特点 ----
    add_heading_styled(doc, '六、技术特点', level=1)

    features = [
        '1. 静态站点生成：将用户内容编译为纯 HTML 文件输出，无需服务器端运行时，网站加载速度快、安全性高。',
        '2. 多因子账户身份系统：支持邮箱和手机号双渠道注册与登录，统一 AccountIdentity 身份标识管理，支持绑定多个邮箱/手机号、设置主身份和解除非主身份绑定。',
        '3. 安全认证体系：采用"邮箱/手机号 + 密码"主登录方式，辅以 6 位一次性验证码通道；密码使用 Werkzeug 自适应哈希算法存储，支持 30 天多设备持久会话和远程撤销。',
        '4. 一次性验证码系统：注册、登录、找回密码和身份绑定统一走验证码通道；验证码 10 分钟有效、最多 5 次尝试、按账号限流，生成新码自动作废旧码。',
        '5. 账户中心工作区：独立 iframe 隔离的账户管理界面，覆盖个人资料、我的站点、账号安全、回收站四大板块。',
        '6. 模块化页面构建（Block 系统）：页面由可复用的功能块组装而成，用户只需选择模块并填写内容。',
        '7. 数据文件存储：网站内容存储为 YAML 文件而非数据库记录，平台关停后用户数据不丢失。',
        '8. 站点软删除与回收站：删除站点仅设置标记，数据库记录和磁盘文件完整保留，支持一键恢复。',
        '9. 一键导出 ZIP：用户可将完整网站打包下载，部署到任意 CDN。',
        '10. 字体子集化：自动提取网站实际使用的字符，将中文字体从 5-10MB 压缩至 15KB 以下。',
        '11. 多语言翻译：集成翻译引擎，自动翻译网站内容到多语言版本。',
        '12. 模板系统：支持多套网站模板，用户可切换模板而不丢失内容数据。',
    ]
    for f in features:
        add_paragraph(doc, f, first_line_indent=21, font_size=11)

    # ---- 七、主要功能模块 ----
    add_heading_styled(doc, '七、主要功能模块', level=1)

    modules = [
        ['1', '用户认证系统', '邮箱/手机号注册登录、验证码找回密码、多设备会话管理'],
        ['2', '账户中心', '个人资料编辑、站点管理、账号安全设置、回收站'],
        ['3', '身份管理', '多邮箱/手机号绑定、主身份设置、身份验证与解绑'],
        ['4', '会话管理', '30 天多设备持久登录、设备列表查看、远程撤销'],
        ['5', '站点管理', '创建/删除/切换站点、基本信息设置（Logo、主色、菜单）'],
        ['6', '页面编辑器', '可视化页面布局，添加/删除/排序功能模块（Block）'],
        ['7', '数据集管理', '产品列表、文章列表等结构化数据的增删改查'],
        ['8', '媒体库', '图片上传、管理、自动压缩优化'],
        ['9', '模板选择', '多套网站模板预览与切换'],
        ['10', '静态站点生成', 'Jinja2 模板引擎渲染，输出纯静态 HTML'],
        ['11', '一键导出', '打包完整站点为 ZIP 文件下载'],
        ['12', '字体子集化', '中文字体按需提取，大幅减小字体文件体积'],
        ['13', '多语言翻译', '网站内容多语言自动翻译'],
        ['14', '站点回收站', '软删除与恢复，数据不丢失'],
    ]
    make_table(doc, ['序号', '功能模块', '说明'], modules, col_widths=[1, 4, 11])

    # 签章区
    add_paragraph(doc, '')
    add_paragraph(doc, '以上信息确认无误。', font_size=11, space_after=20)
    add_paragraph(doc, '')
    add_paragraph(doc,
        '著作权人（盖章）：{}'.format(COMPANY_NAME),
        font_size=11, bold=True, space_after=12)
    add_paragraph(doc, '')
    add_paragraph(doc, '日期：      年    月    日', font_size=11)

    out = os.path.join(OUTPUT_DIR, '01_申请信息采集及确认表.docx')
    doc.save(out)
    print('[OK] {}'.format(out))


# ================================================================
# 文件 02：软件设计说明书
# ================================================================
def generate_02_design_spec():
    doc = Document()
    set_page_margin(doc)
    add_page_header_footer(doc, '{} {} 软件设计说明书'.format(SOFTWARE_FULL_NAME, SOFTWARE_VERSION))

    # 封面
    for _ in range(6):
        add_paragraph(doc, '', font_size=12)
    add_paragraph(doc, '软件设计说明书', font_name='黑体', font_size=26,
                  bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=20)
    add_paragraph(doc, SOFTWARE_FULL_NAME, font_name='黑体', font_size=18,
                  bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)
    add_paragraph(doc, SOFTWARE_VERSION, font_name='宋体', font_size=14,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=40)
    cover_info = [
        '著作权人：{}'.format(COMPANY_NAME),
        '开发单位：{}'.format(COMPANY_NAME),
        '完成日期：2026年07月16日',
    ]
    for line in cover_info:
        add_paragraph(doc, line, font_size=12, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)

    doc.add_page_break()

    # ---- 1. 引言 ----
    add_heading_styled(doc, '1. 引言', level=1)

    add_heading_styled(doc, '1.1 编写目的', level=2)
    add_paragraph(doc,
        '本文档旨在详细描述"{}"的系统设计，包括架构设计、'
        '模块划分、数据模型、关键技术决策等内容。文档面向开发人员、系统维护人员和技术评审人员，'
        '作为软件著作权申请的技术支撑材料。'.format(SOFTWARE_FULL_NAME),
        first_line_indent=21)

    add_heading_styled(doc, '1.2 软件概述', level=2)
    add_paragraph(doc,
        '"{}"是一款面向小企业主的网站搭建与管理平台。'
        '用户无需编写任何代码，通过填写表单的方式即可完成企业展示型网站的创建、编辑和发布。'
        '软件将用户填写的公司信息、产品数据、页面内容生成为纯静态 HTML/CSS/JS 文件，'
        '发布后不需要服务器端程序运行。'.format(SOFTWARE_FULL_NAME),
        first_line_indent=21)

    add_heading_styled(doc, '1.3 目标用户', level=2)
    users = [
        '制造业、贸易、服务业、餐饮业等小企业老板',
        '不会编程，但需要专业企业展示网站的用户',
        '网站内容更新频率较低（每 1-6 个月一次）的用户',
    ]
    for u in users:
        add_paragraph(doc, '• {}'.format(u), first_line_indent=21)

    # ---- 2. 系统架构 ----
    add_heading_styled(doc, '2. 系统架构', level=1)

    add_heading_styled(doc, '2.1 整体架构', level=2)
    add_paragraph(doc,
        '本软件采用经典的 Web 应用架构，后端使用 Flask 框架，前端使用 Vanilla JavaScript，'
        '数据分层存储：平台级元数据使用 SQLite 数据库，网站内容使用 YAML 文件存储。'
        '输出端通过 Jinja2 模板引擎将内容渲染为纯静态 HTML 文件。',
        first_line_indent=21)

    add_paragraph(doc, '核心架构层次：', font_name='黑体', font_size=11, bold=True)
    arch_layers = [
        '表现层：HTML + Jinja2 模板 + Vanilla JS + 自定义 CSS，提供管理后台界面',
        '业务逻辑层：Flask 路由（routes.py）处理 HTTP 请求，builder.py 负责静态生成',
        '数据层：SQLAlchemy ORM（models.py）+ YAML 文件存储（site_storage.py）',
        '输出层：静态 HTML 生成器（builder.py），无服务器端运行时依赖',
    ]
    for a in arch_layers:
        add_paragraph(doc, '  • {}'.format(a), first_line_indent=21, font_size=11)

    add_heading_styled(doc, '2.2 数据流', level=2)
    add_paragraph(doc,
        '用户登录（邮箱/手机号 + 密码）→ 进入管理后台 → 选择站点 → 编辑页面/数据集 → '
        '保存到 YAML 文件 → 触发构建（builder.py）→ Jinja2 渲染 → 输出纯静态 HTML/CSS/JS → '
        '可选导出 ZIP。',
        first_line_indent=21)

    add_heading_styled(doc, '2.3 目录结构', level=2)
    dirs = [
        'app/               Flask 应用（工厂函数、路由、静态资源）',
        'app/core/          核心业务逻辑（路由、构建器、模型、Block 引擎）',
        'app/templates/     后台管理页面 Jinja2 模板',
        'app/static/        后台静态资源（CSS、JS）',
        'site_templates/    网站前端模板（HTML + Jinja2 + CSS），git 版本管理',
        'sites/<name>/      单个网站的全部数据（YAML 文件 + 资源 + 构建产物）',
    ]
    for d in dirs:
        add_paragraph(doc, '  • {}'.format(d), font_name='Consolas', font_size=10)

    # ---- 3. 技术选型 ----
    add_heading_styled(doc, '3. 技术选型', level=1)

    tech_table = [
        ['后端框架', 'Flask (Python)', '轻量级，Jinja2 直接复用做静态生成'],
        ['模板引擎', 'Jinja2', '与 Flask 深度集成，支持静态生成'],
        ['数据库', 'SQLite + SQLAlchemy', 'MVP 阶段单机足够，数据量小，零运维'],
        ['前端', 'Vanilla JavaScript', '不引入 Vue/React，降低新人上手门槛'],
        ['样式', '自定义 CSS', '无第三方 UI 库依赖，完全自主可控'],
        ['数据存储', 'YAML 文件', '导出即复制文件夹，schema 弹性，程序可读'],
        ['认证', 'Werkzeug 哈希 + 验证码', '多因子身份管理，自适应密码哈希'],
        ['版本控制', 'Git', '模板和代码同步管理'],
    ]
    make_table(doc, ['技术项', '选型', '理由'], tech_table, col_widths=[2.5, 4, 9.5])

    # ---- 4. 核心模块设计 ----
    add_heading_styled(doc, '4. 核心模块设计', level=1)

    add_heading_styled(doc, '4.1 认证与账户模块', level=2)
    add_paragraph(doc,
        '认证系统支持邮箱/手机号双渠道注册与登录，采用"账号 + 密码"主登录方式，'
        '辅以 6 位一次性验证码通道（注册、找回密码、绑定新身份）。', first_line_indent=21)
    add_paragraph(doc, '核心数据模型（4 个）：', font_name='黑体', font_size=11, bold=True)
    models_desc = [
        'AccountIdentity：统一身份标识（email/phone），规范化存储，主从身份管理',
        'PasswordCredential：独立密码凭据表，Werkzeug 自适应哈希，保存变更时间',
        'VerificationCode：一次性验证码，哈希存储，10 分钟有效，5 次尝试限制，按账号限流',
        'UserSession：30 天多设备持久会话，支持主动下线、远程撤销和最近活动记录',
    ]
    for m in models_desc:
        add_paragraph(doc, '  • {}'.format(m), first_line_indent=21, font_size=11)

    add_paragraph(doc, '安全措施：', font_name='黑体', font_size=11, bold=True)
    sec_measures = [
        '密码使用 Werkzeug 提供的现代自适应哈希算法，不可逆存储',
        '验证码生成后旧码自动作废，每账号限流防止暴力破解',
        '所有写操作经 Flask-WTF CSRF 校验',
        '修改密码后自动撤销其他所有设备会话',
        '支持用户在账户中心查看并远程撤销任意设备',
    ]
    for s in sec_measures:
        add_paragraph(doc, '  • {}'.format(s), first_line_indent=21, font_size=11)

    add_heading_styled(doc, '4.2 站点管理模块', level=2)
    add_paragraph(doc,
        '站点以子域名 slug 为标识，数据存储于 sites/<slug>/ 目录下。'
        '站点删除采用软删除机制（soft_deleted_at 标记），数据库记录和磁盘文件完整保留，'
        '支持从回收站一键恢复。被软删除的站点不出现在编辑器站点选择器中。',
        first_line_indent=21)

    add_heading_styled(doc, '4.3 Block 模块化页面系统', level=2)
    add_paragraph(doc,
        '页面由声明式功能块（Block）组装而成。每个 Block 通过 data-* 属性声明字段映射，'
        '系统自动生成编辑表单。已转换 9/14 个 Block 为 data-* 声明式渲染，5 个保留 Jinja2 渲染。'
        'Block 类型包括：hero_banner（首页横幅）、feature_grid（特色网格）、'
        'product_list（产品列表）、article_list（文章列表）、contact_form（联系表单）、'
        'text_block（富文本块）、image_gallery（图片画廊）等。',
        first_line_indent=21)

    add_heading_styled(doc, '4.4 静态站点生成模块', level=2)
    add_paragraph(doc,
        'builder.py 为核心生成引擎：读取 YAML 源文件 → 加载模板 → Jinja2 渲染 → '
        '输出静态 HTML/CSS/JS。生成过程包括：字体子集化（fonttools/pyftsubset）、'
        '图片自动优化（Pillow 多尺寸 WebP 转换）、多语言分目录输出。',
        first_line_indent=21)

    add_heading_styled(doc, '4.5 数据集模块', level=2)
    add_paragraph(doc,
        '基于 YAML 的结构化数据管理（datasets.py），支持产品、文章等列表数据的 CRUD 操作。'
        '每条记录以 YAML 文件存储，天然支持嵌套结构和多语言。在小企业站规模下'
        '（几十到几百条记录），全文扫描 YAML 足够快。',
        first_line_indent=21)

    # ---- 5. 数据库设计 ----
    add_heading_styled(doc, '5. 数据库设计', level=1)

    add_paragraph(doc, '数据库仅存储平台级元数据，不存储网站内容。核心表结构如下：', first_line_indent=21)

    db_tables = [
        ['User', 'id, email, display_name, role, preferred_lang, email_verified_at, last_login_at, created_at',
         '用户主表，保留账户主体和资料'],
        ['AccountIdentity', 'id, user_id, identity_type(email/phone), identifier, verified_at, is_primary, created_at',
         '统一身份标识，邮箱和手机号走同一套唯一性规则'],
        ['PasswordCredential', 'id, user_id, password_hash, changed_at, created_at',
         '独立密码凭据表，Werkzeug 自适应哈希，不保存明文'],
        ['VerificationCode', 'id, user_id, code_hash, purpose, identity_type, identifier, expires_at, attempts, consumed_at',
         '验证码表，支持邮箱/短信注册、验证、找回密码和绑定身份'],
        ['UserSession', 'id, user_id, token_hash, device_info, ip_address, expires_at, revoked_at, last_activity_at',
         '持久会话表，支持多设备登录管理和远程撤销'],
        ['Site', 'id, owner_id, name, template, settings, soft_deleted_at, created_at, updated_at',
         '站点登记表，soft_deleted_at 实现软删除'],
        ['Template', 'id, name, display_name, version, path, created_at',
         '模板注册表，site_templates/ 扫描同步'],
    ]
    make_table(doc, ['表名', '关键字段', '说明'], db_tables, col_widths=[3, 6, 7])

    # ---- 6. 关键技术决策 ----
    add_heading_styled(doc, '6. 关键技术决策', level=1)

    decisions = [
        ['为什么用 Flask 而不是 Django',
         '轻量、Python 生态成熟、Jinja2 直接复用做静态生成。MVP 阶段不需要重武器。'],
        ['为什么静态生成而不是 SSR',
         '定位是"发布完不动"的网站。SSR 意味着永远在运行，违背产品理念。'],
        ['为什么 SQLite 起步',
         'MVP 阶段单机够用。每个用户数据量小（几十产品 + 几十张图）。'],
        ['为什么站点数据存 YAML 而非数据库',
         '导出即复制文件夹；schema 弹性（改字段不需 ALTER TABLE）；多语言天然嵌套；'
         '程序可读；平台关停后数据仍可读。'],
        ['为什么模板存文件而非数据库',
         '模板少（3-5 套）、变更频率低、需要 review 和版本控制。Git 是最佳工具。'],
        ['为什么不分前后端',
         '用户端只是表单，复杂度低。Flask + Vanilla JS 足够，避免 Vue/React 增加门槛。'],
        ['为什么不用密码登录的替代方案',
         '最初使用邮箱魔法链接（适合低频用户），后升级为邮箱/手机号 + 密码 + 验证码的'
         '完整认证体系，同时保留旧链接的迁移兼容期。'],
    ]
    make_table(doc, ['决策问题', '原因'], decisions, col_widths=[4, 12])

    out = os.path.join(OUTPUT_DIR, '02_软件设计说明书.docx')
    doc.save(out)
    print('[OK] {}'.format(out))


# ================================================================
# 文件 03：用户操作手册
# ================================================================
def add_screenshot_box(doc, screenshot_id, description, page_name):
    """在文档中插入截图占位框，带编号、页面名称和截图内容说明。"""
    # 上方留间距
    add_paragraph(doc, '', font_size=6)

    # 主框：用表格模拟带边框的占位框
    table = doc.add_table(rows=1, cols=1)
    table.style = 'Table Grid'
    # 设置行高（约 8cm 高的占位区域）
    cell = table.rows[0].cells[0]
    # 顶部标注
    p_title = cell.paragraphs[0]
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p_title.add_run('【 截图 {} — {} 】'.format(screenshot_id, page_name))
    run.bold = True
    run.font.size = Pt(11)
    run.font.name = '黑体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    run.font.color.rgb = RGBColor(0, 0, 0)

    # 留空行（模拟截图区域）
    for _ in range(3):
        pp = cell.add_paragraph()
        pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rr = pp.add_run('（ 在此处插入截图 —— {} ）'.format(description))
        rr.font.size = Pt(9)
        rr.font.name = '宋体'
        rr._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
        rr.font.color.rgb = RGBColor(180, 180, 180)
        rr.italic = True

    # 底部说明：截图内容要点
    p_bottom = cell.add_paragraph()
    p_bottom.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run_b = p_bottom.add_run('▼ 截图要点：{}'.format(description))
    run_b.font.size = Pt(8.5)
    run_b.font.name = '宋体'
    run_b._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    run_b.font.color.rgb = RGBColor(80, 80, 80)

    # 框后间距
    add_paragraph(doc, '', font_size=6)


def generate_03_user_manual():
    doc = Document()
    set_page_margin(doc)
    add_page_header_footer(doc, '{} {} 用户操作手册'.format(SOFTWARE_FULL_NAME, SOFTWARE_VERSION))

    # ---- 封面 ----
    for _ in range(6):
        add_paragraph(doc, '', font_size=12)
    add_paragraph(doc, '用户操作手册', font_name='黑体', font_size=26,
                  bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=20)
    add_paragraph(doc, SOFTWARE_FULL_NAME, font_name='黑体', font_size=18,
                  bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)
    add_paragraph(doc, SOFTWARE_VERSION, font_name='宋体', font_size=14,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=40)
    for line in ['著作权人：{}'.format(COMPANY_NAME), '完成日期：2026年07月16日']:
        add_paragraph(doc, line, font_size=12, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    doc.add_page_break()

    # ==================== 1. 软件概述 ====================
    add_heading_styled(doc, '1. 软件概述', level=1)
    add_heading_styled(doc, '1.1 产品简介', level=2)
    add_paragraph(doc,
        '"{}"是一款面向小企业主的网站搭建与管理工具。用户无需编写任何代码，'
        '通过填写表单的方式即可完成企业展示型网站的创建、编辑和发布。'
        '软件核心思路：将用户填写的公司信息、产品数据、页面内容生成为纯静态 HTML/CSS/JS 文件，'
        '发布后不需要服务器端程序运行，网站加载速度快、安全性高、维护成本近乎为零。'
        .format(SOFTWARE_FULL_NAME), first_line_indent=21)

    add_heading_styled(doc, '1.2 目标用户', level=2)
    for u in ['制造业、贸易、服务业、餐饮业等小企业老板',
              '不会编程，但需要专业企业展示网站的用户',
              '网站内容更新频率每 1-6 个月一次的用户',
              '之前可能使用过 WordPress 但对维护感到困扰的用户']:
        add_paragraph(doc, '• {}'.format(u), first_line_indent=21)

    add_heading_styled(doc, '1.3 核心功能一览', level=2)
    for feat in ['模板选择：多套精美网站模板，一键切换',
                 '页面编辑：可视化添加/删除/排序功能模块',
                 '数据集管理：产品列表、文章列表的结构化数据增删改查',
                 '媒体管理：图片上传、自动压缩优化',
                 '账户中心：个人资料、站点管理、账号安全、回收站',
                 '静态生成：一键生成纯静态 HTML 网站',
                 '导出下载：打包整站为 ZIP 文件',
                 '多语言翻译：自动翻译网站内容到多语言版本']:
        add_paragraph(doc, '• {}'.format(feat), first_line_indent=21)

    # ★ 截图 1：管理后台总览
    add_screenshot_box(doc, '1',
        '登录后进入的管理后台主界面全貌 —— 需体现左侧导航栏、中央仪表盘区域（站点列表/快速入口）、顶部栏',
        '管理后台主界面（仪表盘）')

    # ==================== 2. 运行环境 ====================
    add_heading_styled(doc, '2. 运行环境', level=1)
    add_heading_styled(doc, '2.1 服务器端', level=2)
    for env in ['操作系统：Ubuntu 20.04+ / CentOS 7+ / Windows Server 2016+',
                'Python：3.9 及以上',
                '内存：2 GB 以上',
                '硬盘：20 GB 以上可用空间',
                '数据库：SQLite 3（内置，无需额外安装）']:
        add_paragraph(doc, '• {}'.format(env), first_line_indent=21)

    add_heading_styled(doc, '2.2 客户端（管理后台）', level=2)
    for env in ['操作系统：Windows 10+ / macOS 11+ / Linux',
                '浏览器：Chrome 90+ / Firefox 90+ / Edge 90+',
                '屏幕分辨率：1280×720 以上',
                '网络：宽带网络连接']:
        add_paragraph(doc, '• {}'.format(env), first_line_indent=21)

    # ==================== 3. 安装与启动 ====================
    add_heading_styled(doc, '3. 安装与启动', level=1)
    add_heading_styled(doc, '3.1 获取代码', level=2)
    add_paragraph(doc, '从代码仓库克隆项目到本地：git clone <仓库地址> && cd mycompany.website11', first_line_indent=21)

    add_heading_styled(doc, '3.2 安装依赖', level=2)
    add_paragraph(doc, 'pip install -r requirements.txt', first_line_indent=21)

    add_heading_styled(doc, '3.3 配置环境变量', level=2)
    add_paragraph(doc, '复制模板：cp .env.example .env', first_line_indent=21)
    add_paragraph(doc, '必填配置：SECRET_KEY（会话加密密钥）、SMTP_*（邮件发送配置）、PLATFORM_DOMAIN（部署域名）', first_line_indent=21)

    add_heading_styled(doc, '3.4 创建管理员账号', level=2)
    add_paragraph(doc, 'flask --app run create-user admin@example.com', first_line_indent=21)
    add_paragraph(doc, 'flask --app run promote-admin admin@example.com', first_line_indent=21)

    add_heading_styled(doc, '3.5 启动服务', level=2)
    add_paragraph(doc, '开发：python run.py', first_line_indent=21)
    add_paragraph(doc, '生产：gunicorn run:app -w 4 -b 0.0.0.0:8000', first_line_indent=21)
    add_paragraph(doc, '启动后访问 http://localhost:5000 进入管理后台。', first_line_indent=21)

    # ==================== 4. 功能操作说明 ====================
    add_heading_styled(doc, '4. 功能操作说明', level=1)

    # ---- 4.1 用户注册与登录 ----
    add_heading_styled(doc, '4.1 用户注册与登录', level=2)
    add_paragraph(doc,
        '本软件支持邮箱或手机号注册，采用"账号 + 密码"主登录方式，同时支持验证码辅助认证。', first_line_indent=21)
    add_paragraph(doc, '【注册】', font_name='黑体', font_size=11, bold=True)
    add_paragraph(doc, '1. 在登录页面点击"注册"', first_line_indent=21)
    add_paragraph(doc, '2. 选择注册方式（邮箱或手机号）', first_line_indent=21)
    add_paragraph(doc, '3. 输入邮箱或手机号，系统发送 6 位验证码', first_line_indent=21)
    add_paragraph(doc, '4. 输入验证码并设置登录密码（至少 8 位，须含字母和数字）', first_line_indent=21)
    add_paragraph(doc, '5. 完成注册，自动登录', first_line_indent=21)

    # ★ 截图 2：登录页面
    add_screenshot_box(doc, '2',
        '登录页面完整截图 —— 需清晰展示"邮箱/手机号"输入框、"密码"输入框、"登录"按钮、"注册"和"忘记密码"链接',
        '登录页面')

    add_paragraph(doc, '【登录】', font_name='黑体', font_size=11, bold=True)
    add_paragraph(doc, '1. 输入已注册的邮箱或手机号', first_line_indent=21)
    add_paragraph(doc, '2. 输入登录密码，点击"登录"', first_line_indent=21)

    add_paragraph(doc, '【找回密码】', font_name='黑体', font_size=11, bold=True)
    add_paragraph(doc, '1. 点击"忘记密码"', first_line_indent=21)
    add_paragraph(doc, '2. 输入已注册的邮箱或手机号', first_line_indent=21)
    add_paragraph(doc, '3. 接收并输入 6 位验证码', first_line_indent=21)
    add_paragraph(doc, '4. 设置新密码', first_line_indent=21)

    add_paragraph(doc, '【安全特性】', font_name='黑体', font_size=11, bold=True)
    for s in ['密码使用自适应哈希算法存储，不可逆',
              '验证码 10 分钟有效，最多 5 次尝试',
              '支持 30 天"记住我"持久登录',
              '修改密码后自动撤销其他所有设备登录']:
        add_paragraph(doc, '• {}'.format(s), first_line_indent=21)

    # ---- 4.2 创建站点 ----
    add_heading_styled(doc, '4.2 创建站点', level=2)
    add_paragraph(doc, '1. 登录后进入仪表盘', first_line_indent=21)
    add_paragraph(doc, '2. 点击"创建新站点"', first_line_indent=21)
    add_paragraph(doc, '3. 输入站点名称（如 mycompany）', first_line_indent=21)
    add_paragraph(doc, '4. 选择网站模板', first_line_indent=21)
    add_paragraph(doc, '5. 点击"创建"', first_line_indent=21)
    add_paragraph(doc, '系统会基于模板自动生成初始网站内容（含示例页面和产品数据）。', first_line_indent=21)

    # ★ 截图 3：创建站点页面 / 模板选择
    add_screenshot_box(doc, '3',
        '创建站点页面或模板选择界面 —— 需展示站点名称输入框、模板列表/卡片（可看到模板缩略图）、"创建"按钮',
        '创建站点 / 模板选择')

    # ---- 4.3 编辑站点基本信息 ----
    add_heading_styled(doc, '4.3 编辑站点基本信息', level=2)
    add_paragraph(doc, '1. 进入站点管理后台，在"设置"页面配置以下内容：', first_line_indent=21)
    for s in ['网站名称与标语', 'Logo 与 Favicon', '主色调', '导航菜单', '页眉/页脚信息', '联系方式']:
        add_paragraph(doc, '  • {}'.format(s), first_line_indent=32)

    # ★ 截图 4：站点设置页面
    add_screenshot_box(doc, '4',
        '站点设置/基本信息编辑页面 —— 需展示网站名称、标语、Logo 上传区、主色调选择器、菜单管理入口等设置项',
        '站点设置页面')

    # ---- 4.4 页面编辑（Block 模块化系统）----
    add_heading_styled(doc, '4.4 页面编辑（Block 模块化系统）', level=2)
    add_paragraph(doc, '每个页面由多个功能模块（Block）组装而成：', first_line_indent=21)
    add_paragraph(doc, '1. 在页面列表中选择要编辑的页面', first_line_indent=21)
    add_paragraph(doc, '2. 点击"添加模块"', first_line_indent=21)
    add_paragraph(doc, '3. 选择模块类型（横幅、产品展示、公司介绍、联系方式等）', first_line_indent=21)
    add_paragraph(doc, '4. 在右侧属性面板中填写模块内容', first_line_indent=21)
    add_paragraph(doc, '5. 拖拽调整模块顺序', first_line_indent=21)
    add_paragraph(doc, '6. 点击"保存"', first_line_indent=21)
    add_paragraph(doc, '常用 Block 类型：hero_banner（首页大图横幅）、feature_grid（特色展示网格）、'
        'product_list（产品列表）、article_list（文章列表）、'
        'contact_form（联系表单）、text_block（富文本内容块）、image_gallery（图片画廊）', first_line_indent=21)

    # ★ 截图 5：页面编辑器（最重要的一张）
    add_screenshot_box(doc, '5',
        '页面编辑器完整界面 —— 需展示三栏布局：左侧模块列表 + 中央预览区（能看到页面实际效果）+ 右侧属性编辑面板（展开状态下可见表单字段）',
        '页面编辑器（Block 模块编辑界面）')

    # ---- 4.5 数据集管理 ----
    add_heading_styled(doc, '4.5 数据集管理', level=2)
    add_paragraph(doc, '数据集用于管理结构化列表数据（产品目录、文章列表等）。', first_line_indent=21)
    add_paragraph(doc, '添加：进入"数据集" → "产品" → "添加产品" → 填写信息 → 保存', first_line_indent=21)
    add_paragraph(doc, '编辑：点击要编辑的产品 → 修改信息 → 保存', first_line_indent=21)
    add_paragraph(doc, '删除：找到目标产品 → 点击删除 → 确认', first_line_indent=21)

    # ★ 截图 6：数据集列表
    add_screenshot_box(doc, '6',
        '数据集管理页面 —— 需展示产品/文章列表（含表格行：名称、图片缩略图、状态）、顶部搜索/筛选栏、右上角"添加"按钮',
        '数据集管理（产品/文章列表）')

    # ---- 4.6 媒体库 ----
    add_heading_styled(doc, '4.6 媒体库', level=2)
    add_paragraph(doc, '1. 进入"媒体库"', first_line_indent=21)
    add_paragraph(doc, '2. 点击"上传"选择图片', first_line_indent=21)
    add_paragraph(doc, '3. 系统自动压缩和优化（多尺寸生成）', first_line_indent=21)
    add_paragraph(doc, '4. 编辑内容时可从媒体库选择已上传的图片', first_line_indent=21)
    add_paragraph(doc, '支持格式：JPG、PNG、GIF、WebP', first_line_indent=21)

    # ---- 4.7 账户中心 ----
    add_heading_styled(doc, '4.7 账户中心', level=2)
    add_paragraph(doc, '点击编辑器左下角用户卡片进入独立账户工作区（不丢失当前编辑状态）。', first_line_indent=21)
    add_paragraph(doc, '【个人资料】修改昵称、查看登录邮箱、切换界面语言（简中/繁中/英文）、查看注册和登录时间。', first_line_indent=21, bold=False)
    add_paragraph(doc, '【我的站点】查看所有站点列表（名称、模板、语言、发布状态），可进入编辑、预览、导出一键操作。', first_line_indent=21, bold=False)
    add_paragraph(doc, '【账号与安全】绑定额外邮箱/手机号、设置主登录身份、解绑非主身份、修改密码、查看登录设备列表、远程撤销其他设备。', first_line_indent=21, bold=False)
    add_paragraph(doc, '【回收站】查看已删除站点、一键恢复。被删除站点的文件和数据在恢复前完整保留。', first_line_indent=21, bold=False)

    # ★ 截图 7：账户中心 — 个人资料
    add_screenshot_box(doc, '7',
        '账户中心"个人资料"选项卡 —— 需展示左侧账户导航栏 + 右侧个人资料表单（昵称输入框、语言下拉、邮箱只读显示、注册时间等）',
        '账户中心 — 个人资料')

    # ★ 截图 8：账户中心 — 账号与安全
    add_screenshot_box(doc, '8',
        '账户中心"账号与安全"选项卡 —— 需展示已绑定的邮箱/手机号列表、主身份标识、"绑定新身份"按钮、密码修改区域、登录设备列表',
        '账户中心 — 账号与安全')

    # ---- 4.8 生成与发布 ----
    add_heading_styled(doc, '4.8 生成与发布', level=2)
    add_paragraph(doc, '【生成静态站点】确认内容已保存 → 点击"生成站点" → 系统渲染为静态 HTML → 预览确认。', first_line_indent=21)
    add_paragraph(doc, '【导出下载】点击"导出站点" → 系统打包为 ZIP 文件 → 下载到本地。', first_line_indent=21)
    add_paragraph(doc, '【部署上线】解压 ZIP 后上传到任意 CDN 或 Web 服务器即可。', first_line_indent=21)

    # ★ 截图 9：生成的网站前台
    add_screenshot_box(doc, '9',
        '生成的静态网站前台首页 —— 浏览器中打开生成后的网站，需展示完整的首页效果（导航栏 + 横幅 + 内容区 + 页脚）',
        '生成的网站前台效果（首页）')

    # ---- 4.9 多语言翻译 ----
    add_heading_styled(doc, '4.9 多语言翻译', level=2)
    add_paragraph(doc, '进入"翻译"页面 → 选择目标语言 → 点击"自动翻译" → 系统使用翻译引擎翻译所有内容 → 手动校对修改。', first_line_indent=21)

    # ==================== 5. 常见问题 ====================
    add_heading_styled(doc, '5. 常见问题', level=1)
    faqs = [
        ('Q: 忘记密码怎么办？',
         'A: 在登录页面点击"忘记密码"，输入注册的邮箱或手机号，接收验证码后重设密码。'),
        ('Q: 可以同时绑定邮箱和手机号吗？',
         'A: 可以。在账户中心 → 账号与安全中绑定多个邮箱和手机号，并设置主登录身份。'),
        ('Q: 账号被盗怎么办？',
         'A: 在账户中心 → 账号与安全中查看所有登录设备并远程撤销可疑设备。建议立即修改密码。'),
        ('Q: 网站生成后还能修改吗？',
         'A: 可以。登录后台修改内容后重新生成即可。'),
        ('Q: 误删了站点能恢复吗？',
         'A: 能。采用软删除机制，删除的站点进入回收站，可随时恢复。'),
        ('Q: 平台关停了，我的网站还能访问吗？',
         'A: 能。网站是纯静态 HTML 文件，只要文件在 CDN 上就永远可以访问。'),
        ('Q: 网站加载速度快吗？',
         'A: 非常快。字体子集化（5-10MB→15KB）+ 图片自动压缩 + WebP 转换，首屏通常 < 1 秒。'),
    ]
    for q, a in faqs:
        add_paragraph(doc, q, font_name='黑体', font_size=11, bold=True)
        add_paragraph(doc, a, first_line_indent=21)

    # ==================== 尾页 ====================
    doc.add_page_break()
    add_paragraph(doc, '', font_size=12)
    add_paragraph(doc, '— 本手册适用于 {} {} —'.format(SOFTWARE_FULL_NAME, SOFTWARE_VERSION),
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=12)
    add_paragraph(doc, '著作权人：{}'.format(COMPANY_NAME),
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=12)
    add_paragraph(doc, '联系电话：{}'.format(COMPANY_TEL),
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, font_size=12)

    # ---- 截图索引表（方便对照截取）----
    doc.add_page_break()
    add_heading_styled(doc, '附：截图索引表（共 9 张）', level=1)
    add_paragraph(doc, '请按以下清单从运行中的系统截取界面图片，逐张插入文档中对应编号的占位框位置。', first_line_indent=21, space_after=12)

    screenshot_list = [
        ['1', '管理后台主界面（仪表盘）', '登录后的首页仪表盘全貌，含左侧导航栏、站点列表/快速入口卡片、顶部栏', '第 1 章末尾（1.3 节后）'],
        ['2', '登录页面', '邮箱/手机号输入框、密码输入框、登录按钮、注册和忘记密码链接', '4.1 节"注册"步骤之后'],
        ['3', '创建站点 / 模板选择', '站点名称输入框、模板卡片列表（可见缩略图）、创建按钮', '4.2 节末尾'],
        ['4', '站点设置页面', '网站名称、标语、Logo 上传区、主色调选择器、菜单管理入口', '4.3 节末尾'],
        ['5', '页面编辑器（Block 编辑）', '三栏布局：左侧模块列表 + 中央预览区 + 右侧属性编辑面板（展开状态）', '4.4 节末尾'],
        ['6', '数据集管理（产品/文章列表）', '表格列表（名称/图片/状态列）、搜索/筛选栏、添加按钮', '4.5 节末尾'],
        ['7', '账户中心 — 个人资料', '左侧账户导航栏 + 右侧表单（昵称、语言下拉、邮箱只读、注册时间）', '4.7 节"个人资料"段落后'],
        ['8', '账户中心 — 账号与安全', '已绑定身份列表、主身份标识、密码修改区、登录设备列表', '4.7 节"账号与安全"段落后'],
        ['9', '生成的网站前台效果（首页）', '浏览器打开生成后的静态网站，展示完整首页（导航+横幅+内容+页脚）', '4.8 节末尾'],
    ]
    make_table(doc, ['编号', '截图页面', '截图内容要点', '插入位置'],
               screenshot_list, col_widths=[1, 4, 7, 4])

    out = os.path.join(OUTPUT_DIR, '03_用户操作手册.docx')
    doc.save(out)
    print('[OK] {}'.format(out))


# ================================================================
# 文件 04：源程序鉴别材料（前 30 页 + 后 30 页）
# ================================================================
def generate_04_source_code():
    doc = Document()

    # 页面设置：A4，小边距
    for section in doc.sections:
        section.top_margin = Cm(1.5)
        section.bottom_margin = Cm(1.5)
        section.left_margin = Cm(2.0)
        section.right_margin = Cm(2.0)
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)

    LINES_PER_PAGE = 48  # Word 单页容纳行数
    TOTAL_PAGES = 60
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 前 30 页文件列表
    FRONT_FILES = [
        "app/core/routes.py",
        "app/core/models.py",
        "app/core/builder.py",
        "app/core/block_renderer.py",
        "app/core/menu.py",
        "app/core/site_storage.py",
    ]

    # 后 30 页文件列表
    BACK_FILES = [
        "app/core/translator.py",
        "app/core/block_parser.py",
        "app/core/media_service.py",
        "app/core/template_loader.py",
        "app/core/icon_registry.py",
        "app/core/style_registry.py",
        "app/core/config.py",
        "app/core/datasets.py",
        "app/core/admin_routes.py",
        "app/core/db.py",
        "app/static/js/admin_modules.js",
    ]

    def read_all_lines(file_list):
        lines = []
        for fname in file_list:
            fpath = os.path.join(PROJECT_ROOT, fname) if not os.path.isabs(fname) else fname
            if not os.path.isfile(fpath):
                continue
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            lines.append("// ====== {} ======\n".format(fname))
            lines.append("\n")
            lines.extend(content.split('\n'))
            lines.append("\n")
        return lines

    def write_pages(doc, lines, start_page, max_pages, phase_label):
        page_num = start_page
        line_idx = 0
        pages_written = 0

        while pages_written < max_pages and line_idx < len(lines):
            # 每页开头加页眉信息
            header_text = '{}  {}           第 {} 页 / 共 {} 页'.format(
                SOFTWARE_FULL_NAME, SOFTWARE_VERSION, page_num, TOTAL_PAGES)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(header_text)
            run.font.size = Pt(8)
            run.font.name = '宋体'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
            run.bold = True

            # 分隔线
            p2 = doc.add_paragraph()
            run2 = p2.add_run('─' * 80)
            run2.font.size = Pt(6)

            # 代码内容
            chunk = lines[line_idx:line_idx + LINES_PER_PAGE]
            for c in chunk:
                pp = doc.add_paragraph()
                # 截断过长行
                display = c[:150] if len(c) > 150 else c
                run = pp.add_run(display)
                run.font.name = 'Consolas'
                run.font.size = Pt(7.5)
                # 行间距紧凑
                pf = pp.paragraph_format
                pf.space_before = Pt(0)
                pf.space_after = Pt(0)
                pf.line_spacing = Pt(10)

            line_idx += len(chunk)
            page_num += 1
            pages_written += 1

            if pages_written < max_pages or phase_label == '前':
                doc.add_page_break()

    # 读取所有行
    print('  读取源文件...')
    front_lines = read_all_lines(FRONT_FILES)
    back_lines = read_all_lines(BACK_FILES)

    # 写入前 30 页
    print('  写入前 30 页（核心模块）...')
    write_pages(doc, front_lines, 1, 30, '前')

    # 写入后 30 页
    print('  写入后 30 页（辅助模块）...')
    write_pages(doc, back_lines, 31, 30, '后')

    # 最后一页不需要分页符，删除多余的分页符
    # (doc.add_page_break() 在 write_pages 的最后一次迭代也会加，这是可接受的)

    out = os.path.join(OUTPUT_DIR, '04_源程序鉴别材料_前后各30页.docx')
    doc.save(out)
    print('[OK] {}'.format(out))


# ================================================================
# 文件 05：提交材料清单及办理说明
# ================================================================
def generate_05_checklist():
    doc = Document()
    set_page_margin(doc)

    # 标题
    add_paragraph(doc, '计算机软件著作权登记', font_name='黑体', font_size=22,
                  bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    add_paragraph(doc, '提交材料清单及办理说明', font_name='黑体', font_size=18,
                  bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=16)

    # ---- 一、提交材料清单 ----
    add_heading_styled(doc, '一、提交材料清单', level=1)

    checklist_items = [
        ['1', '软件著作权登记申请表', '在线填写（www.ccopyright.com.cn），提交后打印盖章', '✓ 待填写'],
        ['2', '软件设计说明书', '本文档 02，含架构设计、模块设计、数据库设计、技术决策', '✓ 已准备'],
        ['3', '用户操作手册', '本文档 03，含概述、安装、功能操作、FAQ', '✓ 已准备'],
        ['4', '源程序鉴别材料', '本文档 04，前 30 页 + 后 30 页，共 60 页，每页约 48 行代码', '✓ 已准备'],
        ['5', '申请信息采集及确认表', '本文档 01，含软件信息、著作权人信息、技术特点', '✓ 已准备'],
        ['6', '营业执照复印件', '统一社会信用代码证书（加盖公章）', '□ 待盖章'],
        ['7', '授权委托书', '如委托代理机构办理需提供（加盖公章）', '□ 视情况'],
    ]
    make_table(doc, ['序号', '材料名称', '说明', '状态'], checklist_items, col_widths=[1, 4.5, 8, 2.5])

    add_paragraph(doc,
        '说明：材料 1 在中国版权保护中心网站在线填写后打印；'
        '材料 2-5 见本套文档对应文件；'
        '材料 6 为营业执照复印件加盖公司公章；'
        '材料 7 仅在委托代理机构办理时需提供。',
        font_size=10.5, color=(128, 128, 128))

    # ---- 二、申请人信息 ----  (放在前面方便确认)
    add_heading_styled(doc, '二、申请人信息（确认）', level=1)

    app_table = [
        ['著作权人', COMPANY_NAME],
        ['统一社会信用代码', COMPANY_CREDIT_CODE],
        ['注册地址', COMPANY_ADDRESS],
        ['法定代表人', COMPANY_LEGAL_REP],
        ['联系电话', COMPANY_TEL],
    ]
    make_table(doc, ['项目', '内容'], app_table, col_widths=[3.5, 12.5])

    # ---- 三、软件信息 ----
    add_heading_styled(doc, '三、软件信息（确认）', level=1)

    sw_table = [
        ['软件全称', SOFTWARE_FULL_NAME],
        ['软件简称', SOFTWARE_SHORT_NAME],
        ['版本号', SOFTWARE_VERSION],
        ['分类号', '30200-0000（互联网应用软件）'],
        ['软件类型', '应用软件'],
        ['开发完成日期', '2026年07月16日'],
        ['发表状态', '未发表'],
        ['编程语言', 'Python 21,598 行 / HTML 31,505 行 / CSS 24,357 行 / JS 4,358 行'],
        ['总代码行数', '约 128,000 行（含 YAML 配置 20,666 行和 Markdown 文档 25,836 行）'],
        ['开发周期', '2026年05月—2026年07月，共 291 次 Git 提交'],
    ]
    make_table(doc, ['项目', '内容'], sw_table, col_widths=[3.5, 12.5])

    # ---- 四、办理流程 ----
    add_heading_styled(doc, '四、办理流程', level=1)

    add_paragraph(doc, '步骤一：注册账号', font_name='黑体', font_size=11, bold=True)
    add_paragraph(doc,
        '访问中国版权保护中心（https://www.ccopyright.com.cn），点击"注册"，'
        '选择"机构用户"，使用统一社会信用代码完成实名认证。', first_line_indent=21)

    add_paragraph(doc, '步骤二：在线填写申请表', font_name='黑体', font_size=11, bold=True)
    add_paragraph(doc,
        '登录后进入"软件著作权登记"→"新建申请"，按"申请信息采集及确认表"（本文档 01）内容逐项填写。'
        '注意：软件全称、简称、版本号、分类号、开发完成日期需与本文档一致。',
        first_line_indent=21)

    add_paragraph(doc, '步骤三：上传电子材料', font_name='黑体', font_size=11, bold=True)
    add_paragraph(doc,
        '在线提交以下 PDF 文件：\n'
        '  (1) 软件设计说明书（本文档 02 转 PDF）\n'
        '  (2) 用户操作手册（本文档 03 转 PDF，建议配 6-10 张界面截图）\n'
        '  (3) 源程序鉴别材料（本文档 04 转 PDF，前 30 页 + 后 30 页）\n'
        '  (4) 营业执照复印件（加盖公章后扫描成 PDF）',
        first_line_indent=21)

    add_paragraph(doc, '步骤四：缴费', font_name='黑体', font_size=11, bold=True)
    add_paragraph(doc,
        '企业申请官方费用为 ¥1,000。在线支付后保留缴费凭证。',
        first_line_indent=21)

    add_paragraph(doc, '步骤五：邮寄纸质材料（如需）', font_name='黑体', font_size=11, bold=True)
    add_paragraph(doc,
        '部分地区可能要求邮寄纸质申请材料，包括：盖章的申请表、营业执照复印件、'
        '软件设计说明书、用户操作手册、源程序鉴别材料。'
        '请以受理通知书中的具体要求为准。',
        first_line_indent=21)

    add_paragraph(doc, '步骤六：等待审查', font_name='黑体', font_size=11, bold=True)
    add_paragraph(doc,
        '受理：提交后 3 个工作日内；审查：受理后 30-60 个工作日；'
        '如需补正，按审查意见修改后重新提交；审查通过后发放电子证书，纸质证书约 2 周邮寄。',
        first_line_indent=21)

    # ---- 五、费用说明 ----
    add_heading_styled(doc, '五、费用说明', level=1)
    fee_table = [
        ['软件著作权登记费（企业）', '¥1,000', '官方费用'],
        ['软件著作权登记费（个人）', '¥300', '官方费用（仅供参考）'],
    ]
    make_table(doc, ['费用项目', '金额', '备注'], fee_table, col_widths=[8, 2.5, 5.5])

    # ---- 六、注意事项 ----
    add_heading_styled(doc, '六、注意事项', level=1)

    notes = [
        '1. 所有文档中的软件名称、版本号、开发完成日期必须完全一致，否则会导致补正。',
        '2. 源程序鉴别材料（04）页码必须连续（1-60），每页均需包含软件名称和页码。',
        '3. 如果软件尚未公开发布，发表状态填"未发表"，不影响登记。',
        '4. 营业执照复印件必须加盖公司公章（鲜章），扫描件需清晰可辨。',
        '5. 在线申请表填写后请仔细核对，提交后不可在线修改，如需修改需联系客服。',
        '6. 软著证书有效期为 50 年（法人自首次发表起算）。',
        '7. 如有疑问，可拨打中国版权保护中心咨询电话：010-68003887。',
    ]
    for n in notes:
        add_paragraph(doc, n, first_line_indent=21, font_size=11)

    # ---- 七、联系方式 ----
    add_heading_styled(doc, '七、联系方式', level=1)
    contact_table = [
        ['申请单位', COMPANY_NAME],
        ['联系人', '（待填写）'],
        ['联系电话', COMPANY_TEL],
        ['电子邮箱', '（待填写）'],
        ['联系地址', COMPANY_ADDRESS],
    ]
    make_table(doc, ['项目', '内容'], contact_table, col_widths=[3.5, 12.5])

    out = os.path.join(OUTPUT_DIR, '05_提交材料清单及办理说明.docx')
    doc.save(out)
    print('[OK] {}'.format(out))


# ================================================================
# Main
# ================================================================
if __name__ == '__main__':
    print('=' * 60)
    print('软著申请 Word 文档批量生成器')
    print('著作权人：{}'.format(COMPANY_NAME))
    print('=' * 60)
    print()

    generate_01_application_form()
    generate_02_design_spec()
    generate_03_user_manual()
    generate_04_source_code()
    generate_05_checklist()

    print()
    print('全部完成！输出目录：{}'.format(OUTPUT_DIR))
    print()
    print('注意事项：')
    print('  1. 01 文件末尾需加盖公章')
    print('  2. 03 用户手册建议补充 6-10 张后台界面截图')
    print('  3. 04 源代码文档在 Word 中微调页边距和字号确保每页 50 行')
    print('  4. 所有 docx 需另存/导出为 PDF 后再上传版权中心系统')
