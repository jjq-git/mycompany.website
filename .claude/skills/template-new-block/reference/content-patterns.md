# 内容区模式参考

Block 的标题区（`.section-header`）是统一的，但内容区（`.section .container` 内部）的结构完全由 Block 类型决定。本文档按结构模式分类整理，方便新建 Block 时找到最接近的参考模板。

---

## 导航

| Block | 模式 | 内容区结构 | 字段速查 |
|-------|------|-----------|---------|
| [一、hero_banner](#一hero_banner) | A 图文并排 | 全屏轮播：`.hero-banner-slide` → media + overlay + content | [字段总览](#3hero_banner-字段总览) |
| [二、item_detail](#二item_detail) | A 图文并排 | 双栏详情：`.id-grid` → `.id-image-zone` + `.id-info-zone` | [字段总览](#3item_detail-字段总览) |
| [三、highlight_card](#三highlight_card) | A 图文并排 | `.hl-grid` → `.hl-image` + `.hl-text`（标签/标题/描述/列表/按钮） | [字段总览](#3highlight_card-字段总览) |
| [四、feature_grid](#四feature_grid) | B 网格列表 | `.services-grid` → `.service-card`（图标/标题/描述） | [字段总览](#3feature_grid-字段总览) |
| [五、data_grid](#五data_grid) | B 网格列表 | `.dg-list` → `.dg-card`（图片/标题/描述/标签），支持分页 | [字段总览](#3data_grid-字段总览) |
| [六、product_grid](#六product_grid) | B 网格列表 | `.grid` → `.product-card`（图片/标题/描述） | [字段总览](#3product_grid-字段总览) |
| [七、logo_cloud](#七logo_cloud) | B 网格列表 | `.lc-grid` → `.lc-item` → `.lc-logo` | [字段总览](#3logo_cloud-字段总览) |
| [八、section_title](#八section_title) | C 纯文本 | `.st-block`（标签/标题/描述/按钮） | [字段总览](#3section_title-字段总览) |
| [九、text_content](#九text_content) | C 纯文本 | `.tc-block`（标题/富文本正文，支持双栏） | [字段总览](#3text_content-字段总览) |
| [十、stat_counter](#十stat_counter) | D 数据展示 | `.sc-grid` → `.sc-card`（图标/数字/后缀/标签） | [字段总览](#3stat_counter-字段总览) |
| [十一、process_steps](#十一process_steps) | D 数据展示 | `.ps-track` → `.ps-step`（序号/图标/标题/描述） | [字段总览](#3process_steps-字段总览) |
| [十二、contact_info](#十二contact_info) | D 数据展示 | `.ci-grid` → `.ci-card`（图标/标签/值），数据来自站点设置 | [字段总览](#3contact_info-字段总览) |
| [十三、contact_form](#十三contact_form) | E 表单 | `.cf-form`（姓名/邮箱/电话/留言），可选嵌入地图 | [字段总览](#3contact_form-字段总览) |

> 外层（`.section`）、内层（`.container`）、标题区（`.section-header`）的字段定义见 [block-structure.md](block-structure.md)，本文档仅列出内容区专属字段。

---

## 一、hero_banner

### 1、HTML 骨架

```html
<!-- ===== 全屏轮播 ===== -->
<section class="section hero-banner">
    <div class="container">
        <div class="hero-banner-slides">
            <div class="hero-banner-slide active">
                <div class="hero-banner-media">                       <!-- 媒体区 -->
                <div class="hero-banner-image" style="..."></div>    <!-- 图片背景 -->
                <!-- 或 <video class="hero-banner-video" ...> -->
                </div>
                <div class="hero-banner-overlay"></div>                <!-- 遮罩层 -->
                <div class="hero-banner-content" style="">             <!-- 文字内容 -->
                <h1 class="hero-banner-title" style="">标题</h1>
                <p class="hero-banner-subtitle" style="">副标题</p>
                <div class="hero-banner-actions" style="">            <!-- 按钮区 -->
                    <a href="..." class="btn btn-primary btn-lg" style="">主按钮</a>
                    <a href="..." class="btn btn-secondary btn-lg">副按钮</a>
                </div>
                </div>
            </div>
        </div>
        <!-- 多张时显示导航点 + 左右箭头 -->
        <div class="hero-banner-dots">...</div>
        <button class="hero-banner-nav">...</button>
  </div>
</section>
```

**hero_banner 不使用 `.section-header`**。标题和副标题在 `.hero-banner-content` 内部实现。

**可见即所得的排版**：`banner_align` 字段直接决定文字块的 `left`/`top`/`transform` 定位，不需要用户写 CSS。

### 2、内容区字段

#### 2.1 `.hero-banner`（section 层覆盖）

hero_banner 覆盖了外层 section 的默认行为，使用专属的 `hero_height`/`hero_width` 字段。

**内联style中自定义的css属性：** height、max-width、background

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `hero_width` | Banner 最大宽度 | text | `max-width` | `""` | 如 `100%`（留空=全宽） |
| `hero_height` | Banner 高度 | text | `height` | `""` | 如 `500px` 或 `77vh`（留空=CSS 默认 `77vh`） |
| `banner_align` | 文字排版 | select | — | `""` | `center`=居中 / `left`=居左 / `right`=居右，控制 `.hero-banner-content` 定位 |
| `section_bg` | 外层背景色 | color | `background` | `""` | 轮播区域背景色 |

#### 2.2 `.hero-banner-overlay` — 遮罩层

**作用：** 在媒体层之上、文字之下叠加半透明遮罩，保证文字可读性。

**内联style中自定义的css属性：** background、opacity

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `overlay_color` | 遮罩颜色 | color | `background` | `""` | 如 `#000000`（留空=CSS 默认渐变） |
| `overlay_opacity` | 遮罩透明度 | text | `opacity` | `""` | 如 `0.4`（留空=CSS 默认） |

#### 2.3 `.hero-banner-content` — 文字内容区

**作用：** 绝对定位在 Banner 中央（或左/右）的文字容器。

**内联style中自定义的css属性：** max-width、padding、border-radius、background

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `content_width` | 内容区宽度 | text | `max-width` | `""` | 如 `800px`（留空=全宽） |
| `content_max_width` | 内容区最大宽度 | text | `max-width` | `""` | 与 `content_width` 相同，语义更清晰 |
| `content_padding` | 内容区内边距 | text | `padding` | `""` | 如 `2rem` |
| `content_bg` | 内容区背景 | color | `background` | `""` | 如 `rgba(0,0,0,0.3)`，为文字区加半透明底色 |
| `content_radius` | 内容区圆角 | text | `border-radius` | `""` | 如 `12px` |

#### 2.4 `.hero-banner-title` — 主标题

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `title_font_size` | 标题字号 | text | `font-size` | `""` | 如 `3.5rem` |
| `title_color` | 标题颜色 | color | `color` | `""` | 如 `#ffffff` |
| `title_weight` | 标题字重 | select | `font-weight` | `""` | `400` / `500` / `600` / `700` |
| `title_line_height` | 标题行高 | text | `line-height` | `""` | 如 `1.2` |
| `title_text_shadow` | 标题文字阴影 | text | `text-shadow` | `""` | 如 `0 2px 8px rgba(0,0,0,0.5)` |

#### 2.5 `.hero-banner-subtitle` — 副标题

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `subtitle_font_size` | 副标题字号 | text | `font-size` | `""` | 如 `1.25rem` |
| `subtitle_color` | 副标题颜色 | color | `color` | `""` | 如 `rgba(255,255,255,0.85)` |
| `subtitle_weight` | 副标题字重 | select | `font-weight` | `""` | `300` / `400` / `500` |
| `subtitle_line_height` | 副标题行高 | text | `line-height` | `""` | 如 `1.5` |
| `subtitle_max_width` | 副标题最大宽度 | text | `max-width` | `""` | 如 `600px`，限制行长 |

#### 2.6 `.hero-banner-actions` — 按钮区

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `btn_font_size` | 按钮字号 | text | `font-size` | `""` | 如 `1rem` |
| `btn_text_color` | 按钮文字色 | color | `color` | `""` | 如 `#ffffff` |
| `btn_bg` | 按钮背景色 | color | `background` | `""` | 如 `#067a7a` |
| `btn_radius` | 按钮圆角 | text | `border-radius` | `""` | 如 `8px` |
| `btn_padding` | 按钮内边距 | text | `padding` | `""` | 如 `12px 32px` |
| `btn_weight` | 按钮字重 | select | `font-weight` | `""` | `500` / `600` |
| `btn_hover_bg` | 按钮悬停背景 | color | `background` | `""` | hover 态背景色 |
| `btn_hover_color` | 按钮悬停字体色 | color | `color` | `""` | hover 态文字颜色 |
| `btn_transition` | 按钮过渡 | text | `transition` | `""` | 如 `all 0.3s ease` |

#### 2.7 导航控件

**作用：** 多张轮播时显示的导航点（dots）和左右箭头。

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `dot_color` | 导航点颜色 | color | `background` | `""` | 非激活态的导航点颜色 |
| `dot_active_color` | 激活点颜色 | color | `background` | `""` | 当前 slide 的导航点颜色 |
| `nav_color` | 箭头颜色 | color | `color` | `""` | 左右箭头图标颜色 |
| `nav_bg` | 箭头背景 | color | `background` | `""` | 箭头按钮背景色 |
| `autoplay` | 自动播放 | select | — | `"true"` | `true`=自动轮播 / `false`=手动切换 |
| `autoplay_interval` | 轮播间隔 | text | — | `""` | 如 `5000`（毫秒，留空=8000ms） |

#### 2.8 数据字段（list 子项：`slides`）

| key | label | type | 说明 |
|-----|-------|------|------|
| `slides[].type` | 媒体类型 | select | `image`=图片 / `video`=视频 |
| `slides[].media` | 媒体地址 | url | 图片或视频 URL |
| `slides[].title` | 主标题 | text | 当前 slide 的标题 |
| `slides[].subtitle` | 副标题 | text | 当前 slide 的副标题 |
| `slides[].primaryBtn` | 主按钮文字 | text | 留空不渲染 |
| `slides[].primaryBtnLink` | 主按钮链接 | url | 按钮跳转地址 |
| `slides[].secondaryBtn` | 副按钮文字 | text | 留空不渲染 |
| `slides[].secondaryBtnLink` | 副按钮链接 | url | 副按钮跳转地址 |

---

### 3、hero_banner 字段总览

| group | 包含字段 |
|-------|---------|
| 外层样式 | `hero_width`、`hero_height`、`section_bg`、`banner_align`、`outer_width`、`padding_*` |
| 遮罩层 | `overlay_color`、`overlay_opacity` |
| 内容区 | `content_width`、`content_max_width`、`content_padding`、`content_bg`、`content_radius` |
| 标题 | `title_font_size`、`title_color`、`title_weight`、`title_line_height`、`title_text_shadow` |
| 副标题 | `subtitle_font_size`、`subtitle_color`、`subtitle_weight`、`subtitle_line_height`、`subtitle_max_width` |
| 按钮 | `btn_font_size`、`btn_text_color`、`btn_bg`、`btn_radius`、`btn_padding`、`btn_weight`、`btn_hover_bg`、`btn_hover_color`、`btn_transition` |
| 导航 | `dot_color`、`dot_active_color`、`nav_color`、`nav_bg`、`autoplay`、`autoplay_interval` |
| 数据源 | `slides`（`type`、`media`、`title`、`subtitle`、`primaryBtn`、`primaryBtnLink`、`secondaryBtn`、`secondaryBtnLink`） |

---

### 4、模板源文件位置

| 文件 | 说明 |
|------|------|
| [template.html](../../../../site_templates/dengtec/blocks/hero_banner/template.html) | Block Jinja2 模板 |
| [meta.yaml](../../../../site_templates/dengtec/blocks/hero_banner/meta.yaml) | 当前已接入的字段定义 |
| [block-structure.md](block-structure.md) | 四层结构约定和共享字段定义 |

---

## 二、item_detail

### 1、HTML 骨架

```html
<!-- ===== 双栏详情展示 ===== -->
<div class="id-grid" style="">
  <!-- 左侧：图片区 -->
  <div class="id-image-zone">
    <div class="id-magnify-container">                         <!-- 放大镜容器 -->
      <img class="id-main-image" src="..." style="">           <!-- 主图 -->
      <div class="id-magnify-glass" style="display:none"></div> <!-- 放大镜 -->
    </div>
    <div class="id-thumb-list">                                <!-- 缩略图列表 -->
      <div class="id-thumb-item active" style="..."></div>
    </div>
  </div>
  <!-- 右侧：信息区 -->
  <div class="id-info-zone" style="">
    <h1 class="id-title" style="">标题</h1>
    <p class="id-desc" style="">描述</p>
    <div class="id-tags">
      <span class="id-tag" style="">标签</span>
    </div>
    <div class="id-specs-section">                             <!-- 规格参数表 -->
      <h3 class="id-specs-title">规格参数</h3>
      <table class="id-specs-table">
        <tr><td class="id-spec-name">参数名</td><td class="id-spec-value">参数值</td></tr>
      </table>
    </div>
  </div>
</div>
```

**item_detail 不使用 `.section-header`**。标题和描述在 `.id-info-zone` 内部实现。

### 2、内容区字段

#### 2.1 `.id-grid` — 根容器

**作用：** 双栏 Grid 布局，左侧图片区 + 右侧信息区。

**内联style中自定义的css属性：** gap、min-height、background

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `grid_gap` | 图文间距 | text | `gap` | `""` | 图片区与信息区之间的间距，如 `3rem` |
| `grid_min_height` | 最小高度 | text | `min-height` | `""` | 如 `500px`，保证区域高度统一 |
| `grid_background` | 整体背景色 | color | `background` | `""` | 内容区整体底色 |
| `grid_radius` | 整体圆角 | text | `border-radius` | `""` | 如 `12px` |

#### 2.2 `.id-image-zone` — 图片区

**作用：** 左侧（或上方）的图片展示区，包含主图放大镜和缩略图列表。

**内联style中自定义的css属性：** width、background、padding

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `image_zone_width` | 图片区宽度 | text | `width` | `""` | 如 `55%` |
| `image_zone_bg` | 图片区背景 | color | `background` | `""` | 图片区底色 |
| `img_height` | 主图高度 | text | `height` | `""` | 如 `450px` |
| `img_border_radius` | 主图圆角 | text | `border-radius` | `""` | 如 `12px` |
| `img_object_fit` | 主图填充 | select | `object-fit` | `""` | `cover` / `contain` / `fill` |
| `img_bg` | 主图占位背景 | color | `background` | `""` | 图片加载前的占位色 |
| `thumb_gap` | 缩略图间距 | text | `gap` | `""` | 缩略图之间的间距 |
| `thumb_size` | 缩略图尺寸 | text | `width`/`height` | `""` | 如 `80px` |
| `thumb_radius` | 缩略图圆角 | text | `border-radius` | `""` | 如 `8px` |
| `thumb_border` | 缩略图边框 | text | `border` | `""` | 如 `2px solid transparent` |
| `thumb_active_border` | 激活缩略图边框 | color | `border-color` | `""` | 当前选中缩略图的边框色 |

#### 2.3 `.id-info-zone` — 信息区

**作用：** 右侧文字容器，Flex 纵向排列标题/描述/标签/规格表。

**内联style中自定义的css属性：** padding、background、color

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `info_padding` | 信息区内边距 | text | `padding` | `""` | 如 `2rem` |
| `info_bg` | 信息区背景 | color | `background` | `""` | 如 `#f9fafb` |
| `text_color` | 文字基准色 | color | `color` | `""` | 标题/描述/标签默认继承此颜色 |

#### 2.4 `.id-title` — 标题

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `title` | 标题文字 | text | — | `""` | 留空则整个模块不渲染 |
| `title_size` | 标题字号 | text | `font-size` | `""` | 如 `2rem` |
| `title_color` | 标题颜色 | color | `color` | `""` | 独立于 `text_color` |
| `title_weight` | 标题字重 | select | `font-weight` | `""` | `500` / `600` / `700` |
| `title_margin_bottom` | 标题下间距 | text | `margin-bottom` | `""` | 标题到描述的距离 |

#### 2.5 `.id-desc` — 描述

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `desc` | 描述文字 | textarea | — | `""` | 留空不渲染 |
| `desc_size` | 描述字号 | text | `font-size` | `""` | 如 `1rem` |
| `desc_color` | 描述颜色 | color | `color` | `""` | 独立于 `text_color` |
| `desc_line_height` | 描述行高 | text | `line-height` | `""` | 如 `1.7` |
| `desc_margin_bottom` | 描述下间距 | text | `margin-bottom` | `""` | 描述到标签区的距离 |

#### 2.6 `.id-tag` — 标签

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `tags` | 标签列表 | list | — | `[]` | 数组或逗号分隔字符串 |
| `tag_bg` | 标签背景色 | color | `background` | `""` | 如 `#e0f2fe` |
| `tag_color` | 标签字体色 | color | `color` | `""` | 如 `#0369a1` |
| `tag_size` | 标签字号 | text | `font-size` | `""` | 如 `0.8rem` |
| `tag_radius` | 标签圆角 | text | `border-radius` | `""` | 如 `4px` |
| `tag_padding` | 标签内边距 | text | `padding` | `""` | 如 `4px 10px` |
| `tags_gap` | 标签间距 | text | `gap` | `""` | 标签之间的间距 |

#### 2.7 `.id-specs-table` — 规格参数表

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `specs` | 规格参数列表 | list | — | `[]` | 每条含 `name`（参数名）和 `value`（参数值） |
| `specs_table_border` | 表格边框色 | color | `border-color` | `""` | 如 `#e5e7eb` |
| `specs_row_bg` | 斑马纹背景 | color | `background` | `""` | 奇数行的背景色 |
| `specs_name_width` | 参数名列宽 | text | `width` | `""` | 如 `30%` |
| `specs_text_size` | 表格字号 | text | `font-size` | `""` | 如 `0.9rem` |

---

### 3、item_detail 字段总览

| group | 包含字段 |
|-------|---------|
| 外层样式 | `section_bg`、`outer_width`、`inner_width`、`inner_bg`、`padding_*` |
| 整体容器 | `grid_gap`、`grid_min_height`、`grid_background`、`grid_radius` |
| 图片区 | `image_zone_width`、`image_zone_bg`、`img_height`、`img_border_radius`、`img_object_fit`、`img_bg`、`thumb_gap`、`thumb_size`、`thumb_radius`、`thumb_border`、`thumb_active_border` |
| 信息区 | `info_padding`、`info_bg`、`text_color` |
| 标题 | `title`、`title_size`、`title_color`、`title_weight`、`title_margin_bottom` |
| 描述 | `desc`、`desc_size`、`desc_color`、`desc_line_height`、`desc_margin_bottom` |
| 标签 | `tags`、`tag_bg`、`tag_color`、`tag_size`、`tag_radius`、`tag_padding`、`tags_gap` |
| 规格表 | `specs`、`specs_table_border`、`specs_row_bg`、`specs_name_width`、`specs_text_size` |

---

### 4、模板源文件位置

| 文件 | 说明 |
|------|------|
| [template.html](../../../../site_templates/dengtec/blocks/item_detail/template.html) | Block Jinja2 模板 |
| [meta.yaml](../../../../site_templates/dengtec/blocks/item_detail/meta.yaml) | 当前已接入的字段定义 |
| [block-structure.md](block-structure.md) | 四层结构约定和共享字段定义 |

---

## 三、highlight_card

### 1、HTML 骨架

```html
<!-- ===== 自定义内容区 .hl-grid ===== -->
<div class="hl-grid" style="">
    <div class="hl-image">                                      <!-- 图片侧 -->
        <img src="..." alt="..." loading="lazy" style="">
    </div>
    <div class="hl-text" style="">                              <!-- 文字侧 -->
        <span class="hl-tag" style="">...</span>                <!-- 标签 -->
        <h3 class="hl-title" style="">...</h3>                  <!-- 标题 -->
        <p class="hl-desc" style="">...</p>                     <!-- 描述 -->
        <ul class="hl-features" style="">                       <!-- 功能列表 -->
            <li style="">...</li>
        </ul>
        <div class="hl-actions" style="">                       <!-- 按钮 -->
            <a href="..." class="hl-btn hl-btn--primary" style="">主按钮</a>
            <a href="..." class="hl-btn hl-btn--secondary" style="">副按钮</a>
        </div>
    </div>
</div>
```

**highlight_card 不使用 `.section-header`**。标题区的概念由 `.hl-title` + `.hl-desc` 在内容区内部实现，见下方字段。

### 2、内容区字段

#### 2.1 `.hl-grid`

**作用：** 内容区根容器，用 Grid 将内容分为左右两栏（`.hl-image` 图片侧 + `.hl-text` 文字侧）。

**内联style中自定义的css属性：** border-radius、gap、min-height、background

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `border_radius` | 整体圆角 | text | `border-radius` | `""` | 整个 hl-grid 的圆角，如 `12px` |
| `image_position` | 图文左右位置 | select | — | `"left"` | `left`=图左文右（默认）；`right`=添加 `.hl-grid--reverse` class |
| `content_gap` | 图文间距 | text | `gap` | `""` | `.hl-image` 与 `.hl-text` 之间的间距，如 `2rem` |
| `grid_min_height` | 最小高度 | text | `min-height` | `""` | 保证卡片高度统一，如 `400px` |
| `grid_background` | 整体背景色 | color | `background` | `""` | 图片和文字两栏的共同底色 |

#### 2.2 `.hl-image` — 图片侧

**作用：** 图片展示区，占据左栏（或右栏），承载产品图/配图。

**内联style中自定义的css属性：** width、height、object-fit、border-radius、background-color、aspect-ratio、object-position、opacity

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `image` | 图片 | image / text | `src` | — | 图片 URL，支持上传或手工填写 |
| `image_width` | 图片区宽度 | text | `width` | `""` | 如 `50%` 或 `600px` |
| `image_height` | 图片区高度 | text | `height` | `""` | 如 `400px`，留空自适应 |
| `image_aspect_ratio` | 图片区宽高比 | text | `aspect-ratio` | `""` | 如 `16/9`、`4/3` |
| `image_fit` | 图片填充方式 | select | `object-fit` | `"cover"` | `cover` / `contain` / `fill` |
| `image_position_obj` | 图片焦点位置 | select | `object-position` | `"center"` | `top` / `center` / `bottom`，配合 `cover` 指定保留区域 |
| `image_radius` | 图片圆角 | text | `border-radius` | `""` | 如 `12px 0 0 12px` |
| `image_bg` | 图片区背景色 | color | `background-color` | `""` | 图片加载前或透明图时的占位背景色 |
| `image_opacity` | 图片透明度 | text | `opacity` | `""` | 如 `0.8` |

#### 2.3 `.hl-text` — 文字侧外层

**作用：** 文字内容区，Flex 纵向排列子元素（标签 → 标题 → 描述 → 功能列表 → 按钮）。

**内联style中自定义的css属性：** background、color、padding、text-align、gap、justify-content

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `text_bg` | 文字区背景色 | color | `background` | `""` | 如 `#f9fafb` |
| `text_color` | 文字区字体色 | color | `color` | `""` | 子元素默认继承此值 |
| `text_padding` | 文字区内边距 | text | `padding` | `"2rem"` | 统一四边内边距 |
| `text_gap` | 子元素间距 | text | `gap` | `""` | 标签/标题/描述/列表/按钮之间的统一间距 |
| `text_align` | 水平对齐 | select | `text-align` | `"left"` | `left` / `center` / `right` |
| `text_justify` | 垂直对齐 | select | `justify-content` | `"center"` | `flex-start` / `center` / `flex-end` / `space-between` |

#### 2.4 `.hl-tag` — 标签

**作用：** 分类标签（可选），位于标题上方。

**内联style中自定义的css属性：** background、color、font-size、font-weight、border-radius、padding、margin-bottom、text-transform、letter-spacing

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `tag` | 标签文字 | text | — | `""` | 留空不渲染 |
| `tag_bg` | 标签背景色 | color | `background` | `""` | 如 `#067a7a` |
| `tag_color` | 标签字体色 | color | `color` | `""` | 如 `#ffffff` |
| `tag_size` | 标签字号 | text | `font-size` | `""` | 如 `0.75rem` |
| `tag_weight` | 标签字重 | select | `font-weight` | `""` | `400` / `500` / `600` / `700` |
| `tag_transform` | 文字变换 | select | `text-transform` | `""` | `uppercase` / `none` / `capitalize` |
| `tag_letter_spacing` | 字间距 | text | `letter-spacing` | `""` | 如 `0.05em` |
| `tag_radius` | 标签圆角 | text | `border-radius` | `""` | 如 `4px` 或 `999px`（胶囊形） |
| `tag_padding` | 标签内边距 | text | `padding` | `""` | 如 `4px 12px` |
| `tag_margin_bottom` | 标签下间距 | text | `margin-bottom` | `""` | 标签到标题的距离 |

#### 2.5 `.hl-title` — 标题

**作用：** 模块主标题，控制整个模块的显隐（留空则模块不渲染）。

**内联style中自定义的css属性：** font-size、color、font-weight、text-align、margin-bottom、line-height

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `title` | 标题文字 | text | — | `""` | **控制整个模块显隐** |
| `title_size` | 标题字号 | text | `font-size` | `""` | 如 `1.5rem` |
| `title_color` | 标题颜色 | color | `color` | `""` | 如 `#1e293b` |
| `title_weight` | 标题字重 | select | `font-weight` | `""` | `400` / `500` / `600` / `700` |
| `title_line_height` | 标题行高 | text | `line-height` | `""` | 如 `1.3` |
| `title_align` | 标题对齐 | select | `text-align` | `""` | `left` / `center` / `right` |
| `title_margin_bottom` | 标题下间距 | text | `margin-bottom` | `""` | 标题到描述的距离 |

#### 2.6 `.hl-desc` — 描述

**作用：** 标题下方的补充说明文字。

**内联style中自定义的css属性：** font-size、color、font-weight、line-height、margin-bottom、opacity

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `desc` | 描述文字 | textarea | — | `""` | 留空则不渲染 |
| `desc_size` | 描述字号 | text | `font-size` | `""` | 如 `1rem` |
| `desc_color` | 描述颜色 | color | `color` | `""` | 如 `#64748b` |
| `desc_weight` | 描述字重 | select | `font-weight` | `""` | 默认 `400` |
| `desc_line_height` | 描述行高 | text | `line-height` | `""` | 如 `1.6` |
| `desc_opacity` | 描述透明度 | text | `opacity` | `""` | 如 `0.8` |
| `desc_margin_bottom` | 描述下间距 | text | `margin-bottom` | `""` | 描述到功能列表的距离 |

#### 2.7 `.hl-features` — 功能点列表

**作用：** 产品卖点/特性列表，每条带 ✓ 图标。

**内联style中自定义的css属性：** color、font-size、gap、margin-bottom、line-height

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `features` | 功能点列表 | list | — | `[]` | 每条渲染为 `<li>✓ 文本</li>`，空数组不渲染 |
| `features_color` | 功能点颜色 | color | `color` | `""` | 独立于 `text_color` |
| `features_size` | 功能点字号 | text | `font-size` | `""` | 如 `0.95rem` |
| `features_line_height` | 功能点行高 | text | `line-height` | `""` | 如 `1.5` |
| `features_gap` | 功能点间距 | text | `gap` | `""` | `<li>` 之间的间距 |
| `features_icon_color` | ✓ 图标颜色 | color | `color` | `""` | ✓ 字符的颜色 |
| `features_icon_size` | ✓ 图标字号 | text | `font-size` | `""` | ✓ 字符的字号 |
| `features_margin_bottom` | 功能列表下间距 | text | `margin-bottom` | `""` | 列表到按钮区的距离 |

#### 2.8 `.hl-actions` — 按钮区

**作用：** 按钮容器，横向排列主按钮和副按钮。

**内联style中自定义的css属性：** gap、justify-content、margin-top、flex-wrap

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `actions_gap` | 按钮间距 | text | `gap` | `""` | 主按钮与副按钮之间的间距 |
| `actions_align` | 按钮区对齐 | select | `justify-content` | `""` | `flex-start` / `center` / `flex-end` |
| `actions_margin_top` | 按钮区上间距 | text | `margin-top` | `""` | 按钮区到功能列表的距离 |
| `actions_wrap` | 允许换行 | select | `flex-wrap` | `""` | `wrap` / `nowrap` |

#### 2.9 `.hl-btn--primary` / `.hl-btn--secondary` — 按钮

**作用：** CTA 按钮。主按钮引导核心操作，副按钮提供辅助跳转。

| key | label | type | 作用元素 | CSS 属性 | default | 说明 |
|-----|-------|------|----------|----------|---------|------|
| `primaryBtn` | 主按钮文字 | text | `.hl-btn--primary` | — | `""` | 留空不渲染 |
| `primaryLink` | 主按钮链接 | url | `.hl-btn--primary` | `href` | `""` | 按钮跳转地址 |
| `primaryLinkTarget` | 主按钮打开方式 | select | `.hl-btn--primary` | — | `""` | `""`=当前页 / `_blank`=新标签页 |
| `secondaryBtn` | 副按钮文字 | text | `.hl-btn--secondary` | — | `""` | 留空不渲染 |
| `secondaryLink` | 副按钮链接 | url | `.hl-btn--secondary` | `href` | `""` | 副按钮跳转地址 |
| `btn_bg` | 主按钮背景色 | color | `.hl-btn--primary` | `background` | `""` | 如 `#067a7a` |
| `btn_color` | 主按钮字体色 | color | `.hl-btn--primary` | `color` | `""` | 如 `#ffffff` |
| `btn_size` | 按钮字号 | text | `.hl-btn` | `font-size` | `""` | 主/副按钮统一字号 |
| `btn_weight` | 按钮字重 | select | `.hl-btn` | `font-weight` | `""` | `400` / `500` / `600` |
| `btn_radius` | 按钮圆角 | text | `.hl-btn` | `border-radius` | `""` | 如 `6px` 或 `999px` |
| `btn_padding` | 按钮内边距 | text | `.hl-btn` | `padding` | `""` | 如 `10px 24px` |
| `btn_hover_bg` | 主按钮悬停背景 | color | `.hl-btn--primary:hover` | `background` | `""` | hover 态背景色 |
| `btn_hover_color` | 主按钮悬停字体色 | color | `.hl-btn--primary:hover` | `color` | `""` | hover 态文字颜色 |
| `btn_secondary_border` | 副按钮边框色 | color | `.hl-btn--secondary` | `border-color` | `""` | outline 样式边框颜色 |
| `btn_secondary_color` | 副按钮字体色 | color | `.hl-btn--secondary` | `color` | `""` | 副按钮文字颜色 |
| `btn_secondary_hover_bg` | 副按钮悬停背景 | color | `.hl-btn--secondary:hover` | `background` | `""` | 悬停时填充背景 |
| `btn_secondary_hover_color` | 副按钮悬停字体色 | color | `.hl-btn--secondary:hover` | `color` | `""` | 悬停时字体颜色 |
| `btn_transition` | 按钮过渡动画 | text | `.hl-btn` | `transition` | `""` | 如 `all 0.2s ease` |

---

### 3、highlight_card 字段总览

| group | 包含字段 |
|-------|---------|
| 外层样式 | `section_bg`、`outer_width`、`margin_top`、`margin_bottom`、`padding_top`、`padding_right`、`padding_bottom`、`padding_left` |
| 内层样式 | `inner_width` |
| 图文布局 | `image_position`、`border_radius`、`content_gap`、`grid_min_height`、`grid_background` |
| 图片 | `image`、`image_width`、`image_height`、`image_aspect_ratio`、`image_fit`、`image_position_obj`、`image_radius`、`image_bg`、`image_opacity` |
| 文字区 | `text_bg`、`text_color`、`text_padding`、`text_gap`、`text_align`、`text_justify` |
| 标签 | `tag`、`tag_bg`、`tag_color`、`tag_size`、`tag_weight`、`tag_transform`、`tag_letter_spacing`、`tag_radius`、`tag_padding`、`tag_margin_bottom` |
| 标题 | `title`、`title_size`、`title_color`、`title_weight`、`title_line_height`、`title_align`、`title_margin_bottom` |
| 描述 | `desc`、`desc_size`、`desc_color`、`desc_weight`、`desc_line_height`、`desc_opacity`、`desc_margin_bottom` |
| 功能列表 | `features`、`features_color`、`features_size`、`features_line_height`、`features_gap`、`features_icon_color`、`features_icon_size`、`features_margin_bottom` |
| 按钮区 | `actions_gap`、`actions_align`、`actions_margin_top`、`actions_wrap` |
| 按钮 | `primaryBtn`、`primaryLink`、`primaryLinkTarget`、`secondaryBtn`、`secondaryLink`、`btn_bg`、`btn_color`、`btn_size`、`btn_weight`、`btn_radius`、`btn_padding`、`btn_hover_bg`、`btn_hover_color`、`btn_secondary_border`、`btn_secondary_color`、`btn_secondary_hover_bg`、`btn_secondary_hover_color`、`btn_transition` |

---

### 4、模板源文件位置

| 文件 | 说明 |
|------|------|
| [template.html](../../../../site_templates/dengtec/blocks/highlight_card/template.html) | Block Jinja2 模板 |
| [meta.yaml](../../../../site_templates/dengtec/blocks/highlight_card/meta.yaml) | 当前已接入的字段定义 |
| [admin_modules.js](../../../../app/static/js/admin_modules.js) | 后台编辑表单（搜索 `highlight_card`） |
| [block-structure.md](block-structure.md) | 四层结构约定和共享字段定义 |

---

## 四、feature_grid

### 1、HTML 骨架

```html
<!-- ===== 功能卡片网格 ===== -->
<div class="services-grid" style="">
  <div class="service-card" style="">
    <div class="service-icon"><!-- SVG 图标 --></div>
    <div class="service-content">
      <h3 class="service-title" style="">标题</h3>
      <p class="service-description" style="">描述</p>
    </div>
  </div>
  <!-- 更多 .service-card ... -->
</div>
```

**feature_grid 使用 `.section-header`**（共享标题区）。字段走 [block-structure.md](block-structure.md)。

### 2、内容区字段

#### 2.1 `.services-grid` — 网格容器

**内联style中自定义的css属性：** gap、row-gap

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `grid_columns` | 每行列数 | select | `grid-template-columns` | `""` | `3`=三列 / `4`=四列（留空=CSS 默认 `repeat(3, 1fr)`） |
| `grid_gap` | 卡片间距 | text | `gap` | `""` | 如 `2rem` |
| `grid_row_gap` | 行间距 | text | `row-gap` | `""` | 仅控制行间距 |

#### 2.2 `.service-card` — 功能卡片

**作用：** 单个功能项的容器，包含图标和文字。

**内联style中自定义的css属性：** border、padding、border-radius、background、box-shadow、transform、transition

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `card_show_border` | 显示边框 | select | `border` | `""` | `""`=显示 / `"0"`=隐藏（`border: none`） |
| `card_border_color` | 卡片边框色 | color | `border-color` | `""` | 如 `#e5e7eb` |
| `card_padding_top` | 卡片上内边距 | text | `padding-top` | `""` | 如 `24px` |
| `card_padding_right` | 卡片右内边距 | text | `padding-right` | `""` | 如 `24px` |
| `card_padding_bottom` | 卡片下内边距 | text | `padding-bottom` | `""` | 如 `24px` |
| `card_padding_left` | 卡片左内边距 | text | `padding-left` | `""` | 如 `24px` |
| `card_radius_top_left` | 左上圆角 | text | `border-top-left-radius` | `""` | 如 `12px` |
| `card_radius_top_right` | 右上圆角 | text | `border-top-right-radius` | `""` | 如 `12px` |
| `card_radius_bottom_right` | 右下圆角 | text | `border-bottom-right-radius` | `""` | 如 `12px` |
| `card_radius_bottom_left` | 左下圆角 | text | `border-bottom-left-radius` | `""` | 如 `12px` |
| `card_bg` | 卡片背景色 | color | `background` | `""` | 如 `#ffffff` |
| `card_shadow` | 卡片阴影 | text | `box-shadow` | `""` | 如 `0 2px 12px rgba(0,0,0,0.06)` |
| `card_hover_shadow` | hover 阴影 | text | `box-shadow` | `""` | 悬停时阴影变化 |
| `card_hover_translate_y` | hover 上浮 | text | `transform` | `""` | 如 `-4px`（渲染为 `translateY(-4px)`） |
| `card_transition` | 卡片过渡 | text | `transition` | `""` | 如 `all 0.3s ease` |

#### 2.3 `.service-icon` — 图标区

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `icon_size` | 图标尺寸 | text | `width`/`height` | `""` | 如 `48px` |
| `icon_color` | 图标颜色 | color | `color` | `""` | SVG 图标颜色 |
| `icon_bg` | 图标背景色 | color | `background` | `""` | 图标容器背景 |
| `icon_radius` | 图标区圆角 | text | `border-radius` | `""` | 如 `50%`（圆形图标背景） |
| `icon_margin_bottom` | 图标下间距 | text | `margin-bottom` | `""` | 图标到标题的距离 |

#### 2.4 `.service-title` — 卡片标题

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `title_size` | 标题字号 | text | `font-size` | `""` | 如 `1.25rem` |
| `title_color` | 标题颜色 | color | `color` | `""` | 如 `#1e293b` |
| `title_weight` | 标题字重 | select | `font-weight` | `""` | `500` / `600` / `700` |
| `title_margin_bottom` | 标题下间距 | text | `margin-bottom` | `""` | 标题到描述的距离 |

#### 2.5 `.service-description` — 卡片描述

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `desc_size` | 描述字号 | text | `font-size` | `""` | 如 `0.9rem` |
| `desc_color` | 描述颜色 | color | `color` | `""` | 如 `#64748b` |
| `desc_line_height` | 描述行高 | text | `line-height` | `""` | 如 `1.6` |

#### 2.6 数据字段（list 子项：`features`）

| key | label | type | 说明 |
|-----|-------|------|------|
| `features[].icon` | 图标 | icon | 从预设图标列表中选择 |
| `features[].title` | 标题 | text | 功能卡片标题 |
| `features[].desc` | 描述 | textarea | 功能卡片描述 |

---

### 3、feature_grid 字段总览

| group | 包含字段 |
|-------|---------|
| 外层样式 | `section_bg`、`outer_width`、`margin_*`、`padding_*` |
| 内层样式 | `inner_width` |
| 网格容器 | `grid_columns`、`grid_gap`、`grid_row_gap` |
| 卡片容器 | `card_show_border`、`card_border_color`、`card_padding_*`、`card_radius_*`、`card_bg`、`card_shadow`、`card_hover_shadow`、`card_hover_translate_y`、`card_transition` |
| 图标 | `icon_size`、`icon_color`、`icon_bg`、`icon_radius`、`icon_margin_bottom` |
| 标题 | `title_size`、`title_color`、`title_weight`、`title_margin_bottom` |
| 描述 | `desc_size`、`desc_color`、`desc_line_height` |
| 数据源 | `features`（`icon`、`title`、`desc`） |

---

### 4、模板源文件位置

| 文件 | 说明 |
|------|------|
| [template.html](../../../../site_templates/dengtec/blocks/feature_grid/template.html) | Block Jinja2 模板 |
| [meta.yaml](../../../../site_templates/dengtec/blocks/feature_grid/meta.yaml) | 当前已接入的字段定义 |
| [block-structure.md](block-structure.md) | 四层结构约定和共享字段定义 |

---

## 五、data_grid

### 1、HTML 骨架

```html
<!-- ===== 数据网格 ===== -->
<div class="dg-list" style="">
  <a href="..." class="dg-card" style="">
    <div class="dg-card-image" style="">                         <!-- 图片区 -->
      <span class="dg-card-category" style="">分类</span>       <!-- 分类标签 -->
    </div>
    <div class="dg-card-body" style="">                          <!-- 文字区 -->
      <h3 class="dg-card-title" style="">标题</h3>
      <div class="dg-card-date">日期</div>
      <p class="dg-card-desc" style="">描述</p>
      <div class="dg-card-tags">
        <span class="dg-card-tag" style="">标签</span>
      </div>
    </div>
  </a>
  <!-- 更多 .dg-card ... -->
</div>
<!-- 分页器 -->
<div class="dg-pager">
  <button class="dg-load-more">加载更多 (N 项)</button>
  <!-- 或 -->
  <div class="dg-page-numbers"><button class="dg-page-btn active">1</button>...</div>
</div>
```

**data_grid 使用 `.section-header`**（共享标题区）。数据来自数据集（products/portfolio/posts），卡片布局可选 `image_top`（上图下文）或 `image_left`（左图右文）。

### 2、内容区字段

#### 2.1 `.dg-list` — 网格容器

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `dataset` | 数据来源 | text | — | `"portfolio"` | `products` / `portfolio` / `posts` 或自定义数据集名 |
| `columns` | 每行列数 | number | `grid-template-columns` | `3` | 渲染为 `repeat(N, 1fr)` |
| `items_per_page` | 每页条数 | number | — | `6` | 分页时每页显示的数量 |
| `card_layout` | 卡片布局 | select | — | `"image_top"` | `image_top`=上图下文 / `image_left`=左图右文 |
| `max_items` | 最大显示数 | number | — | `0` | `0`=不限制 |
| `grid_gap` | 卡片间距 | text | `gap` | `""` | 如 `1.5rem` |
| `grid_row_gap` | 行间距 | text | `row-gap` | `""` | 仅控制行间距 |

#### 2.2 `.dg-card` — 数据卡片

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `card_bg` | 卡片背景色 | color | `background` | `""` | 如 `#ffffff` |
| `card_radius` | 卡片圆角 | text | `border-radius` | `""` | 如 `8px` |
| `card_shadow` | 卡片阴影 | text | `box-shadow` | `""` | 如 `0 1px 4px rgba(0,0,0,0.06)` |
| `card_hover_shadow` | hover 阴影 | text | `box-shadow` | `""` | 悬停阴影 |
| `card_hover_translate_y` | hover 上浮 | text | `transform` | `""` | 如 `-4px` |
| `card_transition` | 卡片过渡 | text | `transition` | `""` | 如 `all 0.3s ease` |

#### 2.3 `.dg-card-image` — 卡片图片区

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `image_height` | 图片区高度 | text | `height` | `""` | 如 `200px` |
| `image_bg` | 图片区背景 | color | `background` | `""` | 无图片时的占位背景色 |

#### 2.4 `.dg-card-body` — 卡片文字区

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `body_padding` | 文字区内边距 | text | `padding` | `""` | 如 `1rem` |
| `body_bg` | 文字区背景 | color | `background` | `""` | 文字区底色 |

#### 2.5 `.dg-card-title` / `.dg-card-desc` — 标题与描述

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `title_size` | 标题字号 | text | `font-size` | `""` | 如 `1.1rem` |
| `title_color` | 标题颜色 | color | `color` | `""` | 如 `#1e293b` |
| `title_weight` | 标题字重 | select | `font-weight` | `""` | `500` / `600` |
| `desc_size` | 描述字号 | text | `font-size` | `""` | 如 `0.9rem` |
| `desc_color` | 描述颜色 | color | `color` | `""` | 如 `#64748b` |
| `desc_line_height` | 描述行高 | text | `line-height` | `""` | 如 `1.5` |

#### 2.6 `.dg-card-category` — 分类标签

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `category_bg` | 分类背景色 | color | `background` | `""` | 如 `#067a7a` |
| `category_color` | 分类字体色 | color | `color` | `""` | 如 `#ffffff` |
| `category_size` | 分类字号 | text | `font-size` | `""` | 如 `0.75rem` |

#### 2.7 `.dg-card-tag` — 标签

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `tag_bg` | 标签背景色 | color | `background` | `""` | 如 `#f1f5f9` |
| `tag_color` | 标签字体色 | color | `color` | `""` | 如 `#475569` |
| `tag_size` | 标签字号 | text | `font-size` | `""` | 如 `0.75rem` |
| `tag_radius` | 标签圆角 | text | `border-radius` | `""` | 如 `4px` |

#### 2.8 分页器

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `show_pagination` | 显示分页 | select | — | `"true"` | `true` / `false` |
| `pagination_style` | 分页样式 | select | — | `"load_more"` | `load_more`=加载更多 / `page_numbers`=页码导航 |
| `pager_align` | 分页对齐 | select | `text-align` | `"center"` | `left` / `center` / `right` |
| `load_more_text` | 加载更多文字 | text | — | `""` | 自定义按钮文字 |
| `load_more_bg` | 按钮背景色 | color | `background` | `""` | 加载更多按钮背景 |
| `load_more_color` | 按钮文字色 | color | `color` | `""` | 加载更多按钮文字颜色 |
| `page_btn_bg` | 页码按钮背景 | color | `background` | `""` | 页码按钮背景色 |
| `page_btn_active_bg` | 激活页码背景 | color | `background` | `""` | 当前页按钮背景色 |
| `page_btn_color` | 页码按钮文字色 | color | `color` | `""` | 页码按钮文字颜色 |

---

### 3、data_grid 字段总览

| group | 包含字段 |
|-------|---------|
| 外层样式 | `section_bg`、`outer_width`、`margin_*`、`padding_*` |
| 内层样式 | `inner_width` |
| 数据配置 | `dataset`、`max_items`、`columns`、`items_per_page`、`card_layout`、`category`（分类筛选） |
| 网格容器 | `grid_gap`、`grid_row_gap` |
| 卡片 | `card_bg`、`card_radius`、`card_shadow`、`card_hover_shadow`、`card_hover_translate_y`、`card_transition` |
| 图片区 | `image_height`、`image_bg` |
| 文字区 | `body_padding`、`body_bg` |
| 标题/描述 | `title_size`、`title_color`、`title_weight`、`desc_size`、`desc_color`、`desc_line_height` |
| 分类标签 | `category_bg`、`category_color`、`category_size` |
| 标签 | `tag_bg`、`tag_color`、`tag_size`、`tag_radius` |
| 分页 | `show_pagination`、`pagination_style`、`pager_align`、`load_more_text`、`load_more_bg`、`load_more_color`、`page_btn_bg`、`page_btn_active_bg`、`page_btn_color` |

---

### 4、模板源文件位置

| 文件 | 说明 |
|------|------|
| [template.html](../../../../site_templates/dengtec/blocks/data_grid/template.html) | Block Jinja2 模板 |
| [meta.yaml](../../../../site_templates/dengtec/blocks/data_grid/meta.yaml) | 当前已接入的字段定义 |
| [block-structure.md](block-structure.md) | 四层结构约定和共享字段定义 |

---

## 六、product_grid

### 1、HTML 骨架

```html
<!-- ===== 产品网格 ===== -->
<div class="grid grid-3" style="">
  <a href="..." class="product-card" style="">
    <div class="product-card-image" style="">                    <!-- 图片区 -->
      <span class="product-card-category">分类</span>
    </div>
    <div class="product-card-body" style="">                     <!-- 文字区 -->
      <h3 class="product-card-title" style="">名称</h3>
      <p class="product-card-desc" style="">描述</p>
    </div>
  </a>
  <!-- 更多 .product-card ... -->
</div>
<a href="..." class="btn btn-primary">查看全部</a>
```

**product_grid 使用 `.section-header`**（共享标题区）。product_grid 是 data_grid 的简化版，仅支持产品数据集、三列固定布局。

### 2、内容区字段

#### 2.1 `.grid` — 网格容器

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `dataset` | 数据来源 | select | — | `"products"` | 固定为 products |
| `columns` | 每行列数 | select | `grid-template-columns` | `"3"` | `2`=两列 / `3`=三列 / `4`=四列 |
| `max_items` | 最大显示数 | number | — | `6` | 最多展示几条 |
| `grid_gap` | 卡片间距 | text | `gap` | `""` | 如 `1.5rem` |
| `grid_row_gap` | 行间距 | text | `row-gap` | `""` | 仅控制行间距 |

#### 2.2 `.product-card` — 产品卡片

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `card_bg` | 卡片背景 | color | `background` | `""` | 如 `#ffffff` |
| `card_radius` | 卡片圆角 | text | `border-radius` | `""` | 如 `8px` |
| `card_shadow` | 卡片阴影 | text | `box-shadow` | `""` | 如 `0 2px 8px rgba(0,0,0,0.06)` |
| `card_hover_shadow` | hover 阴影 | text | `box-shadow` | `""` | 悬停阴影 |
| `card_hover_translate_y` | hover 上浮 | text | `transform` | `""` | 如 `-4px` |
| `card_transition` | 过渡动画 | text | `transition` | `""` | 如 `all 0.3s ease` |

#### 2.3 `.product-card-image` — 图片区

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `image_height` | 图片区高度 | text | `height` | `""` | 如 `220px` |
| `image_bg` | 图片区背景 | color | `background` | `""` | 无图片时的占位背景色 |

#### 2.4 `.product-card-title` / `.product-card-desc` — 标题与描述

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `title_size` | 标题字号 | text | `font-size` | `""` | 如 `1.1rem` |
| `title_color` | 标题颜色 | color | `color` | `""` | 如 `#1e293b` |
| `title_weight` | 标题字重 | select | `font-weight` | `""` | `500` / `600` |
| `desc_size` | 描述字号 | text | `font-size` | `""` | 如 `0.9rem` |
| `desc_color` | 描述颜色 | color | `color` | `""` | 如 `#64748b` |

#### 2.5 分类标签 & 查看全部按钮

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `category_bg` | 分类标签背景 | color | `background` | `""` | 如 `#067a7a` |
| `category_color` | 分类标签颜色 | color | `color` | `""` | 如 `#ffffff` |
| `category_size` | 分类标签字号 | text | `font-size` | `""` | 如 `0.75rem` |
| `view_all_text` | 查看全部文字 | text | — | `""` | 底部按钮文字 |
| `view_all_bg` | 查看全部背景 | color | `background` | `""` | 底部按钮背景色 |
| `view_all_color` | 查看全部颜色 | color | `color` | `""` | 底部按钮文字色 |

---

### 3、product_grid 字段总览

| group | 包含字段 |
|-------|---------|
| 外层样式 | `section_bg`、`outer_width`、`padding_*` |
| 内层样式 | `inner_width` |
| 数据配置 | `dataset`、`max_items`、`columns` |
| 网格容器 | `grid_gap`、`grid_row_gap` |
| 卡片 | `card_bg`、`card_radius`、`card_shadow`、`card_hover_shadow`、`card_hover_translate_y`、`card_transition` |
| 图片区 | `image_height`、`image_bg` |
| 标题/描述 | `title_size`、`title_color`、`title_weight`、`desc_size`、`desc_color` |
| 分类/按钮 | `category_bg`、`category_color`、`category_size`、`view_all_text`、`view_all_bg`、`view_all_color` |

---

### 4、模板源文件位置

| 文件 | 说明 |
|------|------|
| [template.html](../../../../site_templates/dengtec/blocks/product_grid/template.html) | Block Jinja2 模板 |
| [meta.yaml](../../../../site_templates/dengtec/blocks/product_grid/meta.yaml) | 当前已接入的字段定义 |
| [block-structure.md](block-structure.md) | 四层结构约定和共享字段定义 |

---

## 七、logo_cloud

### 1、HTML 骨架

```html
<!-- ===== 自定义内容区 .lc-grid ===== -->
<div class="lc-grid" style="">
    <a href="..." class="lc-item" style="" target="_blank">
        <img src="..." alt="品牌名" class="lc-logo lc-logo--grayscale" style="">
    </a>
    <!-- 更多 .lc-item ... -->
</div>
```

**logo_cloud 使用 `.section-header`**（共享标题区）。下文仅列出内容区专属字段。

### 2、内容区字段

#### 2.1 `.lc-grid` — Logo 网格容器

**内联style中自定义的css属性：** grid-template-columns、gap、align-items、background-color、padding、row-gap

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `columns` | 每行列数 | select | `grid-template-columns` | `"4"` | `4`=四列 / `5`=五列 / `6`=六列 |
| `grid_gap` | 网格间距 | text | `gap` | `""` | Logo 卡片之间的间距，如 `2rem` |
| `grid_row_gap` | 行间距 | text | `row-gap` | `""` | 仅控制行与行之间的间距 |
| `grid_align` | 垂直对齐 | select | `align-items` | `""` | `center`=居中 / `start`=顶部 / `stretch`=拉伸 |
| `grid_background` | 网格背景色 | color | `background-color` | `""` | 如 `#fafafa` |
| `grid_padding` | 网格内边距 | text | `padding` | `""` | 如 `2rem` |

#### 2.2 `.lc-item` — Logo 卡片

**内联style中自定义的css属性：** background-color、border、border-radius、width、height、padding、box-shadow、transform、transition

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `logo_bg` | 卡片背景色 | color | `background-color` | `""` | 如 `#f8fafc` |
| `logo_border` | 卡片边框 | text | `border` | `""` | 如 `1px solid #e5e7eb` |
| `logo_border_color` | 卡片边框色 | color | `border-color` | `""` | 快捷设置边框颜色 |
| `logo_radius` | 卡片圆角 | text | `border-radius` | `""` | 如 `8px` |
| `logo_width` | 卡片宽度 | text | `width` | `""` | 如 `120px` |
| `logo_height` | 卡片高度 | text | `height` | `""` | 如 `80px` |
| `logo_padding` | 卡片内边距 | text | `padding` | `""` | 如 `1.5rem` |
| `logo_shadow` | 卡片阴影 | text | `box-shadow` | `""` | 如 `0 2px 8px rgba(0,0,0,0.08)` |
| `logo_hover_shadow` | hover 阴影 | text | `box-shadow` | `""` | 如 `0 4px 16px rgba(0,0,0,0.12)` |
| `logo_hover_scale` | hover 放大 | text | `transform` | `""` | 如 `1.05`（渲染为 `scale(1.05)`） |
| `logo_hover_bg` | hover 背景色 | color | `background-color` | `""` | 悬停时背景色变化 |
| `logo_transition` | 过渡动画 | text | `transition` | `""` | 如 `all 0.3s ease` |

#### 2.3 `.lc-logo` — Logo 图片

**内联style中自定义的css属性：** filter、max-width、max-height、object-fit、opacity

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `grayscale` | 灰度滤镜 | select | `filter` | `"true"` | `true`=灰度 + 半透明，hover 恢复彩色 / `false`=保持原色 |
| `logo_max_width` | 图片最大宽度 | text | `max-width` | `""` | 如 `120px` |
| `logo_max_height` | 图片最大高度 | text | `max-height` | `""` | 如 `60px` |
| `logo_object_fit` | 图片填充方式 | select | `object-fit` | `""` | `contain` / `cover` / `scale-down` |
| `logo_opacity` | 灰度时透明度 | text | `opacity` | `""` | 灰度模式下透明度，如 `0.6` |

#### 2.4 数据字段（list 子项：`logos`）

| key | label | type | 说明 |
|-----|-------|------|------|
| `logos[].image` | Logo 图片 | image | Logo 图片 URL |
| `logos[].name` | 品牌名称 | text | 用于 `alt` 和 `title` 属性 |
| `logos[].link` | 链接（可选）| url | 留空渲染 `<div>`，填写渲染 `<a>` 新窗口打开 |

---

### 3、logo_cloud 字段总览

| group | 包含字段 |
|-------|---------|
| 外层样式 | `section_bg`、`outer_width` |
| 内层样式 | `inner_width`、`inner_bg`、`padding_top`、`padding_right`、`padding_bottom`、`padding_left` |
| 标题区 | `title`、`subtitle` |
| Logo 网格 | `columns`、`grid_gap`、`grid_row_gap`、`grid_align`、`grid_background`、`grid_padding` |
| Logo 卡片 | `logo_bg`、`logo_border`、`logo_border_color`、`logo_radius`、`logo_width`、`logo_height`、`logo_padding`、`logo_shadow`、`logo_hover_shadow`、`logo_hover_scale`、`logo_hover_bg`、`logo_transition` |
| Logo 图片 | `grayscale`、`logo_max_width`、`logo_max_height`、`logo_object_fit`、`logo_opacity` |
| 数据源 | `logos`（`image`、`name`、`link`） |

---

### 4、模板源文件位置

| 文件 | 说明 |
|------|------|
| [template.html](../../../../site_templates/dengtec/blocks/logo_cloud/template.html) | Block Jinja2 模板 |
| [meta.yaml](../../../../site_templates/dengtec/blocks/logo_cloud/meta.yaml) | 当前已接入的字段定义 |
| [admin_modules.js](../../../../app/static/js/admin_modules.js) | 后台编辑表单（搜索 `logo_cloud`） |
| [block-structure.md](block-structure.md) | 四层结构约定和共享字段定义 |

---

## 八、section_title

### 1、HTML 骨架

```html
<!-- ===== 通用标题模块 ===== -->
<div class="st-block" style="">
  <span class="st-tag" style="">标签</span>                     <!-- 可选标签 -->
  <h2 class="st-title" style="">标题</h2>
  <p class="st-desc" style="">描述</p>
  <a href="..." class="st-btn" style="">按钮</a>               <!-- 可选按钮 -->
</div>
```

**section_title 不使用 `.section-header`**。它把自己作为独立标题区，有自己的标签/标题/描述/按钮体系。

**section_title 没有共享的 `.section` → `.container` 包裹**——它自己输出完整的 `<section>` → `<div class="container">` → `.st-block`。

### 2、内容区字段

#### 2.1 `.st-block` — 根容器

**作用：** 整个标题模块的根容器，控制文字排版和内边距。

**内联style中自定义的css属性：** text-align、padding

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `text_align` | 文字排版 | select | `text-align` | `"center"` | `left` / `center` / `right` |
| `block_padding_top` | 内容上内边距 | text | `padding-top` | `""` | 如 `2rem` |
| `block_padding_bottom` | 内容下内边距 | text | `padding-bottom` | `""` | 如 `2rem` |
| `block_max_width` | 内容区最大宽度 | text | `max-width` | `""` | 如 `800px`（留空=全宽） |

#### 2.2 `.st-tag` — 标签

**作用：** 标题上方的分类标签（可选）。

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `tag` | 标签文字 | text | — | `""` | 留空不渲染 |
| `tag_bg` | 标签背景色 | color | `background` | `""` | 如 `#067a7a` |
| `tag_color` | 标签字体色 | color | `color` | `""` | 如 `#ffffff` |
| `tag_size` | 标签字号 | text | `font-size` | `""` | 如 `0.75rem` |
| `tag_weight` | 标签字重 | select | `font-weight` | `""` | `500` / `600` |
| `tag_radius` | 标签圆角 | text | `border-radius` | `""` | 如 `999px` |
| `tag_padding` | 标签内边距 | text | `padding` | `""` | 如 `4px 16px` |
| `tag_margin_bottom` | 标签下间距 | text | `margin-bottom` | `""` | 标签到标题的距离 |

#### 2.3 `.st-title` — 标题

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `title` | 标题文字 | text | — | `""` | **控制模块显隐**：留空不渲染模块 |
| `title_size` | 标题字号 | text | `font-size` | `""` | 如 `2.5rem` |
| `title_color` | 标题颜色 | color | `color` | `""` | 如 `#1e293b` |
| `title_weight` | 标题字重 | select | `font-weight` | `""` | `500` / `600` / `700` |
| `title_line_height` | 标题行高 | text | `line-height` | `""` | 如 `1.3` |
| `title_margin_bottom` | 标题下间距 | text | `margin-bottom` | `""` | 标题到描述的距离 |

#### 2.4 `.st-desc` — 描述

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `desc` | 描述文字 | textarea | — | `""` | 留空不渲染 |
| `desc_size` | 描述字号 | text | `font-size` | `""` | 如 `1rem` |
| `desc_color` | 描述颜色 | color | `color` | `""` | 如 `#64748b` |
| `desc_weight` | 描述字重 | select | `font-weight` | `""` | 默认 `400` |
| `desc_line_height` | 描述行高 | text | `line-height` | `""` | 如 `1.6` |
| `desc_opacity` | 描述透明度 | text | `opacity` | `""` | 如 `0.8` |
| `desc_margin_bottom` | 描述下间距 | text | `margin-bottom` | `""` | 描述到按钮的距离 |

#### 2.5 `.st-btn` — 按钮

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `btn_text` | 按钮文字 | text | — | `""` | 留空不渲染按钮 |
| `btn_url` | 按钮链接 | url | `href` | `""` | 按钮跳转地址 |
| `btn_target` | 打开方式 | select | — | `""` | `""`=当前页 / `_blank`=新标签页 |
| `btn_bg` | 按钮背景色 | color | `background` | `""` | 如 `#067a7a` |
| `btn_color` | 按钮文字色 | color | `color` | `""` | 如 `#ffffff` |
| `btn_size` | 按钮字号 | text | `font-size` | `""` | 如 `1rem` |
| `btn_weight` | 按钮字重 | select | `font-weight` | `""` | `500` / `600` |
| `btn_radius` | 按钮圆角 | text | `border-radius` | `""` | 如 `8px` |
| `btn_padding` | 按钮内边距 | text | `padding` | `""` | 如 `10px 32px` |
| `btn_hover_bg` | 悬停背景 | color | `background` | `""` | hover 态背景色 |
| `btn_hover_color` | 悬停字体色 | color | `color` | `""` | hover 态文字颜色 |
| `btn_transition` | 按钮过渡 | text | `transition` | `""` | 如 `all 0.3s ease` |

---

### 3、section_title 字段总览

| group | 包含字段 |
|-------|---------|
| 外层样式 | `section_bg`、`outer_width`、`margin_*` |
| 内层样式 | `inner_width`、`padding_*` |
| 内容排版 | `text_align`、`block_padding_top`、`block_padding_bottom`、`block_max_width` |
| 标签 | `tag`、`tag_bg`、`tag_color`、`tag_size`、`tag_weight`、`tag_radius`、`tag_padding`、`tag_margin_bottom` |
| 标题 | `title`、`title_size`、`title_color`、`title_weight`、`title_line_height`、`title_margin_bottom` |
| 描述 | `desc`、`desc_size`、`desc_color`、`desc_weight`、`desc_line_height`、`desc_opacity`、`desc_margin_bottom` |
| 按钮 | `btn_text`、`btn_url`、`btn_target`、`btn_bg`、`btn_color`、`btn_size`、`btn_weight`、`btn_radius`、`btn_padding`、`btn_hover_bg`、`btn_hover_color`、`btn_transition` |

---

### 4、模板源文件位置

| 文件 | 说明 |
|------|------|
| [template.html](../../../../site_templates/dengtec/blocks/section_title/template.html) | Block Jinja2 模板 |
| [meta.yaml](../../../../site_templates/dengtec/blocks/section_title/meta.yaml) | 当前已接入的字段定义 |
| [block-structure.md](block-structure.md) | 四层结构约定和共享字段定义 |

---

## 九、text_content

### 1、HTML 骨架

```html
<!-- ===== 文本内容模块 ===== -->
<div class="tc-block" style="">
  <h2 class="tc-title" style="">标题</h2>
  <div class="tc-body" style="">
    <p>段落文字...</p>
  </div>
</div>
```

**text_content 不使用 `.section-header`**。它有自己的标题体系，支持富文本正文和双栏排版（`columns: "2"` 时启用 CSS `column-count: 2`）。

### 2、内容区字段

#### 2.1 `.tc-block` — 根容器

**作用：** 文本内容区的根容器，控制文字排版、分栏和内边距。

**内联style中自定义的css属性：** text-align、column-count、column-gap、max-width、padding、background

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `text_align` | 文字排版 | select | `text-align` | `"left"` | `left` / `center` / `right` |
| `columns` | 分栏 | select | `column-count` | `"1"` | `1`=单栏 / `2`=双栏（CSS columns） |
| `column_gap` | 栏间距 | text | `column-gap` | `""` | 双栏时的栏间距，如 `3rem`（留空=CSS 默认 `2rem`） |
| `block_max_width` | 内容区最大宽度 | text | `max-width` | `""` | 如 `800px`（留空=全宽） |
| `block_padding` | 内容区内边距 | text | `padding` | `""` | 如 `2rem` |
| `block_background` | 内容区背景 | color | `background` | `""` | 如 `#fafafa` |

#### 2.2 `.tc-title` — 标题

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `title` | 标题文字 | text | — | `""` | **控制模块显隐** |
| `title_size` | 标题字号 | text | `font-size` | `""` | 如 `2rem` |
| `title_color` | 标题颜色 | color | `color` | `""` | 如 `#1e293b` |
| `title_weight` | 标题字重 | select | `font-weight` | `""` | `500` / `600` / `700` |
| `title_line_height` | 标题行高 | text | `line-height` | `""` | 如 `1.3` |
| `title_margin_bottom` | 标题下间距 | text | `margin-bottom` | `""` | 标题到正文的距离 |

#### 2.3 `.tc-body` — 正文

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `body` | 正文内容 | richtext | — | `""` | 富文本，支持 H2/H3/加粗/斜体/链接/换行 |
| `body_size` | 正文字号 | text | `font-size` | `""` | 如 `1rem` |
| `body_color` | 正文颜色 | color | `color` | `""` | 如 `#475569` |
| `body_weight` | 正文字重 | select | `font-weight` | `""` | 默认 `400` |
| `body_line_height` | 正文行高 | text | `line-height` | `""` | 如 `1.7` |
| `body_paragraph_gap` | 段落间距 | text | `margin-bottom` | `""` | `<p>` 之间的间距，如 `1rem` |

---

### 3、text_content 字段总览

| group | 包含字段 |
|-------|---------|
| 外层样式 | `section_bg`、`outer_width`、`margin_*` |
| 内层样式 | `inner_width`、`padding_*` |
| 内容排版 | `text_align`、`columns`、`column_gap`、`block_max_width`、`block_padding`、`block_background` |
| 标题 | `title`、`title_size`、`title_color`、`title_weight`、`title_line_height`、`title_margin_bottom` |
| 正文 | `body`、`body_size`、`body_color`、`body_weight`、`body_line_height`、`body_paragraph_gap` |

---

### 4、模板源文件位置

| 文件 | 说明 |
|------|------|
| [template.html](../../../../site_templates/dengtec/blocks/text_content/template.html) | Block Jinja2 模板 |
| [meta.yaml](../../../../site_templates/dengtec/blocks/text_content/meta.yaml) | 当前已接入的字段定义 |
| [block-structure.md](block-structure.md) | 四层结构约定和共享字段定义 |

---

## 十、stat_counter

### 1、HTML 骨架

```html
<!-- ===== 统计计数器 ===== -->
<div class="sc-grid" style="">
  <div class="sc-card" style="">
    <div class="sc-icon"><!-- SVG 图标 --></div>               <!-- 可选图标 -->
    <div class="sc-number" data-target="500">0</div>            <!-- 数字（滚动动画） -->
    <span class="sc-suffix">+</span>                            <!-- 可选后缀 -->
    <div class="sc-label">标签</div>
  </div>
  <!-- 更多 .sc-card ... -->
</div>
```

**stat_counter 使用 `.section-header`**（共享标题区）。数字通过 IntersectionObserver 触发滚动计数动画。

### 2、内容区字段

#### 2.1 `.sc-grid` — 网格容器

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `columns` | 每行列数 | select | `grid-template-columns` | `"4"` | `3`=三列 / `4`=四列 / `6`=六列 |
| `grid_gap` | 卡片间距 | text | `gap` | `""` | 如 `2rem` |
| `grid_row_gap` | 行间距 | text | `row-gap` | `""` | 仅控制行间距 |

#### 2.2 `.sc-card` — 统计卡片

**作用：** 单个统计项的容器，Flex 纵向居中排列。

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `card_bg` | 卡片背景 | color | `background` | `""` | 如 `#ffffff` |
| `card_padding` | 卡片内边距 | text | `padding` | `""` | 如 `1.5rem` |
| `card_radius` | 卡片圆角 | text | `border-radius` | `""` | 如 `12px` |
| `card_shadow` | 卡片阴影 | text | `box-shadow` | `""` | 如 `0 2px 8px rgba(0,0,0,0.06)` |

#### 2.3 `.sc-icon` — 图标

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `icon_size` | 图标尺寸 | text | `width`/`height` | `""` | 如 `48px` |
| `icon_color` | 图标颜色 | color | `color` | `""` | 如 `#067a7a` |
| `icon_margin_bottom` | 图标下间距 | text | `margin-bottom` | `""` | 图标到数字的距离 |

#### 2.4 `.sc-number` / `.sc-suffix` — 数字与后缀

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `number_size` | 数字字号 | text | `font-size` | `""` | 如 `3rem` |
| `number_color` | 数字颜色 | color | `color` | `""` | 如 `#1e293b` |
| `number_weight` | 数字字重 | select | `font-weight` | `""` | `600` / `700` / `800` |
| `number_font` | 数字字体 | text | `font-family` | `""` | 如 `'Georgia', serif` |
| `suffix_size` | 后缀字号 | text | `font-size` | `""` | 如 `2rem` |
| `suffix_color` | 后缀颜色 | color | `color` | `""` | 如 `#067a7a` |

#### 2.5 `.sc-label` — 标签文字

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `label_size` | 标签字号 | text | `font-size` | `""` | 如 `0.95rem` |
| `label_color` | 标签颜色 | color | `color` | `""` | 如 `#64748b` |
| `label_weight` | 标签字重 | select | `font-weight` | `""` | `400` / `500` |
| `label_margin_top` | 标签上间距 | text | `margin-top` | `""` | 数字到标签的距离 |

#### 2.6 数据字段（list 子项：`stats`）

| key | label | type | 说明 |
|-----|-------|------|------|
| `stats[].number` | 数字 | number | 目标数值，动画从 0 滚动到此值 |
| `stats[].suffix` | 后缀 | text | 如 `+`、`K`、`%` |
| `stats[].label` | 标签 | text | 数字下方的说明文字 |
| `stats[].icon` | 图标 | icon | 可选图标 |

---

### 3、stat_counter 字段总览

| group | 包含字段 |
|-------|---------|
| 外层样式 | `section_bg`、`outer_width`、`padding_*` |
| 内层样式 | `inner_width` |
| 标题区 | `title`、`subtitle` |
| 网格容器 | `columns`、`grid_gap`、`grid_row_gap` |
| 卡片 | `card_bg`、`card_padding`、`card_radius`、`card_shadow` |
| 图标 | `icon_size`、`icon_color`、`icon_margin_bottom` |
| 数字/后缀 | `number_size`、`number_color`、`number_weight`、`number_font`、`suffix_size`、`suffix_color` |
| 标签 | `label_size`、`label_color`、`label_weight`、`label_margin_top` |
| 数据源 | `stats`（`number`、`suffix`、`label`、`icon`） |

---

### 4、模板源文件位置

| 文件 | 说明 |
|------|------|
| [template.html](../../../../site_templates/dengtec/blocks/stat_counter/template.html) | Block Jinja2 模板 |
| [meta.yaml](../../../../site_templates/dengtec/blocks/stat_counter/meta.yaml) | 当前已接入的字段定义 |
| [block-structure.md](block-structure.md) | 四层结构约定和共享字段定义 |

---

## 十一、process_steps

### 1、HTML 骨架

```html
<!-- ===== 流程步骤 ===== -->
<div class="ps-track ps-track--horizontal" style="">
  <div class="ps-step" style="">
    <div class="ps-marker">
      <span class="ps-number" style="">1</span>                  <!-- 数字序号 -->
      <!-- 或 <div class="ps-icon"><svg>...</svg></div>         -->  <!-- 图标 -->
    </div>
    <!-- 纵向时用 .ps-body 包裹标题和描述 -->
    <h3 class="ps-title" style="">步骤标题</h3>
    <p class="ps-desc" style="">步骤描述</p>
  </div>
  <!-- 更多 .ps-step ... -->
</div>
```

**process_steps 使用 `.section-header`**（共享标题区）。支持横向（`grid-template-columns`）和纵向（`flex-direction: column`）两种排列。

### 2、内容区字段

#### 2.1 `.ps-track` — 步骤轨道

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `direction` | 排列方向 | select | `flex-direction` / `grid-template-columns` | `"horizontal"` | `horizontal`=横向 Grid / `vertical`=纵向 Flex |
| `step_style` | 步骤样式 | select | — | `"number"` | `number`=数字序号 / `icon`=SVG 图标 |
| `step_gap` | 步骤间距 | text | `gap` | `""` | 步骤之间的间距，如 `2rem` |

#### 2.2 `.ps-step` — 步骤容器

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `step_text_align` | 文字对齐 | select | `text-align` | `""` | `left` / `center` / `right` |
| `step_max_width` | 步骤最大宽度 | text | `max-width` | `""` | 如 `280px`（限制单步宽度） |

#### 2.3 `.ps-marker` — 标记区

**作用：** 序号或图标的容器，标记步骤顺序。

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `marker_size` | 标记尺寸 | text | `width`/`height` | `""` | 序号圆圈的大小，如 `48px` |
| `marker_margin_bottom` | 标记下间距 | text | `margin-bottom` | `""` | 标记到标题的距离 |

#### 2.4 `.ps-number` — 数字序号

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `number_bg` | 序号背景色 | color | `background-color` | `""` | 如 `#067a7a` |
| `number_color` | 序号字体色 | color | `color` | `""` | 如 `#ffffff` |
| `number_font_size` | 序号字号 | text | `font-size` | `""` | 如 `1.5rem` |
| `number_weight` | 序号字重 | select | `font-weight` | `""` | `600` / `700` |

#### 2.5 `.ps-icon` — 图标（`step_style: icon` 时使用）

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `icon_color` | 图标颜色 | color | `color` | `""` | 如 `#067a7a` |
| `icon_size` | 图标尺寸 | text | `width`/`height` | `""` | 如 `32px` |

#### 2.6 `.ps-title` — 步骤标题

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `title_font_size` | 标题字号 | text | `font-size` | `""` | 如 `1.25rem` |
| `title_color` | 标题颜色 | color | `color` | `""` | 如 `#1e293b` |
| `title_weight` | 标题字重 | select | `font-weight` | `""` | `500` / `600` / `700` |
| `title_line_height` | 标题行高 | text | `line-height` | `""` | 如 `1.3` |
| `title_margin_bottom` | 标题下间距 | text | `margin-bottom` | `""` | 标题到描述的距离 |

#### 2.7 `.ps-desc` — 步骤描述

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `desc_font_size` | 描述字号 | text | `font-size` | `""` | 如 `0.95rem` |
| `desc_color` | 描述颜色 | color | `color` | `""` | 如 `#64748b` |
| `desc_weight` | 描述字重 | select | `font-weight` | `""` | 默认 `400` |
| `desc_line_height` | 描述行高 | text | `line-height` | `""` | 如 `1.5` |

#### 2.8 数据字段（list 子项：`steps`）

| key | label | type | 说明 |
|-----|-------|------|------|
| `steps[].title` | 步骤标题 | text | 步骤名称 |
| `steps[].desc` | 步骤描述 | textarea | 步骤说明文字 |
| `steps[].icon` | 图标 | icon | 仅 `step_style: icon` 时使用 |

---

### 3、process_steps 字段总览

| group | 包含字段 |
|-------|---------|
| 外层样式 | `section_bg`、`outer_width` |
| 内层样式 | `inner_width`、`inner_bg`、`padding_*` |
| 标题区 | `title`、`subtitle` |
| 轨道 | `direction`、`step_style`、`step_gap` |
| 步骤容器 | `step_text_align`、`step_max_width` |
| 标记 | `marker_size`、`marker_margin_bottom` |
| 序号 | `number_bg`、`number_color`、`number_font_size`、`number_weight` |
| 图标 | `icon_color`、`icon_size` |
| 标题 | `title_font_size`、`title_color`、`title_weight`、`title_line_height`、`title_margin_bottom` |
| 描述 | `desc_font_size`、`desc_color`、`desc_weight`、`desc_line_height` |
| 数据源 | `steps`（`title`、`desc`、`icon`） |

---

### 4、模板源文件位置

| 文件 | 说明 |
|------|------|
| [template.html](../../../../site_templates/dengtec/blocks/process_steps/template.html) | Block Jinja2 模板 |
| [meta.yaml](../../../../site_templates/dengtec/blocks/process_steps/meta.yaml) | 当前已接入的字段定义 |
| [block-structure.md](block-structure.md) | 四层结构约定和共享字段定义 |

---

## 十二、contact_info

### 1、HTML 骨架

```html
<!-- ===== 联系方式 ===== -->
<div class="ci-grid" style="">
  <div class="ci-card" style="">
    <div class="ci-icon"><svg>...</svg></div>                  <!-- 图标 -->
    <div class="ci-label">电话</div>                            <!-- 标签 -->
    <a href="tel:..." class="ci-value">号码</a>                 <!-- 值（可点击） -->
  </div>
  <!-- 电话 / 手机 / 邮箱 / 地址 / 营业时间 ... -->
</div>
```

**contact_info 使用 `.section-header`**（共享标题区）。数据自动从 `settings.contact` 读取（电话/手机/邮箱/地址/营业时间），通过 `show_*` 字段控制各项目显隐。

### 2、内容区字段

#### 2.1 `.ci-grid` — 网格容器

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `grid_columns` | 每行列数 | select | `grid-template-columns` | `""` | `3`=三列 / `4`=四列（留空=CSS 默认自适应） |
| `grid_gap` | 卡片间距 | text | `gap` | `""` | 如 `2rem` |

#### 2.2 `.ci-card` — 联系方式卡片

**作用：** 单个联系方式的容器（图标 + 标签 + 值）。

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `card_bg` | 卡片背景 | color | `background` | `""` | 如 `#ffffff` |
| `card_padding` | 卡片内边距 | text | `padding` | `""` | 如 `1.5rem` |
| `card_radius` | 卡片圆角 | text | `border-radius` | `""` | 如 `12px` |
| `card_shadow` | 卡片阴影 | text | `box-shadow` | `""` | 如 `0 1px 4px rgba(0,0,0,0.06)` |
| `card_text_align` | 卡片文字对齐 | select | `text-align` | `""` | `left` / `center` / `right` |

#### 2.3 `.ci-icon` — 图标

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `icon_size` | 图标尺寸 | text | `width`/`height` | `""` | 如 `32px` |
| `icon_color` | 图标颜色 | color | `color` | `""` | 如 `#067a7a` |
| `icon_margin_bottom` | 图标下间距 | text | `margin-bottom` | `""` | 图标到标签的距离 |

#### 2.4 `.ci-label` — 标签

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `label_size` | 标签字号 | text | `font-size` | `""` | 如 `0.85rem` |
| `label_color` | 标签颜色 | color | `color` | `""` | 如 `#64748b` |
| `label_weight` | 标签字重 | select | `font-weight` | `""` | `400` / `500` |

#### 2.5 `.ci-value` — 值

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `value_size` | 值字号 | text | `font-size` | `""` | 如 `1.1rem` |
| `value_color` | 值颜色 | color | `color` | `""` | 如 `#1e293b` |
| `value_weight` | 值字重 | select | `font-weight` | `""` | `500` / `600` |

#### 2.6 显隐控制

| key | label | type | default | 说明 |
|-----|-------|------|---------|------|
| `show_phone` | 显示电话 | select | `"true"` | `true` / `false` |
| `show_mobile` | 显示手机 | select | `"true"` | `true` / `false` |
| `show_email` | 显示邮箱 | select | `"true"` | `true` / `false` |
| `show_address` | 显示地址 | select | `"true"` | `true` / `false` |
| `show_business_hours` | 显示营业时间 | select | `"false"` | `true` / `false`（默认隐藏） |

---

### 3、contact_info 字段总览

| group | 包含字段 |
|-------|---------|
| 外层样式 | `section_bg`、`outer_width`、`padding_*` |
| 内层样式 | `inner_width` |
| 标题区 | `title`、`subtitle` |
| 网格容器 | `grid_columns`、`grid_gap` |
| 卡片 | `card_bg`、`card_padding`、`card_radius`、`card_shadow`、`card_text_align` |
| 图标 | `icon_size`、`icon_color`、`icon_margin_bottom` |
| 标签 | `label_size`、`label_color`、`label_weight` |
| 值 | `value_size`、`value_color`、`value_weight` |
| 显隐控制 | `show_phone`、`show_mobile`、`show_email`、`show_address`、`show_business_hours` |

---

### 4、模板源文件位置

| 文件 | 说明 |
|------|------|
| [template.html](../../../../site_templates/dengtec/blocks/contact_info/template.html) | Block Jinja2 模板 |
| [meta.yaml](../../../../site_templates/dengtec/blocks/contact_info/meta.yaml) | 当前已接入的字段定义 |
| [block-structure.md](block-structure.md) | 四层结构约定和共享字段定义 |

---

## 十三、contact_form

### 1、HTML 骨架

```html
<!-- ===== 联系表单 ===== -->
<!-- 单栏模式：仅表单 -->
<form class="cf-form" action="..." method="POST" style="">
  <div class="cf-form-inner" style="">                           <!-- 表单内层（背景/圆角/内边距） -->
    <div class="cf-field">
      <label class="cf-label" style="">姓名</label>
      <input type="text" name="name" class="cf-input" style="">
    </div>
    <!-- 邮箱 / 电话 / 公司 / 留言 ... -->
    <div class="cf-actions" style="">
      <button type="submit" class="cf-btn" style="">发送留言</button>
    </div>
  </div>
</form>

<!-- 双栏模式：表单 + 地图 -->
<div class="cf-layout">
  <div class="cf-form-col" style=""><!-- 表单（同上） --></div>
  <div class="cf-map-col" style="">
    <iframe class="cf-map-iframe" src="..." style=""></iframe>
  </div>
</div>
```

**contact_form 使用 `.section-header`**（共享标题区）。支持单栏（仅表单）和双栏（表单 + 地图）两种布局。

### 2、内容区字段

#### 2.1 `.cf-layout` — 双栏布局容器（有地图时）

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `layout` | 排版方式 | select | — | `"form_left"` | `form_left`=表单左地图右 / `form_right`=地图左表单右 |
| `map_width_ratio` | 地图占比 | select | `flex-basis` | `"40"` | `30`~`70`，表单自动占剩余空间 |
| `layout_gap` | 栏间距 | text | `gap` | `""` | 表单与地图之间的间距，如 `2rem` |

#### 2.2 `.cf-form` — 表单元素

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `form_action` | 表单提交地址 | url | `action` | `""` | 如 `https://formspree.io/f/your-form-id` |
| `submit_text` | 按钮文字 | text | — | `"发送留言"` | 提交按钮文字 |
| `field_gap` | 字段间距 | text | `gap` | `""` | 各字段之间的间距 |
| `form_max_width` | 表单最大宽度 | text | `max-width` | `""` | 如 `600px` |
| `form_margin_top` | 表单上外边距 | text | `margin-top` | `""` | 表单到标题区的距离 |
| `form_margin_bottom` | 表单下外边距 | text | `margin-bottom` | `""` | 表单底部外边距 |
| `form_margin_left` | 表单左外边距 | text | `margin-left` | `""` | 配合居中时使用 `auto` |
| `form_margin_right` | 表单右外边距 | text | `margin-right` | `""` | 配合居中时使用 `auto` |

#### 2.3 `.cf-form-inner` — 表单内层

**作用：** 包裹所有字段，控制表单整体的背景/圆角/内边距。

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `form_bg` | 表单背景色 | color | `background` | `""` | 如 `#ffffff` |
| `form_radius` | 表单圆角 | text | `border-radius` | `""` | 如 `12px` |
| `form_padding_top` | 表单上内边距 | text | `padding-top` | `""` | 如 `2rem` |
| `form_padding_right` | 表单右内边距 | text | `padding-right` | `""` | 如 `2rem` |
| `form_padding_bottom` | 表单下内边距 | text | `padding-bottom` | `""` | 如 `2rem` |
| `form_padding_left` | 表单左内边距 | text | `padding-left` | `""` | 如 `2rem` |

#### 2.4 `.cf-label` — 字段标签

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `label_style` | 标签排版 | select | — | `"top"` | `top`=标签在上 / `left`=标签在左 / `hidden`=隐藏 |
| `title_size` | 标签字号 | text | `font-size` | `""` | 如 `1rem` |
| `text_color` | 标签/文字颜色 | color | `color` | `""` | 同时影响标签和输入框文字颜色 |
| `label_weight` | 标签字重 | select | `font-weight` | `""` | `400` / `500` / `600` |
| `label_margin_bottom` | 标签下间距 | text | `margin-bottom` | `""` | 标签到输入框的距离 |

#### 2.5 `.cf-input` — 输入框

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `input_height` | 输入框高度 | text | `height` | `""` | 如 `48px` |
| `input_bg` | 输入框背景 | color | `background` | `""` | 如 `#ffffff` |
| `input_border` | 输入框边框色 | color | `border-color` | `""` | 如 `#e5e7eb` |
| `input_radius` | 输入框圆角 | text | `border-radius` | `""` | 如 `8px` |
| `input_font_size` | 输入框字号 | text | `font-size` | `""` | 如 `1rem` |
| `input_padding` | 输入框内边距 | text | `padding` | `""` | 如 `0 16px` |
| `input_focus_border` | 聚焦边框色 | color | `border-color` | `""` | 输入框获得焦点时的边框色 |
| `input_focus_shadow` | 聚焦阴影 | text | `box-shadow` | `""` | 如 `0 0 0 3px rgba(6,122,122,0.15)` |
| `input_transition` | 输入框过渡 | text | `transition` | `""` | 如 `border-color 0.2s ease` |

#### 2.6 `.cf-btn` — 提交按钮

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `btn_bg` | 按钮背景色 | color | `background` | `""` | 如 `#067a7a` |
| `btn_color` | 按钮文字色 | color | `color` | `""` | 如 `#ffffff` |
| `btn_size` | 按钮字号 | text | `font-size` | `""` | 如 `1rem` |
| `btn_radius` | 按钮圆角 | text | `border-radius` | `""` | 如 `8px` |
| `btn_align` | 按钮位置 | select | `text-align` | `"left"` | `left` / `center` / `right` |
| `btn_weight` | 按钮字重 | select | `font-weight` | `""` | `500` / `600` |
| `btn_padding_top` | 按钮上内边距 | text | `padding-top` | `""` | 如 `0.75rem` |
| `btn_padding_right` | 按钮右内边距 | text | `padding-right` | `""` | 如 `2rem` |
| `btn_padding_bottom` | 按钮下内边距 | text | `padding-bottom` | `""` | 如 `0.75rem` |
| `btn_padding_left` | 按钮左内边距 | text | `padding-left` | `""` | 如 `2rem` |
| `btn_margin_top` | 按钮上外边距 | text | `margin-top` | `""` | 按钮到最后一个字段的距离 |
| `btn_hover_bg` | 悬停背景 | color | `background` | `""` | hover 态背景色 |
| `btn_hover_color` | 悬停字体色 | color | `color` | `""` | hover 态文字颜色 |
| `btn_transition` | 按钮过渡 | text | `transition` | `""` | 如 `all 0.3s ease` |
| `btn_full_width` | 全宽按钮 | select | `width` | `""` | `true`=100% 宽度 / `false`=自适应宽度 |

#### 2.7 地图区

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `show_map` | 显示地图 | select | — | `"false"` | `true` / `false` |
| `map_src` | 地图嵌入地址 | url | `src` | `""` | iframe src（高德/Google Maps） |
| `map_height` | 地图高度 | text | `height` | `""` | 如 `500px` |
| `map_radius` | 地图圆角 | text | `border-radius` | `""` | 如 `12px` |
| `map_border` | 地图边框 | text | `border` | `""` | 如 `1px solid #e5e7eb` |
| `map_shadow` | 地图阴影 | text | `box-shadow` | `""` | 如 `0 2px 8px rgba(0,0,0,0.08)` |
| `map_margin_top` | 地图栏上外边距 | text | `margin-top` | `""` | 地图栏外边距 |
| `map_margin_bottom` | 地图栏下外边距 | text | `margin-bottom` | `""` | 地图栏外边距 |
| `map_padding_top` | 地图栏上内边距 | text | `padding-top` | `""` | 地图栏内边距 |
| `map_padding_bottom` | 地图栏下内边距 | text | `padding-bottom` | `""` | 地图栏内边距 |

#### 2.8 字段显隐控制

| key | label | type | default | 说明 |
|-----|-------|------|---------|------|
| `show_form` | 显示表单 | select | `"true"` | `true` / `false`（仅要地图时关闭） |
| `show_name` | 显示姓名 | select | `"true"` | `true` / `false` |
| `show_email` | 显示邮箱 | select | `"true"` | `true` / `false` |
| `show_phone` | 显示电话 | select | `"true"` | `true` / `false` |
| `show_company` | 显示公司 | select | `"false"` | `true` / `false`（默认隐藏） |
| `show_message` | 显示留言 | select | `"true"` | `true` / `false` |

---

### 3、contact_form 字段总览

| group | 包含字段 |
|-------|---------|
| 外层样式 | `section_bg`、`outer_width`、`margin_*` |
| 内层样式 | `inner_width`、`padding_*` |
| 标题区 | `title`、`subtitle` |
| 双栏布局 | `layout`、`map_width_ratio`、`layout_gap` |
| 表单元素 | `form_action`、`submit_text`、`field_gap`、`form_max_width`、`form_margin_*` |
| 表单内层 | `form_bg`、`form_radius`、`form_padding_*` |
| 标签 | `label_style`、`title_size`、`text_color`、`label_weight`、`label_margin_bottom` |
| 输入框 | `input_height`、`input_bg`、`input_border`、`input_radius`、`input_font_size`、`input_padding`、`input_focus_border`、`input_focus_shadow`、`input_transition` |
| 按钮 | `btn_bg`、`btn_color`、`btn_size`、`btn_radius`、`btn_align`、`btn_weight`、`btn_padding_*`、`btn_margin_top`、`btn_hover_bg`、`btn_hover_color`、`btn_transition`、`btn_full_width` |
| 地图 | `show_map`、`map_src`、`map_height`、`map_radius`、`map_border`、`map_shadow`、`map_margin_*`、`map_padding_*` |
| 字段显隐 | `show_form`、`show_name`、`show_email`、`show_phone`、`show_company`、`show_message` |

---

### 4、模板源文件位置

| 文件 | 说明 |
|------|------|
| [template.html](../../../../site_templates/dengtec/blocks/contact_form/template.html) | Block Jinja2 模板 |
| [meta.yaml](../../../../site_templates/dengtec/blocks/contact_form/meta.yaml) | 当前已接入的字段定义 |
| [block-structure.md](block-structure.md) | 四层结构约定和共享字段定义 |
