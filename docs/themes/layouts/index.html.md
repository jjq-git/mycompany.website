# index.html：首页布局

`index.html` 是首页的页面布局——`{% extends "_base.html" %}`，填 `content` block。结构极简：组装模块序列即可，不写死任何具体内容。

## 一、源码

```jinja2
{# layouts/index.html #}
{% extends "_base.html" %}
{% block title %}{{ page.title }} — {{ settings.title }}{% endblock %}

{% block content %}
  {% include '_modules.html' %}
{% endblock %}
```

## 二、为什么这么短

首页的内容完全由用户在后台填的模块决定——hero、features、products、cta……每个站首页模块不同、顺序不同、内容不同。`index.html` 不预设任何模块，只做三件事：

1. 继承 `_base.html` 的 HTML 骨架
2. 填 `<title>`
3. 调用 `_modules.html` 把 `page.modules` 逐个渲染出来

> `_modules.html` 负责排序 + 分派 → `render_block()` → `blocks/<type>/`。index.html 不碰循环逻辑，详见 [_modules.html.md](_modules.html.md)。

## 三、与 `_page.html` 的区别

| | `index.html` | `_page.html` |
| --- | --- | --- |
| 对应页 | 首页（`page_key = "home"`） | 所有独立页（about / contact / …） |
| 外层包裹 | 无（模块直接撑满） | `<article>` + 页标题 |
| 面包屑 | 首页不显示 | 有 |
| 模块渲染 | `{% include '_modules.html' %}` | 同 |

独立页需要 `<article>` 包裹和 `<h1>` 标题，首页不需要——首页第一屏通常是 hero 模块，它自带大标题。

## 四、渲染上下文

和所有页面布局一样，`index.html` 可访问 builder 注入的全部变量：

| 变量 | 首页用法 |
| --- | --- |
| `page` | `page.title`、`page.modules` |
| `settings` | `settings.title`（拼进 `<title>`） |
| 其余 | 同 [_base.html.md](_base.html.md) |

## 五、首页专属模块

首页没有强制模块，但典型的首页模块组合：

```
hero       —— 首屏大标题 + 背景图/视频
features   —— 产品亮点（3-6 项）
products   —— 产品矩阵
cta        —— 行动号召
blog       —— 最新文章
```

用户可自由增减、重排、替换。`index.html` 对此一无所知——它只管渲染不管内容。
