# translations.yaml：主题 UI 文案

`translations.yaml` 是主题自带的**界面文案翻译**——导航词、按钮字、提示语等主题模板里写死的固定文字。一个文件含所有语言，渲染时按当前 `lang` 取值。

> 存于主题根目录 `themes/<name>/translations.yaml`，语言无关（不进 `i18n/<lang>/`）。

## 一、和 settings 的分工

| | `translations.yaml` | `settings.*` |
| --- | --- | --- |
| 管什么 | 主题写死的界面词 | 用户填的内容 |
| 谁写 | 主题作者 | 用户 |
| 例子 | "首页"、"菜单"、"了解更多" | 站名、标语、产品名 |
| 多语言方式 | 一个文件含所有语言 | `lang/<code>/` 文件覆盖 |
| 模板用法 | `t.nav.home` | `settings.title` |

`t.*` 是主题皮肤的一部分——用户不改这些词，换了主题界面词就变了。`settings.*` 是用户的业务内容——和主题无关。

## 二、文件结构

```yaml
# themes/<name>/translations.yaml
nav:
  home:
    zh: 首页
    en: Home
    ja: ホーム
  products:
    zh: 产品
    en: Products
    ja: 製品
  about:
    zh: 关于我们
    en: About
    ja: 会社概要
  contact:
    zh: 联系我们
    en: Contact
    ja: お問い合わせ

actions:
  menu:
    zh: 菜单
    en: Menu
    ja: メニュー
  read_more:
    zh: 了解更多
    en: Read More
    ja: 続きを読む
  back:
    zh: 返回
    en: Back
    ja: 戻る
  prev:
    zh: 上一页
    en: Previous
    ja: 前へ
  next:
    zh: 下一页
    en: Next
    ja: 次へ

product:
  specs:
    zh: 技术参数
    en: Specifications
    ja: 仕様

footer:
  copyright:
    zh: 版权所有
    en: All Rights Reserved
    ja: 無断転載禁止
```

一个顶层 key 对应一个语义分组，每个分组下每个 key 对应一个多语言字典（`zh` / `en` / …）。

## 三、模板里怎么用

builder 把 `translations.yaml` 解析为嵌套字典，以当前 `lang` 取值，注入为 `t`：

```jinja2
<a href="/">{{ t.nav.home }}</a>
<button aria-label="{{ t.actions.menu }}"></button>
<span>{{ t.footer.copyright }}</span>
```

`lang = "zh"` 时 `t.nav.home` 取 `"首页"`；`lang = "en"` 时取 `"Home"`。缺当前语言时回退到文件里的第一种语言。

## 四、和 settings 菜单 label 的区别

导航菜单有两层文案，容易混：

| | 来源 | 举例 | 翻译方式 |
| --- | --- | --- | --- |
| 菜单项 `label` | `settings.menu`（用户填） | "产品中心"、"智能门锁" | `lang/<code>/settings.yaml` 覆盖（AI 翻译） |
| 界面词 | `translations.yaml`（主题写死） | "菜单"、"首页"、"了解更多" | 一个文件含所有语言（主题作者手写） |

模板渲染导航时：用户填的菜单 label 从 `item.label` 取、用 `lang/` 覆盖翻译；汉堡按钮上的"菜单"字从 `t.actions.menu` 取、用 translations.yaml 翻译。两种来源、两套机制。

## 五、主题支持哪些语言

`translations.yaml` 里写了哪些语言，主题就支持哪些语言的**界面显示**。这和 `meta.languages`（声明主题提供哪些语言的整套 seed）是独立的两件事：

| | `translations.yaml` | `meta.languages` |
| --- | --- | --- |
| 管什么 | 界面词翻译覆盖范围 | 整套 seed 提供范围 |
| 有 `ja` | `t.*` 能取到日语 UI 词 | 主题提供日文版默认内容（settings / pages / data） |
| 缺 `ja` | `t.*` 回退到第一种语言 | 日文用户不能选用此主题建站 |

通常两者语言的列表一致，但不是强制。

## 六、添加新语言

1. 在 `translations.yaml` 每个 key 下加新语言字段
2. 在 `meta.languages` 里加该语言
3. 在 `i18n/<lang>/` 下放整套 seed（settings.yaml + pages/ + data/）

三步做完，该语言用户即可选用此主题建站，界面词 + 默认内容都就位。

## 七、关键规则

- **一个文件含所有语言**——和 pages/data 的多语言方式不同，不拆分到 `lang/`。
- **缺语言回退第一种**——不会因为缺某个词的某个语言翻译就崩。
- **只放主题皮肤词，不放用户内容**——"菜单"放这里，"产品中心"放 settings.menu。
- **模板里用 `t.xxx.yyy` 取值**——不写死文字，方便多语言。
- **每套主题独立**——换主题 = 换整套 `t.*`，界面词可能完全不同。
