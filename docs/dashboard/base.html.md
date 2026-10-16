# base.html：后台外壳

`app/templates/base.html` 是店主后台的页面外壳——顶栏、三栏布局（左导航 / 中预览 / 右属性面板）、CSS/JS 加载。所有后台页面 `{% extends "base.html" %}`，填 `content` block。

## 一、完整骨架

```text
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta> CSRF token
  <title> 站点名 — 平台域名
  BS5.3.8 CDN CSS
  admin.css（三栏布局 + 拖拽 + 响应式）
  <style> admin_primary 颜色变量注入（Flask → CSS 变量 → BS5 组件）
</head>
<body class="d-flex flex-column vh-100">

  {# 顶栏 #}
  <header class="admin-header">
    SVG logo + 平台名
    站点切换器 dropdown（available_sites）
    新建站点按钮
    预览 / 导出 / 发布（有站点时显示）
    退出表单 + 头像
  </header>

  {# 三栏布局 #}
  <div class="d-flex flex-grow-1 overflow-hidden position-relative">

    {# 左栏：导航 #}
    <nav id="leftNav">
      站点信息区
      设置：公司信息 / 网站头部 / 菜单配置 / 网站底部 / 主题颜色 / 账号管理
      内容：总览 / 首页
      render_left_menu() 递归宏 → 菜单项（list / page / link / group / home）
      站点：模板库
    </nav>
    ← 拖拽分隔条 →
    ← 侧栏折叠按钮 →

    {# 中栏：预览 #}
    <section class="preview-area">
      {# 标签栏（浏览器风格） #}
      <div class="preview-tabs">
        <div class="preview-tab active" data-page-key="home" data-page-url="/">
          <img class="tab-favicon" src="…" alt="">
          <span class="tab-title">首页</span>
          <button class="tab-close" title="关闭">×</button>
        </div>
        <div class="preview-tab" data-page-key="products" data-page-url="/products/">
          <img class="tab-favicon" src="…" alt="">
          <span class="tab-title">产品列表</span>
          <button class="tab-close" title="关闭">×</button>
        </div>
        <button class="tab-new" title="新建标签">+</button>
      </div>
      {# URL 栏（纯展示） #}
      <div class="preview-url-bar">
        <span class="url-icon">🔒</span>
        <span class="url-text">https://mysite.com/products/</span>
      </div>
      {# 工具栏 #}
      <div class="preview-toolbar">
        设备切换按钮（电脑 / 平板 / 手机）
        刷新预览按钮
        属性面板重开按钮（面板隐藏时显示）
      </div>
      <iframe id="previewFrame">
    </section>

    ← 拖拽分隔条 →
    ← 面板折叠按钮 →

    {# 右栏：属性面板 #}
    <aside id="rightPanel" style="width:380px">
      面板标题
      flashed messages + {% block content %}
      底部保存栏（AJAX 加载后移入）
    </aside>
  </div>

  拖拽遮罩 <div id="dragOverlay">
  _datasetKeys 数组

  Popper + BS5 JS CDN
  全局 fetch CSRF 包装
  面板拖拽逻辑
  左侧栏拖拽逻辑
  toggleRightPanel() / togglePanelCollapse()
  switchDevice() / refreshPreview()
  loadPanel() / runPanelScripts()
  表单提交拦截
  侧栏点击 → 加载面板 + 同步预览
  installPreviewCanvasHandlers()（iframe 注入）
  侧栏收缩 localStorage + hover tooltip
  initColorPickers()
  {% block scripts %}
</body>
```

## 二、加载清单

| 资源 | 来源 | 说明 |
| --- | --- | --- |
| `bootstrap@5.3.8` CSS | CDN | 全局样式 |
| `admin.css?v=20260519` | `app/static/css/admin.css` | 三栏布局 + 拖拽 + 响应式 |
| `<style>` 内联 | Flask 注入 | `admin_primary` 等颜色变量覆盖 BS5 默认蓝色 |
| `@popperjs/core@2.11.8` | CDN | dropdown 定位（独立加载，不用 bundle） |
| `bootstrap@5.3.8` JS | CDN | dropdown、offcanvas 等交互组件 |
| 内联 `<script>` | 模板内 | 所有跨页共享逻辑（fetch 包装、拖拽、面板加载、表单提交等） |

**为什么不打包**：Bootstrap JS 用独立构建（popper + bootstrap 分开），不用 bundle——bundle 体积更大且 popper 版本锁定不灵活。

## 三、颜色变量注入

Flask 在 `app/templates/base.html` 渲染时注入 `admin_primary` 等变量，通过内联 `<style>` 覆盖 BS5 的 CSS 变量：

```html
<style>
  :root {
    --bs-primary: {{ admin_primary }};
    --bs-primary-rgb: {{ admin_primary_rgb }};
    --bs-primary-bg: {{ admin_primary }};
    --bs-primary-bg-subtle: {{ admin_primary_light }};
    --bs-primary-text-emphasis: {{ admin_primary_active }};
    --bs-primary-border-subtle: {{ admin_primary_light }};
    --bs-link-color: {{ admin_primary }};
    --bs-link-color-rgb: {{ admin_primary_rgb }};
    --bs-link-hover-color: {{ admin_primary_hover }};
    --bs-link-hover-color-rgb: {{ admin_primary_rgb }};
  }
  .btn-primary {
    --bs-btn-bg: {{ admin_primary }};
    --bs-btn-border-color: {{ admin_primary }};
    --bs-btn-hover-bg: {{ admin_primary_hover }};
    --bs-btn-hover-border-color: {{ admin_primary_hover }};
    --bs-btn-active-bg: {{ admin_primary_active }};
    --bs-btn-active-border-color: {{ admin_primary_active }};
    --bs-btn-disabled-bg: {{ admin_primary }};
    --bs-btn-disabled-border-color: {{ admin_primary }};
  }
  .btn-outline-primary { /* 同理覆盖全套状态色 */ }
  .bg-primary { background-color: rgba(var(--bs-primary-rgb), var(--bs-bg-opacity)) !important; }
  .text-primary { color: {{ admin_primary }} !important; }
  .border-primary { border-color: {{ admin_primary }} !important; }
  .text-bg-primary { color: #fff !important; background-color: {{ admin_primary }} !important; }
</style>
```

**Flask 注入变量一览**：

| 变量 | 含义 | 示例值 |
| --- | --- | --- |
| `admin_primary` | 主色 | `#067a7a` |
| `admin_primary_rgb` | 主色 RGB（逗号分隔） | `6, 122, 122` |
| `admin_primary_hover` | hover 态 | `#056060` |
| `admin_primary_active` | active 态 | `#044040` |
| `admin_primary_light` | 浅色背景 | `#e6f2f2` |
| `platform_domain` | 平台域名 | `mycompany.website` |

和访客端 `_base.html` 的 `:root` 变量注入不同——后台不需要用户换肤，这里覆盖的是 **BS5 组件色**（让 btn-primary 等组件跟着平台主色走），不是主题 token。

## 四、顶栏

```html
<header class="admin-header">
  <div class="d-flex align-items-center h-100 px-3 gap-2">
```

### 4.1 组成部分

| 组件 | 选择器 | 说明 |
| --- | --- | --- |
| Logo + 品牌名 | `.admin-logo` + `.admin-brand` | 内联 SVG 28×28 网格图标 + `platform_domain` 文字，链接到总览 |
| 站点切换器 | `.header-site-btn` + `.dropdown-menu` | BS5 dropdown，遍历 `available_sites`，当前站点加 `.active`，`?site=id` 切换 |
| 新建站点 | `.header-btn` + `openTemplatesPanel()` | 加号图标，JS 打开模板库面板 |
| 预览 | `.header-btn` | 眼睛图标，`target="_blank"` 新窗口打开 `preview_site` |
| 导出 | `.header-btn` | 下载图标，直接跳转 `export_zip` 路由 |
| 发布 | `.header-btn-primary` | 上传图标高亮按钮，`doPublish()` → confirm → fetch POST `/build` → alert |
| 退出 | `button.header-btn` | 表单 POST `core.logout`，带 CSRF hidden input |
| 头像 | `.admin-avatar` | 用户邮箱首字母大写，无图片时兜底 `?` |

### 4.2 有站点 / 无站点

预览、导出、发布三个按钮和它们前面的分隔条整个包在 `{% if site %}` 里——未选站点时不显示操作按钮，只留站点切换器和退出。

### 4.3 内联 SVG Logo

```html
<svg class="admin-logo" width="28" height="28" viewBox="0 0 28 28">
  <rect width="28" height="28" rx="6" fill="#067a7a"/>
  <!-- 四个白色圆角方块构成网格图标 -->
  <rect x="5" y="7" width="7" height="5" rx="1.5" fill="#fff" opacity="0.95"/>
  <rect x="16" y="7" width="7" height="5" rx="1.5" fill="#fff" opacity="0.95"/>
  <rect x="5" y="16" width="7" height="5" rx="1.5" fill="#fff" opacity="0.95"/>
  <rect x="16" y="16" width="7" height="5" rx="1.5" fill="#fff" opacity="0.95"/>
</svg>
```

不依赖外部图片文件——确保任何网络环境下 Logo 都显示。

### 4.4 顶栏不放站点切换器 dropdown 以外的导航

MVP 阶段用户只有一个角色，不需要设置 / 切换账号入口。站点切换用侧栏列出所有站点，不是顶栏 dropdown——顶栏 dropdown 只做切换，不做导航。

## 五、三栏布局

```text
┌─────────────────────────────────────────────────────────┐
│                      顶栏 (56px)                        │
├──────────┬──┬────────────────────────┬──┬───────────────┤
│ 左导航    │拖│  中栏预览               │拖│ 右属性面板      │
│ #leftNav │拽│  ┌─ 标签栏 ───────────┐ │拽│ #rightPanel   │
│ 240px    │条│  │ 🏠首页 📄关于 [+]  │ │条│ 380px         │
│          │  │  ├─ URL 栏 ───────────┤ │  │               │
│  可拖拽   │  │  │ 🔒 https://...    │ │  │  AJAX 加载     │
│  可折叠   │  │  ├─ 工具栏 ───────────┤ │  │  可折叠        │
│          │  │  │ 📱💻🖥  🔄        │ │  │               │
│          │  │  ├────────────────────┤ │  │               │
│          │  │  │                    │ │  │               │
│          │  │  │  iframe 预览       │ │  │               │
│          │  │  │                    │ │  │               │
└──────────┴──┴──┴────────────────────┴──┴───────────────┘
```

- **容器**：`d-flex flex-grow-1 overflow-hidden position-relative`
- **左栏**：`flex-shrink-0 overflow-auto`，CSS 默认宽度 240px，可拖拽调整（60px–480px）、可收缩至 60px
- **中栏**：`flex-grow-1 d-flex flex-column overflow-hidden bg-light`
  - **标签栏** — 浏览器风格梯形标签，显示 favicon + 页面标题，支持新建 / 切换 / 关闭（详见 [§十二](#十二预览标签栏)）
  - **URL 栏** — 当前页面 URL，纯展示不可编辑（详见 [§十二](#十二预览标签栏)）
  - **工具栏** — 设备切换（📱💻🖥）+ 刷新 + 面板重开按钮
  - **iframe** — 预览当前活跃标签的页面
- **右栏**：`flex-shrink-0`，初始宽度 380px，可拖拽调整（240px–900px）、可折叠至 32px

## 六、左侧导航

### 6.1 站点信息区

```html
<div class="left-nav-site-info px-3 py-2">
  <div class="site-label">我的网站</div>
  <div class="site-name">{{ site.name or site.slug }}</div>
</div>
```

无站点时显示"未选择站点"。

### 6.2 固定导航项

| 分组 | 导航项 | data-panel | 说明 |
| --- | --- | --- | --- |
| 设置 | 公司信息 | `company` | 公司名称、联系方式、Logo |
| 设置 | 网站头部 | `header` | header 变体 + 配置 |
| 设置 | 菜单配置 | `menu` | 导航菜单编辑 |
| 设置 | 网站底部 | `footer_variant` | footer 变体 + 链接列 |
| 设置 | 主题颜色 | `theme` | 颜色选择器 |
| 设置 | 账号管理 | `account` | 用户账号设置 |
| 内容 | 总览 | `overview` | 站点仪表盘 |
| 内容 | 首页 | `pages_home` | 首页模块编辑，带 `data-preview-page="home"` |
| 站点 | 模板库 | `templates` | 模板选择 / 新建站点 |

每项有独立的内联 SVG 图标（`.left-nav-icon`），和文字一起放在 `<a class="left-nav-item">` 里。

### 6.3 递归菜单宏

```jinja2
{% macro render_left_menu(items, level=0) %}
  {% for item in items %}
    {% if item.type != 'home' %}
      {% set has_children = item.children | default([]) | length > 0 %}
```

按 `item.type` 分四种渲染方式：

| type | 渲染方式 | 点击行为 |
| --- | --- | --- |
| `list` | 带 nav-badge（产品数 / 文章数）的链接 | 加载列表页面板 + 同步预览 |
| `page` | 普通链接（文档图标） | 加载页面编辑器面板 + 同步预览 |
| `link` | 带外链图标的链接，`target="_blank"` | 新窗口打开外部 URL |
| `group` / `home` / 其他 | 纯标签（文件夹图标），不可点击 | 仅作为分组标识 |

有 `children` 的项额外渲染可折叠子菜单（`left-nav-group` → `left-nav-parent-row` + `left-nav-submenu`），递归调用自身。折叠/展开通过 `toggleLeftSubmenu()` 切换 ▶/▼ 箭头。

子菜单项根据嵌套层级增加左侧内边距：`style="padding-left: {{ 16 + level * 16 }}px;"`

### 6.4 导航计数

列表类型菜单项显示数据条数：

```jinja2
{% if item.target == 'products' %}<span class="nav-badge">{{ counts.products }}</span>
{% elif item.target == 'posts' %}<span class="nav-badge">{{ counts.posts }}</span>
{% endif %}
```

`counts` 由 Flask 视图注入，含 `products` 和 `posts` 两个字段。

## 七、中栏预览

### 7.1 设备切换

```html
<button class="preview-device-btn active" data-device="desktop" onclick="switchDevice('desktop')">电脑</button>
<button class="preview-device-btn" data-device="tablet" onclick="switchDevice('tablet')">平板</button>
<button class="preview-device-btn" data-device="mobile" onclick="switchDevice('mobile')">手机</button>
```

`switchDevice()` 切换 iframe 的 CSS class（`desktop` / `tablet` / `mobile`），配合 `admin.css` 中的 `max-width` 限制模拟不同设备宽度。

### 7.2 预览 iframe

```html
<iframe id="previewFrame"
  src="{{ url_for('core.preview_site', site_id=site.id) }}"
  data-preview-url="..."
  class="preview-frame desktop">
</iframe>
```

- `src`：初始预览 URL
- `data-preview-url`：记录"原始预览 URL"，`refreshPreview()` 用它拼接 `?_=timestamp` 绕过缓存
- `desktop` class：默认桌面宽度（100%）

### 7.3 刷新预览

```javascript
function refreshPreview() {
  fetch('/build?_fragment=1', {method:'POST'})
    .then(...)
    .then(() => { f.src = previewUrl + '?_=' + Date.now(); });
}
```

先 POST `/build` 触发静态生成，再刷新 iframe。`_fragment=1` 参数告诉后端只返回 JSON（不返回完整 HTML 页面）。

### 7.4 无站点状态

{% if not site %} 时 iframe 不渲染，改为空状态提示："尚未创建站点，在左侧模板库中选择一个模板来新建站点"。

### 7.5 属性面板重开按钮

```html
<button id="reopenPanelBtn" style="display:none;" onclick="toggleRightPanel()">☰ 属性</button>
```

当右面板通过 `toggleRightPanel()` 隐藏（`d-none`）时显示，点击重新打开面板。

## 八、右侧属性面板

### 8.1 结构

```html
<aside id="rightPanel" style="width:380px">
  <div class="right-panel-header">   {# 齿轮图标 + 标题 #}
  <div class="right-panel-body">     {# flashed messages + {% block content %} #}
  <div class="right-panel-footer">   {# 保存按钮栏，AJAX 加载后移入 #}
</aside>
```

`{% block content %}` 的默认内容是空状态提示："← 在左侧选择一项开始编辑"。

### 8.2 AJAX 面板加载

点击左侧导航 → `loadPanel(url + '?_fragment=1')` → fetch → 注入 `#rightPanelBody` → `runPanelScripts()` 重新执行内联脚本。

`_fragment=1` 让 Flask 只返回面板内容片段（不含 base.html 外壳）。

加载时自动将 `.panel-save-bar`（保存按钮栏）从 body 移到 footer 固定底部：

```javascript
var saveBar = body.querySelector('.panel-save-bar');
if (saveBar && footer) {
  btn.setAttribute('form', form.id);  // 按钮可能和表单不在同一 DOM 层级
  footer.appendChild(saveBar);
}
```

### 8.3 表单提交拦截

```javascript
document.getElementById('rightPanelBody').addEventListener('submit', function(e) {
  e.preventDefault();
  normalizeUnitInputs(form);  // 纯数字补上单位
  fetch(form.action, {method: 'POST', body: new FormData(form)})
    .then(r => r.text())
    .then(html => { body.innerHTML = html; runPanelScripts(body); refreshPreview(); });
});
```

面板内所有表单默认走 AJAX——阻止原生提交，fetch POST，HTML 回填，自动刷新预览。

`normalizeUnitInputs()` 在提交前检查 `.input-group` 中的文本输入：如果用户输入了纯数字（如 `16`），自动补上单位选择器的当前值（如 `16px`），避免"默认单位为 — 时输入纯数字无效"的问题。

## 九、拖拽系统

三栏布局有两个拖拽分隔条，共用一个 `#dragOverlay` 遮罩。

### 9.1 为什么用遮罩

拖拽时鼠标在 iframe 上方移动——iframe 会吞掉 `mousemove` 事件。解决方案：拖拽开始时显示一个全屏透明遮罩 `#dragOverlay`（`position:fixed;inset:0;z-index:9999`），在遮罩上监听 `mousemove` / `mouseup` / `mouseleave`，拖拽结束后隐藏。

### 9.2 右侧面板拖拽

```javascript
// mousedown → 记录 startX / startWidth
// mousemove(on overlay) → panel.style.width = max(240, min(900, newWidth))
// mouseup → 清理状态
```

范围 240px–900px，向左拖变宽、向右拖变窄。

### 9.3 左侧导航拖拽

范围 60px–480px，**带阈值吸附**：

- 松开时宽度 < 140px → 吸附到收缩态（60px，`left-nav-collapsed` class 接管）
- 松开时宽度 ≥ 140px → 保留拖拽宽度

拖拽过程中跨越 140px 阈值时，实时切换按钮图标（汉堡 ↔ 双箭头）和 `left-nav-collapsed` class，给用户即时视觉反馈。

拖拽期间设置 `leftNav.style.transition = 'none'` 避免 CSS transition 造成延迟感；松开后恢复 transition。

## 十、侧栏收缩

### 10.1 localStorage 持久化

```javascript
var STORAGE_KEY = 'admin_sidebar_collapsed';
var collapsed = localStorage.getItem(STORAGE_KEY) === '1';
```

`sidebarToggleBtn` 点击 → 切换 `collapsed` → `applyState()` → 添加/移除 `left-nav-collapsed` class + 更新按钮图标。

### 10.2 收缩态行为

- CSS class `left-nav-collapsed`：宽度 60px，文字/分组标题/徽章/箭头 `display:none`，只留图标居中
- 鼠标悬停导航项 → 200ms 延迟后弹出 tooltip（`#leftNavTooltip`），显示 `title` 属性文本
- 鼠标移出 → tooltip 隐藏
- 点击有子菜单的父项 → 自动展开侧栏 + 250ms 后展开子菜单

### 10.3 工具提示实现

```javascript
var tooltip = document.createElement('div');
tooltip.id = 'leftNavTooltip';
// position:fixed, z-index:10000, 深色背景白色文字
// 定位在导航项右侧 rect.right + 10px, 垂直居中 translateY(-50%)
```

tooltip 挂到 `document.body` 上，避免被 `#leftNav` 的 `overflow` 裁剪。

### 10.4 与拖拽的协作

- `window._sidebarCustomWidth`：拖拽展开态保留的自定义宽度
- `window._sidebarSetCollapsed(val)`：拖拽模块同步 collapsed 状态到 localStorage
- `window._sidebarIsCollapsed()`：供其他模块查询当前状态
- `window._sidebarExpand()`：供 click 处理器强制展开

## 十一、iframe 画布交互

`installPreviewCanvasHandlers()` 在 iframe 加载完成后注入样式和点击事件：

```javascript
document.getElementById('previewFrame')?.addEventListener('load', installPreviewCanvasHandlers);
```

### 11.1 注入样式

向 iframe 的 `<head>` 注入 CSS：
- `.builder-module:hover` → 青色描边 + 发光阴影
- `.builder-region:hover` → 同上（header 用 `::after` 伪元素处理）
- `.builder-canvas-selected` → 选中态保持高亮

### 11.2 点击处理

| 目标 | 选择器 | 点击行为 |
| --- | --- | --- |
| 页面模块 | `.builder-module[data-builder-module-index]` | 高亮自身 → `selectModuleInPanel(index, pageKey)` 在右侧面板展开对应模块 |
| 区域（header/footer） | `.builder-region[data-builder-region]` | 高亮自身 → `loadPanel('/settings/header' 或 '/settings/footer_variant')` |

`data-builder-module-index` 和 `data-builder-region` 由静态生成时写入，对应后台的模块索引和区域标识。

`pageKeyFromPreviewPath()` 从 iframe 的 `pathname` 推导当前页面 key：
- 无路径或 `/` → `home`
- 详情页（最后一段不是已知数据集 key）→ 返回倒数第二段

## 十二、预览标签栏

预览区顶部是浏览器风格的标签栏 + URL 栏，支持多页面切换，方便对比不同页面的效果。

### 12.1 标签行为

- **新建标签** — 点击 `+` 弹出页面选择器，可选首页、独立页、数据集列表页、数据集具体条目
- **切换标签** — 点标签切换 iframe 的 `src`，切换时左侧菜单取消所有高亮（当前页不再对应单一菜单项）
- **关闭标签** — 每个标签右侧有 `×` 按钮，至少保留一个标签（最后一个不可关）
- **默认标签** — 初始打开后台时自动创建首页标签（`pageKey: home`），刷新后也恢复为首页单标签
- **标签数据** — 纯前端数组 `previewTabs`，存 `{pageKey, title, url}`，不持久化
- **关闭当前标签** — 自动切换到右侧相邻标签，没有右侧则左侧
- **左侧菜单联动** — 点左侧菜单项时，如果该页已有标签 → 切换到已有标签；没有 → 新建标签并切换

### 12.2 页面选择器

点击 `+` 弹出模态框，列出站点所有可预览的页面：

```text
🔍 [搜索页面…]

├── 🏠 首页
├── 📄 关于我们
├── 📄 联系我们
├── 📋 产品列表
│   ├── 静音舱-3000
│   ├── 静音舱-5000
│   └── 静音舱-8000
├── 📋 文章列表
│   ├── 行业趋势 2026
│   └── 办公空间设计指南
└── 📋 案例列表
    └── 腾讯总部
```

- **数据来源** — 后端 `GET /api/site/<name>/page-tree`，返回嵌套结构
- **搜索** — 前端过滤，匹配标题或页面 key
- **数据集条目** — 按数据集分组折叠，避免列表过长；条目超过 50 条时加虚拟滚动
- **键盘** — `↑↓` 移动高亮，`Enter` 确认选择，`Esc` 关闭弹框

### 12.3 URL 栏

标签下方显示当前页的完整 URL，纯展示不可编辑：

```
🔒 https://mysite.com/products/silent-booth-3000/
```

- `https://` 固定前缀（当前无自定义域名，用平台子域）
- 路径部分跟随当前标签的 `pageKey` 和语言设置自动拼接
- 切换语言时 URL 栏同步更新

### 12.4 实现要点

- **标签切换不触发 `loadPanel()`** — 只是改 iframe `src`，不加载面板
- **iframe 加载完成后** — 调用 `installPreviewCanvasHandlers()` 重新注入 canvas 交互
- **设备切换 / 刷新** — 只影响当前活跃标签的 iframe，其他标签保持原状
- **标签栏 CSS** — 浏览器风格梯形标签，`active` 标签与下方 URL 栏无缝连接，未激活标签半透明

## 十三、关键 JS 函数速览

| 函数 | 用途 |
| --- | --- |
| `loadPanel(url)` | fetch 面板 HTML → 注入 `#rightPanelBody` → `runPanelScripts` → 移保存栏到 footer |
| `runPanelScripts(container)` | 重新创建 `<script>` 元素使其执行，触发 `initColorPickers` + `initUnitPickers` |
| `initColorPickers(container)` | 将 `type="color"` 输入转为 `.color-swatch` 色块模式 |
| `initUnitPickers(container)` | 根据输入值（如 `100%`）反向匹配单位选择器选项 |
| `normalizeUnitInputs(form)` | 提交前给裸数字补上当前选择的单位 |
| `switchDevice(device)` | 切换预览 iframe 的 `desktop`/`tablet`/`mobile` class |
| `refreshPreview()` | POST `/build` → 刷新 iframe |
| `doPublish()` | confirm → POST `/build` → alert 结果 → 刷新预览 |
| `toggleRightPanel()` | 显示/隐藏 `#rightPanel`（`d-none`），控制 `#reopenPanelBtn` 和 `#panelCollapseBtn` |
| `togglePanelCollapse()` | 折叠/展开属性面板（保存/恢复宽度，切换箭头方向） |
| `toggleLeftSubmenu(button)` | 展开/折叠菜单子项，切换 ▶/▼ |
| `openTemplatesPanel()` | 取消所有导航高亮 → 高亮模板库 → 打开面板 → 加载模板库 HTML |
| `openDatasetPanel(datasetKey)` | 加载数据集编辑面板 |
| `switchPanelLang(url, langCode)` | 切换面板语言 → 同步预览 iframe URL 和语言路径 |
| `selectModuleInPanel(index, pageKey)` | 手风琴方式选中面板中的模块（折叠其他，展开目标，滚动到视图） |
| `installPreviewCanvasHandlers()` | 向预览 iframe 注入 CSS + click 事件 |
| `pageKeyFromPreviewPath(pathname)` | 从 iframe URL 推导当前页面 key |
| `previewUrlForPage(pageKey)` | 根据页面 key 和当前语言拼预览 URL |
| `currentPreviewLanguage()` | 从 iframe URL 提取当前预览语言 |
| `openPreviewTab(pageKey, title, url)` | 打开或切换到指定标签页 |
| `closePreviewTab(tabEl)` | 关闭标签页（至少保留一个），自动切到相邻标签 |
| `switchPreviewTab(tabEl)` | 切换活跃标签，更新 iframe src 和 URL 栏 |
| `syncLeftMenuWithTab()` | 当前活跃标签对应左侧菜单项时高亮，否则取消所有高亮 |

## 十四、CSRF 保护

### 14.1 meta 标签

```html
<meta name="csrf-token" content="{{ csrf_token() }}">
```

### 14.2 fetch 自动注入

```javascript
var origFetch = window.fetch;
window.fetch = function(input, init) {
  var method = (init.method || 'GET').toUpperCase();
  if (method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS') {
    init.headers.set('X-CSRFToken', token);
  }
  return origFetch.call(this, input, init);
};
```

全局包装 `window.fetch`——所有非 GET/HEAD/OPTIONS 的同源请求自动带上 `X-CSRFToken` 请求头。表单内的 `csrf` hidden input 对传统表单提交仍然有效，fetch 包装主要覆盖 fetch+JSON 的调用。

## 十五、和访客端 base 的对比

| | 访客端 `_base.html` | 后台 `base.html` |
| --- | --- | --- |
| 文件 | `themes/<name>/layouts/_base.html` | `app/templates/base.html` |
| 渲染方式 | builder 静态生成 | Flask 服务器渲染 |
| 顶栏 | 主题 header 变体（Jinja2 include） | 固定 `admin-header`（SVG logo + 站点切换 + 操作按钮） |
| 布局插槽 | `{% block content %}` | `{% block content %}`（右面板内容） |
| CSS 变量 | `:root` 注入用户选的主题色 | `:root` 覆盖 BS5 组件色（`admin_primary`） |
| JS | 可选几行内联 | Popper + BS5 JS + 大量内联（拖拽、面板加载、iframe 交互） |
| 多用户 | 不涉及（单站静态生成） | `user.email`、`site.id`、`available_sites` |
| 核心机制 | 模块排序 → 静态 HTML | AJAX 面板 + iframe 预览 + 实时构建 |

## 十六、关键规则

- **三栏布局不用 CSS Grid，用 flex**——左栏和中栏的宽度需要 JS 动态调整，flex 比 grid 好控制。
- **拖拽用遮罩不用 iframe 事件**——iframe 会吞 `mousemove`，全屏透明遮罩是唯一可靠方案。
- **左侧导航拖拽带阈值吸附**——140px 以下自动收缩到 60px，以上保留自定义宽度。
- **面板内容走 `_fragment=1`**——后端只返回内容片段，不含 base.html 外壳。
- **保存按钮自动移到底部**——`loadPanel()` 和表单提交回调都会把 `.panel-save-bar` 移到 `#rightPanelFooter`。
- **`runPanelScripts()` 重新创建 script 元素**——`innerHTML` 注入的 `<script>` 不会自动执行，必须 `createElement('script')` 替换。
- **CSRF 双重覆盖**——表单用 hidden input，fetch 用请求头包装。
- **顶栏不放站点导航**——站点切换用侧栏，顶栏只放操作按钮和退出。
- **颜色选择器自动转换**——`initColorPickers()` 把原生 `<input type="color">` 转为自定义色块，全局和面板加载后都调用。
