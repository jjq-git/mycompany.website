# 站点创建与模块使用手册

> 面向运营人员和开发者。涵盖从创建站点到使用全部 12 个模块库模块的完整流程。

---

## 目录

1. [概述](#1-概述)
2. [前置条件](#2-前置条件)
3. [创建站点](#3-创建站点)
4. [站点文件结构](#4-站点文件结构)
5. [后台管理界面](#5-后台管理界面)
6. [全局设置](#6-全局设置)
7. [菜单系统](#7-菜单系统)
8. [页面与模块](#8-页面与模块)
9. [模块库详解](#9-模块库详解)
10. [数据集管理](#10-数据集管理)
11. [构建与发布](#11-构建与发布)
12. [常用场景示例](#12-常用场景示例)

---

## 1. 概述

本平台为小企业老板提供"填表即建站"的能力。店主选择一套模板，填写公司信息、产品数据、页面内容，系统自动生成纯静态 HTML 网站。

**核心流程**：创建用户 → 创建站点（选模板）→ 改设置/填数据 → 构建 → 发布

**当前可用模板**：`dengtec`（科技公司-企业官网版），支持三语言（简体中文 / 繁體中文 / English）。

---

## 2. 前置条件

创建站点前必须满足：

1. **至少一个用户存在** — 站点必须归属于某个用户
2. **至少一个模板已同步** — 模板是站点的外观基础

### 2.1 创建用户

```bash
# CLI 方式（开发期跳过邮件验证）
flask --app run create-user <email>

# 示例
flask --app run create-user boss@example.com
```

```bash
# 查看所有用户
flask --app run list-users
```

### 2.2 同步模板

```bash
# 扫描 site_templates/ 目录，将模板信息写入数据库
flask --app run scan-templates
```

输出示例：
```
同步了 1 个模板:
  - dengtec (科技公司-企业官网版) [manufacturing]
```

---

## 3. 创建站点

### 3.1 CLI 方式

```bash
flask --app run create-site <owner_email> <slug> --template <模板名> --name "站点名称"
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `owner_email` | 是 | 站点归属用户的邮箱 |
| `slug` | 是 | URL 标识，3-30 字符，仅限小写字母/数字/连字符，不能以连字符开头或结尾 |
| `--template` | 否 | 模板名，不指定则使用第一个可用模板 |
| `--name` | 否 | 站点名称，默认"我的网站" |

**slug 规则**：
- 正则：`^[a-z0-9][a-z0-9-]{1,28}[a-z0-9]$`
- 保留字不可用：`www`, `mail`, `admin`, `api`, `blog`, `app`, `cdn`, `dev`, `docs`, `help`, `img`, `m`, `my`, `ns`, `shop`, `static`, `store`, `test`, `web`, `site`

**示例**：
```bash
flask --app run create-site boss@example.com my-company --template dengtec --name "昆山德恩基电子科技"
```

**CLI 执行过程**：
1. 校验 slug 格式和唯一性
2. 查找用户和模板
3. 创建 `Site` 数据库记录（获取 `site.id`）
4. 初始化文件夹 `sites/<id>/`（含 `pages/`, `data/`, `translations/`, `assets/` 子目录）
5. 从模板复制种子数据（`site_templates/<name>/seed_data/` → `sites/<id>/`）

### 3.2 Web 界面方式

1. 用户登录后访问 `/templates` 模板画廊
2. 选择模板，点击"使用此模板"
3. 填写站点名称和 slug
4. 提交后自动跳转至站点管理后台

Web 方式使用当前登录用户作为站点所有者，slug 自动转小写。

### 3.3 创建后验证

```bash
# 查看所有站点
flask --app run list-sites

# 构建站点预览
flask --app run build-site <site_id>
```

---

## 4. 站点文件结构

每个站点存储在 `sites/<site_id>/` 下，是纯 YAML 文件 + 上传资源：

```
sites/<site_id>/
├── settings.yaml          # 全局设置（公司信息、联系方式、菜单、页脚、主题色、社交链接）
├── pages/                 # 页面定义（每页一个 YAML）
│   ├── home.yaml          # 首页（modules 数组）
│   ├── about.yaml         # 关于页
│   └── contact.yaml       # 联系页
├── data/                  # 数据集（结构化内容）
│   ├── products.yaml      # 产品
│   ├── portfolio.yaml     # 项目案例
│   ├── posts.yaml         # 博客文章
│   └── features.yaml      # 功能特性（备用）
├── translations/          # 多语言翻译缓存（Phase 2）
├── lang/<code>/           # 各语言版本覆盖
│   ├── pages/*.yaml
│   ├── data/*.yaml
│   └── settings.yaml
└── assets/                # 上传的图片/文件
    └── uploads/           # 自动转为 WebP 的图片
```

### 4.1 settings.yaml 结构

```yaml
company:
  name: 公司全称
  short_name: 简称
  logo: ""
  icp: 备案号

contact:
  phone: "0512-50133094"
  mobile: "18020204529"
  email: info@example.com
  address: 公司地址
  business_hours: 周一至周五 9:00 - 18:00
  weekend: 周末请提前预约

social:
  github: ""
  twitter: ""
  facebook: ""
  linkedin: ""
  youtube: ""

theme: {}        # 留空则使用模板默认主题色

menu: [...]      # 菜单树（数组）
footer:          # 页脚配置
  variant: columns
  columns: []

header:          # 页眉配置
  variant: logo_left_menu_right
  lang_switcher_style: vertical_dropdown
```

### 4.2 页面 YAML 结构

每个页面文件（如 `home.yaml`）的核心是 `modules` 数组：

```yaml
modules:
  - type: hero_banner       # 模块类型（对应 blocks/ 下的目录名）
    order: 1                # 排序（数字越小越靠前）
    variant: text_overlay   # 使用的变体（可选，默认 default）
    data:                   # 模块数据字段
      slides:
        - type: image
          media: ""
          title: 主标题
          subtitle: 副标题
          primaryBtn: 按钮文字
          primaryBtnLink: /products/
```

### 4.3 数据集 YAML 结构

支持两种格式：
```yaml
# 格式一：纯列表
- id: 1
  name: 产品名
  slug: product-slug
  ...

# 格式二：带元信息的字典
items:
  - id: 1
    name: 产品名
    ...
categories:
  - 分类一
  - 分类二
```

系统自动标准化，未指定 `id` 的条目自动按顺序分配（从 1 开始）。

---

## 5. 后台管理界面

管理后台是三栏 SPA 布局：

| 区域 | 宽度 | 功能 |
|------|------|------|
| 左侧导航 | 240px（可折叠至 60px） | 站点切换、设置项、内容管理、页面列表 |
| 中间预览 | 自适应 | 实时预览站点（桌面/平板/手机三种视口切换） |
| 右侧面板 | 380px（可拖拽至 240-900px） | 属性编辑表单，AJAX 提交保存 |

### 5.1 左侧导航菜单

**设置区**：
- 公司信息 — 名称、联系方式、备案号
- 页眉 — 页眉样式、语言切换器、社交链接
- 菜单 — 网站导航结构
- 页脚 — 页脚样式、版权、链接
- 主题色 — 主色、背景色、文字色、边框色
- 账号 — 退出登录、删除站点

**内容区**：
- 概览 — 站点统计
- 首页 — 首页模块编辑
- 动态页面 — 由菜单树生成的页面入口
- 数据集 — 产品、项目案例、博客

**站点区**：
- 模板画廊 — 浏览可用模板
- 新建站点

### 5.2 右侧面板操作

- 所有表单通过 AJAX 提交，保存后自动刷新预览
- 面板可关闭/重新打开
- 支持拖拽调整宽度
- 表单底部有固定保存按钮栏

### 5.3 预览区操作

- **设备切换**：桌面（全宽）/ 平板（768px）/ 手机（375px）
- **点击编辑**：点击预览中的任何模块，右侧面板自动定位到该模块的编辑表单
- **点击页眉/页脚**：打开对应的设置面板

---

## 6. 全局设置

### 6.1 公司信息

路径：左侧导航 → 设置 → 公司信息

| 字段 | 说明 |
|------|------|
| 公司名称 | 全称，显示在页眉和页脚 |
| 公司简称 | 用于紧凑空间 |
| Logo | 上传公司 Logo 图片 |
| ICP 备案号 | 显示在页脚 |
| 电话 | 座机号码 |
| 手机 | 手机号码 |
| 邮箱 | 联系邮箱 |
| 地址 | 公司地址 |
| 营业时间 | 工作日时间 |
| 周末提示 | 周末特别说明 |

### 6.2 页眉设置

路径：左侧导航 → 设置 → 页眉

**四种页眉样式**：

| 样式 | 说明 |
|------|------|
| `logo_left_menu_right` | 经典布局：Logo 在左，菜单在右 |
| `logo_center_menu_below` | 对称布局：Logo 居中，菜单在下方 |
| `minimal_hamburger` | 极简布局：汉堡菜单，适合移动优先 |
| `top_bar_social` | 顶栏布局：联系信息 + 社交图标 |

**语言切换器样式**：

| 样式 | 说明 |
|------|------|
| `vertical_dropdown` | 下拉按钮（带箭头） |
| `inline_row` | 水平排列：简体中文 \| English \| 繁體中文 |
| `flag_icon` | 旗帜 emoji + 语言代码 |

**社交链接**（显示在页眉顶栏）：github, twitter, facebook, linkedin, youtube

### 6.3 主题色

路径：左侧导航 → 设置 → 主题色

| 变量 | 说明 | 默认值 |
|------|------|--------|
| 主色 `color-primary` | 按钮、链接、强调色 | `#067a7a` |
| 主色悬停 `color-primary-hover` | 鼠标悬停时的主色加深 | `#056060` |
| 主色浅 `color-primary-light` | 主色的浅色变体 | `#0d9488` |
| 辅色 `color-secondary` | 次要强调色 | `#f97316` |
| 文字色 `color-text` | 正文颜色 | `#1a1a1a` |
| 反白文字 `color-text-inverse` | 深色背景上的文字 | `#ffffff` |
| 背景色 `color-bg` | 页面背景 | `#ffffff` |
| 次级背景 `color-bg-secondary` | 区块背景 | `#f5f7fa` |
| 边框色 `color-border` | 卡片/分割线边框 | `#e5e7eb` |
| 灰色文字 `color-muted` | 次要文字、说明文字 | `#6b7280` |
| 阴影 sm/md/lg `shadow-*` | 三级阴影深度 | — |
| 圆角 sm/md/lg `radius-*` | 三级圆角 | `6px/12px/16px` |
| 字体 `font-sans` | 字体栈 | Inter + Noto Sans SC/TC |

### 6.4 页脚设置

路径：左侧导航 → 设置 → 页脚

**四种页脚样式**：

| 样式 | 说明 |
|------|------|
| `four_columns` | 四列链接布局 |
| `three_columns_subscribe` | 三列 + 订阅框 |
| `minimal_single_line` | 极简单行（仅版权 + 备案号） |
| `map_contact` | 地图 + 联系方式 |

页脚支持**动态列**配置：每列可设定标题和多个链接项（标签 + URL）。另包含版权文字、ICP 备案号。

### 6.5 社交链接

路径：左侧导航 → 设置 → 社交

| 字段 | 说明 |
|------|------|
| GitHub | GitHub 主页 |
| Twitter | Twitter 主页 |
| Facebook | Facebook 主页 |
| LinkedIn | LinkedIn 主页 |
| YouTube | YouTube 频道 |

---

## 7. 菜单系统

### 7.1 菜单项类型

菜单树由以下五种类型的节点构成：

| 类型 | 说明 | URL 规则 | 示例 |
|------|------|----------|------|
| `home` | 首页（固定在第一位） | `/` | 首页 |
| `list` | 数据集列表页 | `/{target}/` | 产品列表 → `/products/` |
| `page` | 自定义页面 | `/{target}/` | 关于我们 → `/about/` |
| `link` | 外部链接 / 自定义 URL | 完全自定义 | `https://shop.example.com` |
| `group` | 容器（仅用于分组，无独立页面） | 无 | 产品分类下拉菜单 |

### 7.2 下拉菜单样式

当菜单项有子级时，可设置 `dropdown_style`：

| 样式 | 说明 |
|------|------|
| `vertical` | 纵向列表下拉 |
| `horizontal` | 横向展开 |
| `grid` | 网格布局 |
| `cards` | 卡片式布局 |

### 7.3 菜单编辑操作

路径：左侧导航 → 设置 → 菜单

- **添加菜单项**：点击"添加"，选择类型，填写标签和链接目标
- **添加子菜单**：在父项下添加子项
- **拖拽排序**：上下拖动调整顺序
- **删除**：删除前系统会检查影响范围（被其他地方引用的菜单项会收到警告）
- **多语言菜单**：切换语言后可编辑对应语言的菜单标签
- **AI 翻译**：一键将菜单标签翻译到其他语言

### 7.4 菜单约束

- 最大嵌套深度：8 层
- 首页始终在第一位（自动保证）
- `group` 类型不可作为顶级项的目标页

---

## 8. 页面与模块

### 8.1 页面概念

页面 = 一组模块的**有序排列**。存储为 `sites/<id>/pages/<key>.yaml`。

页面分为两类：
- **固定页面**：由站点模板预设（如 `home`、`about`、`contact`）
- **动态页面**：由菜单系统根据 `type: page` 项自动创建对应页面

### 8.2 模块概念

模块 = 页面上一个独立的功能区块。每个模块对应 `site_templates/<name>/blocks/<type>/` 下的一个目录。

**模块的三要素**：

| 要素 | 说明 |
|------|------|
| `type` | 模块类型名（对应 blocks/ 下的目录名） |
| `variant` | 使用的变体（可选，不同布局/样式预设） |
| `data` | 模块数据字段（由模块的 `meta.yaml` 定义） |

### 8.3 模块分类

| 类别 | 说明 | 包含模块 |
|------|------|----------|
| **内容块** | 手动填写内容的区块 | hero_banner, highlight_card, section_title, text_content, feature_grid, stat_counter, process_steps, logo_cloud, contact_info, item_detail |
| **数据块** | 自动从数据集拉取内容 | data_grid |

### 8.4 模块通用操作

- **添加模块**：在右侧面板点击"添加模块"，从模块库中选择
- **删除模块**：点击模块编辑区的删除按钮
- **拖拽排序**：上下拖动模块调整页面顺序
- **变体切换**：在模块顶部选择不同变体（如果模块支持）
- **响应式覆盖**：可分别设置桌面/平板/手机下的列数、显示数量、每页条数等

### 8.5 模块的字段类型

| 字段类型 | UI 控件 | 说明 |
|----------|---------|------|
| `text` | 文本框 | 单行文本 |
| `textarea` | 文本域 | 多行文本 |
| `richtext` | 富文本编辑器 | 支持 HTML 格式 |
| `color` | 颜色选择器 | HEX 颜色值 |
| `number` | 数字输入 | 整数 |
| `select` | 下拉选择 | 预设选项 |
| `url` | URL 输入 | 链接地址 |
| `image` | 图片上传 | 上传并自动转 WebP |
| `icon` | 图标选择器 | 选择预设 SVG 图标 |
| `list` | 列表编辑器 | 可增删的动态子项列表 |

---

## 9. 模块库详解

以下按照后台模块选择器的排列顺序，逐个说明每个模块的**用途、适用场景、所有字段和配置**。

---

### 9.1 Hero Banner（首页轮播大图）

**用途**：全屏轮播图/视频，是访客看到的第一屏。支持自动轮播、圆点导航、前后箭头。

**适用场景**：首页顶部、重要活动推广

**核心字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `hero_width` | text | Banner 整体宽度，如 `100%`（留空=全宽） |
| `hero_height` | text | Banner 整体高度，如 `500px` 或 `77vh`（留空=默认 77vh） |
| `banner_align` | select | 排版方式：默认全宽 / 居中 / 居左 / 居右 |
| `inner_width` | text | 内层内容区宽度，如 `1200px` |

**配色字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title_font_size` | text | 标题字号，如 `3.5rem` |
| `title_color` | color | 标题颜色（留空=白色） |
| `subtitle_font_size` | text | 副标题字号，如 `1.25rem` |
| `subtitle_color` | color | 副标题颜色 |
| `btn_font_size` | text | 按钮字号 |
| `btn_text_color` | color | 按钮文字色 |
| `btn_bg` | color | 按钮背景色（留空=使用主色） |

**幻灯片列表（`slides`）**：每个幻灯片可配置：

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | select | 媒体类型：图片 / 视频 |
| `media` | url | 图片或视频地址 |
| `title` | text | 主标题 |
| `subtitle` | text | 副标题 |
| `primaryBtn` | text | 主按钮文字 |
| `primaryBtnLink` | url | 主按钮链接 |
| `secondaryBtn` | text | 副按钮文字 |
| `secondaryBtnLink` | url | 副按钮链接 |

**使用示例**（home.yaml 中的配置）：
```yaml
modules:
  - type: hero_banner
    order: 1
    variant: text_overlay
    data:
      slides:
        - type: image
          media: ""
          title: 专业展示道具定制开发
          subtitle: 为博物馆、商场、展览馆提供智能展示解决方案
          primaryBtn: 了解产品
          primaryBtnLink: /products/
          secondaryBtn: 联系我们
          secondaryBtnLink: /contact/
```

---

### 9.2 Section Title（标题模块）

**用途**：页面中的段落标题，用于分隔不同内容区域。支持标签、标题、描述、按钮。

**适用场景**：页面各内容段落的标题区；"我们的产品"、"关于我们"、"联系我们"等标题

**外层样式字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `section_bg` | color | 外层背景色（留空=透明） |
| `inner_width` | text | 内容区宽度，如 `1200px`（留空=全宽） |
| `text_align` | select | 文字排版：居中（默认）/ 居左 / 居右 |

**间距字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `margin_top` | text | 上间距，如 `2rem` |
| `margin_bottom` | text | 下间距，如 `2rem` |
| `padding_top` | text | 上内边距，如 `4rem` |
| `padding_bottom` | text | 下内边距，如 `4rem` |
| `padding_left` | text | 左内边距，如 `2rem` |
| `padding_right` | text | 右内边距，如 `2rem` |

**内容字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `tag` | text | 模块上方小标签文字 |
| `title` | text | 主标题 |
| `desc` | textarea | 描述文字 |

**字体样式字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title_color` | color | 标题颜色 |
| `title_size` | text | 标题字号，如 `2.5rem` |
| `desc_color` | color | 描述颜色 |
| `desc_size` | text | 描述字号 |
| `tag_bg` | color | 标签背景色 |
| `tag_color` | color | 标签字体色 |

**按钮字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `btn_text` | text | 按钮文字 |
| `btn_url` | url | 按钮链接 |
| `btn_target` | select | 打开方式：当前页 / 新标签页 |
| `btn_bg` | color | 按钮背景色 |
| `btn_color` | color | 按钮文字色 |

---

### 9.3 Feature Grid（功能特色网格）

**用途**：展示服务/功能亮点，图标 + 标题 + 描述的三列卡片网格。功能卡片直接在模块编辑器中管理，也可回退到全局 `features` 数据集。

**适用场景**：首页核心功能展示、服务介绍、产品特性

**布局字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | text | 区块标题 |
| `subtitle` | text | 区块副标题 |
| `max_width` | text | 整体最大宽度，如 `1200px` |
| `block_align` | select | 整体对齐：默认全宽 / 居中 / 居左 / 居右 |
| `card_align` | select | 卡片组对齐：默认拉伸 / 居中 / 居左 / 居右 |

**外层样式字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `section_bg` | color | 外层背景色 |
| `inner_width` | text | 内层内容区宽度 |
| `margin_top/right/bottom/left` | text | 四向外边距 |

**卡片样式字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `card_show_border` | select | 显示边框：默认显示 / 隐藏（设为 `0`） |
| `card_padding_top/right/bottom/left` | text | 卡片四向内边距，如 `24px` |
| `card_radius_top_left/top_right/bottom_right/bottom_left` | text | 卡片四角独立圆角 |

**功能卡片列表（`features`）**：每张卡片包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `icon` | icon | 功能图标 |
| `title` | text | 功能标题 |
| `desc` | textarea | 功能描述 |

**可用图标列表**：
`circuit`（电路）、`code`（代码）、`structure`/`layers`（结构）、`sensor`（传感器）、`interactive`（交互）、`audio`（音频）、`cpu`（芯片）、`settings`/`gear`（设置）、`shield`（盾牌）、`zap`/`lightning`（闪电）、`wifi`（无线）、`globe`（地球）、`package`（包裹）、`tool`（工具）、`bar-chart`/`chart`（图表）、`monitor`/`display`（显示器）、`camera`/`video`（视频）、`light`/`bulb`（灯泡）、`bluetooth`（蓝牙）、`touch`/`hand`（触摸）

---

### 9.4 Highlight Card（图文模块）

**用途**：通用图文介绍模块，支持左右布局切换。包含标签、标题、描述、图片、功能点列表和双按钮。

**适用场景**：产品亮点介绍、公司介绍、特色服务展示

**外层样式字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `section_bg` | color | 外层背景色 |
| `inner_width` | text | 内容区宽度 |
| `border_radius` | text | 圆角，如 `12px` |
| `margin_top` | text | 上外边距 |
| `margin_bottom` | text | 下外边距 |
| `padding_top/bottom/left/right` | text | 四向内边距 |

**图文布局**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `image_position` | select | 图文位置：图左文右 / 文左图右 |

**内容字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `tag` | text | 标签文字（如"明星产品"） |
| `title` | text | 主标题 |
| `desc` | textarea | 描述文字 |
| `image` | image | 主图 |

**特性列表（`features`）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `text` | text | 单个特性要点 |

**双按钮**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `primaryBtn` | text | 主按钮文字 |
| `primaryLink` | url | 主按钮链接 |
| `primaryLinkTarget` | select | 打开方式：当前页 / 新标签页 |
| `secondaryBtn` | text | 副按钮文字 |
| `secondaryLink` | url | 副按钮链接 |

**配色字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `text_bg` | color | 文本区背景色（留空=透明） |
| `text_color` | color | 文本区字体颜色 |
| `tag_bg` | color | 标签背景色 |
| `tag_color` | color | 标签字体颜色 |
| `btn_bg` | color | 按钮背景色 |
| `btn_color` | color | 按钮字体颜色 |

---

### 9.5 Text Content（文本内容）

**用途**：通用文本内容块，支持标题 + 富文本正文。支持单栏/双栏排版。

**适用场景**：公司介绍、团队介绍、隐私政策、服务条款、任何大段文字

**变体**：`default`（标准宽度）/ `narrow`（窄栏，适合阅读）

**内容字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | text | 标题 |
| `body` | richtext | 正文内容（富文本，支持 HTML 格式） |

**文字排版字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `text_align` | select | 对齐：居左 / 居中 / 居右 |
| `columns` | select | 分栏：单栏 / 双栏 |

**外层样式字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `section_bg` | color | 外层背景色 |
| `inner_width` | text | 内容区宽度，如 `800px` |
| `margin_top/right/bottom/left` | text | 四向外边距 |
| `padding_top/right/bottom/left` | text | 四向内边距 |

**文字样式字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title_size` | text | 标题字号，如 `2rem` |
| `title_color` | color | 标题颜色 |
| `body_size` | text | 正文字号，如 `1rem` |
| `body_color` | color | 正文颜色 |

---

### 9.6 Process Steps（流程步骤）

**用途**：步骤/流程图展示，支持横向/纵向排列和数字/图标两种标记样式。

**适用场景**：服务流程、合作方式、公司发展历程、操作步骤

**变体**：`horizontal`（横向排列）/ `vertical`（纵向排列）/ `numbered`（数字序号）

**外层样式字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `section_bg` | color | 外层背景色 |
| `inner_width` | text | 内容区宽度 |
| `inner_bg` | color | 内层背景色 |
| `padding_top/right/bottom/left` | text | 四向内边距 |

**内容字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | text | 区块标题 |
| `subtitle` | text | 区块副标题 |
| `direction` | select | 排列方向：横向 / 纵向 |
| `step_style` | select | 步骤样式：数字序号 / 图标 |

**字体样式字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title_font_size` | text | 标题字号 |
| `title_color` | color | 标题颜色 |
| `desc_font_size` | text | 描述字号 |
| `desc_color` | color | 描述颜色 |

**配色字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `icon_color` | color | 图标颜色 |
| `number_bg` | color | 序号背景色 |
| `number_font_size` | text | 序号字号 |

**步骤列表（`steps`）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | text | 步骤标题 |
| `desc` | textarea | 步骤描述 |
| `icon` | icon | 图标（仅图标样式时生效） |

**图标样式可用图标**：`search`/`magnify`（搜索）、`edit`/`pen`（编辑）、`check`/`check-circle`（确认）、`truck`/`shipping`（运输）、`settings`/`gear`（设置）、`chat`/`message`（对话）

---

### 9.7 Stat Counter（数据统计）

**用途**：数字 + 标签展示，支持图标和数字后缀（如 +、k、%）。页面滚动到可见区域时自动触发数字滚动动画。

**适用场景**：公司实力数据（年产值、项目数、客户数、专利数等）

**变体**：`grid_3`（三列）/ `grid_4`（四列）/ `grid_6`（六列）

**外层样式字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `section_bg` | color | 外层背景色 |
| `inner_width` | text | 内容区宽度 |

**内容字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | text | 区块标题 |
| `subtitle` | text | 区块副标题 |
| `columns` | select | 每行列数：三列 / 四列 / 六列 |

**统计项列表（`stats`）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `number` | number | 统计数字（整数） |
| `suffix` | text | 后缀，如 `+`、`k`、`%` |
| `label` | text | 标签文字（如"已完成项目"） |
| `icon` | icon | 图标 |

**可用图标**：`users`（用户/人）、`briefcase`/`building`（建筑/公司）、`check`/`shield-check`（确认/认证）、`star`/`award`（星级/奖项）、`clock`/`history`（时钟/历史）

---

### 9.8 Logo Cloud（合作品牌墙）

**用途**：Logo 网格展示合作品牌/客户，支持灰度滤镜（hover 时恢复彩色）、链接跳转。

**适用场景**：客户背书、合作伙伴展示

**变体**：`grid_4`（四列）/ `grid_5`（五列）/ `grid_6`（六列）

**外层样式字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `section_bg` | color | 外层背景色 |
| `inner_width` | text | 内容区宽度 |
| `inner_bg` | color | 内层背景色 |
| `padding_top/right/bottom/left` | text | 四向内边距 |

**Logo 卡片样式字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `logo_bg` | color | 卡片背景色 |
| `logo_border` | text | 边框样式，如 `1px solid #e5e7eb` |
| `logo_border_color` | color | 边框色 |
| `logo_radius` | text | 圆角，如 `8px` |
| `logo_width` | text | Logo 宽度，如 `120px` |
| `logo_height` | text | Logo 高度，如 `60px` |

**内容字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | text | 区块标题 |
| `subtitle` | text | 区块副标题 |
| `columns` | select | 每行列数：四列 / 五列 / 六列 |
| `grayscale` | select | 灰度滤镜：开启（hover 恢复彩色）/ 关闭（保持原色） |

**Logo 列表（`logos`）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `image` | image | Logo 图片 |
| `name` | text | 品牌名称（alt 文字） |
| `link` | url | 跳转链接（可选） |

---

### 9.9 Contact Info（联系方式）

**用途**：自动读取站点全局设置中的联系方式（公司信息页填写的电话、邮箱、地址、营业时间），以卡片或列表方式展示。

**特别注意**：此模块不存独立数据，而是从 `settings.contact` 读取。需先在"公司信息"页面填写联系方式。

**适用场景**：联系页面的联系方式展示

**变体**：`cards`（卡片网格）/ `list`（纵向列表）

**显示控制字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | text | 区块标题 |
| `subtitle` | text | 区块副标题 |
| `show_phone` | select | 显示/隐藏电话 |
| `show_mobile` | select | 显示/隐藏手机 |
| `show_email` | select | 显示/隐藏邮箱 |
| `show_address` | select | 显示/隐藏地址 |
| `show_business_hours` | select | 显示/隐藏营业时间（默认关闭） |

**外层样式字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `section_bg` | color | 外层背景色 |
| `inner_width` | text | 内容区宽度 |

---

### 9.10 Item Detail（条目详情）

**用途**：双栏布局的详情展示模块。左侧多图切换（带 2.5 倍放大镜），右侧展示标题、标签、描述、规格参数表。

**适用场景**：产品详情页、项目案例详情页

**外层样式字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `section_bg` | color | 外层背景色 |
| `inner_width` | text | 内容区宽度 |
| `inner_bg` | color | 内层背景色 |
| `padding_top/right/bottom/left` | text | 四向间距 |

**图片样式字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `img_border_radius` | text | 图片圆角 |
| `img_height` | text | 图片高度，如 `400px` |

**内容字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | text | 标题 |
| `desc` | textarea | 描述 |
| `tags` | text | 标签（逗号分隔） |

**配色字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `text_bg` | color | 文本区背景色 |
| `text_color` | color | 文本区字体颜色 |
| `tag_bg` | color | 标签背景色 |
| `tag_color` | color | 标签字体颜色 |

**图片列表（`images`）**：`url`（image 类型）

**规格参数（`specs`）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | text | 参数名（如"尺寸"） |
| `value` | text | 参数值（如"120×80×60cm"） |

---

### 9.11 Data Grid（数据网格）

**用途**：最强大的通用数据列表模块。从数据集自动拉取内容，支持产品/项目案例/博客三种数据集，两种卡片布局，两种分页方式。

**适用场景**：产品列表、项目案例展示、博客文章列表、任何需要列表+分页的数据展示

**类别**：`data`（数据块，自动拉取数据集内容）

**数据源字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `dataset` | text | 数据集名称：`products` / `portfolio` / `posts` 或自定义数据集 |
| `max_items` | number | 最大显示数量，默认 6 |
| `card_layout` | select | 卡片布局：上图下文 / 左图右文 |

**分页字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `show_pagination` | select | 显示分页 / 隐藏分页 |
| `pagination_style` | select | 分页样式：加载更多按钮 / 页码导航 |
| `items_per_page` | number | 每页条数，默认 6 |
| `pager_align` | select | 分页对齐：居中 / 居左 / 居右 |

**外层样式字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `section_bg` | color | 外层背景色 |
| `inner_width` | text | 内容区宽度 |
| `margin_top/right/bottom/left` | text | 四向外边距 |

**内容字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | text | 区块标题（如"近期项目"、"最新动态"） |

**使用方式**：
- 数据集名称对应 `sites/<id>/data/<name>.yaml`
- 卡片自动读取数据集的：`cover`（封面图）、`name`（标题）、`summary`（摘要）、`slug`（链接）、`category`（分类）、`date`（日期）、`tags`（标签）
- 分页在前端用 JavaScript 驱动（不刷新页面）
- 响应式覆盖可分别设置桌面/平板/手机下的 `max_items` 和 `items_per_page`

---

### 9.12 Product Grid（产品网格）

**用途**：专门从产品数据集自动拉取产品卡片，以三列网格展示。相比 Data Grid 更简洁，固定针对产品数据集。

**适用场景**：首页产品展示、产品分类页

**类别**：`data`（数据块）

**数据字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `dataset` | select | 数据来源（固定为 `products`） |
| `max_items` | number | 最大显示数量，默认 6 |

**外层样式字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `section_bg` | color | 外层背景色 |
| `inner_width` | text | 内容区宽度 |

**内容字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | text | 区块标题 |

---

### 9.13 特殊模块：item_data

`item_data` 不是 `blocks/` 目录下的物理模块，而是数据集条目的详情页专用虚拟模块。当在数据集条目（产品、案例、文章）的详情页配置中使用 `item_data` 模块时，它会渲染该条目本身的数据（title、description、body、tags 等），不需要手动填写。

**用途**：数据集详情页的内容渲染。在编辑数据集条目时选择此模块即可自动展示条目数据。

---

## 10. 数据集管理

### 10.1 数据集概述

数据集是结构化内容的存储方式。每个数据集是一个 YAML 文件，存储在 `sites/<id>/data/<name>.yaml`。

**当前模板定义的数据集**：

| 数据集名 | 文件 | 用途 | 支持语言 |
|----------|------|------|----------|
| `products` | `data/products.yaml` | 产品目录 | 是 |
| `portfolio` | `data/portfolio.yaml` | 项目案例 | 是 |
| `posts` | `data/posts.yaml` | 博客文章 | 是 |
| `features` | `data/features.yaml` | 功能特性（备用） | 是 |

### 10.2 产品数据集（products）

每个产品条目的字段：

| 字段 | 类型 | 说明 | 显示在 |
|------|------|------|--------|
| `slug` | text | URL 标识（唯一，用于生成 `/products/<slug>/`） | URL |
| `name` | text | 产品名称 | 卡片、详情页 |
| `category` | text | 产品分类 | 卡片标签 |
| `cover` | image | 封面图 | 卡片 |
| `image` | image | 主图 | 详情页 |
| `summary` | text | 产品简介 | 卡片 |
| `description` | textarea | 详细描述 | 详情页 |
| `tags` | list | 标签（逗号分隔） | 详情页 |

产品还可拥有**模块列表**（`modules`），用于自定义产品详情页的展示模块。

全局分类存储在 `categories` 数组中（每个产品条目之上的父级键）。

### 10.3 项目案例数据集（portfolio）

每个案例条目的字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `slug` | text | URL 标识 |
| `name` | text | 项目名称 |
| `category` | text | 项目分类 |
| `cover` | image | 封面图 |
| `date` | text | 项目日期 |
| `summary` | text | 项目简介 |
| `description` | textarea | 详细描述 |
| `tags` | list | 标签 |

### 10.4 博客文章数据集（posts）

每篇文章的字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `slug` | text | URL 标识 |
| `title` | text | 文章标题 |
| `date` | text | 发布日期 |
| `cover` | image | 封面图 |
| `excerpt` | textarea | 文章摘要 |
| `body` | richtext | 正文内容（富文本） |
| `tags` | list | 标签 |

### 10.5 数据集操作

在后台通过"内容 → 数据集名称"进入管理面板：

- **查看列表**：表格展示所有条目（封面缩略图、名称、slug、日期等）
- **新增条目**：点击"添加"，填写表单后保存
- **编辑条目**：点击条目进入编辑模式，可修改所有字段
- **删除条目**：点击删除按钮
- **拖拽排序**：在列表视图中上下拖拽调整顺序
- **模块配置**：编辑模式下可为条目添加详情页模块（如 `item_detail`、`text_content` 等）
- **多语言**：切换语言后编辑对应语言版本的数据
- **AI 翻译**：一键将条目内容翻译到其他语言

### 10.6 数据集 URL 映射

| 数据集 | 列表页 URL | 详情页 URL |
|--------|-----------|-----------|
| `products` | `/products/` | `/products/<slug>/` |
| `portfolio` | `/portfolio/` | `/portfolio/<slug>/` |
| `posts` | `/posts/` | `/posts/<slug>/` |

URL 由菜单系统和 builder 自动处理。在菜单中配置 `type: list` + `target: products` 即可自动生成产品列表页。

---

## 11. 构建与发布

### 11.1 CLI 构建

```bash
flask --app run build-site <site_id>
```

构建输出目录：`output/<site_id>/`

### 11.2 Web 构建

在管理后台点击"构建"按钮，系统自动构建并跳转预览。

### 11.3 构建流程

1. 加载站点设置、页面、数据集（合并种子数据默认值）
2. 加载模板翻译文件
3. 解析菜单树，收集所有需要渲染的页面任务
4. 设置 Jinja2 环境，加载模板文件
5. 根据语言列表逐语言渲染：
   - 首页
   - 数据集列表页
   - 数据集详情页
   - 自定义页面
6. 复制静态资源（CSS、JS、图片）和用户上传资产到输出目录
7. 生成语言选择器根页面

### 11.4 导出 ZIP

后台提供一键导出功能，将构建好的静态站点打包为 ZIP 下载。用户拿到 ZIP 后可以直接部署到任何静态托管服务（Nginx、GitHub Pages、阿里云 OSS 等）。

---

## 12. 常用场景示例

### 12.1 新建站点并设置首页

```bash
# 1. 创建用户
flask --app run create-user boss@example.com

# 2. 同步模板
flask --app run scan-templates

# 3. 创建站点
flask --app run create-site boss@example.com my-company --template dengtec --name "我的公司"

# 4. 启动开发服务器
python run.py
```

然后访问 `http://localhost:5000`，登录后：
1. 进入"设置 → 公司信息"，填写公司名称、联系方式
2. 进入"设置 → 主题色"，选择品牌色
3. 进入"内容 → 首页"，编辑首页模块：
   - 修改 Hero Banner 的标题和副标题
   - 修改 Feature Grid 的功能卡片
   - 修改 Highlight Card 的图文内容
4. 点击"构建"预览效果

### 12.2 添加产品

1. 进入"内容 → 产品"
2. 点击"添加产品"
3. 填写产品名称、slug（如 `led-display`）、分类、简介、详细描述
4. 上传封面图和主图
5. 在模块区添加 `item_data` 模块（自动展示产品数据）
6. 保存
7. 菜单中确保有 `type: list, target: products` 的菜单项
8. 重新构建，访问 `/products/` 查看产品列表

### 12.3 添加自定义页面

1. 进入"设置 → 菜单"
2. 添加菜单项：类型选择 `page`，标签填写"服务流程"，目标填写 `service`
3. 保存菜单
4. 左侧导航自动出现"服务流程"页面入口
5. 在页面中添加模块，如：
   - 一个 `section_title` 作为页面标题
   - 一个 `process_steps` 展示服务流程
   - 一个 `highlight_card` 展示核心服务
6. 构建预览

### 12.4 首页典型模块组合

推荐的首页模块排列顺序：

| 顺序 | 模块 | 用途 |
|------|------|------|
| 1 | `hero_banner` | 第一屏轮播大图，传达品牌核心信息 |
| 2 | `feature_grid` | 三列功能卡片，告诉访客"我们能做什么" |
| 3 | `highlight_card` | 图文展示明星产品或核心服务 |
| 4 | `data_grid`（portfolio） | 项目案例列表，建立信任背书 |
| 5 | `stat_counter` | 数据统计（项目数、客户数等），强化实力 |
| 6 | `logo_cloud` | 客户/合作伙伴 Logo 墙 |
| 7 | `data_grid`（posts） | 最新动态/博客 |

### 12.5 联系页典型模块组合

| 顺序 | 模块 | 用途 |
|------|------|------|
| 1 | `section_title` | 页面标题"联系我们" |
| 2 | `contact_info`（cards 变体） | 联系方式卡片（电话、邮箱、地址） |
| 3 | `text_content` | 附加说明文字（如交通指引、服务时间补充） |

### 12.6 关于页典型模块组合

| 顺序 | 模块 | 用途 |
|------|------|------|
| 1 | `section_title` | 页面标题"关于我们" |
| 2 | `highlight_card` | 公司简介（文左图右） |
| 3 | `stat_counter` | 公司实力数据 |
| 4 | `process_steps` | 发展历程 |
| 5 | `text_content` | 企业文化、愿景等大段文字 |

---

> 最后更新：2026-05-18
