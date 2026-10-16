# demo/ — 后台 UI 静态演示

后台管理界面的**独立静态演示**，不依赖 Flask 运行时，用于离线展示三栏布局（导航 / 预览 / 属性面板）、预览标签栏、首页模块编辑器的视觉效果。

## 目录

- [用途](#用途)
- [文件](#文件)
- [生成命令](#生成命令)
- [与上层项目的关系](#与上层项目的关系)

## 用途

把 [app/static/css/admin.css](../app/static/css/admin.css) 内联进一个自包含 HTML，配上假数据，直接用浏览器打开即可看后台长什么样——无需起服务、登库、建站。适合给非技术干系人快速演示界面。

## 文件

| 文件 | 说明 |
|---|---|
| `build_admin_demo.py` | 生成脚本：读 admin.css + 内联模板 → 输出 HTML |
| `admin-dashboard-demo.html` | 生成产物（直接浏览器打开） |

## 生成命令

在项目根目录执行：

```bash
python demo/build_admin_demo.py
```

脚本会读取 `app/static/css/admin.css`（相对项目根定位，见脚本注释 #33），生成 `demo/admin-dashboard-demo.html`。改完后台样式后重跑即可刷新演示。

## 与上层项目的关系

- 样式来源唯一：`app/static/css/admin.css`（与真实后台同一份 CSS，保证演示与实际一致）
- **纯演示**：所有按钮走 `demoToast()` 假动作，不调任何后端、不读真实数据
- 真实后台界面见 [app/templates/](../app/templates/)，样式编辑见 skill `admin-edit-admin-style`
