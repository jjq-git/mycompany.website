# overview.html：仪表盘

`app/templates/dashboard/overview.html` 是站点总览页——内容统计卡片 + 全局样式设置（全局宽度）。

```jinja2
{% extends "base.html" %}
{% block title %}总览 — {{ site.name }}{% endblock %}

{% block content %}
<div class="admin-layout">
  {% include '_sidebar.html' %}

  <main class="admin-main">
    <h4 class="mb-3">{{ site.name }} · 总览</h4>

    <div class="row g-3 mb-4">
      <div class="col-md-6 col-lg-4">
        <div class="card">
          <div class="card-body">
            <p class="text-muted small mb-1">页面</p>
            <p class="fs-2 fw-bold" style="color: #067a7a;">{{ page_count }}</p>
          </div>
        </div>
      </div>
      <div class="col-md-6 col-lg-4">
        <div class="card">
          <div class="card-body">
            <p class="text-muted small mb-1">产品</p>
            <p class="fs-2 fw-bold" style="color: #067a7a;">{{ product_count }}</p>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">全局宽度</div>
      <div class="card-body">
        <div class="input-group" style="max-width: 360px;">
          <input type="text" id="global-width" class="form-control" value="{{ settings.global_width | default(1200) }}">
          <select id="global-width-unit" class="form-select" style="max-width: 100px;">
            <option value="px">px</option>
            <option value="%">%</option>
            <option value="rem">rem</option>
            <option value="vw">vw</option>
          </select>
        </div>
        <button class="btn btn-primary btn-sm mt-2" onclick="saveGlobalSettings()">保存</button>
        <span id="save-status" class="ms-2 small"></span>
      </div>
    </div>
  </main>

  <aside class="admin-config d-none d-xl-block" id="right-panel">
    <div class="p-3">
      <h6 class="text-muted">关于仪表盘</h6>
      <p class="text-muted small">查看站点内容统计，调整全局宽度设置。</p>
    </div>
  </aside>
</div>
{% endblock %}
```

- **内容统计**：页面数、产品数，数字用主色 `#067a7a` 大号加粗
- **全局宽度**：设置所有模块的外层默认宽度，带单位选择器
- 保存按钮 → fetch POST → toast 提示"已保存"
