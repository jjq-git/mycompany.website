# 媒体管理功能方案

## 背景

后台目前缺少统一的媒体文件管理入口。用户上传的图片、视频、文档等资源分散在公司信息、模块编辑、详情数据、富文本等表单里，无法集中浏览、预览、重命名、删除，也无法在操作前判断文件是否仍被页面引用。

本方案建议在左侧栏「网站设置」下新增「媒体管理」菜单，按站点集中管理已上传资源，并支持一种特殊资源类型：网页包。

网页包的参考目录为 `C:\Users\admin\Desktop\rimu_web000`，目录内包含 `index.html + main.js + main.wasm`。它不是“预览单个 `.wasm` 文件”，而是把一组静态 Web 构建产物作为一个目录保存，然后在 iframe 中打开其中的 `index.html`。浏览器会按原页面逻辑继续加载同目录下的 JS、WASM、图片、字体等资源。

## 目标

第一阶段目标是实现一个轻量但完整的媒体管理 MVP：

1. 在后台新增「媒体管理」入口。
2. 集中展示当前站点的图片、视频、文档、其他文件和网页包。
3. 支持上传、预览、下载、重命名、删除。
4. 支持网页包 zip 上传、解压和 iframe 预览。
5. 重命名或删除前检测 YAML 引用；只有未被引用的文件或网页包才允许操作。
6. 保证普通文件和网页包静态资源访问的路径安全。

## 必要性

媒体管理不是单纯的“文件列表页面”，而是后台内容管理能力的基础补齐。

当前系统已经有多个上传入口，但资源缺少统一资产视图，会带来几个实际问题：

1. 用户不知道某个站点已经上传过哪些文件，容易重复上传。
2. 文件被页面、模块或详情数据引用后，没有入口查看影响范围。
3. 删除或重命名文件时，可能导致页面裂图、视频失效、下载链接 404。
4. 多语言内容、模板预览和详情数据可能共同引用同一批资源，问题排查成本较高。
5. `rimu_web000` 这类网页包不能用普通图片/视频上传逻辑覆盖，需要按目录保存和预览。
6. 后续如果要做图库选择、资源复用、文件清理、容量统计、批量替换，也需要先有统一媒体入口。

因此建议先实现可管理、可预览、可防误删的基础版本，不把第一阶段扩展成复杂资产管理系统。

## 可行性

该方案整体可行，且可以在现有项目结构上平滑增加。

1. 现有站点资源已经集中在 `sites/<id>/assets/uploads/`，新增扫描、预览、重命名、删除接口不需要改变现有内容模型。
2. 网页包可以作为独立资源类型处理，保存到 `sites/<id>/assets/media-packages/<package_name>/`。
3. 后端不需要解析 WASM，只需要注册 `.wasm` MIME 并安全托管静态文件。
4. 当前内容主要存储在 YAML 中，引用检测可以先用字符串扫描实现。
5. 后台已有左侧菜单、fragment 面板加载、独立 CSS、模态框、上传接口等模式，可以复用现有实现风格。

主要风险是文件安全和引用完整性：

1. zip 解压必须防路径穿越，限制总大小和目录深度，并要求存在 `index.html`。
2. 网页包静态路由只能访问当前包目录内文件。
3. 重命名/删除不自动改 YAML；如果文件或网页包已被引用，直接阻止操作，避免造成页面资源断裂。
4. iframe 的 sandbox 需要谨慎设置；网页包如果要运行 JS/WASM，不能使用会阻断脚本执行的过严限制。

## 实施边界

第一阶段建议包含：

1. 媒体管理菜单与面板。
2. 图片、视频、文档、其他普通文件的列表、上传、预览、下载、重命名、删除。
3. 网页包 zip 上传、解压、列表展示和 iframe 预览。
4. 重命名/删除前的引用检测；只有引用数为 0 时才允许继续操作。
5. `.wasm` MIME 注册和网页包静态资源安全托管。

第一阶段暂不建议包含：

1. 自动级联更新 YAML 引用。
2. 批量删除、批量替换、批量压缩。
3. 跨站点共享媒体库。
4. 图片裁剪、转码、水印、视频转码。
5. 数据库级媒体索引或引用关系表。

## 文件规划

### 新建文件

| 文件 | 用途 |
| --- | --- |
| `app/templates/dashboard/panel_media.html` | 媒体管理面板片段，包含文件网格、分类标签、上传区、预览浮层、重命名模态框 |
| `app/templates/dashboard/media.html` | 媒体管理完整页面，继承 `base.html`，用于直接访问或刷新 |
| `app/templates/dashboard/media_package_viewer.html` | 网页包预览容器页，使用 iframe 加载已解压网页包的 `index.html` |
| `app/static/css/admin-media.css` | 媒体管理专用样式，沿用 `admin-seo.css` 的独立 CSS 模式 |

### 修改文件

| 文件 | 改动 |
| --- | --- |
| `app/core/site_storage.py` | 新增媒体文件扫描、路径校验、重命名、删除、引用检测相关函数 |
| `app/core/routes.py` | 新增媒体管理页面路由、API、网页包静态路由、上传辅助函数和 `.wasm` MIME 注册 |
| `app/templates/base.html` | 在「网站设置」子菜单中插入「媒体管理」导航项 |

## 数据与目录设计

普通上传文件沿用现有目录：

```text
sites/<site_id>/assets/uploads/
```

网页包使用新目录：

```text
sites/<site_id>/assets/media-packages/<package_name>/
```

一个网页包目录示例：

```text
sites/5/assets/media-packages/rimu_web000/
  index.html
  main.js
  main.wasm
  assets/
```

媒体分类建议：

| 分类 | 判断方式 | 说明 |
| --- | --- | --- |
| `image` | `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.svg` | 图片预览 |
| `video` | `.mp4`, `.webm`, `.ogg`, `.mov` | 视频播放器预览 |
| `document` | `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.txt` | iframe 或下载 |
| `package` | `assets/media-packages/<name>/index.html` | 网页包 iframe 预览 |
| `other` | 其他允许文件 | 元信息 + 下载 |

## 后端设计

### `site_storage.py`

新增 `MEDIA_CATEGORIES`，用于将扩展名或资源类型映射到 `image`、`video`、`package`、`document`、`other` 及中文标签。

新增 `list_media_files(site_id)`：

1. 扫描 `sites/<id>/assets/uploads/` 下所有常规文件，排除隐藏文件和目录。
2. 扫描 `sites/<id>/assets/media-packages/` 下包含 `index.html` 的一级目录。
3. 返回按名称排序的字典列表。
4. 每条记录包含 `name`、`size_bytes`、`size_display`、`mtime`、`category`、`ext`、`url`。
5. 普通文件 URL 为 `/assets/uploads/<name>`。
6. 网页包 URL 和入口 URL 为 `/media-packages/<package_name>/`。

新增 `get_media_file_path(site_id, filename)`：

1. 使用 `secure_filename` 或等价逻辑校验文件名。
2. 防止 `..`、绝对路径、空文件名、隐藏路径等危险输入。
3. 返回安全绝对路径，文件不存在时返回 404。

新增 `get_media_package_path(site_id, package_name)`：

1. 校验包名安全。
2. 返回 `assets/media-packages/<package_name>/` 的绝对路径。
3. 只允许访问包目录内文件，不能跳出该目录。

新增 `_find_media_references(site_id, filename)`：

1. 扫描站点所有 YAML，包括 `settings.yaml`、`pages/*.yaml`、`data/*.yaml`、`lang/*` 覆盖目录。
2. 普通文件搜索 `/assets/uploads/<filename>`。
3. 网页包搜索 `/media-packages/<package_name>/`。
4. 返回引用该文件或网页包的相对路径列表。

新增 `rename_media_file(site_id, old_name, new_name)`：

1. 校验新旧名称合法性。
2. 拒绝覆盖已有文件或目录。
3. 普通文件执行 `os.rename()`。
4. 网页包按整个目录重命名，即 `assets/media-packages/<old>` 到 `assets/media-packages/<new>`。
5. 重命名前必须先确认引用数为 0；如已被引用，后端拒绝重命名。
6. 不自动级联更新 YAML 引用。

新增 `delete_media_file(site_id, filename)`：

1. 校验目标路径。
2. 普通文件执行删除。
3. 网页包按整个包目录删除。
4. 删除前必须先确认引用数为 0；如已被引用，后端拒绝删除。

### `routes.py`

新增媒体管理页面：

```text
GET /media
```

行为：

1. 沿用 `_fragment=1` 模式。
2. fragment 请求渲染 `panel_media.html`。
3. 普通请求渲染 `media.html`。
4. 注入 `files` 列表到模板。

新增引用查询 API：

```text
GET /api/media/references?filename=xxx
```

返回：

```json
{
  "filename": "xxx.webp",
  "refs": ["pages/home.yaml"],
  "count": 1
}
```

新增重命名 API：

```text
POST /api/media/rename
```

接收 `old_name` 和 `new_name`。后端先执行引用检测：如果引用数大于 0，返回 `{ok: false, refs: [...], count: N}` 并拒绝重命名；如果引用数为 0，执行重命名并返回 `{ok, new_name, new_url}`。后端不修改 YAML。

新增删除 API：

```text
POST /api/media/delete
```

接收 `filename`。后端先执行引用检测：如果引用数大于 0，返回 `{ok: false, refs: [...], count: N}` 并拒绝删除；如果引用数为 0，删除文件或网页包目录并返回 `{ok}`。后端不修改 YAML。

新增上传 API：

```text
POST /api/media/upload
```

行为：

1. 图片和视频沿用现有 `_save_uploaded_media()`。
2. `.zip` 如果包含根目录或一级目录下的 `index.html`，按网页包走 `_save_media_package()`。
3. 其他允许类型走 `_save_any_file()`。
4. 返回 `{ok, name, url, category}`，网页包额外返回 `{entry_url}`。

新增网页包入口路由：

```text
GET /media-packages/<package_name>/
```

返回该网页包的 `index.html`。页面内部的 `main.js`、`main.wasm`、图片、字体等资源由浏览器按相对路径继续请求。

新增网页包静态资源路由：

```text
GET /media-packages/<package_name>/<path:filename>
```

只允许访问当前站点 `assets/media-packages/<package_name>/` 目录内文件。`.wasm` 使用 `application/wasm` MIME。

### 上传辅助函数

新增 `_save_any_file()`，用于保存图片/视频之外的允许文件类型，例如 PDF、TXT、ZIP 等。文件保存到 `assets/uploads/`，命名规则沿用现有上传逻辑。

新增 `_save_media_package()`，用于处理网页包 zip：

1. 只接受 `.zip`。
2. 解压到 `sites/<id>/assets/media-packages/<safe_package_name>/`。
3. 解压前校验 zip 内所有条目。
4. 拒绝 `../`、绝对路径、空文件名、过深目录、超大总大小。
5. 必须包含 `index.html`，否则拒绝作为网页包。
6. 保留包内相对目录结构。
7. 返回 `{name, entry_url}`。

### WASM MIME

在 `routes.py` 顶部注册：

```python
import mimetypes

mimetypes.add_type("application/wasm", ".wasm")
```

## 前端设计

### 面板布局

`panel_media.html` 建议结构：

```text
媒体管理
分类标签：全部 / 图片 / 视频 / 网页包 / 文档 / 其他
上传区：拖拽文件到此处或点击上传
文件网格：缩略图、名称、大小、类型、操作按钮
预览浮层：图片、视频、PDF、文本、网页包 iframe
重命名模态框：新名称、引用占用提示、确认按钮
```

卡片操作按钮：

1. 预览。
2. 重命名。
3. 下载。
4. 删除。

### 预览方式

| 类型 | 预览方式 |
| --- | --- |
| 图片 | `<img>` 灯箱 |
| 视频 | `<video controls>` |
| 网页包 | `<iframe src="/media-packages/<package_name>/">` |
| PDF | `<iframe>` |
| JS/CSS/TXT | `fetch()` 后放入 `<pre><code>` |
| 其他 | 元信息卡片 + 下载按钮 |

网页包预览必须由包内 `index.html` 自己加载 `main.js`、`main.wasm` 和其他资源，不在后台页面里手写 Emscripten `Module`，也不直接解析 `.wasm`。

### 核心交互

1. 点击分类标签，在客户端切换卡片显示。
2. 点击卡片或预览按钮，打开预览浮层。
3. 点击重命名，先调用 `GET /api/media/references`。
4. 如果没有引用，打开重命名模态框；如果已有引用，展示引用路径并禁止重命名。
5. 点击删除，先调用 `GET /api/media/references`；如果已有引用，展示引用路径并禁止删除。
6. 拖拽或点击上传，调用 `POST /api/media/upload`，成功后刷新列表或插入新卡片。
7. 下载使用原生 `<a href="file_url" download>`。

### JavaScript 组织

所有 JS 可先放在 `panel_media.html` 底部的单个 `<script>` 块中，风格与 `panel_company.html` 保持一致。主要函数：

1. `filterByCategory(cat)`：分类过滤。
2. `previewFile(filename, category)`：按类型选择预览方式。
3. `closePreview()`：关闭预览浮层。
4. `renameFile(oldName)`：打开重命名模态框。
5. `submitRename()`：提交重命名请求。
6. `deleteFile(filename)`：引用检测、未引用确认、删除。
7. `initUploadZone()`：拖拽上传绑定。
8. `initCardEvents()`：卡片事件委托。

### CSS

新增 `app/static/css/admin-media.css`：

1. 自包含，不混入模板主题 CSS。
2. 使用 `--media-*` 命名空间定义局部 CSS 变量。
3. 复用后台现有按钮、模态框、表单视觉语言。
4. 文件网格使用响应式布局：

```css
grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
```

## 侧边栏入口

在 `app/templates/base.html` 的「网站设置」子菜单中，SEO 检查项之后插入「媒体管理」：

```html
<a class="left-nav-item {% if active == 'media' %}active{% endif %}"
  href="{{ url_for('core.media') }}"
  data-panel="media"
  style="padding-left:32px"
  title="媒体管理">
  <!-- 文件图标 SVG -->
  媒体管理
</a>
```

点击后沿用现有 sidebar click handler，通过 `loadPanel(href + '?_fragment=1')` 加载面板片段。

## 引用影响处理

当前系统是单向路径引用：YAML 文件中保存的是 `/assets/uploads/xxx.webp` 或 `/media-packages/package_name/` 这类字符串，没有独立的反向索引。

因此第一阶段采用“前端检测 + 后端强校验 + 只允许操作未引用资源”的方案。

| 操作 | 前端行为 | 后端行为 |
| --- | --- | --- |
| 重命名 | 先查引用；若有引用，列出引用路径并禁用重命名；若无引用，允许提交 | 再次检测引用；有引用则拒绝；无引用才执行重命名 |
| 删除 | 先查引用；若有引用，列出引用路径并禁用删除；若无引用，允许确认删除 | 再次检测引用；有引用则拒绝；无引用才执行删除 |

只允许操作未引用资源的原因：

1. 可以从源头避免页面裂图、视频失效、下载链接 404。
2. 多个 YAML 文件之间做原子替换复杂，尤其涉及 `lang/*` 覆盖目录。
3. 字符串替换存在误匹配风险，误改用户内容比拒绝操作更难恢复。
4. 用户如果确实要删除或重命名被引用资源，应先到对应页面或数据中解除引用。

后续如果要升级，可以增加媒体引用索引或“替换文件但保持 URL 不变”的能力。

## 实现步骤

1. 在 `routes.py` 注册 `.wasm` MIME。
2. 在 `site_storage.py` 新增媒体扫描、路径校验、引用检测、重命名、删除函数。
3. 在 `routes.py` 新增 `_save_any_file()` 和 `_save_media_package()`。
4. 新增 `/media` 页面路由。
5. 新增 `/api/media/references`、`/api/media/upload`、`/api/media/rename`、`/api/media/delete`。
6. 新增 `/media-packages/<package_name>/` 和 `/media-packages/<package_name>/<path:filename>`。
7. 创建 `admin-media.css`。
8. 创建 `panel_media.html`。
9. 创建 `media.html`。
10. 创建 `media_package_viewer.html`，如确认无需单独容器页，可延后。
11. 修改 `base.html`，添加侧边栏入口。
12. 做集成测试。

## 验证方法

1. 启动 `python run.py`，登录后台并选择站点。
2. 点击左侧「媒体管理」，确认面板加载成功。
3. 确认普通上传文件和网页包能正确出现在列表。
4. 点击分类标签，确认过滤正常。
5. 点击图片文件，确认灯箱预览正常。
6. 点击视频文件，确认播放器预览正常。
7. 点击 PDF 或文本文件，确认预览或下载正常。
8. 上传普通文件，确认文件出现在网格中。
9. 上传包含 `index.html + main.js + main.wasm` 的网页包 zip，确认能解压为网页包。
10. 点击网页包预览，确认 iframe 能打开包内页面，且同目录 JS/WASM 能正常加载。
11. 对被引用文件执行重命名，确认会展示引用路径并拒绝操作。
12. 对被引用文件执行删除，确认会展示引用路径并拒绝操作。
13. 空 `uploads` 和空 `media-packages` 时，确认显示空状态。

## 后续扩展

第一阶段完成后，可以根据实际使用情况再考虑：

1. 在图片字段中接入“从媒体库选择”。
2. 增加文件替换功能，保持 URL 不变，降低引用断裂风险。
3. 增加未引用文件筛选。
4. 增加容量统计和文件大小排序。
5. 增加批量操作。
6. 建立媒体引用索引，替代 YAML 实时扫描。
