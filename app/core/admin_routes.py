"""平台管理员后台路由. 挂在 /admin 下."""
from datetime import datetime, timezone

from flask import Blueprint, abort, flash, redirect, request, session, url_for

from .db import db
from .models import AuditLog, User

bp = Blueprint('admin', __name__)


def _require_admin():
    """只允许当前登录的 admin 用户访问平台管理页."""
    user_id = session.get('user_id')
    if not user_id:
        abort(401)
    admin = User.query.get(user_id)
    if not admin or admin.role != 'admin' or admin.status != 'active':
        abort(403, "需要管理员权限. 用 python -m flask --app run promote-admin <邮箱或手机号> 提升账号.")
    return admin


@bp.route('/users')
def users():
    _require_admin()
    return redirect(url_for('core.account', section='platform'))


@bp.route('/users/<int:user_id>/role', methods=['POST'])
def user_role_update(user_id):
    admin = _require_admin()
    target = User.query.get_or_404(user_id)
    role = request.form.get('role', '').strip().lower()
    if role not in {'user', 'admin'}:
        abort(400)
    if target.id == admin.id and role != 'admin':
        flash('不能在当前会话中降级自己的平台管理员角色', 'danger')
    elif target.role == 'admin' and role == 'user' and User.query.filter_by(role='admin', status='active').count() <= 1:
        flash('不能降级最后一个有效平台管理员', 'danger')
    elif target.role == role:
        flash('平台角色没有变化', 'info')
    else:
        old_role = target.role
        target.role = role
        db.session.add(AuditLog(
            user_id=admin.id, action='platform.user.role.update',
            summary=f'调整用户 #{target.id} 平台角色：{old_role} → {role}',
            details={'target_user_id': target.id, 'old_role': old_role, 'new_role': role},
            ip_address=(request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()[:45]),
            created_at=datetime.now(timezone.utc),
        ))
        db.session.commit()
        flash('平台角色已更新', 'success')
    return redirect(url_for('core.account', section='platform'))
