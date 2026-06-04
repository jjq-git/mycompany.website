# login.html：邮箱登录

`app/templates/auth/login.html` 是后台唯一的登录页面——输入邮箱 → 发送魔法链接 → 点击链接自动登录。不需要密码。

## 一、完整源码

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>登录 — {{ platform_domain }}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css">
</head>
<body class="bg-light min-vh-100 d-flex align-items-center">
  <main class="container" style="max-width: 460px;">

    {# 品牌区 #}
    <div class="text-center mb-4">
      <div class="fw-bold fs-3">{{ platform_domain }}</div>
      <p class="text-muted mb-0">用邮箱魔法链接登录，无需密码</p>
    </div>

    {# flashed messages #}
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="alert alert-{{ category }} py-2">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    {# 登录表单 #}
    <section class="card shadow-sm border-0">
      <div class="card-body p-4">
        <form method="post">
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
          <label class="form-label" for="email">邮箱地址</label>
          <input class="form-control form-control-lg" id="email" name="email" type="email"
                 value="{{ email or '' }}" placeholder="you@example.com" required autofocus>
          <button class="btn btn-primary btn-lg w-100 mt-3" type="submit">发送登录链接</button>
        </form>

        {# 开发环境快捷入口 #}
        {% if magic_link %}
        <div class="alert alert-secondary mt-4 mb-0 small">
          <div class="fw-semibold mb-1">开发环境快捷入口</div>
          <a href="{{ magic_link }}" class="text-break">{{ magic_link }}</a>
        </div>
        {% endif %}
      </div>
    </section>

    {# 提示文案 #}
    <p class="text-center text-muted small mt-3 mb-0">
      链接 15 分钟内有效，点击后自动登录。
    </p>
  </main>
</body>
</html>
```

## 二、页面组成

| 区域 | 内容 | 说明 |
| --- | --- | --- |
| 品牌区 | `platform_domain` + 副标题 | 标题用 `fw-bold fs-3`，副标题解释"无需密码" |
| 消息区 | `get_flashed_messages()` | 发送成功/失败/过期等提示 |
| 登录表单 | 邮箱 input + CSRF hidden + 提交按钮 | `form-control-lg` 大号输入框 + `btn-lg` 大号按钮 |
| 开发入口 | magic_link 直链 | 仅开发环境显示，生产环境不渲染 |
| 底部提示 | 15 分钟有效期说明 | `text-muted small` |

## 三、布局

```text
┌─────────────────────────────────┐
│                                 │
│        mycompany.website        │  ← 品牌名（Flask 注入 platform_domain）
│     用邮箱魔法链接登录，无需密码   │  ← 副标题
│                                 │
│  ┌───────────────────────────┐  │
│  │  邮箱地址                  │  │  ← 卡片（card shadow-sm border-0）
│  │  [you@example.com     ]  │  │  ← form-control-lg
│  │  [══════ 发送登录链接 ════]  │  │  ← btn-primary btn-lg w-100
│  │                           │  │
│  │  ┌ 开发环境快捷入口 ───┐   │  │  ← 仅 magic_link 存在时显示
│  │  │ http://localhost... │   │  │
│  │  └────────────────────┘   │  │
│  └───────────────────────────┘  │
│                                 │
│    链接 15 分钟内有效，点击后自动登录 │  ← 底部提示
│                                 │
└─────────────────────────────────┘
```

- `body`：`bg-light min-vh-100 d-flex align-items-center`——浅灰背景，垂直居中
- `main`：`max-width: 460px`——限制卡片宽度，小屏自适应
- 卡片：`shadow-sm border-0`——轻微阴影，无边框

## 四、CSRF 保护

```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

传统 form POST，用 hidden input 传 CSRF token（Flask-WTF 校验）。登录页不走 AJAX，不需要 fetch 包装。

## 五、开发环境快捷入口

```jinja2
{% if magic_link %}
<div class="alert alert-secondary mt-4 mb-0 small">
  <div class="fw-semibold mb-1">开发环境快捷入口</div>
  <a href="{{ magic_link }}" class="text-break">{{ magic_link }}</a>
</div>
{% endif %}
```

生产环境发邮件，`magic_link` 为 `None`，整块不渲染。开发环境（如未配 SMTP）Flask 把 `magic_link` 作为变量传入模板，直接显示在页面上方便点击。

> `magic_link` 是完整 URL（如 `http://localhost:5000/auth/magic/xxx`），不是相对路径——因为邮件里的链接也必须是完整 URL。

## 六、登录流程

```text
用户                      Flask                       邮件/浏览器
 │                         │                             │
 │  GET /auth/login        │                             │
 │ ──────────────────────→ │                             │
 │ ←────── 登录页 ──────── │                             │
 │                         │                             │
 │  输入邮箱 → POST         │                             │
 │ ──────────────────────→ │                             │
 │                         │  生成 token（SHA-256 哈希）   │
 │                         │  存 token → 拼 magic_link    │
 │                         │                             │
 │                         │  开发环境：                   │
 │                         │  重定向回 /auth/login        │
 │                         │  带 magic_link 参数          │
 │                         │                             │
 │                         │  生产环境：                   │
 │                         │ ── 发送邮件（含 magic_link）─→ │
 │                         │                             │
 │  看到"已发送"提示 或       │                             │
 │  直接点击 magic_link      │                             │
 │ ────────────────────────────────────────────────────→ │
 │                         │  验证 token                  │
 │                         │  设置 session                │
 │                         │  重定向 → 后台总览            │
```

1. GET `/auth/login` → 渲染登录页
2. POST `/auth/login`（email + csrf_token）→ Flask 生成 token 存 DB（SHA-256 哈希），拼 magic_link
3. 开发环境：不发邮件，直接重定向回登录页，`magic_link` 参数渲染在页面上
4. 生产环境：发邮件（含 link），登录页显示"邮件已发送"的 flash message
5. 点击 magic_link → Flask 校验 token（查 DB、比哈希、验过期）→ 设 `session` → 重定向到后台总览

## 七、关键规则

- **不设密码**——邮箱即身份，magic link 是唯一登录方式。免去密码管理、重置、泄露的所有问题。
- **token 存 SHA-256 哈希**——数据库中不存明文 token，只存哈希。
- **15 分钟过期**——`now - token.created_at > 15min` 则拒绝，需重新发送。
- **登录页不继承 base.html**——独立 `<html>` 文档，不加载 admin.css、admin.js、侧栏等后台资源。
- **开发环境 magic_link 直接显示**——`{% if magic_link %}` 控制，生产环境不渲染。
- **CSRF 用传统 hidden input**——不走 AJAX，不需要 fetch 包装。
- **输入框 `autofocus`**——页面加载后光标自动进入邮箱输入框。
- **`type="email"`**——移动端弹出邮箱键盘（含 @ 键），浏览器自带格式校验。
