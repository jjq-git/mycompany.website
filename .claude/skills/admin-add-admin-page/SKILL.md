---
name: admin-add-admin-page
description: "新增后台管理页面(模板 + Panel 片段 + 路由 + 导航)"
---

当用户想在店主后台新增一个管理功能时触发.典型场景:
- 新增一个 CRUD 数据集的管理页面(如"合作伙伴"、"案例")
- 新增一个独立配置表单页面(如"SEO 设置"、"社交媒体")
- 为现有功能补充后台管理界面

目标用户是店主,所有操作通过左侧导航点击后在右侧面板完成(SPA-like),
不需要整页刷新.后台使用 Bootstrap 5 + 自定义 CSS(admin.css).

核心约定:
- 全页面模板:`app/templates/dashboard/<page_key>.html`( extends `base.html`)
- Panel 片段:`app/templates/dashboard/panel_<page_key>.html`(无 extends)
- 路由:`app/core/routes.py` 中的 `@bp.route(...)` + 对应视图函数
- 导航:`app/templates/base.html` 中的 `<a class="left-nav-item">`

## 第一步:明确需求

询问用户以下信息:

| 问题 | 示例答案 |
|------|----------|
| 页面名称(中文) | 合作伙伴 |
| 页面 key(英文下划线) | partners |
| 左侧导航分类 | 内容(设置 / 内容 / 站点 三者之一) |
| 页面类型 | 单个表单页 / 数据集列表页 |
| 如是数据集,有哪些字段 | 名称(text)、Logo(image)、链接(url)、描述(textarea) |

三种导航分类的语义:
- **设置**:站点配置(公司信息、主题颜色、Header、Footer、菜单)
- **内容**:数据管理(产品、功能、博客、→ 新增的自定义数据集)
- **站点**:站点操作(概览、页面管理、模板库、发布)

## 第二步:创建 Panel 片段模板

文件:`app/templates/dashboard/panel_<page_key>.html`

关键约定(必须严格遵守):
- **不加** `{% extends %}` 或 `{% block %}`,直接写 HTML 内容
- 表单 action 必须带 `_fragment=1` 参数:
  `<form method="POST" action="{{ url_for('core.<page_key>', site=site.id, _fragment='1') }}">`
- 样式使用约定的 class:
  - 分区容器:`<div class="panel-section">`
  - 分区标题:`<div class="panel-section-title">`
  - 面板内容区:`<div class="right-panel-body">`
  - 表单控件:`<input class="form-control form-control-sm">`
  - 保存按钮:`<button class="btn btn-sm" style="background:#067a7a;border-color:#067a7a;color:#fff">`

单个表单页模板示例(panel):
```html
<div class="right-panel-body">
  <form method="POST" action="{{ url_for('core.partners', site=site.id, _fragment='1') }}">
    <div class="panel-section">
      <div class="panel-section-title">基本设置</div>
      <div class="form-group">
        <label>合作伙伴标题</label>
        <input class="form-control form-control-sm" name="title"
               value="{{ data.get('title', '') }}">
      </div>
      <div class="form-group">
        <label>描述</label>
        <textarea class="form-control form-control-sm" name="desc"
                  rows="3">{{ data.get('desc', '') }}</textarea>
      </div>
    </div>

    <div style="padding:12px 20px;border-top:1px solid #e8ecf0;">
      <button type="submit" class="btn btn-sm"
              style="background:#067a7a;border-color:#067a7a;color:#fff">保存</button>
    </div>
  </form>
</div>
```

## 第三步:创建全页面模板

文件:`app/templates/dashboard/<page_key>.html`

如果全页面与 Panel 内容完全相同,用 `{% include %}` 避免重复:

```html
{% extends "base.html" %}
{% block content %}
<div class="main-content">
  <div class="right-panel" style="width:600px;max-width:100%;margin:32px auto;float:none;">
    {% include "dashboard/panel_<page_key>.html" %}
  </div>
</div>
{% endblock %}
```

如果页面包含列表(如数据集),直接写表格等内容.

## 第四步:注册路由

在 `app/core/routes.py` 中添加两个路由(GET 渲染 + POST 处理).

标准路由模板(单个表单页):

```python
@bp.route('/<page_key>', methods=['GET', 'POST'])
@login_required
def <page_key>():
    user, site = _current_context()
    data = read_yaml(site.id, '<data_file>.yaml') or {}
    is_fragment = request.args.get('_fragment') is not None

    if request.method == 'POST':
        for field in ['field1', 'field2', 'field3']:
            data[field] = request.form.get(field, '').strip()
        write_yaml(site.id, '<data_file>.yaml', data)
        flash('已保存')
        if is_fragment:
            return redirect(url_for('core.<page_key>', _fragment='1', site=site.id))
        return redirect(url_for('core.<page_key>', site=site.id))

    template = 'dashboard/panel_<page_key>.html' if is_fragment else 'dashboard/<page_key>.html'
    return render_template(template, site=site, user=user, data=data, active='<page_key>')
```

核心约定:
- 用 `_current_context()` 获取当前用户和站点(处理权限)
- `_fragment=1` 参数控制返回完整页面还是面板片段
- POST 成功后重定向到 `_fragment=1` 的 GET(避免面板内跳转到整页)
- 传递 `active='<page_key>'` 控制左侧导航高亮
- 数据读写使用 `read_yaml()` / `write_yaml()`(`app/core/site_storage.py`)

如果是多语言支持的面板,参考 `_get_panel_lang()` 和 `page_panel()` 的实现.

## 第五步:添加左侧导航项

在 `app/templates/base.html` 对应分类区域添加导航项:

```html
<a class="left-nav-item {% if active == '<page_key>' %}active{% endif %}"
   href="{{ url_for('core.<page_key>') }}"
   data-panel="<page_key>" title="<页面标题>">
   <svg class="left-nav-icon" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="2" stroke-linecap="round"
        stroke-linejoin="round">
     <!-- SVG 图标,24x24 viewBox -->
     <path d="..."/>
   </svg>
   <页面标题>
</a>
```

约定:
- `data-panel` 属性让导航点击自动 fetch 加载面板(如果 JS 支持)
- SVG 图标统一 24x24 viewBox,`stroke="currentColor"`,`stroke-width="2"`
- 图标语义与功能匹配(去 Feather Icons 或 Lucide Icons 找合适的 SVG path)

三个分类在 base.html 中的位置:
- **设置**:在 Header/Footer/菜单/主题等设置项附近
- **内容**:在 产品/功能/博客 等数据集管理项附近
- **站点**:在 概览/页面管理/模板库 附近

## 第六步:验证

1. 启动服务器:`python run.py`
2. 登录后台 → 选择站点
3. 点击新增的导航项 → 确认面板正确加载
4. 填写表单 → 保存 → 确认无报错,flash 消息显示"已保存"
5. 检查数据文件:`cat sites/<id>/<data_file>.yaml`
6. 刷新页面 → 确认之前保存的数据仍在
7. 检查左侧导航高亮是否正常(active class 是否生效)

## 常见问题

| 问题 | 原因 | 修复 |
|------|------|------|
| 点击导航整页跳转 | JS 未拦截点击或 data-panel 未设置 | 确认 base.html 中的 JS 逻辑 |
| 保存后跳转到整页 | POST 重定向没有 _fragment=1 | 检查 POST 后的 redirect url |
| 表单数据不保存 | 字段名不匹配或 write_yaml 路径错误 | 检查 form name 和 Python 对应 |
| 面板空白 | 模板文件路径不对或变量缺失 | 检查 render_template 的第一个参数 |
| 导航不显示 | base.html 中未添加导航项 | 确认添加位置和条件 |
| 无权限访问 | _current_context() 获取 site 失败 | 确认用户有站点且有权访问 |

## 关联文件和代码位置

| 文件 | 作用 |
|------|------|
| `app/core/routes.py:224-242` | `_current_context()` 获取用户和站点 |
| `app/core/site_storage.py:42-55` | `write_yaml()` 写数据文件 |
| `app/core/site_storage.py:58-74` | `read_yaml()` 读数据文件 |
| `app/templates/base.html` | 后台布局骨架 + 左侧导航 |
| `app/templates/dashboard/` | 所有后台页面模板 |
| `app/static/css/admin.css` | 后台样式 |

## 关联技能

- `edit-admin-style`:如果新页面需要自定义样式
- `new-block`:如果是需要新增 Block 类型的页面
- `debug-site`:如果页面数据不显示
