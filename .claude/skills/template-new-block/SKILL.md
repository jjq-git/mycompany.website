---
name: template-new-block
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
3. **哪个现有模板需要它**?(`dengtec`)
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

**meta.yaml 字段约定:**

| 属性 | 必需 | 说明 |
|------|------|------|
| `key` | 是 | 字段标识,在 template.html 中通过 `md.get('key')` 取值 |
| `label` | 是 | 后台表单显示的标签名 |
| `type` | 是 | 字段类型(见下表) |
| `group` | 推荐 | 后台表单分组,同名 group 的字段归到一组显示 |
| `default` | 推荐 | 默认值(字符串) |
| `placeholder` | 否 | 输入框占位提示 |
| `options` | select 必填 | 下拉选项列表 `[{value, label}]` |
| `item_label` | list 推荐 | 列表项在后台的显示标签 |
| `item_fields` | list 必填 | 列表子字段定义(同 `fields` 格式,用 `key` 标识) |

**字段类型(type):**

| type | 说明 | 渲染方式 |
|------|------|----------|
| `text` | 单行文本 | `<input type="text">` |
| `textarea` | 多行文本 | `<textarea>` |
| `image` | 图片(上传或 URL) | 文件上传 + 文本框 |
| `url` | URL 地址 | `<input type="url">` |
| `richtext` | 富文本 | 文本域(暂不做编辑器) |
| `select` | 下拉选择 | `<select>` (需配 `options`) |
| `switch` | 开关 | 复选框 |
| `color` | 颜色选择器 | `<input type="color">` |
| `list` | 可增删的列表 | 动态添加/删除子项(需配 `item_fields`) |
| `number` | 数字 | `<input type="number">` |
| `icon` | 图标选择 | 下拉选择预设图标名 |

**推荐的字段分组(group):**

| group 名 | 用途 | 包含的典型字段 |
|----------|------|---------------|
| 内容 | 核心内容字段 | title, subtitle, desc, body, image |
| 外层样式 | 区块尺寸和背景 | section_bg, outer_width, inner_width |
| 外层外边距 | margin 控制 | margin_top/right/bottom/left |
| 内层边距 | padding 控制 | padding_top/right/bottom/left |
| 配色 | 颜色相关 | title_color, desc_color, btn_bg, btn_color |
| 字体样式 | 字号控制 | title_size, body_size, title_font_size |

## 编写 template.html

Block 模板的核心约定(以下为实战代码模式,非示意):

### 1. 数据取用

```jinja2
{# 固定模式:取 module.data,用 md 作为简写 #}
{% set md = module.data if module.data else {} %}

{# 访问字段:始终用 .get() 安全访问,第二个参数是默认值 #}
{% set title = md.get('title', '') %}
{% set section_bg = md.get('section_bg', '') %}
{% set cols = md.get('columns', '3') | int %}

{# 全局宽度回退:优先用字段值,其次用全局设置 #}
{% set outer_w = md.get('outer_width', '') or settings.get('layout', {}).get('global_width', '') %}
```

### 2. 条件渲染 — 数据为空时不输出整块

```jinja2
{# 先判断是否有内容,没内容就不渲染任何 HTML #}
{% if md.title or md.desc %}
<section class="section" ...>
  ...
</section>
{% endif %}

{# 列表数据要做类型安全检查 #}
{% set items = md.get('features', []) %}
{% if items is iterable and items is not string and items | length > 0 %}
  {% for item in items %}
    ...
  {% endfor %}
{% endif %}
```

### 3. Section 结构(固定模式)

```jinja2
{# section_bg 为空时自动使用默认背景色 #}
<section class="section{% if not section_bg %} section-bg{% endif %}"
         {% if section_bg or outer_w %} style="
           {% if outer_w %}max-width: {{ outer_w }}; margin-left: auto; margin-right: auto;{% endif %}
           {% if section_bg %}background: {{ section_bg }};{% endif %}
         "{% endif %}>
  <div class="container" style="max-width: {{ inner_w or 'none' }}; margin: 0 auto;">
    {# 标题区 #}
    {% if md.title %}
    <div class="section-header">
      <h2 class="section-title">{{ md.title }}</h2>
      {% if md.subtitle %}<p class="section-description">{{ md.subtitle }}</p>{% endif %}
    </div>
    {% endif %}

    {# 内容区:用 Block 专属 CSS class #}
    <div class="xx-grid" style="...">
      ...
    </div>
  </div>
</section>
```

### 4. CSS 类名约定

每个 Block 使用专属的 BEM 风格 CSS 前缀,不依赖 `module.type`:
- `hero_banner` → `.hero-banner-*`
- `feature_grid` → `.services-grid`, `.service-card`
- `highlight_card` → `.hl-grid`, `.hl-text`, `.hl-image`
- `data_grid` → `.dg-list`, `.dg-card`
- `process_steps` → `.ps-track`, `.ps-step`

不要用 SKILL 旧版中的 `block-{{ module.type }}` 模式 —— 那需要 CSS 配合,实际没有采用。

### 5. 内联样式拼接

```jinja2
{# 收集多个样式片段,用 join 拼接 #}
{% set style_parts = [] %}
{% if outer_w %}{% set _ = style_parts.append('max-width: ' ~ outer_w ~ '; margin-left: auto; margin-right: auto;') %}{% endif %}
{% if section_bg %}{% set _ = style_parts.append('background: ' ~ section_bg ~ ';') %}{% endif %}
{% if mg_top %}{% set _ = style_parts.append('margin-top: ' ~ mg_top ~ ';') %}{% endif %}

<section style="{{ style_parts | join(' ') }}">  {# 用空格连接 #}
```

### 6. JS 编写约束

```jinja2
{# JS 用 IIFE 包裹,不污染全局 #}
<script>
(function(){                         {# 注意:function(){ 不加空格 #}
  var container = document.querySelector('.xx-list');
  if (!container) return;            {# 防护:DOM 不存在就退出 #}

  // 交互逻辑...

})();                                {# IIFE 结尾 #}
</script>

{# 需要复用的函数(如分页回调)放到 window 作用域 #}
<script>
function loadMoreDataGrid(btn) {     {# onclick 回调,必须是全局函数 #}
  var blockId = btn.dataset.blockId;
  // ...
}
</script>
```

**JS 核心规则:**
- IIFE 包裹:`(function(){ ... })();` (注意 `(){` 中间不加空格)
- 不引入第三方库(jQuery、Swiper 等),纯 vanilla JS
- 选择器限定在 Block 专属 class 内,避免跨 Block 冲突
- 用 `{% if %}` 控制是否输出 `<script>` 标签(只在需要交互时加载)
- `IntersectionObserver` 用于滚动触发动画(见 `stat_counter`)

### 7. data-* 属性约定

JS 通过 `data-*` 属性从 HTML 读取动态值,避免在 JS 中硬编码或直接插值. 实际用到的 data 属性:

**data-block-id / data-page / data-per-page / data-total** — 分页/加载更多:

```jinja2
{# 生成唯一 ID:module.order 是模块在页面中的序号 #}
{% set block_id = 'dg-' ~ module.order | default(0) %}

{# 元素上打标,JS 通过 dataset 读取 #}
<div id="{{ block_id }}-list">...</div>
<button class="dg-load-more"
        data-block-id="{{ block_id }}"
        data-page="1"
        data-per-page="{{ per_page }}"
        data-total="{{ total }}"
        onclick="loadMoreDataGrid(this)">加载更多</button>
```

```javascript
// JS 中通过 dataset 读取
function loadMoreDataGrid(btn) {
  var blockId = btn.dataset.blockId;
  var page = parseInt(btn.dataset.page, 10) || 1;
  var perPage = parseInt(btn.dataset.perPage, 10) || 6;
  var total = parseInt(btn.dataset.total, 10) || 0;
  var list = document.getElementById(blockId + '-list');
  // ...
}
```

**data-target** — 动画目标值(如数字滚动):

```jinja2
<div class="sc-number" data-target="{{ stat.number | default(0) }}">0</div>
```

```javascript
var target = parseInt(card.getAttribute('data-target')) || 0;
// 用 requestAnimationFrame 从 0 动画到 target
```

**data-index / data-slide** — 轮播/切换索引:

```jinja2
<div class="hero-banner-slide" data-index="{{ loop.index0 }}">...</div>
<button class="hero-banner-dot" data-slide="{{ loop.index0 }}"></button>
```

```javascript
dot.addEventListener('click', function() {
  showSlide(parseInt(dot.getAttribute('data-slide')));
});
```

**data-full** — 图片缩略图切换:

```jinja2
<div class="id-thumb-item"
     data-full="{{ thumb_src }}"
     onclick="switchItemDetailImage('{{ block_id }}', this, '{{ thumb_src }}')">
</div>
```

**注意事项:**
- HTML 中用 kebab-case (`data-block-id`),JS 中 `dataset` 自动转 camelCase (`btn.dataset.blockId`)
- `getAttribute()` 永远返回字符串,数字需要 `parseInt()` 转换
- `dataset` 在 IE10+ 支持,本项目目标浏览器都兼容

### 8. 完整示例

以 `text_content` Block 为例(实际代码):

```jinja2
{# 文本内容 — 标题 + 多段落正文 #}
{% set md = module.data if module.data else {} %}
{% if md.title or md.body %}
{% set section_bg = md.get('section_bg', '') %}
{% set outer_w = md.get('outer_width', '') or settings.get('layout', {}).get('global_width', '') %}
{% set inner_w = md.get('inner_width', '') %}
{% set text_align = md.get('text_align', 'left') %}
{% set title_color = md.get('title_color', '') %}
{% set title_size = md.get('title_size', '') %}

<section class="section" style="{% if outer_w %}max-width: {{ outer_w }}; margin-left: auto; margin-right: auto;{% endif %}{% if section_bg %}background: {{ section_bg }};{% endif %}">
  <div class="container" style="max-width: {{ inner_w or 'none' }}; margin: 0 auto;">
    <div class="tc-block" style="text-align: {{ text_align }};">
      {% if md.title %}
      <h2 class="tc-title" style="{% if title_color %}color: {{ title_color }};{% endif %}{% if title_size %}font-size: {{ title_size }};{% endif %}">{{ md.title }}</h2>
      {% endif %}
      {% if md.body %}
      <div class="tc-body">
        {% for para in md.body | string | replace('\n\n', '\n') %}
        <p>{{ para | replace('\n', '<br>') }}</p>
        {% endfor %}
      </div>
      {% endif %}
    </div>
  </div>
</section>
{% endif %}
```

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
