# users.html：用户管理

`app/templates/admin/users.html` 是平台管理员后台的用户列表页——查看所有注册用户、角色、状态、站点数、登录时间。**独立页面，不继承 `base.html`**。

## 一、完整源码

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>用户管理 — {{ platform_domain }} 管理后台</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/admin.css') }}">
  <style>
    .topbar.admin { background: #1a1a2e; color: #fff; }
    .topbar.admin .logo { color: #fff; }
    .role-badge { display: inline-block; padding: 2px 8px; border-radius: 10px;
                  font-size: 12px; font-weight: 500; }
    .role-admin { background: #fef3c7; color: #92400e; }
    .role-owner { background: #e0e7ff; color: #3730a3; }
    .status-active { color: var(--success); }
    .status-suspended { color: var(--danger); }
  </style>
</head>
<body>

<header class="topbar admin">
  <div class="logo">{{ platform_domain }} · 管理后台</div>
  <div class="spacer"></div>
  <span style="opacity: 0.7; margin-right: 12px;">{{ user.email }}</span>
  <a class="btn" href="{{ url_for('core.overview') }}">回到店主后台</a>
</header>

<main class="main" style="margin-left: 0; padding: 24px 32px;">
  <h1 class="page-title">用户管理</h1>
  <p class="page-subtitle">共 {{ rows|length }} 个用户</p>

  <table class="table" style="...">
    <thead>
      <tr>
        <th>ID</th>
        <th>邮箱</th>
        <th>角色</th>
        <th>状态</th>
        <th>站点</th>
        <th>注册时间</th>
        <th>最后登录</th>
      </tr>
    </thead>
    <tbody>
      {% for r in rows %}
      <tr>
        <td>{{ r.id }}</td>
        <td>{{ r.email }}</td>
        <td><span class="role-badge role-{{ r.role }}">{{ r.role }}</span></td>
        <td class="status-{{ r.status }}">{{ r.status }}</td>
        <td>{{ r.site_count }}</td>
        <td>{{ r.created_at.strftime(...) }}</td>
        <td>{{ r.last_login_at.strftime(...) or '从未登录' }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</main>

</body>
</html>
```

## 二、页面组成

| 区域 | 内容 | 说明 |
| --- | --- | --- |
| 顶栏 | `platform_domain` · 管理后台 + 当前用户邮箱 + "回到店主后台"链接 | 深色背景 `#1a1a2e`，和店主后台的 `admin-header` 不同 |
| 标题区 | "用户管理" + 用户总数 | `rows|length` 实时计数 |
| 用户表格 | 7 列表格 | ID、邮箱、角色、状态、站点数、注册时间、最后登录 |

## 三、表格列说明

| 列 | 数据来源 | 渲染方式 |
| --- | --- | --- |
| ID | `r.id` | 灰色文字（`.muted`） |
| 邮箱 | `r.email` | `<strong>` 加粗 |
| 角色 | `r.role` | `.role-badge` 彩色标签：admin 黄底褐字、owner 蓝底靛字 |
| 状态 | `r.status` | `status-{{ r.status }}` 着色：active 绿色、suspended 红色 |
| 站点 | `r.site_count` | 纯数字 |
| 注册时间 | `r.created_at` | `strftime('%Y-%m-%d %H:%M')`，无数据显示 `-` |
| 最后登录 | `r.last_login_at` | 同上，从未登录显示"从未登录" |

## 四、角色标签

```css
.role-badge    { display: inline-block; padding: 2px 8px; border-radius: 10px;
                 font-size: 12px; font-weight: 500; }
.role-admin    { background: #fef3c7; color: #92400e; }   /* 黄色底 + 棕色字 */
.role-owner    { background: #e0e7ff; color: #3730a3; }   /* 蓝色底 + 靛色字 */
```

模板里 `class="role-badge role-{{ r.role }}"` 直接拼角色名——目前只有 `admin` 和 `owner` 两种角色。新增角色只需在 CSS 里加对应的 `.role-xxx` 类。

## 五、后端路由

```python
# app/core/admin_routes.py
@bp.route('/users')
def users():
    admin = _require_admin()
    rows = []
    for u in User.query.order_by(User.id).all():
        rows.append({
            'id': u.id,
            'email': u.email,
            'role': u.role,
            'status': u.status,
            'site_count': Site.query.filter_by(owner_id=u.id).count(),
            'created_at': u.created_at,
            'last_login_at': u.last_login_at,
        })
    return render_template('admin/users.html', user=admin, rows=rows, active='admin_users')
```

### 5.1 鉴权（M1 占位）

```python
def _require_admin():
    """M1 占位: 找到任意一个 admin 用户即放行. M2 改 session 检查."""
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        abort(403, "...")
    return admin
```

当前不检查登录态——只要 DB 里存在至少一个 admin 用户就放行。M2 接入登录后改为检查 `session.role == 'admin'`。

### 5.2 传给模板的变量

| 变量 | 类型 | 说明 |
| --- | --- | --- |
| `user` | User ORM 对象 | 第一个 admin 用户，顶栏显示邮箱 + 传回 `/core/overview` |
| `rows` | list[dict] | 所有用户列表，每项含 id/email/role/status/site_count/created_at/last_login_at |
| `active` | str | `'admin_users'`，标记当前导航项（当前页面未使用） |

### 5.3 站点计数

```python
'site_count': Site.query.filter_by(owner_id=u.id).count()
```

每个用户一行一次 COUNT 查询——当前用户量小没问题，量大后可用 `func.count()` group by 批量取。

## 六、顶栏

```html
<header class="topbar admin">
  <div class="logo">{{ platform_domain }} · 管理后台</div>
  <div class="spacer"></div>
  <span>{{ user.email }}</span>
  <a class="btn" href="{{ url_for('core.overview') }}">回到店主后台</a>
</header>
```

| 元素 | 说明 |
| --- | --- |
| Logo | `platform_domain` · 管理后台 |
| 当前用户邮箱 | 透明度 0.7，告知当前以哪个 admin 身份查看 |
| 回到店主后台 | 跳转 `core.overview`（即店主后台总览页） |

只有一条链接——回店主后台。管理后台目前只有用户列表一个功能，不需要侧栏。

## 七、和店主后台 base.html 的区别

| | 店主后台 `base.html` | 管理员 `users.html` |
| --- | --- | --- |
| 文件 | `app/templates/base.html` | `app/templates/admin/users.html` |
| 鉴权 | 正常登录流程（magic link） | M1 占位（有 admin 用户即放行） |
| 布局 | 三栏（左导航 / 中预览 / 右属性面板） | 单栏（顶栏 + 全宽表格） |
| CSS | BS5 CDN + admin.css + 内联颜色注入 | 仅 admin.css + 页面内联 `<style>` |
| JS | Popper + BS5 JS + 大量内联逻辑 | 无 JS |
| 顶栏 | `admin-header`（SVG logo、站点切换、操作按钮） | `topbar admin`（深色背景、平台名、回店主后台链接） |
| `platform_domain` | 用（标题后缀 + 顶栏品牌名） | 用（标题后缀 + 顶栏 Logo） |
| `admin_primary` 颜色变量 | 注入 BS5 组件色 | 不注入 |

## 八、关键规则

- **不继承 base.html**——管理后台和店主后台是两个独立空间，权限模型不同（M2 后更明显），不共享外壳。
- **不加载 BS5 CDN**——页面样式极简（顶栏 + 表格），`admin.css` 里的基础变量（`--success` / `--danger` / `--border`）够用，不引 BS5。
- **角色标签用 class 拼角色名**——`.role-badge role-{{ r.role }}`，CSS 按角色定义颜色，新增角色只加 CSS。
- **站点计数每行一次查询**——当前用户量小没问题，量大后改为 JOIN + GROUP BY。
- **M1 鉴权不查登录态**——当前只校验 DB 里有 admin 用户，M2 改为 `session.role == 'admin'`。
- **无分页、无搜索、无排序**——MVP 阶段用户少，一张表格全量展示即可。
