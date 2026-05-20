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
{# section_bg 为空时加 section-bg class 兜底 #}
<section class="section{% if not section_bg %} section-bg{% endif %}"
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

## 浏览器渲染输出 (data_grid 示例 B)

```html
<div class="builder-module" data-builder-module-index="3" data-builder-module-type="data_grid">

<section class="section section-bg" style="max-width: 90%; margin-left: auto; margin-right: auto;">
  <div class="container" style="max-width: none; margin: 0 auto;">
    <div class="section-header">
      <h2 class="section-title">近期项目</h2>
    </div>

    <!-- 列表容器: id 用于 JS 定位 -->
    <!-- block_id 'dg-4' = 'dg-' ~ module.order(值为4) -->
    <div id="dg-4-list" class="dg-list " style="grid-template-columns: repeat(3, 1fr);">

      <a href="/preview/7/zh-CN/museum-2024/" class="dg-card ">
        <div class="dg-card-image"><div class="dg-card-placeholder">📷</div></div>
        <div class="dg-card-body">
          <h3 class="dg-card-title">苏州博物馆静音展示项目</h3>
          <div class="dg-card-date">2024-08</div>
          <p class="dg-card-desc">为苏州博物馆定制 12 套静音仓展示系统</p>
          <div class="dg-card-tags">
            <span class="dg-card-tag">博物馆</span>
            <span class="dg-card-tag">静音仓</span>
            <span class="dg-card-tag">定制</span>
          </div>
        </div>
      </a>
      <!-- ...更多卡片... -->
    </div>

    <!-- 分页按钮(数据少时未渲染,此处为形态展示): -->
    <!--
    <div class="dg-pager dg-pager--center" style="margin-top: 1.5rem;">
      <button class="btn btn-outline-primary dg-load-more"
              data-block-id="dg-4"
              data-page="1"
              data-per-page="6"
              data-total="6"
              onclick="loadMoreDataGrid(this)">
        加载更多 <span class="dg-remaining">(0 项)</span>
      </button>
    </div>
    -->
  </div>
</section>
</div>
```

> `data-builder-module-index` 和 `data-builder-module-type` 由 builder 框架自动注入，Block 模板不需要处理。

### 示例 B 中 data-* 的用法分析

这个 data_grid 渲染结果中出现了两类属性，职责完全不同：

**① 框架注入的属性（Block 模板不处理）：**

```html
<div class="builder-module" data-builder-module-index="3" data-builder-module-type="data_grid">
```

这两个属性由 builder 框架在包装每个模块时自动注入，用于后台编辑器的模块识别和拖拽排序。Block 模板不需要知道它们的存在。

**② JS 交互用的 data-*（分页按钮，示例中被注释但逻辑完整）：**

```html
<button data-block-id="dg-4"
        data-page="1"
        data-per-page="6"
        data-total="6"
        onclick="loadMoreDataGrid(this)">
```

这四个 data-* 的职责纯粹是 **JS 运行时状态传递**：

| 属性 | 存储内容 | JS 如何消费 | 是否影响样式 |
|------|---------|------------|-------------|
| `data-block-id` | 模块唯一标识 `"dg-4"` | `btn.dataset.blockId` → 拼接 `getElementById('dg-4-list')` 定位 DOM | 否 |
| `data-page` | 当前页码 `"1"` | `parseInt(btn.dataset.page, 10)` → 计算下一批要显示的卡片 | 否 |
| `data-per-page` | 每页条数 `"6"` | `parseInt(btn.dataset.perPage, 10)` → `Math.min(perPage, hiddenCards.length)` | 否 |
| `data-total` | 总条数 `"6"` | 判断是否还有更多 → 隐藏按钮或更新剩余计数 | 否 |

JS 读这些属性，做的是 DOM 操作（`classList.remove('dg-card--hidden')`、`style.display = 'none'`），然后 **写回** `btn.dataset.page = page + 1` 更新状态。整个过程不涉及任何 CSS 取值或样式计算。

**③ 那为什么同一个页面还有 inline style？**

```html
<!-- 这三处 style 无法用 data-* 替代 -->
<section style="max-width: 90%; margin-left: auto; margin-right: auto;">   <!-- 店主填的任意值 -->
<div style="max-width: none; margin: 0 auto;">                             <!-- 店主填的任意值 -->
<div style="grid-template-columns: repeat(3, 1fr);">                      <!-- 店主选的列数 -->
```

根本原因：**CSS 引擎不认识 data-*，它只认 style 属性和样式表规则。**

这三处 `style` 的共同特点：
- 值是**店主在后台自由填写的**（`90%`、`none`、`repeat(3, 1fr)` 都可能变化）
- 必须**在浏览器渲染 HTML 的那一刻**就生效，不能等 JS 执行
- 值域**无限**——`max-width` 可以是 `90%`、`1200px`、`80vw`、`60rem` 等任意 CSS 值

如果试图用 data-* 承载这些值：

```html
<!-- 这样做不 work：CSS 不认识 data-max-width -->
<div data-max-width="90%">

<!-- 必须在 CSS 里提前为每个可能的值写规则，但值域无限，写不完 -->
div[data-max-width="90%"] { max-width: 90%; }
div[data-max-width="1200px"] { max-width: 1200px; }
div[data-max-width="80vw"] { max-width: 80vw; }
<!-- ...写不完... -->
```

`grid-template-columns: repeat(N, 1fr)` 相对可控（N 通常是 1-4），所以 data_grid 其实**可以**把这行改成 `data-columns="3"` + CSS 属性选择器（见上方 [data-* 能替代内联 style 吗？](#data--能替代内联-style-吗) 章节）。但 `max-width`、`background` 等自由值字段不行。

**总结：data-* 和 inline style 在示例 B 中各管各的——**

| 维度 | data-* | inline style |
|------|--------|-------------|
| 服务对象 | JS（运行时逻辑） | 浏览器渲染引擎 |
| 生效时机 | 用户交互后（点击、滚动） | HTML 解析完成即刻 |
| 值的特点 | 有限枚举（页码、条数、ID） | 任意 CSS 值（颜色、尺寸、单位） |
| 能否互相替代 | 不能替代 style（CSS 引擎不读 data-*） | 不能替代 data-*（JS 状态不应编码进 style） |

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
<section class="section{% if not section_bg %} section-bg{% endif %}"
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
