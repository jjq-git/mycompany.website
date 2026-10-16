# account.html：账号管理

`app/templates/dashboard/account.html` 是账号管理页——显示当前用户邮箱、站点数量、退出按钮。

```jinja2
{% extends "base.html" %}
{% block title %}账号管理 — {{ site.name }}{% endblock %}

{% block content %}
<div class="admin-layout">
  {% include '_sidebar.html' %}

  <main class="admin-main">
    <h4 class="mb-3">账号管理</h4>

    <div class="card" style="max-width: 480px;">
      <div class="card-body">
        <div class="mb-3">
          <label class="text-muted small">登录邮箱</label>
          <p class="fw-bold">{{ session.user_email }}</p>
        </div>
        <div class="mb-3">
          <label class="text-muted small">站点数量</label>
          <p class="fw-bold">{{ sites | length }}</p>
        </div>
        <hr>
        <form method="post" action="{{ url_for('auth.logout') }}">
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
          <button type="submit" class="btn btn-outline-danger">
            <i class="bi bi-box-arrow-right"></i> 退出登录
          </button>
        </form>
      </div>
    </div>
  </main>

  <aside class="admin-config d-none d-xl-block" id="right-panel">
    <div class="p-3">
      <h6 class="text-muted">关于账号</h6>
      <p class="text-muted small">查看账号基本信息，管理站点列表。</p>
    </div>
  </aside>
</div>
{% endblock %}
```

- 退出走 form POST `/core/logout`，含 CSRF
