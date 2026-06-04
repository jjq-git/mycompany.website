# panel_*.html：面板片段

`panel_*.html` **不是独立文件**——它们是页面模板在 `?_fragment=1` 模式下的渲染结果。同一套模板，两种渲染路径：

```text
/dashboard/overview           → {% extends "base.html" %}   → 完整页面（侧栏 + 主内容 + 右侧面板）
/dashboard/overview?_fragment=1  → 只渲染 content block   → 纯内容 HTML，注入右侧面板
```

## 加载方式

侧栏点击 → `loadPanel(url + '?_fragment=1')` → fetch → 注入 `#right-panel`。Flask 后端检测 `_fragment=1` 参数，跳过 `base.html` 外壳，只返回内容 block。

## 为什么不用两套文件

同一套编辑 UI（表单、表格、统计卡片）写两遍只会导致两边不一致。`_fragment` 参数让同一个模板同时服务于"整页查看"和"右侧面板快速编辑"两个场景。

## 面板列表

| 概念名称 | 对应模板 | 页面内容 |
|---|---|---|
| `panel_overview` | `overview.html` | 内容统计 + 全局宽度设置 |
| `panel_company` | `company.html` | 公司名称 / 电话 / 邮箱 / 地址表单 |
| `panel_header` | `header_edit.html` | 头部变体选择（radio 卡片） |
| `panel_menu` | `menu.html` | 菜单表格编辑器 |
| `panel_footer_variant` | `footer_variant.html` | 底部变体选择 + 备案号 |
| `panel_theme` | `theme.html` | 6 个颜色字段 |
| `panel_social` | `social.html` | 5 个社交链接字段 |
| `panel_account` | `account.html` | 邮箱 + 站点数 + 退出按钮 |
| `panel_page_edit` | `page_edit.html` | 页面模块编辑器（通用，所有页面共用） |
| `panel_data_list` | `datasets.html` | 数据集 CRUD 列表 |

## 右侧面板初始状态

整页加载时右侧面板显示静态帮助文字（对应当前页面的功能说明），不是空白的。用户点击侧栏菜单或配置按钮时，`loadPanel()` 才用 `_fragment` 结果替换面板内容。
