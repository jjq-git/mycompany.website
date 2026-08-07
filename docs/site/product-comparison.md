# 产品参数对比页

产品参数对比是独立页面模块，不是 `data_grid` 的布局变体。原产品卡片列表、产品详情页和数据文件保持不变。

## 菜单与数据源

列表菜单的 `target` 表示页面路径，新增的可选 `dataset` 表示内容数据源。旧菜单省略 `dataset` 时仍按 `dataset = target` 处理。

```yaml
- type: list
  label: 产品中心
  target: products

- type: list
  label: 产品参数对比
  target: product-comparison
  dataset: products
  preset: product_comparison
  generate_details: false
```

后台菜单中的“产品参数对比页”预设会自动创建第二种配置。保存菜单后，系统在 `pages/product-comparison.yaml` 中补充一个 `product_comparison` 模块，但不会复制 `products` 数据或修改原产品页。

## 参数结构

详情模板中的 `detail_specs` 可以定义稳定的分组键和参数字段：

```yaml
- type: detail_specs
  data:
    key: basic
    title: 基本参数
    fields:
    - key: manufacturer
      label: 厂商
      unit: ''
      compare: true
```

产品保存时沿用 `detail_specs`，参数键、名称、单位和值保存在同一个结构中。详情页和对比页优先使用稳定的分组键匹配数据；分组键缺失或无法匹配时保留原有的位置回退，避免既有站点因模板组件排序变化而失效。

模板中的 `source_field` 只负责兼容产品根级的旧格式字段 `specs`、`parameters` 和 `attributes`。存在分组 `detail_specs` 时不会使用该选项；兼容读取不会迁移、删除或改写历史数据。

## 页面模块

`dengtec` 和 `claude` 都提供 `product_comparison` block。两个主题共享以下行为：

- 最多同时比较 2–6 个产品；
- 从 URL 的 `compare=id1,id2` 恢复组合；
- 添加、移除和调整产品顺序；
- 搜索参数及隐藏相同项；
- 固定产品表头和参数名称列；
- 保留紧凑的页面 H1 与说明，避免为视觉效果占用过多首屏空间；
- 参数分类与表格保持一体布局；分类导航和产品表头滚动后固定在站点导航下方；
- 超宽表格在页面底部滚动条不可见时提供同步的浮动横向滚动条；
- 参数分组标题固定在参数列，横向滚动时保持可见；
- 产品少于展示槽位数时自动补齐空占位列，默认保持 5 列的稳定表格结构；占位列只影响排版，计数始终使用真实产品总数；
- 移动端分类导航切换为横向吸顶分类条；
- 移动、移除、详情、询价、隐藏、重置和复制等操作使用带提示的图标按钮；
- 移动端横向滚动；
- 复制当前对比链接；
- 复用产品详情页主按钮作为询价入口。

模块只在页面实际使用时加载 `product-comparison.js`。静态构建不依赖后台 API，所需候选产品和参数会随页面 HTML 一起生成。

## 内容编辑与预览

产品数据编辑器额外提供型号、价格、价格说明、参与对比和对比排序。数据集满足以下任一条件时，新建和编辑表单都会显示“对比参数”：使用菜单的产品对比预设、任一语言页面包含指向该数据集的 `product_comparison` 模块，或详情模板参数字段显式配置 `compare: true`。详情模板配置了参数字段后，新产品表单自动显示相应参数行。

产品保存并取得稳定 ID 后，编辑器显示“在对比页预览”，并使用 `?compare=<产品ID>` 打开对比页面。未保存的 `id=0` 草稿不注入对比页。
