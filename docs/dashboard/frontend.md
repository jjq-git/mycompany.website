# 后台前端

店主后台的前端实现：服务器渲染（Flask + Jinja2），Bootstrap 5.3 做 UI，无前端框架。左侧菜单 + 中间内容/预览 + 右侧帮助面板三栏布局。

## 文档

| 文档 | 讲什么 |
| --- | --- |
| [base.html.md](base.html.md) | 后台外壳：顶栏、三栏布局、颜色变量注入、递归菜单宏、拖拽系统、侧栏收缩、iframe 画布交互、CSRF 包装 |
| [login.html.md](auth/login.html.md) | 邮箱登录：魔法链接流程、CSRF 保护、开发环境快捷入口 |
| [users.html.md](admin/users.html.md) | 平台管理员：用户列表、角色标签、鉴权（M1 占位）、独立页面 |
| [overview.html.md](pages/overview.html.md) | 仪表盘：内容统计 + 全局宽度 |
| [settings_forms.html.md](pages/settings_forms.html.md) | 设置表单（company / social / theme）：同一套 card + label + input 骨架，只差字段 |
| [menu.html.md](pages/menu.html.md) | 菜单配置：表格编辑器、类型切换、新增删除上下移 |
| [variants.html.md](pages/variants.html.md) | 变体选择（header_edit / footer_variant）：radio 卡片网格，footer 多一个备案号 |
| [account.html.md](pages/account.html.md) | 账号管理：邮箱 + 退出 |
| [page_edit.html.md](pages/page_edit.html.md) | 页面模块编辑器：通用，不只是首页，所有页面共用模块添加/排序/配置 |
| [datasets.html.md](pages/datasets.html.md) | 内容集合：通用数据集列表，表格 + 新建/编辑/删除（products、news、cases…都是同一种数据集） |
| [panel-fragments.md](pages/panel-fragments.md) | 面板片段：`_fragment` 渲染机制（panel 不是独立文件，是同一模板的去壳渲染） |

## 一、技术选型

| 层 | 用什么 | 不用什么 |
| --- | --- | --- |
| 渲染 | Flask + Jinja2 服务器渲染 | React / Vue / SPA |
| 样式 | Bootstrap 5.3 CDN + `admin.css`（~130 行） | Tailwind / 纯手写 |
| 脚本 | Bootstrap 5.3 JS bundle + `admin.js`（共享） + 页面内联 `<script>` | jQuery（BS5 已去依赖） |
| 表单 | `flask-wtf` 服务端校验 + fetch AJAX 提交 | 传统 form POST |
| 图标 | Bootstrap Icons CDN | 自绘 SVG |

## 二、模板层级

```text
app/templates/
  base.html                       ← 后台外壳（顶栏 + 三栏布局 + 侧栏内联 + JS）
    auth/
      login.html                  ← 邮箱登录（魔法链接）
    dashboard/
      overview.html               ← 仪表盘：站点总览
      ── 设置 ──
      company.html                ← 公司信息 ┐
      social.html                 ← 社交链接 ├ settings_forms 骨架（[doc](pages/settings_forms.html.md)）
      theme.html                  ← 主题颜色 ┘
      menu.html                   ← 菜单配置（[doc](pages/menu.html.md)）
      header_edit.html            ← 头部变体 ┐ variants 模式（[doc](pages/variants.html.md)）
      footer_variant.html         ← 底部变体 ┘
      account.html                ← 账号管理（[doc](pages/account.html.md)）
      ── 内容 ──
      page_edit.html              ← 页面模块编辑器（[doc](pages/page_edit.html.md)）
      datasets.html               ← 内容集合：通用数据集列表（[doc](pages/datasets.html.md)）
    admin/
      users.html                  ← 平台管理员：用户列表（独立页面，不继承 base.html）
```

> 侧栏已内联到 `base.html`（Jinja2 递归宏）。**面板片段不是独立文件**——每个页面模板在 `?_fragment=1` 模式下只渲染 content block（不包外壳），由 `loadPanel()` 注入右侧 `#right-panel`。整页加载时右侧面板显示静态帮助文字。页面默认 `{% extends "base.html" %}` 填 `content` block（三栏布局）；需要全宽时覆盖 `layout` block（如 page_edit）。

## 三、布局系统

### 3.1 两种布局模式

| 布局 | 使用场景 | 结构 |
| --- | --- | --- |
| `.admin-layout`（三栏） | 仪表盘、设置等大部分页面 | 侧栏（240px） + 主内容（flex: 1） + 帮助面板（360px，xl 以上显示） |
| `.admin-layout-full`（全宽） | 页面编辑器 | 侧栏（240px） + iframe 预览（flex: 1） + 模块面板（280px） |



```
全宽布局 (.admin-layout-full) —— 页面编辑器
┌──────────────────────────────────────────────────────────┐
│  navbar                                                   │
├──────────┬──────────────────────────┬────────────────────┤
│ sidebar  │  iframe 预览区           │ 模块面板 (280px)    │
│ 站点页面 │  [电脑|平板|手机]        │                    │
│ 列表     │                          │  [+ 添加模块]       │
│          │  ┌──────────────────┐    │  [≡] hero   [⚙][×] │
│          │  │  iframe 实时预览 │    │  [≡] feat   [⚙][×] │
│          │  │                  │    │                    │
│          │  └──────────────────┘    │  [保存页面]         │
└──────────┴──────────────────────────┴────────────────────┘
```

### 3.2 base.html

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}mycompany.website 管理后台{% endblock %}</title>

  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/admin.css') }}">

  {% block head_extra %}{% endblock %}
</head>
<body>

  {% include 'dashboard/_topbar.html' %}

  {% block layout %}
  <div class="admin-layout">
    {% include '_sidebar.html' %}
    <main class="admin-main">
      {% block content %}{% endblock %}
    </main>
    <aside class="admin-config d-none d-xl-block" id="right-panel">
      <div class="p-3">
        <h6 class="text-muted">关于当前页面</h6>
        <p class="text-muted small">…上下文提示…</p>
      </div>
    </aside>
  </div>
  {% endblock %}

  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script src="{{ url_for('static', filename='js/admin.js') }}"></script>
  {% block scripts %}{% endblock %}
</body>
</html>
```

默认 `layout` block 提供三栏布局（侧栏 + 主内容 + 帮助面板）。多数页面只填 `content` block 即可；需要全宽布局的页面（如 page_edit）覆盖整个 `layout` block。

### 3.3 顶栏

独立的 `_topbar.html`，固定顶部 56px：

```html
<nav class="navbar navbar-dark bg-dark px-3">
  <span class="navbar-brand mb-0 h1">{{ site_name | default('mycompany.website') }}</span>
  <div class="d-flex align-items-center gap-2">
    {% if session.user_email %}
    <span class="text-light small">{{ session.user_email }}</span>
    {% endif %}
    <a href="{{ url_for('auth.logout') }}" class="btn btn-outline-light btn-sm">退出</a>
  </div>
</nav>
```

### 3.4 侧栏（_sidebar.html）

动态生成，遍历用户所有站点，按菜单结构列出页面：

```html
<aside class="admin-sidebar">
  <nav class="nav flex-column">
    <a class="nav-link {{ 'active' if request.path == url_for('dashboard.index') }}"
       href="{{ url_for('dashboard.index') }}">
      <i class="bi bi-speedometer2"></i> 总览
    </a>
  </nav>

  {% for site in nav_sites %}
  <div class="sidebar-section">
    <h6 class="sidebar-heading px-2 mt-3 mb-1 text-muted">
      <span>{{ site.name }}</span>
    </h6>
    <nav class="nav flex-column">
      {% for page_info in nav_pages.get(site.id, []) %}
      <a class="nav-link {{ 'active' if ... }}"
         href="{{ url_for('dashboard.page_editor', site_id=site.id, page_name=page_info.target) }}">
        <i class="bi bi-{{ 'house' if page_info.page_type == 'home'
                     else 'grid' if page_info.page_type == 'list'
                     else 'file-text' }}"></i>
        {{ page_info.label }}
      </a>
      {% endfor %}
      <a class="nav-link" href="{{ url_for('dashboard.media_library', site_id=site.id) }}">
        <i class="bi bi-images"></i> 媒体库
      </a>
      <a class="nav-link" href="{{ url_for('dashboard.translations', site_id=site.id) }}">
        <i class="bi bi-translate"></i> 翻译
      </a>
      <a class="nav-link" href="{{ url_for('dashboard.settings', site_id=site.id) }}">
        <i class="bi bi-gear"></i> 设置
      </a>
    </nav>
  </div>
  {% endfor %}
</aside>
```

- 每个站点一个分组（站点名称 + 其下页面列表）；
- 页面 icon 按类型：首页 `bi-house`、列表 `bi-grid`、独立页 `bi-file-text`；
- 每个站点下固定附媒体库、翻译、设置三个入口。

### 3.5 帮助面板

大屏（`≥1200px`）右侧 `#right-panel` 显示静态帮助文字。点击侧栏或配置按钮时，JS 通过 `loadPanel(url + '?_fragment=1')` 加载同一模板的去壳版本，覆盖 `#right-panel` 内容——panel 不是独立文件，详见 [panel-fragments.md](pages/panel-fragments.md)。HTML 结构见上方 base.html 的 `layout` block 默认内容。

## 四、自定义 CSS（admin.css）

Bootstrap 5.3 覆盖大部分样式，自定义只做三栏布局 ~130 行：

```css
/* 三栏布局 */
.admin-layout {
  display: flex;
  height: calc(100vh - 56px);
  overflow: hidden;
}

.admin-sidebar {
  width: 240px;
  min-width: 240px;
  background: #f8f9fa;
  border-right: 1px solid #dee2e6;
  overflow-y: auto;
}

.admin-main {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.admin-config {
  width: 360px;
  min-width: 360px;
  border-left: 1px solid #dee2e6;
  overflow-y: auto;
  background: #fff;
}

/* 页面编辑器专用：预览区 */
.admin-preview {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #e9ecef;
  overflow: hidden;
}

.preview-toolbar {
  padding: 0.5rem 1rem;
  background: #fff;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  align-items: center;
}

.preview-frame-wrapper {
  flex: 1;
  overflow: auto;
  padding: 1rem;
  display: flex;
  justify-content: center;
}

#preview-frame {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: width 0.3s;
}

/* 模块列表拖拽 */
.module-item { cursor: grab; user-select: none; }
.module-item:active { cursor: grabbing; }
.module-item.dragging { opacity: 0.5; background: #e9ecef; }
.module-item.drag-over { border-top: 2px solid #0d6efd; }

/* 登录页 */
.login-page { display: flex; justify-content: center; align-items: center;
              min-height: 80vh; }
.login-card { max-width: 420px; ... }

/* 响应式 */
@media (max-width: 768px) {
  .admin-sidebar { position: fixed; left: -240px; ... }
  .admin-sidebar.show { left: 0; }
  .admin-config { display: none; }
}
```

- 三栏全部 `overflow: hidden` + 各自内部 `overflow-y: auto`——各自独立滚动，互不影响；
- 移动端侧栏变 offcanvas 式滑出（`left: -240px` → `left: 0`），暂用 `.show` class 手动控制。

## 五、页面编辑器（page_edit.html）

这是后台最复杂的页面——用户在此编辑网站每个页面的模块排列和内容。

### 5.1 三区布局

| 区域 | 内容 |
| --- | --- |
| 左侧栏 | 站点页面列表（`_sidebar.html`，240px） |
| 中间预览 | iframe 实时预览（`/dashboard/preview/<site_id>/<page_name>`），设备切换器（电脑 1280 / 平板 768 / 手机 375） |
| 右侧面板 | 模块列表（可拖拽排序）+ 添加/删除模块 + 保存按钮（280px）；点击齿轮后在此渲染模块配置表单 |

### 5.2 模块列表（可拖拽）

```html
<div id="module-list" class="list-group list-group-flush">
  {% for module in page.modules or [] %}
  <div class="list-group-item module-item px-2 py-1" data-index="{{ loop.index0 }}"
       draggable="true">
    <span class="drag-handle me-1">≡</span>
    <span class="module-name small">{{ module.type }}</span>
    <span class="float-end">
      <button class="btn btn-sm btn-outline-secondary config-module-btn"
              data-index="{{ loop.index0 }}" title="配置">
        <i class="bi bi-gear"></i>
      </button>
      <button class="btn btn-sm btn-outline-danger remove-module-btn"
              data-index="{{ loop.index0 }}" title="删除">
        <i class="bi bi-x"></i>
      </button>
    </span>
  </div>
  {% endfor %}
</div>
<button type="button" class="btn btn-outline-primary btn-sm w-100 mt-2" id="add-module-btn">
  <i class="bi bi-plus"></i> 添加模块
</button>
<button type="button" class="btn btn-primary btn-sm w-100 mt-1" id="save-page-btn">
  <i class="bi bi-check-lg"></i> 保存页面
</button>
```

拖拽用原生 HTML5 Drag and Drop API（`draggable="true"`），`admin.js` 处理 `dragstart` / `dragover` / `drop` 事件，重排后更新 `data-index`。

### 5.3 iframe 预览 + 设备切换

```html
<div class="btn-group btn-group-sm">
  <button type="button" class="btn btn-outline-secondary preview-device active"
          data-width="1280"><i class="bi bi-laptop"></i> 电脑</button>
  <button type="button" class="btn btn-outline-secondary preview-device"
          data-width="768"><i class="bi bi-tablet"></i> 平板</button>
  <button type="button" class="btn btn-outline-secondary preview-device"
          data-width="375"><i class="bi bi-phone"></i> 手机</button>
</div>

<div class="preview-frame-wrapper">
  <iframe id="preview-frame"
          src="/dashboard/preview/{{ site.id }}/{{ page_name }}"
          style="width: 1280px;"></iframe>
</div>
```

点击设备按钮 → 切换 iframe 宽度（`1280` / `768` / `375`），`transition: width 0.3s` 平滑过渡。iframe 指向独立预览路由，用站点真实数据渲染。

### 5.4 JS 数据传递

页面数据通过 `window.PAGE_CONFIG` 传给 JS：

```html
{% block scripts %}
<script>
window.PAGE_CONFIG = {
  siteId: {{ site.id }},
  pageName: "{{ page_name }}",
  templateName: "{{ site.template_name or 'dengtec' }}",
  modules: {{ page.modules | tojson if page.modules else [] }}
};
</script>
{% endblock %}
```

## 六、设置表单

公司信息、社交链接、主题颜色三页共用同一套骨架（`card > label + input`、`max-width: 720px`），详见 [settings_forms.html.md](pages/settings_forms.html.md)。这里以公司信息为例展示 AJAX 保存模式。

### 6.1 公司信息表单（AJAX 保存）

```html
<form id="settings-form">
  <div class="card mb-3">
    <div class="card-header">公司信息</div>
    <div class="card-body">
      <div class="mb-3">
        <label class="form-label">公司名称</label>
        <input type="text" class="form-control" name="company.name"
               value="{{ settings.company.name | default('') }}">
      </div>
      <div class="mb-3">
        <label class="form-label">公司简介</label>
        <textarea class="form-control" name="company.description" rows="3"
                  >{{ settings.company.description | default('') }}</textarea>
      </div>
      <!-- 电话、邮箱、地址、备案号等同上 -->
    </div>
  </div>

  <button type="submit" class="btn btn-primary">
    <i class="bi bi-check-lg"></i> 保存设置
  </button>
  <span id="save-status" class="ms-2 small"></span>
</form>
```

提交走 `fetch` POST JSON，不刷新页面：

```js
document.getElementById('settings-form').addEventListener('submit', function(e) {
  e.preventDefault();
  var data = {};
  new FormData(this).forEach(function(v, k) {
    // "company.name" → data.company.name
    var keys = k.split('.');
    var cur = data;
    for (var i = 0; i < keys.length - 1; i++) {
      if (!cur[keys[i]]) cur[keys[i]] = {};
      cur = cur[keys[i]];
    }
    cur[keys[keys.length - 1]] = v;
  });

  fetch('/dashboard/settings/' + siteId, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  }).then(function(r) {
    document.getElementById('save-status').textContent = r.ok ? '已保存' : '保存失败';
  });
});
```

### 6.2 菜单编辑器

在同一页面，独立表格 UI：

- 表格列：上移/下移按钮 | 菜单名称（input） | 类型（select：首页/列表/单页/链接） | target（input） | 删除按钮
- "添加菜单项"按钮在行末追加新行
- 首页类型不可删除（`disabled`）
- 上移/下移 → 交换数组位置 → `renderMenuRows()` 重新渲染
- "保存菜单"按钮 → `fetch` POST `/api/save_menu` → 刷新侧栏

```html
<div class="card mt-4">
  <div class="card-header d-flex justify-content-between align-items-center">
    <span>网站菜单</span>
    <button type="button" class="btn btn-outline-primary btn-sm" id="add-menu-item-btn">
      <i class="bi bi-plus"></i> 添加菜单项
    </button>
  </div>
  <div class="card-body p-0">
    <div class="alert alert-warning small m-3 mb-0">
      <strong>菜单即页面：</strong>创建一个菜单项 = 创建一个网站页面。
    </div>
    <table class="table table-hover mb-0" id="menu-table">
      <thead><tr><th></th><th>菜单名称</th><th>类型</th><th>页面标识</th><th>操作</th></tr></thead>
      <tbody id="menu-tbody">
        {% for item in settings.menu or [] %}
        <tr class="menu-row" data-index="{{ loop.index0 }}">
          <td>
            <button class="btn btn-sm btn-outline-secondary menu-up-btn" {{ 'disabled' if loop.first }}>↑</button>
            <button class="btn btn-sm btn-outline-secondary menu-down-btn" {{ 'disabled' if loop.last }}>↓</button>
          </td>
          <td><input type="text" class="form-control form-control-sm menu-label" value="{{ item.label }}"></td>
          <td>
            <select class="form-select form-select-sm menu-type">
              <option value="home" {{ 'selected' if item.type == 'home' }}>首页</option>
              <option value="list" {{ 'selected' if item.type == 'list' }}>列表</option>
              <option value="page" {{ 'selected' if item.type == 'page' }}>单页</option>
              <option value="link" {{ 'selected' if item.type == 'link' }}>链接</option>
            </select>
          </td>
          <td><input type="text" class="form-control form-control-sm menu-target" value="{{ item.target }}"></td>
          <td>
            <button class="btn btn-sm btn-outline-danger menu-delete-btn" {{ 'disabled' if item.type == 'home' }}>×</button>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  <div class="card-footer">
    <button type="button" class="btn btn-primary btn-sm" id="save-menu-btn">保存菜单</button>
    <span id="menu-save-status" class="ms-2 small"></span>
  </div>
</div>
```

## 七、JS 架构

| JS 来源 | 用途 | 位置 |
| --- | --- | --- |
| `bootstrap.bundle.min.js`（CDN） | dropdown、offcanvas 等 BS5 交互组件 | `base.html` `<body>` 底部 |
| `admin.js`（静态文件） | 跨页面共享逻辑：模块拖拽、通用工具函数 | `base.html` BS5 之后加载 |
| 页面内联 `<script>` | 页面专属逻辑：表单提交、菜单编辑、媒体上传 | 各模板 `{% block scripts %}` |

### 数据从服务器到 JS

用 Jinja2 的 `| tojson` 过滤器把 Python 对象直接写入 JS 变量：

```html
{% block scripts %}
<script>
window.PAGE_CONFIG = {
  siteId: {{ site.id }},
  modules: {{ page.modules | tojson if page.modules else [] }}
};
</script>
{% endblock %}
```

页面专属 JS 通过 `fetch` API 发送 JSON、更新 DOM，全程不刷新页面。

## 八、Bootstrap 5.3 组件速查

| 组件 | 关键 class | 用在哪 |
| --- | --- | --- |
| 顶栏 | `navbar navbar-dark bg-dark` | 全局 |
| 侧栏导航 | `nav flex-column` + `nav-link active` | 侧栏 |
| 卡片 | `card` / `card-header` / `card-body` | 概览、设置表单、媒体卡片 |
| 表格 | `table table-hover` + `table-light` | 列表页、菜单编辑器、词汇表 |
| 表单 | `form-control` / `form-label` / `form-select` / `mb-3` | 所有编辑页 |
| 按钮 | `btn btn-primary btn-sm` / `btn-outline-*` | 全局 |
| 栅格 | `row g-3` / `col-md-6 col-lg-4` / `col-6 col-md-4 col-lg-3` | 仪表盘卡片、图片网格 |
| 下拉 | `dropdown` / `dropdown-toggle` / `dropdown-menu-end` | 顶栏头像 |
| 进度条 | `progress` / `progress-bar` / `bg-success` / `bg-warning` / `bg-danger` | 上传进度、翻译进度 |
| 提示 | `alert alert-info` / `alert-warning` | 顶部说明、菜单提示 |
| 图标 | `bi bi-*` | 所有按钮、导航 |
| 间距 | `d-flex` / `gap-2` / `mt-3` / `mb-2` / `ps-4` | 布局微调 |

## 九、移动端

768px 以下：

```css
@media (max-width: 768px) {
  .admin-sidebar { position: fixed; left: -240px; top: 56px; bottom: 0;
                   z-index: 1000; transition: left 0.3s; }
  .admin-sidebar.show { left: 0; }
  .admin-config { display: none; }
}
```

- 侧栏变为 offcanvas 滑出式（通过 `.show` class 手动控制，或后续改用 BS5 offcanvas 组件）
- 右侧帮助面板直接隐藏
- 主内容区填满全宽

## 十、关键规则

- **Bootstrap class 为主，自定义 CSS 只做三栏布局** —— `admin.css` ~130 行。
- **图标用 Bootstrap Icons** —— `<i class="bi bi-xxx"></i>`。
- **CDN 加载 BS5** —— 开发阶段用 CDN，发布前评估本地化。
- **服务器渲染为主，fetch API 做局部保存** —— 表单提交不刷新页面（`e.preventDefault()` + `fetch` POST JSON）。
- **JS 分工：admin.js 管共享逻辑，内联脚本管页面专属逻辑** —— 不在 `admin.js` 里写只用于一个页面的代码。
- **数据用 `| tojson` 从服务器传到 JS** —— 不用隐藏 DOM 元素或 `data-*` 属性传数据。
- **侧栏由菜单驱动** —— 菜单改了什么页面，侧栏自动反映，无需手动维护。
- **panel 不是独立文件，`_fragment` 去壳渲染** —— 右侧面板内容通过 `loadPanel(url + '?_fragment=1')` 加载，和整页模板是同一份代码。避免同一 UI 维护两份。
- **三栏各自独立滚动** —— `overflow: hidden` 外层，`overflow-y: auto` 内层，防止整页滚动。
