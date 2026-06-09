# page_edit.html：页面模块编辑器（已过时）

> ⚠️ 本文档描述的是早期 modal 弹框 + 拖拽列表方案，已被当前的手风琴卡片 + schema 驱动表单替代。
> 最新架构见 [frontend.md §5](../frontend.md#五页面编辑器panel_page_edithtml--page_homehtml)。

## 当前实现要点

- **面板渲染**：`panel_page_edit.html` 通过 `?_fragment=1` 注入右侧面板，不是独立页面
- **模块配置**：data-* block 走 `generateSchemaForm()` schema 驱动，radio 字段渲染为 `.segmented-control` 分段按钮组
- **新增/已保存同源**：`addModule()` 和 `initSchemaMounts()` 都通过 `_getMergedSchema(meta)` 合并 meta.yaml 类型后生成表单，保证两处渲染一致
- **变体切换**：`_block_palette.html` 弹框列出 block 变体（meta.yaml 声明 + style_tokens 自动派生）
- **共享构建**：`admin_modules.js` 的 `_buildModuleHTML()` 供数据集编辑页（`panel_data_list.html`）独立使用

## 旧文档（保留供历史参考）

以下内容描述的是 v1 方案，已不再使用。

`app/templates/dashboard/page_home.html`（待重命名为 `page_edit.html`）是通用页面模块编辑器——**不只是首页**，所有页面（关于我们、联系我们……）都用它来排列和配置模块。首页唯一的特殊之处是没有面包屑和 `<h1>` 外层包裹。

```jinja2
{% extends "base.html" %}
{% block title %}{{ page.title }} — {{ site.name }}{% endblock %}

{% block layout %}
<div class="admin-layout-full">
  {% include '_sidebar.html' %}

  <div class="admin-preview">
    <div class="preview-toolbar">
      <div class="btn-group btn-group-sm preview-device-group">
        <button type="button" class="btn btn-outline-secondary active" data-width="1280">
          <i class="bi bi-laptop"></i> 电脑
        </button>
        <button type="button" class="btn btn-outline-secondary" data-width="768">
          <i class="bi bi-tablet"></i> 平板
        </button>
        <button type="button" class="btn btn-outline-secondary" data-width="375">
          <i class="bi bi-phone"></i> 手机
        </button>
      </div>
      <span class="ms-auto text-muted small">实时预览</span>
    </div>

    <div class="preview-frame-wrapper">
      <iframe id="preview-frame"
              src="{{ url_for('dashboard.preview', site_id=site.id, page_name=page_key) }}"
              style="width: 1280px;"></iframe>
    </div>
  </div>

  <!-- 右侧模块列表 -->
  <div class="admin-sidebar-right" style="width: 280px;">
    <div class="p-2 border-bottom">
      <button type="button" class="btn btn-outline-primary btn-sm w-100" data-bs-toggle="modal" data-bs-target="#addModuleModal">
        <i class="bi bi-plus"></i> 添加模块
      </button>
    </div>

    <div id="module-list" class="list-group list-group-flush">
      {% for module in page.modules | sort(attribute='order') %}
      <div class="list-group-item module-item px-2 py-1"
           data-index="{{ loop.index0 }}"
           data-module-type="{{ module.type }}"
           draggable="true">
        <span class="drag-handle me-1">≡</span>
        <span class="module-name small">{{ module.type }}</span>
        <span class="float-end">
          <button class="btn btn-sm btn-outline-secondary config-module-btn" title="配置">
            <i class="bi bi-gear"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger remove-module-btn" title="删除">
            <i class="bi bi-x"></i>
          </button>
        </span>
      </div>
      {% endfor %}
    </div>

    <div class="p-2 border-top">
      <button type="button" class="btn btn-primary btn-sm w-100" id="save-page-btn">
        <i class="bi bi-check-lg"></i> 保存页面
      </button>
    </div>
  </div>
</div>

<!-- 添加模块弹窗 -->
<div class="modal fade" id="addModuleModal" tabindex="-1">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">添加模块</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <div class="row g-3">
          {% for block in available_blocks %}
          <div class="col-6 col-md-4">
            <div class="card block-palette-card" data-block-type="{{ block.type }}" data-bs-dismiss="modal">
              <div class="card-body text-center">
                <i class="bi bi-{{ block.icon }} fs-3"></i>
                <p class="fw-bold mb-1">{{ block.name }}</p>
                <p class="text-muted small mb-0">{{ block.description }}</p>
              </div>
            </div>
          </div>
          {% endfor %}
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

## 首页 vs 独立页的区别

| | 首页 | 独立页 |
|---|---|---|
| `page_key` | `home` | `about`、`contact`… |
| 渲染布局 | `index.html`（无面包屑、无 `<h1>`） | `_page.html`（有面包屑 + `<h1>`） |
| 编辑器 | 同一套 `page_edit.html` | 同一套 `page_edit.html` |

编辑器完全一样，区别只在**渲染时**的主题布局选哪份。`page_edit.html` 不区分首页和其他页——标题用 `{{ page.title }}`、预览用 `{{ page_key }}`。

- **添加模块**：BS5 modal 弹框列出所有可用模块，点击即添加
- **模块列表**：可拖拽排序（`draggable="true"`），点击齿轮打开配置面板
- **三设备预览**：电脑/平板/手机按钮切换 iframe 宽度（1280 / 768 / 375）
- `extends base.html`，填 `layout` block（非 `content`，因为要用全宽布局）
