# _modules.html：模块渲染循环

`_modules.html` 是页面正文的**渲染引擎**——遍历 `page.modules` 数组，按 `order` 排序，逐个调用 `render_block()` 把每个模块渲染成 HTML。

它不关心模块是什么类型、里面有什么数据，只做一件事：**循环 + 分派**。每个页面布局（`index.html`、`_page.html`、列表页）的 `content` block 里只需一行 `{% include '_modules.html' %}`。

## 一、源码

```jinja2
{# layouts/_modules.html #}
{% if page.modules %}
  {% for module in page.modules | sort(attribute='order') %}
    <div class="builder-module" data-builder-module-type="{{ module.type }}">
      {{ render_block(module) }}
    </div>
  {% endfor %}
{% endif %}
```

## 二、渲染流程

```text
page.modules
  │
  │  [{type: "hero", order: 0, data: {...}},
  │   {type: "features", order: 1, data: {...}},
  │   {type: "cta", order: 2, data: {...}}]
  │
  ▼
_modules.html  按 order 排序 → 逐个 render_block(module)
  │
  ▼
render_block()  按 module.type 找 blocks/<type>/ 模板 → 注入 module.data → 输出 HTML
```

## 三、页面如何使用

每个页面布局只写一行——不管页面里有什么模块、多少模块、什么顺序：

```jinja2
{# layouts/index.html #}
{% extends "_base.html" %}
{% block content %}
  {% include '_modules.html' %}
{% endblock %}
```

```jinja2
{# layouts/_page.html #}
{% extends "_base.html" %}
{% block content %}
  <article class="page-{{ page_key }}">
    <h1>{{ page.title }}</h1>
    {% include '_modules.html' %}
  </article>
{% endblock %}
```

用户在后台上添加 / 删除 / 重排模块时，只改页面对应的 YAML，`_modules.html` 和页面布局一行不用动。

> 页面级模块列表：如果某个普通页面由大量相同图文模块组成，并需要在当前页搜索和分页（例如 `/functions/`、`/modules/`），不要改成 `data_grid`。在页面 YAML 顶层启用 `module_list`，由 `_modules.html` 给命中的 `.builder-module` 打标，再由主题 JS 做显隐。详见 [module-list.md](module-list.md)。

## 四、模块的数据结构

`page.modules` 来自页面 YAML（`sites/<name>/pages/<key>.yaml`），每条模块固定三个字段：

| 字段 | 含义 | 例 |
| --- | --- | --- |
| `type` | 模块类型，决定用哪个 block 模板渲染 | `hero`、`features`、`cta` |
| `order` | 排序权重（越小越靠前） | `0`、`1`、`2` |
| `data` | 模块的具体内容，直接注入对应 block 模板 | `{title: "德恩基", subtitle: "专业静音仓制造商"}` |

```yaml
# pages/home.yaml
modules:
  - type: hero
    order: 0
    data:
      title: 德恩基
      subtitle: 专业静音仓制造商
      bg_image: /assets/hero.webp

  - type: features
    order: 1
    data:
      items:
        - {icon: "🔇", title: 超静音, desc: "降噪 35dB 以上"}
        - {icon: "⚡", title: 快速安装, desc: "标准舱 4 小时交付"}
        - {icon: "🎨", title: 定制外观, desc: "颜色 / 材质自由搭配"}
```

## 五、外层 wrapper

每个模块外层包一个 `<div class="builder-module" data-builder-module-type="...">`：

- `class="builder-module"` —— 给 CSS 一个统一的模块边界（间距、背景色等全局样式，不在 block 内部写死）
- `data-builder-module-type` —— 标记模块类型，方便后台可视化编辑时选中 / 高亮（预览模式用，发布时可保留也可去掉）

> `render_block()` 输出的 HTML 不带这个 wrapper——它是 `_modules.html` 加的，不是 block 模板自己包。

## 六、render_block() 的查找规则

`render_block` 是 builder 注入的全局函数，接收一个 module 对象：

1. 取 `module.type`
2. 在主题目录下找 `blocks/<type>/` 目录
3. 用该目录里的模板渲染，把 `module.data` 作为变量注入
4. 返回 HTML 字符串

找不到对应的 block 目录时，输出一段注释 `<!-- block not found: <type> -->`，不中断整页渲染。

## 七、与页面布局的分工

| 谁 | 管什么 |
| --- | --- |
| 页面布局（`index.html`、`_page.html`） | 页面级的壳：标题、独立页的 `<article>` 包裹、面包屑 |
| `_modules.html` | 模块序列的遍历和分派 |
| `blocks/<type>/` 模板 | 单个模块的具体 HTML 结构和样式 |

页面布局不需要知道页面上有哪些模块，模块模板不需要知道自己在第几个、前后是什么模块。三层各管各的。
