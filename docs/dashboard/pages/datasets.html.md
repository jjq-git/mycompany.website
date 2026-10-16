# datasets.html：内容集合

`app/templates/dashboard/datasets.html` 是通用的内容集合管理页——不管数据集叫什么（products、news、cases、team…），同一套列表 + CRUD，只是字段不同。

```jinja2
{% extends "base.html" %}
{% block title %}{{ dataset.label }} — {{ site.name }}{% endblock %}

{% block content %}
<div class="admin-layout">
  {% include '_sidebar.html' %}

  <main class="admin-main">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h4 class="mb-0">{{ dataset.label }} <span class="text-muted small">({{ items | length }})</span></h4>
      <button type="button" class="btn btn-primary btn-sm" id="new-item-btn">
        <i class="bi bi-plus"></i> 添加
      </button>
    </div>

    {% if items %}
    <table class="table table-hover" id="dataset-table">
      <thead>
        <tr>
          {% for col in dataset.columns %}
          <th>{{ col.label }}</th>
          {% endfor %}
          <th style="width: 80px;"></th>
        </tr>
      </thead>
      <tbody>
        {% for item in items %}
        <tr data-slug="{{ item.slug }}">
          {% for col in dataset.columns %}
          <td>
            {% if col.field == 'name' or col.field == 'title' %}
              <a href="{{ url_for('dashboard.dataset_item_edit', site_id=site.id, dataset_name=dataset.name, item_slug=item.slug) }}"
                 class="fw-bold text-decoration-none">{{ item[col.field] }}</a>
            {% elif col.field == 'image' %}
              <img src="{{ item.image }}" style="height: 40px;">
            {% elif col.field == 'price' %}
              {{ item.price }}
            {% elif col.field == 'date' %}
              <span class="text-muted small">{{ item.date }}</span>
            {% else %}
              <span class="text-muted small">{{ item[col.field] | truncate(60) }}</span>
            {% endif %}
          </td>
          {% endfor %}
          <td>
            <button type="button" class="btn btn-sm btn-outline-danger delete-item-btn"
                    data-slug="{{ item.slug }}">×</button>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
    <div class="text-center text-muted py-5">
      <p>还没有内容，点击"添加"创建第一条。</p>
    </div>
    {% endif %}
  </main>

  <aside class="admin-config d-none d-xl-block" id="right-panel">
    <div class="p-3">
      <h6 class="text-muted">关于内容集合</h6>
      <p class="text-muted small">点击行可编辑条目内容。表格列由数据集的字段自动生成。</p>
    </div>
  </aside>
</div>
{% endblock %}
```

- **表格列**：由数据集 schema 动态决定（从 `data/<name>/*.yaml` 首条记录推断字段），不写死列名
- **操作**：点击名称跳转编辑页，删除按钮走 confirm + POST
- **空状态**：提示"添加第一条"
- 名称/标题列可点击跳转到编辑页
- 和主题 block 的对应见 [block 库](../../themes/blocks/library.md)
