# template.html 速查

## 数据取用

```jinja2
{% set md = module.data if module.data else {} %}
{% set title = md.get('title', '') %}
{% set cols = md.get('columns', '3') | int %}

{# 全局宽度回退: 优先字段值, 其次全局设置 #}
{% set outer_w = md.get('outer_width', '') or settings.get('layout', {}).get('global_width', '') %}
```

## 条件渲染

```jinja2
{# 有内容才渲染 #}
{% if md.title or md.desc %}
<section>...</section>
{% endif %}

{# 列表做类型安全检查 #}
{% set items = md.get('features', []) %}
{% if items is iterable and items is not string and items | length > 0 %}
  {% for item in items %}...{% endfor %}
{% endif %}
```

## Section 结构(固定模式)

```jinja2
<section class="section"
         {% if section_bg or outer_w %} style="
           {% if outer_w %}max-width: {{ outer_w }}; margin-left: auto; margin-right: auto;{% endif %}
           {% if section_bg %}background: {{ section_bg }};{% endif %}
         "{% endif %}>
  <div class="container" style="max-width: {{ inner_w or 'none' }}; margin: 0 auto;">
    {% if md.title %}
    <div class="section-header">
      <h2 class="section-title">{{ md.title }}</h2>
      {% if md.subtitle %}<p class="section-description">{{ md.subtitle }}</p>{% endif %}
    </div>
    {% endif %}
    <!-- 内容区 -->
  </div>
</section>
```

## 内联样式拼接

```jinja2
{% set style_parts = [] %}
{% if outer_w %}{% set _ = style_parts.append('max-width: ' ~ outer_w ~ ';') %}{% endif %}
{% if section_bg %}{% set _ = style_parts.append('background: ' ~ section_bg ~ ';') %}{% endif %}
<section style="{{ style_parts | join(' ') }}">
```

## CSS 类名前缀

每个 Block 用专属 BEM 前缀, **不用** `module.type`:

| Block | CSS 前缀 | 示例 class |
|-------|---------|-----------|
| hero_banner | `.hero-banner-*` | `.hero-banner-slide` `.hero-banner-dot` |
| feature_grid | `.services-*` `.service-*` | `.services-grid` `.service-card` |
| highlight_card | `.hl-*` | `.hl-grid` `.hl-text` `.hl-image` |
| data_grid | `.dg-*` | `.dg-list` `.dg-card` `.dg-pager` |
| process_steps | `.ps-*` | `.ps-track` `.ps-step` |
| stat_counter | `.sc-*` | `.sc-grid` `.sc-card` `.sc-number` |
| logo_cloud | `.lc-*` | `.lc-grid` `.lc-item` `.lc-logo` |
| contact_info | `.ci-*` | `.ci-grid` `.ci-card` `.ci-icon` |
| section_title | `.st-*` | `.st-block` `.st-title` `.st-tag` |
| text_content | `.tc-*` | `.tc-block` `.tc-title` `.tc-body` |
| item_detail | `.id-*` | `.id-grid` `.id-image-zone` `.id-magnify-container` |
| product_grid | `.product-card-*` | `.product-card` `.product-card-image` |

## JS 约束

```jinja2
{# IIFE: function(){ 不加空格 #}
<script>
(function(){
  var el = document.querySelector('.xx-list');
  if (!el) return;
  // 交互逻辑...
})();
</script>

{# onclick 回调放 window 作用域 #}
<script>
function loadMoreDataGrid(btn) {
  var blockId = btn.dataset.blockId;
  // ...
}
</script>
```

**规则:**
- IIFE 包裹 `(function(){ ... })();`, `(){` 中间不加空格
- 不引入第三方库, 纯 vanilla JS
- 选择器限定在 Block 专属 class 内
- 用 `{% if %}` 控制是否输出 `<script>` 标签
- `IntersectionObserver` 用于滚动触发动画

## data-* 属性

### 属性列表

| 属性 | 用途 | 示例值 | JS 读取 |
|------|------|--------|---------|
| `data-block-id` | 模块唯一 ID | `"dg-4"` | `btn.dataset.blockId` |
| `data-page` | 当前页码(JS 可写回) | `"1"` | `parseInt(btn.dataset.page, 10)` |
| `data-per-page` | 每页条数 | `"6"` | `parseInt(btn.dataset.perPage, 10)` |
| `data-total` | 总条数 | `"6"` | `parseInt(btn.dataset.total, 10)` |
| `data-target` | 数字动画目标 | `"150"` | `parseInt(el.getAttribute('data-target'))` |
| `data-index` | 轮播索引 | `"0"` | `el.getAttribute('data-index')` |
| `data-slide` | 圆点切换目标 | `"0"` | `parseInt(dot.getAttribute('data-slide'))` |
| `data-full` | 缩略图大图 URL | `"/img/a.jpg"` | `el.getAttribute('data-full')` |
| `data-columns` | CSS 属性选择器用 | `"3"` | `el.getAttribute('data-columns')` |

### 规则

- HTML 用 kebab-case (`data-block-id`), JS `dataset` 自动转 camelCase (`dataset.blockId`)
- `getAttribute()` 返回字符串, 数字需 `parseInt()`
- 有限值 (1-4列等) 可用 CSS `[data-columns="3"]` 属性选择器
- 任意值 (颜色、尺寸) 仍走内联 style

### Jinja2 生成示例

```jinja2
{% set block_id = 'dg-' ~ module.order | default(0) %}

<div id="{{ block_id }}-list" class="dg-list" data-columns="{{ columns }}">

<button data-block-id="{{ block_id }}"
        data-page="1"
        data-per-page="{{ per_page }}"
        data-total="{{ total }}"
        onclick="loadMoreDataGrid(this)">
  加载更多
</button>
```

---

## data-* 能替代内联 style 吗？

**能替代的情况 —— 值是有限的、可穷举的：**

```css
/* columns 只有 1-4 几种可能,用属性选择器穷举 */
.dg-list[data-columns="1"] { grid-template-columns: repeat(1, 1fr); }
.dg-list[data-columns="2"] { grid-template-columns: repeat(2, 1fr); }
.dg-list[data-columns="3"] { grid-template-columns: repeat(3, 1fr); }
.dg-list[data-columns="4"] { grid-template-columns: repeat(4, 1fr); }
```

```html
<!-- 原来: -->
<div id="dg-4-list" class="dg-list" style="grid-template-columns: repeat(3, 1fr);">
<!-- 改为: -->
<div id="dg-4-list" class="dg-list" data-columns="3">
```

**不能替代的情况 —— 值是任意的、店主可以自由输入：**

| 字段 | 典型值 | 为什么不能穷举 |
|------|--------|---------------|
| `outer_width` | `1200px` `80vw` `90%` `60rem` | 单位任意，值任意 |
| `section_bg` | `#f5f7fa` `rgba(0,0,0,0.5)` `transparent` | 1670 万色 |
| `margin_top` | `0px` `2rem` `10vh` | 同上 |

**结论：** 有限值字段用 CSS class（如 `dg-list--horizontal`），任意值字段走内联 style，这是一致的做法。

---

## 关键机制: data 属性分页

`data-block-id` 是数据网格的"身份证号"——同一页面可能有两个 data_grid 模块，分别用 `dg-4` 和 `dg-5` 区分，各自独立分页。`data-page` 是唯一会被 JS **写回**的属性 (`btn.dataset.page = page + 1`)，HTML 上会动态变化: `data-page="1"` → `data-page="2"`。

---


## block结构布局及字段

`builder-module` 包装器已剥离，展示内层结构。

> `data-builder-module-index` 和 `data-builder-module-type` 由 builder 框架在包装每个模块时自动注入，Block 模板不需要处理。

---

### hero / 首屏

#### hero_banner

```html
<section class="section hero-banner" id="heroBanner"
         style="max-width: 90%; margin-left: auto; margin-right: auto;">
  <div class="container" style="height: 100%;">
    <div class="hero-banner-slides">
      <div class="hero-banner-slide active" data-index="0">
        <div class="hero-banner-media">
          <div class="hero-banner-image"
               style="background-image: url('/preview/7')"></div>
        </div>
        <div class="hero-banner-overlay"></div>
        <div class="hero-banner-content">
          <h1 class="hero-banner-title">专业展示道具定制开发</h1>
          <p class="hero-banner-subtitle">为博物馆、商场、展览馆提供智能展示解决方案</p>
          <div class="hero-banner-actions">
            <a href="/products/" class="btn btn-primary btn-lg">了解产品</a>
            <a href="/contact/" class="btn btn-secondary btn-lg">联系我们</a>
          </div>
        </div>
      </div>
      <!-- 多 slide 时有 dots + nav 按钮,此例只有 1 张 -->
    </div>
  </div>
</section>
<script>(function(){ ... })();</script>
```

> hero_banner 不使用 `section-header`。标题、副标题、按钮通过 `hero-banner-content` > `hero-banner-title` 绝对定位叠加在背景图上。也不使用标准 `section > container` 内层结构——slides 使用绝对定位，container 必须带 `height: 100%` 才能保持高度链不断裂。

**布局变体（banner_align 4 种模式）：**

| 值 | 效果 | 适用场景 |
|----|------|---------|
| 默认（空） | 全宽 Banner，左右撑满 | 通用首页 |
| `center` | 左右 auto margin 居中，宽度由 `hero_width` 决定 | 需要两侧留白的展示 |
| `left` | 居左对齐，右侧留白 | 文字左对齐的设计 |
| `right` | 居右对齐，左侧留白 | 文字右对齐的设计 |

**完整字段参考：**

| 分组 | 字段 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| 外层样式 | `hero_width` | text | `""`（全宽） | Banner 最大宽度，如 `100%` |
| 外层样式 | `hero_height` | text | `""`（77vh） | Banner 整体高度，如 `500px`、`77vh` |
| 外层样式 | `content_width` | text | `""`（全宽） | 内容区 container 的 max-width，如 `1200px` |
| 外层样式 | `banner_align` | select | `""`（全宽） | 排版：默认 / center / left / right |
| 外层样式 | `outer_width` | text | `""` | 外层宽度（留空使用全局宽度） |
| 外层样式 | `inner_width` | text | `""` | 内层内容区宽度（留空=全宽） |
| 配色 | `title_font_size` | text | `""` | 标题字号，如 `3.5rem` |
| 配色 | `title_color` | color | `""`（白色） | 标题颜色 |
| 配色 | `subtitle_font_size` | text | `""` | 副标题字号，如 `1.25rem` |
| 配色 | `subtitle_color` | color | `""`（白色） | 副标题颜色 |
| 配色 | `btn_font_size` | text | `""` | 按钮字号，如 `1rem` |
| 配色 | `btn_text_color` | color | `""`（白色） | 按钮文字色 |
| 配色 | `btn_bg` | color | `""`（主色） | 按钮背景色 |

**轮播数据结构（slides 列表）：**

每个 slide 包含以下子字段：

| 子字段 | 类型 | 说明 |
|--------|------|------|
| `type` | select(image/video) | 媒体类型：图片或视频 |
| `media` | url | 媒体地址 |
| `title` | text | 主标题 |
| `subtitle` | text | 副标题 |
| `primaryBtn` | text | 主按钮文字 |
| `primaryBtnLink` | url | 主按钮链接 |
| `secondaryBtn` | text | 副按钮文字 |
| `secondaryBtnLink` | url | 副按钮链接 |

**多轮播行为：** slides > 1 时自动渲染导航圆点（`.hero-banner-dots`）和左右箭头（`.hero-banner-nav`），JS 自动播放 8 秒间隔。每张 slide 支持独立的标题、副标题、按钮。`type=video` 时渲染 `<video>` 标签，否则渲染背景图。单 slide 时不渲染导航控件。

---

### content / 内容

#### feature_grid

```html
<section class="section"
         style="max-width: 90%; margin-left: auto; margin-right: auto;">
  <div class="container" style="max-width: none; margin: 0 auto;">
    <div class="section-header">
      <h2 class="section-title">核心服务</h2>
      <p class="section-description">让展示回归安静</p>
    </div>
    <div class="services-grid" style="grid-template-columns: repeat(3, auto); gap: 24px;">
      <div class="service-card">
        <div class="service-icon"><svg>...</svg></div>
        <div class="service-content">
          <h3 class="service-title">定制开发</h3>
          <p class="service-description">根据客户需求进行硬件与软件的定制开发...</p>
        </div>
      </div>
      <div class="service-card">
        <div class="service-icon"><svg>...</svg></div>
        <div class="service-content">
          <h3 class="service-title">品质保障</h3>
          <p class="service-description">严选元器件，每台设备出厂前经过 72 小时老化测试...</p>
        </div>
      </div>
      <div class="service-card">
        <div class="service-icon"><svg>...</svg></div>
        <div class="service-content">
          <h3 class="service-title">智能控制</h3>
          <p class="service-description">支持手机APP、PC端远程控制...</p>
        </div>
      </div>
    </div>
  </div>
</section>
```

**布局变体：**

网格列数通过 `grid-template-columns: repeat(N, auto)` 控制，N 由卡片数量动态计算（未在 meta.yaml 中暴露为独立字段）。卡片边框可通过 `card_show_border` 开关。

| 字段 | 类型 | 默认值 | 效果 |
|------|------|--------|------|
| `card_show_border` | select | `""`（显示） | 设为 `"0"` 时隐藏卡片边框 → `border: none` |

**完整字段参考：**

| 分组 | 字段 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| 内容 | `title` | text | `""` | 区块标题 |
| 内容 | `subtitle` | text | `""` | 区块副标题 |
| 外层样式 | `section_bg` | color | `""` | 外层背景色，如 `#f5f7fa` |
| 外层样式 | `outer_width` | text | `""` | 外层宽度（留空使用全局宽度） |
| 外层样式 | `margin_top` | text | `""` | 外层上外边距，如 `40px` |
| 外层样式 | `margin_right` | text | `""` | 外层右外边距 |
| 外层样式 | `margin_bottom` | text | `""` | 外层下外边距 |
| 外层样式 | `margin_left` | text | `""` | 外层左外边距 |
| 内层样式 | `inner_width` | text | `""` | 内层内容区宽度（留空=全宽） |
| 卡片样式 | `card_show_border` | select | `""`（显示） | 显示/隐藏边框 |
| 卡片样式 | `card_padding_top` | text | `""` | 卡片上内边距，如 `24px` |
| 卡片样式 | `card_padding_right` | text | `""` | 卡片右内边距 |
| 卡片样式 | `card_padding_bottom` | text | `""` | 卡片下内边距 |
| 卡片样式 | `card_padding_left` | text | `""` | 卡片左内边距 |
| 卡片样式 | `card_radius_top_left` | text | `""` | 卡片左上圆角，如 `12px` |
| 卡片样式 | `card_radius_top_right` | text | `""` | 卡片右上圆角 |
| 卡片样式 | `card_radius_bottom_right` | text | `""` | 卡片右下圆角 |
| 卡片样式 | `card_radius_bottom_left` | text | `""` | 卡片左下圆角 |

**功能卡片数据结构（features 列表）：**

每张卡片包含三个子字段：

| 子字段 | 类型 | 说明 |
|--------|------|------|
| `icon` | icon | 图标，支持 17 种内联 SVG（circuit/code/structure/sensor/interactive/audio/cpu/settings/shield/zap/wifi/globe/package/tool/bar-chart/monitor/camera），无匹配时 fallback 为默认 info 图标 |
| `title` | text | 卡片标题 |
| `desc` | textarea | 卡片描述 |

**数据源优先级：** 优先使用模块内联 `features` 列表，为空时 fallback 全局 `features` 变量。

---

#### highlight_card

```html
<section class="section"
         style="max-width: 90%; margin-left: auto; margin-right: auto">
  <div class="container" style="max-width: none; margin: 0 auto;">
    <div class="section-header">
      <h2 class="section-title">明星产品</h2>
      <p class="section-description">让展示回归安静</p>
    </div>
    <div class="hl-grid">
      <div class="hl-image"><img></div>
      <div class="hl-text" style="padding: 2rem;">
        <span class="hl-tag">明星产品</span>
        <h3 class="hl-title">静音仓 V2 — 让展示回归安静</h3>
        <p class="hl-desc">专为博物馆、美术馆等高要求场景设计。多层隔音结构...</p>
        <ul class="hl-features">
          <li>✓ 隔音等级 ≥ 35dB，满足博物馆一级展厅标准</li>
          <li>✓ 智能恒温恒湿，自动调节仓内环境参数</li>
          <li>✓ 支持远程监控与故障预警，降低运维成本</li>
        </ul>
        <div class="hl-actions">
          <a href="/products/silent-booth/" class="hl-btn hl-btn--primary">了解更多</a>
        </div>
      </div>
    </div>
  </div>
</section>
```

> 模板不含 `section-header`（标题在 `hl-text` > `hl-title` 内），示例中为展示完整性加上了 `section-header`。

**布局变体（image_position 控制图文位置）：**

| 值 | CSS 实现 | 效果 |
|----|---------|------|
| `left`（默认） | 无额外 class | 图左文右，标准双栏布局 |
| `right` | 追加 class `hl-grid--reverse` | `flex-direction: row-reverse` 翻转，文左图右 |

**完整字段参考：**

| 分组 | 字段 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| 内容 | `tag` | text | `""` | 标签文字（不为空才渲染 `.hl-tag`） |
| 内容 | `title` | text | `""` | 标题（必须不为空才渲染整个模块） |
| 内容 | `desc` | textarea | `""` | 描述文字 |
| 内容 | `image` | image | `""` | 图片（不为空才显示图片区） |
| 图文布局 | `image_position` | select | `left` | 图左文右 / 文左图右 |
| 外层样式 | `section_bg` | color | `""` | 外层背景色 |
| 外层样式 | `outer_width` | text | `""` | 外层宽度（留空使用全局宽度） |
| 外层样式 | `inner_width` | text | `""` | 内层内容区宽度（留空=全宽） |
| 外层样式 | `border_radius` | text | `""` | 整体圆角，应用于 `.hl-grid`，如 `12px` |
| 外层样式 | `margin_top` | text | `""` | 上外边距，如 `2rem` |
| 外层样式 | `margin_bottom` | text | `""` | 下外边距，如 `2rem` |
| 内层样式 | `padding_top` | text | `""` | 文本区上内边距，如 `2rem` |
| 内层样式 | `padding_bottom` | text | `""` | 文本区下内边距 |
| 内层样式 | `padding_left` | text | `""` | 文本区左内边距 |
| 内层样式 | `padding_right` | text | `""` | 文本区右内边距 |
| 配色 | `text_bg` | color | `""`（透明） | 文本区背景色 |
| 配色 | `text_color` | color | `""`（默认深色） | 文本区字体色（覆盖标题、描述、特性列表） |
| 配色 | `tag_bg` | color | `""`（主色） | 标签背景色 |
| 配色 | `tag_color` | color | `""`（白色） | 标签字体色 |
| 配色 | `btn_bg` | color | `""`（主色） | 按钮背景色 |
| 配色 | `btn_color` | color | `""`（白色） | 按钮字体色 |

**特性列表数据结构（features 列表）：**

| 子字段 | 类型 | 说明 |
|--------|------|------|
| `text` | text | 特性文本（渲染为 `<li>✓ text</li>`） |

**按钮配置：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `primaryBtn` | text | `""` | 主按钮文字（与 primaryLink 同时存在才渲染） |
| `primaryLink` | url | `""` | 主按钮链接 |
| `primaryLinkTarget` | select | `""`（当前页） | 打开方式：当前页 / `_blank` 新标签页 |
| `secondaryBtn` | text | `""` | 副按钮文字（与 secondaryLink 同时存在才渲染） |
| `secondaryLink` | url | `""` | 副按钮链接 |

**条件显示逻辑：** `title` 不为空才渲染整个模块。`image` 不为空才显示图片区。`tag` 不为空才渲染标签。`features` 不为空才渲染特性列表。主/副按钮需文字+链接同时存在才显示。

---

#### text_content

```html
<section class="section"
         style="max-width: 90%; margin-left: auto; margin-right: auto;">
  <div class="container" style="max-width: none; margin: 0 auto;">
    <div class="section-header">
      <h2 class="section-title">关于我们</h2>
      <p class="section-description">让展示回归安静</p>
    </div>
    <div class="tc-block" style="text-align: left;">
      <h2 class="tc-title">公司简介</h2>
      <div class="tc-body">
        <p>昆山德恩基电子科技有限公司成立于2014年，位于江苏省昆山市开发区...</p>
      </div>
    </div>
  </div>
</section>
```

> 模板不含 `section-header`（标题在 `tc-block` > `tc-title` 内），示例中为展示完整性加上了 `section-header`。meta.yaml 声明了 `variants: default（标准宽度）/ narrow（窄栏适合阅读）`。

**布局变体（两个维度交叉）：**

| 字段 | 类型 | 默认值 | 选项 | 说明 |
|------|------|--------|------|------|
| `text_align` | select | `left` | left / center / right | 通过 `text-align` inline style 控制对齐 |
| `columns` | select | `1` | 1（单栏）/ 2（双栏） | 双栏使用 CSS `column-count: 2; column-gap: 2rem` |

**组合效果：** `left`+`1`=标准左对齐单栏；`center`+`1`=居中单栏（适合短文案）；`left`+`2`=左对齐双栏（适合长文分栏阅读）；`center`+`2`=居中双栏。

**完整字段参考：**

| 分组 | 字段 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| 内容 | `title` | text | `""` | 标题 |
| 内容 | `body` | richtext | `""` | 正文内容（支持富文本） |
| 文字排版 | `text_align` | select | `left` | 居左 / 居中 / 居右 |
| 文字排版 | `columns` | select | `1` | 单栏 / 双栏 |
| 外层样式 | `section_bg` | color | `""`（透明） | 外层背景色 |
| 外层样式 | `outer_width` | text | `""` | 外层宽度（留空使用全局宽度） |
| 外层样式 | `inner_width` | text | `""`（全宽） | 内层内容区宽度，如 `800px` |
| 外层样式 | `margin_top` | text | `""` | 上外边距，如 `2rem` |
| 外层样式 | `margin_right` | text | `""` | 右外边距 |
| 外层样式 | `margin_bottom` | text | `""` | 下外边距 |
| 外层样式 | `margin_left` | text | `""` | 左外边距 |
| 内层样式 | `padding_top` | text | `""` | 上内边距，如 `2rem` |
| 内层样式 | `padding_right` | text | `""` | 右内边距 |
| 内层样式 | `padding_bottom` | text | `""` | 下内边距 |
| 内层样式 | `padding_left` | text | `""` | 左内边距 |
| 文字样式 | `title_size` | text | `""` | 标题字号，如 `2rem` |
| 文字样式 | `title_color` | color | `""`（默认深色） | 标题颜色 |
| 文字样式 | `body_size` | text | `""` | 正文字号，如 `1rem` |
| 文字样式 | `body_color` | color | `""`（默认灰色） | 正文颜色 |

**富文本渲染逻辑：** `body` 为 richtext 类型。内容含 `</` 或 `<br` 标签时直接 `| safe` 输出（用户已写 HTML）；否则按 `\n\n` 分段，每段包裹 `<p>` 标签。

---

#### process_steps

```html
<section class="section">
  <div class="container" style="max-width: 1200px; margin: 0 auto;">
    <div class="section-header">
      <h2 class="section-title">合作流程</h2>
      <p class="section-description">让展示回归安静</p>
    </div>
    <div class="ps-track ps-track--horizontal"
         style="grid-template-columns: repeat(4, 1fr);">
      <div class="ps-step">
        <div class="ps-marker"><span class="ps-number">1</span></div>
        <h3 class="ps-title">需求沟通</h3>
        <p class="ps-desc">了解您的展示需求与预算范围</p>
      </div>
      <div class="ps-step">
        <div class="ps-marker"><span class="ps-number">2</span></div>
        <h3 class="ps-title">方案设计</h3>
        <p class="ps-desc">量身定制展示解决方案</p>
      </div>
      <!-- ...更多步骤... -->
    </div>
  </div>
</section>
```

> meta.yaml 声明了 `variants: horizontal（横向排列）/ vertical（纵向排列）/ numbered（数字序号）`。

**布局变体（2 维度交叉 = 4 种组合）：**

| 字段 | 类型 | 默认值 | 选项 | 说明 |
|------|------|--------|------|------|
| `direction` | select | `horizontal` | horizontal / vertical | 排列方向 |
| `step_style` | select | `number` | number / icon | 步骤标记样式 |

**4 种组合的 DOM 差异：**

| 组合 | CSS class | 标记渲染 | 布局特点 |
|------|-----------|---------|---------|
| `horizontal` + `number` | `ps-track--horizontal` | `<span class="ps-number">N</span>` | 横向等宽 CSS Grid，每列 `1fr` |
| `horizontal` + `icon` | `ps-track--horizontal` | `<svg class="ps-icon">...</svg>` | 同上，标记换为 SVG 图标 |
| `vertical` + `number` | `ps-track--vertical` | `<span class="ps-number">N</span>` | 纵向堆叠，`.ps-body` 包裹标题+描述形成双栏 |
| `vertical` + `icon` | `ps-track--vertical` | `<svg class="ps-icon">...</svg>` | 同上，标记换为 SVG 图标 |

**横向模式：** 步骤之间通过 CSS Grid 等宽排列，适合步骤数 ≤6 的场景。**纵向模式：** 每个步骤独占一行，左侧标记 + 右侧 `.ps-body`（标题+描述），适合步骤数多或描述文字长的场景。

**完整字段参考：**

| 分组 | 字段 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| 内容 | `title` | text | `""` | 区块标题 |
| 内容 | `subtitle` | text | `""` | 区块副标题 |
| 内容 | `direction` | select | `horizontal` | 排列方向 |
| 内容 | `step_style` | select | `number` | 步骤样式 |
| 外层样式 | `section_bg` | color | `""` | 外层背景色 |
| 外层样式 | `outer_width` | text | `""` | 外层宽度（留空使用全局宽度） |
| 外层样式 | `inner_width` | text | `""`（全宽） | 内层内容区宽度 |
| 内层样式 | `inner_bg` | color | `""`（透明） | 内层背景色 |
| 内层样式 | `padding_top` | text | `""` | 上内边距，如 `2rem` |
| 内层样式 | `padding_right` | text | `""` | 右内边距 |
| 内层样式 | `padding_bottom` | text | `""` | 下内边距 |
| 内层样式 | `padding_left` | text | `""` | 左内边距 |
| 字体样式 | `title_font_size` | text | `""` | 步骤标题字号，如 `1.25rem` |
| 字体样式 | `title_color` | color | `""`（默认深色） | 步骤标题颜色 |
| 字体样式 | `desc_font_size` | text | `""` | 步骤描述字号，如 `0.95rem` |
| 字体样式 | `desc_color` | color | `""`（默认灰色） | 步骤描述颜色 |
| 配色 | `icon_color` | color | `""`（主色） | 图标颜色（icon 模式） |
| 配色 | `number_bg` | color | `""`（主色） | 序号背景色（number 模式） |
| 配色 | `number_font_size` | text | `""` | 序号字号，如 `1.5rem` |

**步骤数据结构（steps 列表）：**

| 子字段 | 类型 | 说明 |
|--------|------|------|
| `title` | text | 步骤标题 |
| `desc` | textarea | 步骤描述 |
| `icon` | icon | 图标（仅 step_style=icon 时使用），支持 search/edit/check/truck/settings/chat 共 6 种 SVG，无匹配 fallback 到数字序号 |

---

#### contact_info

```html
<section class="section"
         style="max-width: 90%; margin-left: auto; margin-right: auto;">
  <div class="container" style="max-width: none; margin: 0 auto;">
    <div class="section-header">
      <h2 class="section-title">联系方式</h2>
      <p class="section-description">您可以通过以下方式找到我们</p>
    </div>
    <div class="ci-grid">
      <div class="ci-card">
        <div class="ci-icon"><svg>...</svg></div>
        <div class="ci-label">电话</div>
        <a href="tel:0512-50133094" class="ci-value">0512-50133094</a>
      </div>
      <div class="ci-card">
        <div class="ci-icon"><svg>...</svg></div>
        <div class="ci-label">邮箱</div>
        <a href="mailto:info@dengtec.com" class="ci-value">info@dengtec.com</a>
      </div>
      <div class="ci-card">
        <div class="ci-icon"><svg>...</svg></div>
        <div class="ci-label">地址</div>
        <div class="ci-value">江苏省昆山市开发区新星路5号</div>
      </div>
      <!-- ...更多联系方式... -->
    </div>
  </div>
</section>
```

> meta.yaml 声明了 `variants: cards（卡片网格）/ list（纵向列表）`，但当前模板仅实现了 cards 分支——list 纵向布局为预留扩展点。

**显示控制（5 个独立开关，按需组合）：**

| 字段 | 类型 | 默认值 | 渲染标签 | 说明 |
|------|------|--------|---------|------|
| `show_phone` | select | `true` | `<a href="tel:...">` | 显示电话 |
| `show_mobile` | select | `true` | `<a href="tel:...">` | 显示手机 |
| `show_email` | select | `true` | `<a href="mailto:...">` | 显示邮箱 |
| `show_address` | select | `true` | `<div>`（纯文本） | 显示地址 |
| `show_business_hours` | select | `false` | `<div>` + 周末时额外 `<small>` | 显示营业时间 |

**5 个开关独立控制**，可任意组合（如只显示电话和邮箱、隐藏地址）。数据取自 `settings.contact` 全局设置，非模块内联数据。

**完整字段参考：**

| 分组 | 字段 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| 内容 | `title` | text | `""` | 区块标题 |
| 内容 | `subtitle` | text | `""` | 区块副标题 |
| 显示控制 | `show_phone` | select | `true` | 显示/隐藏电话 |
| 显示控制 | `show_mobile` | select | `true` | 显示/隐藏手机 |
| 显示控制 | `show_email` | select | `true` | 显示/隐藏邮箱 |
| 显示控制 | `show_address` | select | `true` | 显示/隐藏地址 |
| 显示控制 | `show_business_hours` | select | `false` | 显示/隐藏营业时间 |
| 外层样式 | `section_bg` | color | `""` | 外层背景色 |
| 外层样式 | `outer_width` | text | `""` | 外层宽度（留空使用全局宽度） |
| 外层样式 | `inner_width` | text | `""`（全宽） | 内层内容区宽度 |

**布局：** 固定卡片网格（`.ci-grid`），CSS Grid 根据可见卡片数量自适应排列（1-5 列）。每张卡片图标+标签+值垂直排列，链接类型渲染为 `<a>`，纯文本类型渲染为 `<div>`。

---

### data / 数据展示

#### data_grid

```html
<section class="section"
         style="max-width: 90%; margin-left: auto; margin-right: auto;">
  <div class="container" style="max-width: none; margin: 0 auto;">
    <div class="section-header">
      <h2 class="section-title">近期项目</h2>
    </div>
    <div id="dg-4-list" class="dg-list"
         style="grid-template-columns: repeat(3, 1fr);">
      <a href="/preview/7/zh-CN/museum-2024/" class="dg-card">
        <div class="dg-card-image">
          <div class="dg-card-placeholder">📷</div>
        </div>
        <div class="dg-card-body">
          <h3 class="dg-card-title">苏州博物馆静音展示项目</h3>
          <div class="dg-card-date">2024-08</div>
          <p class="dg-card-desc">为苏州博物馆定制 12 套静音仓展示系统</p>
          <div class="dg-card-tags">
            <span class="dg-card-tag">博物馆</span>
            <span class="dg-card-tag">静音仓</span>
          </div>
        </div>
      </a>
      <!-- ...更多卡片（共 6 张）... -->
    </div>
    <!-- 分页区形态（数据超过 per_page 时渲染）: -->
    <!--
    <div class="dg-pager dg-pager--center" style="margin-top: 1.5rem;">
      <button class="btn btn-outline-primary dg-load-more"
              data-block-id="dg-4" data-page="1"
              data-per-page="6" data-total="12"
              onclick="loadMoreDataGrid(this)">
        加载更多 <span class="dg-remaining">(6 项)</span>
      </button>
    </div>
    -->
  </div>
</section>
<script>function loadMoreDataGrid(btn){ ... }</script>
```

**布局变体：**

| 字段 | 类型 | 默认值 | 选项 | 说明 |
|------|------|--------|------|------|
| `card_layout` | select | `image_top` | image_top / image_left | 上图下文（`.dg-list`）/ 左图右文（追加 `.dg-list--horizontal`，CSS flex-direction: row） |
| `columns` | number | `3` | 任意整数 | 控制 `grid-template-columns: repeat(N, 1fr)` |

**分页模式（2 种，对应不同 JS 函数）：**

| 字段 | 类型 | 默认值 | 选项 | 说明 |
|------|------|--------|------|------|
| `show_pagination` | select | `true` | true / false | 总开关，隐藏时不渲染分页 UI |
| `pagination_style` | select | `load_more` | load_more / page_numbers | `load_more`=按钮逐批显示；`page_numbers`=页码按钮跳转 |
| `items_per_page` | number | `6` | 任意整数 | 每批/每页显示条数 |
| `pager_align` | select | `center` | center / left / right | 分页按钮对齐 |

**两种分页的 JS 行为差异：**

| 维度 | load_more | page_numbers |
|------|-----------|-------------|
| 触发函数 | `loadMoreDataGrid(btn)` | `goToDataGridPage(btn, page)` |
| 交互方式 | 点击追加显示下一批卡片 | 点击页码直接跳转到对应页 |
| DOM 操作 | 逐步移除 `.dg-card--hidden` class | 按页范围批量切换 hidden class |
| 按钮状态 | 剩余为 0 时隐藏按钮 | 当前页按钮加 `.active` class |
| 适用场景 | 内容量不确定、浏览式 | 内容量固定、查找式 |

**完整字段参考：**

| 分组 | 字段 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| 内容 | `title` | text | `""` | 区块标题 |
| 数据 | `dataset` | text | `portfolio` | 数据来源：products / portfolio / posts / 自定义数据集名 |
| 数据 | `max_items` | number | `6` | 总共展示几条（截断数量） |
| 数据 | `card_layout` | select | `image_top` | 上图下文 / 左图右文 |
| 分页 | `show_pagination` | select | `true` | 显示/隐藏分页 |
| 分页 | `pagination_style` | select | `load_more` | 加载更多 / 页码导航 |
| 分页 | `items_per_page` | number | `6` | 每页条数 |
| 分页 | `pager_align` | select | `center` | 分页对齐 |
| 外层样式 | `section_bg` | color | `""` | 外层背景色 |
| 外层样式 | `outer_width` | text | `""` | 外层宽度（留空使用全局宽度） |
| 外层样式 | `inner_width` | text | `""`（全宽） | 内层内容区宽度 |
| 外层样式 | `margin_top` | text | `""` | 上外边距 |
| 外层样式 | `margin_right` | text | `""` | 右外边距 |
| 外层样式 | `margin_bottom` | text | `""` | 下外边距 |
| 外层样式 | `margin_left` | text | `""` | 左外边距 |

**卡片内容按数据集类型差异渲染：**

| 数据集 | 图片区 | 正文区 | 特有字段 |
|--------|--------|--------|---------|
| `products` | cover/image + category 标签 | title/name + summary/description | 分类角标 `.dg-card-category` |
| `posts` | cover/image | title + date + excerpt（截断60字） | 日期 `.dg-card-date` |
| `portfolio` | cover/image | title + description/summary/excerpt（截断80字） | — |
| 自定义 | cover/image | title/name + 任意描述字段 | 按实际数据字段 fallback |

**分类过滤：** `category` 字段不为空时，从 `all_datasets[dataset_key].items` 中筛选 `item.category == category` 的条目。数据源优先级：`all_datasets[dataset_key]`（结构化数据集）> 全局变量（`products`/`portfolio`/`posts`）。

---

#### product_grid

```html
<section class="section">
  <div class="container" style="max-width: 1200px; margin: 0 auto;">
    <div class="section-header">
      <h2 class="section-title">产品中心</h2>
    </div>
    <div class="grid grid-3" style="grid-template-columns: repeat(3, 1fr);">
      <a href="/preview/7/zh-CN/products/silent-booth/" class="product-card">
        <div class="product-card-image">
          <div class="product-card-placeholder">📦</div>
          <span class="product-card-category">静音仓</span>
        </div>
        <div class="product-card-body">
          <h3 class="product-card-title">静音仓 V2</h3>
          <p class="product-card-desc">多层隔音结构，满足博物馆一级展厅标准</p>
        </div>
      </a>
      <!-- ...更多产品卡片... -->
    </div>
    <div class="text-center" style="margin-top: 2rem;">
      <a href="/preview/7/zh-CN/products/" class="btn btn-primary">查看全部</a>
    </div>
  </div>
</section>
```

**与 data_grid 的区别：** product_grid 是 data_grid 的简化版——无分页、无 card_layout 选项、无分类过滤、无配色字段。底部固定渲染"查看全部"按钮链向产品列表页。适合产品数量少（≤12个）、不需要翻页的场景。

**完整字段参考：**

| 分组 | 字段 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| 内容 | `title` | text | `""` | 区块标题 |
| 数据 | `dataset` | select | `products` | 数据来源（当前仅 products） |
| 数据 | `max_items` | number | `6` | 最大显示数量 |
| 外层样式 | `section_bg` | color | `""` | 外层背景色 |
| 外层样式 | `outer_width` | text | `""` | 外层宽度（留空使用全局宽度） |
| 外层样式 | `inner_width` | text | `""`（全宽） | 内层内容区宽度 |

**网格列数：** 通过 `grid grid-N` class 控制，N 由 `max_items` 动态计算（≤3 时单列，4-6 时 2-3 列），不在 meta.yaml 中暴露为独立字段。

---

#### item_detail

```html
<section class="section">
  <div class="container" style="max-width: 1200px; margin: 0 auto;">
    <div class="id-grid">
      <div class="id-image-zone">
        <div class="id-magnify-container" id="id-5678-magnify">
          <img class="id-main-image" id="id-5678-main-img"
               src="/media/product/silent-booth.jpg" alt="静音仓 V2"
               style="border-radius: 12px;">
          <div class="id-magnify-glass" id="id-5678-glass"
               style="display:none;"></div>
        </div>
        <div class="id-thumb-list">
          <div class="id-thumb-item active"
               data-full="/media/product/silent-booth.jpg"
               onclick="switchItemDetailImage('id-5678', this, '...')"
               style="background-image: url('...');"></div>
          <!-- ...更多缩略图... -->
        </div>
      </div>
      <div class="id-info-zone">
        <h1 class="id-title">静音仓 V2</h1>
        <p class="id-desc">专为博物馆、美术馆等高要求场景设计...</p>
        <div class="id-tags">
          <span class="id-tag">静音仓</span>
          <span class="id-tag">博物馆</span>
        </div>
        <div class="id-specs-section">
          <h3 class="id-specs-title">规格参数</h3>
          <table class="id-specs-table">
            <tr><td class="id-spec-name">隔音等级</td>
                <td class="id-spec-value">≥ 35dB</td></tr>
            <tr><td class="id-spec-name">尺寸</td>
                <td class="id-spec-value">200×200×220cm</td></tr>
          </table>
        </div>
      </div>
    </div>
  </div>
</section>
<script>(function(){ /* 放大镜 + 缩略图切换 */ })();</script>
```

> item_detail 不使用 `section-header`。标题在右侧信息区 `id-info-zone` > `id-title` 内，与描述、标签、规格表组成产品详情布局。固定双栏：左 `.id-image-zone` + 右 `.id-info-zone`，无双栏交换选项。

**图片布局变体（由图片数量自动决定）：**

| 图片数量 | 渲染行为 |
|---------|---------|
| 0 张 | 图片区不渲染 |
| 1 张 | 仅主图（`id-main-image`），无缩略图列表、无放大镜 |
| ≥2 张 | 主图 + 缩略图列表（`.id-thumb-list`）+ 鼠标悬浮放大镜 |

**放大镜机制：** 主图容器 `id-magnify-container` 绑定 `mousemove` 事件，实时计算鼠标相对图片的位置百分比，在 `id-magnify-glass`（180×180px 镜片）中显示 2.5 倍放大的对应区域。`mouseleave` 时隐藏镜片。`data-full` 存储每张缩略图的大图 URL，点击缩略图切换主图。

**完整字段参考：**

| 分组 | 字段 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| 内容 | `title` | text | `""` | 标题 |
| 内容 | `desc` | textarea | `""` | 描述文字 |
| 内容 | `tags` | text | `""` | 逗号分隔的标签，渲染为 `.id-tag` span |
| 外层样式 | `section_bg` | color | `""` | 外层背景色 |
| 外层样式 | `outer_width` | text | `""` | 外层宽度（留空使用全局宽度） |
| 外层样式 | `inner_width` | text | `""`（全宽） | 内层内容区宽度 |
| 内层样式 | `inner_bg` | color | `""`（透明） | 内层背景色 |
| 内层样式 | `padding_top` | text | `""` | 内层上间距，如 `2rem` |
| 内层样式 | `padding_right` | text | `""` | 内层右间距 |
| 内层样式 | `padding_bottom` | text | `""` | 内层下间距 |
| 内层样式 | `padding_left` | text | `""` | 内层左间距 |
| 图片样式 | `img_border_radius` | text | `""`（默认 `var(--radius-md)`） | 图片圆角，如 `12px` |
| 图片样式 | `img_height` | text | `""`（自适应） | 图片高度（`object-fit: cover`），如 `400px` |
| 配色 | `text_bg` | color | `""`（透明） | 文本区背景色 |
| 配色 | `text_color` | color | `""`（默认深色） | 文本区字体色 |
| 配色 | `tag_bg` | color | `""`（主色） | 标签背景色 |
| 配色 | `tag_color` | color | `""`（白色） | 标签字体色 |

**图片列表数据结构（images 列表）：**

| 子字段 | 类型 | 说明 |
|--------|------|------|
| `url` | image | 图片 URL |

**规格参数数据结构（specs 列表）：**

| 子字段 | 类型 | 说明 |
|--------|------|------|
| `name` | text | 参数名（左列） |
| `value` | text | 参数值（右列） |

规格表不为空时渲染 `<table class="id-specs-table">`，每行两列（参数名 + 参数值）。

---

### social / 社交证明

#### stat_counter

```html
<section class="section"
         style="max-width: 90%; margin-left: auto; margin-right: auto;">
  <div class="container" style="max-width: none; margin: 0 auto;">
    <div class="section-header">
      <h2 class="section-title">公司实力</h2>
      <p class="section-description">用数字说话</p>
    </div>
    <div class="sc-grid" style="grid-template-columns: repeat(4, 1fr);">
      <div class="sc-card">
        <div class="sc-icon"><svg>...</svg></div>
        <div class="sc-number" data-target="10">0</div>
        <span class="sc-suffix">年+</span>
        <div class="sc-label">行业经验</div>
      </div>
      <!-- ...更多统计卡片 (200 个+ / 50 项+ / 5000㎡)... -->
    </div>
  </div>
</section>
<script>
(function(){
  /* IntersectionObserver + requestAnimationFrame 数字滚动动画
     读取 data-target 获取目标值,从 0 缓动到目标 */
})();
</script>
```

> meta.yaml 声明了 `variants: grid_3（三列）/ grid_4（四列）/ grid_6（六列）`。数字动画完全由 JS 驱动：`IntersectionObserver` 检测可见性，`data-target` 存储目标值，`requestAnimationFrame` 做缓动动画。CSS 不参与动画逻辑。

**布局变体（columns 控制列数）：**

| 值 | 效果 | 适用场景 |
|----|------|---------|
| `3` | 三列（`grid-template-columns: repeat(3, 1fr)`） | 统计项少（3 项），每项更宽 |
| `4`（默认） | 四列 | 标准 4 项统计 |
| `6` | 六列 | 统计项多（6 项），紧凑排列 |

**完整字段参考：**

| 分组 | 字段 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| 内容 | `title` | text | `""` | 区块标题 |
| 内容 | `subtitle` | text | `""` | 区块副标题 |
| 内容 | `columns` | select | `4` | 每行列数：3 / 4 / 6 |
| 外层样式 | `section_bg` | color | `""` | 外层背景色 |
| 外层样式 | `outer_width` | text | `""` | 外层宽度（留空使用全局宽度） |
| 外层样式 | `inner_width` | text | `""`（全宽） | 内层内容区宽度 |

**统计项数据结构（stats 列表）：**

每项包含 4 个子字段：

| 子字段 | 类型 | 说明 |
|--------|------|------|
| `number` | number | 目标数字（存储在 `data-target` 属性中，JS 从 0 缓动到此值） |
| `suffix` | text | 后缀文字（如 `+`、`%`、`万`、`㎡`），渲染在数字旁边 |
| `label` | text | 标签文字（如"行业经验"），渲染在数字下方 |
| `icon` | icon | 图标，支持 users / briefcase / check / star / clock 共 5 种 SVG，无匹配 fallback 圆形感叹号 |

**动画触发条件：** `IntersectionObserver` 监测 `.sc-grid` 进入视口（threshold 0.3），触发后动画只执行一次（`dataset.counted` 标记防重复）。

---

#### logo_cloud

```html
<section class="section">
  <div class="container" style="max-width: 1200px; margin: 0 auto;">
    <div class="section-header">
      <h2 class="section-title">合作伙伴</h2>
      <p class="section-description">他们信任我们</p>
    </div>
    <div class="lc-grid" style="grid-template-columns: repeat(4, 1fr);">
      <div class="lc-item" title="客户 A">
        <img src="/media/logos/client-a.png" alt="客户 A"
             class="lc-logo lc-logo--grayscale" loading="lazy"
             style="filter: grayscale(100%) opacity(0.6);">
      </div>
      <!-- ...更多 Logo（每行 4 个）... -->
    </div>
  </div>
</section>
```

> meta.yaml 声明了 `variants: grid_4（四列）/ grid_5（五列）/ grid_6（六列）`。

**布局变体：**

| 字段 | 类型 | 默认值 | 选项 | 说明 |
|------|------|--------|------|------|
| `columns` | select | `4` | 4 / 5 / 6 | 控制 `grid-template-columns: repeat(N, 1fr)` |
| `grayscale` | select | `true` | true / false | 灰度滤镜开关 |

**grayscale 行为细节：**
- `true`（默认）：图片加 class `lc-logo--grayscale` + inline `filter: grayscale(100%) opacity(0.6)`，hover 时通过 CSS `:hover` 规则恢复彩色（`filter: none; opacity: 1`）
- `false`：不加 class，图片保持原色

**完整字段参考：**

| 分组 | 字段 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| 内容 | `title` | text | `""` | 区块标题 |
| 内容 | `subtitle` | text | `""` | 区块副标题 |
| 内容 | `columns` | select | `4` | 每行列数：4 / 5 / 6 |
| 内容 | `grayscale` | select | `true` | 灰度滤镜：开启 / 关闭 |
| 外层样式 | `section_bg` | color | `""` | 外层背景色 |
| 外层样式 | `outer_width` | text | `""` | 外层宽度（留空使用全局宽度） |
| 外层样式 | `inner_width` | text | `""`（全宽） | 内层内容区宽度 |
| 内层样式 | `inner_bg` | color | `""`（透明） | 内层背景色 |
| 内层样式 | `padding_top` | text | `""` | 上内边距，如 `2rem` |
| 内层样式 | `padding_right` | text | `""` | 右内边距 |
| 内层样式 | `padding_bottom` | text | `""` | 下内边距 |
| 内层样式 | `padding_left` | text | `""` | 左内边距 |
| 卡片样式 | `logo_bg` | color | `""`（透明） | Logo 卡片背景色，如 `#f8fafc` |
| 卡片样式 | `logo_border` | text | `""`（无边框） | Logo 卡片边框，如 `1px solid #e5e7eb` |
| 卡片样式 | `logo_border_color` | color | `""` | Logo 卡片边框色，如 `#e5e7eb` |
| 卡片样式 | `logo_radius` | text | `""` | Logo 卡片圆角，如 `8px` |
| 卡片样式 | `logo_width` | text | `""`（自适应） | Logo 图片宽度，如 `120px` |
| 卡片样式 | `logo_height` | text | `""`（自适应） | Logo 图片高度，如 `60px` |

**Logo 列表数据结构（logos 列表）：**

| 子字段 | 类型 | 说明 |
|--------|------|------|
| `image` | image | Logo 图片 |
| `name` | text | 品牌名称（用作 `alt` 和 `title` 属性） |
| `link` | url | 链接（可选，不为空时渲染 `<a target="_blank">`，为空时渲染纯展示 `<div>`） |

---

### layout / 布局

#### section_title

```html
<section class="section" style="max-width: 90%; margin-left: auto; margin-right: auto; background: #ffffff;">
  <div class="container" style="max-width: none; margin: 0 auto;">
    <div class="st-block" style="text-align: center;">
      <span class="st-tag"
            style="background: #067a7a; color: #ffffff;">11</span>
      <h2 class="st-title" style="color: #1e293b;">22</h2>
      <p class="st-desc" style="color: #64748b;">33</p>
    </div>
  </div>
</section>
```

> section_title 不使用 `section-header`——它本身就是标题模块。`st-block` > `st-tag` + `st-title` + `st-desc` 组成独立的标题/分隔区，通常放在其他内容 Block 之前作为段落分隔。

**布局变体（text_align 控制对齐）：**

| 值 | 效果 | 适用场景 |
|----|------|---------|
| `center`（默认） | 内容居中，`text-align: center` | 通用段落标题 |
| `left` | 内容居左，`text-align: left` | 左对齐的内容区标题 |
| `right` | 内容居右，`text-align: right` | 特殊设计需求 |

**完整字段参考：**

| 分组 | 字段 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| 内容 | `tag` | text | `""` | 标签文字（不为空才渲染 `.st-tag`） |
| 内容 | `title` | text | `""` | 标题 |
| 内容 | `desc` | textarea | `""` | 描述文字 |
| 文字排版 | `text_align` | select | `center` | 居左 / 居中 / 居右 |
| 外层样式 | `section_bg` | color | `""`（透明） | 外层背景色 |
| 外层样式 | `outer_width` | text | `""` | 外层宽度（留空使用全局宽度） |
| 外层样式 | `margin_top` | text | `""` | 上外边距，如 `2rem` |
| 外层样式 | `margin_right` | text | `""` | 右外边距 |
| 外层样式 | `margin_bottom` | text | `""` | 下外边距 |
| 外层样式 | `margin_left` | text | `""` | 左外边距 |
| 内层样式 | `inner_width` | text | `""`（全宽） | 内层宽度 |
| 内层样式 | `padding_top` | text | `""` | 上内边距，如 `4rem` |
| 内层样式 | `padding_right` | text | `""` | 右内边距 |
| 内层样式 | `padding_bottom` | text | `""` | 下内边距 |
| 内层样式 | `padding_left` | text | `""` | 左内边距 |
| 字体样式 | `title_size` | text | `""` | 标题字号，如 `2.5rem` |
| 字体样式 | `title_color` | color | `""`（默认深色） | 标题颜色 |
| 字体样式 | `desc_size` | text | `""` | 描述字号，如 `1rem` |
| 字体样式 | `desc_color` | color | `""`（默认灰色） | 描述颜色 |
| 字体样式 | `tag_bg` | color | `""`（主色） | 标签背景色 |
| 字体样式 | `tag_color` | color | `""`（白色） | 标签字体色 |
| 按钮 | `btn_text` | text | `""` | 按钮文字（与 `btn_url` 同时存在才渲染） |
| 按钮 | `btn_url` | url | `""` | 按钮链接 |
| 按钮 | `btn_target` | select | `""`（当前页） | 打开方式：当前页 / `_blank` |
| 按钮 | `btn_bg` | color | `""`（主色） | 按钮背景色 |
| 按钮 | `btn_color` | color | `""`（白色） | 按钮文字色 |

**条件显示逻辑：** title / tag / desc / btn 至少一项不为空才渲染整个模块。所有颜色和字号通过 inline style 注入，不留空则使用 CSS 默认值。

---

### data-* 用法分析（以 data_grid 为例）

**① JS 交互用的 data-*：**

```html
<button data-block-id="dg-4"
        data-page="1"
        data-per-page="6"
        data-total="12"
        onclick="loadMoreDataGrid(this)">
```

| 属性 | 存储内容 | JS 如何消费 | 是否影响样式 |
|------|---------|------------|-------------|
| `data-block-id` | 模块唯一标识 `"dg-4"` | `btn.dataset.blockId` → `getElementById('dg-4-list')` 定位 DOM | 否 |
| `data-page` | 当前页码，**唯一会被 JS 写回** | `parseInt(btn.dataset.page, 10)` → 计算下一批显示范围 | 否 |
| `data-per-page` | 每页条数 `"6"` | `parseInt(btn.dataset.perPage, 10)` → 每批显示几张 | 否 |
| `data-total` | 总条数 `"12"` | 判断 `remaining <= 0` → 隐藏或更新按钮文字 | 否 |

**② 那为什么同一个页面还有 inline style？**

```html
<!-- 这三处 style 无法用 data-* 替代 -->
<section style="max-width: 90%; ...">  <!-- 店主填的任意值 -->
<div style="max-width: none; ...">     <!-- 同上 -->
<div style="grid-template-columns: repeat(3, 1fr);">  <!-- columns 可用 data-* -->
```

**CSS 引擎不认识 data-*，它只认 style 属性和样式表规则。** 这三处 `style` 的共同点：值是店主在后台自由填写的（值域无限）、必须在 HTML 解析完成即刻生效（不能等 JS）。其中 `grid-template-columns` 因为 N 只有 1-4，可以用 `data-columns="3"` + CSS 属性选择器替代（见上方 data-* 能替代章节），但 `max-width`、`background` 等任意值不行。

**总结：data-* 和 inline style 在各管各的——**

| 维度 | data-* | inline style |
|------|--------|-------------|
| 服务对象 | JS（运行时逻辑） | 浏览器渲染引擎 |
| 生效时机 | 用户交互后（点击、滚动） | HTML 解析完成即刻 |
| 值的特点 | 有限枚举（页码、条数、ID） | 任意 CSS 值（颜色、尺寸、单位） |
| 能否互相替代 | 不能替代 style | 不能替代 data-* |

---

## 网站头部（Header）渲染输出

网站头部由 `_base.html` 中的 Jinja2 模板控制，通过 `header_variant` 设置切换 4 种排版。

头部通用结构为 `header.site-header` > `.header-main` > `.container`，其中 `.container` 用 flexbox 横向排列 Logo、导航、操作区。

### 头部全局配置

| 设置项 | 字段路径 | 说明 |
|--------|---------|------|
| 排版方式 | `settings.header.variant` | 4 选 1，默认 `logo_left_menu_right` |
| 内容区宽度 | `settings.header.inner_width` | 控制 `.header-main .container` 的 max-width |
| 内边距 | `settings.header.padding_top/right/bottom/left` | 容器内边距 |
| 语言切换器 | `settings.header.language_switcher.enabled` | 开关，默认 true |
| 语言切换器样式 | `settings.header.language_switcher.style` | 3 选 1，默认 `vertical_dropdown` |

> 头部宽度和内边距通过内联 `<style>` 注入 `.site-header .header-main .container` 选择器，不在 HTML 上写内联 style。

### JS 行为（所有变体共用）

| 功能 | 触发方式 | 说明 |
|------|---------|------|
| 滚动阴影 | `window scroll` 事件 | `scrollY > 50` 时给 header 加 `.scrolled` class |
| 移动端菜单 | `onclick="toggleMobileMenu()"` | 切换 `#headerNav` 的 `.mobile-open` |
| 下拉菜单 | `onclick="toggleMenuDropdown(event, this)"` | 切换 `.nav-dropdown` 的 `.open`，同级互斥 |
| 语言下拉 | `onclick="toggleLangDropdown(event)"` | 切换 `#langDropdownMenu` 的 display |
| 当前页高亮 | 页面加载后自动执行 | 匹配 URL path 给对应 `nav-link` 加 `.active` |
| 外部点击关闭 | `document click` 事件 | 关闭所有展开的下拉菜单和语言菜单 |

---

### 变体 1: logo_left_menu_right（默认 / 经典导航栏）

**适用场景：** 最通用的导航布局，Logo 居左、导航居中、语言切换器居右。移动端折叠为汉堡菜单。

**排版特点：**
- Logo + 文字组合在左侧
- 导航链接水平排列在中间，间距 `2rem`
- 语言切换器在右侧
- 汉堡菜单在移动端（≤768px）才显示

```html
<header class="site-header builder-region header-variant--logo-left-menu-right"
        id="siteHeader" data-builder-region="header">
  <div class="header-main">
    <div class="container">
      <a href="/preview/7/zh-CN/" class="logo">
        <div class="logo-text-group">
          <span class="logo-text">昆山德恩基电子科技有限公司</span>
          <span class="logo-text-cn">德恩基电子科技</span>
        </div>
      </a>
      <nav class="header-nav" id="headerNav">
        <a href="/preview/7/zh-CN/" class="nav-link">首页</a>
        <div class="nav-dropdown">
          <div class="nav-dropdown-parent">
            <a href="/preview/7/zh-CN/products/" class="nav-link nav-dropdown-link">产品</a>
            <button class="nav-dropdown-arrow" type="button"
                    onclick="toggleMenuDropdown(event, this)"
                    aria-label="展开子菜单" aria-expanded="false">
              <span class="dropdown-chevron">▼</span>
            </button>
          </div>
          <div class="nav-dropdown-menu nav-dropdown-menu--horizontal">
            <a href="/preview/7/zh-CN/products/silent-booth/"
               class="nav-dropdown-item">静音仓</a>
            <a href="/preview/7/zh-CN/products/props-display/"
               class="nav-dropdown-item">产品展示</a>
            <a href="/preview/7/zh-CN/products/dry-ice-machine/"
               class="nav-dropdown-item">干冰机</a>
          </div>
        </div>
        <a href="/preview/7/zh-CN/portfolio/" class="nav-link">近期项目</a>
        <a href="/preview/7/zh-CN/about/" class="nav-link">关于我们</a>
        <a href="/preview/7/zh-CN/contact/" class="nav-link">联系</a>
      </nav>
      <div class="header-actions">
        <div class="language-switcher-dropdown" id="langSwitcher">
          <button class="dropdown-toggle"
                  onclick="toggleLangDropdown(event)"
                  aria-haspopup="true" aria-expanded="false">
            <span class="current-language">
              <span class="lang-name">简体中文</span>
              <span class="dropdown-arrow">▼</span>
            </span>
          </button>
          <div class="dropdown-menu" id="langDropdownMenu" style="display:none;">
            <ul class="language-list">
              <li class="language-item active">
                <a href="/preview/7/zh-CN/" class="lang-name"
                   style="color:inherit;text-decoration:none;">简体中文</a>
                <span class="checkmark">✓</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
      <button class="menu-toggle" id="menuToggle" aria-label="菜单"
              onclick="toggleMobileMenu()">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</header>
```

---

### 变体 2: logo_center_menu_below（居中 Logo + 下方菜单）

**适用场景：** 品牌感强的网站，Logo 居中突出，导航在下方形成独立一行。

**排版特点：**
- `.header-main--centered` 容器改为纵向 flex 布局（`flex-direction: column`）
- 顶部行：语言切换器右对齐
- Logo 居中（`logo--centered`：`margin: 0 auto`）
- 导航居中（`header-nav--centered`），上方有 `border-top` 分隔线

```html
<header class="site-header builder-region header-variant--logo-center-menu-below"
        id="siteHeader" data-builder-region="header">
  <div class="header-main header-main--centered">
    <div class="container">
      <div class="header-top-row">
        <div class="header-actions">
          <div class="language-switcher-dropdown" id="langSwitcher">
            <button class="dropdown-toggle"
                    onclick="toggleLangDropdown(event)"
                    aria-haspopup="true" aria-expanded="false">
              <span class="current-language">
                <span class="lang-name">简体中文</span>
                <span class="dropdown-arrow">▼</span>
              </span>
            </button>
            <div class="dropdown-menu" id="langDropdownMenu" style="display:none;">
              <ul class="language-list">
                <li class="language-item active">
                  <a href="/zh-CN/" class="lang-name"
                     style="color:inherit;text-decoration:none;">简体中文</a>
                  <span class="checkmark">✓</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      <a href="/zh-CN/" class="logo logo--centered">
        <div class="logo-text-group">
          <span class="logo-text">昆山德恩基电子科技有限公司</span>
          <span class="logo-text-cn">德恩基电子科技</span>
        </div>
      </a>
      <nav class="header-nav header-nav--centered" id="headerNav">
        <a href="/zh-CN/" class="nav-link active">首页</a>
        <div class="nav-dropdown">
          <div class="nav-dropdown-parent">
            <a href="/zh-CN/products/" class="nav-link nav-dropdown-link">产品</a>
            <button class="nav-dropdown-arrow" type="button"
                    onclick="toggleMenuDropdown(event, this)"
                    aria-label="展开子菜单" aria-expanded="false">
              <span class="dropdown-chevron">▼</span>
            </button>
          </div>
          <div class="nav-dropdown-menu nav-dropdown-menu--vertical">
            <a href="/zh-CN/products/silent-booth/"
               class="nav-dropdown-item">静音仓</a>
            <a href="/zh-CN/products/props-display/"
               class="nav-dropdown-item">产品展示</a>
          </div>
        </div>
        <a href="/zh-CN/about/" class="nav-link">关于我们</a>
        <a href="/zh-CN/contact/" class="nav-link">联系</a>
      </nav>
      <button class="menu-toggle" id="menuToggle" aria-label="菜单"
              onclick="toggleMobileMenu()">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</header>
```

---

### 变体 3: minimal_hamburger（极简汉堡菜单）

**适用场景：** 单页网站、落地页、移动优先设计。导航默认隐藏，汉堡按钮始终显示（包括桌面端）。

**排版特点：**
- 汉堡按钮始终可见（`.menu-toggle--always-visible` = `display: flex !important`）
- 导航区（`.header-nav--overlay`）默认隐藏，展开后以绝对定位覆盖层出现
- 语言切换器和汉堡按钮并列在 `header-actions` 中

```html
<header class="site-header builder-region header-variant--minimal-hamburger"
        id="siteHeader" data-builder-region="header">
  <div class="header-main">
    <div class="container">
      <a href="/zh-CN/" class="logo">
        <span class="logo-text" style="font-size:var(--font-size-lg);">
          昆山德恩基电子科技有限公司
        </span>
      </a>
      <div class="header-actions">
        <div class="language-switcher-dropdown" id="langSwitcher">
          <button class="dropdown-toggle"
                  onclick="toggleLangDropdown(event)"
                  aria-haspopup="true" aria-expanded="false">
            <span class="current-language">
              <span class="lang-name">简体中文</span>
              <span class="dropdown-arrow">▼</span>
            </span>
          </button>
          <div class="dropdown-menu" id="langDropdownMenu" style="display:none;">
            <ul class="language-list">
              <li class="language-item active">
                <a href="/zh-CN/" class="lang-name"
                   style="color:inherit;text-decoration:none;">简体中文</a>
                <span class="checkmark">✓</span>
              </li>
            </ul>
          </div>
        </div>
        <button class="menu-toggle menu-toggle--always-visible"
                id="menuToggle" aria-label="菜单"
                onclick="toggleMobileMenu()">
          <span></span><span></span><span></span>
        </button>
      </div>
      <nav class="header-nav header-nav--overlay" id="headerNav">
        <a href="/zh-CN/" class="nav-link">首页</a>
        <div class="nav-dropdown">
          <div class="nav-dropdown-parent">
            <a href="/zh-CN/products/" class="nav-link nav-dropdown-link">产品</a>
            <button class="nav-dropdown-arrow" type="button"
                    onclick="toggleMenuDropdown(event, this)"
                    aria-label="展开子菜单" aria-expanded="false">
              <span class="dropdown-chevron">▼</span>
            </button>
          </div>
          <div class="nav-dropdown-menu nav-dropdown-menu--vertical">
            <a href="/zh-CN/products/silent-booth/"
               class="nav-dropdown-item">静音仓</a>
            <a href="/zh-CN/products/props-display/"
               class="nav-dropdown-item">产品展示</a>
          </div>
        </div>
        <a href="/zh-CN/about/" class="nav-link">关于我们</a>
        <a href="/zh-CN/contact/" class="nav-link">联系</a>
      </nav>
    </div>
  </div>
</header>
```

---

### 变体 4: top_bar_social（顶部信息栏 + 社交图标）

**适用场景：** 商务/企业官网，在导航上方展示联系方式、社交链接。

**排版特点：**
- **双层结构**：顶部 utility 栏（联系方式 + 社交图标 + 语言切换器）+ 下方标准导航栏
- 顶部栏背景色 `var(--color-bg-secondary)`（浅灰）
- 左侧（`.utility-left`）：电话、邮箱链接
- 右侧（`.utility-right`）：GitHub / Twitter / LinkedIn 图标 + 语言切换器

```html
<header class="site-header builder-region header-variant--top-bar-social"
        id="siteHeader" data-builder-region="header">
  <div class="header-utility">
    <div class="container">
      <div class="utility-left">
        <a href="tel:0512-50133094" class="utility-link">0512-50133094</a>
        <a href="mailto:info@dengtec.com" class="utility-link">info@dengtec.com</a>
      </div>
      <div class="utility-right">
        <a href="https://github.com/dengtec" target="_blank" rel="noopener"
           class="utility-social-link" aria-label="GitHub">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59..."/>
          </svg>
        </a>
        <div class="language-switcher-dropdown" id="langSwitcher">
          <button class="dropdown-toggle"
                  onclick="toggleLangDropdown(event)"
                  aria-haspopup="true" aria-expanded="false">
            <span class="current-language">
              <span class="lang-name">简体中文</span>
              <span class="dropdown-arrow">▼</span>
            </span>
          </button>
          <div class="dropdown-menu" id="langDropdownMenu" style="display:none;">
            <ul class="language-list">
              <li class="language-item active">
                <a href="/zh-CN/" class="lang-name"
                   style="color:inherit;text-decoration:none;">简体中文</a>
                <span class="checkmark">✓</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="header-main">
    <div class="container">
      <a href="/zh-CN/" class="logo">
        <div class="logo-text-group">
          <span class="logo-text">昆山德恩基电子科技有限公司</span>
          <span class="logo-text-cn">德恩基电子科技</span>
        </div>
      </a>
      <nav class="header-nav" id="headerNav">
        <a href="/zh-CN/" class="nav-link active">首页</a>
        <a href="/zh-CN/products/" class="nav-link">产品</a>
        <a href="/zh-CN/about/" class="nav-link">关于我们</a>
        <a href="/zh-CN/contact/" class="nav-link">联系</a>
      </nav>
      <button class="menu-toggle" id="menuToggle" aria-label="菜单"
              onclick="toggleMobileMenu()">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</header>
```

### 四种变体对比

| 特性 | logo_left_menu_right | logo_center_menu_below | minimal_hamburger | top_bar_social |
|------|---------------------|----------------------|-------------------|----------------|
| Logo 位置 | 左侧 | 居中 | 左侧（仅文字） | 左侧 |
| 导航位置 | 水平居中 | Logo 下方居中 | 隐藏（overlay） | 水平居中 |
| 汉堡菜单显示 | 仅移动端 | 仅移动端 | **始终显示** | 仅移动端 |
| 顶部栏 | 无 | 无 | 无 | **有（联系方式+社交）** |
| 导航上方分隔线 | 无 | **有** (`border-top`) | 无 | 无 |
| 适合 | 通用 | 品牌展示 | 单页/落地页 | 企业/B2B |

---

### 菜单下拉排版（nav-dropdown-menu）

每个带子菜单的导航项通过 `item.dropdown_style` 控制下拉排版。桌面端 hover 展开，移动端点击展开。

#### vertical（默认 / 垂直列表）

```html
<div class="nav-dropdown-menu nav-dropdown-menu--vertical">
  <a href="..." class="nav-dropdown-item">静音仓</a>
  <a href="..." class="nav-dropdown-item">产品展示</a>
  <a href="..." class="nav-dropdown-item">干冰机</a>
</div>
```

CSS: `display: flex; flex-direction: column; gap: 2px`，每项 `width: 100%`。

#### horizontal（水平排列）

```html
<div class="nav-dropdown-menu nav-dropdown-menu--horizontal">
  <a href="..." class="nav-dropdown-item">静音仓</a>
  <a href="..." class="nav-dropdown-item">产品展示</a>
  <a href="..." class="nav-dropdown-item">干冰机</a>
</div>
```

CSS: `display: flex; flex-direction: row; gap: 4px; padding: 6px 8px`。

#### grid（三列网格）

```html
<div class="nav-dropdown-menu nav-dropdown-menu--grid">
  <a href="..." class="nav-dropdown-item">静音仓</a>
  <a href="..." class="nav-dropdown-item">产品展示</a>
  <a href="..." class="nav-dropdown-item">干冰机</a>
  <!-- ...更多子项... -->
</div>
```

CSS: `display: grid; grid-template-columns: repeat(3, 1fr); max-width: 560px`。

#### cards（三列卡片）

```html
<div class="nav-dropdown-menu nav-dropdown-menu--cards">
  <a href="..." class="nav-dropdown-item">静音仓</a>
  <a href="..." class="nav-dropdown-item">产品展示</a>
  <a href="..." class="nav-dropdown-item">干冰机</a>
</div>
```

CSS: 每项有 `border: 1px solid var(--color-border); border-radius: 8px; background: #fafbfc; padding: 12px 14px`。

#### 四种排版对比

| 排版 | class | CSS 布局 | 列数 | 适用 |
|------|-------|---------|------|------|
| vertical | `--vertical` | flex column | 1 | 子项少，纵向简洁 |
| horizontal | `--horizontal` | flex row | 1 行 | 子项少，横向铺开 |
| grid | `--grid` | CSS grid | 3 列 | 子项多，紧凑排列 |
| cards | `--cards` | CSS grid | 3 列 | 子项多，需视觉区分 |

---

### 语言切换器样式

语言切换器通过 `_lang_switcher.html` 局部模板渲染，被所有 4 种 header 变体共用。通过 `settings.header.language_switcher.style` 切换 3 种样式。

#### vertical_dropdown（默认 / 下拉菜单）

```html
<div class="language-switcher-dropdown" id="langSwitcher">
  <button class="dropdown-toggle"
          onclick="toggleLangDropdown(event)"
          aria-haspopup="true" aria-expanded="false">
    <span class="current-language">
      <span class="lang-name">简体中文</span>
      <span class="dropdown-arrow">▼</span>
    </span>
  </button>
  <div class="dropdown-menu" id="langDropdownMenu" style="display:none;">
    <ul class="language-list">
      <li class="language-item active">
        <a href="/zh-CN/" class="lang-name"
           style="color:inherit;text-decoration:none;">简体中文</a>
        <span class="checkmark">✓</span>
      </li>
      <li class="language-item">
        <a href="/en/" class="lang-name"
           style="color:inherit;text-decoration:none;">English</a>
      </li>
    </ul>
  </div>
</div>
```

#### inline_row（水平按钮组）

```html
<div class="language-switcher language-switcher--inline" id="langSwitcher">
  <a href="/zh-CN/" class="lang-switcher-link active">简体中文</a>
  <a href="/en/" class="lang-switcher-link">English</a>
  <a href="/zh-TW/" class="lang-switcher-link">繁體中文</a>
</div>
```

#### flag_icon（旗帜 + 代码）

```html
<div class="language-switcher language-switcher--flag" id="langSwitcher">
  <a href="/zh-CN/" class="lang-switcher-link active" title="简体中文">
    🇨🇳 CN
  </a>
  <a href="/en/" class="lang-switcher-link" title="English">
    🇺🇸 EN
  </a>
</div>
```

### 移动端适配

所有 4 种变体在 ≤768px 时共享相同行为：
- `.header-nav` 隐藏，展开后为 `position: absolute; top: 100%` 全宽下拉面板
- `.menu-toggle` 显示为三横线汉堡图标（激活时变形为 X）
- 下拉菜单通过点击展开，所有排版降级为 block 纵排
- 语言切换器保持在 `header-actions` 内

---

## 网站底部（Footer）渲染输出

网站底部由 `_base.html` 中 `<footer>` 区块控制，通过 `footer_variant` 设置切换 2 种排版。

### 底部全局配置

| 设置项 | 字段路径 | 说明 |
|--------|---------|------|
| 排版方式 | `settings.footer.variant` | 2 选 1，默认 `columns` |
| 栏目内容 | `settings.footer.columns` | 仅 `columns` 变体使用，每项含 `{title, type, links}` |
| 版权文字 | `settings.footer.copyright` | 默认取 `settings.company.name` |
| ICP 备案号 | `settings.footer.icp` | 显示在版权行下方 |

### 变体 1: minimal（极简版权行）

**适用场景：** 内容极简的网站，不需要栏目导航。

```html
<footer class="site-footer builder-region" data-builder-region="footer">
  <div class="container">
    <div class="footer-bottom">
      <p>© 2026 昆山德恩基电子科技有限公司</p>
      <p>苏ICP备14020096号-1</p>
    </div>
  </div>
</footer>
```

### 变体 2: columns（多栏目导航）

**适用场景：** 大多数企业网站，用多栏网格展示导航链接、联系方式等。

**排版特点：**
- `.footer-grid` 按栏目数设置 `grid-template-columns: repeat(N, 1fr)`
- 栏目内容分 **menu 类型**（`ul > li > a` 链接列表）和 **text 类型**（`p` 文本段落）
- 响应式：≤900px 时 2 列，≤640px 时 1 列

```html
<footer class="site-footer builder-region" data-builder-region="footer">
  <div class="container">
    <div class="footer-grid" style="grid-template-columns: repeat(4, 1fr);">
      <div class="footer-col">
        <h4>产品中心</h4>
        <ul>
          <li><a href="/zh-CN/products/silent-booth/">静音仓</a></li>
          <li><a href="/zh-CN/products/led-display/">LED 显示屏</a></li>
          <li><a href="/zh-CN/products/dry-ice-machine/">干冰机</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>快捷导航</h4>
        <ul>
          <li><a href="/zh-CN/about/">关于我们</a></li>
          <li><a href="/zh-CN/portfolio/">近期项目</a></li>
          <li><a href="/zh-CN/contact/">联系我们</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>联系方式</h4>
        <div class="footer-col-text">
          <p>电话：0512-50133094</p>
          <p>邮箱：info@dengtec.com</p>
        </div>
      </div>
      <div class="footer-col">
        <h4>公司地址</h4>
        <div class="footer-col-text">
          <p>江苏省昆山市开发区新星路5号</p>
        </div>
      </div>
    </div>
    <div class="footer-bottom">
      <p>© 2026 昆山德恩基电子科技有限公司</p>
      <p>苏ICP备14020096号-1</p>
    </div>
  </div>
</footer>
```

### 两种变体对比

| 特性 | minimal | columns |
|------|---------|---------|
| 栏目网格 | 无 | 多列 grid（按栏目数） |
| 导航链接 | 无 | 支持（menu 类型） |
| 文本内容 | 无 | 支持（text 类型） |
| 响应式断点 | 无 | 900px → 2 列，640px → 1 列 |
| 适合 | 极简短页 | 企业官网 |

---


## 完整源码: data_grid Jinja2 模板

```jinja2
{# === 1. 数据准备 === #}
{# 数据网格 — 通用数据列表模块 #}
{% if module.data %}
{% set md = module.data if module.data else {} %}
{% set dataset_key = md.get('dataset', 'portfolio') %}

{# 从 all_datasets 或全局变量中取数据集 #}
{% if all_datasets is defined and dataset_key in all_datasets %}
  {% set ds_data = all_datasets[dataset_key] %}
  {% if ds_data is mapping and 'items' in ds_data %}
    {% set items = ds_data['items'] %}
  {% elif ds_data is iterable and ds_data is not string %}
    {% set items = ds_data %}
  {% else %}
    {% set items = [] %}
  {% endif %}
{% else %}
  {% set items = products if dataset_key == 'products' else portfolio if dataset_key == 'portfolio' else posts if dataset_key == 'posts' else [] %}
{% endif %}

{% if items %}
{# === 2. 分类过滤 === #}
{% set filter_category = md.get('category', '') %}
{% set filtered_items = items %}
{% if filter_category %}
  {% set _tmp = [] %}
  {% for _it in items %}
    {% if _it.category | default('') | string == filter_category | string %}
      {% set _ = _tmp.append(_it) %}
    {% endif %}
  {% endfor %}
  {% set filtered_items = _tmp %}
{% endif %}

{% if filtered_items %}
{# === 3. 配置提取 === #}
{% set per_page = md.get('items_per_page', 6) | int %}
{% set card_layout = md.get('card_layout', 'image_top') %}
{% set section_bg = md.get('section_bg', '') %}
{% set outer_w = md.get('outer_width', '') or settings.get('layout', {}).get('global_width', '') %}
{% set inner_w = md.get('inner_width', '') %}
{% set columns = md.get('columns') | int or 3 %}
{% set show_pagination = md.get('show_pagination', true) not in (false, 'false', 'False', '') %}
{% set pagination_style = md.get('pagination_style', 'load_more') %}
{% set display_items = filtered_items %}
{% set total = display_items | length %}
{% set is_products = dataset_key == 'products' %}
{% set is_posts = dataset_key == 'posts' %}
{% set is_portfolio = dataset_key == 'portfolio' %}
{% set block_id = 'dg-' ~ module.order | default(0) %}
{#                ───┬───     ──────┬──────
        data 属性来源:       module.order 由后端自动分配,
        'dg-' 前缀确保      表示模块在页面中的序号,
        页面内唯一           两个 data_grid 同页时分别得 dg-4 和 dg-5  #}

{# === 4. 外层 Section === #}
{% set mg_top = md.get('margin_top', '') %}{% set mg_right = md.get('margin_right', '') %}{% set mg_bottom = md.get('margin_bottom', '') %}{% set mg_left = md.get('margin_left', '') %}{% set has_margin = mg_top or mg_right or mg_bottom or mg_left %}
<section class="section"
         {% if section_bg or has_margin or outer_w %} style="
           {% if outer_w %}max-width: {{ outer_w }}; {% endif %}
           {% if section_bg %}background: {{ section_bg }};{% endif %}
           {% if mg_top %}margin-top: {{ mg_top }};{% endif %}
           {% if mg_right %}margin-right: {{ mg_right }};{% endif %}
           {% if mg_bottom %}margin-bottom: {{ mg_bottom }};{% endif %}
           {% if mg_left %}margin-left: {{ mg_left }};{% endif %}
         "{% endif %}>
  <div class="container" style="max-width: {{ inner_w or 'none' }}; ">

    {# === 5. 标题 === #}
    {% if md.title %}
    <div class="section-header">
      <h2 class="section-title">{{ md.title }}</h2>
    </div>
    {% endif %}

    {# === 6. 卡片列表 === #}
    <div id="{{ block_id }}-list" class="dg-list {% if card_layout == 'image_left' %}dg-list--horizontal{% endif %}"
         style="grid-template-columns: repeat({{ columns }}, 1fr);">
      {% for item in display_items %}
      <a href="{{ base_url }}/{{ lang }}{{ current_path }}{{ item.slug }}/"
         class="dg-card {% if loop.index0 >= per_page %}dg-card--hidden{% endif %}{% if card_layout == 'image_left' %} dg-card--horizontal{% endif %}">
        {# 初始超过 per_page 的卡片加 hidden class,JS 分页时逐批显示 #}
        <div class="dg-card-image"{% if item.cover or item.image %} style="background-image: url('{{ item.cover | default(item.image) }}')"{% endif %}>
          {% if not (item.cover or item.image) %}<div class="dg-card-placeholder">{{ '📦' if is_products else '📷' }}</div>{% endif %}
          {% if is_products and item.category %}<span class="dg-card-category">{{ item.category }}</span>{% endif %}
        </div>
        <div class="dg-card-body">
          <h3 class="dg-card-title">{{ item.title | default(item.name) }}</h3>
          {% if item.date %}<div class="dg-card-date">{{ item.date }}</div>{% endif %}
          {% if is_products and (item.summary or item.description) %}<p class="dg-card-desc">{{ item.summary | default(item.description | truncate(80)) }}</p>{% endif %}
          {% if is_posts and item.excerpt %}<p class="dg-card-desc">{{ item.excerpt | truncate(60) }}</p>{% endif %}
          {% if not is_products and not is_posts %}{% set desc = item.description or item.summary or item.excerpt or '' %}{% if desc %}<p class="dg-card-desc">{{ desc | truncate(80) }}</p>{% endif %}{% endif %}
          {% if item.tags %}
          <div class="dg-card-tags">
            {% for tag in (item.tags if item.tags is iterable and item.tags is not string else item.tags.split(','))[:5] %}
            <span class="dg-card-tag">{{ tag | trim }}</span>
            {% endfor %}
          </div>
          {% endif %}
        </div>
      </a>
      {% endfor %}
    </div>

    {# === 7. 分页区域 === #}
    {% if show_pagination and total > per_page %}
    {% set total_pages = (total / per_page) | round(0, 'ceil') | int %}
    <div id="{{ block_id }}-pager" class="dg-pager dg-pager--{{ md.get('pager_align', 'center') }}" style="margin-top: 1.5rem;">
      {% if pagination_style == 'page_numbers' %}
      <div class="dg-page-numbers">
        {% for p in range(1, total_pages + 1) %}
        <button class="dg-page-btn {% if p == 1 %}active{% endif %}"
                data-block-id="{{ block_id }}"
                data-page="{{ p }}"
                data-per-page="{{ per_page }}"
                onclick="goToDataGridPage(this, {{ p }})">{{ p }}</button>
        {% endfor %}
      </div>
      {% else %}
      <button class="btn btn-outline-primary dg-load-more"
              data-block-id="{{ block_id }}"
              data-page="1"
              data-per-page="{{ per_page }}"
              data-total="{{ total }}"
              onclick="loadMoreDataGrid(this)">
        {{ t.actions.loadMore | default('加载更多') }}
        <span class="dg-remaining">({{ total - per_page }} {{ t.products.itemsUnit | default('项') }})</span>
      </button>
      {% endif %}
    </div>
    {% endif %}

  </div>
</section>
{% endif %}
{% endif %}
{% endif %}

<script>
function loadMoreDataGrid(btn) {
  var blockId = btn.dataset.blockId;
  var page = parseInt(btn.dataset.page, 10) || 1;
  var perPage = parseInt(btn.dataset.perPage, 10) || 6;
  var total = parseInt(btn.dataset.total, 10) || 0;
  var list = document.getElementById(blockId + '-list');
  if (!list) return;
  var hiddenCards = list.querySelectorAll('.dg-card--hidden');
  var nextCount = Math.min(perPage, hiddenCards.length);
  for (var i = 0; i < nextCount; i++) {
    hiddenCards[i].classList.remove('dg-card--hidden');
  }
  var remaining = hiddenCards.length - nextCount;
  if (remaining <= 0) {
    btn.style.display = 'none';
  } else {
    btn.dataset.page = page + 1;
    var span = btn.querySelector('.dg-remaining');
    var unit = '{{ t.products.itemsUnit | default('项') }}';
    if (span) span.textContent = '(' + remaining + ' ' + unit + ')';
  }
}

function goToDataGridPage(btn, targetPage) {
  var blockId = btn.dataset.blockId;
  var perPage = parseInt(btn.dataset.perPage, 10) || 6;
  var list = document.getElementById(blockId + '-list');
  if (!list) return;
  var cards = list.querySelectorAll('.dg-card');
  var startIdx = (targetPage - 1) * perPage;
  var endIdx = startIdx + perPage;
  cards.forEach(function(card, i) {
    if (i >= startIdx && i < endIdx) {
      card.classList.remove('dg-card--hidden');
    } else {
      card.classList.add('dg-card--hidden');
    }
  });
  var pager = document.getElementById(blockId + '-pager');
  if (pager) {
    pager.querySelectorAll('.dg-page-btn').forEach(function(b, i) {
      b.classList.toggle('active', i + 1 === targetPage);
    });
  }
}
</script>
```

---

## 待开发 Block （ 19 个）

> 状态: 待开发 | 更新时间: 2026-05-21

### P0 — 通用高频（7 个）

| # | Block | 中文名 | 核心字段 |
|---|-------|--------|---------|
| 1 | `cta_banner` | 行动号召 | 标题、描述、1-2 个按钮、背景图/色、文字排版 |
| 2 | `faq_accordion` | 常见问题 | Q&A 列表（问题+答案富文本）、展开模式（单/多） |
| 3 | `contact_form` | 联系表单 | 姓名、邮箱、电话、留言、提交按钮文案、接收邮箱， 地图定位、地图服务选择（高德/Google）、坐标/地址
| 4 | `image_gallery` | 图片画廊 | 图片列表（可批量上传）、布局（瀑布流/网格/幻灯片）、灯箱 |
| 5 | `video_embed` | 视频嵌入 | 视频链接（YouTube/Bilibili/腾讯视频）、封面图、宽高比 |
| 6 | `testimonial_carousel` | 客户评价 | 头像、姓名、职位/公司、评星(1-5)、评语、轮播/网格切换 |
| 7 | `team_grid` | 团队介绍 | 头像、姓名、职位、简介、社交链接（微信/邮箱/领英） |

### P1 — 行业差异化（7 个）

| # | Block | 中文名 | 核心字段 |
|---|-------|--------|---------|
| 8 | `timeline` | 发展历程 | 年份/日期、标题、描述、图标/图片、左右交替/单侧布局 |
| 9 | `pricing_table` | 价格表 | 套餐名、价格、币种/周期、特性列表（勾/叉）、推荐标记、按钮 |
| 11 | `certificate_grid` | 资质证书 | 证书图片、名称、发证机构、点击放大查看 |
| 12 | `file_download` | 文件下载 | 文件名、文件上传、图标、文件大小显示 |
| 13 | `menu_list` | 菜品菜单 | 菜品名、价格、描述、图片、分类标签、推荐标记 |
| 14 | `related_items` | 相关推荐 | 数据来源、显示条数、推荐依据（同分类/手动指定） |

### P2 — 功能增强（6 个）

| # | Block | 中文名 | 核心字段 |
|---|-------|--------|---------|
| 15 | `announcement_bar` | 公告通知条 | 文字、链接、可关闭开关、背景色、页面顶部/底部定位 |
| 16 | `tabs` | 标签页 | 标签项列表（标签名+内嵌模块）、默认激活标签 |
| 17 | `comparison_table` | 对比表格 | 对比项列表（产品名/图/链接）、行定义（参数名+各产品值）、高亮列 |
| 18 | `countdown_timer` | 倒计时 | 截止时间、数字样式、过期后行为（隐藏/显示文字） |
| 19 | `image_comparison` | 前后对比 | 前图、后图、滑块方向（左右/上下） |

### 不单独做 Block 的

| 场景 | 原因 |
|------|------|
| `social_links` 社交链接 | 已通过站点设置 `settings.social` + Header `top_bar_social` 变体 + `panel_social.html` 管理面板覆盖 |
| `breadcrumb` 面包屑 | 属模板全局组件，应自动生成 |
| `share_buttons` 分享按钮 | B2B 小企业站需求极低 |

### 新增 Block 参考现有模式

每个新增 Block 遵循与现有 Block 相同的结构：
- `site_templates/dengtec/blocks/<name>/meta.yaml` — 字段定义
- `site_templates/dengtec/blocks/<name>/template.html` — Jinja2 渲染模板
- `site_templates/dengtec/blocks/<name>/variants/` — 可选布局变体
- `app/templates/dashboard/_block_icons.html` — SVG 图标
- `app/static/js/admin_modules.js` — 后台表单构建器（自动读 meta.yaml）
- `app/core/routes.py` `_parse_modules_form()` — 表单解析（复杂列表结构需手动添加）
