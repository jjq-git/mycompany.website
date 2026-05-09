# TODO

## 当前状态

- [x] 后端核心：Flask + Jinja2 + SQLAlchemy（MVP 可跑）
- [x] 前端框架：Bootstrap 5.3 CDN 引入，配合自定义 admin.css
- [x] 模板系统：dengtec、tech-product 两个模板
- [x] 后台三栏布局：左配置菜单 | 中预览 (iframe) | 右属性面板
- [x] 三设备预览切换：电脑/平板/手机
- [x] 数据集 id 自动补齐：兼容旧种子数据
- [x] 静态生成：builder.py 可渲染站点到 output/
- [x] 数据集 CRUD：products、features、posts 可增删改
- [x] 左栏动态菜单：从 settings.yaml menu 列表自动生成（首页 index 固定，其余来自菜单配置）
- [x] 右栏 AJAX 动态加载：左栏点击 → `?_fragment=1` → 右侧面板替换
- [x] 首页模块编辑器：可用模块库选择 + 已选模块配置 + 保存即刷新预览
- [x] `page_panel` 路由：动态菜单项自动分派到数据集列表/单页编辑

## 现有代码与目标规范差距

> 目标规范详见 [开发指南.md](开发指南.md)

### 模板结构

- [x] **dengtec 模板重构** — `blocks/` 5 个模块，pages/home.yaml modules 数组格式
- [x] **模块库扫描** — `template_loader.py:scan_blocks()`
- [ ] **tech-product 模板重构** — 暂缓

### Builder（静态生成器）

- [x] 菜单驱动渲染（`collect_render_tasks()`）、首页固定、list/page/link 自动生成

### 菜单系统

- [x] 多级子菜单递归、删除关联检查
- [x] 子菜单下拉样式四种变体（dengtec 模板渲染端）
- [x] 首页 index 不可删除（后端校验）

### Header / Footer

- [x] Header/Footer 模块库变体选择 UI（`/settings/header`、`/settings/footer_variant`）
- [x] 语言切换按钮（in 网站头部面板，三种样式可选）

### 预览面板

- [x] 三种设备模式切换
- [x] 模块按设备独立配置（responsive 字段编辑 UI，每个模块支持电脑/平板/手机三端独立设置 columns/max_items/隐藏）

### 后台功能

- [x] 登录系统（邮箱魔法链接，MVP：开发环境页面显示链接；生产邮件发送待接入）
- [x] 图片上传 + WebP（产品/文章封面、模块图片字段上传到 `sites/<id>/assets/uploads/` 并自动转换）
- [ ] 字体子集化
- [x] 整站导出 ZIP（MVP：构建 output 后打包下载）
- [ ] 发布 CDN + SSL

### 数据库

- [ ] login_tokens / publish_versions / provisioning_jobs / audit_log

## Phase 2

- [ ] 多语言 + AI 翻译
- [ ] 订阅/支付

## 建议推进顺序

| 优先级 | 任务 | 状态 |
|--------|------|------|
| P0 | 核心流程闭环 + 三栏布局 + 模块编辑器 | ✅ 已完成 |
| P1 | tech-product 模板重构 | ⏸️ 暂缓 |
| P2 | Header/Footer 模块库 + 设备独立配置 UI | ✅ 已完成 |
| P3 | 登录系统 + 图片上传 + 字体子集化 | 🚧 登录系统与图片上传已完成，字体子集化待做 |
| P4 | 发布 CDN + SSL + 导出 ZIP | ❌ |
