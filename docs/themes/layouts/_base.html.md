# _base.html：页面最外层骨架

`_base.html` 是每套主题的**页面外壳**——所有页面布局（`layouts/*.html`）都 `{% extends "_base.html" %}`。它管 `<head>`（SEO / OG / CSS / 主题色变量）、语言切换、页眉、面包屑、页脚。

内容和渲染逻辑分拆到各子布局（`_modules.html`、`index.html`、`_page.html` 等），`_base.html` 只管壳。

## 一、完整骨架

```html
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  {# 标题与描述 —— block 让子页面可覆盖 #}
  <title>{% block title %}{{ page.title }} — {{ settings.title }}{% endblock %}</title>
  <meta name="description" content="{% block description %}{{ page.description }}{% endblock %}">

  {# OG 标签 —— 社交分享用，复用上面 block 的内容 #}
  <meta property="og:title" content="{{ self.title() }}">
  <meta property="og:description" content="{{ self.description() }}">
  <meta property="og:image" content="{{ page.og_image | default(settings.logo) }}">
  <meta property="og:type" content="website">

  <link rel="icon" href="{{ settings.favicon }}">
  <link rel="stylesheet" href="{{ base_url }}/static/css/main.css">

  {# 主题色变量注入 :root —— 首屏渲染必须就绪，写内联 #}
  <style>
    :root {
      {% for key, val in theme.items() %}--{{ key }}: {{ val }};
      {% endfor %}
    }
  </style>

  {# 全站 <head> 注入（百度统计 / 客服等第三方代码） #}
  {{ settings.head_html | safe }}

  {% block head_extra %}{% endblock %}
</head>
<body>
  {% block header %}
    {% include 'header/' + settings.header.variant + '.html' %}
  {% endblock %}

  {# 面包屑 —— 子页面填，首页留空 #}
  {% block breadcrumb %}{% endblock %}

  <main>
    {% block content %}{% endblock %}
  </main>

  {% block footer %}
    {% include 'footer/' + settings.footer.variant + '.html' %}
  {% endblock %}

  <style>{{ settings.custom_css }}</style>

  {% block scripts %}{% endblock %}
</body>
</html>
```

## 二、OG 标签与 `self.title()`

`og:title` / `og:description` 不能直接再写一遍 `{{ page.title }}`——那样子页面 override 了 `title` block 后 OG 拿到的还是默认值。用 `{{ self.title() }}` 取的是 **block 最终渲染结果**（含子页面覆盖后的值），一份内容、OG 自动同步。

```html
<title>{% block title %}{{ page.title }} — {{ settings.title }}{% endblock %}</title>
<meta property="og:title" content="{{ self.title() }}">
```

> `og:image` 优先取 `page.og_image`（该页自定义封面），没有则回退 `settings.logo`。

## 三、渲染上下文

`_base.html` 可访问 builder 注入的全部变量，详见 [README.md](README.md) 第二节：

| 变量 | 关键用法 |
| --- | --- |
| `settings` | `settings.title`、`settings.favicon`、`settings.logo`、`settings.head_html`、`settings.custom_css`、`settings.header`、`settings.footer`、`settings.languages`、`settings.menu` |
| `theme` | 遍历 `theme.items()` 注入 `:root` 作为 CSS 变量 |
| `page` | `<title>` / `<meta description>` / `og_image` / `page_key` |
| `menu` | 页眉里渲染导航（builder 已解析，每项含 `url`、`active`） |
| `t` | UI 固定文案（"菜单""关闭"等），来自主题 `translations.yaml` |
| `lang` | `<html lang>`、语言切换器的当前高亮、`aria-label` 语言判断 |
| `base_url` | CSS/JS 路径前缀 |
| `now` | Python `datetime.now()`，页脚版权年用 |

## 四、页眉要点

页眉内部结构写在 `layouts/header/<variant>.html` 里，但以下四项每套主题的每个变体都必须有：

### 4.1 导航菜单

`menu` 由 builder 从 `settings.menu` 解析，是**扁平数组**（嵌套子菜单通过每项的 `children` 字段）。每项结构：

```yaml
# settings.menu
- {label: 首页, type: home}
- {label: 产品, type: list, target: products}
- {label: 关于, type: page, target: about, children:
    [{label: 团队, type: page, target: team},
     {label: 联系, type: page, target: contact}]}
```

模板渲染时三种 `type` 的链接写法不同：

| `type` | 链接 | 说明 |
| --- | --- | --- |
| `home` | `/` | 首页 |
| `list` | `/{{ item.target }}/` | 数据集列表页 |
| `page` | `/{{ item.target }}/` | 独立页 |
| `link` | `{{ item.url }}` | 外部链接（直接给完整 URL） |

有 `children` 的项渲染时套一层 `<ul class="sub-nav">`。

### 4.2 移动端菜单切换

每个变体必须有 hamburger 按钮 + 移动端导航展开/收起逻辑：

```html
<button class="mobile-toggle" aria-label="{{ t.nav.menu }}">☰</button>
```

`aria-label` 用 `t.nav.menu`（来自 `translations.yaml`），不写死文字。JS 交互内联在 `scripts` block。

### 4.3 语言切换器

语言数量 ≥ 2 时才显示。渲染在 header 里：

```jinja2
{% if settings.languages | length > 1 %}
<div class="lang-switcher">
  {% for l in settings.languages %}
    <a href="/{{ l.code }}/{{ '' if page_key == 'home' else page_key + '/' }}"
       class="lang-link{% if lang == l.code %} active{% endif %}"
       hreflang="{{ l.code }}">{{ l.name }}</a>
  {% endfor %}
</div>
{% endif %}
```

### 4.4 Logo

```html
<a href="/" class="header-logo-link">
  <img class="header-logo" src="{{ settings.logo }}" alt="{{ settings.title }}" height="40">
</a>
```

## 五、面包屑

`breadcrumb` block 放在 header 和 main 之间。首页留空；子页面填路径。示例（`_page.html` 里 override）：

```html
{% block breadcrumb %}
<nav class="breadcrumb">
  <a href="/">{{ t.nav.home }}</a>
  <span class="sep">/</span>
  <span>{{ page.title }}</span>
</nav>
{% endblock %}
```

## 六、页脚要点

页脚内部结构写在 `layouts/footer/<variant>.html` 里，必须包含：

### 6.1 链接列

从 `settings.footer.links` 渲染，格式：

```yaml
# settings.footer.links（在 settings.yaml 里）
footer:
  variant: default
  links:
    - title: 产品
      links:
        - {label: 产品中心, url: /products/}
    - title: 关于
      links:
        - {label: 关于我们, url: /about/}
        - {label: 联系我们, url: /contact/}
```

每列一个 `<h4>` + 竖向链接列表。

### 6.2 版权与备案

```html
<span>{{ settings.copyright | default('© ' + now.year | string + ' ' + settings.title + ' 版权所有') }}</span>
{% if settings.icp %}
<span class="footer-icp">{{ settings.icp }}</span>
{% endif %}
```

`now.year` 是 Python `datetime.now().year`，render 时注入，年份始终是当前年。

> 联系方式 / 社交链接等**内容**不属于页脚骨架，由 block 承载——主题从 block 数据读，不写死在 footer 模板里。

## 七、页眉 / 页脚变体

用户选用的变体存在 `settings.header.variant` / `settings.footer.variant`，`_base.html` 按它 include 对应模板：

```
themes/<name>/
  layouts/
    header/
      default.html
      centered.html
      ...
    footer/
      default.html
      minimal.html
      ...
```

主题提供几个预置变体，variant 默认值由主题的 `i18n/<lang>/settings.yaml` 给；用户可在自己的 `sites/<name>/settings.yaml` 里改。

## 八、block 一览

| block | 谁填 | 填什么 |
| --- | --- | --- |
| `title` | 各页面布局 | `<title>` 标签内容；OG 用 `self.title()` 自动同步 |
| `description` | 各页面布局 | `<meta description>`；OG 用 `self.description()` 自动同步 |
| `head_extra` | 各页面布局（可选） | 该页专属的 `<meta>` / `<link>` / `<style>` |
| `header` | `_base.html` 自身 | include 页眉变体；特殊页面（全屏 hero）才 override |
| `breadcrumb` | 各页面布局 | 面包屑导航；首页留空 |
| `content` | 各页面布局 | 页面正文 |
| `footer` | `_base.html` 自身 | include 页脚变体；特殊页面才 override |
| `scripts` | 各页面布局（可选） | 该页专属的 `<script>`；移动端菜单 JS 建议写在此处 |

## 九、关键规则

- **OG 标签用 `self.title()` / `self.description()`**，不重复写变量——子页面覆盖后 OG 自动同步。
- **CSS 变量注入在 `<head>` 内联 `<style>`**，不在外部文件——确保首屏渲染时变量已就绪。
- **`settings.custom_css` 放在 `</body>` 前**（不在 `<head>`），优先级高于主题 CSS，方便用户覆盖。
- **`settings.head_html` 原样注入**（`| safe`），承载百度统计、客服脚本等第三方代码。
- **语言切换器只在语言数 ≥ 2 时显示**；链接带 `hreflang`。
- **`static/` 目录整个按原路径引用**：`/static/css/main.css`、`/static/js/xxx.js`，构建时自动拷进 `output/`。
- JS 保持最少：移动端菜单切换直接内联 `<script>` 写在 `scripts` block；更多脚本放 `static/js/`，用 `defer` 引入。
- 年份用 `now.year`，不写死数字。
