---
name: template-new-template
description: "脚手架:在 site_templates/ 下创建新的网站模板"
---

当用户说"新建模板"、"创建新模板"、"加一套模板"时触发.
在 site_templates/ 下生成一个完整的模板骨架,包括 meta.yaml、Jinja2 模板、CSS 和种子数据目录.

模板是网站的"皮肤".CLAUDE.md 核心信念 #3:模板要少而精(3 套精美 > 30 套粗糙).

## 设计决策

开始前确认:
1. **行业适配**:这个模板为哪个行业设计?(tech/manufacturing/restaurant/service/retail)
2. **设计风格**:简洁商务 / 大胆创意 / 温暖亲近
3. **是否需要多语言**:MVP 阶段默认不做,Phase 2 再加
4. **参考哪个现有模板**:`dengtec` 作为起点

模板设计的核心原则(来自 CLAUDE.md):
- 模板代码由开发者 + AI 编写,git 管理,不是可视化编辑器拖出来的
- 每个模板独立完整,目录结构一致
- 不做 30 套模板,把 3-5 套做精

## 创建目录结构

完整的模板目录结构:

```
site_templates/<name>/
├── meta.yaml                  # 模板元数据(必需)
├── blocks/                    # Block 组件目录
│   ├── hero_banner/          # 首页横幅
│   │   ├── meta.yaml         # Block 字段定义
│   │   └── template.html     # Jinja2 渲染模板
│   ├── feature_grid/         # 功能特性网格
│   │   ├── meta.yaml
│   │   └── template.html
│   └── ...                   # 其他 Block
├── templates/                # Jinja2 页面模板
│   ├── _base.html           # 最外层骨架(HTML 头、CSS/JS 加载、导航/页脚宏)
│   ├── _page.html           # 通用页面布局(Header + 内容 + Footer)
│   ├── _modules.html        # Block 渲染宏(在页面中渲染 modules 数组)
│   ├── index.html           # 首页(通常 extends _base.html)
│   ├── about.html           # 关于页
│   ├── products.html        # 产品列表页(数据集列表)
│   ├── product_detail.html  # 产品详情页
│   ├── _generic_detail.html # 通用详情页(兜底)
│   └── blog.html            # 博客列表页(如需要)
├── static/
│   └── css/
│       └── main.css         # 全局样式(CSS Design Tokens + 组件样式)
└── seed_data/               # 初始内容
    ├── settings.yaml        # 站点设置(公司信息、菜单、主题)
    ├── pages/               # 页面初始数据
    │   ├── home.yaml
    │   ├── about.yaml
    │   └── contact.yaml
    └── data/                # 数据集初始数据
        ├── products.yaml
        ├── features.yaml
        └── posts.yaml
```

## 创建 meta.yaml

模板元数据的完整格式(参考 `site_templates/dengtec/meta.yaml`):

```yaml
display_name: 模板显示名称(中文)
industry: tech
description: 适合科技公司的现代简洁风格
cover_image: ''
version: '1.0.0'
is_public: true

datasets:
  - name: products
    label: 产品
  - name: features
    label: 功能特性
  - name: posts
    label: 博客

default_menu:
  - label: 首页
    type: home
  - label: 产品
    type: list
    target: products
  - label: 关于
    type: page
    target: about
  - label: 联系我们
    type: page
    target: contact

default_theme:
  accent: '#067a7a'
  bg: '#ffffff'
  surface: '#f8fafc'
  text: '#1e293b'
  text_muted: '#64748b'
  border: '#e8ecf0'

# 以下为可选字段:
# languages:              # 多语言支持(Phase 2)
#   - code: zh-CN
#     name: 简体中文
#     flag: 🇨🇳
# default_language: zh-CN
# header_variants:        # Header 变体列表
#   - key: logo_left_menu_right
#     label: Logo 左 + 菜单右
# footer_variants:        # Footer 变体列表
#   - key: four_columns
#     label: 四栏链接
```

## 创建 _base.html

`_base.html` 是模板的最外层骨架,所有页面通过
`{% extends '_base.html' %}` 继承它.

关键要素(参考 `site_templates/dengtec/templates/_base.html`):
- `<!DOCTYPE html>` + `<html lang="...">`
- `<head>`:charset、viewport、title、CSS 加载、主题变量注入
- 主题 CSS 变量通过 `<style>` 注入:
  ```html
  <style>
    :root {
      --color-accent: {{ theme.accent }};
      --color-bg: {{ theme.bg }};
      --color-text: {{ theme.text }};
      --font-family-base: '...';
    }
  </style>
  ```
- `<body>`:Header → `{% block content %}{% endblock %}` → Footer
- Header 和 Footer 通常定义为 Jinja2 宏(macro),在不同变体间切换
- CSS 加载:`<link rel="stylesheet" href="{{ base_url }}/static/css/main.css">`

## 创建 _modules.html

`_modules.html` 是 Block 渲染的核心——遍历页面 modules 数组并渲染每个 Block.

核心宏:
```jinja2
{% macro render_modules(modules) %}
  {% for module in modules %}
    {% set block_type = module.type %}
    {% set block_data = module.data %}
    {% set block_variant = module.variant | default('default') %}
    {% include 'blocks/' + block_type + '/template.html' %}
  {% endfor %}
{% endmacro %}
```

页面中通过 `{% from '_modules.html' import render_modules %}` 引入后使用
`{{ render_modules(page.get('modules', [])) }}`.

## 创建 main.css

CSS 设计约定(参考 `site_templates/dengtec/static/css/main.css`):

文件分区结构:
1. **CSS Design Tokens**(`:root` 变量)
2. **排版与工具类**(标题、正文、工具 class)
3. **布局**(Header、Footer、网格系统)
4. **通用组件**(按钮、卡片、表单、标签)
5. **Block 样式区**(各 Block 的 CSS)

关键约定:
- 颜色用 `var(--color-*)` 引用,不硬编码色值
- 字体用 `var(--font-family-base)`
- 必须做响应式适配(`@media` 断点)
- 类名用 `BEM` 风格:`.block-name__element--modifier`

## 创建种子数据

种子数据让新站点创建后不是空白的.详见 `seed-data` 技能.

最少必需的种子数据文件:
- `seed_data/settings.yaml`:公司信息(名称、联系方式为空)、默认菜单
- `seed_data/pages/home.yaml`:首页的 modules 数组
- `seed_data/data/products.yaml`:2-3 个示例产品
- `seed_data/data/features.yaml`:3-4 个示例功能特性

## 完成后的步骤

1. 同步到数据库:`flask --app run scan-templates`
2. 创建测试站点:`flask --app run create-site test@test.com test-<name> --template <name>`
3. 构建预览:`flask --app run build-site <new_site_id>`
4. 启动服务器预览:`$env:FLASK_HOST='0.0.0.0'; $env:FLASK_DEBUG='1'; python run.py` → 访问后台
5. 迭代完善:对比参考模板,补充缺失的 Block 和页面

## 参考现有模板

| 模板 | 目录名 | 行业 | 特点 |
|------|--------|------|------|
| 瞪特科技 | dengtec | tech/制造业 | 模块化设计,支持多语言,完整 Block 集 |

推荐以 `dengtec` 为参考模板,它是最完整的实现.

## 关联技能

- `seed-data`:详细的种子数据管理指南
- `new-block`:添加 Block 到模板
- `scan-templates`:同步模板到数据库
- `edit-template-style`:修改模板样式
- `create-site`:创建测试站点
- `build-site`:构建验证
