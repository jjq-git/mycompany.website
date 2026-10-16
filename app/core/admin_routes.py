"""平台管理员后台路由. 挂在 /admin 下."""
from datetime import datetime, timezone

from flask import Blueprint, abort, flash, redirect, request, session, url_for

from .db import db
from .models import AccountIdentity, AuditLog, OrganizationMember, Site, User, UserSession

bp = Blueprint('admin', __name__)


def _client_ip():
    """审计日志统一取客户端 IP，兼容反向代理。"""
    return request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()[:45]


def _revoke_all_sessions(user_id):
    """停用/删除用户后立即撤销其全部登录会话，避免已登录的 session 继续可用。"""
    UserSession.query.filter_by(user_id=user_id, revoked_at=None).update(
        {'revoked_at': datetime.now(timezone.utc)}
    )


def _tombstone_identifier(value, ts):
    """把邮箱/手机号改成可逆的“墓碑”标识，释放原值以便同一邮箱可重新注册。

    email 与 AccountIdentity.identifier 有全局唯一约束、且不区分删除状态；删除后若不释放，
    原邮箱会卡死（既登录不了也注册不了）。这里加 `deleted+<时间戳>+` 前缀腾出原值，
    原始邮箱完整保留在后缀中，需要人工救援时可去掉前缀还原。已带前缀的不重复包裹。
    """
    if not value or value.startswith('deleted+'):
        return value
    return f'deleted+{ts}+{value}'


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
    # 安全：平台管理员是内部运维角色，提权（user→admin）不在客户可见后台开放，
    # 只能走服务器命令行 flask promote-admin。Web 端仅允许降级（收敛权限）。
    if role == 'admin' and target.role != 'admin':
        flash('平台管理员需用命令行 flask promote-admin 提升，后台不开放提权', 'warning')
        return redirect(url_for('core.account', section='platform'))
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


@bp.route('/users/<int:user_id>/status', methods=['POST'])
def user_status_update(user_id):
    """停用 / 启用用户。停用只禁登录、保留全部数据，可随时启用恢复。"""
    admin = _require_admin()
    target = User.query.get_or_404(user_id)
    action = request.form.get('action', '').strip().lower()  # suspend / activate
    if action not in {'suspend', 'activate'}:
        abort(400)
    if action == 'suspend':
        # 护栏：不能停用自己，也不能停用最后一个有效管理员（与降级保护一致）
        if target.id == admin.id:
            flash('不能停用当前登录的自己', 'danger')
        elif target.status != 'active':
            flash('该用户已不是正常状态', 'info')
        elif target.role == 'admin' and User.query.filter_by(role='admin', status='active').count() <= 1:
            flash('不能停用最后一个有效平台管理员', 'danger')
        else:
            target.status = 'suspended'
            _revoke_all_sessions(target.id)  # 停用即刻踢下线，已登录 session 立即失效
            db.session.add(AuditLog(
                user_id=admin.id, action='platform.user.suspend',
                summary=f'停用用户 #{target.id}',
                details={'target_user_id': target.id}, ip_address=_client_ip(),
                created_at=datetime.now(timezone.utc),
            ))
            db.session.commit()
            flash('用户已停用', 'success')
    else:  # activate
        # 只把已停用（suspended）的用户改回 active；已软删除的用户走另外的恢复入口，不在此启用
        if target.status == 'active':
            flash('该用户已是正常状态', 'info')
        elif target.status == 'deleted':
            flash('该用户已删除，请先恢复再启用', 'warning')
        else:
            target.status = 'active'
            db.session.add(AuditLog(
                user_id=admin.id, action='platform.user.activate',
                summary=f'启用用户 #{target.id}',
                details={'target_user_id': target.id}, ip_address=_client_ip(),
                created_at=datetime.now(timezone.utc),
            ))
            db.session.commit()
            flash('用户已启用', 'success')
    return redirect(url_for('core.account', section='platform'))


@bp.route('/users/<int:user_id>/delete', methods=['POST'])
def user_delete(user_id):
    """删除用户：界面语义为“彻底移除”，删除后不再出现在用户列表、后台不提供恢复入口。
    实现仍是软删除（status=deleted + 名下站点一并软删），数据行与磁盘文件都保留在库中兜底，
    仅供误删时经数据库/命令行救回——绝不物理删除，避免连锁破坏站点/订单/审计等关联数据。
    停用（可逆封号）与删除（彻底移除）职责分明，不重叠。"""
    admin = _require_admin()
    target = User.query.get_or_404(user_id)
    # 护栏：不能删自己，不能删最后一个有效管理员
    if target.id == admin.id:
        flash('不能删除当前登录的自己', 'danger')
    elif target.role == 'admin' and User.query.filter_by(role='admin', status='active').count() <= 1:
        flash('不能删除最后一个有效平台管理员', 'danger')
    elif target.status == 'deleted':
        flash('该用户已删除', 'info')
    else:
        now = datetime.now(timezone.utc)
        ts = int(now.timestamp())
        target.status = 'deleted'
        _revoke_all_sessions(target.id)
        # 释放邮箱/身份：加墓碑前缀腾出原值，让同一邮箱可重新注册（原值保留在后缀中可救援）
        target.email = _tombstone_identifier(target.email, ts)
        for identity in AccountIdentity.query.filter_by(user_id=target.id).all():
            identity.identifier = _tombstone_identifier(identity.identifier, ts)
        # 名下未删站点一并软删；仅标记时间，磁盘 sites/<id>/ 文件原位保留，可恢复
        site_ids = [
            site.id for site in Site.query.filter_by(owner_id=target.id).filter(Site.soft_deleted_at.is_(None)).all()
        ]
        if site_ids:
            Site.query.filter(Site.id.in_(site_ids)).update(
                {Site.soft_deleted_at: now}, synchronize_session=False
            )
        # 移除组织成员身份：人删了，团队关系也断。所有成员查询都按 status=='active' 过滤，
        # 置为 removed 后该用户自动从各团队成员列表消失，不再是“幽灵成员”。
        # 他作为 owner 创建的组织与共享关系(OrganizationSite)保留：组织多为个人团队，
        # owner 删除后自然废弃；共享站点已随本人站点一并软删，团队他人本就看不到。
        member_removed = OrganizationMember.query.filter_by(
            user_id=target.id, status='active'
        ).update({OrganizationMember.status: 'removed'}, synchronize_session=False)
        db.session.add(AuditLog(
            user_id=admin.id, action='platform.user.delete',
            summary=f'删除用户 #{target.id}（软删除，连带 {len(site_ids)} 个站点、{member_removed} 个团队成员关系）',
            details={'target_user_id': target.id, 'soft_deleted_site_ids': site_ids,
                     'removed_memberships': member_removed},
            ip_address=_client_ip(), created_at=now,
        ))
        db.session.commit()
        flash(f'用户已彻底移除（连带下线 {len(site_ids)} 个站点）', 'success')
    return redirect(url_for('core.account', section='platform'))
