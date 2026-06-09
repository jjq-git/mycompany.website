# overview.html：仪表盘

`app/templates/dashboard/overview.html` 是站点总览页，展示内容统计卡片。

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
  </main>

  <aside class="admin-config d-none d-xl-block" id="right-panel">
    <div class="p-3">
      <h6 class="text-muted">关于仪表盘</h6>
      <p class="text-muted small">查看站点内容统计。</p>
    </div>
  </aside>
</div>
{% endblock %}
```

- **内容统计**：页面数、产品数，数字用主色 `#067a7a` 大号加粗
