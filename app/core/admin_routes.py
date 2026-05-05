"""平台管理员后台路由. 挂在 /admin 下.

M1: 没有登录, 用 _require_admin() 简单断言任意 admin 用户存在.
M2 接登录后改成检查 session.role == 'admin'.
"""
from flask import Blueprint, abort, render_template

from .models import Site, User

bp = Blueprint('admin', __name__)


def _require_admin():
    """M1 占位: 找到任意一个 admin 用户即放行. M2 改 session 检查."""
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        abort(403, "没有管理员账号. 用 .venv/bin/flask --app run promote-admin EMAIL 创建一个.")
    return admin


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
