# Block 系统

页面由「模块（block）」拼成。一个 block = 一段**纯 HTML + `data-*` 属性**的模板，这段 HTML 同时是两样东西：**声明可编辑字段（schema）** + **渲染骨架**。系统自动解析它 → 生成编辑表单 → 注入数据 → 输出干净 HTML。主题作者只写这段 HTML，不写后端、不写表单代码。

本目录：

- 本文 —— 设计总览
- [data-attributes.md](data-attributes.md) —— `data-*` 8 个属性速查
- [library.md](library.md) —— block 目录（含设计中的类型，不等于当前已实现）

## 一个 block 长什么样

```html
<section data-name="features" data-type="list"
         data-hideable data-style="cols" style="--cols: 3">
  <div data-name="feature" data-type="group">
    <img data-name="icon" data-type="image" src="icon1.svg">
    <h3 data-name="title" data-type="text">高性能</h3>
    <p data-name="desc" data-type="text">说明文字……</p>
  </div>
</section>
```

- `data-name` = 字段 key，对应 YAML `module.data` 里的 key。
- `data-type` = 内容类型（text / image / video / list / grid / group…）。
- HTML 里的文字 / src / style 值 = 默认值。

## 一个 block 的目录

```text
themes/<主题>/blocks/<block名>/
  template.html         默认变体（= schema + 渲染骨架）
  variants/*.html       其它排版变体（data-name 必须一致，只换结构）
  meta.yaml             label、预览图、variants 列表（主题作者维护）
  structure-diagram.svg 结构示意（可选）
```

## 渲染流程

```text
template.html ──解析 data-*──▶ schema ──▶ 后台自动生成右栏编辑表单
                                              │ 用户填 → module.data（YAML）
template.html + module.data ──注入──▶ 干净静态 HTML（剥掉 data-*）
```

后台「三栏」（左导航 / 中预览 / 右属性面板）不变；右侧表单由 schema **自动生成**，不再为每个 block 类型写分支。

## 核心约定

- **项模板**：list / grid 容器内「第一个带 `data-name` 的直接子元素」即项模板，按数据条数复制。
- **空值自动隐藏**：text / image / video 等叶子值为空 → 自动加 `hidden`。
- **数据格式**：`module.data` 的 key = `data-name`；换变体 = 同一份数据换一套 HTML 结构。
- **样式只开放结构性变量**：`data-style` + 约 10 个全局 CSS 变量（cols / dir / bg…），登记在 `STYLE_REGISTRY`；不开像素级微调（padding / margin / 字号由主题 CSS 定）。
- **CSS 变量默认值只写在 CSS 里**（`var(--cols, 3)`），HTML 与注册表不重复。
- **Header / Footer 也是 block**：写在 `blocks/header/`、`blocks/footer/`，必显（不加 `data-hideable`）。其中导航菜单、语言切换不靠用户手填——用保留数据源 `data-source="menu"` / `"languages"` 由 builder 注入；页眉 / 页脚的不同排版走 block 变体（`variants/*.html`，对应 `settings.header.variant` / `settings.footer.variant`）。

## 功能型 block 的阶段性约定

- **联系表单（`contact_form`）已内置留言系统**：`form_action` 留空时表单自动提交到平台后端 API（`/api/contact/<site_id>`），留言存入 `contact_messages` 表，店主在后台"留言管理"页面查看。反垃圾：蜜罐隐藏字段 + 速率限制（每分钟 10 条）。CORS 开放、CSRF 豁免（静态站点无法生成 token）。`form_action` 填了第三方 URL 则仍走外部提交（兼容原有行为）。

## 不做

- 不开放像素级样式微调。
