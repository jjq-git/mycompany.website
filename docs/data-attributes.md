# data-* 属性全量清单

| 属性 | 位置 | 消费方式 | 用途 |
|---|---|---|---|
| `data-target` | `stat_counter` block: `.sc-number` div | `getAttribute('data-target')` | 数字滚动动画的目标值 |
| `data-slide` | `hero_banner` block: `.hero-banner-dot` button | `getAttribute('data-slide')` | 轮播指示器点击定位到对应 slide |
| `data-block-id` | `data_grid` block: `.dg-page-btn` / `.dg-load-more` | `btn.dataset.blockId` | 标识 data grid 实例，避免多实例冲突 |
| `data-page` | `data_grid` block: `.dg-page-btn` / `.dg-load-more` | `btn.dataset.page` | 当前页码 |
| `data-per-page` | `data_grid` block: `.dg-page-btn` / `.dg-load-more` | `btn.dataset.perPage` | 每页显示条数 |
| `data-total` | `data_grid` block: `.dg-load-more` | `btn.dataset.total` | 数据总条数，判断"加载更多"按钮是否隐藏 |
| `data-panel` | `base.html` 左侧导航 `<a>` | `querySelector('[data-panel="..."]')` | 导航项对应的面板名称，加载右侧面板和匹配路由 |
| `data-preview-page` | `base.html` 左侧导航 `<a>` | `link.dataset.previewPage` | 点击后在预览 iframe 中显示的页面路径 |
| `data-preview-url` | `base.html` 预览 iframe | `f.dataset.previewUrl` / `frame.dataset.previewUrl = ...` | 预览 iframe 的当前 URL |
| `data-href` | `panel_templates.html` 模板卡片按钮 | `this.dataset.href` → `loadPanel()` | 模板卡片上存储的面板加载 URL |
| `data-level` | `base.html` 菜单组容器 | CSS / JS 间接 | 菜单组的嵌套层级 |
| `data-device` | 预览设备按钮（`base.html` / `page_home.html` / `panel_page_edit.html`） | `querySelector('[data-device="..."]')` | 预览设备类型：`desktop` / `tablet` / `mobile` |
| `data-module-index` | 各页面 `.module-item` 和编辑器容器 | `querySelector('[data-module-index="..."]')` | 模块在页面中的索引，**模块编辑器最核心属性**，用于增删改查子项 |
| `data-page-key` | 各页面 `<form>` | `form.dataset.pageKey` | 表单关联的页面标识（如 `"home"`、`"products"`），用于 AJAX 提交后匹配右侧面板 |
| `data-builder-region` | `base.html` 构建器预览区 | `regionEl.dataset.builderRegion` → 加载 header/footer 设置 | 构建器区域标识：`header` / `footer_variant` |
| `data-builder-module-index` | `base.html` 构建器预览区模块 | `moduleEl.dataset.builderModuleIndex` → 联动选中编辑面板中的模块 | 预览区点击模块后联动选中右侧面板对应模块 |
| `data-block-name` | `.block-card`（`page_home.html` / `panel_page_edit.html` / `panel_data_list.html`） | `card.dataset.blockName` → `addModule()` | 点击 block 卡片时获取 block 名称 |
| `data-block-variant` | `.block-card` | `card.dataset.blockVariant` → `addModule()` | block 的变体标识（如 `default`） |
| `data-slide-index` | `hero_banner` 模块: `.hero-slide-item` | `item.dataset.slideIndex = idx` → 重排索引 | 轮播子项序号 |
| `data-feature-index` | `feature_grid` 模块: `.feature-item` | `item.dataset.featureIndex = idx` → 重排索引 | 特性子项序号 |
| `data-image-index` | `item_detail` 模块: `.id-image-item` | `item.dataset.imageIndex = i` → 重排索引 | 图片子项序号 |
| `data-spec-index` | `item_detail` 模块: `.id-spec-item` | `item.dataset.specIndex = i` → 重排索引 | 规格子项序号 |
| `data-item-index` | `stat_counter` / `logo_cloud` / `process_steps`: `.list-item` | `item.dataset.itemIndex = idx` → 重排索引 | 通用列表子项序号 |
| `data-tab` | `panel_page_edit.html` 各模块 `.content-style-tab` 按钮 | `onclick="switchContentStyleTab(this, 'content')"` / `onclick="switchContentStyleTab(this, 'style')"` | 切换模块编辑器的"内容"和"样式" Tab |
| `data-type` | `menu.html` / `panel_menu.html` 菜单行 | `tr.dataset.type` / CSS `[data-type="home"]` | 菜单项类型：`home` `list` `page` `link` `group` |
| `data-depth` | `panel_menu.html` 菜单树行 | `row.dataset.depth = depth`（JS 写入） | 菜单项嵌套深度 |
| `data-ajax-handled` | `base.html` 表单提交逻辑 | `form.dataset.ajaxHandled` | 防止表单重复 AJAX 提交 |
| `data-saved-width` | `base.html` 右侧面板 | `panel.dataset.savedWidth`（JS 运行时读写） | 用户拖拽调整面板宽度后记住宽度 |
| `data-bs-dismiss` | 所有模态框关闭/取消按钮 | Bootstrap 5 JS 自动处理 | 关闭当前模态框 |
| `data-bs-toggle="dropdown"` | `base.html` 站点切换按钮 | Bootstrap 5 JS 自动处理 | 切换下拉菜单 |
| `data-bs-toggle="modal"` | Block 选择器触发按钮 | Bootstrap 5 JS 自动处理 | 打开 Block 选择器模态框 |
| `data-bs-target` | 与 `data-bs-toggle="modal"` 配合 | Bootstrap 5 JS 自动处理 | 指定要打开的模态框 ID |

