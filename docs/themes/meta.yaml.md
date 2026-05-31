# meta.yaml：主题概要

`themes/<name>/meta.yaml` 只记录一套主题的**概要信息**——这套主题"是什么"（身份、分类、版本、作者…）。

**具体内容一律不放这里**。菜单、配色、页面、数据这些用户真正在调的东西，全部在 settings，见 [settings.yaml.md](settings.yaml.md)。

|            | meta.yaml                     | settings.yaml         |
| ---------- | ----------------------------- | --------------------- |
| 属于       | 主题（所有用户共享）          | 单个用户的站          |
| 管什么     | 主题概要（身份 / 分类 / 版本）| 用户填 / 改的具体内容 |
| 改了影响谁 | 所有用该主题的新站            | 只这一个站            |

## 完整示例

```yaml
theme_name: Tech Product - Dark
industry: [tech-product, hardware]      # 适合哪些行业（数组）
languages: [en, zh]                     # 本主题提供哪些语言的整套 seed（数组）
description:                            # 多语言：每套主题独有，内联中 / 英两版
  zh: 适合硬件创业 / 模块化产品 / 极客向项目。深色主题，支持视频 hero、产品矩阵、功能亮点、博客。
  en: For hardware startups, modular products and geek projects. Dark theme with video hero, product matrix, feature highlights and blog.
version: 0.1.0
tags: [深色, 科技感]                     # 风格标签（数组，取自受控词表）
level: 2                               # 等级，越高越高级；高级会员才能用
author: 平台设计组
is_public: true
created: 2026-05-31                     # 主题创建日期
updated: 2026-05-31                     # 主题最后更新日期
```

> 缩略图不在 meta 配置：按约定放 `preview/cover.webp`（固定路径），后台自动读取（目录结构见 [README.md](README.md)）。

## 一、概要字段

主题"是什么"。扫描主题时这些被读进数据库 `Theme` 表，供后台展示 / 筛选 / 选主题。缺省时取「缺省」列的值。

| 字段          | 含义                                                                  | 缺省    |
| ------------- | --------------------------------------------------------------------- | ------- |
| `theme_name`  | 后台展示的主题名（**只用英文**）                                     | 目录名  |
| `industry`    | 行业归类（**数组**，可挂多个：tech-product / manufacturing…），按行业筛选 | `[]`    |
| `languages`   | 主题提供整套 seed 的语言（**数组**），决定哪些语言的用户可选用此主题建站（见五） | `[]`    |
| `description` | 主题简介，帮用户选主题。**多语言**，内联中 / 英两版（见三）           | 空      |
| `version`     | 语义版本号。建站时记进站点；build 比对不一致打警告（不阻塞）          | `1.0.0` |
| `tags`        | 风格标签（**数组**，受控词表：深色 / 极简…），按风格筛选（见二）       | `[]`    |
| `level`       | 等级（数值，越高越高级）。按等级筛选；高级会员才能用高 level 主题（见四） | `1`     |
| `author`      | 主题作者（平台方 / 外包）                                             | 空      |
| `is_public`   | 是否对用户可见（`false` = 仅内部 / 草稿）                             | `true`  |
| `created`     | 主题**创建**日期（手写）                                              | 空      |
| `updated`     | 主题**最后更新**日期（手写）                                          | 空      |

> 主题的唯一标识是**目录名 slug**（如 `tech-product`），不在 meta.yaml 里重复写；数据库 `Theme.name` 即它。`theme_name` 是展示名，二者不同。

> `created` / `updated` 是**主题制作 / 修改**日期，手写在 meta；数据库另有扫描时自动记的**登记时间** `created_at` / `updated_at`，二者不是一回事。

## 二、行业与风格标签（industry / tags）

主题靠两个维度被分类、被筛选，**都是数组**（一套主题可挂多个）：

| 维度       | 含义             | 例                         |
| ---------- | ---------------- | -------------------------- |
| `industry` | 适合哪些**行业** | `[tech-product, hardware]` |
| `tags`     | 是什么**风格**   | `[深色, 科技感]`           |

用户选主题：**先按行业找候选 → 再按风格挑中意的那套**。主题做得多而精，用户选中后基本不用改样式，直接填内容。

### tags 是受控词表（强制）

`tags` 只能从平台预定义的**合法标签清单**里选，不能自由写——避免出现「深色」「暗色」这类同义标签把筛选搞乱。清单**逐步补全**：现阶段先列常用标签，新风格在做新主题时先加进清单、再用。

起步标签：

| 维度 | 标签                           |
| ---- | ------------------------------ |
| 明暗 | 深色、浅色                     |
| 气质 | 极简、大胆、雅致、科技感、温暖 |

`tags` 的多语言显示走 **gettext**（和 description 不同，见下节对比）：原值用中文（`深色`），后台按界面语言翻成英文（`Dark`），走 Flask-Babel，和后台界面多语言同一套机制（详见 [../admin-i18n.md](../admin-i18n.md)）。meta.yaml 里只写中文标签，不写翻译。

## 三、description 多语言（内联 zh/en）

`description` 是每套主题**独有的一段话**、作者写的内容，不在主题间复用。所以它的多语言**内联**在 meta 里，直接写中 / 英两版：

```yaml
description:
  zh: 适合硬件创业 / 模块化产品 / 极客向项目…
  en: For hardware startups, modular products…
```

后台按界面语言取 `description.zh` 或 `description.en`；缺哪种回退另一种。

### 为什么 description 和 tags 多语言方式不同

| 字段          | 多语言方式       | 为什么                                   |
| ------------- | ---------------- | ---------------------------------------- |
| `tags`        | gettext（`.po`） | 固定受控词表，全平台复用                 |
| `description` | 内联 zh/en       | 每套主题独有的长文本，作者一处写两版即可 |

固定且复用的词 → 进 gettext 词表；每主题独有的内容 → 内联。

## 四、等级与会员（level）

`level` 是数值，**越高越高级**。两个用途：

- 后台按 `level` 筛选主题
- **权限**：高级会员才能用高 `level` 的主题；建站选主题时校验「会员等级 ≥ 主题 level」

> 具体分级（level 1 / 2 / 3 各对应什么会员等级）**待定**，先记下「主题分等级、按会员权限放开」这个规则。

## 五、languages 与按语言分整套的 seed

`languages` 声明这套主题**提供哪些语言的整套 seed**（如 `[en, zh]`）。seed 内容按语言分整套放在 `themes/<name>/i18n/<lang>/`，每个 `<lang>` 目录是一整套（含 `settings.yaml` + `pages/` + `data/`），互相独立、不共享。`layouts/` `blocks/` `static/` 是语言无关的皮肤，不进 `i18n/`。

用户先选后台界面语言（如 `en`），再选主题；只有 `languages` 含该语言的主题才可选用。建站时系统把 `themes/<name>/i18n/en/` 这一整套拷到站点，`en` 成为该站的**源语言**（用户用它填真实内容），之后逐篇 AI 翻译到目标语言（详见 [README.md](README.md)）。

## 六、字段流向

```text
meta.yaml
├── theme_name / description / author / created / updated / is_public
│        └──► 扫描写入 Theme 表 ──► 后台展示主题
│
├── industry / tags / level
│        └──► 后台筛选（行业 / 风格 / 等级）；level 还管会员权限；tags 显示走 gettext
│
├── languages
│        └──► 决定哪些语言的用户可选用此主题；建站时拷对应 i18n/<lang>/ 整套 seed
│
├── version
│        ├──► 建站时记进站点
│        └──► 每次 build 比对，不一致打警告
```

## 七、约束

- `meta.yaml` 缺失时，该目录**不会**被登记为主题（扫描直接跳过）。
- 字段值都是给人读 / 给后台展示的纯数据，不写逻辑。
- `tags` 只能取自合法标签清单；非法标签在扫描时应被拒绝或警告。
- `level` 缺省为最低级（人人可用）；高 level 主题需会员权限才能选用。
- 改概要字段后需**重新扫描主题**才同步进数据库。
