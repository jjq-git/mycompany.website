---
name: template-edit-template-style
description: "修改网站模板前端样式(访客看到的网站外观)"
---

当用户想调整面向访客的网站外观时触发.典型场景:
- 调整模板配色、字体、间距
- 修改某个 Block 的展示样式
- 调整网站 Header / Footer 布局
- 给 Block 增加新的样式变体
- 修改响应式断点

模板样式有三层:主题变量(后台注入)→ 全局 CSS(main.css)→ Block 内联样式.

## 确定修改范围和层级

先确认要修改哪个模板和哪个层级:

| 层级 | 位置 | 影响范围 | 修改方式 |
|------|------|----------|----------|
| 主题色变量 | `_base.html` 内联 `<style>`(构建时注入) | 整个模板的颜色体系 | 后台"主题颜色"面板设置 |
| 全局样式 | `static/css/main.css` | 所有页面和 Block | 直接编辑 CSS 文件 |
| Block 样式 | `blocks/<name>/template.html` 内联 | 单个 Block 的结构和 JS | 编辑 Block 模板 |
| 布局结构 | `templates/_base.html`、`_page.html` | 整体页面骨架 | 编辑模板 HTML |

**主题色变量优先**:如果只是换颜色,通过后台"主题颜色"面板设置,不要直接改 main.css.
构建时主题变量注入到 `_base.html` 的 `<style>` 中,覆盖 `:root` 中的默认值.

## CSS 架构约定

模板 CSS(`site_templates/<name>/static/css/main.css`)的分区组织:

```
1. CSS Design Tokens      (:root 变量 —— 颜色、字体、间距、阴影)
2. 排版与工具类            (h1-h6、.container、间距 class)
3. 布局                    (Header、Footer、导航、网格)
4. 通用组件                (按钮、卡片、表单、标签)
5. Block 样式区            (各 Block 的 CSS,按 Block 名分组)
6. 响应式                  (@media 查询,按断点组织)
```

核心规则:
- **颜色用 `var(--color-*)` 引用**,不硬编码色值
  ```css
  /* 正确 */
  .btn-primary { background: var(--color-accent); }

  /* 错误 */
  .btn-primary { background: #067a7a; }
  ```
- **字体用 CSS 变量**:`font-family: var(--font-family-base);`
- 新增样式追加到对应分区末尾,不散落在文件各处
- 模板面向访客,**必须做响应式适配**(与后台不同)

## CSS Design Tokens 体系

`:root` 中定义的 CSS 变量(模板默认值,可被后台主题色覆盖):

```css
:root {
  /* 颜色 */
  --color-accent: #067a7a;        /* 主色 */
  --color-accent-hover: #056666;  /* 主色悬停 */
  --color-accent-light: #e6f2f2;  /* 主色浅底 */
  --color-bg: #ffffff;            /* 背景色 */
  --color-surface: #f8fafc;       /* 卡片/区块背景 */
  --color-text: #1e293b;          /* 主文字 */
  --color-text-muted: #64748b;    /* 次文字 */
  --color-text-light: #94a3b8;    /* 三级文字 */
  --color-border: #e8ecf0;        /* 边框 */
  --color-border-light: #f1f5f9;  /* 细边框 */

  /* 字体 */
  --font-family-base: 'Inter', 'Noto Sans SC', -apple-system, sans-serif;
  --font-family-heading: 'Inter', 'Noto Sans SC', -apple-system, sans-serif;
  --font-size-xs: 0.75rem;        /* 12px */
  --font-size-sm: 0.875rem;       /* 14px */
  --font-size-base: 1rem;         /* 16px */
  --font-size-lg: 1.125rem;       /* 18px */
  --font-size-xl: 1.25rem;        /* 20px */
  --font-size-2xl: 1.5rem;        /* 24px */
  --font-size-3xl: 2rem;          /* 32px */

  /* 间距 */
  --space-xs: 0.25rem;            /* 4px */
  --space-sm: 0.5rem;             /* 8px */
  --space-md: 1rem;               /* 16px */
  --space-lg: 1.5rem;             /* 24px */
  --space-xl: 2rem;               /* 32px */
  --space-2xl: 3rem;              /* 48px */

  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
  --shadow-lg: 0 10px 25px rgba(0,0,0,0.1);

  /* 圆角 */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
}
```

## 修改全局样式

编辑 `site_templates/<name>/static/css/main.css`.

示例修改:

**调整字体大小**:
```css
/* 原来:--font-size-base: 1rem */
:root {
  --font-size-base: 1.0625rem;  /* 17px,稍微大一点 */
}
```

**调整卡片间距**:
```css
/* 在 Block 样式区找到 .product-card */
.product-card {
  padding: var(--space-lg);  /* 原来是 var(--space-md) */
  gap: var(--space-md);      /* 原来是 var(--space-sm) */
}
```

**调整按钮样式**:
```css
.btn-primary {
  background: var(--color-accent);
  border-radius: var(--radius-md);
  padding: 12px 24px;        /* 原来是 8px 20px */
  font-weight: 600;           /* 原来是 500 */
}
```

## 修改 Block 样式

Block 模板(`blocks/<name>/template.html`)中有两类样式:

**动态样式**(用户可配置的):
渲染为内联 `style` 属性,不需要手动改 CSS:
```html
<h2 style="font-size: {{ data.title_size }}px; color: {{ data.title_color }};">
  {{ data.title }}
</h2>
```

**固定样式**(Block 结构样式):
写在 `main.css` 中对应的 Block 分区:
```css
/* ====== hero_banner ====== */
.block-hero_banner {
  position: relative;
  overflow: hidden;
}
.block-hero_banner .slide {
  min-height: 60vh;
  display: flex;
  align-items: center;
}
.block-hero_banner .slide-title {
  font-size: var(--font-size-3xl);
  font-weight: 700;
}
```

**给 Block 添加新变体样式**:
```css
/* hero_banner --centered 变体 */
.block-hero_banner--centered {
  text-align: center;
}
.block-hero_banner--centered .slide {
  justify-content: center;
}
```

## 修改布局结构

三个核心模板文件的作用:

**`templates/_base.html`**:
- HTML 骨架(`<!DOCTYPE>` 到 `</html>`)
- CSS 加载(`<link rel="stylesheet">`)
- 主题色注入(`:root` 变量覆盖)
- Header/Footer 宏定义
- 网站全局 JS(导航、滚动等)
- `<head>` 注入点(百度统计、Google Analytics 等)

**`templates/_page.html`**:
- 通用页面布局:Header + `{% block content %}` + Footer
- 大多数页面继承它而不是直接继承 `_base.html`

**`templates/_modules.html`**:
- Block 渲染宏:遍历 `modules` 数组并 `{% include %}` 每个 Block 模板
- 如果需要限制 Block 渲染数量或加容器,在这里改

修改布局示例:
```html
<!-- _base.html:给 Header 增加阴影 -->
<header class="site-header" style="box-shadow: var(--shadow-sm);">
  ...
</header>
```

## 响应式设计

模板必须适配三种设备(与后台不同):

| 设备 | 断点 | 常见调整 |
|------|------|----------|
| 手机 | < 768px | 单列布局、汉堡菜单、缩小字号 |
| 平板 | 768px - 1024px | 双列布局、适中间距 |
| 桌面 | > 1024px | 多列布局、完整导航 |

```css
/* 平板 */
@media (max-width: 1024px) {
  .product-grid { grid-template-columns: repeat(2, 1fr); }
  .site-nav { display: none; }
  .hamburger-menu { display: block; }
}

/* 手机 */
@media (max-width: 767px) {
  .product-grid { grid-template-columns: 1fr; }
  .hero-banner .slide { min-height: 40vh; }
  .slide-title { font-size: var(--font-size-2xl); }
}
```

响应式测试方法:
1. 启动服务器 → 后台 → 站点预览
2. 浏览器 DevTools → 设备模拟(F12 → Toggle Device Toolbar)
3. 切换 iPhone SE / iPad / Desktop 三种尺寸查看
4. 或直接在预览 iframe 中使用设备切换按钮

## 改主题色的正确方式

通过后台"主题颜色"面板设置,不要直接改 main.css 默认变量值.

后台设置的逻辑(`routes.py:969-998`):
1. 店主在"设置 → 主题颜色"面板中输入色值
2. 保存到 `sites/<id>/settings.yaml` 的 `theme` 字段
3. 构建时 `builder.py:214-215` 合并模板默认主题和站点主题:
   `theme = {**theme_default, **(settings.get('theme') or {})}`
4. 注入到 `_base.html` 的 `<style>` 标签覆盖 `:root` 变量

如果要给模板增加新的主题变量:
1. 在 `main.css` 的 `:root` 中添加变量
2. 在 `meta.yaml` 的 `default_theme` 中添加默认值
3. 在后台主题面板中添加对应的输入框(`panel_theme.html`)

## 字体配置

中文字体对网站体验影响巨大(信念 #5).模板中的字体配置:

```css
:root {
  --font-family-base: 'Inter', 'Noto Sans SC', -apple-system, 'PingFang SC',
                      'Microsoft YaHei', 'Helvetica Neue', sans-serif;
  --font-family-heading: 'Inter', 'Noto Sans SC', -apple-system, 'PingFang SC',
                         'Microsoft YaHei', sans-serif;
}
```

原则:
- 英文字体在前,中文字体在后(英文用 Inter,中文回落 Noto Sans SC)
- 系统字体兜底(PingFang SC、Microsoft YaHei)
- 不做 Google Fonts 外链(慢,且可能被墙)
- 字体文件在 `fonts/` 目录,通过 `@font-face` 加载子集化后的版本

## 预览验证

样式修改后验证:
1. `$env:FLASK_HOST='0.0.0.0'; $env:FLASK_DEBUG='1'; python run.py` 启动服务器
2. 后台 → 选择站点 → 预览
3. 在预览 iframe 中检查所有关键页面:首页、列表页、详情页
4. 在浏览器 DevTools 中切换设备尺寸检查响应式
5. 如果预览没变化 → 强制刷新(Ctrl+Shift+R)清除缓存
6. 如果还没变化 → 重新构建站点(`flask --app run build-site <id>`)

## 关联文件

| 文件 | 作用 |
|------|------|
| `site_templates/<name>/static/css/main.css` | 全局样式 |
| `site_templates/<name>/templates/_base.html` | HTML 骨架 + 主题注入 |
| `site_templates/<name>/templates/_page.html` | 通用页面布局 |
| `site_templates/<name>/templates/_modules.html` | Block 渲染宏 |
| `site_templates/<name>/blocks/<name>/template.html` | Block 模板 |
| `site_templates/<name>/meta.yaml` | 默认主题和变体定义 |
| `app/core/builder.py:214-215` | 主题合并逻辑 |

## 关联技能

- `new-template`:创建新模板时设计初始样式
- `new-block`:为 Block 添加配套 CSS
- `build-site`:样式修改后重新构建验证
- `edit-admin-style`:修改后台样式(不是前端)
