# 主题开发

一套主题（`themes/<name>/`）= 网站的"皮肤"：页面布局 + block 库 + 样式 + 初始内容。**用代码写**（HTML / Jinja2 / CSS），不是可视化拖拽。本文是写主题的规则。

> 新模板落地前必须按 [新模板开发规范清单](template-development-checklist.md) 自检，尤其是种子数据完整性、多语言、详情页多图交互和 data-attr block 纯声明式写法。

> 术语：**主题（theme）** 生成用户网站；**template** 一词留给后台 Flask（`app/templates/`）。主题内部的 Jinja2 页面骨架叫**布局（layout）**。

## 一、目录结构

```text
themes/<name>/
  meta.yaml            主题概要（身份 / 分类 / 版本 / languages：声明本主题提供哪些语言的整套 seed）
  preview/             主题缩略图 / 截图（后台展示用，不进 build）—— 语言无关
    cover.webp         固定文件名，后台列表的主缩略图
  layouts/             页面布局（Jinja2）—— 语言无关的皮肤
    _base.html         最外层：<head>、CSS/JS、主题色变量注入、header、footer include
    _modules.html      把 page.modules 渲染成 block 序列
    index.html         首页
    _page.html         独立页（about / contact…）
    list.html          数据集列表页（products / news…）—— 构建期全量渲进 HTML，JS 只做显隐 / 分页，不走 JSON
    detail.html        详情页，一个模板通吃所有数据集，靠 CSS 区分外观
    header/            头部导航（按 settings.header.variant 切变体）
    footer/            页脚（按 settings.footer.variant 切变体）
  blocks/<名>/          内容 block 库（写法见 blocks/）—— 语言无关
  static/              —— 语言无关
    css/main.css       全局样式（设计令牌 + 组件 + block 样式）
    js/                如需脚本放这里（可选）
  translations.yaml    主题 UI 文案（t.*：导航 / 按钮等界面词），一个文件含所有语言 —— 语言无关
  i18n/<lang>/         按语言分的整套 seed（meta.languages 里每个语言一套）
    settings.yaml      该语言的默认站点设置（含 menu / title / slogan 及语言无关的配色，配色各语言重复但值相同）
    pages/*.yaml       该语言的初始页面内容
    data/*.yaml        该语言的初始数据集内容
```

- 所有页面 `{% extends "_base.html" %}`。
- 页面如果由大量 `highlight_card` 等模块组成，并需要当前页搜索 / 分页（如 `/functions/`、`/modules/`），使用页面顶层 `module_list` 配置；开发约定见 [layouts/module-list.md](layouts/module-list.md)。
- `meta.yaml` 在管理员上传主题 ZIP 时解析进数据库（`Theme` 表）。字段逐项说明见 [meta.yaml.md](meta.yaml.md)。其中 `languages` 字段（如 `languages: [en, zh, ja]`）声明本主题为哪些语言提供了 `i18n/<lang>/` 整套 seed。
- `settings.yaml` 是主题自带的默认站点设置，位于 `i18n/<lang>/` 下（每语言一份），字段见 [settings.yaml.md](settings.yaml.md)。
- `layouts/` `blocks/` `static/` `preview/` `translations.yaml` 是语言无关的皮肤，不进 `i18n/`（`translations.yaml` 一个文件含所有语言的 UI 文案，渲染时按当前语言取 `t.*`）。建站时系统按用户选的语言把 `i18n/<lang>/` 整套拷进 `sites/<id>/`，该语言即成为站点源语言（`settings.default_language`）。

## 二、渲染上下文（布局里能用的变量）

builder 渲染每页时注入：

| 变量 | 是什么 | 例 |
| --- | --- | --- |
| `settings` | 该站 `settings.yaml`（用户填的内容） | `settings.title`、`settings.logo` |
| `menu` | builder 把 `settings.menu` 的 `{type, target}` 解析后的导航（每项含 `url`、`active`） | `item.url`、`item.active` |
| `theme` | 解析后的主题色令牌（已注入 `:root`） | `theme.accent` |
| `page` | 当前页 | `page.modules`、`page.title`、`page.description` |
| `page_key` | 当前页 key | `home`、`about` |
| `t` | 当前语言的 **UI 文案字典**（主题自带翻译） | `t.nav.home`、`t.actions.menu` |
| `lang` | 当前语言代码 | `zh-CN` |
| `base_url` | URL 前缀（拼资源与内部链接） | `''` |
| `render_block(module)` | 渲染一个 block（全局函数） | 见第四节 |

> **`settings` vs `t`**：`settings.*` 是用户填的内容（站名、菜单、产品…），多语言靠 `lang/<code>/` 覆盖；`t.*` 是主题自带的界面文案（导航词、按钮字），来自主题的 `translations.yaml`。详见 [i18n.md](../site/i18n.md)。

## 三、放 CSS / JS

**CSS** —— 主题样式写在 `static/css/main.css`，在 `_base.html` 的 `<head>` 里加载：

```html
<link rel="stylesheet" href="{{ base_url }}/static/css/main.css">
```

**主题色变量** —— 用户选的颜色等通过 `theme` 注入 `:root`，`main.css` 一律用 `var(--xxx)` 引用、不硬编码色值：

```html
<style>
  :root {
    {% for key, val in theme.items() %}--{{ key }}: {{ val }};
    {% endfor %}
  }
</style>
```

```css
/* main.css */
.btn { background: var(--accent); }
```

**favicon** —— 来自 `settings.favicon`：`<link rel="icon" href="{{ settings.favicon }}">`。

**JS** —— 保持最少。小交互（移动端菜单切换等）直接内联 `<script>` 写在 `_base.html`；需要更多脚本放 `static/js/*.js`，用 `<script src="{{ base_url }}/static/js/xxx.js" defer></script>` 引入。不引第三方追踪脚本。

`static/` 整个目录构建时原样拷进 `output/.../static/`。

## 四、在页面里调用 block

页面正文就是渲染 `page.modules` 这个模块数组。`layouts/_modules.html` 遍历并逐个渲染：

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

页面只需 include 它：

```jinja2
{# layouts/index.html #}
{% extends "_base.html" %}
{% block content %}
  {% include '_modules.html' %}
{% endblock %}
```

- `render_block(module)` 由 builder 提供：按 `module.type` 找到主题的 `blocks/<type>/`，用 `module.data` 注入渲染，输出干净 HTML。
- block 自身写法（`data-*` 声明式）见 [blocks/](blocks/)。

## 五、读取用户设置

直接从 `settings`（= 该站 `settings.yaml`，结构见 [settings.yaml.md](settings.yaml.md)）取：

```jinja2
{{ settings.title }}                          {# 站点名 #}
{% if settings.logo %}<img src="{{ settings.logo }}">{% endif %}

{# 导航：menu 由 builder 从 settings.menu 的 {type, target} 解析而来，每项含 url 与 active #}
{% for item in menu %}
  <a href="{{ item.url }}" class="{{ 'active' if item.active }}">{{ item.label }}</a>
{% endfor %}
```

> 联系方式 / 社交 / 备案号等**内容**不在 settings，由 block 承载——主题从 block 数据读，不从 settings 读。

- 页眉 / 页脚变体：用户的选择存在 `settings.header.variant` / `settings.footer.variant`，布局按它渲染对应排版。
- 界面固定文案（"菜单""上一页"等）用 `t.*`，不要写死中文，方便多语言。

## 六、开发流程

1. 以现有主题为起点（最完整的参考）。
2. 写 `meta.yaml` → `layouts/` → `blocks/` → `static/css/main.css` → `i18n/<lang>/`（`meta.languages` 里每个语言一整套：`settings.yaml` + `pages/*.yaml` + `data/*.yaml`）。
3. 本地放 `themes/<name>/` 调试；上线用管理员后台上传 ZIP。
