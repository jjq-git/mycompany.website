---
name: site-scan-templates
description: "扫描 site_templates/ 目录同步模板到数据库"
---

当用户说"扫描模板"、"同步模板"、"刷新模板"时触发.
新增或修改 site_templates/ 下的模板后需要执行,将 meta.yaml 信息写入数据库 Template 表.

核心代码:`app/core/template_loader.py` → `scan_templates()`
数据流:`site_templates/<name>/meta.yaml` → 解析 YAML → 写入/更新 `templates` 表

## 前置条件

确认以下条件满足:
1. `site_templates/` 目录存在且包含至少一个模板子目录
2. 每个模板子目录下有 `meta.yaml`(缺少则跳过该目录)
3. `meta.yaml` 必须包含 `display_name` 和 `industry` 字段(见下方格式)
4. 数据库已初始化(Flask 启动过或手动建过表)

## 执行扫描

运行命令:
```
flask --app run scan-templates
```

输出示例:
```
同步了 1 个模板:
  - dengtec (瞪特科技官网) [tech]
```

扫描逻辑(`template_loader.py:20-53`):
- 遍历 `site_templates/` 下所有子目录
- 跳过 `.` 开头的目录
- 读取每个目录的 `meta.yaml`
- 如果数据库已有同名模板则更新,否则新建
- 更新的字段:display_name、industry、description、cover_image、version、is_public

## meta.yaml 格式要求

每个模板必须有一个 `meta.yaml`,最少内容:
```yaml
display_name: 模板显示名(中文)
industry: tech
version: '1.0.0'
```

完整字段(参考 `site_templates/dengtec/meta.yaml`):
```yaml
display_name: 瞪特科技官网
industry: tech
description: 适合科技公司的现代简洁风格模板
cover_image: '/static/templates/dengtec.png'
version: '1.0.0'
is_public: true
datasets:
  - name: products
    label: 产品
  - name: features
    label: 功能特性
  - name: posts
    label: 博客
default_menu:
  - label: 首页
    type: home
  - label: 产品
    type: list
    target: products
default_theme:
  accent: '#067a7a'
  bg: '#ffffff'
languages:
  - code: zh-CN
    name: 简体中文
    flag: 🇨🇳
  - code: en
    name: English
    flag: 🇬🇧
default_language: zh-CN
header_variants:
  - key: logo_left_menu_right
    label: Logo 左 + 菜单右
footer_variants:
  - key: four_columns
    label: 四栏链接
```

字段说明:
| 字段 | 必需 | 用途 |
|------|------|------|
| display_name | 是 | 模板库中展示的名称 |
| industry | 是 | 行业分类(tech/manufacturing/restaurant/service 等) |
| version | 是 | 语义版本号,站点创建时记录此值 |
| description | 否 | 模板库中的描述文字 |
| cover_image | 否 | 模板封面图路径 |
| is_public | 否 | 是否在模板库中显示(默认 true) |
| datasets | 否 | 模板支持的数据集列表 |
| default_menu | 否 | 新站点的默认导航结构 |
| default_theme | 否 | 默认主题色变量 |
| languages | 否 | 多语言支持列表 |
| default_language | 否 | 默认语言代码 |
| header_variants | 否 | Header 变体列表 |
| footer_variants | 否 | Footer 变体列表 |

## 验证结果

扫描成功后验证:
1. 确认输出显示正确数量的模板
2. 检查数据库:
   ```
   sqlite3 instance/app.db "SELECT name, display_name, industry, current_version FROM templates;"
   ```
3. 新创建的站点应该能看到新模板

## 常见问题

| 问题 | 原因 | 修复 |
|------|------|------|
| "未找到任何模板" | site_templates/ 下没有含 meta.yaml 的目录 | 检查目录结构 |
| 模板名称重复 | 目录名就是模板唯一标识,不能重复 | 重命名目录 |
| 扫描后模板库没更新 | 可能是浏览器缓存 | 强制刷新(Ctrl+Shift+R) |
| 改了 meta.yaml 未生效 | 需要重新扫描 | 再运行一次 scan-templates |
| 数据库写入失败 | 数据库文件权限问题 | 检查 instance/ 目录权限 |

## 关联技能

- `new-template`:创建新模板(完成后需要 scan-templates)
- `new-block`:新增 Block(Block 变更不需扫描,模板元信息才需要)
- `db-manage`:查看数据库中的模板记录
- `create-site`:创建站点(依赖模板已扫描)
