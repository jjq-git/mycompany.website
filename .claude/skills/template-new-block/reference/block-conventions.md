# Block 模板的结构、数据绑定、样式控制的约定速查

## 数据/样式写到各层的方法

`builder-module` 包装器已剥离，展示内层结构。

> `data-builder-module-index` 和 `data-builder-module-type` 由 builder 框架在包装每个模块时自动注入，Block 模板不需要处理。

```html
<!-- 样式走 inline style，有值才输出，空值不写让 CSS 变量兜底 -->
<section class="section" style="">                                           <!-- ① 外层 -->
  <div class="container" style="">                                           <!-- ② 内层 -->
    <!-- 标题区：数据走 {{ }} 文本插值，整个区块用 {% if %} 控制存亡 -->
    {% if md.title %}
    <div class="section-header">                                             <!-- ③ 标题区 -->
      <h2 class="section-title">{{ md.title }}</h2>                             <!-- 标题 -->
      <p class="section-description">{{ md.subtitle }}</p>                      <!-- 副标题/描述 -->
    </div>
    {% endif %}
    <!-- 内容区(以列表为例)：列表数据用 {% for %} 遍历，子字段走 {{ }} -->
    <div class="hl-grid">                                                    <!-- ④ 自定义内容区 -->
      {% for item in md.features %}
      <div class="hl-card">
        <img src="{{ item.icon }}" alt="">
        <h3>{{ item.title }}</h3>
      </div>
      {% endfor %}
    </div>
  </div>
</section>
```

### .section

整个块的最外层, 可以设置下面几个样式, 左右是要铺满的.

1. margin:
2. paddong:

### .container

作用是什么?


| 层级 | 数据怎么来 | 样式怎么来 |
|------|-----------|-----------|
| ① 外层 `<section>` | 无文本数据 | `{% if %}` 包裹 `style="..."`，字段有值才输出，空值不写 |
| ② 内层 `<div class="container">` | 无文本数据 | `style="max-width: {{ inner_w or 'none' }};"` |
| ③ 标题区 `.section-header` | `{{ md.title }}` / `{{ md.subtitle }}` 插值 | 字号颜色可暴露字段走 inline style，为空时 CSS 变量兜底 |
| ④ 内容区 | `{% for %}` 遍历列表 + `{{ }}` 插子字段 | 布局（grid 列数等）走 inline style；卡片样式走专属 CSS class |

### ① 外层 `<section class="section">` —— 模块的外层


**作用：** 模块的最外层包装器，负责模块与模块之间的**间距**和**背景**。

| 承载的样式字段 | 说明 |
|---------------|------|
| `section_bg` | 外层背景色，如 `#f5f7fa`。为空时自动追加 `.section-bg` class 兜底 |
| `outer_width` | 外层最大宽度，如 `1200px`。居中策略：`margin-left: auto; margin-right: auto` |
| `margin_top / margin_right / margin_bottom / margin_left` | 外层外边距，控制模块与上下模块的间距 |

**规则：**
- 所有 Block 模板都以 `<section class="section">` 开头、`</section>` 结尾
- `outer_width` 是"限定模块整体宽度"，不是"限定内容宽度"——它管的是这堵墙能铺多宽
- `section_bg` 为空时依赖 `.section-bg` class（CSS 中有全局默认背景），不为空时走 inline style 覆盖

### ② 内层 `<div class="container">` —— 模块内容区

**作用：** 在模块内部限定**内容的展示宽度**，与外层解耦。

| 承载的样式字段 | 说明 |
|---------------|------|
| `inner_width` | 内容区最大宽度，如 `800px`。为空时 `max-width: none`（全宽） |

**规则：**
- `inner_width` 和外层 `outer_width` 是独立的：外层可以铺满全屏，内层只占 800px 居中
- 固定写法：`style="max-width: {{ inner_w or 'none' }}; margin: 0 auto;"`
- 这个 div 不做背景色——背景色在外层 section 上

**常见组合：**
| outer_width | inner_width | 效果 |
|-------------|-------------|------|
| 90%（全局宽度） | none（全宽） | 内容撑满模块，两侧有统一页边距 |
| 90% | 800px | 内容窄栏居中（适合阅读型文本） |
| 空（全屏） | 1200px | 背景全屏铺开，内容居中限定宽度 |

### ③ 标题区 `<div class="section-header">` —— 模块的标题

**作用：** 统一的区块标题区域，包含主标题和副标题。

| 子元素 | 标签 | 承载字段 | 说明 |
|--------|------|---------|------|
| 主标题 | `h2.section-title` | `title` | 模块大标题，如"核心服务"、"产品中心" |
| 副标题 | `p.section-description` | `subtitle` 或 `desc` | 模块描述文字，小号灰色放在标题下方 |

**规则：**
- 标题/副标题为空时**整个 `section-header` 不渲染**（`{% if md.title %}` 包裹）
- class 名固定为 `section-header`、`section-title`、`section-description`，所有 Block 共用，不随 BEM 前缀变化
- 标题区的字体样式（字号、颜色）可按需暴露为模块字段（如 `title_size`、`title_color`、`desc_size`、`desc_color`），**字段为空时走全局 CSS 变量兜底**——inline style 不输出，浏览器自然使用 CSS 默认值

**不使用 `section-header` 的例外 Block：**

| Block | 为什么不走 section-header | 标题放哪里 |
|-------|--------------------------|-----------|
| `hero_banner` | 标题需要叠加在背景图上，绝对定位 | `hero-banner-content` > `hero-banner-title` |
| `highlight_card` | 标题是图文卡片的一部分 | `hl-text` > `hl-title` |
| `section_title` | 它自己就是标题模块，不需要再套一层 | `st-block` > `st-title` |
| `item_detail` | 标题在右侧详情区 | `id-info-zone` > `id-title` |

### ④ 自定义内容区 —— 模块的自定义内容

**作用：** 每个 Block 的核心展示区域，结构完全由 Block 类型决定。

**模板怎么知道该用 `{{ }}` 还是 `{% for %}` 还是 `{% if %}`？**
——看 `meta.yaml` 里字段的 `type`：

| meta.yaml 中的 type | 模板渲染方式 | 示例 |
|---------------------|-------------|------|
| `text` / `textarea` / `richtext` | **`{{ }}` 文本插值** | `<h2>{{ md.title }}</h2>` → 单值 |
| `color` / `number` / `url` | **`{{ }}` 写入 style 或属性** | `style="color: {{ md.title_color }};"` → 单值 |
| `list` | **`{% for %}` 遍历** | `{% for item in md.features %}` → 数组，子字段用 `item.xxx` |
| `select` | **`{% if %}` 判断值** | `{% if direction == 'horizontal' %}class{% endif %}` → 枚举切换 |
| `image` | **`{% if %}` + `{{ }}`** | `{% if md.image %}<img src="{{ md.image }}">{% endif %}` → 可选 |

Block 的所有可变属性（颜色、尺寸、间距、排列、显隐、列数等）通过 **4 种机制** 落到 DOM 上：

**机制一：inline style（有值才输出，空值不写 → CSS 变量兜底）**

适用于值无限、不可穷举的字段。写法：`{% if field %}style="prop: {{ field }};"{% endif %}`

| 控制维度 | 字段示例 | CSS 属性 | 写法 |
|---------|---------|---------|------|
| 颜色 | `title_color`, `subtitle_color`, `desc_color`, `body_color`, `text_color`, `section_bg`, `inner_bg`, `btn_bg`, `btn_color`, `tag_bg`, `tag_color`, `text_bg`, `icon_color`, `number_bg`, `logo_bg` | `color`, `background`, `background-color` | `style="color: {{ title_color }};"` |
| 字号 | `title_size`, `subtitle_size`, `desc_size`, `body_size`, `title_font_size`, `desc_font_size`, `number_font_size`, `btn_font_size` | `font-size` | `style="font-size: {{ title_size }};"` |
| 宽度 | `outer_width`, `inner_width`, `hero_width`, `content_width`, `logo_width` | `max-width`, `width` | `style="max-width: {{ outer_w }};"` |
| 高度 | `hero_height`, `img_height`, `logo_height` | `height` | `style="height: {{ hero_height }};"` |
| 外边距 | `margin_top`, `margin_right`, `margin_bottom`, `margin_left` | `margin-*` | `style="margin-top: {{ margin_top }};"` |
| 内边距 | `padding_top`, `padding_right`, `padding_bottom`, `padding_left` | `padding-*` | `style="padding-top: {{ padding_top }};"` |
| 圆角 | `border_radius`, `img_border_radius`, `logo_radius`, `card_radius_*` | `border-radius` | `style="border-radius: {{ logo_radius }};"` — 支持四角独立 |
| 边框 | `border_width`, `border_style`, `border_color` | `border` | `style="border: {{ border_width }} {{ border_style }} {{ border_color }};"` |
| 阴影 | `box_shadow`, `text_shadow` | `box-shadow`, `text-shadow` | `style="box-shadow: 0 4px 12px rgba(0,0,0,0.1);"` |
| 透明度 | `opacity` | `opacity` | `style="opacity: 0.8;"` |
| 滤镜 | `grayscale` | `filter` | `style="filter: grayscale(100%) opacity(0.6);"` — Logo 墙灰度常用 |
| 背景图 | `bg_image`, `item.cover` | `background-image` | `style="background-image: url('{{ bg_image }}');"` |
| 背景图定位 | `bg_position`, `bg_size` | `background-position`, `background-size` | `style="background-size: cover; background-position: center;"` |
| 对齐 | `text_align` | `text-align` | `style="text-align: {{ md.text_align or 'left' }};"` |
| Grid 列数 | `columns`（任意整数） | `grid-template-columns` | `style="grid-template-columns: repeat({{ cols }}, 1fr);"` |
| 网格间距 | `gap` | `gap` | `style="gap: {{ gap }};"` |
| 图片适配 | `img_height`, `img_fit` | `object-fit`, `height` | `style="height: {{ img_height }}; object-fit: cover;"` |
| 过渡动画 | `transition` | `transition` | `style="transition: all 0.3s ease;"` — hover 变色/浮起 |
| 变换 | `transform` | `transform` | `style="transform: scale(1.05);"` — hover 缩放/位移 |

多值拼接用 list 收集：

```jinja2
{% set section_styles = [] %}
{% if section_bg %}{% set _ = section_styles.append('background: ' ~ section_bg) %}{% endif %}
{% if outer_w %}{% set _ = section_styles.append('max-width: ' ~ outer_w ~ '; margin-left: auto; margin-right: auto') %}{% endif %}
<section style="{{ section_styles | join('; ') }}">
```

**关键原则：字段为空时不输出 style 属性，浏览器自然走 CSS 变量/默认值。** 店主不填 ≠ 显示异常。


---

**机制二：CSS class 切换（有限枚举 → modifier class，样式写死在 CSS 里）**

适用于值 ≤4 种、可穷举的字段。

| 控制维度 | 适用场景 | 字段 | 值 → 效果 | 写法 |
|---------|---------|------|-----------|------|
| 左右排版 | 图文模块 | `image_position` | `left` → 图左文右；`right` → 图右文左 | `{% if img_pos == 'right' %}xx-grid--reverse{% endif %}` |
| 上图下文/左图右文 | 卡片列表 | `card_layout` | `image_top` → 图上文下；`image_left` → 左图右文 | `{% if card_layout == 'image_left' %}xx-list--horizontal{% endif %}` |
| 横向/纵向 | 步骤/列表 | `direction` | `horizontal` → 横向 Grid；`vertical` → 纵向堆叠 | `xx-track--{{ direction }}` |
| 对齐方式 | 标题/文本/分页 | `text_align`, `pager_align` | `center` / `left` / `right` | `xx-pager--{{ md.get('pager_align', 'center') }}` |
| 分页样式 | 数据列表 | `pagination_style` | `load_more` → 加载更多按钮；`page_numbers` → 页码导航 | `{% if pagination_style == 'page_numbers' %}<div class="xx-page-numbers">{% else %}<button>{% endif %}` |
| 灰度开关 | Logo 墙 | `grayscale` | `true` → 灰度滤镜；`false` → 原色 | `{% if grayscale %}xx-logo--grayscale{% endif %}` |
| 按钮变体 | CTA/链接 | `btn_style` | `primary` / `outline` → 不同 class | `xx-btn--{{ btn_style }}` |
| 尺寸变体 | 通用 | `size` | `sm` / `md` / `lg` | `xx-card--{{ size }}` |
| 图片形状 | 头像/Logo | `img_shape` | `rounded` / `circle` / `square` | `xx-img--{{ img_shape }}` |
| 悬停效果 | 卡片/按钮 | `hover_effect` | `lift` / `glow` / `none` | `xx-card--hover-{{ hover_effect }}` |
| 内容宽度 | 文本区 | `content_width` | `narrow` / `normal` / `wide` | `xx-content--{{ content_width }}` |
| 链接打开方式 | 按钮/链接 | `link_target` | `_self` → 当前页；`_blank` → 新标签 | `{% if link_target == '_blank' %}target="_blank" rel="noopener"{% endif %}` |

**CSS 类名切换的本质：** `{% if %}` 决定是否追加 modifier class；CSS 文件中集中管理各状态样式。


---

**机制三：`{% if %}` 控制元素存亡（字段为空 → 整个 DOM 不渲染）**

适用于"有就显示、没有就不显示"的字段。与机制一的区别：机制一是不输出 `style` 属性（元素还在）；机制三是整个元素不渲染（DOM 里没有这个标签）。

| 控制维度 | 字段/条件 | 写法 |
|---------|----------|------|
| 模块整体显隐 | `title` 等核心字段不为空才渲染 | `{% if md.title %}<section>...</section>{% endif %}` |
| 标题区显隐 | `title` | `{% if md.title %}<div class="section-header">...</div>{% endif %}` |
| 副标题显隐 | `subtitle` | `{% if md.subtitle %}<p class="section-description">{{ md.subtitle }}</p>{% endif %}` |
| 描述显隐 | `desc` | `{% if md.desc %}<div class="xx-desc">{{ md.desc }}</div>{% endif %}` |
| 图片显隐 | `image` | `{% if md.image %}<div class="xx-image"><img src="{{ md.image }}"></div>{% endif %}` |
| 图片 fallback | `item.cover` or `item.image`（取第一个非空值） | `{% if item.cover or item.image %}<img src="{{ item.cover or item.image }}">{% else %}<div class="placeholder">{% endif %}` |
| 按钮显隐 | `btn_text` + `btn_url`（两者同时存在才渲染） | `{% if md.btn_text and md.btn_url %}<a href="{{ md.btn_url }}">{{ md.btn_text }}</a>{% endif %}` |
| 按钮区显隐 | 至少一个按钮存在 | `{% if md.primaryBtn or md.secondaryBtn %}<div class="xx-actions">{% endif %}` |
| 标签显隐 | `tag` | `{% if md.tag %}<span class="xx-tag">{{ md.tag }}</span>{% endif %}` |
| 列表区域显隐 | list 字段不为空 | `{% if items is iterable and items is not string and items \| length > 0 %}` |
| 日期显隐 | `item.date` | `{% if item.date %}<div class="xx-date">{{ item.date }}</div>{% endif %}` |
| 摘要显隐 | `item.summary` / `item.description` / `item.excerpt` | `{% set desc = item.description or item.summary or item.excerpt or '' %}{% if desc %}<p>{{ desc }}</p>{% endif %}` |
| 分类/标签显隐 | `item.category`, `item.tags` | `{% if item.category %}<span class="xx-category">{{ item.category }}</span>{% endif %}` |
| 显示开关 | `show_phone`, `show_email`, `show_address`, `show_hours` | `{% if md.show_phone and contact.phone %}` |
| 分页显隐 | `show_pagination` + 数据超过一页 | `{% if show_pagination and total > per_page %}` |
| 边框显隐 | `show_border` | `{% if show_border == '0' %}border: none;{% endif %}` |
| 富文本/纯文本 | `body` 是否含 HTML 标签 | `{% if '</' in body_str or '<br' in body_str %}{{ body_str \| safe }}{% else %}按分段包装 <p>{% endif %}` |
| 链接/纯展示 | `link`（有链接→`<a>`，无→`<div>`） | `{% if logo.link %}<a href="{{ logo.link }}">{% else %}<div>{% endif %}` |
| 外部链接标识 | `link` 是否以 `http` 开头 | `{% if link.startswith('http') %}target="_blank" rel="noopener"{% endif %}` |
| 多图判断 | 图片 ≥ 2 张才渲染缩略图/轮播控件 | `{% if md.images and md.images \| length >= 2 %}` |
| 空状态 | 数据集为空 → 占位提示 | `{% if items \| length == 0 %}<div class="empty-state">暂无内容</div>{% endif %}` |
| 奇偶行 | `loop.index % 2`（隔行变色等） | `{% if loop.index is odd %}class="odd-row"{% else %}class="even-row"{% endif %}` |


---

**机制四：`data-*` 属性（数据写给 JS 消费，不影响渲染）**

适用于**纯前端就能闭环**的交互——不需要后端、不需要第三方服务、一段 `<script>` 自给自足。

`style` 在 HTML 解析完成即刻渲染，`data-*` 要等 JS 读取后才生效。

| 控制维度 | 属性 | 写法 | 用什么 JS |
|---------|------|------|----------|
| 数字动画目标 | `data-target` | `<span data-target="{{ stat.number }}">0</span>` | `IntersectionObserver` + `requestAnimationFrame` 缓动 |
| 分页定位/状态 | `data-block-id`, `data-page`, `data-per-page`, `data-total` | `data-page="1" data-per-page="{{ per_page }}" data-total="{{ total }}"` | DOM class 切换（显示/隐藏卡片） |
| 缩略图大图 | `data-full` | `data-full="{{ image.url }}"` | 点击替换主图 `src` |
| 轮播索引 | `data-index`, `data-slide` | `data-index="{{ loop.index0 }}"` | `setInterval` + class 切换 |
| 轮播配置 | `data-autoplay-interval` | `data-autoplay-interval="5000"` | `setInterval` 读取间隔 |
| 动画触发 | `data-animate`, `data-animation-delay` | `data-animate="fade-up" data-animation-delay="200"` | `IntersectionObserver` 进入视口加 class |
| 防重复触发 | `data-counted` | JS 内 `el.dataset.counted = 'true'` | 动画/计数只播一次 |
| CSS 属性选择器 | `data-columns` | `data-columns="{{ columns }}"` | 零 JS，CSS `[data-columns="3"]` 直接匹配 |
| 手风琴折叠 | `data-accordion-group` | `data-accordion-group="faq"` | 点击切同级 `.open` class |
| Tab 切换 | `data-tab`, `data-tab-group` | `data-tab="tab-1" data-tab-group="detail"` | 点击切面板显隐 |
| 客户端过滤 | `data-filter`, `data-filter-group` | `data-filter="museum" data-filter-group="projects"` | 点击显示/隐藏匹配项 |
| 倒计时 | `data-deadline` | `data-deadline="2026-12-31T23:59:59"` | `setInterval` + 计算时间差 |


---

### 控制方法速查

| 你要控制的 | 用什么方法 | 判断依据 |
|-----------|-----------|---------|
| 颜色、字号、宽高、间距、圆角、阴影 | **inline style** `{% if %}` guard | 值无限 |
| 背景图、透明度、滤镜、对齐 | **inline style** `{% if %}` guard | 值无限 |
| Grid 列数/间距、图片适配 | **inline style** `{% if %}` guard | 值无限 |
| 左右交换、横纵切换、上图下/左图右 | **CSS class 切换** | 值 ≤4 种 |
| 灰度开关、分页样式、图片形状、悬停效果 | **CSS class 切换** | 值 ≤4 种 |
| 整个元素显示/隐藏（标题、图片、按钮、标签等） | **`{% if %}` 条件渲染** | 无值 = 不渲染 DOM |
| 分页、轮播、数字动画 | **`data-*` + 纯前端 JS** | 一段 `<script>` 自闭环 |
| 手风琴、Tab 切换、过滤、倒计时 | **`data-*` + 纯前端 JS** | 同上 |
| 列表子项遍历 | **`{% for %}` 遍历** | list 类型字段 |
| 纯文本/富文本内容 | **`{{ }}` 插值 / `\| safe`** | text/textarea/richtext 字段 |

**规则：**
- 每个 Block 用专属 BEM 前缀，**不用** `module.type`（详见下方 CSS 类名前缀表）
- 内容区 class 不参与外层/内层的布局逻辑——它只管自己内部的排列




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
