# Block 系统改造方案

> 将 block 模板从 Jinja2 命令式写法迁移到声明式纯 HTML + data-* 属性，对齐 [data-attributes-reference.md](docs/data-attributes-reference.md) 和 [Block 示例库.md](docs/Block%20示例库.md) 规范。

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

详见 [data-attributes-reference.md](docs/data-attributes-reference.md)，这里只列关键点：

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

### Phase 1：基础设施（不改任何 block 模板）

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

### Phase 2：转换简单 block（验证全流程）

转换 4 个最简单的非列表 block，验证"编辑 → 存储 → 构建"完整链路。

| block | 字段 | 复杂点 |
|-------|------|--------|
| **section_title** | tag, title, desc, btn_text, btn_url | 无 |
| **text_content** | title, body | body 是富文本 |
| **contact_info** | addr, phone, email, map | email 有 data-href，map 有 embed |
| **hero_banner** | title, subtitle, cta, bg | data-style="bg"，有 data-href |

**每步操作：**
1. 重写 `template.html` 为纯 HTML + data-*（现有 Jinja2 版改名为 `template.jinja2.bak`）
2. 在编辑器中测试 schema 驱动表单生成（新增/编辑/保存）
3. 构建站点，浏览器打开 output/ 确认渲染结果
4. 与改造前的 output/ 做 diff 对比

**Phase 2 交付物：** 4 个简单 block 全流程走通，编辑器不再依赖硬编码分支。

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
