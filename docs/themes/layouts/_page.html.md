# _page.html：独立页布局

`_page.html` 是**所有独立页的通用布局**——about、contact、privacy、terms……任何不是首页、不是列表页、不是详情页的页面都用它渲染。`{% extends "_base.html" %}`，填面包屑、页标题、模块序列。

> 列表页有专用的 [`list.html`](list.html.md)（筛选栏 + 分页），不需要用 `_page.html` 兼。

> 旧做法是 `about.html`、`contact.html` 等**每页一个文件**，内容完全一样（标题 + 循环模块），纯粹复制粘贴。`_page.html` 把它们合并成一个。

## 一、源码

```jinja2
{# layouts/_page.html #}
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
<article class="page-{{ page_key }}">
  <h1 class="page-title">{{ page.title }}</h1>
  {% include '_modules.html' %}
</article>
{% endblock %}
```

## 二、和首页的区别

| | `index.html` | `_page.html` |
| --- | --- | --- |
| 对应页 | `page_key = "home"` | 所有其他独立页 |
| `<article>` 包裹 | 无（hero 自带） | 有 |
| `<h1>` 标题 | 无（hero 自带） | 有 `{{ page.title }}` |
| 面包屑 | 无 | 有（首页 > 当前页） |
| 模块渲染 | `{% include '_modules.html' %}` | 同 |

首页第一屏通常是 hero 模块，自带大标题和背景，不需要外层 `<h1>` 和面包屑。独立页是一个标准的内容页，需要文章包裹 + 页面标题 + 面包屑导航。

## 三、page_key

`page_key` 是页面的唯一标识（文件名去掉 `.yaml`），builder 渲染时注入：

```text
sites/<name>/pages/about.yaml   → page_key = "about"
sites/<name>/pages/contact.yaml → page_key = "contact"
```

两个用途：

- CSS hook：`<article class="page-about">`、`<article class="page-contact">`，方便给特定页面加样式
- 面包屑 / 语言切换器拼 URL

## 四、面包屑

```jinja2
{% block breadcrumb %}
<nav class="breadcrumb">
  <a href="/">{{ t.nav.home }}</a>
  <span class="sep">/</span>
  <span>{{ page.title }}</span>
</nav>
{% endblock %}
```

固定两段：首页（用 `t.nav.home` 翻译词）→ 当前页标题。`_base.html` 里的 `breadcrumb` block 默认空，首页不显示；`_page.html` 填上，独立页显示。

若页面层级深（如 `/about/team`），可覆盖面包屑为多段——但这属于少数情况，`_page.html` 给的两段式兜底够用。

## 五、渲染上下文

| 变量 | 用法 |
| --- | --- |
| `page` | `page.title`（标题 + 面包屑）、`page.modules`（模块序列） |
| `page_key` | CSS class `page-{{ page_key }}` |
| `settings` | `settings.title`（拼进 `<title>`） |
| `t` | `t.nav.home`（面包屑"首页"文字） |
| 其余 | 同 [_base.html.md](_base.html.md) |
