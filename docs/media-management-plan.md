# 媒体管理功能实现计划

## Context

后台目前缺少统一的媒体文件管理入口。用户上传的图片、视频等文件分散在各个编辑表单中，无法集中浏览、预览、重命名。现在需要在左侧栏「网站设置」下新增「媒体管理」菜单，提供站点所有上传文件的管理能力。

**触发场景**: 用户选中 sidebar 中的 `--color-surface` CSS 变量后提出此需求。参考目录 `C:\Users\admin\Desktop\rimu_web000`（含 index.html + main.js + main.wasm）说明需要支持「网页包」预览：它不是预览单个 `.wasm` 文件，而是把一组静态 Web 构建产物作为一个目录，在 iframe 中打开其中的 `index.html`，由浏览器按原页面逻辑加载同目录下的 JS/WASM/资源文件。

## 涉及文件清单

### 新建文件
| 文件 | 用途 |
|------|------|
| `app/templates/dashboard/panel_media.html` | 媒体管理面板片段（文件网格、分类标签、预览浮层、重命名模态框、上传区） |
| `app/templates/dashboard/media.html` | 完整页面（extends base.html，用于直接导航或刷新） |
| `app/templates/dashboard/media_package_viewer.html` | 网页包预览容器页（iframe 加载已解压网页包的 index.html） |
| `app/static/css/admin-media.css` | 功能专用样式（沿用 `admin-seo.css` 的独立 CSS + 自定义属性模式） |

### 修改文件
| 文件 | 改动 |
|------|------|
| `app/core/site_storage.py` | 新增 `list_media_files()` / `get_media_file_path()` / `rename_media_file()` / `delete_media_file()` |
| `app/core/routes.py` | 新增媒体管理路由/API + `_save_any_file()` / `_save_media_package()` 辅助函数 + `.wasm` MIME 注册 |
| `app/templates/base.html` | 在「网站设置」子菜单中插入「媒体管理」导航项 |

---

## 后端设计

### 1. site_storage.py 新增函数（文件末尾追加）

**常量 `MEDIA_CATEGORIES`**: 将扩展名/资源类型映射到分类（`image`/`video`/`package`/`document`/`other`）及中文标签。其中 `package` 表示可 iframe 预览的网页包目录，不是单个 `.wasm` 文件。

**`list_media_files(site_id)`**: 
- 扫描 `sites/<id>/assets/uploads/` 下所有常规文件（排除隐藏文件和目录）
- 同时扫描 `sites/<id>/assets/media-packages/` 下的网页包目录；每个包含 `index.html` 的一级目录作为一条「网页包」记录
- 返回按名称排序的字典列表，每条记录含：`name`, `size_bytes`, `size_display`, `mtime`（ISO 格式）, `category`, `ext`, `url`
- 普通上传文件的 `url` 为 `/assets/uploads/<name>`；网页包的 `url`/`entry_url` 为 `/media-packages/<package_name>/`

**`get_media_file_path(site_id, filename)`**:
- 用 `secure_filename` 校验文件名，防止路径穿越
- 返回安全绝对路径，文件不存在时 404

**`get_media_package_path(site_id, package_name)`**:
- 用安全包名校验，防止路径穿越
- 返回 `assets/media-packages/<package_name>/` 的绝对路径
- 只允许访问包目录内文件，不能跳出该目录

**`_find_media_references(site_id, filename)`**:
- 扫描站点所有 YAML（settings.yaml + pages/*.yaml + data/*.yaml + lang/* 覆盖），搜索 `/assets/uploads/<filename>` 路径字符串
- 返回引用该文件的所有相对路径列表（如 `['pages/home.yaml', 'data/products.yaml']`）
- 用于重命名/删除前的引影响评估

**`rename_media_file(site_id, old_name, new_name)`**:
- 校验新旧文件名合法性，拒绝覆盖已有文件
- `os.rename()` 执行重命名，返回新文件名
- **注意：不自动级联更新 YAML 引用**，路径断裂由用户负责（前端会先调用 `_find_media_references` 展示影响范围，用户确认后再执行）
- 网页包重命名按整个包目录处理，即 `assets/media-packages/<old>` → `assets/media-packages/<new>`，不重命名包内单个文件

**`delete_media_file(site_id, filename)`**:
- 校验后删除文件，返回 True/False
- **同上：不阻止删除被引用的文件**，由前端引用检测 + 用户二次确认来兜底
- 网页包删除按整个包目录处理，删除前展示引用该包入口 URL 的 YAML 列表

### 2. routes.py 新增路由

**`/media` — 媒体管理页面**
- 沿用 `_fragment=1` 模式：fragment 时渲染 `panel_media.html`，否则渲染 `media.html`
- 注入 `files` 列表到模板（分类过滤在客户端完成）

**`GET /api/media/references` — 查询文件引用**
- 接收 `?filename=xxx`，调用 `_find_media_references()` 返回 `{filename, refs: [...], count: N}`
- 前端在重命名/删除前调用此接口，展示影响范围

**`POST /api/media/rename` — 重命名**
- 接收 `old_name` + `new_name`，返回 JSON `{ok, new_name, new_url}`
- 不自动级联更新 YAML，返回 `broken_refs` 列表供前端展示警告

**`POST /api/media/delete` — 删除**
- 接收 `filename`，返回 JSON `{ok}` 或错误
- 不阻止删除被引用的文件，由前端引用检测 + 用户二次确认兜底

**`POST /api/media/upload` — 上传**
- 接收 `file`
- 图片/视频走现有 `_save_uploaded_media()`
- `.zip` 若包含根目录或一级目录下的 `index.html`，按网页包走 `_save_media_package()`，解压到 `assets/media-packages/`
- 其他允许类型走 `_save_any_file()`
- 返回 JSON `{ok, name, url, category}`；网页包额外返回 `{entry_url}`

**`/media-packages/<package_name>/` — 网页包预览入口**
- 以 iframe 打开已解压网页包中的 `index.html`
- 网页包目录示例：`sites/<id>/assets/media-packages/rimu_web000/index.html`
- 页面内部的 `main.js`、`main.wasm`、图片、字体等资源由浏览器按相对路径继续请求
- 后端只负责安全地托管该包目录下的静态文件，不手写 Emscripten `Module`，也不直接解析 `.wasm`

**`/media-packages/<package_name>/<path:filename>` — 网页包静态资源**
- 只允许访问当前站点 `assets/media-packages/<package_name>/` 目录内文件
- 必须防路径穿越：拒绝 `..`、绝对路径、空包名、隐藏危险路径
- `.wasm` 使用 `application/wasm` MIME，其余文件按 Flask/send_file 的 MIME 推断返回

### 3. `_save_any_file()` 辅助函数

放在 `_save_uploaded_media()` 之后（约第 203 行）。处理图片/视频之外的允许文件类型（pdf, zip, txt 等），直接原样保存到 `assets/uploads/`，沿用相同的时间戳+随机 hex 命名规则。

### 4. `_save_media_package()` 辅助函数

处理类似 `rimu_web000.zip` 的网页包上传：
- 只接受 `.zip`
- 解压到 `sites/<id>/assets/media-packages/<safe_package_name>/`
- 解压前校验 zip 内每个条目，拒绝 `../`、绝对路径、空文件名、过深目录、超大总大小
- 必须包含 `index.html`，否则拒绝作为网页包
- 保留包内相对目录结构，让 `index.html` 可以继续加载 `main.js`、`main.wasm` 等资源
- 返回 `{name, entry_url}`，其中 `entry_url` 指向 `/media-packages/<package_name>/`

### 5. `.wasm` MIME 注册

在 routes.py 顶部 import 区添加:
```python
import mimetypes
mimetypes.add_type('application/wasm', '.wasm')
```

---

## 前端设计

### panel_media.html 布局

```
┌─────────────────────────────────────────┐
│ 媒体管理                                 │  ← .fw-semibold（提取为面板标题）
├─────────────────────────────────────────┤
│ [全部] [图片 N] [视频 N] [网页文件 N] ... │  ← 分类标签栏
├─────────────────────────────────────────┤
│  拖拽文件到此处或点击上传                  │  ← 上传放置区
├─────────────────────────────────────────┤
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│ │ 缩略图│ │ 缩略图│ │ 图标 │ │ 图标 │   │  ← CSS Grid 文件卡片
│ │ a.jpg│ │ b.mp4│ │rimu.zip│ │ d.pdf│ │
│ │245KB │ │5.1MB │ │1.9MB │ │89KB  │   │
│ │[图片]│ │[视频]│ │[网页]│ │[文档]│   │
│ │◎◎◎◎│ │◎◎◎◎│ │◎◎◎◎│ │◎◎◎◎│   │  ← 预览/重命名/下载/删除按钮
│ └──────┘ └──────┘ └──────┘ └──────┘   │
└─────────────────────────────────────────┘
```

### 核心交互

1. **分类过滤**: 点击标签按钮，纯客户端 `display:none/block` 切换卡片显隐
2. **文件预览**: 点击卡片或预览按钮 → 打开固定定位浮层
   - 图片：`<img>` 灯箱（复用 checkerboard 背景 + 点击关闭）
   - 视频：`<video controls>` 
   - 网页包：`<iframe>` 指向 `/media-packages/<package_name>/`，由包内 `index.html` 自己加载 JS/WASM/资源
   - JS/CSS/TXT：`<pre><code>` 通过 `fetch()` 加载文本
   - PDF：`<iframe>` 直接加载
   - 其他：元信息卡片 + 下载按钮
3. **重命名**: 点击重命名 → 先调用 `GET /api/media/references` 查询引用 → 若被引用则在模态框中展示「⚠ 此文件被 N 个页面引用：[列表]，重命名后这些页面将显示异常，需手动更新」→ 用户确认后再 POST `/api/media/rename`
4. **删除**: 点击删除 → 先调用 `GET /api/media/references` 查询引用 → 若被引用则二次确认「此文件被 N 个页面引用，删除后不可恢复」→ 用户确认后再 POST `/api/media/delete` → 移除卡片 DOM
5. **上传**: 拖拽/点击 → POST `/api/media/upload` → 成功后插入新卡片到网格。若上传的是网页包 zip，则后端解压并以「网页包」类型显示
6. **下载**: `<a href="file_url" download>` 原生下载

### JavaScript 组织

所有 JS 以单个内联 `<script>` 块写在 `panel_media.html` 底部，命名函数风格，与 `panel_company.html` 模式一致。主要内容：
- `filterByCategory(cat)` — 分类过滤
- `previewFile(filename, category)` — 按类型选择预览方式
- `closePreview()` — 关闭浮层
- `renameFile(oldName)` — 打开重命名模态框
- `submitRename()` — 提交重命名请求
- `deleteFile(filename)` — 确认 + 删除
- `initUploadZone()` — 拖拽上传绑定
- `initCardEvents()` — 卡片事件委托

### media.html 完整页面

```html
{% extends "base.html" %}
{% block title %}媒体管理{% endblock %}
{% block content %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/admin-media.css') }}">
{% include 'dashboard/panel_media.html' %}
{% endblock %}
```

### media_package_viewer.html

独立 HTML 页面（不继承 base.html），作为网页包预览容器：
- 接收后端传入的 `entry_url`
- 用 `<iframe>` 加载 `/media-packages/<package_name>/`
- iframe 可按需要添加 `sandbox`，但要评估目标网页包是否需要脚本、同源资源、表单等能力
- 不在此模板里定义 Emscripten `Module`，不手动加载 `.wasm`
- 页面包内的运行逻辑完全由包自己的 `index.html`、`main.js`、`main.wasm` 决定

### admin-media.css

- 约 150-200 行，自包含，CSS 自定义属性命名空间 `--media-*`
- 遵循 `admin-seo.css` 的独立文件 + 自定义属性模式
- 响应式网格：`grid-template-columns: repeat(auto-fill, minmax(180px, 1fr))`

---

## 侧边栏修改（base.html）

在「网站设置」子菜单的 SEO 检查项之后（第 319 行 `</a>` 之后），插入：

```html
<a class="left-nav-item {% if active == 'media' %}active{% endif %}"
  href="{{ url_for('core.media') }}" data-panel="media" style="padding-left:32px" title="媒体管理">
  <!-- 文件图标 SVG -->
  媒体管理
</a>
```

点击后由现有的 sidebar click handler 自动处理：`loadPanel(href + '?_fragment=1')` 加载面板片段。

---

## 重命名/删除对页面引用的影响处理

当前系统是**单向路径引用**：YAML 文件里只存 `/assets/uploads/xxx.webp` 这样的字符串，没有反向索引。重命名或删除文件后，引用该文件的页面会静默断裂（显示裂图/404）。

### 采用方案：前端检测 + 用户确认（不自动级联）

| 操作 | 前端行为 | 后端行为 |
|------|----------|----------|
| 重命名 | 先调 `GET /api/media/references` 查引用 → 若有引用，模态框中标红列出引用路径 → 用户确认后提交 | 只执行 `os.rename()`，不改动 YAML |
| 删除 | 同上，二次确认弹窗展示引用列表 → 用户强制确认后删除 | 只执行 `os.remove()`，不改动 YAML |

**不做自动级联更新的理由**：
- 跨多个 YAML 文件的原子替换实现复杂（涉及 lang 覆盖目录）
- 万一替换出错（部分匹配等），破坏用户内容比断裂图片更严重
- 符合「简单 > 优化」原则：小企业站文件数量少，手动更新成本低

**后端新增**：`_find_media_references(site_id, filename)` 扫描所有 YAML 中是否包含 `/assets/uploads/<filename>` 路径。

---

## 实现步骤

1. **注册 WASM MIME** — routes.py 顶部加 `mimetypes.add_type`
2. **新增 site_storage.py 函数** — `_find_media_references()` + `list_media_files()` 等 5 个函数
3. **routes.py 加 `_save_any_file()` + 6 条路由**（多了 `/api/media/references`）
4. **创建 `admin-media.css`**
5. **创建 `media_package_viewer.html`**
6. **创建 `panel_media.html`**
7. **创建 `media.html`**
8. **修改 `base.html`** 侧边栏导航
9. **集成测试** — 启动 dev server，验证各项功能

## 验证方法

1. 启动 `python run.py`，登录后台，选择站点
2. 点击左侧「媒体管理」，确认面板加载、文件列表正确显示
3. 点击各分类标签，确认过滤正常
4. 点击图片文件 → 灯箱预览，点击空白关闭
5. 点击视频文件 → 视频播放器预览
6. 点击重命名按钮 → 修改文件名 → 确认卡片更新
7. 点击删除按钮 → 确认后卡片消失
8. 拖拽文件到上传区 → 文件出现在网格中
9. 上传或放入包含 `index.html + main.js + main.wasm` 的网页包 zip → 点击预览 → iframe 能打开包内页面，页面能正常加载同目录 JS/WASM
10. 空 uploads 目录 → 显示「暂无媒体文件」占位提示
