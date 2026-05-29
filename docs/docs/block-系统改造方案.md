# Block 系统：Jinja2 模板 → 纯 HTML + data-* 属性

## Context

当前 block 模板用 Jinja2 编写（`{% if %}`, `{% for %}`, `md.get('title')`），与文档声明的"纯 HTML + data-* 属性"规范是两套完全不同的体系。本次改造将 block 模板从命令式 Jinja2 切换到声明式纯 HTML，让"HTML 即 Schema + 默认渲染"，系统自动解析 data-* 属性生成编辑器和注入数据。

**页面级模板**（`_base.html`, `index.html`, `_page.html`, `_modules.html`）保持 Jinja2 不变。仅改 `blocks/*/template.html`。

---

## 新增 3 个模块

### `app/core/block_parser.py`
解析纯 HTML block 模板，提取 schema。
- 用 stdlib `html.parser.HTMLParser` 遍历 DOM
- 对每个 `data-name` 元素提取 `FieldDef`（type/tag/default_text/href_field/attributes）
- 根元素提取 style_tokens/hideable/source/page_size/cols
- list/grid 容器识别项模板：容器内第一个带 data-name 的直接子元素的 innerHTML
- 输出 `BlockSchema` dataclass

### `app/core/block_renderer.py`
接收 BlockSchema + module.data + 全局 context，产出最终 HTML。
- 字段注入：按 data-name 匹配 data dict，写入 innerText/src/href
- 列表展开：data-source=manual → 循环 module.data[list_name]；data-source=products → 查 context['all_datasets']
- 显隐：data-hideable + 空值自动 hidden
- CSS 变量注入：读 data-style → 查 style_registry → 写 style="--cols: 3"
- 用字符串替换（非 DOM 重建）保持格式稳定

### `app/core/style_registry.py`
CSS 变量 → UI 控件映射表（单一真相源）。
```python
STYLE_REGISTRY = {
    'cols':       { control: 'select', options: ['1','2','3','4'], css_var: '--grid-cols' },
    'bg-color':   { control: 'color', css_var: '--bg-color' },
    'dir':        { control: 'select', options: ['row','row-reverse'], css_var: '--flex-direction' },
    'bg':         { control: 'image', css_var: '--bg-image' },
    'text-align': { control: 'select', options: ['left','center','right'], css_var: 'text-align' },
    # ... 约 20 个
}
```

---

## 修改现有文件

| 文件 | 改动 |
|---|---|
| **builder.py** | 注册 `render_blocks()` 为 Jinja2 全局函数；在 `_modules.html` 中替换 `{% include %}` 循环为函数调用；检测 block 格式（有 `{%` 用旧路径，纯 HTML 用新渲染器） |
| **template_loader.py** | `scan_blocks()` 增加格式检测字段；新增 `scan_block_schema(block_name)` |
| **routes.py** | 新增 `GET /_api/block/<name>/schema` 端点返回 JSON schema；`page_home()`/`page_panel()` 传递 schema 给模板 |
| **admin_modules.js** | `buildModuleHTML()` 从硬编码分支改为 schema 驱动生成表单；新增 `generateStyleForm()` 和 `generateListEditor()` |
| **_modules.html** | `{% for %}` + `{% include %}` 替换为 `{{ render_blocks(page.modules, ctx) }}` |
| **config.py** | 加 `ENABLE_DATA_ATTR_BLOCKS = True` 特性开关 |

---

## 分阶段实施

### Phase 1：基础设施（不改 block 模板）
- 创建 block_parser.py / block_renderer.py / style_registry.py
- builder 注册 render_blocks，格式检测逻辑
- routes 新增 schema API
- **交付物**：拿 mock HTML 测试解析+渲染往返正确，开关关闭不影响现有功能

### Phase 2：转换一个简单 block（section_title）
- 重写 section_title/template.html 为纯 HTML + data-*
- admin_modules.js 增加 schema 驱动表单生成（保留旧分支作 fallback）
- **交付物**：section_title 全流程走通（编辑 → 存储 → 构建）

### Phase 3：转换列表/网格 block
- feature_grid / product_grid / stat_counter
- 实现项模板识别 + 列表展开
- 前端实现 generateListEditor()
- **交付物**：手动列表 block 完整可用

### Phase 4：转换数据集驱动 block
- data_grid 的 dataset 模式
- 实现 data-source 自动解析 + 分页
- **交付物**：数据驱动 block 完整可用

### Phase 5：转换其余 block
- text_content, contact_info, contact_form, highlight_card, process_steps, logo_cloud, hero_banner, item_detail
- **交付物**：全部 15 个 block 迁移完成

### Phase 6：清理
- 删除 admin_modules.js 中 ~500 行硬编码分支
- 简化 meta.yaml（移除 fields 键，字段全在 HTML 里）
- 删除 builder.py 旧格式兼容代码

---

## 关键设计决策

1. **数据格式不变**：YAML 中 `module.data` 的 key 名直接对应 `data-name`，已有站点数据无需迁移
2. **混合模式共存**：builder 按 block 检测格式，新旧 block 可在同一页面渲染
3. **特性开关**：`ENABLE_DATA_ATTR_BLOCKS` 控制，关闭即回退
4. **回退无数据损失**：回退只需还原 block HTML 文件为 Jinja2 版本，YAML 数据不变

---

## 验证方法

- Phase 1：用 pytest 或手动脚本验证 block_parser 对 mock HTML 的解析结果
- 每个 Phase：创建测试站点 → 编辑 block → 构建 → 浏览器打开 output/ 确认渲染正确
- 最终：`flask --app run build-site 1` 构建已有站点，对比 output/ 与改造前是否一致
