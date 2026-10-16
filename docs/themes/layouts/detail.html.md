# detail.html：详情页布局

数据集里的每条记录（产品、文章、案例……）点击进入的详情页。**一个 `detail.html` 通吃所有数据集**，条目以通用变量 `item` 传入，靠 `dataset_name` 和 CSS 区分不同数据集的外观。

## 一、源码

```jinja2
{# layouts/detail.html #}
{% extends "_base.html" %}
{% block title %}{{ item.name | default(item.title) }} — {{ settings.title }}{% endblock %}
{% block description %}{{ item.desc | default(item.description, '') | truncate(160) }}{% endblock %}

{% block breadcrumb %}
<nav class="breadcrumb">
  <a href="/">{{ t.nav.home }}</a>
  <span class="sep">/</span>
  <a href="/{{ dataset_name }}/">{{ t.nav[dataset_name] | default(dataset_name) }}</a>
  <span class="sep">/</span>
  <span>{{ item.name | default(item.title) }}</span>
</nav>
{% endblock %}

{% block content %}
<article class="detail detail-{{ dataset_name }}">
  <h1>{{ item.name | default(item.title) }}</h1>

  {% if item.image %}
  <div class="detail-cover">
    <img src="{{ item.image }}" alt="{{ item.name | default(item.title) }}">
  </div>
  {% endif %}

  {% if item.desc or item.description %}
  <p class="detail-desc">{{ item.desc | default(item.description) }}</p>
  {% endif %}

  {% if item.content %}
  <div class="detail-content">
    {{ item.content | safe }}
  </div>
  {% endif %}
</article>
{% endblock %}
```

## 二、渲染上下文

| 变量 | 说明 |
| --- | --- |
| `item` | 当前条目完整数据（通用名，不随数据集名变化） |
| `dataset_name` | 当前数据集名（如 `"products"`），拼返回链接 / CSS class 用 |
| `page` | 当前页面元信息 |
| 其余 | 同 `_base.html` |

> `item.name | default(item.title)` 兼容不同数据集的命名习惯——有的用 `name`（产品），有的用 `title`（文章）。

## 三、列表页 vs 详情页

| | 列表页 | 详情页 |
| --- | --- | --- |
| 负责文件 | [`list.html`](list.html.md) | `detail.html` |
| 变量 | `page`（含 `page.modules`） | `item`（当前数据条目） |
| 渲染 | `render_block()` 遍历模块 | 直接写 HTML + 条目字段 |
| URL 示例 | `/products/` | `/products/silent-booth-3000/` |

列表页用模块驱动（用户可自由排版），详情页的结构是主题作者定的——因为详情页的字段和排版跟数据集强相关，不适合做成通用模块。

## 四、不同数据集怎么定制外观

一个 `detail.html` 渲染所有数据集，区别外观靠 CSS：

```css
/* 所有详情页共用 */
.detail { … }

/* 产品详情页有规格表 */
.detail-products .detail-specs { display: table; }

/* 文章详情页有作者 / 日期 */
.detail-posts .detail-meta { display: flex; }
```

如果某个数据集需要完全不同的 HTML 结构（不只是样式差异），可以在 `detail.html` 里用 `dataset_name` 做条件分支。只有极少数情况才需要，绝大多数差异靠 CSS 即可。
