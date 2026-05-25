---
name: template-new-block
description: "Block 组件的创建与修改（新增模块类型/修改字段/调整样式表单）"
---

当用户说"新建 Block"、"加个模块"、"创建组件"、"修改模块字段"、"调整模块样式"时触发.
在现有模板的 blocks/ 下创建或修改可复用模块(meta.yaml + template.html).

**修改现有模块时，必须同步更新三处：Jinja 模板 + addModule() + admin_modules.js，详见 [三处同步规则](reference/three-place-sync.md)。**

Block 是网站页面的组成单元——首页横幅、产品网格、功能介绍、客户评价等都是 Block.
店主在后台给页面拖拽和配置 Block(在 _panel 页面编辑器中选择、排序、填写).

核心代码:`app/core/template_loader.py` → `scan_blocks()`

## 设计 Block 前确认

1. **这个 Block 解决什么展示需求**?(是展示产品?展示评价?展示数据?)
2. **店主需要配置哪些字段**?(标题、描述、图片、列表项等)
3. **哪个现有模板需要它**?(`dengtec`)
4. **参考哪个现有 Block**?(`hero_banner`、`feature_grid`、`product_grid` 等)

Block 设计的核心原则:
- **一个 Block 做好一件事**(不要做一个"万能通用模块")
- **字段够用就好**(不是越多越好,店主填起来累)
- **固定样式写在 CSS**,可变样式通过字段配置
- **meta.yaml 的 default 必须与 CSS 兜底值一致**: 每个字段的 `default` 要填模板 CSS 中的实际默认值(如 padding 默认 1rem、header 内层宽度默认 1440px), 不能随意留空。 详见 [reference/meta-yaml.md](reference/meta-yaml.md#default-字段填写规则硬约束)
## 创建目录和文件

```
site_templates/<template>/blocks/<name>/
├── meta.yaml       # Block 定义:显示名、分类、字段列表、变体
└── template.html   # Jinja2 渲染模板 + 内联 JS(如需要)
```

Block 命名约定:
- 目录名用英文下划线:`testimonial_carousel`、`faq_accordion`
- meta.yaml 中 name 用中文:`客户评价轮播`、`FAQ 折叠`
- category:`hero`(首屏)/ `content`(内容)/ `data`(数据展示)/ `social`(社交证明)/ `layout`(布局)

## 编写 meta.yaml

完整格式参考(以 `highlight_card` 为例):

```yaml
name: 图文模块
category: content
icon: highlight_card.svg
description: 通用图文介绍模块，支持左右布局切换
fields:
  - key: title          # 字段标识(在 template.html 中用 md.get('title') 访问)
    label: 标题          # 后台显示标签
    type: text           # 字段类型
    group: 内容          # 后台分组(同类字段放一组)
    default: ""

  - key: desc
    label: 描述
    type: textarea
    group: 内容
    default: ""

  - key: image
    label: 图片
    type: image
    group: 内容

  - key: section_bg
    label: 外层背景色
    type: color
    group: 外层样式
    default: ""
    placeholder: 如 #f5f7fa（留空=透明）

  - key: outer_width
    label: 外层宽度
    type: text
    group: 外层样式
    default: ""
    placeholder: 如 1200px（留空使用全局宽度）

  - key: inner_width
    label: 内层内容区宽度
    type: text
    group: 外层样式
    default: ""
    placeholder: 如 1200px（留空=全宽）

  - key: margin_top
    label: 上外边距
    type: text
    group: 外层外边距
    default: ""
    placeholder: 如 0px / 2rem（留空=默认）

  - key: features              # list 类型:子项列表
    label: 功能点列表
    type: list
    group: 特性列表
    item_label: 特性           # 每个子项的显示标签
    item_fields:               # 子字段定义(注意是 item_fields 不是 fields)
      - key: text
        label: 文本
        type: text

variants:                      # 可选:预设样式变体
  - key: default
    label: 图左文右
  - key: right
    label: 图右文左
```

> 字段属性的完整约定、字段类型表、推荐 group 分组详见 [reference/meta-yaml.md](reference/meta-yaml.md)

## 编写 template.html

模板的核心约定详见 [reference/template-html.md](reference/template-html.md)，包含：
- 数据取用 / 条件渲染 / Section 结构 / 内联样式 / CSS 类名 / JS 约束
- data-* 属性列表和用法
- data-* 与内联 style 的选择边界分析
- 浏览器真实渲染输出（示例 B）
- data_grid 完整 Jinja2 源码

## 三处同步（硬约束 ⚠️）

**新增或修改模块的样式编辑表单时，必须同步更新以下三处：**

| # | 文件 | 位置 | 用途 |
|---|------|------|------|
| 1 | `app/templates/dashboard/panel_page_edit.html` | Jinja2 模板（~112-1017行） | 已保存模块的服务端渲染 |
| 2 | `app/templates/dashboard/panel_page_edit.html` | `addModule()` 函数 | 新增模块的客户端生成 |
| 3 | `app/static/js/admin_modules.js` | `buildModuleHTML()` 函数 | 数据集编辑器的模块表单 |

**漏掉任何一处，用户就会看到不一致的界面。**

**新增字段必须按语义归类，插入到相关字段旁边，不能追加到末尾**（详见 [字段排序规则](reference/three-place-sync.md#字段排序规则硬约束)）。

三处代码风格不同（Jinja2 vs JS `cP()`/`uP()` vs JS `_cn()`/`_un()`），但生成的 HTML 结构、字段顺序、分组标签、单位数组必须完全一致。

详细的字段放置规则、单位约定、各模块对照表见 **[reference/three-place-sync.md](reference/three-place-sync.md)**。

## 注册到模板

Block 创建后不需要手动"注册"——`scan_blocks()` 会自动扫描 blocks/ 目录.
Block 创建后立即可在后台页面编辑器中使用.

验证:
1. 启动服务器 `python run.py`
2. 进入后台 → 选择站点 → 页面管理 → 编辑某个页面
3. 在模块选择器中应该能看到新 Block
4. 添加 Block → 填写字段 → 保存 → 预览
5. **打开已保存的模块 → 对比表单和新建时是否一致**

## 常见 Block 类型参考

现有 Block 列表(`site_templates/dengtec/blocks/`):

| Block | 类别 | 用途 |
|-------|------|------|
| hero_banner | hero | 首页横幅(图片/视频 + 标题 + CTA) |
| feature_grid | content | 功能特性网格展示 |
| product_grid | data | 产品卡片网格 |
| data_grid | data | 通用数据网格(从数据集拉数据) |
| highlight_card | content | 高亮卡片(图文左右布局) |
| item_detail | data | 数据详情展示(产品/案例详情) |
| text_content | content | 纯文本内容块 |
| section_title | layout | 区块标题/分隔 |
| stat_counter | social | 统计数字展示 |
| logo_cloud | social | 客户 Logo 墙 |
| contact_info | content | 联系信息展示 |
| process_steps | content | 流程步骤展示 |

## 国际化约束（与 admin_modules.js 相关）

**新建或修改 Block 时，meta.yaml 中的 `label` 和 `placeholder` 目前仍直接使用中文**，这些文字由 `admin_modules.js` 中的 `renderField()` 函数渲染到后台属性面板。

后续管理员后台 UI 国际化实施后（方案见 `.claude/admin-i18n.md`），Block 字段标签也需要支持多语言。当前的过渡约定：

1. **label 用中文写描述性名称**（如 `标题`、`外层背景色`），保持与现有 Block 一致
2. **不要为了"将来可能支持 i18n"而在 label 中使用英文 key**——当前 admin_modules.js 直接渲染 label 值，用英文 key 会让店主看不懂
3. **相似字段复用相同的 label 措辞**（如所有模块的 padding 字段都叫 `内边距`），这样后续做 i18n 时能批量替换

未来改造方向（不在此 skill 范围内）：
- meta.yaml 的 label 改为 i18n key → admin_modules.js 通过 `_t()` 查翻译表
- 或者 meta.yaml 增加 `label_i18n` 字段，存储按语言的翻译

## 关联技能

- `new-template`:创建新模板(Block 属于模板)
- `edit-template-style`:为 Block 添加 CSS 样式
- `block-diagram-svg`:为 Block 生成 HTML 骨架结构示意图 SVG
- `seed-data`:在种子数据中使用 Block
- `add-admin-page`:如果需要后台特殊处理
