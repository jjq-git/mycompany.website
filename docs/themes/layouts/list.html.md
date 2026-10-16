# list.html：数据集列表页布局

`list.html` 是**所有数据集列表页的通用布局**——产品列表、文章列表、案例列表……`{% extends "_base.html" %}`，填面包屑、页标题、筛选栏、模块序列、分页。

## 一、源码

```jinja2
{# layouts/list.html #}
{% extends "_base.html" %}
{% block title %}{{ page.title }} — {{ settings.title }}{% endblock %}

{% block breadcrumb %}
<nav class="breadcrumb">
  <a href="/">{{ t.nav.home }}</a>
  <span class="sep">/</span>
  <span>{{ page.title }}</span>
</nav>
{% endblock %}

{% block content %}
<div class="list-page" data-list-dataset="{{ page.dataset }}">
  <h1 class="page-title">{{ page.title }}</h1>

  <div class="list-filters">
    {# 构建期根据数据集条目的 tags 生成筛选按钮 #}
  </div>

  <div class="list-items">
    {% include '_modules.html' %}
  </div>

  <nav class="pagination" aria-label="分页">
    {# JS 驱动，构建期按 data-page-size 计算页数 #}
  </nav>
</div>
{% endblock %}
```

## 二、和 _page.html 的区别

| | `_page.html` | `list.html` |
| --- | --- | --- |
| 用途 | 独立页（about / contact…） | 数据集列表页（产品 / 文章…） |
| `<article>` 包裹 | 有 | 无（列表不是文章） |
| 筛选栏 | 无 | 有 `.list-filters` |
| 分页 | 无 | 有 `.pagination` |
| 模块渲染 | `{% include '_modules.html' %}` | 同 |

列表页的条目渲染、分页、筛选由 block（`data-type="list"` + `data-source`）负责，`list.html` 只管壳。

## 三、渲染上下文

| 变量 | 用法 |
| --- | --- |
| `page` | `page.title`、`page.modules`、`page.dataset`（当前数据集名） |
| `page_key` | CSS hook `list-{{ page.dataset }}` |
| `settings` | `settings.title`（拼进 `<title>`） |
| `t` | `t.nav.home`（面包屑"首页"文字） |
| 其余 | 同 [_base.html.md](_base.html.md) |
