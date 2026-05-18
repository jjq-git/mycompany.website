---
description: "脚手架:在指定模板中创建新的 Block 组件"
---

当用户说"新建 Block"、"加个模块"、"创建组件"时触发.
在现有模板的 blocks/ 下创建一个新的可复用模块(meta.yaml + template.html).

Block 是网站页面的组成单元——首页横幅、产品网格、功能介绍、客户评价等都是 Block.
店主在后台给页面拖拽和配置 Block(在 _panel 页面编辑器中选择、排序、填写).

核心代码:`app/core/template_loader.py` → `scan_blocks()`

## 设计 Block 前确认

1. **这个 Block 解决什么展示需求**?(是展示产品?展示评价?展示数据?)
2. **店主需要配置哪些字段**?(标题、描述、图片、列表项等)
3. **哪个现有模板需要它**?(`dengtec` 还是 `tech-product`)
4. **参考哪个现有 Block**?(`hero_banner`、`feature_grid`、`product_grid` 等)

Block 设计的核心原则:
- **一个 Block 做好一件事**(不要做一个"万能通用模块")
- **字段够用就好**(不是越多越好,店主填起来累)
- **固定样式写在 CSS**,可变样式通过字段配置

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

完整格式参考:

```yaml
name: 客户评价轮播
category: social
icon: message-square
description: 轮播展示客户评价,支持头像、姓名、职位和评价内容
fields:
  - name: title
    label: 区块标题
    type: text
    default: 客户怎么说

  - name: subtitle
    label: 副标题
    type: text
    default: ''

  - name: items
    label: 评价列表
    type: list
    fields:
      - name: avatar
        label: 头像
        type: image
      - name: name
        label: 姓名
        type: text
      - name: title
        label: 职位
        type: text
      - name: company
        label: 公司
        type: text
      - name: quote
        label: 评价内容
        type: textarea

  - name: autoplay
    label: 自动播放间隔(秒,0 为不自动)
    type: text
    default: '5'

variants:
  - key: default
    label: 标准轮播
    description: 单列居中轮播
  - key: grid
    label: 网格展示
    description: 多列网格同时展示
  - key: cards
    label: 卡片切换
    description: 卡片叠层切换
```

字段类型(type):
| type | 说明 | 渲染方式 |
|------|------|----------|
| text | 单行文本 | `<input type="text">` |
| textarea | 多行文本 | `<textarea>` |
| image | 图片(上传或 URL) | 文件上传 + 文本框 |
| richtext | 富文本 | 文本域(暂不做编辑器) |
| select | 下拉选择 | `<select>` |
| switch | 开关 | 复选框 |
| color | 颜色 | `<input type="color">` |
| list | 列表(子字段可配置) | 动态添加/删除子项 |
| number | 数字 | `<input type="number">` |

## 编写 template.html

Block 模板的核心约定:

```jinja2
{# site_templates/<name>/blocks/testimonial_carousel/template.html #}

{# 模块数据在 module.data 中,模块类型在 module.type 中 #}
{% set data = module.data %}
{% set variant = module.variant | default('default') %}

{# 如果整个模块是隐藏的(响应式配置中 hidden=true),不渲染 #}
{% if module.responsive and module.responsive.get('hidden') %}
  {# 跳过 #}
{% else %}
  <section class="block block-{{ module.type }} block-{{ module.type }}--{{ variant }}
                  {% if module.responsive and module.responsive.get('tablet', {}).get('hidden') %}hide-tablet{% endif %}
                  {% if module.responsive and module.responsive.get('mobile', {}).get('hidden') %}hide-mobile{% endif %}">

    {% if data.title %}
      <h2 class="block-title">{{ data.title }}</h2>
    {% endif %}

    {% if data.subtitle %}
      <p class="block-subtitle">{{ data.subtitle }}</p>
    {% endif %}

    {# 列表数据渲染 #}
    <div class="testimonial-list">
      {% for item in data.get('items', []) %}
        <div class="testimonial-card">
          {% if item.avatar %}
            <img src="{{ item.avatar }}" alt="{{ item.name }}" class="avatar">
          {% endif %}
          <blockquote>{{ item.quote }}</blockquote>
          <cite>{{ item.name }}{% if item.title %}, {{ item.title }}{% endif %}</cite>
        </div>
      {% endfor %}
    </div>

  </section>
{% endif %}

{# JS 交互:轮播逻辑 #}
{% if data.get('items', []) | length > 1 and data.get('autoplay', '0') != '0' %}
<script>
  (function() {
    // 轮播 JS,IIFE 包裹,不污染全局
    var container = document.querySelector('.testimonial-list');
    var items = container.querySelectorAll('.testimonial-card');
    var interval = parseInt('{{ data.autoplay }}') * 1000;
    // ...轮播逻辑...
  })();
</script>
{% endif %}
```

JS 编写约束:
- 用 IIFE 包裹:`(function() { ... })();`
- 不引入第三方库(jQuery、Swiper 等),纯 vanilla
- 用 `{% if %}` 控制是否输出 JS(只在需要时加载)
- 选择器限定在 `.block-{{ module.type }}` 内,避免跨 Block 冲突

## Block 的响应式配置

每个 Block 自动获得响应式控制能力(由 `_parse_modules_form()` 处理):
- `columns`:电脑端列数
- `max_items`:最大显示条数
- `responsive.tablet.columns` / `tablet.max_items`:平板端配置
- `responsive.mobile.columns` / `mobile.max_items`:手机端配置
- `responsive.tablet.hidden` / `mobile.hidden`:设备隐藏

在 template.html 中通过 CSS class 响应这些配置(main.css 中定义 `.hide-tablet`、`.hide-mobile`).

## 注册到模板

Block 创建后不需要手动"注册"——`scan_blocks()` 会自动扫描 blocks/ 目录.
Block 创建后立即可在后台页面编辑器中使用.

验证:
1. 启动服务器 `python run.py`
2. 进入后台 → 选择站点 → 页面管理 → 编辑某个页面
3. 在模块选择器中应该能看到新 Block
4. 添加 Block → 填写字段 → 保存 → 预览

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

## 关联技能

- `new-template`:创建新模板(Block 属于模板)
- `edit-template-style`:为 Block 添加 CSS 样式
- `seed-data`:在种子数据中使用 Block
- `add-admin-page`:如果需要后台特殊处理
