# admin-dashboard-demo.html —— 管理后台 UI 原型

独立的 HTML 文件，不需要启动 Flask 就能在浏览器里预览管理后台的完整 UI。
用于快速迭代设计、验证交互、对齐前端实现方向。

路径：`demo/admin-dashboard-demo.html`

## 为什么要有这个 Demo

- 实际后台页面散落在多个 Jinja2 模板里，改一个样式要重启服务器、登录、点几层菜单才能看到效果
- Demo 把所有 UI 状态集中在一个文件里：三种侧栏模式、主题色切换、模块展开/收缩、导航切换
- 设计和前端在这里快速试错，确认方案后再同步到 `app/templates/` 和 `app/static/css/admin.css`

## 设计原则

1. **主题色全部联动** — 通过 `setThemeColor(hex)` 计算 CSS 变量，所有按钮/链接/激活态/徽章/图标统一变色
2. **侧栏三种模式独立配色** — 深色用 `rgba(255,255,255,x)` 透明度阶梯，浅色/白色用灰度阶梯
3. **内容区简约** — 模块卡片无阴影、细边框、表单紧凑，重点在配置内容本身
4. **状态可见** — 激活导航项有指示条+背景，tab 用下划线式，分组用卡片框

## 技术要点

### CSS 变量双层架构

Bootstrap CDN 在 `.btn-primary` 等类上硬编码了 `--bs-btn-bg`，会屏蔽 `:root` 级别的同名变量。
解决方案：引入 `--theme-btn-*` 中间变量，`setThemeColor()` 设置 inline style 覆盖。

### 侧栏颜色层级（深色模式）

| 元素 | 颜色 | 说明 |
|---|---|---|
| 导航文字 | `rgba(255,255,255,0.75)` | 常规可见 |
| 分组标题 | `rgba(255,255,255,0.5)` | 次要信息 |
| 箭头/图标 | `rgba(255,255,255,0.75)` | 跟随文字 |
| 徽章背景 | `rgba(255,255,255,0.15)` | 半透明胶囊 |
| 激活态指示条 | `rgba(255,255,255,0.8)` | 左侧竖线 |

### Nav-light / Nav-white 激活态

激活态背景、文字、图标全部用 `var(--bs-primary)` / `rgba(var(--bs-primary-rgb), 0.1)` 跟随主题色。

## 与正式实现的对应关系

| Demo 区域 | 正式模板 |
|---|---|
| 左侧导航 | `app/templates/dashboard/page_home.html` 侧栏部分 |
| site-info | 站点名称/标识显示区 |
| 右侧属性面板 | `app/templates/dashboard/panel_page_edit.html` |
| 模块配置 | `app/templates/dashboard/_block_editor.html` |
| 样式 | `app/static/css/admin.css` |

## `build_admin_demo.py`

从正式模板自动拼接生成 Demo HTML 的脚本。**生成后会覆盖手动修改**，仅用于初始化或正式模板大改后重新同步。日常 UI 微调直接在 HTML 上改。

```bash
python demo/build_admin_demo.py
```
