"""平台管理员后台路由. 挂在 /admin 下."""
from flask import Blueprint, abort, render_template, session

from .models import Site, User

bp = Blueprint('admin', __name__)


def _require_admin():
    """只允许当前登录的 admin 用户访问平台管理页."""
    user_id = session.get('user_id')
    if not user_id:
        abort(401)
    admin = User.query.get(user_id)
    if not admin or admin.role != 'admin' or admin.status != 'active':
        abort(403, "需要管理员权限. 用 .venv/bin/flask --app run promote-admin EMAIL 提升账号.")
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
