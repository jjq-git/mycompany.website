# 变体选择：header_edit / footer_variant

`header_edit.html` 和 `footer_variant.html` 共用同一套变体选择模式——遍历 variants 列表，radio 卡片网格，选中高亮，form POST 保存。

```jinja2
{% extends "base.html" %}
{% block title %}{{ page_title }} — {{ site.name }}{% endblock %}

{% block content %}
<div class="admin-layout">
  {% include '_sidebar.html' %}

  <main class="admin-main">
    <h4 class="mb-3">{{ page_title }}</h4>

    <form method="post" style="max-width: 720px;">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

      <div class="row g-3">
        {% for variant in variants %}
        <div class="col-md-6">
          <label class="card variant-card {% if current_variant == variant.id %}border-primary{% endif %}">
            <div class="card-body">
              <input type="radio" name="{{ field_name }}" value="{{ variant.id }}"
                     {{ 'checked' if current_variant == variant.id }}
                     class="form-check-input me-2">
              <strong>{{ variant.name }}</strong>
              <p class="text-muted small mb-0">{{ variant.description }}</p>
            </div>
          </label>
        </div>
        {% endfor %}
      </div>

      {% block extra_fields %}{% endblock %}

      <button type="submit" class="btn btn-primary mt-3">保存</button>
    </form>
  </main>

  <aside class="admin-config d-none d-xl-block" id="right-panel">
    <div class="p-3">
      <h6 class="text-muted">关于{{ page_title }}</h6>
      <p class="text-muted small">选择一种排版变体。具体内容在各自面板中编辑。</p>
    </div>
  </aside>
</div>
{% endblock %}
```

## 两个页面只差字段

| 页面 | 变体列表 | 字段名 | 额外字段 |
|---|---|---|---|
| `header_edit` | `header_variants` | `header.variant` | 无 |
| `footer_variant` | `footer_variants` | `footer.variant` | ICP 备案号 `footer.icp` |

footer 多一个备案号，通过 `{% block extra_fields %}` 插入：

```jinja2
{# footer_variant.html 的 extra_fields block #}
{% block extra_fields %}
<div class="card mt-3">
  <div class="card-header">备案信息</div>
  <div class="card-body">
    <div class="mb-3">
      <label class="form-label">ICP 备案号</label>
      <input type="text" class="form-control" name="footer.icp"
             value="{{ settings.footer.icp | default('') }}"
             placeholder="如：苏ICP备XXXXXXXX号-1">
    </div>
  </div>
</div>
{% endblock %}
```

- 不需要为 header 和 footer 各写一个完整文件，子模板只需填 `extra_fields` block
- 选中状态用 `border-primary` 高亮
- 实际模板里 `header_edit.html` 和 `footer_variant.html` 是否合并成一个通用文件，看代码实现时的判断
