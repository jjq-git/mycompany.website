---
description: "管理模板的种子数据(添加/修改/查看 site_templates/<name>/seed_data/)"
---

当用户说"种子数据"、"加示例数据"、"修改默认产品"、"模板的初始内容"时触发.
种子数据是新站点创建时从模板复制到 `sites/<id>/` 的初始内容.
对模板开发至关重要——它决定了店主创建站点后看到的默认内容.

数据流:`site_templates/<name>/seed_data/` → `copy_seed_data()` → `sites/<id>/`

## 了解种子数据目录结构

```
site_templates/<name>/seed_data/
├── settings.yaml      # 站点设置(公司信息、联系方式、菜单、主题)
├── pages/             # 页面定义
│   ├── home.yaml      # 首页内容
│   ├── about.yaml     # 关于页面
│   └── contact.yaml   # 联系页面
└── data/              # 数据集
    ├── products.yaml  # 产品数据
    ├── features.yaml  # 功能特性
    ├── posts.yaml     # 博客文章
    └── ...            # 其他自定义数据集
```

关键约定:
- 目录结构必须与 `sites/<id>/` 完全一致
- 新站点创建时 `copy_seed_data()` 直接复制整个 seed_data/ 目录
- 多语言站点:seed_data 是默认语言的数据,其他语言通过后台 AI 翻译生成

## 查看现有种子数据

列出模板的所有种子数据文件:
```
ls site_templates/<name>/seed_data/
ls site_templates/<name>/seed_data/pages/
ls site_templates/<name>/seed_data/data/
```

查看具体内容(YAML 格式):
```
cat site_templates/<name>/seed_data/settings.yaml
cat site_templates/<name>/seed_data/pages/home.yaml
cat site_templates/<name>/seed_data/data/products.yaml
```

参考现有实现:
- `site_templates/dengtec/seed_data/` — 完整示例
- `site_templates/tech-product/seed_data/` — 另一套示例

## 修改 settings.yaml

`settings.yaml` 是站点全局设置,格式:
```yaml
company:
  name: 公司全称
  short_name: 公司简称
  icp: ''  # ICP 备案号

contact:
  phone: ''
  email: ''
  address: ''
  wechat: ''

menu:
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

theme:
  accent: '#067a7a'
  bg: '#ffffff'
  text: '#1e293b'

header:
  variant: logo_left_menu_right
  language_switcher:
    enabled: true
    style: vertical_dropdown

footer:
  variant: four_columns

social:
  enabled: true
  github: ''
  twitter: ''
  facebook: ''
  linkedin: ''
  youtube: ''
```

注意事项:
- `menu` 必须包含 type=home 的首页项(构建时 `ensure_home()` 也会自动补上)
- 每个 type=list 的菜单项需要对应 data/ 下的同名数据集文件
- `theme` 中的颜色用 CSS 变量引用(在 main.css 中 `var(--color-accent)`)
- `header.variant` 和 `footer.variant` 的值来自模板 `meta.yaml` 中定义的变体列表

## 修改 pages/*.yaml(页面数据)

页面有两种格式:

**旧格式(固定 key)** — `dengtec` 模板使用:
```yaml
hero:
  title: 标题文字
  subtitle: 副标题
  badge: 徽章
  cta_text: 了解更多
  cta_url: '/products/'
  background_image: ''
featured_section:
  enabled: true
  title: 产品展示
  subtitle: 看我们的产品
  limit: 6
```

**新格式(modules 数组)** — `tech-product` 模板使用:
```yaml
modules:
  - type: hero_banner
    variant: default
    order: 1
    data:
      slides:
        - title: 标题
          subtitle: 副标题
          primaryBtn: 按钮文字
          primaryBtnLink: '/products/'
  - type: feature_grid
    variant: default
    order: 2
    data:
      title: 我们的优势
      features:
        - icon: star
          title: 功能1
          desc: 描述1
```

要确定用哪种格式,查看模板 `meta.yaml` 中是否定义了 datasets 和 blocks.

## 修改 data/*.yaml(数据集)

数据集支持两种格式(`datasets.load()` 兼容两种):

**格式一:直接列表**
```yaml
- id: 1
  name: 产品A
  slug: product-a
  summary: 简介
  description: 详细描述
  cover: ''
  category: 分类A
  specs:
    尺寸: 100x100
    重量: 1kg
- id: 2
  name: 产品B
  slug: product-b
  summary: 简介
  description: 详细描述
  cover: ''
  category: 分类B
```

**格式二:含 items 键**
```yaml
categories:
  - 分类A
  - 分类B
items:
  - id: 1
    name: 产品A
    slug: product-a
    ...
```

关键规则:
- 每条必须有 `id` 字段(整数)或由 `datasets.load()` 自动分配
- `slug` 用于生成详情页 URL:`/<lang>/<dataset>/<slug>/`
- `cover` 是图片路径(种子数据中可为空字符串,店主会上传)
- 数据集文件名必须与 `meta.yaml` 中 `datasets` 列表和菜单 `target` 一致
- 如模板定义了 `meta.yaml` 中 `datasets: [products, features, posts]`,就至少要有这三个 YAML 文件

## 在 meta.yaml 中声明种子数据结构

模板的 `meta.yaml` 需要正确声明种子数据相关的配置:

```yaml
display_name: 模板显示名
industry: tech
version: '1.0.0'

# 数据集定义:告诉系统这个模板有哪些数据集
datasets:
  - name: products
    label: 产品
  - name: features
    label: 功能特性
  - name: posts
    label: 博客

# 默认菜单:新站点创建后看到的导航
default_menu:
  - label: 首页
    type: home
  - label: 产品
    type: list
    target: products
  - label: 关于
    type: page
    target: about

# 语言支持(多语言模板才需要)
languages:
  - code: zh-CN
    name: 简体中文
    flag: 🇨🇳
  - code: en
    name: English
    flag: 🇬🇧
default_language: zh-CN
```

注意:
- `datasets` 列表中的 name 决定了数据文件名(`data/<name>.yaml`)
- `default_menu` 决定了新站点的初始导航结构
- 如果没有 `default_menu`,构建时会为空,用户需要手动设置

## 验证种子数据

创建测试站点来验证种子数据是否正确:
1. `flask --app run create-user test@example.com`
2. `flask --app run create-site test@example.com test-site --template <name>`
3. `flask --app run build-site <new_site_id>`
4. 检查 `output/<site_id>/` 下的 HTML 文件
5. 启动服务器 `python run.py`,用预览功能在浏览器验证

常见问题:
- YAML 缩进/语法错误 → 构建时解析失败
- slug 重复 → 详情页生成时后者覆盖前者
- 数据集文件名与 menu target 不匹配 → 列表页无数据
- 缺少必需字段 → 模板渲染时显示空白
