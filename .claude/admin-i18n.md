# 店主后台 UI 国际化方案

## 背景

店主后台所有面板（属性面板、页头设置、菜单编辑等）的界面文字目前硬编码为中文。需要支持多语言切换，让使用不同语言的店主都能操作后台。

## 核心设计决策

### 1. 后台 UI 语言列表与网站语言版本一致

不另建后台语言列表。店主后台可切换的语言直接读取 `Site.enabled_languages`，与"属性面板 → 语言设置 → 网站语言版本"是同一套数据。

```
模板 meta.yaml 定义 language 列表（唯一来源）
  │
  ├─→ 网站前台多语言版本（panel_header 勾选启用）
  └─→ 店主后台 UI 语言切换器（同一套列表）
```

### 2. 浏览器语言仅作兜底

语言优先级：

1. 店主手动选择的语言（存 `user.ui_lang` 字段）
2. 浏览器 `Accept-Language` / `navigator.language`
3. 模板 `default_language`（如 zh-CN）

店主可随时在后台切换语言，切换后刷新页面即时生效。

### 3. 自定义 JSON 翻译文件，不用 Flask-Babel

不引入 Flask-Babel 依赖。用自定义 JSON 文件存翻译，零新增依赖，符合项目"依赖能少则少"原则。

## 文件结构

```
app/
  translations/
    admin_zh-CN.json    ← 简体中文（兜底语言，其他文件缺失的 key 从这里回退）
    admin_zh-TW.json    ← 繁體中文
    admin_en.json       ← English
  core/
    i18n.py             ← 加载翻译、注册 Jinja2 全局函数、注入 JS 变量
```

模型变更（SQLite 新增字段）：

```
User 表新增: ui_lang  VARCHAR(10)  -- 店主手动选择的 UI 语言，NULL=未选择
```

## 翻译文件格式

按"页面 → 区块 → key"两级组织，key 名即语义：

```json
{
  "panel_header": {
    "section_title": "网站头部",
    "layout_tab": "头部布局",
    "content_tab": "内容",
    "style_tab": "样式",
    "lang_settings": "语言设置",
    "lang_switcher_toggle": "在前台显示语言切换按钮",
    "lang_versions": "网站语言版本",
    "button_style": "按钮样式",
    "social_links": "社交链接",
    "show_social_icons": "显示社交链接图标",
    "outer_style": "外层样式",
    "inner_style": "内层样式",
    "padding": "内边距",
    "margin": "外边距",
    "save": "保存"
  },
  "panel_page_edit": {
    "edit_language": "编辑语言",
    "add_module": "+ 添加模块",
    "available_modules": "可用模块",
    "selected_modules": "已选模块（点击箭头排序 | 点击配置）",
    "move_up": "上移",
    "move_down": "下移",
    "delete": "删除",
    "content_tab": "内容",
    "style_tab": "样式",
    "outer_style": "外层样式",
    "inner_style": "内层样式",
    "padding": "内边距",
    "margin": "外边距",
    "color_scheme": "配色"
  }
}
```

注意：只翻译**管理后台 UI 界面文字**（label、按钮、提示、tab 名称）。网站**前台内容**（产品名、文章正文）已按语言分文件存储（`pages/home_en.yaml`），不在此范围。

## 数据流

### 请求生命周期

```
request → before_request:
  1. 读取当前语言:
     - 优先 session['admin_ui_lang']
     - 否则 user.ui_lang（DB 字段）
     - 否则 Accept-Language 请求头
     - 否则 default_language
  2. 校验该语言在 Site.enabled_languages 中（否则回退到 default_language）
  3. 加载 app/translations/admin_{lang}.json 为 dict
  4. 存入 g.admin_lang, g.admin_i18n

render_template:
  - Jinja2 全局 _t(key) → g.admin_i18n 取值，key 不存在则 fallback 到中文 JSON

JS:
  - base.html 注入 <script>window._i18n = {...}; window._adminLang = 'zh-CN';</script>
  - admin_modules.js 用 _t(key) 替代硬编码中文
```

### 语言切换流程

```
店主点击后台右上角语言切换下拉
  → POST /admin/set-language { lang: 'en' }
  → 更新 user.ui_lang = 'en'（登录用户持久化）
  → session['admin_ui_lang'] = 'en'（当前会话即时生效）
  → 刷新当前页面，所有标签切换为目标语言
```

## 模板接入

```html
<!-- 之前 -->
<span class="fw-semibold">网站头部</span>
<span class="small text-muted mt-2 mb-1">内边距</span>

<!-- 之后 -->
<span class="fw-semibold">{{ _t('panel_header.section_title') }}</span>
<span class="small text-muted mt-2 mb-1">{{ _t('panel_page_edit.padding') }}</span>
```

## JS 接入（admin_modules.js）

```javascript
// 全局 _t 函数（base.html 注入 window._i18n 后可用）
const _t = (key) => window._i18n?.[key] ?? key;

// label 生成时
// 之前: '<label>标题</label>'
// 之后: '<label>' + _t('common.title') + '</label>'
```

## 翻译文件缺失处理

- 当前语言文件缺失某个 key → fallback 到 `admin_zh-CN.json` 的同名 key
- 连 zh-CN 也没有 → 直接显示 key 名本身（开发期醒目，方便补翻译）
- 整个语言文件不存在（如未来加 ja）→ 全部 fallback 到 zh-CN

## 实施步骤

| 步骤 | 内容 | 影响范围 |
|---|---|---|
| 1 | 新建 `app/translations/admin_zh-CN.json`，从现有模板逐文件提取中文 | 纯新增 |
| 2 | 新建 `app/core/i18n.py`，实现加载、fallback、Jinja2 全局函数 | 新增 ~40 行 |
| 3 | User 模型新增 `ui_lang` 字段，执行 migration | models.py +1 行 |
| 4 | `base.html` 注入 `window._i18n` + 语言切换下拉 UI | base.html |
| 5 | 添加 `/admin/set-language` 路由 | routes.py +10 行 |
| 6 | 逐面板替换硬编码中文为 `{{ _t('...') }}`（35 个模板文件） | 量大但机械 |
| 7 | `admin_modules.js` 替换硬编码中文为 `_t('...')`（~344 处） | 量大但机械 |
| 8 | 创建 `admin_zh-TW.json` + `admin_en.json` 翻译文件 | 按需 |
