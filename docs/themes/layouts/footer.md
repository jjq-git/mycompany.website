# footer：页脚

`layouts/footer/<variant>.html` 是网站的页脚组件——链接列、版权声明、备案号。`_base.html` 按 `settings.footer.variant` 选择引入哪个变体。

## 一、引入方式

```html
{% block footer %}
  {% include 'footer/' + settings.footer.variant + '.html' %}
{% endblock %}
```

和 header 同一套机制：变体默认值由主题的 `i18n/<lang>/settings.yaml` 给，用户可在后台切换。

## 二、默认变体（default.html）

```html
{# layouts/footer/default.html #}
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      {% for col in settings.footer.links %}
      <div class="footer-col">
        <h4>{{ col.title }}</h4>
        {% for link in col.links %}
        <a href="{{ link.url }}">{{ link.label }}</a>
        {% endfor %}
      </div>
      {% endfor %}
    </div>

    <div class="footer-bottom">
      <span>{{ settings.copyright | default('© ' + now.year | string + ' ' + settings.title + ' 版权所有') }}</span>
      {% if settings.icp %}
      <span class="footer-icp">{{ settings.icp }}</span>
      {% endif %}
    </div>
  </div>
</footer>
```

### 三个组成部分

| 组件 | 选择器 | 说明 |
| --- | --- | --- |
| 链接网格 | `.footer-grid` + `.footer-col` | 遍历 `settings.footer.links`，每列一个 `<h4>` + 链接列表 |
| 版权声明 | `.footer-bottom` | 年号用 `now.year`，不写死 |
| 备案号 | `.footer-icp` | 有则显示，没有则整行不渲染 |

## 三、链接列结构

用户在自己的 `settings.yaml` 里配置 footer 链接：

```yaml
# sites/<name>/settings.yaml
footer:
  variant: default
  links:
    - title: 产品
      links:
        - {label: 产品中心, url: /products/}
        - {label: 案例展示, url: /cases/}
    - title: 关于
      links:
        - {label: 关于我们, url: /about/}
        - {label: 联系我们, url: /contact/}
    - title: 法律
      links:
        - {label: 隐私政策, url: /privacy/}
        - {label: 使用条款, url: /terms/}
```

> 联系方式 / 社交图标等**内容**不属于页脚骨架，由 block 承载——主题从 block 数据读，不写死在 footer 模板里。

## 四、版权声明

```jinja2
<span>{{ settings.copyright | default('© ' + now.year | string + ' ' + settings.title + ' 版权所有') }}</span>
```

- 优先取 `settings.copyright`（用户自己写的完整版权文案）
- 没有则用默认格式：`© 2026 公司名 版权所有`
- `now.year` 是 Python `datetime.now().year`，永远当前年，不手动改

## 五、备案号

```jinja2
{% if settings.icp %}
<span class="footer-icp">{{ settings.icp }}</span>
{% endif %}
```

中国大陆站点需要 ICP 备案号（如 `粤ICP备xxxxxxxx号`），用户填了才显示。

## 六、变体

```yaml
# settings.footer
footer:
  variant: default    # → layouts/footer/default.html
```

```text
layouts/footer/
  default.html       四列链接 + 居中版权栏
  minimal.html       单行版权，无链接列
  three-col.html     三列链接 + 左侧 Logo + 右侧版权
```

每个变体是完全独立的 HTML 文件，结构可以完全不同——比如 `minimal.html` 只有一行版权，`default.html` 有完整的四列链接网格。

## 七、渲染上下文

| 变量 | 用途 |
| --- | --- |
| `settings` | `settings.footer`（含 `variant` / `links`）、`settings.copyright`、`settings.icp`、`settings.title` |
| `now` | Python `datetime.now()`，`now.year` 取当前年 |
| `t` | 如需翻译词（如"版权所有"），但不常用——版权文案用 `settings.copyright` |
| `lang` | 当前语言 |

## 八、为什么不是 block

和 header 同理，footer 和页面内容 block 有本质区别：

| | 内容 block | footer |
| --- | --- | --- |
| 出现位置 | 页面正文里，用户随意排序 | `_base.html` 固定位置（`</main>` 之下） |
| 出现次数 | 任意 | 每页恰好 1 个 |
| 作用范围 | 单页 | 全站每页相同 |
| 数据来源 | `page.modules[].data`（页面 YAML） | `settings.footer` + `settings.copyright` + `settings.icp` |

做成 block 意味着用户可以在编辑器里删掉 footer、拖到第一屏、一个页面加三个 footer——全是破坏性操作，builder 需要额外写防错逻辑。

**数据来源也不同**。block 的数据在模板自身（HTML 里的文字即默认值），footer 的数据在 `settings.yaml`：

| footer 零件 | 数据来源 | 能纯 data-\* 吗 |
| --- | --- | --- |
| 链接列 `{% for %}` | `settings.footer.links` | 不能，没有对应的 data-source |
| 版权 `now.year` | Python 运行时 | 不能，data-\* 没有表达式 |
| ICP `{% if settings.icp %}` | `settings.icp` | 不能，data-\* 没有条件语法 |
| 公司名 `settings.title` | `settings.title` | 不能，没有 `data-source="title"` |

链接列理论上可以加一个 `data-source="footer-links"` 保留源——但就这一个场景，为它专门加一条保留源不划算。模板用 Jinja2 的 `{% for %}` 循环，三行代码，直截了当。

## 九、关键规则

- **所有变体都用 `class="site-footer"`**——CSS 靠这个选择器统一给深色背景 / 灰色文字。
- **链接列用 `container` 包裹**——最大宽度和页面内容对齐。
- **`now.year` 不写死数字**——版权年始终为当前年。
- **ICP 备案号有才显示**——不提不渲染。
- **联系方式不放这里**——电话、邮箱、地址等业务内容由 block 承载，footer 模板只管骨架。
