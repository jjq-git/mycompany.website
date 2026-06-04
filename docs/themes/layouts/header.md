# header：头部导航

`layouts/header/<variant>.html` 是网站的头部导航组件——Logo、菜单、语言切换器、移动端汉堡按钮。`_base.html` 按 `settings.header.variant` 选择引入哪个变体。

## 一、引入方式

`_base.html` 只写一行 include，不写任何 header HTML：

```html
{% block header %}
  {% include 'header/' + settings.header.variant + '.html' %}
{% endblock %}
```

用户改 `settings.header.variant` 就换排版。变体默认值由主题的 `i18n/<lang>/settings.yaml` 给。

## 二、默认变体（default.html）

```html
{# layouts/header/default.html #}
<header class="site-header">
  <div class="header-inner">
    <a href="/" class="header-logo-link">
      <img class="header-logo" src="{{ settings.logo }}" alt="{{ settings.title }}" height="40">
    </a>

    <button class="mobile-toggle" aria-label="{{ t.actions.menu }}">☰</button>

    <nav class="main-nav" id="main-nav">
      <ul class="nav-list">
        {% for item in menu %}
        <li class="nav-item{% if item.children %} has-children{% endif %}">
          {% if item.type == 'home' %}
          <a href="/"{% if item.active %} class="active"{% endif %}>{{ item.label }}</a>
          {% elif item.type == 'link' %}
          <a href="{{ item.url }}">{{ item.label }}</a>
          {% else %}
          <a href="/{{ item.target }}/"{% if item.active %} class="active"{% endif %}>{{ item.label }}</a>
          {% endif %}

          {% if item.children %}
          <ul class="sub-nav">
            {% for child in item.children %}
            <li><a href="{{ child.url | default('/' + child.target + '/') }}">{{ child.label }}</a></li>
            {% endfor %}
          </ul>
          {% endif %}
        </li>
        {% endfor %}
      </ul>
    </nav>

    {% if settings.languages | length > 1 %}
    <div class="lang-switcher">
      {% for l in settings.languages %}
      <a href="/{{ l }}/{{ '' if page_key == 'home' else page_key + '/' }}"
         class="lang-link{% if lang == l %} active{% endif %}"
         hreflang="{{ l }}">{{ l }}</a>
      {% endfor %}
    </div>
    {% endif %}
  </div>
</header>
```

### 四个组成部分

| 组件 | 选择器 | 说明 |
| --- | --- | --- |
| Logo | `.header-logo-link` + `.header-logo` | 链接到首页，`alt` 用 `settings.title` |
| 导航菜单 | `.main-nav` + `.nav-list` | 遍历 builder 解析后的 `menu`，按 `type` 拼不同链接 |
| 语言切换器 | `.lang-switcher` | 语言数 ≥2 才显示，当前语言加 `.active`，带 `hreflang` |
| 汉堡按钮 | `.mobile-toggle` | 移动端可见（CSS 控制），JS toggle `.open` 类 |

## 三、导航菜单的四种 type

`menu` 由 builder 从 `settings.menu` 解析，每项已含 `url` 和 `active`。模板按 `type` 拼不同链接：

| `type` | 链接写法 | 示例 |
| --- | --- | --- |
| `home` | `/` | 首页 |
| `list` | `/{{ item.target }}/` | 产品列表 / 文章列表 |
| `page` | `/{{ item.target }}/` | 关于 / 联系 |
| `link` | `{{ item.url }}` | 外部链接（完整 URL） |

有 `children` 的项额外渲染 `<ul class="sub-nav">` 下拉子菜单（纯 CSS hover 弹出，移动端静态展开）。

## 四、语言切换器

```jinja2
{% if settings.languages | length > 1 %}
<div class="lang-switcher">
  {% for l in settings.languages %}
  <a href="/{{ l }}/{{ '' if page_key == 'home' else page_key + '/' }}"
     class="lang-link{% if lang == l %} active{% endif %}"
     hreflang="{{ l }}">{{ l }}</a>
  {% endfor %}
</div>
{% endif %}
```

- 语言数 ≥2 才显示（单语言站不需要切换器）
- 当前语言加 `.active` 高亮
- `hreflang` 给搜索引擎看
- 首页不加路径、子页跟 `page_key`

## 五、移动端菜单

汉堡按钮默认隐藏（CSS `display: none`），768px 以下显示：

```css
.mobile-toggle { display: none; }
@media (max-width: 768px) {
  .mobile-toggle { display: block; }
  .main-nav { display: none; }
  .main-nav.open { display: block; }
}
```

JS 极简：

```html
<script>
  document.querySelector('.mobile-toggle').addEventListener('click', () => {
    document.querySelector('.main-nav').classList.toggle('open');
  });
</script>
```

## 六、变体

`settings.header.variant` 只需指定文件名（不含 `.html`），值必须对应 `layouts/header/` 下一个存在的文件：

```yaml
# settings.header
header:
  variant: default    # → layouts/header/default.html
```

主题可提供多种变体：

```text
layouts/header/
  default.html       导航左、Logo 左、语言切换器右
  centered.html      Logo 居中、导航居中、汉堡左
  transparent.html   透明背景、白色文字、适合 hero 视频
```

每个变体是完全独立的 HTML 文件，结构可以完全不同——只要它输出 `<header>` 包裹的内容。变体之间的切换不影响页面其他部分。

## 七、渲染上下文

header 模板可访问全部 builder 变量：

| 变量 | 用途 |
| --- | --- |
| `settings` | `settings.logo`、`settings.title`、`settings.languages`、`settings.header` |
| `menu` | 解析后的导航数组（含 `url`、`active`、`children`） |
| `lang` | 当前语言，语言切换器高亮用 |
| `page_key` | 当前页 key，语言切换器拼 URL 用 |
| `t` | `t.actions.menu`（汉堡按钮 aria-label） |

## 八、为什么不是 block

header 和页面内容 block（hero、features 等）有本质区别：

| | 内容 block | header |
| --- | --- | --- |
| 出现位置 | 页面正文里，用户随意排序 | `_base.html` 固定位置（`<main>` 之上） |
| 出现次数 | 任意 | 每页恰好 1 个 |
| 作用范围 | 单页 | 全站每页相同 |
| 数据来源 | `page.modules[].data`（页面 YAML） | `settings.header` + `settings.menu` + `settings.logo` + `settings.languages` |

做成 block 会引入不必要的防错逻辑——防止用户删掉 header、拖到页面中间、一个页面加多个 header——这些约束在 block 管道里没有现成机制，全要额外写。

**数据来源也不同**。block 的数据在模板自身（HTML 里的文字即默认值），header 的数据在 `settings.yaml`（用户填的菜单、Logo、语言配置），模板只负责"怎么展示"。硬改成 block 等于让 builder 去 YAML 里找字段再注入回模板，多绕一层。

## 九、关键规则

- **所有变体都用 `class="site-header"`**——CSS 靠这个选择器统一给 sticky / 毛玻璃 / 高度，变体内部可加额外 class。
- **导航遍历 `menu`，不遍历 `settings.menu`**——`menu` 是 builder 解析过的（已含 `url` / `active`），`settings.menu` 是原始 YAML。
- **汉堡按钮必须存在**——就算移动端访客少，也不能缺。
- **语言切换器只在多语言站显示**——`settings.languages | length > 1`。
- **子菜单纯 CSS hover**——不加 JS，移动端退化为静态展开。
