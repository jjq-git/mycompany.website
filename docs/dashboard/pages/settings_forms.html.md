# 设置表单：company / social / theme

`company.html`、`social.html`、`theme.html` 是同一类简单设置页——`card > label + input` 表单，`max-width: 720px`，form POST 保存。骨架完全一样，只差字段名和字段数量。

## 通用骨架

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

      <div class="card">
        <div class="card-body">
          {% for field in fields %}
          <div class="mb-3">
            <label class="form-label">{{ field.label }}
              {% if field.default %}<span class="text-muted small">（默认 {{ field.default }}）</span>{% endif %}
            </label>
            {% if field.type == 'color' %}
            <input type="color" class="form-control form-control-sm color-picker" name="{{ field.name }}" value="{{ field.value | default(field.default) }}">
            {% elif field.type == 'url' %}
            <input type="url" class="form-control" name="{{ field.name }}" value="{{ field.value | default('') }}" placeholder="{{ field.placeholder }}">
            {% else %}
            <input type="{{ field.type | default('text') }}" class="form-control" name="{{ field.name }}" value="{{ field.value | default('') }}" placeholder="{{ field.placeholder | default('') }}">
            {% endif %}
          </div>
          {% endfor %}
        </div>
      </div>

      <button type="submit" class="btn btn-primary mt-3">保存</button>
    </form>
  </main>

  <aside class="admin-config d-none d-xl-block" id="right-panel">
    <div class="p-3">
      <h6 class="text-muted">关于{{ page_title }}</h6>
      <p class="text-muted small">{{ help_text }}</p>
    </div>
  </aside>
</div>
{% endblock %}
```

## 三个页面只差数据

| 页面 | 字段数 | 字段类型 | 默认值 | 特殊说明 |
|---|---|---|---|---|
| `company` | 6 个 | text + email | 无 | 点号分隔命名 `company.name` / `contact.phone`，分两张卡片 |
| `social` | 5 个 | url | 无 | 每个 label 带图标；留空不显示该平台 |
| `theme` | 6 个 | color | 有 | `initColorPickers()` 转色块模式 |

### company 字段

```text
company.name        text    公司名称
company.short_name  text    公司简称
company.icp         text    备案号
contact.phone       text    电话
contact.email       email   邮箱
contact.address     text    地址
```

### social 字段

```text
social.github     url
social.twitter    url
social.facebook   url
social.linkedin   url
social.youtube    url
```

### theme 字段（带默认值）

```text
colors.accent          color   #067a7a
colors.bg              color   #ffffff
colors.panel           color   #f8f9fa
colors.text            color   #212529
colors.text_secondary  color   #6c757d
colors.border          color   #dee2e6
```

## 实现建议

三个页面可以用同一个通用设置模板，后端传 `fields` 列表驱动渲染。company 分多张卡片的需求通过 `fields` 里的 `card` 分组字段处理。如果觉得通用模板过早抽象，现阶段保持三个独立文件、各自复制骨架也可以——改动时注意同步。
