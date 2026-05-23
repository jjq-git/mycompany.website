# 内容区模式参考

下面以 `highlight_card`（图文模块）为例，完整展示内容区的 HTML 结构和所有可配置字段。

## 一、highlight_card HTML 骨架

<div style="display:flex;gap:20px;padding:20px;background:#6b7280;border-radius:6px;font-family:sans-serif;max-width:700px;">
  <!-- 图片侧 -->
  <div style="flex:1;background:#9ca3af;border-radius:4px;display:flex;align-items:center;justify-content:center;min-height:200px;color:#fff;font-size:13px;">图片区</div>
  <!-- 文字侧 -->
  <div style="flex:1;display:flex;flex-direction:column;gap:8px;color:#1f2937;">
    <span style="background:#374151;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;display:inline-block;width:fit-content;">标签</span>
    <div style="font-size:18px;font-weight:bold;color:#111827;">标题文字</div>
    <div style="font-size:13px;color:#4b5563;">描述文字，简要说明内容</div>
    <ul style="margin:0;padding-left:16px;font-size:12px;color:#374151;">
      <li>功能点一</li>
      <li>功能点二</li>
    </ul>
    <div style="display:flex;gap:8px;margin-top:4px;">
      <span style="background:#374151;color:#fff;padding:6px 16px;border-radius:4px;font-size:12px;">主按钮</span>
      <span style="border:1px solid #9ca3af;color:#374151;padding:6px 16px;border-radius:4px;font-size:12px;">副按钮</span>
    </div>
  </div>
</div>

**↑ 色块线框图：快速理解结构。↓ 实际渲染版：还原项目 CSS 的真实效果。**

<div style="display:grid;grid-template-columns:1fr 1fr;align-items:stretch;gap:0;border-radius:12px;overflow:hidden;font-family:sans-serif;">
  <!-- 图片侧 -->
  <div style="background:#e2e8f0;min-height:360px;overflow:hidden;display:flex;align-items:center;justify-content:center;">
    <div style="width:100%;height:100%;background:linear-gradient(135deg,#cbd5e1 0%,#94a3b8 100%);display:flex;align-items:center;justify-content:center;color:#64748b;font-size:14px;">产品图片</div>
  </div>
  <!-- 文字侧 -->
  <div style="display:flex;flex-direction:column;justify-content:center;gap:1rem;padding:2rem;color:#1e293b;">
    <span style="display:inline-block;padding:0.25rem 0.75rem;font-size:0.75rem;font-weight:600;text-transform:uppercase;background:#067a7a;color:#fff;border-radius:4px;width:fit-content;">核心优势</span>
    <h3 style="font-size:1.5rem;font-weight:700;line-height:1.3;color:#1e293b;margin:0;">一体化生产管理系统</h3>
    <p style="font-size:0.95rem;line-height:1.65;color:#64748b;margin:0;">帮助制造企业在数字化转型中实现高效协同，从订单到交付全流程可视化管控，降本增效一步到位。</p>
    <ul style="list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:0.5rem;">
      <li style="font-size:0.9rem;line-height:1.5;color:#334155;">✓ 实时订单追踪与智能排产</li>
      <li style="font-size:0.9rem;line-height:1.5;color:#334155;">✓ 多工厂数据互通，统一管控</li>
      <li style="font-size:0.9rem;line-height:1.5;color:#334155;">✓ 移动端随时查看生产进度</li>
    </ul>
    <div style="display:flex;gap:0.75rem;flex-wrap:wrap;margin-top:0.5rem;">
      <a style="display:inline-flex;align-items:center;padding:0.625rem 1.5rem;font-size:0.875rem;font-weight:600;border-radius:8px;background:#067a7a;color:#fff;border:none;text-decoration:none;">预约演示</a>
      <a style="display:inline-flex;align-items:center;padding:0.625rem 1.5rem;font-size:0.875rem;font-weight:600;border-radius:8px;background:transparent;border:1.5px solid #067a7a;color:#067a7a;text-decoration:none;">了解更多</a>
    </div>
  </div>
</div>

**highlight_card 不使用 `.section-header`**。标题区的概念由 `.hl-title` + `.hl-desc` 在内容区内部实现，见下方字段。

## 二、内容区字段（highlight_card 专属）

按 HTML 结构从上到下、从外到内展开。

### 2.1 `.hl-grid` — 图文整体容器

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `border_radius` | 整体圆角 | text | `border-radius` | `""` | 整个 hl-grid 的圆角，如 `12px` |
| `image_position` | 图文左右位置 | select | — | `"left"` | `left`=图左文右（默认）；`right`=添加 `.hl-grid--reverse` class（`flex-direction: row-reverse`） |
| `content_gap` | 图文间距 | text | `gap` | `""` | `.hl-image` 与 `.hl-text` 之间的间距，如 `2rem` |
| `grid_min_height` | 最小高度 | text | `min-height` | `""` | 保证卡片高度统一，如 `400px` |

### 2.2 `.hl-image` — 图片侧

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `image` | 图片 | image / text | `src` | — | 图片 URL，支持上传或手工填写 |
| `image_width` | 图片宽度 | text | `width` | `""` | 如 `50%`（占 hl-grid 的一半）或 `600px` |
| `image_height` | 图片高度 | text | `height` | `""` | 如 `400px`，留空自适应用 `object-fit: cover` |
| `image_fit` | 图片填充方式 | select | `object-fit` | `"cover"` | `cover`=裁剪填充 / `contain`=完整显示 / `fill`=拉伸 |
| `image_radius` | 图片圆角 | text | `border-radius` | `""` | 如图片需要独立于 hl-grid 的圆角值，如 `12px 0 0 12px` |
| `image_bg` | 图片区背景色 | color | `background-color` | `""` | 图片加载前或透明图时的占位背景色 |

### 2.3 `.hl-text` — 文字侧外层

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `text_bg` | 文字区背景色 | color | `background` | `""` | 覆盖整个文字侧的背景色，如 `#f9fafb` |
| `text_color` | 文字区字体色 | color | `color` | `""` | 文字侧基准颜色，`.hl-title` / `.hl-desc` / `.hl-features` 默认继承此值 |
| `text_padding` | 文字区内边距 | text | `padding` | `"2rem"` | 统一四边内边距；如需独立四边，拆为 `text_padding_top` 等 |
| `text_align` | 文字侧对齐 | select | `text-align` | `"left"` | `left` / `center` / `right` |

### 2.4 `.hl-tag` — 标签

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `tag` | 标签文字 | text | — | `""` | 标签文本内容，留空则整个标签不渲染 |
| `tag_bg` | 标签背景色 | color | `background` | `""` | 如 `#067a7a`（留空=默认主色） |
| `tag_color` | 标签字体色 | color | `color` | `""` | 如 `#ffffff`（留空=白色） |
| `tag_size` | 标签字号 | text | `font-size` | `""` | 如 `0.75rem`（留空=CSS 默认） |
| `tag_weight` | 标签字重 | select | `font-weight` | `""` | `400` / `500` / `600` / `700` |
| `tag_radius` | 标签圆角 | text | `border-radius` | `""` | 如 `4px` 或 `999px`（胶囊形） |
| `tag_padding` | 标签内边距 | text | `padding` | `""` | 如 `4px 12px` |
| `tag_margin_bottom` | 标签下间距 | text | `margin-bottom` | `""` | 标签到标题的距离，如 `8px` |

### 2.5 `.hl-title` — 标题

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `title` | 标题文字 | text | — | `""` | **控制整个模块显隐**：不录入则不渲染模块 |
| `title_size` | 标题字号 | text | `font-size` | `""` | 如 `1.5rem`（留空=CSS 默认） |
| `title_color` | 标题颜色 | color | `color` | `""` | 独立于 `text_color`，如 `#1e293b` |
| `title_weight` | 标题字重 | select | `font-weight` | `""` | `400` / `500` / `600` / `700`（默认加粗） |
| `title_align` | 标题对齐 | select | `text-align` | `""` | 继承 `text_align`；可独立设置 `left` / `center` / `right` |
| `title_margin_bottom` | 标题下间距 | text | `margin-bottom` | `""` | 标题到描述的距离，如 `12px` |

### 2.6 `.hl-desc` — 描述

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `desc` | 描述文字 | textarea | — | `""` | 标题下方的说明文字，留空则不渲染 |
| `desc_size` | 描述字号 | text | `font-size` | `""` | 如 `1rem`（留空=CSS 默认） |
| `desc_color` | 描述颜色 | color | `color` | `""` | 独立于 `text_color`，如 `#64748b` |
| `desc_weight` | 描述字重 | select | `font-weight` | `""` | 默认 `400`（常规） |
| `desc_line_height` | 描述行高 | text | `line-height` | `""` | 如 `1.6`（留空=CSS 默认） |
| `desc_margin_bottom` | 描述下间距 | text | `margin-bottom` | `""` | 描述到功能列表的距离，如 `16px` |

### 2.7 `.hl-features` — 功能点列表

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `features` | 功能点列表 | list | — | `[]` | 每条一项，渲染为 `<li>✓ 文本</li>`，空数组则不渲染 |
| `features_color` | 功能点颜色 | color | `color` | `""` | 独立于 `text_color` |
| `features_size` | 功能点字号 | text | `font-size` | `""` | 如 `0.95rem` |
| `features_gap` | 功能点间距 | text | `gap` | `""` | `<li>` 之间的间距，如 `8px`（推荐用 `gap` 配合 `flex` 或 `column-gap`） |
| `features_icon_color` | ✓ 图标颜色 | color | `color` | `""` | ✓ 字符的颜色，独立于文字颜色 |
| `features_margin_bottom` | 功能列表下间距 | text | `margin-bottom` | `""` | 列表到按钮区的距离，如 `20px` |

### 2.8 `.hl-actions` — 按钮区

| key | label | type | CSS 属性 | default | 说明 |
|-----|-------|------|----------|---------|------|
| `actions_gap` | 按钮间距 | text | `gap` | `""` | 主按钮与副按钮之间的间距，如 `12px` |
| `actions_align` | 按钮区对齐 | select | `justify-content` | `""` | `flex-start` / `center` / `flex-end` |

### 2.9 `.hl-btn--primary` / `.hl-btn--secondary` — 按钮

| key | label | type | 目标元素 | CSS 属性 | default | 说明 |
|-----|-------|------|----------|----------|---------|------|
| `primaryBtn` | 主按钮文字 | text | `.hl-btn--primary` | — | `""` | 按钮文字，留空则主按钮不渲染 |
| `primaryLink` | 主按钮链接 | url | `.hl-btn--primary` | `href` | `""` | 按钮跳转地址 |
| `primaryLinkTarget` | 主按钮打开方式 | select | `.hl-btn--primary` | — | `""` | `""`=当前页 / `_blank`=新标签页 |
| `secondaryBtn` | 副按钮文字 | text | `.hl-btn--secondary` | — | `""` | 留空则副按钮不渲染 |
| `secondaryLink` | 副按钮链接 | url | `.hl-btn--secondary` | `href` | `""` | 副按钮跳转地址 |
| `btn_bg` | 按钮背景色 | color | `.hl-btn--primary` | `background` | `""` | 主按钮背景色，如 `#067a7a` |
| `btn_color` | 按钮字体色 | color | `.hl-btn--primary` | `color` | `""` | 主按钮文字颜色，如 `#ffffff` |
| `btn_size` | 按钮字号 | text | `.hl-btn` | `font-size` | `""` | 主/副按钮统一字号，如 `0.9rem` |
| `btn_weight` | 按钮字重 | select | `.hl-btn` | `font-weight` | `""` | `400` / `500` / `600` |
| `btn_radius` | 按钮圆角 | text | `.hl-btn` | `border-radius` | `""` | 如 `6px` |
| `btn_padding` | 按钮内边距 | text | `.hl-btn` | `padding` | `""` | 如 `10px 24px` |
| `btn_hover_bg` | 按钮悬停背景 | color | `.hl-btn--primary:hover` | `background` | `""` | hover 态背景色（需模板层配合写出 `:hover` 规则） |
| `btn_secondary_border` | 副按钮边框色 | color | `.hl-btn--secondary` | `border-color` | `""` | 副按钮为 outline 样式，边框颜色如 `#067a7a` |
| `btn_secondary_color` | 副按钮字体色 | color | `.hl-btn--secondary` | `color` | `""` | 副按钮文字颜色 |

---

## 三、字段总览（按 group 分组）

| group | 包含字段 |
|-------|---------|
| 外层样式 | `section_bg`, `outer_width`, `margin_top`, `margin_bottom`, `padding_top`, `padding_right`, `padding_bottom`, `padding_left` |
| 内层样式 | `inner_width` |
| 图文布局 | `image_position`, `border_radius`, `content_gap`, `grid_min_height` |
| 图片 | `image`, `image_width`, `image_height`, `image_fit`, `image_radius`, `image_bg` |
| 文字区 | `text_bg`, `text_color`, `text_padding`, `text_align` |
| 标签 | `tag`, `tag_bg`, `tag_color`, `tag_size`, `tag_weight`, `tag_radius`, `tag_padding`, `tag_margin_bottom` |
| 标题 | `title`, `title_size`, `title_color`, `title_weight`, `title_align`, `title_margin_bottom` |
| 描述 | `desc`, `desc_size`, `desc_color`, `desc_weight`, `desc_line_height`, `desc_margin_bottom` |
| 功能列表 | `features`, `features_color`, `features_size`, `features_gap`, `features_icon_color`, `features_margin_bottom` |
| 按钮区 | `actions_gap`, `actions_align` |
| 按钮 | `primaryBtn`, `primaryLink`, `primaryLinkTarget`, `secondaryBtn`, `secondaryLink`, `btn_bg`, `btn_color`, `btn_size`, `btn_weight`, `btn_radius`, `btn_padding`, `btn_hover_bg`, `btn_secondary_border`, `btn_secondary_color` |

---

## 五、模板源文件位置

| 文件 | 说明 |
|------|------|
| [template.html](../../../site_templates/dengtec/blocks/highlight_card/template.html) | Block Jinja2 模板 |
| [meta.yaml](../../../site_templates/dengtec/blocks/highlight_card/meta.yaml) | 当前已接入的字段定义 |
| [admin_modules.js](../../../app/static/js/admin_modules.js) | 后台编辑表单（搜索 `highlight_card`） |
| [block-structure.md](block-structure.md) | 四层结构约定和共享字段定义 |
