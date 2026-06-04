# dashboard 页面

后台 `dashboard/` 下的页面模板文档。所有页面 `{% extends "base.html" %}`，填 `content` block。

这些页面分三组：

- **设置** —— settings_forms（company / social / theme）/ menu / variants（header / footer）/ account，配置网站基础信息和外观
- **内容** —— page_edit / pages / datasets，管理页面模块和内容集合
- **概念** —— `_fragment` 渲染机制：panel 不是独立文件，是同一模板的去壳渲染

## 文档

| 文档 | 讲什么 |
|---|---|
| [overview.html.md](overview.html.md) | 仪表盘：内容统计 + 全局宽度 |
| [settings_forms.html.md](settings_forms.html.md) | 设置表单（company / social / theme）：同一套 card + label + input 骨架 |
| [menu.html.md](menu.html.md) | 菜单配置：表格编辑器、类型切换、新增删除上下移 |
| [variants.html.md](variants.html.md) | 变体选择（header_edit / footer_variant）：radio 卡片网格 |
| [account.html.md](account.html.md) | 账号管理：邮箱 + 退出 |
| [page_edit.html.md](page_edit.html.md) | 页面模块编辑器：通用，所有页面共用模块添加/排序/配置 |
| [datasets.html.md](datasets.html.md) | 内容集合：通用数据集列表，表格 + 新建/编辑/删除 |
| [panel-fragments.md](panel-fragments.md) | 面板片段：`_fragment` 渲染机制（panel 不是独立文件，是同一模板的去壳渲染） |
