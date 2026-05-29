# 多语言与 AI 翻译

> 本文是《开发指南》的第十一章。返回总目录见 [README.md](README.md)。

---

## 多语言 + AI 翻译（Phase 2）

> 翻译的 AI 执行端是 [DeepSeek AI 助手](AI助手.md)，店主通过助手完成翻译交互。本节描述翻译的引擎逻辑（三层策略、Hash 缓存、增量翻译）。

Phase 1 MVP 先做单语言闭环。Phase 2 引入多语言，**店主只需维护母语内容，翻译由系统自动完成**。

### 翻译流程：三层策略
```
店主填完母语内容 → 点击「翻译为英文」
        │
        ▼
┌──────────────────────────────────────────────┐
│  第一层：词汇表（Glossary）—— 店主说了算       │
│                                              │
│  glossary.yaml 中指定的翻译直接采用，          │
│  跳过 AI。例：                                │
│    "智能门锁": "Smart Door Lock"              │
│    "德恩基电子": "Dengtech Electronics"       │
│                                              │
│  用途：公司名、产品名、专业术语等店主想         │
│  精确控制的翻译                               │
└──────────────┬───────────────────────────────┘
               │ 词汇表未覆盖的文本
               ▼
┌──────────────────────────────────────────────┐
│  第二层：人工覆盖（Override）                  │
│                                              │
│  店主在后台逐条手动修改 AI 翻译结果。          │
│  覆盖后的值记录到 translations/<lang>.yaml，  │
│  标记 overridden: true，下次不会被子集化刷新。 │
└──────────────┬───────────────────────────────┘
               │ 其余文本
               ▼
┌──────────────────────────────────────────────┐
│  第三层：AI 自动翻译                          │
│                                              │
│  遍历所有 data-type="text"/"textarea"/        │
│  "richtext" 的字段值，调用 DeepSeek API 翻译。 │
│                                              │
│  上下文注入：告诉 AI 这是 XX 公司（行业：XX）  │
│  的网站内容，保持语气一致。                    │
└──────────────────────────────────────────────┘
```

### 数据存储
翻译结果按语言分文件存储，与源内容分开：

```text
sites/<site_id>/
├── settings.yaml              # 源语言（中文）菜单、Header、Footer 配置
├── pages/                     # 源语言（中文）页面内容
│   └── home.yaml
├── data/                      # 源语言（中文）数据集
│   └── products.yaml
├── translations/              # 翻译缓存（按语言分文件）
│   ├── en.yaml                # 所有翻译到英文的键值对
│   └── zh-Hant.yaml           # 所有翻译到繁体中文的键值对
├── glossary.yaml              # 词汇表（店主指定的固定翻译）
└── assets/                    # 图片等资源（语言无关）
```

`translations/<lang>.yaml` 是扁平的键值映射，key 为源文本的 hash，value 为译文：

```yaml
# sites/<id>/translations/en.yaml
# 格式：<XXHash64(源文本)>: <译文>
# 例：XXHash64("用技术驱动未来") → "3a7b2c..."
3a7b2c1d4e5f: "Driving the Future with Technology"
6b8c3d2e1f0a: "Smart Door Lock Pro"
# ...
```

Hash 的好处：源文本改了 → hash 变了 → 旧翻译不匹配 → 自动标记为"待重译"，不会错误复用。

### Hash 缓存：只翻译改过的内容
每次翻译任务启动前，系统对比源文本 hash 与已有翻译 key：

| 场景 | 判断逻辑 | 行为 |
| --- | --- | --- |
| 源文本未变 | hash 已存在于 translations 文件 | **跳过**，直接用已有译文 |
| 源文本新增 | hash 不存在 | 调 AI 翻译 |
| 源文本修改 | 旧 hash 消失，新 hash 出现 | 旧翻译保留（可手动清理），新文本调 AI 翻译 |
| 源文本删除 | hash 不再出现在源内容中 | 保留在翻译文件中（不影响构建，构建时只取需要的 key） |

翻译任务记录到 `translation_jobs` 表（见 [数据库设计.md](数据库设计.md)），包含输入字符数、token 消耗、预估费用。

### 可翻译内容全景
访客切换语言时，以下所有内容同步切换：

```text
┌─────────────────────────────────────────────────────────┐
│  Header                                                 │
│  ├── Logo alt 文本（公司名）                              │
│  ├── 导航菜单标签（含所有层级）                            │
│  ├── CTA 按钮文字                                        │
│  └── 语言切换按钮的选项名                                │
├─────────────────────────────────────────────────────────┤
│  页面内容（每个页面的模块数据）                            │
│  ├── Hero：标题、副标题、按钮文字                         │
│  ├── Features：每条特性的标题、描述                       │
│  ├── About：公司简介正文                                  │
│  ├── CTA Band：标题、按钮文字                             │
│  └── … 所有 data-type="text" / "textarea" / "richtext"    │
├─────────────────────────────────────────────────────────┤
│  数据集内容                                              │
│  ├── 产品：名称、描述、参数表                             │
│  ├── 文章：标题、摘要、正文                               │
│  └── 案例：标题、描述                                    │
├─────────────────────────────────────────────────────────┤
│  Footer                                                 │
│  ├── 链接栏标题（"产品"、"关于"等）                       │
│  ├── 链接文字                                            │
│  ├── 社交图标 alt 文本                                   │
│  └── 版权声明文字                                        │
└─────────────────────────────────────────────────────────┘
```

**不需要翻译的内容**：图片（无文字）、视频、嵌入地图、URL、CSS 变量、data-name 等属性名。

### 访客端语言切换
访客看到的语言切换按钮（Header 中），交互流程：

```text
访客当前在 /en/products/smart-lock.html
        │
        │ 点击语言切换按钮 → 选择 "中文"
        ▼
浏览器跳转到 /zh/products/smart-lock.html
        │
        │ （如果该页面在中文版不存在，fallback 到 /zh/ 首页）
        ▼
访客看到同一产品的中文页面，继续浏览
```

切换语言时**保持当前页面路径**（`/en/products/xxx` → `/zh/products/xxx`），而不是跳回首页。这依赖：
- 所有语言共享同一套 slug（产品 slug、文章 slug 是语言无关的）
- 构建时每种语言独立生成目录，但路径结构一致

### 根路径语言选择：以浏览器设置的语言为准
访客打开网站根路径（如 `company-a.com/`）时，系统读取浏览器请求头中的 `Accept-Language`，**自动匹配到对应的语言版本**：

> 例：浏览器首选语言设为英文 → 打开 `company-a.com` → 自动跳转到 `company-a.com/en/`，看到英文版。

```text
company-a.com/           ← 根路径
    │
    ├── 读取请求头 Accept-Language 的首选语言
    │   ├── zh / zh-CN           → 302 跳转到 /zh/          （简体中文版）
    │   ├── zh-Hant / zh-TW / zh-HK → 302 跳转到 /zh-Hant/   （繁体中文版）
    │   ├── en / en-*            → 302 跳转到 /en/           （英文版）
    │   └── 其他语言 / 无法判断   → 显示语言选择页，让访客手动选
    │
    ├── /zh/              简体中文整站
    ├── /zh-Hant/         繁体中文整站
    └── /en/              英文整站
```

**不能纯 JS 跳转**——LLM 爬虫（GPTBot、ClaudeBot）不执行 JS。根路径必须用服务端 `Accept-Language` 检测 + `<hreflang>` 标签 + `<meta http-equiv="refresh">` 兜底。

访客也可以在任意页面通过 Header 的语言切换按钮手动切换语言，手动切换后记录到 Cookie，后续访问优先用 Cookie 值（覆盖浏览器设置）。

### 发布输出
每种语言生成**自包含的完整静态目录**：

```text
company-a.com/
├── index.html              ← 语言选择 + 跳转
├── zh/                     ← 简体中文整站
│   ├── index.html
│   ├── about.html
│   ├── products/
│   │   ├── index.html
│   │   └── smart-lock.html
│   ├── css/
│   ├── fonts/              ← 子集化后的简体中文字体
│   └── images/
├── zh-Hant/                ← 繁体中文整站
│   ├── index.html
│   ├── about.html
│   ├── products/
│   │   ├── index.html
│   │   └── smart-lock.html
│   ├── css/                ← 同一份 CSS（CSS 无语言差异）
│   ├── fonts/              ← 子集化后的繁体中文字体
│   └── images/             ← 同一份图片（复制，不共享）
├── en/                     ← 英文整站
│   ├── index.html
│   ├── about.html
│   ├── products/
│   │   ├── index.html
│   │   └── smart-lock.html
│   ├── css/                ← 同一份 CSS（CSS 无语言差异）
│   ├── fonts/              ← 子集化后的英文字体（无中文字符，更小）
│   └── images/             ← 同一份图片（复制，不共享）
├── sitemap.xml             ← 含所有语言所有 URL + hreflang
└── robots.txt
```

**核心原则：每个语言目录是自包含的整站。** 单语言导出 = 复制一个文件夹就能跑。不区分共享资源，简单 > 优化。

### 构建时的翻译注入
构建器（`builder.py`）渲染每种语言时：

```text
for lang in site.enabled_languages:
    1. 加载 translations/<lang>.yaml → 翻译键值对
    2. 遍历所有页面 .yaml：
       对每个 text/textarea/richtext 字段值 → 查 hash → 替换为译文
    3. 遍历所有数据集 .yaml：
       同上逻辑替换每个条目的文本字段
    4. 替换 settings.yaml 中的菜单 label、Header/Footer 文本
    5. Jinja2 渲染 → 写入 output/<lang>/
    6. 为当前语言做字体子集化（扫描 <lang>/ 下所有 HTML 用到的字符）
    7. 复制图片等资源到 <lang>/images/
```

Jinja2 模板不变，**翻译在数据层面完成后再交给 Jinja2 渲染**。模板作者不需要为多语言做任何额外工作。
