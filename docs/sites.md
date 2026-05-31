# 站点内容模型

数据分两层：

- **数据库** —— 平台级元数据（账号、站点 / 主题登记、登录 token），共 4 张表。本文不展开，见 [database.md](database.md)。
- **磁盘 `sites/<name>/`** —— 一个网站的全部内容（设置 / 页面 / 数据集 / 翻译 / 资源），纯 YAML + 文件，是内容的唯一真相源。**本文讲它。**

> 网站正文内容**不进数据库**，全部存磁盘 YAML。

## 一、磁盘：一个网站的文件布局

```text
sites/<name>/
  settings.yaml        站点设置，源语言（主题色 / 菜单 / 语言 / 页眉页脚 / 社交…）
  pages/               独立页面，源语言（index、about、contact…）
    home.yaml
    about.yaml
  data/                数据集，源语言（同构条目的列表）
    products.yaml
    posts.yaml
  lang/<目标语言>/      AI 翻译产出（pages/ data/ settings.yaml）
  assets/              上传的图片（WebP）与文件
  output/              构建产物（静态站，导出即打包它；非源）
```

根目录的 `settings.yaml` / `pages/` / `data/` 是**源语言**内容 —— 用户建站时选的、用来填真实内容的语言（`settings.default_language` 记录它），不固定为某种语言。源语言内容由建站时把所选主题 `themes/<name>/i18n/<源语言>/` 整套拷到 `sites/<name>/` 而来，再由用户用母语填真实内容。`lang/<目标语言>/` 是把源语言逐篇 AI 翻译成目标语言的产出；其下同名文件覆盖源语言，缺失字段回退源语言。

#### 生成的页面与 URL（导出的静态站）

| 内容 | 生成路径 | 来源 |
| --- | --- | --- |
| 首页 | `/index.html` | `pages/home` |
| 独立页 | `/<页面>.html`，如 `/contact_us.html` | `pages/<页面>` |
| 产品列表 | `/products.html` | 数据集 `products` |
| 产品详情 | `/products/<slug>.html`，如 `/products/abc.html` | `products` 每条（按 `slug`） |
| 主题资源 | `/asset/`（css / js） | 主题 `static/` |
| 用户资源 | 可自建目录：`image/`、`datasheet/` 等 | 上传的图片 / 图纸 / 视频 |

> 资源目录由用户自定（`image/`、`datasheet/`…），构建时原样带进静态站。



### settings.yaml

站点级配置（站名 / 配色 / 菜单 / 语言 / 页眉页脚 / 社交）。字段与示例见 [themes/settings.yaml.md](themes/settings.yaml.md)。

### pages/（页面）

每个页面 = 一个**模块（block）数组**，布局由用户增删 / 排序模块决定。示例：

```yaml
# pages/home.yaml
modules:
  - {type: hero_banner, data: {title: ..., image: ...}}
  - {type: feature_grid, data: {items: [...]}}
  - {type: product_grid, data: {target: products, limit: 6}}
```

模块的字段与渲染见 [themes/blocks/](themes/blocks/)。

### data/（数据集）

每个数据集是一个 `data/<name>.yaml`，内容为**条目列表**，每条有唯一 `id`。布局固定，用户只填内容。示例：

```yaml
# data/products.yaml
- id: 1
  slug: silent-booth          # 详情页 URL 用
  title: 静音仓
  category: 静音仓             # 可选：分类字段
  cover: /assets/uploads/booth.webp
  summary: ...
  body: ...
- id: 2
  slug: dry-ice-machine
  title: 干冰机
  ...
```

一个站点有哪些数据集，由所选主题 `i18n/<lang>/data/` 提供的整套 seed 决定（如产品、博客、案例）。

### 内容模型：页面 / 数据集 / 分类

| 类型 | 存哪 | 是什么 | 例子 |
| --- | --- | --- | --- |
| 页面 Page | `pages/*.yaml` | 结构性独立页，布局 = 模块数组 | index、关于我们、联系 |
| 数据集 Dataset | `data/<name>.yaml` | 同构条目的列表，布局固定只填内容 | 产品、博客文章、案例 |
| 分类 category | 数据集条目的**可选字段** | 给条目分组（不是独立分类系统） | 产品分「静音仓 / 干冰机」 |

- 不做 tag（标签）—— 小企业站规模下属过度设计。
- 分类就是条目上的一个 `category` 字符串字段，需要时主题按它分组渲染；不引入 WordPress 那套 taxonomy 表。

## 二、约束

- 网站内容只描述网站本身（设置、页面、数据集、翻译、资源）。
- 改字段结构不用动数据库（YAML 弹性）；改的是主题 + 对应数据。
- `sites/<name>/` 整目录可打包；导出的静态站是其中的 `output/`。
