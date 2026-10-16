# 全项目代码审查报告（2026-06-09）

> 本报告由多 agent 审查（7 维度并行 + 对抗性验证，44 个 agent）产出，确认 **37 个真实问题**，其中 5 个最高危项经人工独立复核。
>
> **本报告仅记录问题与修复建议，未改动任何代码**。修复时请遵循 [CLAUDE.md](../CLAUDE.md) 的提交/文档规范，按严重度分批进行。

## 目录

- [一、审查方法](#一审查方法)
- [二、问题汇总表](#二问题汇总表)
- [三、必须立刻修（critical / 高危安全）](#三必须立刻修critical--高危安全)
- [四、高优先（high）](#四高优先high)
- [五、中等（medium）— 健壮性 / 数据安全](#五中等medium-健壮性--数据安全)
- [六、低优先（low）— 代码质量 / 健壮性细节](#六低优先low-代码质量--健壮性细节)
- [七、误报与已澄清项（不需修）](#七误报与已澄清项不需修)
- [八、建议修复顺序](#八建议修复顺序)

---

## 一、审查方法

- **范围**：全部约 5660 行 Python（`app/core/` 核心 + `run.py` + `scripts/` + `demo/`）+ 前端模板（`site_templates/`、`app/templates/`）+ 配置。
- **方式**：按 7 个维度并行审查 → 每个发现独立对抗性验证（重新读源码、追数据流、跑攻击链）→ 完整性补漏。
  - 维度：安全 / 数据完整性 / 构建发布 / 业务逻辑 / 资源异常 / 前端模板 / 设计一致性。
- **人工复核**：路径穿越、SECRET_KEY、两个 XSS、图标渲染、slug 任意写——逐一用 `test_client` / 脚本实测确认，非纯理论。

---

## 二、问题汇总表

| # | 严重度 | 问题 | 主要位置 |
|---|---|---|---|
| 1 | 🔴 critical | 路径穿越 → 跨租户 IDOR + 任意 .yaml 覆盖 | routes.py / site_storage.py |
| 2 | 🔴 critical | 生产可能静默使用硬编码 SECRET_KEY → 会话可伪造 | config.py |
| 3 | 🟠 high | 主题色未校验 + `{{ val\|safe }}` → 跨用户存储型 XSS | routes.py / _base.html |
| 4 | 🟠 high | 语言选择首页字符串拼 HTML，公司名未转义 → 存储型 XSS | builder.py |
| 5 | 🟠 high | 数据集 slug 未校验 → 构建期任意文件写入 | menu.py / builder.py / routes.py |
| 6 | 🟠 high | 预览路由免登录 + 无归属校验 → 匿名遍历读他人未发布站点 | routes.py |
| 7 | 🟠 high | 图标注册表 11 个 `<rect>` 缺 width/height → 图标残缺 | icon_registry.py / extract_icons.py |
| 8 | 🟡 medium | Session Cookie 未设 SECURE/SAMESITE/LIFETIME | \_\_init\_\_.py |
| 9 | 🟡 medium | `/login` 无限流 + 任意邮箱自动建号 → 邮件轰炸/刷库 | routes.py |
| 10 | 🟡 medium | `run.py` 默认 debug=True（曾修复又回退，docstring 自相矛盾） | run.py |
| 11 | 🟡 medium | YAML 写入非原子（先截断）→ 崩溃/磁盘满损坏用户内容 | site_storage.py |
| 12 | 🟡 medium | 建站先 commit 后建目录，中途失败留半成品站 | routes.py |
| 13 | 🟡 medium | 单页渲染异常逐页吞掉 → 导出/发布静默缺页 | builder.py |
| 14 | 🟡 medium | 菜单渲染前未先 cap_menu_depth → 非 dict 项致整站构建崩溃 | builder.py |
| 15 | 🟡 medium | preview 路由两处 `except Exception: pass` 吞构建失败 → 误导 404 | routes.py |
| 16 | 🟡 medium | 建站成功 flash 文案乱码 + 正确文案藏在不可达死代码里 | routes.py |
| 17 | 🔵 low | `menu.py` 用 `rstrip('s')` 错剥多字符（address→addre） | menu.py |
| 18 | 🔵 low | claude 模板 contact_info 默认变体电话/邮箱/地址永远渲染空 | site_templates/claude/blocks/contact_info |
| 19 | 🔵 low | `_render()` if/else 两分支相同（伪分支 + 误导 docstring） | routes.py |
| 20 | 🔵 low | `_field_looks_like_uploadable_media` 死函数 + 与孪生函数重复 | routes.py |
| 21 | 🔵 low | collect_render_tasks 详情页二次回退不可达死代码 | menu.py |
| 22 | 🔵 low | 菜单遍历逻辑内联复制 3 次（命名还不一致） | routes.py |
| 23 | 🔵 low | ~30 处函数内重复 `from flask import ...` | routes.py |
| 24 | 🔵 low | 数据集 CRUD 读-改-写无锁 → 并发丢更新（单店主低频，概率低） | datasets.py |
| 25 | 🔵 low | `_save_uploaded_image` 未用 with + 损坏图在编辑路径 500 | routes.py |
| 26 | 🔵 low | `/favicon.ico` 绝对路径且从不生成 → 每页 404 | _base.html |
| 27 | 🔵 low | 语言切换器详情页跨语言可能 404 | _base.html / menu.py |
| 28 | 🔵 low | `.bak` 回退模板 XSS（已 gitignore，仅本地） | site_templates/*/blocks/*/template.jinja2.bak |
| 29 | 🔵 low | 建站 slug 唯一性 TOCTOU → 重复 slug 触发未捕获 500 | routes.py |
| 30 | 🔵 low | `_migrate_login_tokens_table` 手写建表丢 CASCADE（死代码+地雷） | \_\_init\_\_.py |
| 31 | 🔵 low | `_migrate_users_add_columns` 迁移不完整（只补 2 列） | \_\_init\_\_.py |
| 32 | 🔵 low | context_processor 裸 except 吞异常 + translation_enabled 误关 | \_\_init\_\_.py |
| 33 | 🔵 low | `demo/build_admin_demo.py` 硬编码他机 Windows 路径必崩 | demo/build_admin_demo.py |
| 34 | 🔵 low | `.env.example` 漏声明 ENABLE_DATA_ATTR_BLOCKS / MAX_CONTENT_LENGTH | .env.example |

---

## 三、必须立刻修（critical / 高危安全）

### #1 路径穿越 → 跨租户 IDOR + 任意 .yaml 覆盖 🔴

- **位置**：`app/core/routes.py`（`/_panel/<path:page_key>`、`/_dataset/<path:dataset_key>` 等路由）、`app/core/site_storage.py:42-74`、`app/core/datasets.py:19,36`
- **问题**：`page_key`/`dataset_key` 用 Flask `<path:>` 转换器接收（保留 `..` 和 `/`），未经任何校验直达 `read_yaml`/`write_yaml(site_id, f'pages/{key}.yaml')`。而 `site_storage` 的 `write_yaml`/`read_yaml` 实现是 `site_root(site_id) / relative_path`，**没有任何路径边界校验**。
- **对比**：同项目 `routes.py:73` 的 `_safe_send_from_directory` 对资产/构建输出做了完整的 `resolve()+relative_to()` 防护——YAML 路径这条链路明显缺失同等防御，属漏防而非有意设计。
- **后果**：任一已登录店主（最低权限）可通过 `GET /_panel/%2e%2e/%2e%2e/<其他站点id>/data/products` 读取**其他店主站点**的 .yaml 内容（跨租户 IDOR），可通过 POST 写入/覆盖/删除任意路径的 .yaml 文件，破坏其他站点数据。
- **复核**：已用 Flask test_client（项目实际依赖版本）实测 `/_panel/../../data/x`、`/_dataset/%2e%2e/%2e%2e/3/data/products` 全部返回 200，视图收到的 key 原样含 `..`；`Path('/sites/5')/'pages/../../../../etc/passwd.yaml'` 逃出目录边界成立。
- **建议修复**（两层都做）：
  1. **存储层兜底**：`site_storage` 加 `_safe_path(site_id, relative_path, lang)`——`base=site_root(或lang_root).resolve()`，`full=(base/relative).resolve()`，`full.relative_to(base)` 失败即 `abort(400)`。`write_yaml`/`read_yaml` 都走它。
  2. **路由层白名单**：对 `page_key`/`dataset_key` 用 `^[a-z0-9][a-z0-9_-]{0,40}$` 校验，非法直接 404。
- **兼容性**：已核实现有所有数据集/页面 key（about/contact/home/portfolio/posts/pricing/products/features）均符合白名单，零误伤。

### #2 生产可能静默使用硬编码 SECRET_KEY → 会话可伪造 🔴

- **位置**：`app/core/config.py:17-31`（`_resolve_secret_key`）
- **问题**：`is_prod` 只在 `FLASK_ENV=production/prod` 或 `FLASK_DEBUG=0` 时为真。最常见的生产部署方式 `gunicorn run:app`（不设这两个环境变量）下 `is_prod=False`，于是 SECRET_KEY 未配置时**静默回落到硬编码常量** `'dev-only-do-not-use-in-prod'`，只打一条 warning 不阻断启动。
- **后果**：攻击者拿到源码里公开的固定 key，即可伪造任意用户（含 admin）的 session cookie，直接登录后台。docstring 还声称"生产必须拒绝启动"，与实际行为矛盾。
- **复核**：实测 `FLASK_ENV='' FLASK_DEBUG=''` → `is_prod=False` → 用硬编码 key，确认裸 gunicorn 启动会裸奔。
- **建议修复**：判定反过来（fail-closed）——默认按生产对待，只有显式 `is_dev = FLASK_ENV in ('development','dev') or FLASK_DEBUG in ('1','true')` 才允许回落临时 key；否则 `raise`。
  - **注意衔接**：fail-closed 后，本地 `python run.py` 若既无 SECRET_KEY 也无 dev 声明会拒绝启动。本机 `.env` 已设 SECRET_KEY，不受影响；但应在 `.env.example` 写清楚本地开发需 `FLASK_DEBUG=1` 或设 SECRET_KEY。

---

## 四、高优先（high）

### #3 主题色未校验 + `{{ val|safe }}` → 跨用户存储型 XSS 🟠

- **位置**：`app/core/routes.py`（`theme_edit`，6 个颜色字段只取值不校验）；`site_templates/claude/templates/_base.html`、`site_templates/dengtec/templates/_base.html`（`{% ... %}--{{ key }}: {{ val | safe }};`）
- **问题**：`theme_edit` 把表单颜色值原样存进 `settings.theme`，`_base.html` 用 `{{ val|safe }}` 注入 `<style>` 块（关闭转义）。`color-primary` 设成 `red}</style><script>alert(document.domain)</script>` 即可闭合 style 标签注入脚本。
- **放大**：配合免登录的 `/preview/<id>`（见 #6），脚本在平台自身 origin 下对任意访客执行，并写进导出的静态站点。
- **复核**：已确认两个 `_base.html` 都用 `|safe`，`theme_edit` 的 6 个字段无格式校验。`block_renderer` 自身注释声明"所有注入值统一转义、style 值按白名单校验"，唯独主题注入破了这个约定。
- **建议修复**：后端用与 `block_renderer._SAFE_COLOR` 等价的正则 `^(#[0-9a-f]{3,8}|rgba?\(...\)|hsla?\(...\)|[a-z]+)$` 校验每个颜色值，非法丢弃；或把 `_base.html` 的 `|safe` 改回默认转义。

### #4 语言选择首页字符串拼 HTML，公司名未转义 → 存储型 XSS 🟠

- **位置**：`app/core/builder.py:281-297`（`_build_language_selector_page`）
- **问题**：该函数不走 Jinja2，手工 `html += '<title>... ' + 公司名` 字符串拼接，把店主在 `/company` 填的公司名原样塞进 `<title>`/`<h1>`。`company` 路由保存时只 `.strip()`、不转义。公司名填 `<script>...</script>` 即在生成的根 index.html 执行。
- **放大**：该页经免登录 `/preview` 暴露；是多语言站每次构建必经的根页面。
- **建议修复**：用 `markupsafe.escape()` 包裹所有拼入 HTML 的用户值，或改用最小 Jinja2 模板渲染（默认自动转义）。

### #5 数据集 slug 未校验 → 构建期任意文件写入 🟠

- **位置**：`app/core/menu.py:328-333`、`app/core/builder.py:331-333`、`app/core/routes.py`（`dataset_edit` 保存 slug 处）
- **问题**：详情页输出路径 `f'{item_path}/{slug}/index.html'`，slug 取自店主可编辑的 `data/*.yaml` 条目；`dataset_edit` 保存 slug 时只查唯一性、不校验格式（对比站点级 slug 用 `SLUG_PATTERN` 严格校验）。slug 设成 `../../../../home/rie/.ssh/foo` 时，`builder` 的 `out.parent.mkdir + out.write_text` 会把 HTML 写到 output 目录外。
- **后果**：经身份认证的店主可触发构建期任意文件写入/覆盖（可链到 RCE）。
- **建议修复**：① `dataset_edit` 保存 slug 时复用 `SLUG_PATTERN`（或 `[a-z0-9-]` 白名单）；② `builder` 写文件前断言 `out.resolve()` 仍在 output 根内（`relative_to` 检查），越界跳过并记日志。

### #6 预览路由免登录 + 无归属校验 → 匿名遍历读他人未发布站点 🟠

- **位置**：`app/core/routes.py`（`AUTH_EXEMPT_ENDPOINTS` + `preview`/`preview_site`/`preview_or_build`）
- **问题**：三个吐真实用户 output 的预览路由都在 `AUTH_EXEMPT_ENDPOINTS` 里（`require_login` 直接放行），且只做 `Site.query.get_or_404(site_id)`，从不校验站点归属。
- **后果**：① 任何匿名者自增 `site_id` 即可读其他老板尚未发布的私密站点全部 HTML/资源（跨用户 IDOR）；② `?_=1` 还能对任意 site_id 触发 `build_site()` 重建，消耗 CPU/磁盘。
- **说明**：`template_preview` 只渲染模板种子数据、不涉及用户私有数据，可保持免登录。
- **建议修复**：从 `AUTH_EXEMPT_ENDPOINTS` 移除这三个；每个路由取到 site 后补 `_require_site_access`——`user=_current_user(); if not user: abort(401); if user.role!='admin' and site.owner_id!=user.id: abort(403)`。若确需"免登录分享预览"，改用 `itsdangerous` 签名 token（含 site_id+过期），而非裸自增整数。

### #7 图标注册表 11 个 `<rect>` 缺 width/height → 图标残缺 🟠

- **位置**：`app/core/icon_registry.py`、`scripts/extract_icons.py:30`
- **问题**：`ICON_REGISTRY` 里 briefcase/building/camera/circuit/cpu(×2)/display/monitor/shipping/truck/video 共 11 个 `<rect>` 缺 `width`/`height`。SVG 规范下零面积 rect 不渲染，图标显示残缺/空白。
- **根因**：`extract_icons.py:30` 的 `re.sub(r'\s(width|height)="[^"]*"', '', svg)` 本想只剥根 `<svg>` 写死的尺寸（让 CSS 控制），但正则对全文所有元素生效，把 `<rect>` 的内在尺寸也删了。`icon_registry.py` 里已是被剥坏的成品，运行期直接受影响。
- **复核**：已实测遍历 `ICON_REGISTRY` 确认 11 个坏 rect；对照原始 `.bak` 模板确认正确尺寸（如 briefcase rect 应为 `width="20" height="14"`，cpu 内层 `width="6" height="6"`）。
- **建议修复**：① 正则只针对根 `<svg>` 标签段；② 直接给这 11 个 rect 补回正确尺寸（参照原始 Feather 图标值）。

---

## 五、中等（medium）— 健壮性 / 数据安全

> ⚠️ **#11 与产品 P0 信念"网站像 PDF，5 年后还能打开"直接冲突，建议优先于其他 medium 修。**

### #8 Session Cookie 未加固
- **位置**：`app/__init__.py`、`app/core/config.py`
- **问题**：全项目从未设置 `SESSION_COOKIE_SECURE`/`SAMESITE`/`PERMANENT_SESSION_LIFETIME`（HTTPONLY 默认 True 这条 OK）。SECURE=False 意味着存在 HTTP 路径时会话 cookie 明文传输可被窃取；SAMESITE 缺省少了 CSRF 浏览器层纵深。
- **建议修复**：`create_app` 显式设 `SESSION_COOKIE_HTTPONLY=True`、`SESSION_COOKIE_SAMESITE='Lax'`、生产 `SESSION_COOKIE_SECURE=True`、合理的 `PERMANENT_SESSION_LIFETIME`。

### #9 `/login` 无限流 + 任意邮箱自动建号
- **位置**：`app/core/routes.py:408-446`（`_create_magic_link` + `login`）
- **问题**：对任何含 `@` 的字符串直接 `User(email=...)` 建号落库，且 `/login` 无任何速率限制。接入真实邮件后：① 任意第三方邮箱 → 邮件轰炸（发件域是本平台，损声誉）；② 海量伪造邮箱 → 无限写 users/login_tokens 表撑爆库（当前刷库向量已生效）。
- **建议修复**：对 `/login` 加 IP+邮箱维度限流；对未注册邮箱统一返回中性提示（"若已注册将收到邮件"）而不立即建号，或把建号推迟到 token 被实际消费时。

### #10 `run.py` 默认 debug=True
- **位置**：`run.py:17`
- **问题**：`FLASK_DEBUG` 未设时 `debug=True`，开启 Werkzeug 交互式调试器（PIN 曾多次被绕过，等同 RCE 入口）。git 历史显示这是一次回归：提交 `bc0c478`（"security: 默认关 debug"）曾改为 `'0'`，提交 `d2bbcee`（提交信息是无意义的"1"）又改回 `'1'`，docstring/`.env.example` 未同步——当前文件自相矛盾（docstring 写"默认 0"，代码是默认 1）。
- **建议修复**：默认改回 `'0'`，并在 host 非本机（0.0.0.0）时强制拒绝 debug；同步修正 docstring 与 `.env.example`。

### #11 YAML 写入非原子 ⚠️
- **位置**：`app/core/site_storage.py:52-55`
- **问题**：`write_text('w' 模式)` 先把目标文件截断为 0 再写。进程在写入中崩溃/被 kill/磁盘满，文件停在截断/半写的损坏状态——而这是店主网站的唯一权威副本（pages/data/settings），无备份、`sites/` 不入仓。
- **复核**：已实测截断为 0 字节文件 `yaml.safe_load` 返回 None（内容静默全失）；半写文件可丢记录或抛 ScannerError。
- **建议修复**：原子写——先写同目录临时文件，`fsync` 后 `os.replace(tmp, path)` 原子替换。`write_yaml` 是所有写入的单一出口，一处改动覆盖全部。

### #12 建站先 commit 后建目录
- **位置**：`app/core/routes.py`（建站流程）+ `app/commands.py`（`create_site_cmd` 同样问题）
- **问题**：`db.session.add(site) → commit()`（DB 已落库）之后才 `init_site_folder/copy_seed_data`。文件操作期间异常（磁盘满/权限/seed 损坏）会留下"DB 有、文件无"的半成品站，且无回滚。
- **建议修复**：把文件初始化移到 commit 前，或用 try/except 包裹文件操作，失败时 `db.session.delete(site)+commit` 回滚。

### #13 单页渲染异常逐页吞掉 → 静默缺页
- **位置**：`app/core/builder.py:311-338`、`app/core/routes.py`（export_zip）
- **问题**：`_render_for_language` 对每页渲染包 try/except，异常只 `logger.error` 后 continue，不计数不上抛；`build_site` 无条件返回，export 直接打包现有文件。结构性渲染失败时该页静默缺失，店主拿到缺页 ZIP/发布缺页站点而无任何提示。
- **建议修复**：累计失败任务并返回；export/发布在有失败时给店主明确提示（"N 个页面构建失败，未包含"）。

### #14 菜单渲染前未先 cap_menu_depth
- **位置**：`app/core/builder.py:368-374`（build_site）/ `534-540`（preview）
- **问题**：直接对原始 `settings['menu']` 调 `upgrade_old_format/normalize_for_render/ensure_home`，这三个都假设 item 是 dict。若 menu 列表混入标量/None（手工编辑 yaml 或模板作者写错），会抛 AttributeError/ValueError 中断整站构建。`cap_menu_depth` 才是唯一过滤非 dict 的防线，但在此路径上执行太晚。
- **建议修复**：调 `upgrade_old_format` 前先包一层 `cap_menu_depth`（与 routes.py 一致），或在三个函数内加 `if not isinstance(it, dict): continue`。

### #15 preview 路由两处 `except Exception: pass`
- **位置**：`app/core/routes.py`（preview 自动重建处，两处）
- **问题**：`except Exception: pass` 完全吞掉 `build_site` 失败，不记日志不提示，最终走到误导性的 `abort(404, '未生成页面')`。对比同文件 `build()` 路由规范用了 `logger.exception`。
- **建议修复**：两处 `except` 改为 `current_app.logger.exception('预览构建站点 %s 失败', site_id)`，保留 pass 继续尝试返回已有文件，但必须留痕。

### #16 建站成功 flash 文案乱码 + 不可达死代码
- **位置**：`app/core/routes.py`（site_new 成功分支）
- **问题**：真正执行的那行 flash 文案是乱码 `宸插垱寤虹珯鐐?#...`（"已创建站点 #" 的 UTF-8 字节被按 GBK 误解码的 mojibake）；而文案正确的版本因缩进位于 if/else 两分支 return 之后，是不可达死代码。
- **复核**：已做字节级回环验证确认 mojibake 机理；AST 分析确认死代码不可达。
- **建议修复**：把乱码行改回正确"已创建站点 #..."，删除后面那段不可达的重复块。

---

## 六、低优先（low）— 代码质量 / 健壮性细节

| # | 问题 | 位置 | 建议 |
|---|---|---|---|
| 17 | `rstrip('s')` 错剥多字符（address→addre），与下方 `[:-1]` 不一致 | menu.py:235 | 改为 `target[:-1]` |
| 18 | claude 模板 contact_info 默认变体 phone/email/address 永远空（data-from 写在无 data-name 的叶子上）；**dengtec 写法正确不受影响** | site_templates/claude/blocks/contact_info/template.html | 给每个 `<p>` 加 data-name+data-type，块根用 `data-from="settings:contact"` |
| 19 | `_render()` if/else 两分支完全相同 + docstring 误导 | routes.py | 删 if 直接 return，修正 docstring |
| 20 | `_field_looks_like_uploadable_media` 死函数且与孪生函数逐字重复 | routes.py | 直接删除 |
| 21 | collect_render_tasks 详情页二次回退不可达 | menu.py | 删除该死分支 |
| 22 | 菜单遍历逻辑内联复制 3 次（命名不一致） | routes.py | 抽公共函数到 menu.py |
| 23 | ~30 处函数内重复 `from flask import ...`（顶部已导入） | routes.py | 删冗余局部 import |
| 24 | 数据集 CRUD 读-改-写无锁，并发丢更新（单店主低频概率低） | datasets.py | 配合 #11 加文件锁 |
| 25 | `_save_uploaded_image` 未用 with + 损坏图在 product/post 编辑路径 500 | routes.py | `with Image.open(...)` + 编辑路径捕获 PIL 异常 |
| 26 | `/favicon.ico` 绝对路径且 builder 从不生成 → 每页 404 | _base.html | 生成默认 favicon 并加 `{{ base_url }}`，或删该行 |
| 27 | 语言切换器详情页跨语言可能 404（slug 按语言各自生成） | _base.html / menu.py | 详情页降级到列表页，或建 slug 映射 |
| 28 | `.bak` 回退模板 XSS（已 gitignore，仅本地，self-XSS） | site_templates/*/blocks/*/template.jinja2.bak | 直接从本地模板树移除这些 .bak |
| 29 | 建站 slug 唯一性 TOCTOU → 重复 slug 触发未捕获 500 | routes.py | try/except IntegrityError + rollback + 友好提示 |
| 30 | `_migrate_login_tokens_table` 手写建表丢 CASCADE（死代码+休眠地雷） | \_\_init\_\_.py | 删死代码，或补 ON DELETE CASCADE |
| 31 | `_migrate_users_add_columns` 只补 2 列（名实不符的半成品迁移） | \_\_init\_\_.py | 做全或删掉，明确依赖 create_all |
| 32 | context_processor 裸 except 吞异常 + translation_enabled 被误关 | \_\_init\_\_.py | except 内 logger.exception；translator_ready 移出 try |
| 33 | `demo/build_admin_demo.py` 硬编码他机 Windows 路径必崩 | demo/build_admin_demo.py | 改相对项目根定位；补 demo/ README |
| 34 | `.env.example` 漏声明 ENABLE_DATA_ATTR_BLOCKS / MAX_CONTENT_LENGTH | .env.example | 补两段注释样例，与 config.py 一一对应 |

---

## 七、误报与已澄清项（不需修）

审查过程中对抗性验证主动澄清/纠正的，记录在此避免误改：

- **dengtec 的 contact_info 是正确写法**（根 `data-from="settings:contact"` + 每值带 data-name），#18 只影响 claude 默认变体。审查初稿误报"dengtec 同款"，已纠正。
- **context_processor 注入的 `template_meta` 实际无模板消费**（路由各自构造并传入），#32 中"侧栏因 template_meta 缺失而空"这部分是误报；真正成立的是 `translation_enabled` 被误关 + 无日志。
- **`_save_uploaded_image` 的 PIL 句柄"泄漏"实际影响接近零**（局部变量函数退出即被引用计数回收），#25 属代码卫生/一致性，非会无界累积的真实泄漏。
- **`_migrate_users_add_columns` 的 bug 对本仓不可达**（所有列都在 initial commit 一起引入，ALTER 分支永不触发），#31 是名实不符的设计问题而非活跃 bug。
- **MVP 刻意简化的设计不是问题**：不写测试、SQLite、自动建表、手写迁移本身符合 CLAUDE.md 取向，仅其实现里的具体 bug 才计入。

---

## 八、建议修复顺序

按严重度分批，**每批一个独立提交**，从安全开始：

1. **第一批（安全，强烈建议立刻）**：#1 路径穿越 + #2 SECRET_KEY + #6 预览越权 + #3/#4 两个 XSS + #5 slug 写入。这 6 个都是认证用户或匿名者可利用的真实漏洞。
2. **第二批（数据安全）**：#11 原子写（优先）+ #12 建站事务 + #13 静默缺页 + #14 菜单崩溃 + #15 吞异常。
3. **第三批（可见 bug）**：#7 图标 + #16 乱码文案 + #17 逻辑笔误 + #18 contact_info。
4. **第四批（清理）**：死代码（#19/#20/#21/#30/#31）+ 重复（#22/#23）+ 配置文档（#34）+ 其余 low。

> 修复时遵循 [CLAUDE.md](../CLAUDE.md) 第十四节：每批改完先本地验证，提交前告知文件清单与提交信息，等确认后再 commit；不推送 main。
