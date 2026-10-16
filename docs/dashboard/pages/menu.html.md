# menu.html：菜单配置

`app/templates/dashboard/menu.html` 是网站导航菜单编辑器——表格 UI，每行一个菜单项。

```jinja2
{% extends "base.html" %}
{% block title %}菜单 — {{ site.name }}{% endblock %}

{% block content %}
<div class="admin-layout">
  {% include '_sidebar.html' %}

  <main class="admin-main">
    <h4 class="mb-3">菜单配置</h4>

    <form method="post" style="max-width: 880px;">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

      <table class="table table-hover" id="menu-table">
        <thead>
          <tr>
            <th style="width: 80px;"></th>
            <th>菜单名称</th>
            <th>类型</th>
            <th>目标</th>
            <th style="width: 60px;"></th>
          </tr>
        </thead>
        <tbody id="menu-tbody">
          {% for item in settings.menu or [] %}
          <tr class="menu-row" data-index="{{ loop.index0 }}">
            <td>
              <button type="button" class="btn btn-sm btn-outline-secondary menu-up-btn" {{ 'disabled' if loop.first }}>↑</button>
              <button type="button" class="btn btn-sm btn-outline-secondary menu-down-btn" {{ 'disabled' if loop.last }}>↓</button>
            </td>
            <td><input type="text" class="form-control form-control-sm menu-label" value="{{ item.label }}"></td>
            <td>
              <select class="form-select form-select-sm menu-type" data-type="{{ item.type }}">
                <option value="home" {{ 'selected' if item.type == 'home' }}>首页</option>
                <option value="list" {{ 'selected' if item.type == 'list' }}>列表页</option>
                <option value="page" {{ 'selected' if item.type == 'page' }}>单页</option>
                <option value="link" {{ 'selected' if item.type == 'link' }}>外链</option>
                <option value="container" {{ 'selected' if item.type == 'container' }}>容器</option>
              </select>
            </td>
            <td>
              <input type="text" class="form-control form-control-sm menu-target" value="{{ item.target }}"
                     data-show-when="list,page,link">
              <span class="text-muted small" data-show-when="home,container">—</span>
            </td>
            <td>
              <button type="button" class="btn btn-sm btn-outline-danger menu-delete-btn" {{ 'disabled' if item.type == 'home' }}>×</button>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>

      <button type="button" class="btn btn-outline-primary btn-sm" id="add-menu-btn">+ 添加菜单项</button>
      <button type="submit" class="btn btn-primary btn-sm ms-2">保存菜单</button>
    </form>
  </main>

  <aside class="admin-config d-none d-xl-block" id="right-panel">
    <div class="p-3">
      <h6 class="text-muted">关于菜单</h6>
      <p class="text-muted small">菜单即页面：创建一个菜单项 = 创建一个网站页面。修改后点"保存菜单"即可。</p>
    </div>
  </aside>
</div>
{% endblock %}
```

- **类型切换**：不同类型显示不同目标输入框，通过 `data-show-when` 属性 + CSS 控制显隐
- **上移/下移**：交换 DOM 位置
- 传统 form POST 保存，`max-width: 880px`
