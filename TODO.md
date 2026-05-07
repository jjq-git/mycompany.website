# TODO

## 当前状态

- [x] 后端核心：Flask + Jinja2 + SQLAlchemy（MVP 可跑）
- [x] 前端框架：Bootstrap 5.3 已引入管理后台
- [x] 模板系统：dengtec、tech-product 两个模板（硬编码方式）
- [x] 静态生成：builder.py 可渲染站点到 output/
- [x] 数据集 CRUD：products、features、posts 可增删改

## 现有代码与目标规范差距（需重构）

> 目标规范详见 [开发指南.md](开发指南.md)

### 模板结构

- [ ] **dengtec 模板重构** — 按开发指南增加 `blocks/` 目录（meta.yaml + template.html + variants/）。tech-product 暂时不动
- [ ] **dengtec 页面数据格式改造** — `pages/home.yaml` 从固定 key（`banners`、`services`）改为 `modules` 数组（`type` + `order` + `variant` + `data`）
- [ ] **模块库实现** — 后台从 `blocks/` 扫描模块列表，店主选择→排序→填表
- [ ] **模块排版变体** — 每个模块支持 2-3 个 variants，店主可切换
- [ ] **模块显示配置** — columns（列数）、max_items（显示数量）、dataset（数据来源）

### Builder（静态生成器）

- [ ] **页面改为菜单驱动** — 去掉硬编码 page_map，遍历 `settings.yaml` 的 menu 列表动态渲染
- [ ] **首页 index 固定** — 始终渲染 index.html
- [ ] **list 类型自动生成** — 按 `target` 名匹配模板，查数据集自动渲染列表页+详情页
- [ ] **page 类型自动生成** — 按 `target` 名匹配模板，查 pages/*.yaml 渲染单页
- [ ] **link 类型不生成页面** — 仅导航链接

### 菜单系统

- [ ] **多级子菜单** — 不固定层级，每级可独立配置
- [ ] **子菜单下拉样式** — 垂直列表/水平平铺/网格排列/图文卡片四种变体
- [ ] **菜单删除关联检查** — 删除前扫描页面数据、数据集、引用链、子菜单、SEO 影响
- [ ] **首页 index 不可删除**

### Header / Footer

- [ ] **Header 模块库** — Logo 居中+菜单下方、Logo 左+菜单右、极简风、带顶栏等变体
- [ ] **Footer 模块库** — 四栏链接、三栏+订阅、极简单行等变体
- [ ] **语言切换按钮** — 水平行内/垂直下拉/旗帜+简称三种变体

### 预览面板

- [ ] **三种设备模式** — 电脑(1280px)/平板(768px)/手机(375px) 切换
- [ ] **模块按设备独立配置** — 变体、列数、显示数量、隐藏、图片尺寸按设备覆盖
- [ ] **responsive 字段存储** — 未配置的设备默认继承电脑端

### 后台功能

- [ ] 登录系统（邮箱魔法链接）
- [ ] 图片上传 + 自动压缩/WebP 转换
- [ ] 字体子集化（fonttools）
- [ ] 发布到 CDN（阿里云 OSS）
- [ ] 自定义域名 + SSL（Let's Encrypt ACME）
- [ ] 整站导出 ZIP

### 数据库

- [ ] login_tokens 表（魔法链接）
- [ ] publish_versions 表（发布历史）
- [ ] provisioning_jobs 表（云资源自动化）
- [ ] audit_log / email_log 表

## Phase 2（后续）

- [ ] 多语言 + AI 翻译
- [ ] 订阅/支付（年付）
- [ ] 自定义域名 + SSL