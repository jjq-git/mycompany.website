# settings.yaml：站点设置

`settings.yaml` 是一个站点的**基本设置**——配色、字体、菜单、语言、页眉页脚版式，以及全站自定义代码。

> **settings 只放全站级字段**——配色 / 菜单 / 语言 / 页眉页脚版式 / 全站代码。其中 `title` / `slogan` / `menu` 标签虽是要翻译的文字，但属"全站级身份"，仍放这里（翻译走 `lang/`，机制见末节「多语言覆盖」）。**逐条业务内容**（联系方式、备案号、公司介绍、产品…）才由 **block** 承载，不进 settings。

## 两份，同一套结构

| 哪份         | 位置                                      | 作用                                                          |
| ------------ | ----------------------------------------- | ------------------------------------------------------------- |
| **主题默认** | `themes/<name>/i18n/<lang>/settings.yaml` | 出厂默认（菜单 / 配色 / 页眉页脚…），建站时按用户选的语言整套拷给用户 |
| **用户站点** | `sites/<name>/settings.yaml`              | 用户改自己这份（源语言）；目标语言用 `lang/<code>/settings.yaml` 承载 AI 翻译产出 |

主题的 settings 提供 `menu` / `theme` / `header` / `footer` 等**默认值**——用户改的是自己那份，主题不变。

主题按 `meta.languages` 声明的每种语言，在 `i18n/<lang>/` 下各放**一整套完整的 settings**（含 `menu` / `title` / `slogan`，以及语言无关的配色 `theme`）。配色等语言无关字段在各语言的 settings 里重复出现，但值相同——这是刻意的简单选择（不区分共享，整套按语言拷）。建站时系统把用户所选语言对应的那套 `i18n/<lang>/settings.yaml` 拷成站点的源语言 settings。

> 和 [meta.yaml.md](meta.yaml.md) 的分工：meta 是主题**概要**（身份 / 分类 / 版本），settings 是站点的**基本设置**。

## 完整示例

```yaml
title: 德恩基                  # 站点显示名
slogan: 专业静音仓制造商
favicon: /assets/favicon.webp
logo: /assets/logo.webp
theme:                        # 主题色令牌（覆盖主题自带的默认）
  color-primary: "#067a7a"
  color-secondary: "#f97316"
  font-sans: "Inter, 'Noto Sans SC', sans-serif"
languages: [zh-CN, en]        # 启用的语言（须在主题支持范围内）
default_language: zh-CN        # 源语言 = 用户建站时选的语言（此处示例为 zh-CN）
menu:                         # 导航（项结构见下）
  - {label: 首页, type: home}
  - {label: 产品, type: list, target: products}
  - {label: 关于我们, type: page, target: about}
header: {variant: ...}        # 选用的页眉变体
footer: {variant: ...}        # 选用的页脚变体
custom_css: ""                # 全站自定义 CSS（注入每页末尾）
head_html: ""                 # 注入 <head> 的代码（百度统计等）
```

> **示例语言无关**：上面拿 zh-CN 当源语言只是举例。**源语言 = 你建站时选的语言**——选英文，系统就拷主题的 `i18n/en/settings.yaml`，整份都是英文（`default_language: en`，title / slogan / 菜单全英文），你全程用英文编辑；中文若启用反而成 `lang/zh-CN/` 的翻译目标。前提是主题在 `meta.languages` 里声明了该语言、并提供了对应的 `i18n/<lang>/`（见 [meta.yaml.md](meta.yaml.md)）。

**同一家公司**若建站时选英文作源语言（而非中文），它的源语言 settings 就长这样（`favicon` / `logo` / `theme` / `header` / `footer` 等语言无关字段同上，略）：

```yaml
title: DENGTEC                # 站点显示名（英文源语言）
slogan: Silent Booth Maker
languages: [en, zh-CN]        # 启用语言（顺序不决定源语言）
default_language: en          # 源语言 = en
menu:
  - {label: Home, type: home}
  - {label: Products, type: list, target: products}
  - {label: About, type: page, target: about}
```

## 字段

| 字段                | 含义                                                       |
| ------------------- | ---------------------------------------------------------- |
| `title`             | 站点显示名                                                 |
| `slogan`            | 标语                                                       |
| `favicon`           | 站点图标路径                                               |
| `logo`              | logo 图片路径                                              |
| `theme`             | 主题色令牌，覆盖主题自带的默认                             |
| `languages`         | 启用的语言（须在主题支持范围内）                           |
| `default_language`  | 源语言 = 用户建站时选的语言（不固定某种语言）             |
| `menu`              | 导航菜单（项结构见下）                                     |
| `header` / `footer` | 选用的页眉 / 页脚变体                                      |
| `custom_css`        | 全站自定义 CSS，注入每页末尾（[publish.md](../publish.md) 口子 3） |
| `head_html`         | 注入 `<head>` 的代码，百度统计 / 客服等（[publish.md](../publish.md) 口子 2） |

## 菜单项结构

`menu` 是导航项数组，每项 `{label, type, target?}`：

| `type`  | 含义           | `target`               |
| ------- | -------------- | ---------------------- |
| `home`  | 首页           | 无                     |
| `list`  | 数据集列表页   | 数据集名（如 products）|
| `page`  | 独立页         | 页面名（如 about）     |

> 译文（`lang/<code>/settings.yaml`）里 `menu` 只写 `label`，`type` / `target` 不重复——按位置继承源语言（见下节）。

## 多语言覆盖

settings 的多语言**按语言分文件**（和 pages / data 同一套机制，不用内联 `{zh, en}`）：源语言用根目录 `settings.yaml`，目标语言用 `lang/<code>/settings.yaml` 覆盖，缺字段回退源语言。源语言 = 用户建站时选的语言（不固定中文），`lang/<目标语言>/` 是 AI 从源语言翻译过来的产出。

`title` / `slogan` / `menu` 等要翻译的字段，在各语言文件里各写一份（下例以 zh-CN 作源语言、en 作目标语言，仅为示例，实际取决于用户所选语言）：

```yaml
# sites/<name>/settings.yaml —— 源语言（此例为 zh-CN）
title: 德恩基
slogan: 专业静音仓制造商
menu:
  - {label: 首页, type: home}
  - {label: 产品, type: list, target: products}
```

```yaml
# sites/<name>/lang/en/settings.yaml —— 目标语言（en，AI 翻译产出）
title: DENGTEC
slogan: Silent Booth Maker
menu:                          # 只给 label；type/target 按位置继承源语言，不重复
  - {label: Home}
  - {label: Products}
```

- 只覆盖要变的字段，没写的回退源语言（`favicon` / `logo` / 配色 `theme` 通常各语言共用，不必在 `lang/` 里重复）。
- **字体是例外**：`theme.font-*` 若用了 CJK 专用字体（简中 `Noto Sans SC` 与日文 `Noto Sans JP` 字形不同），多语言站点要在对应 `lang/` 里按语言覆盖，否则字形会错。
- `menu` **按位置合并**：结构（`type` / `target`）只在源语言存一份，`lang/` 里每项只给 `label`，builder 按顺序套上源语言结构。源语言以后增删菜单项也不会与译文漂移——译文缺的项回退显示源语言 `label`。
- 整套多语言策略（每语言独立文件 / 目录）见 [../i18n.md](../i18n.md)。
