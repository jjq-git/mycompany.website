# Block data-* 迁移：优化开发方案

> **设计规范参见 [block-data-attributes.md](block-data-attributes.md)。** 本文基于设计文档做逐 Block 分析和实施路径规划，不重复属性语法、扫描器输出格式等规范细节。

基于 `block-data-attributes.md` 设计文档，对全部 15 个 Block 做了逐模板分析，提取所有千奇百怪的模式，确保开发方案覆盖无死角。

## 一、全貌总览

### 1.1 Block 总览（系统共 15 个，2 个不迁移 → 实际迁移 13 个）

| 分类 | Block | 复杂度 | 核心特征 |
|---|---|---|---|
| **轮播/媒体** | hero_banner | 高 | CSS 字段+select+toggle+列表+轮播JS+视频/图片切换 |
| **结构化内容** | feature_grid | 中 | CSS 字段+列表+图标互斥组+多元素独立样式 |
| | section_title | 低 | 纯文本字段+CSS 样式+按钮 |
| | text_content | 低 | 纯文本字段+**富文本编辑器**(特殊控件) |
| | highlight_card | 中 | 文本字段+CSS 样式+**变体**(图左/图右) |
| **数据绑定** | data_grid | 高 | **数据集绑定**+动态字段映射+分类筛选+分页JS |
| | product_grid | 高 | **数据集绑定**(products)+卡片布局+分类筛选 |
| | item_detail | 中 | **双列表**(images/specs)+详情页渲染+图片放大镜JS（数据全在 module.data 中，自包含模块） |
| **列表型** | stat_counter | 中 | 列表+计数动画JS+图标映射+columns控制 |
| | logo_cloud | 中 | 列表+文件上传+灰度滤镜+columns控制 |
| | process_steps | 中 | 列表+**双变体**(direction+step_style 影响DOM结构)+图标映射 |
| **表单/联系** | contact_info | 中 | **跨数据源**(settings.contact)+visibility toggle×5 |
| | contact_form | 中 | **跨数据源**+visibility toggle×7+map嵌入+layout变体 |
| **特殊** | header | — | 站点导航(暂无 template.html，后续补充后同样改为零 Jinja2 模式) |
| | item_data | — | **条目编辑器(不迁移)**，含 isDatasetMode/editItem 特殊上下文 |

### 1.2 四个硬编码位置现状

| 位置 | 硬编码数量 | 涉及代码量 |
|---|---|---|
| `admin_modules.js` `buildModuleHTML()` | 15 个 `if type === 'xxx'` 分支 | ~780行 |
| `panel_page_edit.html` Jinja2 | 14 个 `{% elif module.type == 'xxx' %}` 分支 | ~1144行 |
| `panel_page_edit.html` `addModule()` JS | 14 个 `if (type === 'xxx')` 分支 | ~850行 |
| `routes.py` `_parse_modules_form()` | 6 个列表解析分支+hero_banner文件上传 | ~180行 |

## 二、所有边缘情况（按类型分类）

### 2.1 数据源模式

| 模式 | 出现位置 | data-* 处理方式 |
|---|---|---|
| `module.data.<key>` | 所有 Block | 标准——从 module_data 取值 |
| `settings.contact.<field>` | contact_info, contact_form | **新发现**——跨数据源取值。后处理函数需支持从 settings 取值 |
| `settings.layout.global_width` | 多个 Block | 已解决——管理后台预填，不需要模板访问 |
| `all_datasets.<name>` | data_grid, product_grid, item_detail | 数据集绑定——模板保留 Jinja2 `{% if all_datasets %}` |
| `products`/`portfolio`/`posts` | data_grid | 旧兼容——保留 Jinja2 fallback |
| `base_url`/`lang`/`current_path` | data_grid, product_grid, item_detail | 全局变量——模板保留 Jinja2 |

### 2.2 数据变换（需要在后处理或模板中处理）

| 变换 | 出现位置 | 处理方式 |
|---|---|---|
| `\| truncate(N)` | data_grid (description/excerpt) | **模板保留 Jinja2 filter**——内容注入不改数据格式 |
| `\| int` | data_grid (per_page, columns) | **模板保留**——类型转换不涉及 data-* |
| `\| default(x)` | data_grid, contact_info 等 | **模板保留**——item 级数据兜底 |
| `\| trim` | data_grid (tags split) | **模板保留** |
| `split(',')` + `[:5]` | data_grid (tags) | **模板保留**——数据加工逻辑 |
| `\| string` | data_grid (category比较) | **模板保留** |
| newline → `<br>` | contact_info (business_hours+weekend) | **新发现**——通过 `<meta data-field data-type="textarea">` 声明，模板用 `\| replace('\n', '<br>')` = 保留 Jinja2 filter |

### 2.3 复杂条件/变体（逐一精确分析）

**已确认可以替换（之前判断过于保守，现已纠正）：**

| 条件 | Block | 实际机制 | 替换方式 |
|---|---|---|---|
| `image_position` | highlight_card | 仅添加 `hl-grid--reverse` class → 等价 `flex-direction: row-reverse` | CSS 字段 `flex-direction`，meta select 覆盖选项标签(row=图左文右, row-reverse=文左图右) |
| `step_style` | process_steps | `{% if %}` 分支选择 SVG 或 `<span>` | data-when 互斥组（与 feature_grid 图标完全同模式） |
| `direction` | process_steps | 控制是否在 title+desc 外包 `<div class="ps-body">` | 模板始终包含包装层，CSS 处理横/纵向差异；`grid-template-columns: repeat(N, 1fr)` 保留 Jinja2 |
| `layout` | contact_form | 仅添加 `cf-layout--reverse` class → 等价 `flex-direction: row-reverse` | 与 image_position 相同 |

**已通过 CSS 字段解决：**

| 条件 | Block | 影响范围 | 替换方式 |
|---|---|---|---|
| `banner_align` | hero_banner | 1 个 CSS 属性 (text-align) | 模板改为 flexbox 布局，`data-label-text-align="内容排版"` + `<meta data-type="select">` 控制。详见下方迁移备注 |
| `card_layout` | data_grid | 两个不同元素的 CSS：容器 `grid-template-columns` + 卡片 `flex-direction` | 拆为两个独立的 CSS 字段，各自用 `data-label-*` + `<meta data-type="select">` 控制 |

**属于结构控制流（已由 `expand_repeat_items()` 替代）：**

| 条件 | 处理方式 |
|---|---|
| `{% for item in items %}` / `{% if items %}` | `expand_repeat_items()` 根据数据数组自动克隆 `data-type="list"` 的直接子元素，空数组时删除容器 |

**仍保留 Jinja2 的场景（与 data-* 无关）：**

| 条件 | Block | 原因 |
|---|---|---|
| `show_pagination` + `pagination_style` | data_grid | `{% for p in range(...) %}` 动态分页循环（动态计算，不是数据绑定列表） |
| `{% if images \| length > 1 %}` | item_detail | 列表长度判断（结构级条件）——但可通过 CSS 或 JS 处理 |

**已由设计文档解决：**

| 条件 | Block | 处理方式 |
|---|---|---|
| `{% if item.type == 'video' %}` | hero_banner | `data-when` 互斥组 |
| `show_phone/show_email/...` | contact_info/contact_form | `data-when` |
| `{% if item.title %}` / `{% if item.subtitle %}` | 多个 Block | 空值自动隐藏 |

> **hero_banner 内容排版迁移备注：** 旧模板用绝对定位 + `data-attr-style` 注入整段 CSS（left/right/transform/text-align），现 `data-attr-style` 已删除。迁移时需将 `.hero-banner-content` 从绝对定位改为 flexbox 布局：
> ```html
> <!-- 旧：绝对定位，依赖 data-attr-style 注入整段 CSS -->
> <div class="hero-banner-content" style="position: absolute; top: 50%; left: 50%;
>      transform: translate(-50%, -50%); text-align: center;"
>      data-attr-style="content_position">
> 
> <!-- 新：flexbox，text-align 作为独立 CSS 字段 -->
> <div class="hero-banner-content" style="display: flex; flex-direction: column;
>      justify-content: center; align-items: center; text-align: center;"
>      data-key="content" data-label-text-align="内容排版">
> ```
> 配合 `<meta>` 声明下拉选项：
> ```html
> <meta data-field="content_text_align" data-label="内容排版" data-type="select"
>       data-options="居中:center, 居左:left, 居右:right" data-default="center">
> ```
> 字段 key 生成规则：`data-key="content"` + CSS 属性 `text-align` → `content_text_align`。`inject_styles()` 自动将选中的值写入 `style` 末尾，覆盖默认值。

### 2.4 特殊 JS 交互

| JS 功能 | Block | 处理方式 |
|---|---|---|
| 轮播 (carousel) | hero_banner | **保留模板内 `<script>`**——data-* 不涉及 JS |
| 分页 (load more / page numbers) | data_grid | **保留模板内 `<script>`** + data-block-id 属性 |
| 计数动画 (count-up) | stat_counter | **保留模板内 `<script>`** |
| 图片放大镜 (magnifier) | item_detail | **保留模板内 `<script>`** |
| 富文本编辑器 (contenteditable → hidden textarea) | text_content | **保留 admin JS 特殊分支**——这是编辑器控件，不是模板字段 |
| 表单提交 | contact_form | **保留模板内 JS** |

### 2.5 非 CSS 字段的特殊类型

| 类型 | 出现位置 | 表单控件 |
|---|---|---|
| `visibility` | contact_info (5个), contact_form (7个) | 眼球开关 (visToggle) |
| `select` + `data-options` | 几乎所有 Block | 下拉选择 |
| `url` + 文件上传 | logo_cloud, highlight_card, hero_banner | 文本框+文件选择+图片预览 |
| `icon` (图标选择器) | feature_grid, stat_counter, process_steps | 图标选择器(从预定义列表中选) |
| `textarea` | text_content (body), section_title (desc), etc. | 多行文本 |
| Rich textarea (contenteditable) | text_content (body) | **保留特殊编辑器**——富文本工具栏 |

### 2.6 列表字段的特征差异

| Block | 列表 key | 每项字段数 | 特殊处理 |
|---|---|---|---|
| hero_banner | slides | 9 | 文件上传→自动判断 type (image/video) |
| feature_grid | features | 3 | icon 图标选择器 |
| stat_counter | stats | 4 | icon+number+suffix+label |
| logo_cloud | logos | 3 | image 文件上传 |
| process_steps | steps | 3 | icon+title+desc |
| item_detail | images | 1 | url 文件上传 |
| item_detail | specs | 2 | name+value (双列表) |

### 2.7 data-* 设计文档已覆盖但需要验证的模式

| 模式 | 设计位置 | 验证重点 |
|---|---|---|
| 图标互斥组 (data-when + data-type="default") | §2.5.2, §5.4 | SVG 数量是否正确保留/删除 |
| 空值自动隐藏 (data-content 等) | §2.5.1 | 模板默认文本是否被替换 |
| 内容注入 5 种属性 | §2.4 | data-content/src/href/bg/target 都正确替换 |
| CSS 级联覆盖 | §4.4.1 | 追加到 style 末尾，不修改默认值 |
| 多列表 (data-type="list") | §2.6 | item_detail 的 images+specs 双列表 |
| data-no-resp | §2.7 | hero_banner 不显示响应式控件 |
| global_width 预填 | §9.3-D | 新建模块时预填 settings.layout.global_width |

### 2.8 旧数据格式兼容

| 兼容场景 | 处理位置 | 方式 |
|---|---|---|
| hero_banner data 直接是列表 `[{type:...}]` | builder.py `_normalize_module_data()` | 包装为 `{slides: [...]}` |
| 旧 form 前缀 `module_N_slide_S_` | routes.py | 迁移后统一为 `module_N_data_slides_S_` |
| `_modules.html` 的 `module.type == 'hero_banner'` 判断 | §9.3-K | 简化掉 |

### 2.9 不能/不需迁移的边缘情况

**真正无法替换（保留 Jinja2）：**

| 情况 | 原因 |
|---|---|
| 数据集绑定 (`all_datasets`/`products`/`portfolio`/`posts`) | data_grid/product_grid 的动态数据源解析（字段定义由数据集 schema 决定，非模板静态声明） |
| `show_pagination` + `pagination_style` 动态分页 | `{% for p in range(...) %}` 动态分页循环（range 基于动态页数，不是数据绑定列表） |

**已通过 data-* 机制解决：**

| 情况 | 替换方式 |
|---|---|
| `banner_align` 多 CSS 属性联动 | 模板改 flexbox，`data-label-text-align` + `<meta data-type="select">` 控制 |
| `card_layout` 跨元素联动 | 拆为两个独立 CSS 字段，各自用 `data-label-*` + `<meta data-type="select">` 控制 |
| `{% for %}` 循环 + `{% if items %}` | `expand_repeat_items()` 后处理，模板只写一份（直接子元素作为模板项） |
| `{% if item.type == 'xxx' %}` | `data-when` 互斥组 |
| `{% if item.title %}` / `{% if item.subtitle %}` | 空值自动隐藏 |
| `{{ }}` 变量输出 | `data-content` / `data-src` / `data-href` / `data-bg` / `data-target` |
| CSS 字段逐个声明 | `data-label` 批量自动生成 + `data-label-*` 精确覆盖 |
| `image_position` / `layout` / `step_style` / `direction` | CSS 字段 + data-when 互斥组 |

**不需要替换（不属于 data-* 迁移范围）：**

| 情况 | 原因 |
|---|---|
| 数据变换 (`truncate`/`split`/`int`/`default`/`trim`/`replace`) | Jinja2 filter 能力，不是字段声明 |
| text_content 的富文本编辑器 | 特殊交互控件，保留为 admin JS 控件类型 |
| item_data 全部 | 条目编辑器，不是 Block 模块（设计文档已确认） |
| JS 脚本（轮播/分页/计数动画/放大镜） | JS 逻辑不涉及字段声明 |

## 三、优化后的基础设施设计

### 3.1 核心新增文件

| 文件 | 职责 | 行数估计 |
|---|---|---|
| `app/core/block_scanner.py` | 扫描 template.html，提取字段定义 | ~300行 |
| `app/core/block_styles.py` | `expand_repeat_items()`, `inject_styles()`, `inject_content()`, `apply_visibility()`, `strip_schema_output()` | ~400行 |

### 3.2 核心修改文件

| 文件 | 改动范围 |
|---|---|
| `app/core/template_loader.py` | 新增 `load_all_block_fields()`, 改造 `scan_blocks()` |
| `app/core/builder.py` | `_render_for_language()` 中新增后处理调用链 + `_normalize_module_data()` |
| `app/static/js/admin_modules.js` | 新增 `renderListEditor()`, 增强 `renderField()`(color/url/visibility), 删除 15 个 per-block 分支 |
| `app/templates/dashboard/panel_page_edit.html` | 删除 Jinja2 和 JS 的 per-block 分支，改为数据驱动渲染 |
| `app/core/routes.py` | `_parse_modules_form()` 删除 6 个 per-block 分支，改为通用列表解析 |
| `site_templates/dengtec/templates/_modules.html` | 简化 `hero_banner` 旧格式兼容 |

### 3.3 renderField() 增强

```javascript
// 新增支持的 type:
'color'    → 颜色选择器（现有 cn() 逻辑，抽成 renderField 内部）
'url'      → <input type="url"> + 图片预览缩略图
'visibility' → 眼球开关（现有 visToggle() 逻辑）
'icon'     → 图标选择器（下拉式图标列表）
'textarea' → <textarea>（已支持）

// 单位选择器集成：
// 字段定义中有 units: ["px","rem","%"] → 自动渲染 input + select.unit-picker
```

### 3.4 renderListEditor() 通用列表编辑器

```javascript
function renderListEditor(moduleIdx, listKey, itemFields, existingItems) {
  // itemFields: [{key, label, type, default, options, units, ...}]
  // existingItems: [{field: value, ...}, ...]
  //
  // 生成:
  // <div class="list-editor" data-list-key="slides">
  //   <div class="list-items">
  //     {existingItems.map(function(item, i) {
  //       return '<div class="list-item">' +
  //         itemFields.map(function(f) { return renderField(prefix + i + '_', f, item[f.key]); }).join('') +
  //         '<button onclick="removeListItem(this)">删除</button>' +
  //       '</div>';
  //     })}
  //   </div>
  //   <button onclick="addListItem(this)">+ 添加</button>
  //   <input type="hidden" name="module_{idx}_data_{listKey}_count" value="{count}">
  // </div>
  //
  // form name 格式: module_{idx}_data_{listKey}_{itemIndex}_{fieldKey}
}
```

### 3.5 _parse_modules_form() 通用列表解析

```python
# 去掉所有 per-block if 分支，改为：
# 1. 从现有模块数据或 block_fields 推断 type=list 的字段
# 2. 遍历请求中的 module_N_data_<listKey>_<index>_<field> 键
# 3. 按 index 分组构建列表
# 4. 文件上传按字段名匹配 (_field_file 后缀)

def _parse_list_from_form(form, module_prefix, list_key, item_fields, request):
    """通用列表解析——替代 6 个 per-block 分支。
    
    Args:
        module_prefix: 如 "module_0"（含 module_ 前缀）
        list_key: 列表字段 key，如 "slides"
    """
    count = 0
    try:
        count = int(form.get(f'{module_prefix}_data_{list_key}_count', '0'))
    except (ValueError, TypeError):
        pass
    items = []
    for i in range(count):
        prefix = f'{module_prefix}_data_{list_key}_{i}_'
        item = {}
        for f in item_fields:
            key = f['key']
            value = form.get(f'{prefix}{key}', '').strip()
            if value:
                item[key] = _parse_value(value)
            # 检查文件上传
            upload = request.files.get(f'{prefix}{key}_file')
            if upload and upload.filename:
                item[key] = _save_uploaded_image(...)
        if item:  # 非空才加入
            items.append(item)
    return items if items else None
```

### 3.6 跨数据源字段（settings.contact）

`data-*` 在模板声明，后处理从 `settings.contact` 取值。需要在扫描器增加 `data-source` 声明：

```html
<meta data-field="phone" data-label="电话" data-type="text"
      data-source="settings.contact" data-readonly="true">
```

或者更简单——contact_info/contact_form 这类跨数据源的 Block **延迟到最后迁移**，确保基础机制成熟后再处理。

**推荐方案：** contact_info/contact_form 的 section 级标题/副标题按标准 data-* 处理，visibility 字段按 `<meta data-type="visibility">` 处理，但 `settings.contact` 的数据读取保留在模板的 `{% set contact = settings.contact %}` 中。**这两个 Block 的迁移范围缩小为：CSS 字段用 data-label-*，visibility 开关用 data-type="visibility"**，不强制消除所有 Jinja2。

## 四、优化的迁移顺序

按"机制验证 → 批量推进 → 难点攻克"三阶段：

### 阶段一：基础设施 (约 800 行代码)

```
1. block_scanner.py (新文件)
2. block_styles.py (新文件) 
3. 备份 6 个基础设施文件
4. 增强 renderField() (color/url/visibility/单位选择器)
5. 新增 renderListEditor() (admin_modules.js)
6. 改造 _parse_modules_form() 为数据驱动 (routes.py)
7. 改造 builder.py (添加后处理调用链)
8. 改造 template_loader.py (load_all_block_fields)
9. 简化 _modules.html
```

### 阶段二：样板 Block (验证完整链路)

```
10. hero_banner   ← 最复杂，验证所有机制(CSS注入/内容注入/条件可见性/列表/互斥组/文件上传)
11. section_title ← 最简单，快速验证基础CSS注入+内容注入
12. text_content  ← 验证 textarea + 富文本编辑器保留
```

### 阶段三：批量迁移 (6 个 Block，机制类似)

```
13. highlight_card  (CSS字段+内容注入)
14. stat_counter    (列表+columns)
15. logo_cloud      (列表+文件上传)
16. feature_grid    (列表+图标互斥组)
17. process_steps   (列表+data-when互斥组)
18. contact_info    (visibility+跨数据源保留)
19. item_detail     (双列表+详情页，数据自包含)
```

### 阶段四：数据集 Block (2 个，最复杂)

```
20. data_grid       (数据集绑定+分页)
21. product_grid    (数据集绑定+卡片布局)
```

### 阶段五：收尾

```
22. contact_form    (visibility+map+layout变体)
23. 清理 panel_page_edit.html 残存分支
24. 全链路验证
```

## 五、零 Bug 保证策略

### 5.1 每个 Block 迁移后验证清单

| # | 验证项 | 方法 |
|---|---|---|
| 1 | 扫描器无报错 | `flask --app run scan-templates` |
| 2 | 字段列表与 meta.yaml.bak 一致 | diff 比较字段 key、type、default |
| 3 | 后台属性面板正确渲染 | 新建模块 → 检查每个字段的控件 |
| 4 | 保存后回显正常 | 填值 → 保存 → 刷新 → 打开属性面板 |
| 5 | 数据集编辑器也一致 | admin_modules.js 的 buildModuleHTML() |
| 6 | 构建输出与迁移前一致 | 旧新模板各构建一次，diff output/ |
| 7 | 无新增 console error | 浏览器 devtools |
| 8 | 列表增删改正常 | 添加项 → 保存 → 刷新 → 确认数据存在 |
| 9 | 文件上传正常 | 上传图片 → 保存 → 确认图片出现 |
| 10 | 空值处理正确 | 清空字段 → 保存 → 确认不从默认值回退 |

### 5.2 逐 Block 提交

每个 Block 迁移验证通过后单独 git commit，不批量提交：

```
refactor: hero_banner 迁移到 data-* 字段声明
refactor: section_title 迁移到 data-* 字段声明
...
```

好处：任一个 Block 出问题，只需 revert 该 commit，不影响其他。

### 5.3 回滚机制（每 Block 独立）

```
cp template.html.bak template.html
cp meta.yaml.bak meta.yaml
flask --app run scan-templates
# 启动 dev server 验证
```

### 5.4 关键风险点及缓解

| 风险 | 严重程度 | 缓解措施 |
|---|---|---|
| 单位选择器集成到 renderField 后旧代码不兼容 | 高 | 先在 hero_banner 上验证，保留 un() 旧函数 |
| 旧 form 前缀兼容（旧站点数据无法解析） | 高 | routes.py 保留旧格式兼容逻辑 2 个版本 |
| 数据集 Block 迁移失败 | 中 | 排在最后，充分验证基础设施 |
| 图标互斥组删除逻辑错误 | 中 | 用 Python 脚本单独测试 apply_visibility |
| panel_page_edit.html 改动太大 | 高 | **只删不改**——新增数据驱动代码，旧分支用 `{# 旧代码 #}` 注释保留，全验证通过后再删除 |
| multi-list Block (item_detail) 的 data-repeat 解析 | 中 | 扫描器支持多 data-repeat 容器，单元测试 |

### 5.5 禁止事项重申

1. **不准为 data-* 模式新增任何 per-block 硬编码代码**（§9.4 验证标准 #8）
2. **旧分支先注释后删除**——panel_page_edit.html 改动过大时先 `{# comment #}` 旧代码
3. **每个 Block 迁移前必须备份** template.html + meta.yaml
4. **不删除 .bak 文件直到用户明确指令**
5. **Edit 失败一次立刻写 Python 脚本**（CLAUDE.md 规范）

## 六、与原设计文档的差异补充

原设计文档 (`block-data-attributes.md`) 已非常详尽。逐模板复查后，本方案补充/纠正了以下内容：

1. **跨数据源字段** (§2.1)：contact_info/contact_form 从 `settings.contact` 取值，迁移范围缩小为 CSS 字段 + visibility 开关
2. **变体可替换性重新评估** (§2.3)：初判 6 个 Block 有 DOM 变体需保留 Jinja2 → 全部可替换（banner_align 改 flexbox + text-align CSS 字段，card_layout 拆为独立 CSS 字段，image_position/layout 用 flex-direction CSS 字段，step_style 用 data-when 互斥组，direction 用 CSS）
3. **expand_repeat_items() 列表展开**：新增后处理函数，替代 {% for %} 循环和 {% if items %} 空列表守护。模板只写一份，直接子元素作为模板项
4. **data-label 批量标签**：新增属性，style 中所有 CSS 属性自动生成字段标签（内置中文字典），替代逐行 data-label-*
5. **item_detail 纠正**：初判为"数据集绑定"→ 复查模板后发现数据全在 `module.data` 中，是自包含模块，可完全迁移
6. **数据变换保留** (§2.2)：truncate/split/int/default 等 Jinja2 filter 不在 data-* 迁移范围内
7. **富文本编辑器** (§2.4)：text_content 的 contenteditable 保留为 admin JS 控件类型
8. **JS 脚本保留** (§2.4)：轮播/分页/计数动画/图片放大镜——JS 逻辑不涉及字段声明
9. **panel_page_edit.html 迁移策略**：从"直接删除旧代码"改为"先注释后删除"
10. **header Block**：暂无 template.html，后续补充模板后同样改为零 Jinja2 模式

---

开发等待用户明确指令："开始迁移"。
