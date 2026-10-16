"""开发期 CLI 命令.

用法: flask --app run <command>
"""
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

import click
import yaml
from flask import current_app
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from .core.builder import build_site
from .core.db import db
from .core.models import (AccountEntitlement, AccountIdentity, PasswordCredential,
                          SLUG_RESERVED, Site, Template, User)
from .core.site_storage import (copy_seed_data, init_site_folder, read_yaml,
                                site_root, write_yaml)
from .core.template_loader import scan_templates


SLUG_PATTERN = re.compile(r'^[a-z0-9][a-z0-9-]{1,28}[a-z0-9]$')


def _template_language_options(template_name):
    """读取模板语言配置；CLI 建站必须与后台建站保持相同的数据模型。"""
    meta_path = Path(current_app.config['TEMPLATES_DIR']) / template_name / 'meta.yaml'
    meta = yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {} if meta_path.exists() else {}
    languages = meta.get('languages') or [{'code': 'zh-CN'}]
    codes = list(dict.fromkeys(
        item.get('code') for item in languages
        if isinstance(item, dict) and item.get('code')
    )) or ['zh-CN']
    default_language = meta.get('default_language') or codes[0]
    if default_language not in codes:
        default_language = codes[0]
    return codes, default_language


def init_app(app):
    app.cli.add_command(scan_templates_cmd)
    app.cli.add_command(create_user_cmd)
    app.cli.add_command(create_site_cmd)
    app.cli.add_command(list_sites_cmd)
    app.cli.add_command(list_users_cmd)
    app.cli.add_command(promote_admin_cmd)
    app.cli.add_command(demote_admin_cmd)
    app.cli.add_command(ensure_admin_cmd)
    app.cli.add_command(build_site_cmd)


@click.command('scan-templates')
@with_appcontext
def scan_templates_cmd():
    """扫描 site_templates/ 同步到数据库."""
    templates = scan_templates()
    if not templates:
        click.echo('未找到任何模板。请确认 site_templates/<name>/meta.yaml 存在。')
        return
    click.echo(f'同步了 {len(templates)} 个模板:')
    for t in templates:
        click.echo(f'  - {t.name} ({t.display_name}) [{t.industry}]')


@click.command('create-user')
@click.argument('email')
@click.option('--password', default=None, help='指定登录密码；留空时为新账号生成一次性密码。')
@with_appcontext
def create_user_cmd(email, password):
    """创建或补全一个可实际登录的账号。"""
    normalized_email = (email or '').strip().lower()
    if not normalized_email:
        raise click.ClickException('邮箱不能为空')

    now = datetime.now(timezone.utc)
    identity = AccountIdentity.query.filter_by(
        identity_type='email', identifier=normalized_email
    ).first()
    user = identity.user if identity else User.query.filter_by(email=normalized_email).first()
    created = user is None
    if created:
        user = User(email=normalized_email, status='active', email_verified_at=now)
        db.session.add(user)
        db.session.flush()
    else:
        user.email = normalized_email
        user.status = 'active'
        user.email_verified_at = user.email_verified_at or now

    if identity is None:
        identity = AccountIdentity(
            user_id=user.id,
            identity_type='email',
            identifier=normalized_email,
            is_primary=True,
            verified_at=now,
        )
        db.session.add(identity)
    else:
        identity.is_primary = True
        identity.verified_at = identity.verified_at or now

    credential = PasswordCredential.query.filter_by(user_id=user.id).first()
    generated_password = None
    if credential is None:
        generated_password = password or secrets.token_urlsafe(12)
        db.session.add(PasswordCredential(
            user_id=user.id,
            password_hash=generate_password_hash(generated_password),
            password_changed_at=now,
        ))
    elif password:
        credential.password_hash = generate_password_hash(password)
        credential.password_changed_at = now

    entitlement = AccountEntitlement.query.filter_by(user_id=user.id).first()
    if entitlement is None:
        db.session.add(AccountEntitlement(user_id=user.id, can_create_sites=True))
    else:
        entitlement.can_create_sites = True

    db.session.commit()
    click.echo(f"{'已创建' if created else '已更新'}用户: {normalized_email}")
    if generated_password and not password:
        click.echo(f'一次性登录密码: {generated_password}')
    elif password:
        click.echo('登录密码已设置')
    else:
        click.echo('已有密码保持不变')


@click.command('create-site')
@click.argument('owner_email')
@click.argument('slug')
@click.option('--template', default=None, help='模板名 (默认用第一个)')
@click.option('--name', default='我的网站', help='站点名 (店主可见)')
@with_appcontext
def create_site_cmd(owner_email, slug, template, name):
    """创建站点 + 文件夹 + 复制模板的 seed_data."""
    # 校验 slug
    if not SLUG_PATTERN.match(slug):
        click.echo(f'slug 格式不合法 (要求 [a-z0-9-], 3-30 字符, 不以 - 开头/结尾): {slug}')
        return
    if slug in SLUG_RESERVED:
        click.echo(f'slug 是保留字: {slug}')
        return

    owner = User.query.filter_by(email=owner_email).first()
    if not owner:
        click.echo(f'用户不存在: {owner_email}')
        return

    if Site.query.filter_by(slug=slug).first():
        click.echo(f'slug 已被占用: {slug}')
        return

    if template:
        tpl = Template.query.filter_by(name=template).first()
        if not tpl:
            click.echo(f'模板不存在: {template}')
            return
    else:
        tpl = Template.query.first()
        if not tpl:
            click.echo('数据库里没有模板, 先运行: flask --app run scan-templates')
            return

    enabled_languages, default_language = _template_language_options(tpl.name)

    site = Site(
        owner_id=owner.id,
        name=name,
        slug=slug,
        folder_path='',  # 拿到 id 后再填
        template_name=tpl.name,
        template_version=tpl.current_version,
        default_language=default_language,
        enabled_languages=enabled_languages,
        cdn_provider='aliyun',
    )
    db.session.add(site)
    db.session.flush()  # 拿 id

    site.folder_path = f'sites/{site.id}'
    # #12: 文件初始化全部成功后才 commit, 失败回滚, 不留"DB 有、文件无"的半成品站。
    try:
        init_site_folder(site.id)
        copied = copy_seed_data(site.id, tpl.name)
        settings = read_yaml(site.id, 'settings.yaml', default={}) or {}
        header = settings.setdefault('header', {})
        header['enabled_languages'] = enabled_languages
        language_switcher = header.setdefault('language_switcher', {})
        language_switcher['enabled'] = len(enabled_languages) > 1
        write_yaml(site.id, 'settings.yaml', settings)
    except Exception as exc:
        db.session.rollback()
        raise click.ClickException(f'建站文件初始化失败, 已回滚: {exc}')
    db.session.commit()

    click.echo(f'已创建站点: id={site.id}, slug={slug}, 模板={tpl.name}')
    click.echo(f'文件夹: {site_root(site.id)}')
    click.echo(f'seed_data: {"已复制" if copied else "模板无 seed_data, 跳过"}')


@click.command('list-sites')
@with_appcontext
def list_sites_cmd():
    """列出所有站点."""
    sites = Site.query.order_by(Site.id).all()
    if not sites:
        click.echo('暂无站点。')
        return
    click.echo(f'共 {len(sites)} 个站点:')
    for s in sites:
        click.echo(f'  id={s.id}  slug={s.slug}  template={s.template_name}  status={s.status}  owner={s.owner.email}')


@click.command('list-users')
@with_appcontext
def list_users_cmd():
    """列出所有用户."""
    users = User.query.order_by(User.id).all()
    if not users:
        click.echo('暂无用户。')
        return
    click.echo(f'共 {len(users)} 个用户:')
    for u in users:
        sites = Site.query.filter_by(owner_id=u.id).count()
        click.echo(f'  id={u.id}  email={u.email}  role={u.role}  status={u.status}  sites={sites}')


@click.command('promote-admin')
@click.argument('identifier')
@with_appcontext
def promote_admin_cmd(identifier):
    """按邮箱或手机号把用户提升为平台管理员。"""
    identity = AccountIdentity.query.filter_by(identifier=identifier.strip().lower()).first()
    user = identity.user if identity else User.query.filter_by(email=identifier.strip().lower()).first()
    if not user:
        click.echo(f'用户不存在: {identifier}')
        return
    if user.role == 'admin':
        click.echo(f'已经是 admin: {identifier}')
        return
    user.role = 'admin'
    db.session.commit()
    click.echo(f'已将 {identifier} 提升为 admin')


@click.command('demote-admin')
@click.argument('identifier')
@with_appcontext
def demote_admin_cmd(identifier):
    """把平台管理员降为普通用户；至少保留一个管理员。"""
    identity = AccountIdentity.query.filter_by(identifier=identifier.strip().lower()).first()
    user = identity.user if identity else User.query.filter_by(email=identifier.strip().lower()).first()
    if not user:
        raise click.ClickException(f'用户不存在: {identifier}')
    if user.role != 'admin':
        click.echo(f'已经是普通用户: {identifier}')
        return
    if User.query.filter_by(role='admin', status='active').count() <= 1:
        raise click.ClickException('不能降级最后一个有效平台管理员')
    user.role = 'user'
    db.session.commit()
    click.echo(f'已将 {identifier} 降为 user')


@click.command('ensure-admin')
@click.argument('email')
@click.argument('password')
@with_appcontext
def ensure_admin_cmd(email, password):
    """创建或重置一个可密码登录的平台管理员（新部署初始化用）。

    登录改为账号密码后，能登录的账号需要三件套：User + AccountIdentity + PasswordCredential，
    而 create-user 只建 User。本命令一次建全并设 active/admin；账号已存在则重置密码，幂等可重跑。
    云服务器/新机器首次部署后跑一次即可登录，无需手改数据库。

    用法: flask --app run ensure-admin <邮箱> <密码>
    """
    email = email.strip().lower()
    now = datetime.now(timezone.utc)

    # User：按邮箱或已有身份定位，没有则新建；确保 active + admin
    identity = AccountIdentity.query.filter_by(identifier=email).first()
    user = identity.user if identity else User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, status='active', role='admin', email_verified_at=now)
        db.session.add(user)
        db.session.flush()
        click.echo(f'新建 User id={user.id}')
    else:
        # 冲突保护：邮箱身份若挂在别的账号上，不擅自改动，交人工核对
        if identity and identity.user_id != user.id:
            raise click.ClickException(f'邮箱 {email} 身份属于 user_id={identity.user_id}，请人工核对')
        user.status, user.role = 'active', 'admin'
        click.echo(f'复用 User id={user.id}（已置为 active/admin）')

    # AccountIdentity：邮箱身份，已验证、设为主
    if not identity or identity.user_id != user.id:
        db.session.add(AccountIdentity(user_id=user.id, identity_type='email', identifier=email,
                                       verified_at=now, is_primary=True))
        click.echo('新建 AccountIdentity（email，已验证，主）')
    else:
        identity.verified_at = identity.verified_at or now
        identity.is_primary = True

    # PasswordCredential：设置或重置密码
    cred = PasswordCredential.query.filter_by(user_id=user.id).first()
    if not cred:
        db.session.add(PasswordCredential(user_id=user.id, password_hash=generate_password_hash(password),
                                          password_changed_at=now))
        click.echo('新建密码凭据')
    else:
        cred.password_hash = generate_password_hash(password)
        cred.password_changed_at = now
        click.echo('已重置密码')

    # AccountEntitlement：补齐建站资格记录（admin 本就短路放行，这里保持数据完整）
    if not AccountEntitlement.query.filter_by(user_id=user.id).first():
        db.session.add(AccountEntitlement(user_id=user.id, can_create_sites=True))

    db.session.commit()
    click.echo(f'完成：{email} 现为 active 平台管理员，可用密码登录。')


@click.command('build-site')
@click.argument('site_id', type=int)
@click.option('--preview', is_flag=True, help='使用 /preview/<slug> 作为 base_url，方便开发时通过 Flask dev server 预览')
@with_appcontext
def build_site_cmd(site_id, preview):
    """生成静态站点到 output/<site_id>/. 加 --preview 后可通过 /preview/<slug>/ 在浏览器预览."""
    site = db.session.get(Site, site_id)
    if not site:
        raise click.ClickException(f'站点不存在: {site_id}')
    base_url = f'/preview/{site.slug}' if preview else ''
    # --preview 是开发预览，跳过昂贵的死链校验；正式构建(无 --preview)保留校验拦截坏链。
    out = build_site(site_id, base_url=base_url, validate_links=not preview)
    if preview:
        click.echo(f'已生成: {out}')
        click.echo(f'预览: http://localhost:5000/preview/{site.slug}/')
    else:
        click.echo(f'已生成: {out}')
