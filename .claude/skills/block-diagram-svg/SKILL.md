---
name: block-diagram-svg
description: "为 Block 生成 HTML 骨架结构示意图 SVG"
---

当用户说"生成 SVG 示意图"、"画个结构图"、"做个 skeleton diagram"时触发。

读取 Block 的 `template.html`，分析 HTML 层级结构，生成可视化的 SVG 结构示意图，输出到 `site_templates/<template>/blocks/<name>/structure-diagram.svg`。

## 工作流程

1. **读取模板**：`site_templates/dengtec/blocks/<name>/template.html`
2. **提取 HTML 结构**：识别 `<section>` → `<div class="container">` → 自定义内容区的层级嵌套关系
3. **按规范生成 SVG**：遵循下文约定的颜色、字号、间距、布局
4. **写入文件**：`structure-diagram.svg` 放到 Block 目录下

## 参考示例

- [hero_banner 示例](reference/hero_banner.svg)
- [highlight_card 示例](reference/highlight_card.svg)

## 一、SVG 整体规范

### 画布

| 属性 | 值 |
|------|-----|
| `viewBox` | 宽 1540，高度按内容自适应（结构区 + 属性字段区 + 图例区） |
| 背景 | `fill="#fff" rx="4"` |
| 字体 | `font-family:"Microsoft YaHei","PingFang SC",sans-serif` |

### 标题栏

顶部横幅，y=0，h=50，`fill="#f0f2f5"`。

标题格式：`<block_name> — HTML 骨架 与 属性映射`

- `text-anchor="middle"`，x=画布宽/2，y=34
- `font-size="22" font-weight="bold" fill="#1a1a2e"`

## 二、层级颜色约定

所有 Block 共享统一的层级配色：

| 层级 | 元素 | 边框色 | 填充 | 标签色 |
|------|------|--------|------|--------|
| 最外层 | `.section` | `#5b8def` | `rgba(91,141,239,0.035)` | `#3b6fd4` |
| padding 区域 | `padding_*` | `#e74c3c` (半透明) | `rgba(231,76,60,0.13)` | `#c0392b` |
| 内层 | `.container` | `#27ae60` | 无 | `#1e7a45` |
| 内容区容器 | 视 Block 而定 | `#e67e22` | 无 | `#b8601f` |
| 媒体/图片区 | `.hl-image` 等 | `#6c5ce7` | 无 | `#5b4bc4` |
| 文字区 | `.hl-text` 等 | `#0984e3` | `rgba(9,132,227,0.025)` | `#0767b3` |
| 标签/按钮 | `.hl-tag` / `.btn` | — | `#067a7a` | `#fff`（内部文字） |
| 标题 | `.hl-title` 等 | `#d4a0a0` | 无 | — |
| 描述 | `.hl-desc` 等 | `#d4b890` | 无 | — |
| 功能列表 | `.hl-features` 等 | `#d4c870` / `#f1c40f` | 无 | — |
| 按钮区 | `.hl-actions` 等 | `#90c890` | 无 | — |
| 遮罩层 | `.hero-banner-overlay` | — | `rgba(0,0,0,0.3)` | — |
| 轮播/幻灯片 | `.hero-banner-slides` | `#d4a017` | 无 | `#9a760e` |
| 单个 slide | `.hero-banner-slide` | `#8b5cf6` | 无 | `#6d3fd6` |

### 边框样式

- `.section`：`stroke-dasharray="10 4" stroke-width="2"`
- `.container`：`stroke-dasharray="6 4" stroke-width="1.2"`
- 内容区容器：`stroke-width="1.3"`（实线或 `stroke-dasharray="5 3"`）
- 内部区块（hl-title / hl-desc 等）：`stroke-width="1"` 实线
- padding 区域：`stroke-width="0.5"`

## 三、核心层级结构（所有 Block 通用）

每个 Block 的 SVG 必须包含这三层，从外到内：

### 3.1 外层 `.section`

- 蓝色虚线大框，包裹整个模块
- 左上角标注 `.section`（`font-size="17"`，蓝色）
- 四边标注 padding 色块：
  - 顶部/底部：横向通栏，h=22-24
  - 左侧/右侧：纵向窄条，w=22-24
  - 标签文字居中放置在色块内，`font-size="15-16"`，红棕色粗体
- section 右侧标注 `hero_width` 或其他专属宽度字段（如有）

### 3.2 内层 `.container`

- 绿色虚线框，嵌套在 padding 内部
- 左上角标注 `.container`（`font-size="17"`，绿色）

### 3.3 标题区 `.section-header`（可选）

如果 Block 使用了 `.section-header`（如 `section_title`、`feature_grid`），在 container 内部画出标题区：
- 灰色矩形区域
- 包含 `.section-title`（主标题）和 `.section-description`（副标题）
- 颜色参考 builder-module-structure.svg

### 3.4 自定义内容区

每个 Block 的核心差异区域。根据 template.html 中的实际 HTML 结构绘制。

## 四、字号规范

| 元素 | 字号 |
|------|------|
| 标题栏 | `22` |
| 层级标签（.section / .container / .hl-grid） | `16-17` |
| padding 标签 | `15-16` |
| 内容区子元素标签（.hl-title / .hl-image 等） | `16` |
| 内容区内部文字（示例文本） | `15-19` |
| 主标题示例文本 | `22-23` |
| 属性字段卡片标题 | `16` |
| 属性字段卡片内容 | `15` |
| 属性字段区域标题 | `16` |
| 图例文字 | `16` |

**字号不得小于 14**，确保可读性。

## 五、属性字段区域（底部表格）

在结构图下方、图例上方，用灰底卡片网格展示关键字段映射。

- 外框：`fill="#f7f8fa" stroke="#d5d8de" stroke-width="0.8" rx="4"`
- 区域标题："属性字段"（居中，`font-size="16" fill="#888" font-weight="bold"`）
- 内部卡片：白色 282×90（单行）或 282×92（双行），带彩色边框
- 卡片标题：`font-size="16" font-weight="bold"`，颜色与对应层级标签一致
- 卡片内容：`font-size="15" fill="#555"`，格式 `key : css属性`
- 卡片排列：每行 5 个（x = 16, 312, 608, 904, 1200），第二行 y 比第一行 +110

## 六、图例

底部横条，`fill="#f0f2f5"`，h=36，列出所有颜色标识的含义。

每项：小色块（16×12） + 说明文字（`font-size="16" fill="#666"`），水平排列。

## 七、生成步骤

1. **读 template.html**，提取 `<section>` 内的 DOM 树
2. **确定 viewBox 高度**：
   - 结构区：约 620-660（含 section + padding + container + 内容区）
   - 属性字段区：约 230-250（含标题 + 两行卡片）
   - 图例：40
   - 总计：约 910-940
3. **画 section 框**，标注 padding 四边
4. **画 container 框**
5. **画自定义内容区**：根据 HTML 结构逐层嵌套矩形，标注 class 名，适当放置示例文字
6. **画属性字段卡片**：从 meta.yaml 提取关键字段分组，填入卡片
7. **画图例**：汇总所有出现的颜色标识

## 八、注意事项

- **文字不能重叠**：每个 `<text>` 的 y 坐标必须留足间距（至少 16-20px）
- **文字不能半透明**：所有 `fill` 使用实色，不用 `rgba` 做文字色
- **class 名准确**：标注的 CSS class 名必须与 template.html 中实际使用的一致
- **不做 CSS 属性注释**：结构图内部只标注 HTML class 名和数据字段来源（如 `slides[].title`），不标注 CSS 属性（如 `background`、`font-size`）。CSS 属性映射统一放在底部的"属性字段"表格中
- **箭头标注**：如需标注间距/宽度，使用 `marker-end` 箭头 + 文字说明，箭头颜色用 `#e67e22`
- **image_position 等特殊标注**：放在对应容器上方的小色块内，不与其它文字重叠
