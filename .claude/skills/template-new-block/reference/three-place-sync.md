# 三处同步规则（硬约束）

新增或修改模块的**样式编辑表单**时，必须同步更新以下三处，保证排版和字段分类完全一致：

| # | 文件 | 位置 | 用途 | 代码风格 |
|---|------|------|------|---------|
| 1 | `app/templates/dashboard/panel_page_edit.html` | Jinja2 模板 (~112-1017行) | 已保存模块的服务端渲染 | Jinja2 + HTML |
| 2 | `app/templates/dashboard/panel_page_edit.html` | `addModule()` 函数 (~1500行之后) | 新增模块的客户端生成 | JS 字符串拼接, `cP()`/`uP()` 辅助函数 |
| 3 | `app/static/js/admin_modules.js` | `buildModuleHTML()` 函数 | 数据集编辑器的模块表单 | JS 字符串拼接, `window._cn()`/`window._un()` 辅助函数 |

**每次改一个模块的样式表单，三处都要改。漏掉任何一处，用户就会看到不一致的界面。**

**同样适用于 UI 控件的增删：按钮、图标、标签、提示文字等任何在三个位置共同出现的元素，都要三处同步增删。**

## 字段分组约定

所有模块的样式表单按以下层级组织：

```
外层样式
├── section_bg (外层背景色)
├── outer_width (外层宽度)  ← 大部分模块放这里
├── margin_top/right/bottom/left (外边距)
内层样式
├── inner_bg (内层背景色)  ← 部分模块有
├── inner_width (内层宽度)
├── padding_top/right/bottom/left (内边距)
配色 / 字体样式 / 卡片样式 / ...
```

## outer_width 放置规则

| 模块 | outer_width 位置 | outer_width 单位 | inner_width 单位 |
|------|-----------------|-----------------|-----------------|
| section_title | **外层样式** | `['px','%','rem','vw']` | `['px','%','rem']` |
| data_grid | **外层样式** | `['px','%','rem','vw']` | `['px','%','rem']` |
| product_grid | **外层样式** | `['px','%','rem','vw']` | `['px','%','rem']` |
| feature_grid | **外层样式** | `['px','%','rem','vw']` | `['px','%','rem']` |
| process_steps | **外层样式** | `['px','%','rem']` | `['px','%','rem']` |
| hero_banner | **外层样式** | `['px','%','rem']` | `['px','%','rem']` |
| text_content | **外层样式** | `['px','%','rem']` | `['px','%','rem']` |
| highlight_card | **外层样式** | `['px','%','rem']` | `['px','%','rem']` |
| stat_counter | **外层样式** | `['px','%','rem']` | `['px','%','rem']` |
| contact_info | **外层样式** | `['px','%','rem']` | `['px','%','rem']` |
| **item_detail** | **内层样式** | `['px','%','rem','vw']` | `['px','%','rem']` |
| **logo_cloud** | **内层样式** | `['px','%','rem','vw']` | `['px','%','rem']` |

> **关键规则：** item_detail 和 logo_cloud 的 `outer_width` 在**内层样式**（不在外层），因为这两个模块的结构不同——它们的"外层"没有独立的容器包裹内层。

## inner_width 放置规则

- **始终在"内层样式"分组下**，不要和 outer_width 挤在同一行
- 单位数组：`['px','%','rem']`（不加 vw）

## 外边距 sub-label

- `data_grid` 的外边距区域要在 margin 字段前加 sub-label：
  ```html
  <div class="small text-muted mt-2 mb-1" style="font-size:11px">外边距</div>
  ```
- margin 字段标签用简化名称：`上` `右` `下` `左`（不用 `上外边距` / `右外边距` 等）
- 其他模块（section_title、feature_grid、text_content）的 margin 标签也统一用简化名称

## process_steps 特殊结构

process_steps 有额外的"配色"分组，包含：
- title_font_size / title_color
- desc_font_size / desc_color
- icon_color / number_bg
- number_font_size

## addModule() vs admin_modules.js 代码对照

`panel_page_edit.html` 的 `addModule()` 使用局部辅助函数：
- `cP(name, label, default)` — 颜色选择器
- `uP(name, label, units)` — 带单位选择器的文本输入

`admin_modules.js` 的 `buildModuleHTML()` 使用 window 作用域函数：
- `window._cn(name, label, default)` — 颜色选择器（等效 cP）
- `window._un(name, label, units, currentValue)` — 带单位选择器的文本输入（等效 uP，多一个当前值参数）

两者生成的 HTML 结构必须一致（字段顺序、分组标签、CSS class 名）。

## 修改流程

1. 修改 `meta.yaml` 字段定义（如需要）
2. 修改 Jinja 模板（panel_page_edit.html 前半部分）
3. 修改 `addModule()`（panel_page_edit.html 后半部分）
4. 修改 `admin_modules.js` 中对应的 `buildModuleHTML()` 分支
5. 启动服务器验证：新建模块 + 保存后再打开，两边表单一致

## 常见错误

| 错误 | 后果 | 预防 |
|------|------|------|
| 三处中漏改一处 | 新建和已保存模块表单不一致 | 改完一处立刻改另外两处 |
| outer_width 放错分组 | 用户在外层/内层样式里找不到字段 | 对照上表检查 |
| inner_width 误加 vw 单位 | 内层宽度出现不合理的视口单位 | 检查单位数组 |
| outer_width 和 inner_width 挤在同一行 | 两个字段无法独立换行，排版错乱 | 确保分成两行 |
| Python replace 命中同行多处 | 不该改的字段也被修改（如 inner_width 被误加 vw） | 检查是否同一行有多个 `['px','%','rem']` |
| 删除 UI 控件只改一处 | 其他位置仍有按钮/标签，功能不一致 | 改前先 grep 所有出现位置，三处同步删 |

## 模块图标同步

已选模块列表标题前的图标也需要保持同步：

| # | 文件 | 位置 | 形式 |
|---|------|------|------|
| 1 | `app/templates/dashboard/_block_icons.html` | `block_icon` 宏 | Jinja2 宏，服务端渲染 |
| 2 | `app/templates/dashboard/panel_page_edit.html` | `getBlockIconHTML()` 函数 | JS 函数，`addModule()` 调用 |
| 3 | `app/static/js/admin_modules.js` | `getBlockIconHTML()` 函数 | JS 函数，`buildModuleHTML()` 调用 |

新增模块类型时，三处的 SVG 图标都要添加。三处使用相同的 SVG 代码（`width="28" height="28"`），仅语法不同（Jinja2 vs JS 字符串）。
