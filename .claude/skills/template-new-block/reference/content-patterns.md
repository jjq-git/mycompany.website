# 内容区模式参考

## 导航

| Block | 内容区结构 | 字段速查 |
|-------|-----------|---------|
| [一、highlight_card](#一highlight_card) | 图文并排 | [字段总览](#3字段总览按-group-分组) |
| [二、logo_cloud](#二logo_cloud) | 网格列表 | [字段总览](#3字段总览按-group-分组-1) |

> 外层（`.section`）、内层（`.container`）、标题区（`.section-header`）的字段定义见 [block-structure.md](block-structure.md)，本文档仅列出内容区专属字段。


## 一、highlight_card

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

按 HTML 结构从上到下、从外到内展开。

### 2.1 `.hl-grid` 

**作用：** 内容区根容器，用 Grid 将内容分为左右两栏（`.hl-image` 图片侧 + `.hl-text` 文字侧）。

**内联style中自定义的css属性：** border-radius、gap、min-height、background

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `border_radius` | 整体圆角 | text | `border-radius` | `""` | 整个 hl-grid 的圆角，如 `12px` |
| `image_position` | 图文左右位置 | select | — | `"left"` | `left`=图左文右（默认）；`right`=添加 `.hl-grid--reverse` class |
| `content_gap` | 图文间距 | text | `gap` | `""` | `.hl-image` 与 `.hl-text` 之间的间距，如 `2rem` |
| `grid_min_height` | 最小高度 | text | `min-height` | `""` | 保证卡片高度统一，如 `400px` |
| `grid_background` | 整体背景色 | color | `background` | `""` | 图片和文字两栏的共同底色 |

### 2.2 `.hl-image` — 图片侧

**作用：** 图片展示区，占据左栏（或右栏），承载产品图/配图，图片通过 `<img>` 标签加载。

**内联style中自定义的css属性：** width、height、object-fit、border-radius、background-color、aspect-ratio、object-position、opacity

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `image` | 图片 | image / text | `src` | — | 图片 URL，支持上传或手工填写 |
| `image_width` | 图片区宽度 | text | `width` | `""` | 如 `50%`（占 hl-grid 的一半）或 `600px` |
| `image_height` | 图片区高度 | text | `height` | `""` | 如 `400px`，留空自适应用 `object-fit: cover` |
| `image_aspect_ratio` | 图片区宽高比 | text | `aspect-ratio` | `""` | 如 `16/9`、`4/3`，比直接设 height 更灵活 |
| `image_fit` | 图片填充方式 | select | `object-fit` | `"cover"` | `cover`=裁剪填充 / `contain`=完整显示 / `fill`=拉伸 |
| `image_position_obj` | 图片焦点位置 | select | `object-position` | `"center"` | `top` / `center` / `bottom` / `left`，配合 `cover` 裁剪时指定保留区域 |
| `image_radius` | 图片圆角 | text | `border-radius` | `""` | 如图片需要独立于 hl-grid 的圆角值，如 `12px 0 0 12px` |
| `image_bg` | 图片区背景色 | color | `background-color` | `""` | 图片加载前或透明图时的占位背景色 |
| `image_opacity` | 图片透明度 | text | `opacity` | `""` | 如 `0.8`，用于叠加文字或弱化图片 |

### 2.3 `.hl-text` — 文字侧外层

**作用：** 文字内容区，Flex 纵向排列子元素（标签 → 标题 → 描述 → 功能列表 → 按钮），图文模块的核心信息所在。

**内联style中自定义的css属性：** background、color、padding、text-align、gap、justify-content

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `text_bg` | 文字区背景色 | color | `background` | `""` | 覆盖整个文字侧的背景色，如 `#f9fafb` |
| `text_color` | 文字区字体色 | color | `color` | `""` | 文字侧基准颜色，`.hl-title` / `.hl-desc` / `.hl-features` 默认继承此值 |
| `text_padding` | 文字区内边距 | text | `padding` | `"2rem"` | 统一四边内边距；如需独立四边，拆为 `text_padding_top` 等 |
| `text_gap` | 子元素间距 | text | `gap` | `""` | 标签/标题/描述/列表/按钮之间的统一间距，如 `1rem` |
| `text_align` | 文字侧水平对齐 | select | `text-align` | `"left"` | `left` / `center` / `right` |
| `text_justify` | 文字侧垂直对齐 | select | `justify-content` | `"center"` | `flex-start`=顶部对齐 / `center`=居中 / `flex-end`=底部对齐 / `space-between`=两端分散 |

### 2.4 `.hl-tag` — 标签

**作用：** 分类标签（可选），位于标题上方，用于标识模块主题（如"核心优势""新功能"），留空则不渲染。

**内联style中自定义的css属性：** background、color、font-size、font-weight、border-radius、padding、margin-bottom、text-transform、letter-spacing

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `tag` | 标签文字 | text | — | `""` | 标签文本内容，留空则整个标签不渲染 |
| `tag_bg` | 标签背景色 | color | `background` | `""` | 如 `#067a7a`（留空=默认主色） |
| `tag_color` | 标签字体色 | color | `color` | `""` | 如 `#ffffff`（留空=白色） |
| `tag_size` | 标签字号 | text | `font-size` | `""` | 如 `0.75rem`（留空=CSS 默认） |
| `tag_weight` | 标签字重 | select | `font-weight` | `""` | `400` / `500` / `600` / `700` |
| `tag_transform` | 文字变换 | select | `text-transform` | `""` | `uppercase`（全大写）/ `none`（原文）/ `capitalize`（首字母大写） |
| `tag_letter_spacing` | 字间距 | text | `letter-spacing` | `""` | 如 `0.05em`，配合 uppercase 使用效果更好 |
| `tag_radius` | 标签圆角 | text | `border-radius` | `""` | 如 `4px` 或 `999px`（胶囊形） |
| `tag_padding` | 标签内边距 | text | `padding` | `""` | 如 `4px 12px` |
| `tag_margin_bottom` | 标签下间距 | text | `margin-bottom` | `""` | 标签到标题的距离，如 `8px` |

### 2.5 `.hl-title` — 标题

**作用：** 模块主标题，控制整个模块的显隐（留空则模块不渲染），位于标签下方、描述上方。

**内联style中自定义的css属性：** font-size、color、font-weight、text-align、margin-bottom、line-height

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `title` | 标题文字 | text | — | `""` | **控制整个模块显隐**：不录入则不渲染模块 |
| `title_size` | 标题字号 | text | `font-size` | `""` | 如 `1.5rem`（留空=CSS 默认） |
| `title_color` | 标题颜色 | color | `color` | `""` | 独立于 `text_color`，如 `#1e293b` |
| `title_weight` | 标题字重 | select | `font-weight` | `""` | `400` / `500` / `600` / `700`（默认加粗） |
| `title_line_height` | 标题行高 | text | `line-height` | `""` | 如 `1.3`，多行标题时控制行间距 |
| `title_align` | 标题对齐 | select | `text-align` | `""` | 继承 `text_align`；可独立设置 `left` / `center` / `right` |
| `title_margin_bottom` | 标题下间距 | text | `margin-bottom` | `""` | 标题到描述的距离，如 `12px` |

### 2.6 `.hl-desc` — 描述

**作用：** 标题下方的补充说明文字，对模块内容做进一步解释。

**内联style中自定义的css属性：** font-size、color、font-weight、line-height、margin-bottom、opacity

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `desc` | 描述文字 | textarea | — | `""` | 标题下方的说明文字，留空则不渲染 |
| `desc_size` | 描述字号 | text | `font-size` | `""` | 如 `1rem`（留空=CSS 默认） |
| `desc_color` | 描述颜色 | color | `color` | `""` | 独立于 `text_color`，如 `#64748b` |
| `desc_weight` | 描述字重 | select | `font-weight` | `""` | 默认 `400`（常规） |
| `desc_line_height` | 描述行高 | text | `line-height` | `""` | 如 `1.6`（留空=CSS 默认） |
| `desc_opacity` | 描述透明度 | text | `opacity` | `""` | 如 `0.8`，弱化描述文字的视觉权重 |
| `desc_margin_bottom` | 描述下间距 | text | `margin-bottom` | `""` | 描述到功能列表的距离，如 `16px` |

### 2.7 `.hl-features` — 功能点列表

**作用：** 产品卖点/特性列表，每条带 ✓ 图标，位于描述下方。

**内联style中自定义的css属性：** color、font-size、gap、margin-bottom、line-height

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `features` | 功能点列表 | list | — | `[]` | 每条一项，渲染为 `<li>✓ 文本</li>`，空数组则不渲染 |
| `features_color` | 功能点颜色 | color | `color` | `""` | 独立于 `text_color` |
| `features_size` | 功能点字号 | text | `font-size` | `""` | 如 `0.95rem` |
| `features_line_height` | 功能点行高 | text | `line-height` | `""` | 如 `1.5`，控制列表项内部行间距 |
| `features_gap` | 功能点间距 | text | `gap` | `""` | `<li>` 之间的间距，如 `8px` |
| `features_icon_color` | ✓ 图标颜色 | color | `color` | `""` | ✓ 字符的颜色，独立于文字颜色 |
| `features_icon_size` | ✓ 图标字号 | text | `font-size` | `""` | ✓ 字符的字号，如 `1rem` |
| `features_margin_bottom` | 功能列表下间距 | text | `margin-bottom` | `""` | 列表到按钮区的距离，如 `20px` |

### 2.8 `.hl-actions` — 按钮区

**作用：** 按钮容器，横向排列主按钮和副按钮，位于功能列表下方。

**内联style中自定义的css属性：** gap、justify-content、margin-top、flex-wrap

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `actions_gap` | 按钮间距 | text | `gap` | `""` | 主按钮与副按钮之间的间距，如 `12px` |
| `actions_align` | 按钮区对齐 | select | `justify-content` | `""` | `flex-start` / `center` / `flex-end` |
| `actions_margin_top` | 按钮区上间距 | text | `margin-top` | `""` | 按钮区到功能列表的距离，如 `24px` |
| `actions_wrap` | 允许换行 | select | `flex-wrap` | `""` | `wrap`=按钮多时换行 / `nowrap`=不换行 |

### 2.9 `.hl-btn--primary` / `.hl-btn--secondary` — 按钮

**作用：** CTA 按钮。主按钮（`.hl-btn--primary`）引导核心操作如"预约演示"；副按钮（`.hl-btn--secondary`）提供辅助跳转如"了解更多"。

**内联style中自定义的css属性：** background、color、font-size、font-weight、border-radius、padding、border-color、transition

| key | label | type | 目标元素 | CSS 属性 | default | 说明 |
|-----|-------|------|----------|----------|---------|------|
| `primaryBtn` | 主按钮文字 | text | `.hl-btn--primary` | — | `""` | 按钮文字，留空则主按钮不渲染 |
| `primaryLink` | 主按钮链接 | url | `.hl-btn--primary` | `href` | `""` | 按钮跳转地址 |
| `primaryLinkTarget` | 主按钮打开方式 | select | `.hl-btn--primary` | — | `""` | `""`=当前页 / `_blank`=新标签页 |
| `secondaryBtn` | 副按钮文字 | text | `.hl-btn--secondary` | — | `""` | 留空则副按钮不渲染 |
| `secondaryLink` | 副按钮链接 | url | `.hl-btn--secondary` | `href` | `""` | 副按钮跳转地址 |
| `btn_bg` | 主按钮背景色 | color | `.hl-btn--primary` | `background` | `""` | 如 `#067a7a` |
| `btn_color` | 主按钮字体色 | color | `.hl-btn--primary` | `color` | `""` | 如 `#ffffff` |
| `btn_size` | 按钮字号 | text | `.hl-btn` | `font-size` | `""` | 主/副按钮统一字号，如 `0.9rem` |
| `btn_weight` | 按钮字重 | select | `.hl-btn` | `font-weight` | `""` | `400` / `500` / `600` |
| `btn_radius` | 按钮圆角 | text | `.hl-btn` | `border-radius` | `""` | 如 `6px` 或 `999px`（胶囊按钮） |
| `btn_padding` | 按钮内边距 | text | `.hl-btn` | `padding` | `""` | 如 `10px 24px` |
| `btn_hover_bg` | 主按钮悬停背景 | color | `.hl-btn--primary:hover` | `background` | `""` | hover 态背景色 |
| `btn_hover_color` | 主按钮悬停字体色 | color | `.hl-btn--primary:hover` | `color` | `""` | hover 态文字颜色 |
| `btn_secondary_border` | 副按钮边框色 | color | `.hl-btn--secondary` | `border-color` | `""` | outline 样式，边框颜色如 `#067a7a` |
| `btn_secondary_color` | 副按钮字体色 | color | `.hl-btn--secondary` | `color` | `""` | 副按钮文字颜色 |
| `btn_secondary_hover_bg` | 副按钮悬停背景 | color | `.hl-btn--secondary:hover` | `background` | `""` | 悬停时填充背景，如 `#067a7a` |
| `btn_secondary_hover_color` | 副按钮悬停字体色 | color | `.hl-btn--secondary:hover` | `color` | `""` | 悬停时字体变白 |
| `btn_transition` | 按钮过渡动画 | text | `.hl-btn` | `transition` | `""` | 如 `all 0.2s ease`，悬停平滑过渡 |

---

### 3、字段总览（按 group 分组）

| group | 包含字段 |
|-------|---------|
| 外层样式 | `section_bg`, `outer_width`, `margin_top`, `margin_bottom`, `padding_top`, `padding_right`, `padding_bottom`, `padding_left` |
| 内层样式 | `inner_width` |
| 图文布局 | `image_position`, `border_radius`, `overflow`, `content_gap`, `grid_min_height`, `grid_background` |
| 图片 | `image`, `image_width`, `image_height`, `image_aspect_ratio`, `image_fit`, `image_position_obj`, `image_radius`, `image_bg`, `image_opacity` |
| 文字区 | `text_bg`, `text_color`, `text_padding`, `text_gap`, `text_align`, `text_justify` |
| 标签 | `tag`, `tag_bg`, `tag_color`, `tag_size`, `tag_weight`, `tag_transform`, `tag_letter_spacing`, `tag_radius`, `tag_padding`, `tag_margin_bottom` |
| 标题 | `title`, `title_size`, `title_color`, `title_weight`, `title_line_height`, `title_align`, `title_margin_bottom` |
| 描述 | `desc`, `desc_size`, `desc_color`, `desc_weight`, `desc_line_height`, `desc_opacity`, `desc_margin_bottom` |
| 功能列表 | `features`, `features_color`, `features_size`, `features_line_height`, `features_gap`, `features_icon_color`, `features_icon_size`, `features_margin_bottom` |
| 按钮区 | `actions_gap`, `actions_align`, `actions_margin_top`, `actions_wrap` |
| 按钮 | `primaryBtn`, `primaryLink`, `primaryLinkTarget`, `secondaryBtn`, `secondaryLink`, `btn_bg`, `btn_color`, `btn_size`, `btn_weight`, `btn_radius`, `btn_padding`, `btn_hover_bg`, `btn_hover_color`, `btn_secondary_border`, `btn_secondary_color`, `btn_secondary_hover_bg`, `btn_secondary_hover_color`, `btn_transition` |

---

### 4、模板源文件位置

| 文件 | 说明 |
|------|------|
| [template.html](../../../../site_templates/dengtec/blocks/highlight_card/template.html) | Block Jinja2 模板 |
| [meta.yaml](../../../../site_templates/dengtec/blocks/highlight_card/meta.yaml) | 当前已接入的字段定义 |
| [admin_modules.js](../../../../app/static/js/admin_modules.js) | 后台编辑表单（搜索 `highlight_card`） |
| [block-structure.md](block-structure.md) | 四层结构约定和共享字段定义 |

---

## 二、logo_cloud

### 1、HTML 骨架

```html
<!-- ===== 自定义内容区 .lc-grid ===== -->
<div class="lc-grid" style="">
    <!-- 每条 Logo 用一个 .lc-item，可选 <a> 链接或 <div> 容器 -->
    <a href="..." class="lc-item" style="" target="_blank">
        <img src="..." alt="品牌名" class="lc-logo lc-logo--grayscale" style="">
    </a>
    <!-- 更多 .lc-item ... -->
</div>
```

**logo_cloud 使用 `.section-header`**（共享标题区），字段走 [block-structure.md](block-structure.md) 的三、三-a、三-b。下文仅列出内容区专属字段。

### 2、内容区字段

按 HTML 结构从上到下、从外到内展开。

### 2.1 `.lc-grid` — Logo 网格容器

**作用：** Logo 网格的根容器，用 CSS Grid 按列数排列 Logo 卡片。

**内联style中自定义的css属性：** grid-template-columns、gap、align-items、padding、row-gap

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `columns` | 每行列数 | select | `grid-template-columns` | `"4"` | `4`=四列 / `5`=五列 / `6`=六列，渲染为 `repeat(N, 1fr)` |
| `grid_gap` | 网格间距 | text | `gap` | `""` | Logo 卡片之间的统一间距，如 `2rem`（留空=CSS 默认 `1.5rem`） |
| `grid_row_gap` | 行间距 | text | `row-gap` | `""` | 仅控制行与行之间的间距，如 `2rem`（留空=跟随 `grid_gap`） |
| `grid_align` | 垂直对齐 | select | `align-items` | `""` | `center`=居中（默认）/ `start`=顶部 / `stretch`=拉伸 |
| `grid_padding` | 网格内边距 | text | `padding` | `""` | 网格容器内部边距，如 `2rem`（留空=无） |

### 2.2 `.lc-item` — Logo 卡片

**作用：** 单个 Logo 的容器，flex 居中显示 Logo 图片。如果配置了 `link` 则为 `<a>` 标签（可点击跳转），否则为 `<div>`。

**内联style中自定义的css属性：** background-color、border、border-radius、width、height、padding、box-shadow、transform、transition

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `logo_bg` | 卡片背景色 | color | `background-color` | `""` | 如 `#f8fafc`（留空=透明） |
| `logo_border` | 卡片边框 | text | `border` | `""` | 如 `1px solid #e5e7eb`（留空=无边框） |
| `logo_border_color` | 卡片边框色 | color | `border-color` | `""` | 快捷设置边框颜色（自动补全 `1px solid`），如 `#e5e7eb` |
| `logo_radius` | 卡片圆角 | text | `border-radius` | `""` | 如 `8px`（留空=CSS 默认） |
| `logo_width` | 卡片宽度 | text | `width` | `""` | 如 `120px`（留空=自适应网格列宽） |
| `logo_height` | 卡片高度 | text | `height` | `""` | 如 `80px`（留空=由 padding + 图片撑开） |
| `logo_padding` | 卡片内边距 | text | `padding` | `""` | 如 `1.5rem`（留空=CSS 默认 `1rem`） |
| `logo_shadow` | 卡片阴影 | text | `box-shadow` | `""` | 如 `0 2px 8px rgba(0,0,0,0.08)`（留空=无阴影） |
| `logo_hover_shadow` | hover 阴影 | text | `box-shadow` | `""` | 鼠标悬停时的阴影，如 `0 4px 16px rgba(0,0,0,0.12)` |
| `logo_hover_scale` | hover 放大 | text | `transform` | `""` | 鼠标悬停时的缩放比例，如 `1.05`（渲染为 `scale(1.05)`） |
| `logo_hover_bg` | hover 背景色 | color | `background-color` | `""` | 鼠标悬停时卡片的背景色变化 |
| `logo_transition` | 过渡动画 | text | `transition` | `""` | 控制 hover 效果的平滑过渡，如 `all 0.3s ease` |

### 2.3 `.lc-logo` — Logo 图片

**作用：** Logo 图片本身，支持灰度滤镜和 hover 动效。通过 `.lc-logo--grayscale` class 控制滤镜状态。

**内联style中自定义的css属性：** filter、max-width、max-height、object-fit、opacity

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `logos` | Logo 列表 | list | — | `[]` | 数据来源，每条含 `image`（图片）、`name`（品牌名）、`link`（可选跳转链接） |
| `grayscale` | 灰度滤镜 | select | `filter` | `"true"` | `true`=灰度 + 半透明，hover 恢复彩色 / `false`=保持原色 |
| `logo_max_width` | 图片最大宽度 | text | `max-width` | `""` | 如 `120px`，与 `logo_max_height` 配合控制图片尺寸上限 |
| `logo_max_height` | 图片最大高度 | text | `max-height` | `""` | 如 `60px`（留空=CSS 默认 `60px`） |
| `logo_object_fit` | 图片填充方式 | select | `object-fit` | `""` | `contain`=完整显示（默认）/ `cover`=裁剪 / `scale-down`=缩小 |
| `logo_opacity` | 灰度时透明度 | text | `opacity` | `""` | 灰度模式下图片透明度，如 `0.6`（留空=CSS 默认） |

### 2.4 数据字段（list 子项：`logos`）

| key | label | type | 说明 |
|-----|-------|------|------|
| `logos[].image` | Logo 图片 | image | Logo 图片 URL |
| `logos[].name` | 品牌名称 | text | 用于 `alt` 和 `title` 属性 |
| `logos[].link` | 链接（可选）| url | 留空则渲染为 `<div>`，填写则渲染为 `<a>` 标签新窗口打开 |

---

### 3、字段总览（按 group 分组）

| group | 包含字段 |
|-------|---------|
| 外层样式 | `section_bg`、`outer_width`（见 [block-structure.md](block-structure.md)） |
| 内层样式 | `inner_width`、`inner_bg`、`padding_top`、`padding_right`、`padding_bottom`、`padding_left`（见 [block-structure.md](block-structure.md)） |
| 标题区 | `title`、`subtitle`（见 [block-structure.md](block-structure.md) 三-a、三-b） |
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
