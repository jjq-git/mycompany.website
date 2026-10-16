# 页面模块列表搜索与分页（module_list）

`module_list` 用于“一个页面里有很多相同图文模块”的页面，例如：

- `/functions/`：每个功能是一块图文介绍。
- `/modules/`：每个模块是一块图文介绍。
- 服务清单、工具目录、能力目录等。

它解决的是当前页面内的搜索和分页，不会新建后台数据集，也不会生成新的分页 URL。

## 什么时候使用

适合使用 `module_list`：

- 页面内容由多个 `highlight_card` 这类模块组成。
- 每个模块就是一个列表项。
- 只需要在当前页面搜索、翻页。
- `section_title` 这类标题模块不应该被搜索或分页隐藏。

不适合使用 `module_list`：

- 产品、博客、案例来自 `data/*.yaml` 数据集。
- 页面使用 `data_grid` 自动展示数据集条目。
- 一个 `featured_picks` 模块内部有很多卡片，并希望分页每张内部卡片。

简单判断：

| 内容来源 | 使用 |
| --- | --- |
| 页面 YAML 的 `modules` 数组 | `module_list` |
| 数据集 YAML 的 `data/*.yaml` | `data_grid` |

## YAML 配置

在页面 YAML 顶层加入 `module_list`：

```yaml
title: Functions

module_list:
  enabled: true
  search: true
  pagination: true
  page_size: 6
  target_types:
    - highlight_card
  search_placeholder: Search functions...
  empty_text: No matching items.
  results_label: results
  prev_label: Previous
  next_label: Next

modules:
  - type: section_title
    order: 1
    data:
      title: Functions

  - type: highlight_card
    order: 2
    data:
      title: Resistor Decoder
      desc: Decode resistor color bands.
```

中文页面可以这样写：

```yaml
module_list:
  enabled: true
  search: true
  pagination: true
  page_size: 6
  target_types:
    - highlight_card
  search_placeholder: 搜索功能...
  empty_text: 没有匹配的内容。
  results_label: 个结果
  prev_label: 上一页
  next_label: 下一页
```

## 字段说明

| 字段 | 说明 |
| --- | --- |
| `enabled` | 是否启用页面模块列表功能。只有 `true` 才生效。 |
| `search` | 是否显示搜索框。 |
| `pagination` | 是否显示分页。 |
| `page_size` | 每页显示多少个模块。 |
| `target_types` | 哪些模块类型参与搜索和分页。常用 `highlight_card`。 |
| `search_placeholder` | 搜索框占位文字。 |
| `empty_text` | 搜索无结果时显示的文字。 |
| `results_label` | 结果数后面的文字，例如 `results` 或 `个结果`。 |
| `prev_label` | 上一页按钮文字。 |
| `next_label` | 下一页按钮文字。 |

## 编辑内容时要注意

- `section_title` 通常不要放进 `target_types`，否则搜索和分页会把页面标题一起隐藏。
- 如果一个条目就是一个 `highlight_card`，就在 `target_types` 中写 `highlight_card`。
- 如果页面还有其他条目模块，也可以加入：

```yaml
target_types:
  - highlight_card
  - text_content
```

- 搜索会匹配模块里能看到的文字，包括标题、标签、描述、列表项和按钮文字。
- 搜索后会自动回到第 1 页。
- 没有 JavaScript 时，页面会显示全部模块，不分页，内容仍然完整。

## 推荐页面结构

功能目录页推荐：

```yaml
modules:
  - type: section_title
    order: 1
    data:
      title: Functions
      subtitle: Choose a tool to get started.

  - type: highlight_card
    order: 2
    data:
      title: Resistor Decoder
      desc: Decode resistor color bands.

  - type: highlight_card
    order: 3
    data:
      title: Base Converter
      desc: Convert values between number bases.
```

模块目录页推荐：

```yaml
module_list:
  enabled: true
  search: true
  pagination: true
  page_size: 6
  target_types:
    - highlight_card
  search_placeholder: Search modules...
  empty_text: No matching modules.
  results_label: results
  prev_label: Previous
  next_label: Next
```

## 和 data_grid 的区别

`data_grid` 是数据集模块，适合产品、文章、案例这类结构化内容。编辑人员在数据集中增删条目，页面自动展示。

`module_list` 是页面模块能力，适合已经由多个页面模块组成的目录页。编辑人员还是照常在页面里增删模块，只是页面前端会自动给这些模块加搜索和分页。
