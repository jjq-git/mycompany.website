# CLAUDE.md

本文件是 Claude 在本项目工作时的指导。所有未来的代码生成、文档修改、架构决策都应遵循下面的原则。

## 交流规范

- **始终用中文回答**：所有对话、解释、建议、代码审查意见均使用中文

## 代码规范

- **代码必须带注释**：关键逻辑、设计意图、边界条件必须用中文注释说明——不只是"做了什么"，而是"为什么这么做"

## 工作流程

- **CLAUDE.md 每条规则都是硬约束**：开始任何操作前先扫一遍相关规则。如果某条规则没被遵守，说明执行有漏洞，事后要在对应规则下加具体化的操作条款，防止同类再犯
- **工具调用标签必须带 `antml:` 前缀，禁止漏写**：每个工具调用的外层标签必须是 `antml:function_calls`、`antml:invoke`、`antml:parameter`，逐字带 `antml:` 命名空间前缀。漏掉前缀（写成 `invoke` / `parameter`）会导致调用无法解析、整轮作废、用户误以为"卡住"。这是曾反复发生的致命低级错误。发出每个工具调用前，先自检三层标签前缀是否齐全，确认后再发。一旦发现漏写，立即用正确格式重发，不解释、不重复道歉
- **先搜索后修改**：收到任务后先用 Grep 搜所有相关引用，列出完整文件清单，确认没有遗漏再动手。不要改一步看一步
- **任何工具失败或结果异常，立刻停手分析，不准重试原方案**：失败不是"再试一次"的信号，是"方案有问题"的信号。先搞清楚为什么失败，再决定下一步用什么，不允许换参数 / 换转义 / 换正则再赌一把
- **3 次工具调用搞不定一个简单任务 → 强制复盘**：如果一个排版 / 删除 / 简单替换用了 3 次以上工具调用还没完成，必须停下来问自己：任务到底有多简单？当前方案是不是走偏了？有没有更直接的方式一步到位？
- **Edit 失败一次 → 立刻写 Python 脚本**：Edit 工具只要匹配失败一次，不准换参数重试。直接写 Python 脚本按行号+中文关键字做精确处理，一轮过。这条没有例外
- **模板修改范围约束**：涉及 `site_templates/` 的修改，默认只改 `claude` 和 `dengtec` 两套模板。`airbnb`、`apple`、`notion` 等其他模板不动，除非用户明确指出要改哪套。这条同样适用于新增 block、修改 CSS/JS、调整种子数据等所有模板层操作
- **后台 schema 表单改动必须先查全链路**：改 data-* block 字段时，先同时确认 `template.html`、`meta.yaml`、`app/templates/dashboard/panel_page_edit.html`、`app/static/js/admin_modules.js`、`block_renderer.py` 五处职责。右侧面板以 `template.html` 解析出的 schema 为主，`meta.yaml` 只补类型、label、options、`show_if` 等元信息；不要把 `meta.fields` 整体塞进内容表单，只有被 `show_if` 依赖但不在 schema 里的控制字段（如 `media_type`）可以额外注入。新增/已保存、桌面/平板/手机三条路径必须一起验证。
- **富文本编辑器（RTE）只有一处定义**：`richEditorHtml()` 的唯一定义在 `app/static/js/admin_modules.js`。`panel_page_edit.html` 和 `panel_data_list.html` 都加载此 JS 后直接使用，不应在任何模板中重复定义同名函数。`page_home.html` 是独立体系（不加载 `admin_modules.js`，用 `onmousedown` 事件），暂不纳入统一。改 RTE 只改 `admin_modules.js` 即可生效于所有后台编辑面板。
- **getMergedSchema 有两个独立版本，禁止合并**：`admin_modules.js` 和 `panel_page_edit.html` 各有一套 `getMergedSchema`（前者用 `schemaFieldToFormField` 转换，后者用 `_schemaChildren` + 手动合并），内部字段映射逻辑不同，合并会导致表单重复/缺字段。两处各自独立维护，改字段时要两边确认。
- **硬编码编辑器 ≠ schema 自动生成，两者只能走一条路**：`feature_grid` 已统一使用 schema 自动表单，首次新增、保存后重载和变体切换都不得再回退到旧硬编码编辑器；否则旧表单的 `feature` 单数字段与 schema/后端的 `features` 列表不一致，会造成首次预览为空、保存丢内容和图标控件不同。仍保留硬编码编辑器的 block（如 `data_grid`）必须在 schema 通用路径中主动排除，避免生成重复字段。新增或迁移编辑器时，必须同时检查 `addModule`、`initSchemaMounts`、`admin_modules.js` 的 `buildModuleHTML` 三条路径。
- **改完模板/CSS/JS/Python 后自动重启 dev server**：涉及 HTML 模板、CSS、JS 文件改动后，改完立即杀掉旧进程，按下面「重启 dev server 必须带 FLASK_HOST 和 FLASK_DEBUG」那条的完整命令重启，不要让用户提醒。Flask 热重载有时不生效（多进程残留、JS 缓存等），直接杀进程重启最可靠。**改 Python 文件（`app/__init__.py` 的过滤器、`app/core/*.py` 的路由等）尤其必须重启**：局域网模式（`FLASK_HOST=0.0.0.0`）下 Werkzeug reloader 随调试器一起被关掉，只有模板会热重载，`.py` 改动完全不生效 —— 曾因新加了 Jinja 过滤器没重启，模板里一调用就找不到过滤器，账户中心整页 500。
- **改完 JS 后自动升版本号**：每次修改 `admin_modules.js` 后，同时更新 `panel_page_edit.html` 和 `panel_data_list.html` 中 `<script src="/static/js/admin_modules.js?v=N">` 的版本号（递增），避免浏览器缓存导致修改不生效。
- **重启 dev server 必须先杀光端口上所有进程**：`netstat -ano | grep ':5000'` 查看，`taskkill /F /PID <id>` 逐个杀。不能只 `Stop-Process python`（可能漏掉子进程）或信任旧进程已退出。Flask reloader 会 fork 子进程，多次重启会堆积僵尸进程，导致 HTTP 请求始终由最早的旧进程处理，代码改动不生效。杀完后用 `netstat -ano | grep ':5000.*LISTENING'` 确认端口清空，再启动。
- **重启 dev server 必须带 `FLASK_HOST=0.0.0.0` 和 `FLASK_DEBUG=1`**：缺 `FLASK_DEBUG=1` 则 `TEMPLATES_AUTO_RELOAD` 为 False，Jinja2 把编译后的模板缓存在内存里，改模板文件不会生效；缺 `FLASK_HOST=0.0.0.0` 则只绑回环，局域网地址 `http://192.168.1.31:5000` 会直接断掉（`.env` 里 `FLASK_HOST` 是注释掉的，不显式设就是 127.0.0.1，曾因此把别人正在看的服务弄停）。完整命令：`$env:FLASK_HOST='0.0.0.0'; $env:FLASK_DEBUG='1'; python run.py`。对外暴露时 `run.py` 会自动关掉 Werkzeug 交互式调试器（RCE 风险），模板热重载不受影响，两者已解耦。
- **文件改动后必须字节级验证，禁止只看 Read 工具输出**：Read 工具可能读到的是 IDE 缓存或工作树快照。改完关键文件后用 `python -c "open(path,'rb').read()"` + 正则/hex 直接读磁盘字节确认改动真的写入了，不要信 Read 的输出。
- **后台按钮图标统一用内联 SVG，禁用 Unicode 特殊字符**：`↑` `↓` 这类箭头是 ASCII 安全字符可以用，但 `⇄`（U+21C4）、`↔` 等落在 CJK/特殊符号区的字符在浏览器/系统字体下经常渲染成 `?` 乱码。新增按钮图标一律用和现有删除按钮同款 14×14 SVG（`stroke="currentColor" stroke-width="2"`），尺寸颜色风格对齐。这条同时适用于模板 Jinja 版和 JS 动态生成版 —— 两处必须同步改。

## 一、产品是什么

**让小企业老板自己做出"不会坏的网站"的平台。**

一句话定位：

> 你的网站像一份 PDF —— 发布出去就在那里，5 年后还能正常打开。

详见 [docs/vision.md](docs/vision.md)。

## 二、目标用户

- 不会编程的小企业老板（制造业、餐饮、服务业、贸易）
- 网站更新频率：**每 1-6 个月一次**（加产品、改活动、写公告）
- 之前可能用过 WordPress 但被升级 / 插件 / 被黑搞怕了

## 三、核心信念（写代码前先回想这 7 条）

1. **小企业网站不需要"程序"，只需要"文件"** —— 输出永远是静态 HTML
2. **用户应该填表，不该写代码** —— 不让用户碰 HTML / CSS / JS
3. **模板要少而精** —— 3 套精美模板 > 30 套粗糙模板
4. **平台死了，用户的网站不能死** —— 一键导出 ZIP 是 P0 功能
5. **速度是产品的一部分** —— 字体子集化、图片自动优化、首屏 < 1 秒
6. **简单 > 优化** —— 小企业站规模下不为省几十 MB 增加判断逻辑（多语言资源全部按语言分目录复制，不区分共享）
7. **低频用户友好** —— 老板可能 6 个月才登录一次：账号密码登录（忘密可用邮箱/短信验证码找回）、按年订阅、帮助随手可得、回归提示

## 四、不做的事（很重要 — 防止过度设计）

| ❌ 不做                              | 为什么                                                                 |
| ------------------------------------ | ---------------------------------------------------------------------- |
| 引入可视化模板编辑器（Grapes.js 等） | 模板由开发者 + AI 写代码做，git 管理。3-5 套模板不值得为可视化系统买单 |
| 用户改 CSS / HTML / JS               | 模板升级会冲突                                                         |
| 30 套模板                            | 资源稀释，不如 3 套做精                                                |
| 在 Phase 1 MVP 里做多语言            | 留到 Phase 2（创始人 dogfooding 时上线）                               |
| 按月订阅                             | 低频用户会冲动退订                                                     |
| 整页所见即所得编辑器                 | 复杂度爆炸，需求其实是"换模板"                                         |
| 评论 / 论坛 / 用户系统               | 不是展示型网站的必需                                                   |
| 在线交易 / 购物车                    | 用 Shopify / 有赞，不是我们的赛道                                      |

## 五、技术栈

- **后端**：Flask + Jinja2
- **数据库**：SQLite（MVP）→ PostgreSQL（规模化后）
- **店主端前端**：vanilla JS + 简单表单（不引入 Vue / React）
- **模板**：HTML + Jinja2 + CSS，文件形式存于 `site_templates/`，git 管理（开发者 + AI 编写）
- **静态生成**：Python（Jinja2 渲染）
- **字体子集化**：fonttools / pyftsubset
- **图片处理**：Pillow（多尺寸 + WebP）
- **CDN / 域名 / SSL**：阿里云 OSS + CDN + 云解析（性能）+ Let's Encrypt（SSL，无配额，ACME 自动签 / 续），详见 [docs/infrastructure.md](docs/infrastructure.md)
- **登录**：账号（邮箱 / 手机号）+ 密码，注册与改密走一次性验证码（邮箱 SMTP / 手机短信）确认。旧邮箱魔法链接仅保留迁移兼容入口，新登录不再生成

## 六、加新功能前的检查清单

加入新功能前问自己：

1. 这是「老板会用到的」还是「程序员觉得酷的」？
2. 不做这个，用户会流失吗？
3. 做了这个，会让模板升级变难吗？
4. 这个能等到 Phase 2 / 3 再做吗？

任何一条让你犹豫，**默认不做**。

## 七、代码风格

- **简洁优先**：能 30 行写完的不写 100 行
- **不过度抽象**：MVP 不要为"未来可能的需求"留接口
- **注释用中文**，代码（变量名、函数名）用英文
- **错误处理只在系统边界做**（用户输入、外部 API），内部代码相信调用方
- **不写测试**，直到核心流程稳定（MVP 阶段验证产品比验证代码重要）
- **依赖能少则少**，每个新依赖都要问"必须吗"

## 八、文档约定

- **少写代码**（代码会过时，人话不会）
- 文档面向**人**（创始人、未来的协作者），不是面向编译器
- 多用表格、列表、对比、图示
- 每个 docs/ 下的文件都应该独立可读
- 不写"接下来会..."这类时态依赖的句子

## 九、提交信息约定

中文，简洁，说"为什么"而不只是"什么"：

```text
feat: 增加字体子集化（首屏字体从 9MB 降到 15KB）
fix: 修复发布时旧字体文件未清除导致的乱码
refactor: 简化模板加载逻辑，去掉未使用的扩展点
docs: 调整产品定位，明确不做整页所见即所得编辑器
```

## 十、常用命令速查

所有命令在项目根目录执行：

| 命令 | 用途 |
|---|---|
| `$env:FLASK_HOST='0.0.0.0'; $env:FLASK_DEBUG='1'; python run.py` | 启动开发服务器（本机 http://127.0.0.1:5000 、局域网 http://192.168.1.31:5000）——命令行别用 `localhost`，它会先试 IPv6 白等约 2 秒 |
| `flask --app run scan-templates` | 扫描 site_templates/ 同步模板到数据库 |
| `flask --app run create-user <email>` | 创建用户 (开发期跳过邮件验证) |
| `flask --app run create-site <email> <slug> --template <name>` | 创建站点 + 复制种子数据 |
| `flask --app run build-site <site_id>` | 生成静态站点到 output/<site_id>/ |
| `flask --app run list-users` | 列出所有用户 |
| `flask --app run list-sites` | 列出所有站点 |
| `flask --app run promote-admin <email>` | 将用户提升为平台管理员 |

## 十一、关键文件速查

| 想做什么 | 看哪个文件 |
|---|---|
| 改登录/注册逻辑 | [app/core/routes.py](app/core/routes.py) (auth 相关路由) |
| 改站点模型/数据库表 | [app/core/models.py](app/core/models.py) |
| 改静态站点生成逻辑 | [app/core/builder.py](app/core/builder.py) |
| 改菜单系统（类型/渲染/升级） | [app/core/menu.py](app/core/menu.py) |
| 改数据集 CRUD（产品/文章等） | [app/core/datasets.py](app/core/datasets.py) |
| 改站点文件读写（YAML） | [app/core/site_storage.py](app/core/site_storage.py) |
| 改模板扫描/加载逻辑 | [app/core/template_loader.py](app/core/template_loader.py) |
| 改管理后台页面 | [app/templates/](app/templates/) |
| 改管理后台样式 | [app/static/css/admin.css](app/static/css/admin.css) |
| 改网站模板（前端展示） | [site_templates/<模板名>/](site_templates/) |
| 改系统配置/环境变量 | [.env.example](.env.example) / [app/core/config.py](app/core/config.py) |
| 了解产品愿景 | [docs/vision.md](docs/vision.md) |
| 了解系统架构 | [docs/architecture.md](docs/architecture.md) |
| 了解数据库设计 | [docs/database.md](docs/database.md) |
| 了解模板/Block 系统 | [docs/templates.md](docs/templates.md) |

## 十二、禁止的操作

以下操作在任何情况下都**不能做**，除非用户明确书面要求：

| ❌ 禁止 | 原因 |
|---|---|
| 删除 `sites/` 目录或其内容 | 那是用户的真实网站数据 |
| 删除 `output/` 目录（手动 `rm -rf`） | 构建输出可能包含待发布的站点 |
| 修改 git 历史（`rebase -i`、`reset --hard`、`push --force`） | 破坏协作基础 |
| 删除或重建 SQLite 数据库文件 | 里面有用户账号和站点记录 |
| 修改 `.gitignore` 中已有的忽略规则 | 可能导致敏感文件被提交 |
| 安装未经 `requirements.txt` 声明的新依赖 | 违背"依赖能少则少"原则 |
| 修改 `app/core/models.py` 中已上线的表结构（只增不减） | 破坏数据兼容性 |
| 跳过 git hooks（`--no-verify`、`--no-gpg-sign`） | hooks 存在是有原因的 |

## 十三、本项目的故事

这个项目最初是创始人想给自己网站用的工具。设计源自 WordPress 维护痛苦的真实体验。

保持「自己也会用」的视角 —— 这是它最大的护城河。

任何决策犹豫时，问自己一句：**"如果我自己用这个产品，这样做合理吗？"**

## 十四、Git 提交、文档与推送时机（AI 行为规范）

### 14.1 什么时候该提交

**以下情况 AI 应主动建议提交：**

| 触发条件 | 示例 |
|---|---|
| 用户交代的一个任务完整做完 | "产品列表改好了，要提交吗？" |
| 多步骤任务到达自然分界点 | 数据模型 → 路由 → 模板，每个做完各提一个 |
| 重构完成且行为无变化 | "9 个死文件删完了，832 行，提交？" |
| Bug 修复完成并验证通过 | "空指针修好了，dev server 验证过，提交？" |
| 文档更新完成 | "架构文档已更新反映 block 系统，提交？" |

**以下情况不应提交：**

| 禁止条件 | 原因 |
|---|---|
| 代码处于中间态，功能不可用 | 半成品让 git bisect 失效 |
| 临时调试代码、注释掉的实验 | 不要把垃圾桶存进 git |
| 未在本地验证 | 没跑过的代码不提交 |
| 琐碎到不值得单独记录 | 改空格、调缩进，合并到下一个有意义的提交 |

### 14.2 提交信息格式

沿用现有规范，**无意义信息绝对禁止**：

```
feat: 中文描述（说为什么）
fix: 中文描述（说什么问题 + 怎么修的）
refactor: 中文描述（说简化 / 删除了什么）
docs: 中文描述（说补充 / 修正了什么）
style: 中文描述
chore: 中文描述
```

`"1"`、`"update"`、`"fix"`、`"改"` 这类信息等同于没写——**禁止**。

### 14.3 什么时候该写 / 更新 docs/

| 应该写 | 不该写 |
|---|---|
| 新功能改变用户可见行为或开发者工作流 | 纯内部重构，对外行为不变 |
| 架构 / 数据库表结构变更 | 简单 Bug 修复（除非揭示了设计缺陷） |
| 新增配置项（env var / config.py） | 代码足够自解释的小改动 |
| 做了非显而易见的决策（选 X 不选 Y） | — |
| 用户明确要求 | — |

### 14.4 什么时候该推送

| 应该推送 | 不该推送 |
|---|---|
| 用户要求推送 | 代码未在本地验证 |
| 一批提交完成，需要分享 / 部署 | 分支上有半成品 |
| 工作阶段结束（如"今天的都推上去"） | 包含已知破坏性改动且用户不知情 |

### 14.5 AI 操作边界（硬约束）

1. **提交前必须告知，等用户确认后才执行**——说清楚"要提交哪些文件、提交信息是什么"，用户回复确认后再 `git commit`
2. **推送前必须确认**——说清楚"推哪个分支、包含几个提交"，等用户确认
3. **允许推送到非 main 分支**（如 dev 分支），无需额外确认
4. **绝对不推送 main/master**——除非用户明确说"推到 main"
5. **代码完成后自检文档触发条件**——改完代码自问一句"这次改动有没有触发 14.3 的文档更新条件？"有的话提醒用户
6. **多步骤任务拆小提交**——一个功能涉及多个层次（模型 / 路由 / 模板），各自独立提交，不混在一起
