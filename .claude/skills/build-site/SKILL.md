---
description: "生成静态站点到 output/ 目录"
---

当用户说"构建站点"、"生成静态文件"、"发布"、"build"时触发.
将站点的 YAML 数据 + Jinja2 模板渲染为静态 HTML 文件,输出到 `output/<site_id>/`.

核心代码:`app/core/builder.py` → `build_site()`
数据流:读取 YAML → 收集数据 → Jinja2 渲染 → 复制静态资源 → 输出 HTML

## 前置条件

构建前确认:
1. 目标站点存在:`flask --app run list-sites`
2. 站点文件夹完整:`sites/<id>/settings.yaml` 存在
3. 模板文件完整:`site_templates/<name>/templates/` 存在
4. output/ 目录可写

## 执行构建

```
flask --app run build-site <site_id>
```

构建过程(`builder.py:181-304`):
1. 读取站点 settings.yaml + pages/*.yaml + data/*.yaml
2. 与模板 seed_data 做 deep merge(种子数据兜底)
3. 读取模板 meta.yaml(获取 default_menu、theme、languages 等)
4. 菜单升级(`menu_lib.upgrade_old_format`)+ 规范化
5. 创建 Jinja2 Environment(搜索 templates/ + blocks/ 目录)
6. 清空并重建 output/<site_id>/
7. 复制 static/(CSS/JS/字体)
8. 复制 assets/(店主上传的图片)
9. 对每种语言循环渲染所有页面
10. 多语言站点:生成根 index.html(语言选择页)

输出示例:
```
已生成: f:\dengtec\mycompany.website\output\1
```

## 构建产物结构

```
output/<site_id>/
├── index.html              ← 多语言站点:语言选择页(含 hreflang + JS 跳转)
├── static/                 ← 模板的 static/ 复制
│   └── css/main.css
├── assets/                 ← 店主上传的文件复制
├── zh-CN/                  ← 默认语言目录
│   ├── index.html          ← 首页
│   ├── about/index.html    ← 关于页
│   ├── products/
│   │   ├── index.html      ← 产品列表页
│   │   └── product-a/index.html  ← 每个产品的详情页
│   └── ...
└── en/                     ← 其他语言目录(结构相同)
```

注意:
- 每种语言是一个自包含的完整子目录
- 详情页预生成为静态 HTML(SEO 友好)
- 列表页的数据在 JS 加载的 data.json 中(暂未实现,当前直接服务端渲染)

## 构建日志和错误处理

构建中有警告和错误两级:

**警告(不阻止构建)**:
- 模板版本不一致:`WARNING: 站点 X 记录的模板版本 A 与磁盘上 B 的当前版本 C 不一致`

**错误(跳过该页面,继续构建其他页面)**:
- `页面 X (type=X, lang=X) 渲染失败: <详细错误>`
- 单页渲染失败不影响其他页面

**致命错误(构建中止)**:
- 站点不存在
- 文件系统不可写

如果某页面渲染失败:
1. 抄下控制台输出的完整错误信息
2. 参考 `debug-site` 技能排查

## 构建与预览的关系

后台预览按钮调用 `build_site(site_id, base_url='/preview/<id>')`,
构建到 `output/<id>/` 后通过 `/preview/<id>/` 路由访问.

与 CLI 构建的区别:
| 场景 | base_url | 访问方式 |
|------|----------|----------|
| 后台预览 | `/preview/<id>` | 通过 Flask 路由 |
| CLI 构建 | `''`(空) | 直接打开 HTML 文件 |
| 导出 ZIP | `''`(空) | 解压后放到任意服务器 |
| CDN 发布 | `''`(空) | 上传到 CDN 根目录 |

预览时图片路径:`/preview/<id>/assets/uploads/xxx.webp`
导出时图片路径:`/assets/uploads/xxx.webp`

## 常见问题

| 问题 | 原因 | 修复 |
|------|------|------|
| 构建后页面空白 | 模板渲染出错但被 try/except 吞了 | 查看控制台日志 |
| 页面数量不对 | 菜单未配置或配置错误 | 检查 settings.yaml 的 menu |
| 静态资源 404 | static/ 未正确复制 | 检查 site_templates/<name>/static/ 是否存在 |
| 图片不显示 | assets/ 路径问题 | 检查 sites/<id>/assets/ 和 output 中的 assets/ |
| 多语言站点某语言无输出 | meta.yaml languages 配置问题 | 检查模板的 meta.yaml |
| output/ 目录为空 | build_site 执行中出错 | 单独运行 CLI 命令看错误信息 |

## 关联技能

- `debug-site`:构建问题排查
- `export-site`:构建 + 打包 ZIP
- `publish-flow`(规划中):完整发布流程
- `dev-server`:启动服务器查看预览
