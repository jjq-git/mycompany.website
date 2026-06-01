# Block 系统改造方案

> 将 block 模板从 Jinja2 命令式写法迁移到声明式纯 HTML + data-* 属性，对齐 [data-attributes-reference.md](data-attributes-reference.md) 和 [Block 示例库.md](Block%20示例库.md) 规范。

---

## 一、现状 vs 目标

### 当前状态（Jinja2 命令式）

14 个 block 模板（`site_templates/dengtec/blocks/*/template.html`）全部用 Jinja2 编写：

```jinja2
{# 当前写法示例：feature_grid/template.html #}
{% set features = md.get('features') or [] %}
{% for f in features %}
<div class="feature-card">
  <img src="{{ f.icon }}" alt="{{ f.title }}">
  <h3>{{ f.title }}</h3>
  <p>{{ f.description }}</p>
</div>
{% endfor %}
```

后端 builder.py 用 Jinja2 `{% include %}` 加载 block 模板，传 `md` (module.data) 变量进去渲染。前端 admin_modules.js 里 `buildModuleHTML()` 有约 600 行硬编码的 `if type === 'xxx'` 分支，为每个 block 类型手写了编辑表单。

### 目标状态（纯 HTML 声明式）

Block 模板用纯 HTML + data-* 属性编写，HTML 同时承担 Schema 和 Render 两个角色：

```html
<!-- 目标写法示例：features -->
<section data-name="features" data-type="list"
         data-hideable data-style="cols" style="--cols: 3">
  <div data-name="feature" data-type="group">
    <img data-name="icon" data-type="image" src="icon1.svg">
    <h3 data-name="title" data-type="text">高性能</h3>
    <p data-name="desc" data-type="text">说明文字……</p>
  </div>
</section>
```

系统自动解析 data-* 属性 → 生成编辑表单 → 注入数据 → 渲染输出。编辑器和渲染器都是通用的，不再需要按 block 类型写分支。

### 核心差异对比

| 维度 | 当前 (Jinja2) | 目标 (data-*) |
|---|---|---|
| Schema 定义 | meta.yaml 的 fields 数组 | HTML 里的 data-name + data-type |
| 渲染 | Jinja2 `{% for %}` `{% if %}` | Python 解析 HTML + 注入数据 |
| 编辑器 | 每个类型 50-100 行硬编码分支 | schema 驱动自动生成 |
| 变体 | meta.yaml variants 列表 | 同目录下 variants/*.html |
| 样式 | 几十个 style 表单字段 | data-style + CSS 变量 + 全局注册表 |
| 列表/网格 | `{% for item in list %}` | data-type="list"/"grid" + 项模板约定 |

---

## 二、data-* 属性体系（8 种）

详见 [data-attributes-reference.md](data-attributes-reference.md)，这里只列关键点：

| # | 属性 | 职责 | 示例 |
|---|------|------|------|
| 1 | `data-type` | 内容类型（text/image/video/list/grid/group...） | `data-type="text"` |
| 2 | `data-name` | 字段 key，对应 YAML 数据中的 key 名 | `data-name="title"` |
| 3 | `data-href` | 让元素可点击，值为空则不注入 href | `data-href="titleLink"` |
| 4 | `data-style` | 声明开放给用户的 CSS 变量（逗号分隔） | `data-style="cols, dir"` |
| 5 | `data-hideable` | 用户可整块隐藏（开关 → hidden 属性） | `data-hideable` |
| 6 | `data-source` | 列表数据来源：省略/manual 为手动，存在/具名 为数据集 | `data-source="products"` |
| 7 | `data-page-size` | 列表每页条数 | `data-page-size="9"` |
| 8 | `data-cols` | 二维栅格列数（仅 grid 类型） | `data-cols="3"` |

**关键约定：**
- **项模板**：list/grid 容器内"带 data-name 的直接子元素"即为项模板，渲染时按数据复制
- **空值自动隐藏**：text/image/video 等叶子类型值为空时自动加 hidden
- **HTML 里的值即默认值**：标签文字、src、style 值均为默认值
- **CSS 变量默认值只写在 CSS 里**（`var(--cols, 3)`），HTML 和注册表不重复

---

## 三、分阶段实施

### Phase 1：基础设施（不改任何 block 模板）✅ 已完成（2026-05-29）

> 落地情况见文末「九、Phase 1 实施记录」。3 个新模块 + 开关 + loader 改造已就绪，
> 39 项往返测试全过，开关默认关，现有 14 个 Jinja2 block 行为零变化。

**新增 3 个 Python 模块：**

#### 3.1 `app/core/block_parser.py` — HTML 解析器

用 stdlib `html.parser.HTMLParser` 解析 block 模板，提取 schema。

```
输入：template.html 的 HTML 字符串
输出：BlockSchema dataclass
  - block_name: str
  - root_tag: str
  - style_tokens: list[str]       # data-style 声明的 CSS 变量
  - hideable: bool                # 是否有 data-hideable
  - source: str | None            # data-source 值
  - page_size: int | None         # data-page-size 值
  - cols: int | None              # data-cols 值（grid 专用）
  - root_type: str                # data-type 值（list/grid/group 等）
  - fields: list[FieldDef]        # 字段列表
  - item_template_html: str | None  # list/grid 的项模板 HTML
```

`FieldDef` dataclass：
```
  - name: str              # data-name 值
  - type: str              # data-type 值 (text/image/video/group/...)
  - tag: str               # HTML 标签名
  - default_text: str      # 标签内的默认文字
  - default_src: str       # 默认 src
  - default_value: str     # 通用默认值
  - href_field: str        # data-href 对应的字段名
  - attributes: dict       # 其他需保留的属性
  - children: list[FieldDef]  # 子字段（group/list/grid 时递归）
```

**核心算法：**
1. 遍历 DOM，遇到带 `data-name` 的元素 → 创建 FieldDef
2. 遇到 `data-type="list"` 或 `"grid"` → 识别容器内第一个带 data-name 的直接子元素作为项模板
3. 项模板的子元素递归解析为 FieldDef.children
4. 根元素提取 style_tokens / hideable / source / page_size / cols

#### 3.2 `app/core/block_renderer.py` — 数据注入渲染器

接收 BlockSchema + module.data + 全局 context，产出最终 HTML。

```
输入：block_html, schema, data_dict, context (含 all_datasets)
输出：渲染后的 HTML 字符串
```

**核心处理流程（5 步后处理管线）：**

1. **字段注入**：遍历 schema.fields，按 data-name 匹配 data_dict，将值写入 innerText/src/href
2. **列表展开**（`data-type="list"/"grid"`）：
   - 手动模式（无 data-source 或 data-source="manual"）：从 data_dict[list_name] 取数组，循环复制项模板
   - 数据集模式（有 data-source）：从 context['all_datasets'] 查数据集，循环生成
3. **显隐处理**：`data-hideable` → 检查 hidden 标记；文本/媒体空值 → 自动加 hidden
4. **CSS 变量注入**：读 data-style → 查 STYLE_REGISTRY → 写 style 属性
5. **清理 data-* 属性**（最终输出不含 data-*，只留干净 HTML）

> data_grid 和 product_grid 的数据集绑定逻辑保留：渲染时从 all_datasets 取值循环。contact_info 从 settings.contact 取值。

#### 3.3 `app/core/style_registry.py` — CSS 变量注册表

```python
STYLE_REGISTRY = {
    'cols':       {'label': '每行个数', 'control': 'select', 'css_var': '--cols',
                   'options': ['2','3','4']},
    'dir':        {'label': '图文方向', 'control': 'switch', 'css_var': '--dir',
                   'options': [{'value':'row','text':'图左文右'}, {'value':'row-reverse','text':'图右文左'}]},
    'bg':         {'label': '背景图', 'control': 'image', 'css_var': '--bg'},
    'bg-color':   {'label': '背景色', 'control': 'color', 'css_var': '--bg-color'},
    'text-align': {'label': '文字对齐', 'control': 'select', 'css_var': '--text-align',
                   'options': ['left','center','right']},
}
```

注册表是全局的，按"变量"建表而非按"block"建表。`features` 和 `news` 都用 `cols` → 共用同一条。

#### 3.4 修改 `builder.py`

- 在 `_render_for_language()` 的 Jinja2 环境中注册 `render_blocks()` 为全局函数
- `render_blocks(page, ctx)` — 页面的 Jinja2 模板中调用此函数，代替 `{% include %}`
- 格式检测：检查 block HTML 是否含 `{%` 或 `{{` → 有则走旧 Jinja2 渲染；纯 HTML 则走新渲染器
- `_modules.html` 中 `{% for module in page.modules %}{% include ... %}` 替换为 `{{ render_blocks(page, ctx) }}`

#### 3.5 修改 `template_loader.py`

- `scan_blocks()` 增加：调用 `block_parser.parse()`，在返回结果中附加 `schema` 字段
- 新增函数 `scan_block_schema(block_name)` — 只解析不扫描

#### 3.6 新增 API 端点（`routes.py`）

- `GET /_api/block/<name>/schema` — 返回 block 的 JSON schema（给前端表单生成用）

#### 3.7 修改 `admin_modules.js`

- 新增 `generateSchemaForm(schema, idx, mdata)` — 通用 schema 驱动表单生成，替代 `buildModuleHTML()` 中的硬编码分支
- 新增 `generateStyleForm(style_tokens, idx, mdata)` — 根据 style_tokens 生成样式编辑区
- 新增 `generateListEditor(list_field, idx, mdata)` — 列表/网格的条目编辑器
- 现有硬编码分支保留作为 fallback（开关关闭时使用）

#### 3.8 特性开关

在 `config.py` 中加：
```python
ENABLE_DATA_ATTR_BLOCKS = True
```

开关关闭时，整个系统行为与改造前完全一致。

**Phase 1 交付物：** 基础设施就绪，拿 `Block 示例库.md` 中的 mock HTML 做解析+渲染往返测试。开关关闭时不影响任何现有功能。

---

### Phase 2：转换简单 block（验证全流程）✅ 部分完成（2026-05-29）

转换最简单的非列表 block，验证"编辑 → 存储 → 构建"完整链路。

| block | 字段 | 复杂点 | 状态 |
|-------|------|--------|------|
| **section_title** | tag, title, desc, btn(+btn_url) | data-style="text-align"，btn 有 data-href | ✅ 已转 |
| **text_content** | title, body | body 是 richtext（富文本） | ✅ 已转 |
| **contact_info** | addr, phone, email, map | **数据来自 settings.contact 而非 module.data**；5 固定卡片 + SVG 图标 + show_xxx 开关 | ⏸ 跳过（见下） |
| **hero_banner** | title, subtitle, cta, bg | **全屏轮播 + 内嵌 `<script>` + data 可为 list/dict 双形态 + video/image 分支** | ⏸ 跳过（见下） |

**为什么跳过后两个（原方案误判为"简单"）：**
- **contact_info** 不符合 data-* 的"字段=data-name、数据来自 module.data"模型——它从全站 `settings.contact` 取数。需要先给 renderer 加"从 settings 取数"的特殊能力（方案 3.2 末尾提过此设计点，尚未实现）。归到数据来源特殊的一批，单独处理。
- **hero_banner** 带轮播交互 JS（内嵌 `<script>`）、双数据形态、条件媒体渲染，远超"简单 block"。归到复杂交互 block，待基础设施更成熟（如编辑器 schema 表单完成）再啃。

**每步操作：**
1. 重写 `template.html` 为纯 HTML + data-*（现有 Jinja2 版改名为 `template.jinja2.bak`）
2. 构建站点，确认渲染结果与改造前一致（已转的两个均端到端验证通过）
3. 同步 CSS（结构性样式收回 CSS 变量）+ 种子数据（字段 key 对齐 data-name）

**Phase 2 交付物：** section_title + text_content 全流程走通（双路径渲染、富文本字段、样式收回、空值隐藏、向后兼容均验证）。contact_info / hero_banner 留待专门 Phase。编辑器 schema 驱动表单（前端 + API 端点）仍待做。

---

### Phase 3：转换 list/grid block（手动列表）

转换涉及可重复列表的 block，验证项模板识别 + 渲染器列表展开。

| block | 类型 | 字段 | 复杂点 |
|-------|------|------|--------|
| **feature_grid** | list + group | icon, title, desc | data-style="cols" |
| **stat_counter** | list + group | num, label | data-style="cols" |
| **process_steps** | list + group | no, title, desc | data-style="cols" |
| **logo_cloud** | grid | logo | data-cols，image 类型 |

**关键验证点：**
- 项模板正确识别（容器内带 data-name 的直接子元素）
- 手动增删条目 → YAML 存储 → 构建时正确展开
- data-style CSS 变量在编辑器中正确生成 select/switch 控件
- logo_cloud 的 `data-type="grid"` + `data-cols` 正确渲染为二维栅格

**Phase 3 交付物：** 手动列表/网格 block 完整可用，前端 generateListEditor() 正常工作。

---

### Phase 4：转换数据集驱动 block

转换需要从数据集读取数据的 block。

| block | 数据来源 | 复杂点 |
|-------|---------|--------|
| **product_grid** | `data-source="products"` | dataset 绑定 + max_items + 链接配置 |
| **data_grid** | 店主选数据集 | data-source 空值 → 下拉选择 + items_per_page + 分页 |

**关键处理：**
- data-source 属性检测：存在且非 manual → 渲染时从 all_datasets 取值
- data-source 为空 → 店主后台选数据集（dataset 下拉框）
- data-source="products" → 限定只能用 products 数据集
- `data-page-size` → 渲染器自动加页码导航
- 前端 generateSchemaForm() 根据 data-source 生成数据集选择控件

**Phase 4 交付物：** 数据集驱动 block 完整可用，构建时正确从 YAML 数据文件读取 + 渲染。

---

### Phase 5：转换其余 block

| block | 类型 | 备注 |
|-------|------|------|
| **highlight_card** | group | tag, title, desc, image, primaryBtn, primaryLink；data-style="dir" |
| **contact_form** | group | 表单字段较特殊，但本质上也是 text + data-href 组合 |
| **item_detail** | group | title, desc, tags, images(list), specs(list) — 嵌套列表 |

---

### Phase 6：清理

1. 删除 `admin_modules.js` 中所有硬编码的 `if type === 'xxx'` 分支（约 600 行 → 保留 ~100 行通用逻辑）
2. 删除 `panel_page_edit.html` 中的硬编码 Jinja2 分支
3. 简化 `meta.yaml`：移除 `fields` 键（字段定义全在 HTML 的 data-* 里），meta.yaml 只保留 name/category/icon/variants
4. 删除 `builder.py` 中旧 Jinja2 渲染兼容代码
5. 删除旧 `template.jinja2.bak` 备份文件
6. 将 `ENABLE_DATA_ATTR_BLOCKS` 开关改为 `True` 并设 `True` 为默认

---

## 四、关键设计决策

### 4.1 数据格式不变

YAML 中 `module.data` 的 key 名直接对应 HTML 中的 `data-name` 值。

> **备注：** 开发/测试阶段的已有站点数据无需考虑迁移兼容，后续测试时会直接删除站点重新创建。

```yaml
# 改造前（Jinja2）和改造后（data-*）数据格式完全一致
modules:
  - type: section_title
    order: 1
    variant: default
    data:
      title: 德恩基电子科技
      desc: 提供展示道具行业的电子产品
```

### 4.2 混合模式共存

- builder.py 按 block 模板内容检测格式（含 `{%` 或 `{{` = 旧，纯 HTML = 新）
- 新旧 block 可在同一页面渲染，切换过程不需要一次性全部转换

### 4.3 变体系统

- 每个 block 的 `template.html` = 默认变体
- `variants/*.html` = 其他排版变体
- 变体之间的 data-name **必须一致**（字段定义相同），只是 HTML 结构不同
- 店主换变体 = 同一份数据用不同的 HTML 结构渲染
- meta.yaml 的 variants 列表仍由模板开发者手工维护（预览图、label 等）

### 4.4 样式简化

当前每个 block 有 30-50 个独立的样式字段（padding_top, margin_bottom, title_color, desc_size...），这是过度设计。改造后：
- **结构性样式**用 data-style + CSS 变量（cols, dir, bg, bg-color 等，共约 10 个全局变量）
- **不再开放像素级微调**（padding/margin/font-size 等回到 CSS 控制，模板开发者设定，店主不调）
- 如果后续需要扩展，只需在 STYLE_REGISTRY 加条目

### 4.5 Header/Footer 处理

目前 header 是特殊的（不在 14 个 block 列表中，用 Jinja2 `_base.html` 渲染）。按文档设计，Header/Footer 也是 block 库的一员（`data-type="group"`），使用相同的弹框选择模式。

- **本次改造不处理 Header/Footer 的 data-* 化**（它们在 `_base.html` 中用 Jinja2 渲染是合理的，因为涉及菜单数据结构、语言切换等复杂逻辑）
- 后续可以单独处理，但优先级低

### 4.6 回退策略

- 把单个 block 的 `template.html` 替换回 Jinja2 版本即可回退
- YAML 数据不变，无需数据迁移
- 特性开关关闭即全局回退

### 4.7 店主后台排版不动

当前后台是**左-中-右三栏布局**：左侧菜单/页面列表、中间预览、右侧属性面板。改造**不改变这个布局和交互流程**，只替换属性面板内部的表单生成引擎。

- **左侧（菜单/页面列表）**：完全不动
- **中间（预览 iframe）**：完全不动
- **右侧（属性面板）**：外观、分组、控件风格保持不变，但内部的表单字段从"14 个硬编码 `if type === 'xxx'` 分支"改为 schema 驱动自动生成
- **模块列表（页面编辑器内）**：拖拽排序、显隐开关的位置和交互不变

**模块库弹框保留：** 点击 **[+ 添加模块]** 弹出模态框，左右两栏布局（左侧模块列表 + 右侧变体预览），与 [模块系统.md](开发指南/模块系统.md) 描述一致。这是"添加"这个动作的独立交互，不影响三栏布局。

---

## 五、涉及文件清单

### 新增文件

| 文件 | 用途 |
|------|------|
| `app/core/block_parser.py` | HTML 解析，提取 schema |
| `app/core/block_renderer.py` | 数据注入渲染器 |
| `app/core/style_registry.py` | CSS 变量注册表 |

### 修改文件

| 文件 | 改动范围 |
|------|---------|
| `app/core/builder.py` | 注册 `render_blocks()` 全局函数，格式检测 + 双路径渲染 |
| `app/core/template_loader.py` | `scan_blocks()` 增加 schema 解析 |
| `app/core/routes.py` | 新增 `/_api/block/<name>/schema` 端点 |
| `app/core/config.py` | 加 `ENABLE_DATA_ATTR_BLOCKS` 开关 |
| `app/static/js/admin_modules.js` | 新增 `generateSchemaForm()` / `generateStyleForm()` / `generateListEditor()` |
| `app/templates/dashboard/panel_page_edit.html` | 传递 schema 给前端 |

### 重写文件（分阶段）

| 文件 | 阶段 |
|------|------|
| `site_templates/dengtec/blocks/section_title/template.html` | Phase 2 |
| `site_templates/dengtec/blocks/text_content/template.html` | Phase 2 |
| `site_templates/dengtec/blocks/contact_info/template.html` | Phase 2 |
| `site_templates/dengtec/blocks/hero_banner/template.html` | Phase 2 |
| `site_templates/dengtec/blocks/feature_grid/template.html` | Phase 3 |
| `site_templates/dengtec/blocks/stat_counter/template.html` | Phase 3 |
| `site_templates/dengtec/blocks/process_steps/template.html` | Phase 3 |
| `site_templates/dengtec/blocks/logo_cloud/template.html` | Phase 3 |
| `site_templates/dengtec/blocks/product_grid/template.html` | Phase 4 |
| `site_templates/dengtec/blocks/data_grid/template.html` | Phase 4 |
| `site_templates/dengtec/blocks/highlight_card/template.html` | Phase 5 |
| `site_templates/dengtec/blocks/contact_form/template.html` | Phase 5 |
| `site_templates/dengtec/blocks/item_detail/template.html` | Phase 5 |

### 删除内容（Phase 6）

| 位置 | 删除内容 |
|------|---------|
| `admin_modules.js` | `buildModuleHTML()` 中 14 个 `if type === 'xxx'` 硬编码分支（约 600 行） |
| `panel_page_edit.html` | 14 个 `{% elif module.type == 'xxx' %}` Jinja2 硬编码分支 |
| `blocks/*/meta.yaml` | `fields` 键（每个文件） |

---

## 六、不做的事

| 不做 | 原因 |
|------|------|
| 不迁移 Header/Footer 到 data-* | 它们在 `_base.html` 中用 Jinja2 渲染是合理的，涉及菜单树、语言切换等复杂逻辑 |
| 不实现 `data-type="richtext"` / `"textarea"` / `"icon"` / `"audio"` | MVP 阶段用不到，Phase 2+ 按需加 |
| 不修改 `item_data` block | 它是数据集条目编辑器，不是页面 block，不在本次改造范围 |
| 不改变 YAML 数据存储格式 | module.data 的 key-value 结构保持不变 |
| 不在本次改造中增加 block 数量 | 专注于将现有 14 个 block 从 Jinja2 迁移到 data-* |

---

## 七、验证方法

- **Phase 1**：用 mock HTML（从 `Block 示例库.md` 取）测试 parser → renderer 往返，确认输出与输入语义一致
- **每 Phase**：创建测试站点 → 编辑 block → 保存 → 构建 → 浏览器打开 output/ 确认渲染正确
- **最终验证**：`flask --app run build-site 1` 构建已有站点，对比 output/ 与改造前是否一致（允许空格/缩进差异）
- **前端验证**：打开店主后台 → 每个 block 的编辑面板表单由 schema 自动生成 → 确认所有字段可编辑、保存正确

---

## 八、原方案与现状的偏差（动手前核对发现）

落地 Phase 1 前对照真实代码，发现几处方案需修正，记录在此供后续 Phase 参考：

| 方案描述 | 实际代码 | 影响 |
|---|---|---|
| block 用 `{% include %}` 加载 | ✅ 属实，在 `_modules.html` 第 6 行 | 双路径渲染应通过 Jinja2 全局函数注入，不动 `_render_for_language` |
| config 用 `ENABLE_DATA_ATTR_BLOCKS = True`（class 风格） | config 是 `load_config()` 返回 dict | 开关加进 dict，由环境变量 `ENABLE_DATA_ATTR_BLOCKS=1` 控制 |
| 硬编码分支只在 `admin_modules.js`（约 600 行） | **还有 `panel_page_edit.html`（约 1250 行、14 个 elif）+ `page_home.html` 也有一份** | Phase 6 前端工作量比方案估计大；三处需同步改，否则首页/子页编辑器表单不一致 |
| builder.py 有一处 env | **build_site 和 build_template_preview 各一处 env**（231/370 行） | 双路径渲染要在两处都注册 render_blocks |
| 14 个 block | 实际目录 16 个（多 `header`/`item_data`，方案明确不动这两个） | scan_blocks 自然只扫到 14 个标准 block，符合预期 |

## 九、Phase 1 实施记录（2026-05-29）

**交付物（全部完成，开关默认关 → 现有功能零影响）：**

| 文件 | 状态 | 说明 |
|---|---|---|
| `app/core/style_registry.py` | 新增 | CSS 变量注册表，5 个 token（cols/dir/bg/bg-color/text-align）；默认值只在 CSS，注册表不重复 |
| `app/core/block_parser.py` | 新增 | 自建轻量 DOM 树（stdlib html.parser），还原父子关系识别项模板；输出 BlockSchema/FieldDef |
| `app/core/block_renderer.py` | 新增 | 5 步管线：字段注入→列表展开→显隐→样式→清 data-*；在 DOM 树上变换后序列化（不用正则替换） |
| `app/core/config.py` | 改 | 加 `ENABLE_DATA_ATTR_BLOCKS` 开关，默认 False |
| `app/core/template_loader.py` | 改 | `scan_blocks()` 增加 `is_data_attr`/`schema` 字段；新增 `scan_block_schema()`；旧 Jinja2 block 解析失败静默降级 |
| `scripts/test_block_roundtrip.py` | 新增 | 39 项往返测试，全过 |

**与方案的实现差异：**
- 方案 3.4 说"在 `_render_for_language()` 里注册 render_blocks"，实际**未改 builder.py**——Phase 1 定位为纯基础设施、零破坏，builder 的双路径渲染留到 Phase 2 接第一个真实 block 时再接（届时通过 Jinja2 全局函数注入，不动 `_render_for_language` 主体）。
- 方案 3.6 的 `GET /_api/block/<name>/schema` API 端点**未做**——Phase 1 无前端消费方，留到 Phase 2 前端 schema 驱动表单时一起加（`scan_block_schema()` 已备好底层函数）。
- 渲染器约定：用户调样式存 `style_<token>`（如 `style_cols`）、整块隐藏存 `_hidden`、数据集驱动列表的数据集名存 `dataset`。这些 key 约定原方案未明确，Phase 2 前端需对齐。

**已验证（不影响现有功能的证据）：**
- 开关默认 False；`scan_blocks('dengtec')` 扫 14 个旧 block 全部识别为 Jinja2 旧式、schema=None，无异常。
- 往返测试覆盖：text/image/data-href、group、list(手动)、list(数据集驱动)、grid、data-style 注入、data-hideable、叶子空值自动隐藏、data-* 全清理。

## 十、Phase 2 实施记录（2026-05-29）

**已完成：**

| 项 | 说明 |
|----|------|
| builder 双路径渲染 | 新增 `render_block(module)` Jinja2 全局函数 + `_SCHEMA_CACHE` 缓存；`_modules.html` 的 `{% include %}` 换成 `{{- render_block(module) }}`；两处 env（build_site / build_template_preview）均注册 |
| 开关关回退 | 开关关时，已转 data-* 的 block 自动回退到 `template.jinja2.bak`（否则 data-* HTML 会被当 Jinja2 原样吐出脏属性）；向后兼容验证 contact/about 逐字节一致 |
| section_title 转换 | 26 字段 → 4 内容字段（tag/title/desc/btn）+ data-style="text-align"；CSS 收回变量；种子数据 subtitle→desc、删 section_bg |
| text_content 转换 | title + body(richtext)；CSS 收回 text-align 变量；种子数据 body 转 HTML 段落（richtext=innerHTML） |
| 单语言构建 bug 修复 | `build_site` 单语言分支引用未定义的 products_categories/items 导致崩溃，已补提取 + all_datasets |
| 孤儿记录清理 | 删除指向缺失模板的 3 Site + 3 Template（globex/serveco/tasty），当前仅 dengtec |

**跳过：** contact_info（数据来自 settings.contact，需 renderer 加特殊取数）、hero_banner（轮播 JS + 双数据形态），见 Phase 2 表格说明。

**代码审查修复（独立 reviewer 实测复现，全部已修 + 加回归测试）：**

| 级别 | 问题 | 修复 |
|------|------|------|
| P0 | `_Node` 文本/子元素分开存 → 序列化重排（破坏 inline 排版） | 重构为**有序节点列表**（_Text + _Node 混排） |
| P0 | `convert_charrefs=True` → 属性里 HTML 实体被解码后裸写破坏 HTML | `convert_charrefs=False` + 序列化属性值统一转义 |
| P0 | `_apply_style` 样式值不转义 → 可逃逸出 style 属性 XSS | 按 control 类型白名单校验（select/color/image）+ 转义 |
| P1 | `_expand_list._ctx` 模块级全局 → 并发构建串味 | context 全程显式传递，删全局状态 |
| P1 | 空数组列表留可见空容器 | 空列表容器自动 hidden |
| P1 | data-href 不挡 javascript: scheme | href scheme 白名单 |

**遗留（非代码，待后续）：**
- richtext 按 innerHTML 不转义 → 内容须在**录入侧** sanitize（编辑器链路待确认）
- `_SCHEMA_CACHE` 进程内永不失效 → 改 block 后须重启开发服务器（同 CLAUDE.md 已记的 Flask 重载坑）

### 编辑器 schema 驱动表单（2026-05-29，新增模块场景已通）

让 data-* block 在店主后台用 schema 自动生成编辑表单，不再写硬编码分支。

| 改动 | 文件 | 说明 |
|------|------|------|
| 前端 schema 表单 | `panel_page_edit.html` | 新增 `generateSchemaForm`（内容字段+显隐开关）/ `generateSchemaStyleForm`（data-style 控件）/ `_schemaFieldHtml` / `_schemaHideToggle` |
| addModule 拦截 | `panel_page_edit.html` | 在所有硬编码 `if type===` 分支**最前面**加 `if (meta.is_data_attr && meta.schema)` → 走 schema 表单，零侵入旧分支 |
| 样式注册表下发 | `routes.py` + `panel_page_edit.html` | page_panel 传 `style_registry`，模板加 `styleRegistryJson`，前端按 token 查控件类型 |
| _hidden 判断修正 | `block_renderer.py` | 表单存字符串布尔，`'false'` 是真值会误隐藏 → 加 `_is_truthy()` 显式判断 |

**字段命名对齐**：schema 表单字段 name = `module_<idx>_data_<fieldName>`，data-href 额外生成 `<href_field>`，样式 `style_<token>`，显隐 `_hidden`——与后端 `_parse_modules_form` 还原规则一致。无需新增 API 端点（schema 已随 `blockLibraryJson` 全量下发）。

**已验证（test client 端到端 20/20）**：编辑器下发 schema 函数+注册表 → POST schema 表单字段 → YAML 正确写入（tag/title/desc/btn/btn_url/style/​_hidden）→ 渲染闭环正确、无 data-* 残留。测试自清理无污染。

**仍待做**：
- **已有模块**的服务端渲染仍走旧 Jinja2 分支（section_title/text_content 有 elif 保底，功能一致）；统一到 schema 表单需改 panel_page_edit.html 的 Jinja2 链（Phase 6 清理时一起做）
- schema 字段缺中文 label（现用字段名）——后续可在 meta 或 data-label 补
- group/list/grid 结构字段的编辑器（增删条目）未做 → Phase 3

## 十一、Phase 3 实施记录（2026-05-29，渲染侧完成）

转换 4 个 list/grid block，并为此给渲染器补了三项能力。

**新增能力（renderer/parser）：**

| 能力 | 文件 | 说明 |
|------|------|------|
| 图标注册表 | `icon_registry.py`（新增，46 图标） | data-type="icon" 字段存图标名，渲染时查表注入 SVG。由 `scripts/extract_icons.py` 从原模板硬编码 SVG 分支自动抽取，去掉写死 width/height 改 CSS 控制 |
| icon 类型渲染 | `block_renderer.py` | `_inject_leaf` 加 icon 分支：图标名→SVG（innerHTML）；未知名/空值隐藏 |
| CDATA(script) 保护 | `block_parser.py` | script/style 内文本按 CDATA 原样保留，不转义（否则 JS 的 `a < b` 会变 `a &lt; b` 破坏脚本） |
| 业务 data-* 保留 | `block_renderer.py` | `_strip_data_attrs` 改白名单：只删 schema 用的 data-*（name/type/href/style/...），保留业务 data-*（data-target 等） |

**转换的 block：**

| block | 结构 | 要点 |
|-------|------|------|
| feature_grid | group 包 list，项=group(icon/title/desc) | 顶层标题用 heading/subheading（避免与项内 title 同名）；data-style="cols" |
| stat_counter | group 包 list + 数字动画 script | script 移进 section 内（根子树），改读 textContent 作动画目标（原用 data-target 会被清理） |
| process_steps | group 包 list，项=group(icon/title/desc) | ps-track 横向布局 |
| logo_cloud | group 包 grid，项=image 叶子(+data-href) | data-cols="6" 固定列数 |

**CSS 同步**：services-grid / sc-grid / lc-grid 改用 `repeat(var(--cols, N), 1fr)`，列数由 data-style/data-cols 注入。

**已验证（端到端构建）**：home 页 feature_grid（3 卡片+图标）、about 页 stat_counter（4 卡片+数字+动画 script 完整保留）正确渲染，无 schema data-* 残留。种子数据 stat_counter 字段对齐（title/subtitle→heading/subheading，columns→style_cols）。全套回归 48+20 项通过。

**仍待做（Phase 3 编辑器侧）：** ✅ 已于 2026-06-01 完成，见「十三」。
- ~~前端 schema 表单的 list 增删条目编辑器 + icon 下拉选择器~~ → 已实现
- ~~后端 `_parse_modules_form` 的 data-* list 通用解析~~ → 已实现（通用复数命名 + 跳过硬编码分支）
- 已转 9/14 个 block（section_title, text_content, feature_grid, stat_counter, process_steps, logo_cloud, highlight_card, data_grid, product_grid）；其余 4 个按架构边界保留 Jinja2（见「十五」）

**测试现状：** `test_block_roundtrip.py` 48 项（含交错文本/charref/XSS/href/空列表安全回归）、section_title/text_content 端到端、向后兼容、单语言分支均通过。

**新增测试脚本（scripts/）：** test_block_roundtrip / test_section_title / test_e2e_section_title / test_render_block_compat / test_editor_schema_form / cleanup_orphan_records / extract_icons。

---

## 十二、续作清单（下次照此继续）

> **已转 9/14 个 block**：section_title, text_content, feature_grid, stat_counter, process_steps, logo_cloud, highlight_card（见「十四」）、data_grid, product_grid（数据集驱动，见「十五」）。**其余 4 个（hero_banner / item_detail / contact_info / contact_form）按架构边界保留 Jinja2**（见「十五·乙」）。**开关 `ENABLE_DATA_ATTR_BLOCKS` 现默认开**（2026-06-01，P1 完成后；设 `=0` 回退旧 Jinja2，需本地 .bak）。现有模块编辑器已统一走 schema 表单（见「十六」）。

### 当前状态速览

| 维度 | 状态 |
|------|------|
| 渲染引擎（parser/renderer/style_registry/icon_registry） | ✅ 稳定，覆盖 text/textarea/richtext/image/video/embed/icon/group/list/grid + data-style/href/hideable/source + CDATA script + 业务 data-* 保留 |
| builder 双路径 | ✅ 开关关回退 .jinja2.bak，开关开走 renderer |
| 编辑器表单（新增模块） | ✅ 叶子字段 + data-style + 显隐开关 + **list/grid 增删条目编辑器**（icon 下拉、增删/重排）已通（2026-06-01） |
| 编辑器表单（已有模块） | 🟡 仍走旧 Jinja2 服务端分支（feature/stat/step 键名与 renderer 一致；logo_cloud 键名已对齐 {logo,link}）；统一到 schema 表单仍属 P1/Phase 6 |
| 后端 list 解析 | ✅ 通用 data-* list 解析（`module_<i>_<listName>_count` + 子字段），命中即跳过对应硬编码分支；旧 Jinja2 单数命名仍由硬编码分支兜底，两套不冲突 |

### 待办（按优先级）

**P0 — 完成 Phase 3 编辑器闭环（让店主能在后台增删 list 条目）** ✅ 已完成（2026-06-01，见「十三」）

现状（已解决）：feature_grid/stat_counter/process_steps/logo_cloud 渲染没问题，但后台**无法增删卡片/条目**——这 4 个 block 在编辑器里是"半残"。要两端配合：

1. **前端**（`app/templates/dashboard/panel_page_edit.html`，约 1631 行 `generateSchemaForm` 里 `field.type === 'list'/'grid'` 分支，现在只输出占位提示）：
   - 写一个 list 条目编辑器：渲染已有条目 + "添加条目"/"删除条目"按钮；每条目用 `field.children`（schema 里的项字段）渲染子表单。
   - 字段命名约定：`module_<idx>_<listName>_<itemIdx>_<subField>`（如 `module_0_features_0_title`），外加隐藏的 `module_<idx>_<listName>_count`。**可参考现有 hero_banner/feature_grid 的硬编码增删实现**（同文件里 `_addFeatureItem`/`_addHeroSlide` 等函数）——命名规则照搬，但改成由 schema 驱动通用生成。
   - icon 子字段：生成图标下拉选择器（图标名列表从后端下发；可让 routes 额外传 `icon_registry.icon_names()` 类似 styleRegistry 那样注入 `iconListJson`）。

2. **后端**（`app/core/routes.py` 的 `_parse_modules_form`，约 1810 行循环内）：
   - 现在按 `if m_type == 'feature_grid'` 等硬编码解析 list（1947/1977 行等）。要在这些硬编码分支**之前**加一个**通用 data-* list 解析**：若该 block 是 data-* 声明式（查 schema，schema 里 root 含 list/grid 字段），按 `module_<idx>_<listName>_count` + `module_<idx>_<listName>_<i>_<subField>` 通用还原成 `data[listName] = [{...}, ...]`，并跳过后面的硬编码分支。
   - 注意：`_parse_modules_form` 当前不一定能拿到 schema，需要把 `_get_available_blocks` 的结果（含 schema）传进去或在函数内取。
   - 坑：`_parse_value` 会把 'true'/'false' 保留为字符串；list 子字段同样要走它。

3. **验证**：扩展 `scripts/test_editor_schema_form.py`，POST 一个带 features 的 feature_grid（`module_0_features_count=2` + 各子字段），确认 YAML 还原出 `features: [{...},{...}]`，再构建确认渲染。

**P1 — 已有模块统一走 schema 表单**
现在已有模块用旧 Jinja2 分支（`panel_page_edit.html` 的 14 个 `{% elif module.type %}`）。已转的 6 个 block 可以让服务端渲染也走 schema 占位 + JS 初始化填充，删掉对应 Jinja2 分支。**与 Phase 6 清理合并做**。

**P2 — 继续转剩余 block（按难度排序）**
~~`highlight_card`~~ 已转（2026-06-01，见「十四」）。未转 7 个：`item_detail`（嵌套 list：images+specs，需 renderer 支持嵌套 list——目前规范说不支持嵌套，要评估）、`contact_form`（表单字段特殊）、`data_grid`/`product_grid`（**Phase 4 数据集驱动**，data-source 机制 renderer 已支持但未接真实 block）、`contact_info`（数据来自 settings.contact，需 renderer 加"从 settings 取数"能力）、`hero_banner`（轮播 JS + list/dict 双数据形态）。`item_data` 不转（是数据集条目编辑器，非页面 block）。

**P3 — Phase 6 清理**
删 `admin_modules.js` + `panel_page_edit.html` + `page_home.html` 的硬编码分支；删 meta.yaml 的 fields 键；删 `.jinja2.bak`；开关默认改 True。

### 非代码遗留（环境/约定）
- **richtext 录入侧 sanitize**：richtext 按 innerHTML 不转义，内容须在编辑器录入时做 HTML 白名单清洗（防存储型 XSS）。目前编辑器是否做需确认。
- **改 block 后须重启**：`_SCHEMA_CACHE`（builder.py）进程内永不失效，改 block 模板后开发服务器要重启才生效（同 CLAUDE.md 的 Flask 非 debug 不重载坑）。
- **key 约定**（前后端对齐用）：样式 `style_<token>`、整块显隐 `_hidden`（字符串 'true'/'false'，renderer 用 `_is_truthy` 判断）、数据集驱动列表数据集名 `dataset`。
- **图标扩展**：新图标加进 `icon_registry.py` 的 `ICON_REGISTRY` 即可，全 block 共用。

### 关键文件地图（续作直接定位）
| 文件 | 职责 |
|------|------|
| `app/core/block_parser.py` | HTML→BlockSchema（_Node 有序节点树、CDATA、项模板识别） |
| `app/core/block_renderer.py` | schema+数据→HTML（5 步管线、icon/href/style 注入、转义、白名单） |
| `app/core/style_registry.py` | CSS 变量 token 注册表 |
| `app/core/icon_registry.py` | 图标名→SVG（46 个） |
| `app/core/builder.py` | `_make_render_block`/`_load_block_for_render` 双路径 + `_SCHEMA_CACHE` |
| `app/core/template_loader.py` | `scan_blocks` 附加 is_data_attr/schema |
| `app/core/routes.py` | `_parse_modules_form`（通用 data-* list 解析 + 硬编码兜底）、`page_panel`（下发 blocks/style_registry/icon_list） |
| `app/templates/dashboard/panel_page_edit.html` | `generateSchemaForm`/`generateSchemaStyleForm`/`_schemaListEditor`/`schemaListAdd`/`_schemaListReindex`、`addModule`（is_data_attr 拦截） |
| `site_templates/dengtec/blocks/<name>/template.html` | data-* 模板；旧版备份 `template.jinja2.bak` |

---

## 十三、Phase 3 编辑器闭环实施记录（2026-06-01）

落地「十二」的 **P0**：让店主在后台**增删 list/grid 条目**，并把后端解析通用化。改 4 文件、+259 行。

**改动：**

| 文件 | 改动 |
|------|------|
| `block_parser.py` | 新增 `_item_children()`：list/grid 项模板根是 **leaf**（如 logo 墙 `<img data-name="logo" data-href="link">`）时，把该 leaf 暴露为单个 child（name=logo, type=image, href_field=link）。group 项行为不变。纯增量，渲染器不受影响（leaf 项仍走 `_inject_root_leaf`） |
| `routes.py` `_parse_modules_form` | 新增**通用 data-\* list/grid 解析**：按 schema 还原 `module_<i>_<listName>_count` + `module_<i>_<listName>_<j>_<subField>` → `data[listName]=[{...}]`，data-href 子字段（logo→link）一并还原；命中的 listName 跳过对应硬编码分支。`schema_by_type` 由 `_current_context()` 取模板 schema |
| `routes.py` `page_panel` | 下发 `icon_list=icon_names()`（顺带补上新页分支漏传的 `style_registry`） |
| `panel_page_edit.html` | `generateSchemaForm` 的 list/grid 分支由占位提示改为 `_schemaListEditor`（增删条目 + 子字段子表单 + 重排重命名）；`_schemaFieldHtml` 的 icon 字段改为**下拉选择器**（`iconList` 来自 `iconListJson`）；新增 `_schemaIconOptions`/`_schemaListEditor`/`_schemaListItemHtml`/`schemaListAdd`/`schemaListRemove`/`_schemaListReindex` |
| logo_cloud 旧 Jinja2 编辑器 + 硬编码 parser | 键名 `{image,name,link}` → `{logo,link}`，对齐 data-\* renderer（否则新增的 logo_cloud 重载后用旧编辑器编辑会丢图） |
| `scripts/test_editor_schema_form.py` | +17 项：POST feature_grid（group 项×2）+ logo_cloud（leaf 项×1）通用命名 → 验证 YAML 还原 + 渲染闭环（icon SVG、列数、href、无 data-\* 残留） |

**命名契约（前后端对齐）：** 条目子字段 `module_<i>_<listName>_<j>_<subField>` + 隐藏 `module_<i>_<listName>_count`，listName = list 字段的 data-name（复数，如 features/stats/steps/logos）。**与旧 Jinja2 编辑器的单数命名（feature_count 等）不同**，故现有模块的旧编辑器仍由硬编码分支兜底，两套互不冲突。

**双系统现状（这 4 个 block）：** 新增模块走 schema 条目编辑器（复数命名→通用解析）；已有模块仍走旧 Jinja2 编辑器（单数命名→硬编码分支）。同一份 `data[listName]` 键一致，故"新增→保存→重载"数据不丢，仅编辑器 UI 在重载后从 schema 表单切回 Jinja2（功能等价）。**统一到 schema 表单属 P1，留待 Phase 6 清理**。

**验证：**
- 单测：`test_block_roundtrip` 48/48、`test_editor_schema_form` 37/37（含新增 17 项）、`test_section_title`/`test_e2e_section_title`/`test_render_block_compat` 均通过（compat 的 home 页 1 处空白差异为改前既存，与本次无关）。
- 构建：flag ON 全站 `build_site(1)`，en/home 的 feature_grid（3 卡片+图标 SVG）、en/about 的 stat_counter（数字+标签+动画 script）正确渲染，全站零 data-\* 残留。
- 浏览器（Playwright，真实 Chromium）：登录→开面板→新增 feature_grid→「+添加条目」×2→icon 下拉选值+填字段→删第 2 条+重排→再添加→提交，13/13 通过；真实"浏览器提交→后端通用解析→YAML"闭环成立，features 数组正确落库。

**仍待做（承接 P1/P2/P3）：**
- ~~P1：已有模块统一走 schema 表单~~ ✅ 已完成（2026-06-01，见「十六」）：现有 data-* 模块用 JS 挂载 schema 表单回填，开关默认改 True。旧硬编码 Jinja2 elif 分支 + addFeature/addStat 等 JS 已成死代码（被拦截），实际删除留待后续纯清理。
- P2：`highlight_card`/`data_grid`/`product_grid` 已转（见「十四」「十五」）；`hero_banner`/`item_detail`/`contact_info`/`contact_form` 评估后保留 Jinja2（见「十五·乙」）。
- 编辑器侧 list 条目暂为 URL 文本输入（image 子字段未接文件上传 UI，后端已可兜 `_file`，按需补前端）。

---

## 十四、highlight_card 转 data-*（2026-06-01，P2 第 1 个）

承接 P2，转第 7 个 block。group 根 + 1 个叶子文本 list（features）+ 2 个带 data-href 的按钮，是检验「十三」list 条目编辑器（叶子项 + href）的好样本。

**改动文件：**

| 文件 | 改动 |
|------|------|
| `blocks/highlight_card/template.html` | 旧 Jinja2（27 个 `{% set %}` + 大量内联 style）→ 纯 data-* 声明式：root `group data-hideable data-style="dir"`；字段 image/tag/title/desc(textarea)/**features(list，项=叶子 `<li data-name="text">`)**/primaryBtn(href=primaryLink)/secondaryBtn(href=secondaryLink)。旧版备份 `template.jinja2.bak` |
| `static/css/main.css` | `.hl-grid` 由 `grid` 改 **flex + `flex-direction: var(--dir, row)`**（变量从 section 继承）；`.hl-features li.hl-feature::before` 提供 ✓（仅作用 data-* 输出，旧 .bak 文本里硬写的 ✓ 不受影响）；`.hl-text` 收回 `padding: 2rem`；移动端 `flex-direction: column`。保留 `.hl-grid--reverse`（flag off 的 .bak 仍用） |
| `seed_data/pages/home.yaml`、`about.yaml` | `image_position: left/right` → `style_dir: row / row-reverse`（对齐 data-style token） |

**简化（对齐方案 4.4）：** 丢弃旧 meta 的像素级微调字段（section_bg/各 padding/各 color/border_radius 等，回到 CSS 控制），只保留 `dir` 一个结构性样式 token。meta.yaml 的旧 `fields` 暂留（同其它已转 block，Phase 6 统一清）。

**验证：**
- 解析：schema = group + 7 字段，features list 的项为叶子 `text`（children=[text]）。
- 渲染（直接 + builder 全链路）：en/home highlight_card 正确出 hl-feature(✓)、`--dir: row`、按钮 href，空图/空副按钮自动 hidden，零 data-\* 残留；compat 仍仅 home 既存空白差异（.bak 未动）。
- 浏览器（Playwright，真实 Chromium）7/7：新增 highlight_card → desc 为 textarea、primaryBtn 自动生成 primaryLink 链接输入、features 条目编辑器增删 → 提交，YAML 还原 `features:[{text},{text}]` + primaryBtn/primaryLink，渲染闭环正确。

> 注：`.jinja2.bak` 被 .gitignore（全部已转 block 皆如此，属既有约定）——flag off 回退依赖本地 .bak，生产应以 `ENABLE_DATA_ATTR_BLOCKS=1` 运行。此为既存事项，非本次引入。

---

## 十五、Phase 4 数据集驱动 + 架构边界（2026-06-01）

### 甲、data_grid / product_grid 转 data-*（Phase 4）

转这两个数据集驱动 block，为此给渲染器补了一套通用能力（不写任何 block 专属逻辑）：

| 新增渲染器能力 | 文件 | 说明 |
|---|---|---|
| `data-href-template` | `block_renderer.py` `_inject_href`/`_fill_template` | 含 `{占位符}` 的链接模板，从 `context['vars']`（base_url/lang/current_path）+ 当前项字段填充；占位符无值则跳过（不完整链接）。过 scheme 白名单。|
| `data-fallback` | `block_parser.py` + `_field_value` | 字段空时依次回退备选 key：title←name、desc←summary/excerpt/description——解决各数据集字段名不一致 |
| 标量列表项 | `_inject_root_leaf`/`_expand_list` | list 项是字符串（如 tags）时值即本身，不再要求 dict |
| `data-page-size` 上限 | `_expand_list` | 数据集列表最多展示 N 条（product_grid max 6）|
| 静态 href 模板补扫 | `_fill_static_href_templates` | "查看全部"等仅依赖上下文变量的链接，全树补扫填充 |
| 渲染上下文扩展 | `builder.py` `_make_render_block` | context 加 `vars`={base_url, lang, current_path} |
| 编辑器数据集下拉 | `panel_page_edit.html` `_schemaDatasetField` | list 字段有 `data-source` → 不手动增删：具名（products）只读提示、空串给数据集下拉（存 `data.dataset`）|

**模板写法：** 复用现成 `.dg-card` 视觉（加一条 `.dg-card-image img` 规则替代旧背景图）。
- `product_grid`：`data-source="products"` 固定 + `data-page-size="6"` + 每项 `data-href-template="{base_url}/{lang}/products/{slug}/"` + 末尾"查看全部"静态模板链接。
- `data_grid`：`data-source=""`（店主选 dataset）+ 每项 `data-href-template="{base_url}/{lang}{current_path}{slug}/"`；title `data-fallback="name"`、desc `data-fallback="excerpt,description"`、tags 标量列表、category/date 空值自动隐藏。简化丢弃：分页（数据集均 ≤6 条，全展示）、category 过滤、card_layout、columns 微调。

**验证：** 新增 `scripts/test_dataset_blocks.py` 16/16（用真实 seed 数据集渲染 product_grid 5 卡 / data_grid portfolio 6 卡 / posts 4 卡，校验 href 模板、fallback、标量 tags、page_size、空数据集隐藏、零 data-\* 残留）；roundtrip 48 / editor 37 全过；flag ON 全站构建零残留。
> 注：site 1 无数据集数据，故其页面 data_grid 渲染为空属正常（无数据→空），非回归。

### 乙、保留 Jinja2 的 4 个 block（架构边界，**不转 data-***）

落地中确认：data-* 声明式模型适合**内容块**（text/image/list/数据集），不适合下列**交互/设置/表单逻辑**块。强转要么丢功能、要么堆 block 专属渲染器特性（违背"通用"初衷）。按方案「四·4.5 / 六」对 Header/Footer 的同一判断，这 4 个保留 Jinja2：

| block | 不转原因（结构性/语义性硬伤）|
|---|---|
| **hero_banner** | ① video/image 按 `item.type` 条件渲染**不同元素**；② 圆点导航是对 slides 数组的**第二次遍历**——data-* 一个 list 只能在一处展开。轮播 JS + 每帧媒体上传/视频。|
| **item_detail** | 同一个 images 数组要**同时**做主图 + 缩略图列表（一处展开装不下）；放大镜 + 缩略图切换 JS 依赖随机 block_id。|
| **contact_info** | 5 张固定卡（写死 SVG 图标 + 标签）数据来自 `settings.contact`（非 module.data）；每卡独立 show 开关（data-* 的 hideable 是整块级，非逐卡）。|
| **contact_form** | 带 show_name/email/phone/company/message 开关的**固定表单输入**，不是用户内容字段。|

> `item_data` 同样不转（数据集条目编辑器，非页面 block）。故 data-* 化的合理终点是 **9 个内容/数据集块**，而非 14/14。若将来确需转这 4 个，应作为独立专题（每个先建对应渲染器能力：条件元素 / 一数组多处展开 / settings 取数 / 逐卡 hideable），不混在通用迁移里。

### 丙、本次改动文件清单（甲）

`block_parser.py`（href_template/fallback 字段）、`block_renderer.py`（href 模板化/fallback/标量项/page_size/静态链接补扫）、`builder.py`（context vars）、`panel_page_edit.html`（数据集下拉）、`blocks/{data_grid,product_grid}/template.html`（+ `.jinja2.bak` 备份）、`static/css/main.css`（`.dg-card-image img`）、`scripts/test_dataset_blocks.py`（新增）。

---

## 十六、P1：现有模块统一 schema 表单 + 开关默认开（2026-06-01）

转完 9 个 block 后，让这些 block 的**现有模块**（已存在于页面里的）也走 schema 表单，并把总开关默认改 True。

**为什么必须做：** 现有模块此前走旧 Jinja2 服务端编辑器分支，写的是旧键名（如 section_title 的 `text_align`）；而 data-* 渲染器读新键名（`style_text-align`）。开关关时渲染走 .jinja2.bak（旧键名一致）没问题，但开关开后两者不一致 → 必须先统一编辑器再翻开关。

**做法（JS 挂载，不删旧分支）：**
| 改动 | 文件 | 说明 |
|---|---|---|
| 传 data-* 类型集合 | `panel_page_edit.html` | `{% set data_attr_types = blocks | selectattr('is_data_attr') | map(attribute='name') | list %}` |
| 拦截分支 | `panel_page_edit.html` | 模块 desktop 编辑区 if/elif 链最前加 `{% if module.type in data_attr_types %}` → 渲染内容/样式两个**空挂载点** + `mdata | tojson`；旧的 9 个 elif 分支被拦截成死代码（留待纯清理删） |
| JS 挂载 | `panel_page_edit.html` `initSchemaMounts()` | 面板加载时遍历挂载点，用 `generateSchemaForm`/`generateSchemaStyleForm` + mdata 回填；幂等（`data-mounted` 守卫），语言切换重载也安全 |
| 开关默认开 | `config.py` | `os.environ.get('ENABLE_DATA_ATTR_BLOCKS','1') != '0'`；设 `=0` 回退 |

**效果：** 已转 9 个 block 的新增 + 现有模块走同一套 schema 表单（存 data-* 渲染器读的新键名）；未转的 4 个块不在 `data_attr_types`，仍走各自旧 Jinja2 编辑器；开关开后 data-* 块走渲染器、Jinja2 块走 Jinja2，共存。

**验证：**
- Playwright 11/11：测试页含现有 section_title + feature_grid 模块 → 挂载点被现有数据回填（tag/title、features 两条 功能一/功能二）、无旧 `text_align` 字段、改 title 提交后存新键名（`style_text-align` 保留、features 完整）。
- 默认开关（不设 env）全站构建：en/home 上 hl-feature / service-card-title / dg-list（data-*）与 hero-banner-slide（Jinja2）共存，零 data-* 残留。
- roundtrip 48 / editor 37 / dataset 16 全过；compat（显式设开关关）仍仅 home 既存空白差异。

**仍待（纯清理，非功能）：** 删 `panel_page_edit.html` 里被拦截的 9 个死 elif 分支 + `addFeature/addStat/addLogo/addStep/addHeroSlide` 等已无用 JS + meta.yaml 的 `fields` 键。这些是死代码清理，不影响功能，按需做。
