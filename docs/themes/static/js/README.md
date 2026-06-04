# static/js/：主题脚本

`static/js/` 放主题的 JavaScript 文件。构建时整个目录原样拷进 `output/.../static/js/`。

**可选**——如果主题只用 CSS 就能完成交互（hover 菜单、transition 动画），这个目录可以空着。

## 一、引入方式

在 `_base.html` 的底部（`scripts` block 之前或之内）用 `defer` 引入：

```html
<script src="{{ base_url }}/static/js/main.js" defer></script>
```

> `defer` 保证 DOM 就绪后才执行、不阻塞首屏渲染。

## 二、哪些放这里、哪些内联

| 放哪 | 标准 | 示例 |
| --- | --- | --- |
| `static/js/` 外部文件 | 多页共用、超过 20 行 | 图片懒加载、筛选/分页逻辑、动画库 |
| `_base.html` 内联 `<script>` | 每个页面都需要、10 行以内 | 移动端菜单切换（`.open` toggle） |

## 三、移动端菜单（必须）

每套主题至少需要一段 JS 控制汉堡菜单的展开/收起。建议内联写在 `_base.html` 的 `scripts` block 里：

```html
{% block scripts %}
<script>
  const toggle = document.querySelector('.mobile-toggle');
  const nav = document.querySelector('.main-nav');
  toggle.addEventListener('click', () => {
    nav.classList.toggle('open');
  });
</script>
{% endblock %}
```

逻辑极简：CSS 管显示/隐藏（`.main-nav { display: none; } .main-nav.open { display: block; }`），JS 只 toggle class。

## 四、列表筛选 / 分页（可选）

列表页的筛选和分页通过 JS 对已渲染的 DOM 做显隐（零网络请求），逻辑放 `static/js/list.js`：

```html
<script src="{{ base_url }}/static/js/list.js" defer></script>
```

- 所有条目构建期已渲染进 HTML（SEO 吃得到）
- `data-page-size` 控制每页条数，超出当前页的条目加 `hidden`
- 筛选靠条目上的 `data-f-*` 属性匹配
- 关 JS 时降级为"全部可见、不分页"（内容不丢）

## 五、关键规则

- **不用框架**——不引 jQuery、Vue、React，纯原生 JS。
- **不用第三方追踪脚本**——百度统计、客服等走 `settings.head_html`（用户自己填），不写进主题 JS。
- **defer 引入**——永远不阻塞 HTML 解析。
- **关 JS 不能丢内容**——所有内容必须先存在于 HTML（构建期渲染），JS 只做显隐/增强。
