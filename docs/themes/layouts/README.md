# layouts：页面布局与骨架组件

`layouts/` 是主题的 HTML 模板层——页面骨架（`_base.html`）、页面布局（index / _page / detail）、模块渲染循环（`_modules.html`）、骨架组件（header / footer）。

所有布局 `{% extends "_base.html" %}`，渲染上下文见 [../README.md](../README.md) 第二节。

## 文档

| 文档 | 讲什么 |
| --- | --- |
| [_base.html.md](_base.html.md) | 页面最外层骨架：`<head>`、CSS/JS 加载、主题色变量注入、OG 标签、header/footer include、全部 Jinja2 block |
| [_modules.html.md](_modules.html.md) | 模块渲染循环：遍历 `page.modules` → 排序 → `render_block()` → 输出 HTML |
| [index.html.md](index.html.md) | 首页布局：极简，组装模块序列即可 |
| [_page.html.md](_page.html.md) | 独立页通用布局（about / contact / …）：面包屑 + 页标题 + 模块序列 |
| [list.html.md](list.html.md) | 数据集列表页通用布局（products / news / …）：筛选栏 + 模块序列 + 分页 |
| [detail.html.md](detail.html.md) | 详情页布局：一个模板通吃所有数据集，条目以 `item` 传入，靠 CSS 区分外观 |
| [header.md](header.md) | 头部导航组件：Logo、导航菜单、语言切换器、汉堡按钮，按 `settings.header.variant` 切换变体 |
| [footer.md](footer.md) | 页脚组件：链接列、版权声明、备案号，按 `settings.footer.variant` 切换变体 |

## 模板层级

```text
_base.html                     ← 页面外壳（<head>、OG、header/footer include）
  ├── header/<variant>.html    ← 头部导航（_base.html include）
  ├── index.html               ← 首页（extends _base.html）
  │     └── _modules.html      ← 模块循环（index.html include）
  ├── _page.html               ← 独立页（extends _base.html）
  ├── list.html                 ← 数据集列表页（extends _base.html）
  │     └── _modules.html
  └── detail.html               ← 详情页（extends _base.html）
        footer/<variant>.html  ← 页脚（_base.html include）
```
