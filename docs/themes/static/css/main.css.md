# main.css：主题全局样式

`static/css/main.css` 是一套主题的**全部样式**——设计令牌、基础重置、通用组件、block 样式、响应式。构建时原样拷进 `output/.../static/css/main.css`。

不依赖任何前端框架，纯 CSS。

## 一、分层架构

一个文件从上到下分五层，每一层只依赖上一层：

```text
1. 设计令牌（:root 变量）
   │
2. 基础重置（reset + 元素默认样式）
   │
3. 通用组件（按钮 / Header / Footer / 面包屑 / 分页）
   │
4. Block 样式（Hero / Features / Products / Blog / CTA / Stats / Testimonials / Timeline / Contact / About）
   │
5. 响应式（@media 断点）
```

## 二、设计令牌（:root）

`_base.html` 在运行时把 `theme` 变量注入 `:root`，覆盖主题默认值。所以 `main.css` 里 `:root` 的每个变量都是**默认值**（用户不改时生效）：

```css
:root {
  --color-primary: #1a56db;
  --color-primary-dark: #1e40af;
  --color-primary-light: #dbeafe;
  --color-accent: #f59e0b;
  --color-text: #1f2937;
  --color-text-light: #6b7280;
  --color-bg: #ffffff;
  --color-bg-alt: #f9fafb;
  --color-bg-dark: #111827;
  --color-border: #e5e7eb;
  --font-family: system-ui, -apple-system, 'Segoe UI', 'Microsoft YaHei', sans-serif;
  --max-width: 1200px;
  --header-height: 72px;
  --radius: 8px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.1);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.1);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);
}
```

| 变量类别 | 覆盖方 | 说明 |
| --- | --- | --- |
| `--color-*` | 用户（`settings.theme`） | 用户选的主色、辅色，构建时注入 `:root` 覆盖默认 |
| `--font-family` | 用户（`settings.theme.font-sans`） | 字体栈，多语言站按语言覆盖字形 |
| `--max-width` / `--header-height` / `--radius` | 主题作者 | 布局尺寸，用户不改 |
| `--shadow-*` | 主题作者 | 阴影层级，用户不改 |

> 所有样式一律用 `var(--xxx)` 引用，不硬编码色值。详见 [README.md](../README.md) 第三节。

## 三、基础重置

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html { font-size: 16px; scroll-behavior: smooth; }

body {
  font-family: var(--font-family);
  color: var(--color-text);
  background: var(--color-bg);
  line-height: 1.6;
}

a { color: var(--color-primary); text-decoration: none; }
img { max-width: 100%; height: auto; display: block; }
```

标题层级（h1-h4）也在这里定义，统一行高和字重。

## 四、通用组件

页面上会反复出现的 UI 零件，独立于具体内容：

| 组件 | 选择器 | 说明 |
| --- | --- | --- |
| 容器 | `.container` | `max-width: var(--max-width)` + 居中 + 两侧内边距 |
| 按钮 | `.btn` / `.btn-primary` / `.btn-outline` | 主按钮（实心）+ 次按钮（描边），用 `var(--radius)` |
| Header | `.site-header` | sticky 定位、毛玻璃背景、Logo、导航、子菜单、语言切换器 |
| Footer | `.site-footer` | 深色背景、多列链接网格、版权栏 |
| 面包屑 | `.breadcrumb` | 灰色小字 + 分隔符 |
| 分页 | `.pagination` | 居中按钮列表 |
| 页面横幅 | `.page-header` | 渐变色背景 + 居中大标题 |
| 汉堡菜单 | `.mobile-toggle` | 默认隐藏，768px 以下显示 |

### 导航子菜单

```css
.main-nav .sub-nav { display: none; position: absolute; top: 100%; left: 0; }
.main-nav .nav-item.has-children:hover > .sub-nav { display: block; }
```

纯 CSS hover 弹出，不依赖 JS。移动端退化为静态展开（在媒体查询里覆盖）。

## 五、Block 样式

每个 block 对应一个 CSS 区块（section），命名约定：`<block名>-section` / `<block名>-grid` / `<block名>-card`。

| Block | 选择器 | 特点 |
| --- | --- | --- |
| Hero | `.hero-section` | 全宽背景图、暗色蒙版、居中内容、双按钮 |
| Features | `.features-section` + `.features-grid` | 栅格卡片，列数由 `--cols` 控制 |
| Stats | `.stats-section` + `.stats-grid` | 数字 + 标签，大字号主色数字 |
| Products | `.products-section` + `.products-grid` + `.product-card` | 图 + 名称 + 摘要，hover 阴影 |
| Blog | `.blog-section` + `.blog-grid` + `.blog-card` | 图 + 日期 + 标题 + 摘要 |
| CTA | `.cta-section` | 渐变背景，白色文字，白色描边按钮 |
| About | `.about-section` + `.about-layout` | 图文左右排列，`--dir` 控制方向 |
| Testimonials | `.testimonials-section` + `.testimonials-grid` + `.testimonial-card` | 头像 + 引语 + 名字 |
| Timeline | `.timeline-section` + `.timeline` + `.timeline-event` | 中轴线 + 左右交替排列 |
| Contact | `.contact-section` + `.contact-grid` + `.contact-info` | 信息列表 + 表单区域 |

### Grid 列数用 CSS 变量

```css
.features-grid {
  display: grid;
  gap: 2rem;
  grid-template-columns: repeat(var(--cols, 3), 1fr);
}
```

`--cols` 默认 3。用户通过 `data-style="cols"` 可调为 2 或 4——`_base.html` 把用户选择写到元素 `style="--cols: 4"` 上，覆盖 CSS 默认值。没打开的 block 不暴露 `--cols`，兜底值（3）始终生效。

## 六、响应式

三个断点，移动优先（覆盖式）：

| 断点 | 命中设备 | 主要调整 |
| --- | --- | --- |
| `≤1024px` | 平板横屏 | 产品/博客/Features 从 3 列变 2 列；产品详情图文上下排列；About 强制竖排 |
| `≤768px` | 平板竖屏 / 大屏手机 | Header 显示汉堡菜单、导航折叠；Hero 缩小；所有 grid 最低 2 列；时间线从双栏变单栏 |
| `≤480px` | 小屏手机 | 所有 grid 变单列；Hero 按钮竖排 |

```css
@media (max-width: 768px) {
  .mobile-toggle { display: block; }
  .main-nav { display: none; }
  .main-nav.open { display: block; }
  .main-nav .nav-list { flex-direction: column; }
}
```

移动端菜单展开/收起用 JS 给 `.main-nav` 加 `.open` 类（`scripts` block 里写几行 JS），CSS 只管显示/隐藏。

## 七、关键规则

- **不依赖框架**——纯 CSS，无 Tailwind / Bootstrap。
- **色值一律 `var(--xxx)`**——不出现 `#1a56db` 这样的硬编码色值（只在 `:root` 里定义一次）。
- **block 样式跟 block 名**——`blocks/hero/` 的样式在 `main.css` 里写 `.hero-section`，一个 block 一个区块，不跨 block 混写。
- **Grid 列数用 `--cols`**——不在媒体查询里写死 `grid-template-columns: repeat(3, 1fr)`，用 `var(--cols, 3)` 兜底，用户可覆盖。
- **响应式只做布局调整**——不改颜色、不改字体、不改间距逻辑，只调 grid 列数和 flex 方向。
- **JS 保持最少**——只有移动端菜单切换需要几行 JS（`.open` 类的 toggle），其余交互（hover、transition）全用 CSS。
- **字体栈中西结合**——`system-ui` 兜底西文、`Microsoft YaHei` 兜底中文，具体字体由 `settings.theme.font-sans` 覆盖。
