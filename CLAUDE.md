# CLAUDE.md

本文件是 Claude 在本项目工作时的指导。所有未来的代码生成、文档修改、架构决策都应遵循下面的原则。

## 交流规范

- **始终用中文回答**：所有对话、解释、建议、代码审查意见均使用中文

## 代码规范

- **代码必须带注释**：关键逻辑、设计意图、边界条件必须用中文注释说明——不只是"做了什么"，而是"为什么这么做"

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
7. **低频用户友好** —— 老板可能 6 个月才登录一次：邮箱魔法链接、按年订阅、帮助随手可得、回归提示

## 四、不做的事（很重要 — 防止过度设计）

| ❌ 不做                              | 为什么                                                                 |
| ------------------------------------ | ---------------------------------------------------------------------- |
| 引入可视化模板编辑器（Grapes.js 等） | 模板由开发者 + AI 写代码做，git 管理。3-5 套模板不值得为可视化系统买单 |
| 用户改 CSS / HTML / JS               | 模板升级会冲突                                                         |
| 30 套模板                            | 资源稀释，不如 3 套做精                                                |
| 在 Phase 1 MVP 里做多语言            | 留到 Phase 2（创始人 dogfooding 时上线）                               |
| 按月订阅                             | 低频用户会冲动退订                                                     |
| 密码登录                             | 6 个月后用户找不回密码                                                 |
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
- **登录**：邮箱魔法链接（不要密码）

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
| `python run.py` | 启动开发服务器 (http://localhost:5000) |
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
