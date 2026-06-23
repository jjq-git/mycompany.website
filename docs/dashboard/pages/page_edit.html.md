# page_edit.html：页面模块编辑器

页面模块编辑器是后台用于编辑站点页面模块顺序、内容和样式的通用面板。当前实现是 `panel_page_edit.html` 面板片段 + `page_home.html` 外层预览页，不再使用早期文档中的 `addModuleModal`。

## 当前实现要点

- **面板渲染**：`panel_page_edit.html` 通过 `?_fragment=1` 注入右侧面板，不是独立页面。
- **添加模块**：使用通用组件 `dashboard/_block_palette.html`，实际 modal id 为 `#blockPaletteModal`。
- **共用弹框**：页面编辑面板和数据集编辑面板都 include 同一个 `_block_palette.html`；同一页面内只有一个 `blockPaletteModal` 实例。
- **变体切换**：已有模块的“换变体”也复用 `#blockPaletteModal`，打开前把标题临时改为“更换变体”，关闭后恢复“添加模块”。
- **变体来源**：弹框中的排版变体来自 `meta.yaml` 的 `variants`，以及从 `data-style` / `style_registry` 自动派生出的样式变体。
- **模块构建**：`admin_modules.js` 暴露 `window._buildModuleHTML(type, idx, mdata)`，供页面编辑和数据集编辑共用。

## 添加模块弹框

```jinja2
<button class="btn btn-outline-primary btn-sm w-100 panel-add-module-btn"
        type="button"
        data-bs-toggle="modal"
        data-bs-target="#blockPaletteModal">
  + 添加模块
</button>

{% include 'dashboard/_block_palette.html' %}
```

`_block_palette.html` 负责：

- 读取 `window.blockLibrary` 或 `blockLibraryJson` / `blockLibraryDsJson`。
- 左侧渲染模块类型列表。
- 右侧渲染该模块的结构变体和样式变体缩略图。
- 确认后调用当前页面定义的 `onBlockPaletteConfirm(type, variant, dataPreset)`。

页面编辑中的回调走 `addModule(type, variant, dataPreset)`；数据集编辑中的回调走 `addModuleDs(type, variant, dataPreset)`。

## 变体规则

结构变体由模板作者在 block 的 `meta.yaml` 中维护：

```yaml
variants:
  - key: horizontal
    label: 横向排列
  - key: vertical
    label: 纵向排列
```

样式变体由 `data-style` 自动派生。只有 `style_registry.py` 中 `control` 为 `select` 或 `switch` 的 token 会出现在添加模块弹框里，例如：

```html
<section data-name="feature_grid" data-type="group" data-style="cols">
```

会派生出 `cols_2`、`cols_3`、`cols_4` 等变体，并在确认时传入类似 `{style_cols: "3"}` 的 `dataPreset`。

`template.html` 和 `variants/*.html` 中声明的 `data-style` 都会参与扫描；`meta.yaml` 中手写的结构变体优先于同 key 的自动样式变体。

## 相关文件

- `app/templates/dashboard/panel_page_edit.html`
- `app/templates/dashboard/panel_data_list.html`
- `app/templates/dashboard/_block_palette.html`
- `app/static/js/admin_modules.js`
- `app/core/template_loader.py`
- `app/core/style_registry.py`
