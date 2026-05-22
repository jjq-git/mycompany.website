# Block 模板的结构约定速查

```html
<div class="builder-module" data-builder-module-index="2" data-builder-module-type="highlight_card"> <!-- 由 builder 框架在包装每个模块时自动注入，Block 模板不需要处理-->
  <!-- 样式走 inline style，有值才输出，空值不写让 CSS 变量兜底 -->
  <section class="section" style="">                                           <!-- ① 外层 -->
                                           
    <div class="container" style=""> 
      
      <div class="section-header">                                             <!-- ③ 标题区 -->
        <h2 class="section-title">...</h2>                                     <!-- 标题 -->
        <p class="section-description">...</p>                                 <!-- 副标题/描述 -->
      </div>
     
      <!-- 内容区(以列表为例) -->
      <div class="hl-grid">                                                    <!-- ④ 自定义内容区 -->
        <div class="hl-card">
          <img src="{{ item.icon }}" alt="">
          <h3>...</h3>
        </div>
        
      </div>
    </div>
  </section>
</div>
```

### ① 外层 .section

**作用：** 模块的最外层包装器，负责模块与模块之间的**间距**和**背景**。

| meta.yaml 字段 | CSS 属性 | 说明 |
|---------------|----------|------|
| `outer_width` | `max-width` | 外层最大宽度。留空使用全局宽度 |
| `margin_top` / `margin_right` / `margin_bottom` / `margin_left` | `margin` | 外层外边距（四边独立） |
| `padding_top` / `padding_right` / `padding_bottom` / `padding_left` | `padding` | 外层内边距（四边独立） |
| `section_bg` | `background` | 外层背景色 |

### ② 内层 .container

**作用：** 在模块内部限定**内容的展示宽度**，与外层解耦。

| meta.yaml 字段 | CSS 属性 | 说明 |
|---------------|----------|------|
| `inner_width` | `max-width` | 内层最大宽度。与外层 `outer_width` 独立：外层可铺满全屏，内层仅 800px 居中 |
| `inner_bg` | `background-color` | 内层背景色（process_steps / logo_cloud 使用） |
| `inner_margin_top` / `_right` / `_bottom` / `_left` | `margin` | 内层外边距（四边独立） |
| `inner_padding_top` / `_right` / `_bottom` / `_left` | `padding` | 内层内边距（四边独立） |


### ③ 标题区 .section-header

**作用：** 统一的区块标题区域，包含主标题和副标题。（不是所有 Block 都使用标题，视 Block 需求而定）

| meta.yaml 字段 | CSS 属性 | 说明 |
|---------------|----------|------|
| `text_align` | `text-align` | 标题区文字排版（left / center / right） |
| `header_margin_top` / `_bottom` 等 | `margin` | 标题区外边距 |
| `header_padding_top` / `_bottom` 等 | `padding` | 标题区内边距 |

### ③-a 主标题 .section-title

**作用：** Block 主标题（控制标题区显隐：不录入主标题则整个标题区不显示）

| meta.yaml 字段 | CSS 属性 | 说明 |
|---------------|----------|------|
| `title_size` 或 `title_font_size` | `font-size` | 标题字号 |
| `title_color` | `color` | 标题颜色 |
| `title_margin_top` / `_bottom` 等 | `margin` | 标题外边距 |
| `title_padding_top` / `_bottom` 等 | `padding` | 标题内边距 |

### ③-b 副标题 .section-description

**作用：** Block 副标题（永远放在主标题下方）

| meta.yaml 字段 | CSS 属性 | 说明 |
|---------------|----------|------|
| `desc_size` 或 `subtitle_size` 或 `desc_font_size` | `font-size` | 副标题字号 |
| `desc_color` 或 `subtitle_color` | `color` | 副标题颜色 |
| `desc_margin_top` / `_bottom` 等 | `margin` | 副标题外边距 |
| `desc_padding_top` / `_bottom` 等 | `padding` | 副标题内边距 |


### ④ 自定义内容区

**作用：** 每个 Block 的核心展示区域，结构完全由 Block 类型决定。

详见 **[内容区模式参考](content-patterns.md)**。


## 层 → 字段速查

| 层 | 对应 meta.yaml 字段 | 
|---|---|
| ① .section | `section_bg`, `outer_width`, `margin_*`, `padding_*`, `hero_height` 等 | 
| ② .container | `inner_width`, `inner_bg`, `inner_margin_*`, `inner_padding_*` | 
| ③ .section-header | `text_align`, `header_margin_*`, `header_padding_*` | 
| ③-a .section-title | `title_size`, `title_color`, `title_margin_*`, `title_padding_*` | 
| ③-b .section-description | `desc_size`, `desc_color`, `desc_margin_*`, `desc_padding_*` | 
| ④ 自定义内容区 | 视 Block 类型而定 | 见 [content-patterns.md](content-patterns.md) |

## 参考示例

参考 meta.yaml 字段：[data_grid/meta.yaml](../../../../site_templates/dengtec/blocks/data_grid/meta.yaml)
