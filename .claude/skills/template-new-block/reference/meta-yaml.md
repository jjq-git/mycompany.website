# meta.yaml 速查

## 字段属性

| 属性 | 必需 | 说明 |
|------|------|------|
| `key` | 是 | 字段标识, template.html 中 `md.get('key')` 取值 |
| `label` | 是 | 后台显示标签 |
| `type` | 是 | 字段类型 |
| `group` | 推荐 | 后台分组, 同名 group 归到一组显示 |
| `default` | **必填** | 默认值(字符串), 必须与模板 CSS 实际兜底值一致 |
| `placeholder` | 推荐 | 占位提示, 应注明"留空=CSS 默认值" |
| `options` | select 必填 | `[{value, label}]` |
| `item_label` | list 推荐 | 列表项显示标签 |
| `item_fields` | list 必填 | 子字段定义(用 `key`, 不是 `name`) |

## 字段类型

| type | HTML 控件 | 备注 |
|------|----------|------|
| `text` | `<input type="text">` | |
| `textarea` | `<textarea>` | |
| `image` | 文件上传 + 文本框 | |
| `url` | `<input type="url">` | |
| `richtext` | 文本域 | |
| `select` | `<select>` | 需配 `options` |
| `switch` | 复选框 | |
| `color` | `<input type="color">` | |
| `list` | 动态增删子项 | 需配 `item_fields` |
| `number` | `<input type="number">` | |
| `icon` | 图标下拉选择 | |

## 推荐 group 分组

| group | 用途 | 典型字段 |
|-------|------|---------|
| 内容 | 核心内容 | title, subtitle, desc, body, image |
| 外层样式 | 尺寸和背景 | section_bg, outer_width, inner_width |
| 外层外边距 | margin | margin_top/right/bottom/left |
| 内层边距 | padding | padding_top/right/bottom/left |
| 配色 | 颜色 | title_color, desc_color, btn_bg, btn_color |
| 字体样式 | 字号 | title_size, body_size, title_font_size |

### default 字段填写规则（硬约束 ⚠️）

**`default` 必须填写模板 CSS 中该属性的实际兜底值**, 不能随意留空。 原因:

1. 新建站点/新加模块时, 属性面板通过 `d[f.key] || f.default || ''` 渲染初始值
2. 如果 `default: ""`, 面板显示为空, 用户不知道"现在的实际效果是什么"
3. 模板的 CSS 文件(main.css)定义了视觉兜底, meta.yaml 的 default 必须与之同步

**填写方法**:

1. 打开模板的 CSS 文件(如 `site_templates/<name>/static/css/main.css`)
2. 找到该 block 对应的 CSS 规则, 提取属性值
3. 将 CSS 值写入 meta.yaml 的 `default` 字段

**常见 CSS 默认值速查**(以 dengtec 模板为例):

| CSS 规则 | 属性 | meta.yaml default |
|----------|------|-------------------|
| `.section { padding-top: var(--spacing-md) }` | 外层上内边距 | `"1rem"` |
| `.section { padding-bottom: var(--spacing-md) }` | 外层下内边距 | `"1rem"` |
| `.hero-banner { height: 77vh }` | Banner 高度 | `"77vh"` |
| `.container { max-width: var(--container-max) }` | 内容区宽度(header) | `"1440px"` |
| `background: transparent` (无 CSS 规则) | 背景色 | `""` (空=透明) |
| `padding: 0` (无 CSS 规则) | 内边距为 0 | `""` (空=0, 避免冗余 inline style) |

**例外**: 值为 `0`、`none`、`transparent` 的字段可保持 `default: ""`, 避免生成冗余的 inline style。 此时 `placeholder` 应明确说明默认值(如"留空=透明")。

## 完整示例 (highlight_card)

```yaml
name: 图文模块
category: content
icon: highlight_card.svg
description: 通用图文介绍模块，支持左右布局切换
fields:
  - key: title
    label: 标题
    type: text
    group: 内容
    default: ""

  - key: desc
    label: 描述
    type: textarea
    group: 内容
    default: ""

  - key: image
    label: 图片
    type: image
    group: 内容

  - key: section_bg
    label: 外层背景色
    type: color
    group: 外层样式
    default: ""
    placeholder: 如 #f5f7fa（留空=透明）

  - key: outer_width
    label: 外层宽度
    type: text
    group: 外层样式
    default: ""
    placeholder: 如 1200px（留空使用全局宽度）

  - key: features              # list 类型:子项列表
    label: 功能点列表
    type: list
    group: 特性列表
    item_label: 特性
    item_fields:               # 注意是 item_fields 不是 fields
      - key: text
        label: 文本
        type: text

variants:
  - key: default
    label: 图左文右
  - key: right
    label: 图右文左
```

## 最小示例

```yaml
name: 我的模块
category: content
icon: my_block.svg
description: 一句话描述
fields:
  - key: title
    label: 标题
    type: text
    group: 内容
    default: ""
variants:
  - key: default
    label: 默认样式
```
