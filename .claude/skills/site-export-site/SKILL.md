---
name: site-export-site
description: "构建站点并导出为 ZIP 文件"
---

当用户说"导出站点"、"下载 ZIP"、"导出网站"、"打包"时触发.
先构建静态文件,再将 `output/<site_id>/` 打包为 ZIP 供用户下载.
这是 P0 功能——"平台死了,用户的网站不能死"(CLAUDE.md 核心信念 #4).

核心代码:
- CLI:`flask --app run build-site <id>` + 手动 zip
- Web:`app/core/routes.py` → `export_zip()`(`/export.zip` 路由)

## 前置条件

1. 目标站点存在且可构建成功
2. 站点数据完整(settings.yaml、pages/*.yaml)
3. 模板文件完整

## 方式一:Web 界面导出

登录后台 → 选择站点 → 访问 `/export.zip` → 浏览器自动下载

路由实现(`routes.py:1130-1154`):
- `build_site(site_id, base_url='')` 构建(base_url 为空,适用于任意服务器部署)
- 用 Python `zipfile` 打包 output/ 目录
- `ZIP_DEFLATED` 压缩
- 文件名:`<slug>-static.zip`
- 返回 `send_file()` 下载

## 方式二:命令行导出

1. 先构建:
   ```
   flask --app run build-site <site_id>
   ```

2. 再打包:
   ```
   powershell Compress-Archive -Path output\<site_id>\* -DestinationPath output\<slug>-<日期>.zip
   ```

3. 检查 ZIP 内容:
   ```
   powershell Expand-Archive -Path output\<slug>-<日期>.zip -DestinationPath output\_verify\ -Force
   ls output\_verify\
   ```

## ZIP 内容结构

下载解压后的目录结构(与 `output/<id>/` 一致):

```
my-company-static/
├── index.html              ← 语言选择页(多语言站点)
├── static/                 ← CSS/JS/字体
│   └── css/main.css
├── assets/                 ← 图片等上传资源
│   └── uploads/
├── zh-CN/                  ← 默认语言
│   ├── index.html
│   ├── about/index.html
│   ├── products/
│   │   ├── index.html
│   │   └── product-a/index.html
│   └── ...
└── en/                     ← 其他语言
    └── ...

单语言站点(无 languages 配置):
```
my-company-static/
├── index.html              ← 直接是首页
├── static/
├── assets/
├── about/index.html
└── ...
```

## 验证导出

导出后验证:
1. ZIP 文件大小合理(不含视频的典型站点 < 50MB)
2. 解压到任意目录
3. 用浏览器直接打开 HTML 文件
4. 检查所有页面链接是否正常(相对链接在本地也能工作)
5. 检查图片是否正常显示
6. CSS 样式是否正确加载

关键验证点:
- 首页能打开
- 导航链接可点击跳转
- 产品列表页有数据
- 产品详情页内容完整
- 图片正常显示
- CSS 样式正确

## 导出结果的使用方式

导出 ZIP 的 3 种使用场景:

1. **部署到任意静态服务器**(如 Nginx、Apache、阿里云 OSS)
   解压整个 ZIP → 上传到服务器根目录即可

2. **部署到 GitHub Pages**
   解压 → 推送到 `<username>.github.io` 仓库

3. **本地备份**
   保留 ZIP 作为当前站点的完整快照

导出产物的核心特性:
- **零依赖**:纯 HTML + CSS + JS,不需要 PHP/Python/Node.js
- **自包含**:所有资源在文件夹内,不依赖外部服务
- **平台无关**:脱离 mycompany.website 平台完全可运行

## 常见问题

| 问题 | 原因 | 修复 |
|------|------|------|
| ZIP 非常大(> 100MB) | 未压缩的视频/图片 | 检查 assets/ 目录大小 |
| 解压后中文文件名乱码 | ZIP 编码问题 | 用 UTF-8 解压(WinRAR 7-Zip 都支持) |
| 链接指向 localhost | 构建时 base_url 不为空 | 用 `base_url=''` 重新构建 |
| 图片路径以 / 开头 | 绝对路径在本地打不开 | 确认模板中图片路径是相对路径 |

## 关联技能

- `build-site`:先构建再导出
- `debug-site`:导出前排查构建问题
- `publish-flow`(规划中):完整 CDN 发布流程
