# Issue #8：整体界面改造

> 工单：[learn_data_github/mycompany.website#8](http://192.168.1.88:3000/learn_data_github/mycompany.website/issues/8)  
> 标题：整体界面  
> 创建人：YoungGu  
> 创建时间：2026-07-08 16:13:41（UTC+8）  
> 状态：Open  
> 工单最后更新时间：2026-07-08 16:55:18（UTC+8）

## 1. 文档范围

本文档整理工单中已经明确提出的界面要求，并结合当前代码标注可能涉及的文件。

- “需求与验收标准”以工单原文为准。
- “当前实现与代码位置”仅用于开发定位，不等同于已经确定的技术方案。
- 工单没有说明的交互、接口、数据结构和权限展示方式，不在本文档中自行补充。

## 2. 顶部区域（工单图 A）

### 2.1 Logo 与 favicon

需求：

- 将后台顶部 Logo 和 favicon 替换为工单附件
  [`icon.svg`](http://192.168.1.88:3000/attachments/b64d2aa5-dd2b-4922-b44e-033e6a24df06)。
- 移除顶部的 `mycompany.website` 文字。

验收标准：

- 浏览器标签页与顶部区域使用同一版新图标。
- 顶部不再显示 `mycompany.website` 品牌文字。
- 图标资源保存在本地，不依赖外部地址。

当前实现与代码位置：

- `app/templates/base.html`：顶部内联 SVG、`.admin-brand` 和 `<link rel="icon">`。
- `app/__init__.py`：`_serve_favicon()` 当前返回内联 SVG。
- `app/static/css/admin.css`：`.admin-logo`、`.admin-brand` 的样式。

### 2.2 站点选择去重（这条事实上不是重复，只是凑巧文字一样）

需求：

- 修复站点下拉列表中的重复项，例如 `rimu/rimu`。

验收标准：

- 每个站点在列表中只出现一次。
- 当前站点仍能正确高亮，切换站点功能不受影响。

实现前需要确认重复的来源：`available_sites` 中存在重复记录，还是同一项同时显示了站点名称和 slug。不要仅通过 CSS 隐藏重复内容。

当前实现与代码位置：

- `app/templates/base.html`：`available_sites` 循环及站点项的“名称 + `/slug`”显示。
- `app/core/routes.py`：后台模板上下文及 `available_sites` 的生成逻辑。

### 2.3 语言切换改为国旗

需求：

- 取消语言下拉框。
- 使用横向排列的国旗图标切换语言。
- 国旗资源取自 [Flag Icons](https://flagicons.lipis.dev/) 并下载到本地。
- “语言”入口同时放到用户区域下方。

验收标准：

- 当前可用语言均有对应入口，点击后能切换到该语言。
- 当前语言有明确的选中状态，并提供可访问的语言名称（如 `title` 或 `aria-label`），不能只依赖国旗辨识语言。
- 页面运行时不请求 Flag Icons 网站。

待确认：

- “顶部横向国旗”与“用户区域下方的语言入口”是否需要同时保留。工单两处描述可能表示同时存在，也可能表示最终只保留用户区域中的入口，实施前应由产品确认。
- 语言与国家并非一一对应；例如 `zh-CN`、`zh-TW` 应采用什么旗帜，需要确认映射规则。

当前实现与代码位置：

- `app/templates/base.html`：`#siteLangDropdown`、`admin_languages` 和 `current_lang`。
- `app/static/css/admin.css`：顶部按钮样式；需要补充国旗列表样式。
- 建议将本地图标放入 `app/static/flags/`，最终路径以项目静态资源约定为准。

### 2.4 顶部操作与用户区域

需求：

- 移除独立的“新建站点”按钮。
- 将“站点”“语言”“下载/导出”“发布”和“模板库”入口移到用户区域下方。
- 用户区域的图标改为正方形。
- 顶部最终只保留工单所述的“查看”“退出”和“头像”按钮。
- 顶部字体大小统一为 `14px`。

说明：

- 当前代码中的对应操作名称是“预览”“导出”“发布”。工单中的“查看”“下载”是否分别对应“预览”“导出”，需要按工单截图确认。
- “模板库”移入用户区域后，工单明确说明不在该处重新选择模板；因此入口的具体行为需要确认，不能默认沿用当前模板切换/新建站点行为。
- 工单使用“用户下面”描述目标位置，未明确要求使用下拉菜单、弹层或独立面板，不应在文档中提前锁定交互形式。

验收标准：

- 顶部不再显示“新建站点”、导出和发布的独立按钮。
- 移动后的入口仍保持原有功能和权限约束。
- 用户图标的可视区域宽高一致。
- 顶部文字的计算字号为 `14px`。

当前实现与代码位置：

- `app/templates/base.html`：顶部站点/语言、“新建站点”、预览、导出、发布、退出和头像入口。
- `app/templates/dashboard/panel_account.html`：当前头像点击后打开的账户面板；如继续复用该面板，需要在此承载移动后的入口。
- `app/static/css/admin.css`：`.admin-header`、`.header-btn`、`.admin-avatar`。

## 3. 左侧区域（工单图 B）

### 3.1 站点名称与语言国旗

需求：

- 左侧顶部显示当前网站名称和当前语言对应的国旗。

验收标准：

- 切换站点或语言后，名称和国旗同步更新。
- 国旗带有可访问的语言文本。

当前实现与代码位置：

- `app/templates/base.html`：`.left-nav-site-info` 当前显示站点名称和语言文字。
- `app/static/css/admin.css`：`.left-nav-site-info` 及侧栏折叠状态样式。

### 3.2 移走“站点 / 模板库”

需求：

- 将左侧“站点”分组及“模板库”入口移到用户区域下方。
- 不在移动后的入口中重新选择模板。

验收标准：

- 左侧不再显示“站点”分组和“模板库”入口。
- 用户区域中可找到对应入口。
- 入口行为符合产品确认后的定义，不误触发模板更换。

### 3.3 修复“网站设置”无响应

需求：

- 点击左侧菜单中的“网站设置”文字或所在行时，应展开或收起其下级菜单。当前只有点击右侧箭头才会展开。
- 可设置网站颜色、字体和文字大小。
- 中间区域实时显示预览效果。

验收标准：

- 点击“网站设置”文字、图标或所在行的空白区域，与点击右侧箭头具有相同的展开/收起效果。
- 点击“网站设置”父级只控制下级菜单，不直接跳转或打开设置面板。
- 右侧箭头随状态变化，并通过 `aria-expanded` 表达当前展开状态。
- 下级菜单中的具体设置项仍可正常点击和打开。
- 修改颜色、字体或文字大小后，中间预览可见更新。
- 保存、取消及刷新后的状态遵循现有设置页规则。

当前实现与代码位置：

- `app/templates/base.html`：`.left-nav-parent-label` 当前没有展开事件，只有右侧 `.left-nav-chevron-btn` 调用 `toggleLeftSubmenu()`；应让父级行的非链接区域复用同一展开逻辑。
- `app/templates/dashboard/panel_basic_settings.html`：基本设置面板。
- `app/templates/dashboard/panel_theme.html`：已有主题色、字体和字号相关界面，应优先评估复用。
- `app/templates/dashboard/basic_settings_embed.html`：独立设置页面。

待确认：

- 实时预览是仅临时预览，还是同时持久化设置。

## 4. SEO 页面

### 4.1 顶部标题区（工单图“标题-1”）

需求：

- 顶部标题与当前网页的数据关联，而不是只显示整个站点的数据。
- 增加“全站设置”入口。
- 全站设置中集中显示：
  - `robots.txt` 是否误屏蔽页面；
  - 哪些页面包含 `noindex`；
  - `sitemap.xml`；
  - AI 使用的文本索引文件；
  - 原“系统检查”内容。

说明：

- 工单中的 `llm.txt` 是笔误，正确文件名为 `llms.txt`；界面、检查逻辑和生成逻辑均统一使用 `llms.txt`。
- 工单说全站设置内容“需要优化”，未明确要求这些文件可在线编辑或重新生成；第一阶段至少应能展示检查结果。

验收标准：

- 切换 SEO 页面列表中的网页时，标题区同步展示该网页的数据。
- 全站设置入口可访问上述检查内容。
- `robots.txt` 检查能区分“文件存在”和“规则可能误屏蔽页面”，不能只检查文件是否生成。
- `noindex` 检查能列出具体页面。

当前实现与代码位置：

- `app/templates/dashboard/seo_workspace.html`：SEO 工作区、页面列表和右侧内容加载。
- `app/templates/dashboard/_seo_health_content.html`：当前健康检查内容。
- `app/core/routes.py`：`_seo_health_report()` 当前检查 `robots.txt`、`sitemap.xml`、`llms.txt` 是否存在，但尚未完成规则级的误屏蔽与 `noindex` 页面检查。

### 4.2 左侧页面列表（工单图“左侧-2”）

需求：

- 页面列表按网站菜单层级显示。包含下级页面的父级栏目可以展开和收缩，下级页面默认收起，以便用户先看到页面结构全貌。
- 父级页面名称仍用于选择该页面；展开/收缩使用独立的箭头按钮，避免点击父级名称时同时触发两种操作。例如“LED 灯条”可选择自身，也可通过箭头展开或收起其下的多个详情页。
- 每个页面使用 Material Symbols/Icons 的 `looks_one`、`looks_two`、`looks_3`、`looks_4`、`looks_5` 显示 1～5 分。
- 分数颜色从红色过渡到黄色、绿色。

验收标准：

- 首次进入时，有下级页面的父级栏目默认收起；没有下级的页面正常显示。
- 父级栏目旁显示明确的展开/收缩按钮，按钮状态具有 `aria-expanded` 等可访问性信息。
- 展开后，下级页面按正确层级缩进显示；多级页面树可以逐级展开和收缩。
- 点击父级页面名称只选择并打开父级页面，点击箭头只改变下级页面的展开状态。
- 当前选中页位于已收起的分支中时，其祖先分支应自动展开，保证当前页面清晰可见。
- 每个页面都有 1～5 的确定分数，并有非颜色提示，不能只靠颜色表达结果。
- 评分规则固定、可解释，相同数据得到相同分数。

待确认：

- 1～5 分的计算规则和各颜色阈值。当前代码只有全站 0～100 分及页面 `ok/auto/warn` 状态，不能直接等同于工单要求的逐页五级评分。

当前实现与代码位置：

- `app/templates/dashboard/seo_workspace.html`：`.seo-sidebar` 和页面列表。
- `app/static/css/admin-seo.css`：SEO 侧栏与状态样式。
- `app/core/routes.py`：`_seo_health_report()`、`_seo_page_rows()` 等报告数据。

### 4.3 详细信息区（工单图“详细信息-3”）

每个当前网页至少展示以下项目：

1. URL：显示 URL 要求说明。
2. 标题：显示标题要求说明。
3. H1：检查页面是否只有一个 H1，并检查后续标题是否按 H2、H3 等层级组织。
4. Meta Description：显示描述要求说明。
5. 图片 alt：列出当前网页使用的全部图片及其 alt 状态。
6. 结构化数据、Open Graph、Twitter Card：补充检查项和建议。
7. 每个可编辑输入框后增加 `auto_awesome` AI 按钮。

验收标准：

- 所有检查都以当前网页为范围，切换网页后结果同步变化。
- URL、标题和 Meta Description 的要求说明具体且可执行；字数或长度阈值需要产品/SEO 规则确认后固定。
- H1 检查基于最终渲染结果，能报告 H1 数量和标题层级问题；不能仅假设模板一定正确。
- 图片检查覆盖当前网页最终渲染出的所有图片，并区分“缺少 `alt` 属性”和“空 `alt`”。装饰性图片允许使用空 `alt`，不应一律判错。
- 结构化数据、Open Graph 和 Twitter Card 显示实际检测结果。工单中的“咨询一下 AI”表示需求尚需细化，不能直接解释为运行时必须调用 AI。

当前实现与差距：

- 当前 SEO 工作区已有页面标题、描述编辑和部分图片 alt 修复能力。
- 当前 alt 健康检查主要检查详情数据中的部分常见图片字段，不等同于“当前网页最终渲染出的所有图片”。
- 当前代码尚未完整提供 URL 规则、最终 HTML 的 H1 层级、结构化数据、Open Graph 和 Twitter Card 的逐页检查结果。

## 5. AI 按钮与权限

需求：

- 在每个可编辑输入框后显示 Material Symbols/Icons 的 `auto_awesome` 按钮。
- 点击按钮调用 AI，生成或优化对应字段。
- AI 功能与用户权限或 token 余额关联。
- 无 AI 权限或 token 不足时，弹出“token 不足”提示。

验收标准：

- 按钮作用于它所在的字段，不覆盖其他字段。
- 调用中有加载和防重复提交状态；失败时保留原值。
- 服务端必须校验权限或额度，不能只做前端判断。
- token 不足时不发起生成，或由服务端拒绝后统一显示明确提示。

待确认：

- 哪些字段属于“每个输入框”的范围；H1 和图片 alt 检查结果是否也允许 AI 修改。
- token 的数据来源、扣减时机、计费规则和并发处理。
- 工单只规定无权限时弹框，没有要求隐藏 AI 按钮，因此本文档不把“隐藏按钮”列为需求。

当前实现与代码位置：

- `app/core/translator.py`：已有 AI 翻译及 SEO 描述生成相关能力，但不等同于完整的用户 token 计费系统。
- `app/core/routes.py`：已有页面 SEO 描述生成/保存流程；需要评估权限校验和额度能力。
- `app/templates/dashboard/seo_workspace.html`、`app/templates/dashboard/_seo_health_content.html`：现有 SEO 交互。
- `app/static/css/admin-seo.css`：AI 按钮、加载态和提示样式可放在此处。

## 6. 预计涉及的文件

以下是根据当前代码得出的定位结果，不是排他清单：

| 区域 | 主要文件 | 现有职责 |
|---|---|---|
| 顶部与左侧导航 | `app/templates/base.html` | 顶部工具栏、站点/语言入口、用户头像、左侧导航 |
| 账户/用户区域 | `app/templates/dashboard/panel_account.html` | 头像点击后的账户面板 |
| 后台通用样式 | `app/static/css/admin.css` | 顶部、头像、左侧导航样式 |
| favicon | `app/__init__.py` | `/favicon.ico` 响应 |
| 网站设置 | `app/templates/dashboard/panel_basic_settings.html`、`panel_theme.html` | 基本设置、主题色、字体、字号 |
| SEO 工作区 | `app/templates/dashboard/seo_workspace.html` | SEO 三栏布局、页面选择和交互 |
| SEO 检查内容 | `app/templates/dashboard/_seo_health_content.html` | 当前健康检查与编辑表单 |
| SEO 样式 | `app/static/css/admin-seo.css` | SEO 布局和状态样式 |
| SEO 数据与接口 | `app/core/routes.py` | SEO 报告、页面 SEO 保存、描述生成、alt 修复 |
| AI 能力 | `app/core/translator.py` | 现有 AI 调用与 SEO 描述生成 |

不应提前断言 `site_templates/`、`builder.py`、`models.py` 等文件一定无需修改。若逐页检查基于最终 HTML、需要持久化评分/token，或需要调整 `robots.txt`、`sitemap.xml`、`llms.txt` 的生成行为，这些位置可能也会受到影响。

## 7. 实施前必须确认的事项

1. 顶部“查看”“下载”是否分别对应当前的“预览”“导出”。
2. “模板库”移到用户区域后的准确行为。
3. 逐页 1～5 分的最终评分公式和颜色阈值。
4. URL、标题和 Meta Description 的最终业务规则。
5. AI token 的用户级余额来源、扣减和并发处理规则。

上述未确认项应作为产品问题处理；在确认前可以完成不依赖这些决策的界面整理，但不应把推测写成验收标准。
