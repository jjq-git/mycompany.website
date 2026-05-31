# 域名与 URL 规划

整站使用 `mycompany.website` 主域，按子域分配不同用途。

## 一、子域分配

```text
mycompany.website                       平台介绍站（落地页）

<slug>.mycompany.website                用户子域名（自动分配）
                                        例: com-a.mycompany.website

docs.mycompany.website                  平台文档站（这个目录的内容）
design.mycompany.website                用户后台（在线设计 / 编辑器）
```

`docs` / `design` / `www` / `api` / `admin` / `app` / `cdn` / `assets` / `mail` / `blog` / `status` / `help` / `about` 等都是**保留子域**，不能被用户注册成 slug（`Site.name` 见 [database.md](database.md)；保留字清单 `SLUG_RESERVED` 见 [app/core/models.py](../app/core/models.py)）。

## 二、用户 slug 规则

- 字符集：`[a-z0-9-]`（小写字母、数字、连字符）
- 长度：3 ~ 30
- **不允许下划线** —— DNS 主机名 RFC 1123 不支持，部分 SSL 证书和邮件系统会拒
- 不允许以 `-` 开头或结尾
- 不能命中保留列表

例：`com-a` ✓ &nbsp; `com_a` ✗ &nbsp; `-com` ✗ &nbsp; `docs` ✗（保留）

## 三、URL 路径与多语言

**默认语言由站点的 `default_language` 决定**（即站点的源语言 —— 用户建站时选的、用来填内容的语言；平台没有固定的默认语言）。所有用户站点用相同的语言路径策略：

```text
com-a.mycompany.website/en/             英文
com-a.mycompany.website/zh/             中文
com-a.mycompany.website/                语言选择首页（hreflang + 即时 JS 跳转）
```

- 不在根路径直接渲染任何语言版本，**所有内容都在 `/en/`、`/zh/` 之类的子路径里**
- 这样切语言只是路径替换，简单直接
- 根路径生成一个"语言选择首页"，含 `hreflang` 标签 + JS 即时跳转 + `<meta refresh>` 兜底 + 给爬虫看的可读链接（详见 [seo.md](seo.md)）。**不要用纯 JS 跳转**，否则不跑 JS 的 LLM 爬虫拿到空页面

文档站同规则：

```text
docs.mycompany.website/en/              英文文档（默认）
docs.mycompany.website/zh/              中文文档
docs.mycompany.website/                 跳转到 /en/
```

用户后台例外：

```text
design.mycompany.website/               Flask SSR 多页应用，语言不进路径（无前缀）
```

后台是动态应用而不是静态发布产物，路径参数已经留给业务逻辑（路由、站点 ID）。
语言不用路径前缀，按用户偏好（`User.preferred_lang`）+ 浏览器 `Accept-Language` 决定，详见 [admin-i18n.md](admin-i18n.md)。

## 四、预览 URL

预览要和真实站点视觉、链接、字体子集化、CDN 路径一致，因此**预览放在主子域下**，不在 design 域：

```text
com-a.mycompany.website/_preview/<token>/        预览未发布的版本
com-a.mycompany.website/_preview/<token>/en/     预览的英文版
com-a.mycompany.website/_preview/<token>/zh/     预览的中文版
```

- `<token>` 是一次性预览 token，过期后 404
- token 由 design 后台生成；用户在后台点"预览"会跳到这个 URL
- `_preview` 也加入保留 slug 列表，用户不能用

放在 design 域下（如 `design.mycompany.website/preview/com-a/`）的隐患：

- 字体跨域加载、相对路径行为可能跟生产不一致
- "开发时好看，发布后链接挂了"的坑

## 五、SSL 证书

`*.mycompany.website` 通配符证书。

- **签发方**：Let's Encrypt（免费、无配额、ACME 自动化）
- **验证方式**：DNS-01（通配符证书**不能**用 HTTP-01）
- **工具**：`acme.sh` 或 `certbot` + 阿里云 DNS API 插件
- **续期**：90 天周期，自动续

详见 [infrastructure.md](infrastructure.md)。

## 六、自定义域名（Phase 2 之后）

用户带自己的域名（例：`com-a.com` 直接指向我们的 CDN）：

- 用户在后台填入自己的域名
- 用户在自己的 DNS 后台加 CNAME 指向 `com-a.mycompany.website`
- 我们的 CDN 配置接受这个自定义域，签 Let's Encrypt 证书（不再是通配符，是按域单签）
- 路径规则不变，仍然是 `/en/`、`/zh/`

MVP 阶段不做。
