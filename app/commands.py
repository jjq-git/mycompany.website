"""开发期 CLI 命令.

用法: flask --app run <command>
"""
import re

import click
from flask.cli import with_appcontext

from .core.builder import build_site
from .core.db import db
from .core.models import SLUG_RESERVED, Site, Template, User
from .core.site_storage import copy_seed_data, init_site_folder, site_root
from .core.template_loader import scan_templates


SLUG_PATTERN = re.compile(r'^[a-z0-9][a-z0-9-]{1,28}[a-z0-9]$')


def init_app(app):
    app.cli.add_command(scan_templates_cmd)
    app.cli.add_command(create_user_cmd)
    app.cli.add_command(create_site_cmd)
    app.cli.add_command(list_sites_cmd)
    app.cli.add_command(list_users_cmd)
    app.cli.add_command(promote_admin_cmd)
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
@with_appcontext
def create_user_cmd(email):
    """创建用户 (开发用, 跳过邮件验证)."""
    if User.query.filter_by(email=email).first():
        click.echo(f'用户已存在: {email}')
        return
    user = User(email=email, status='active')
    db.session.add(user)
    db.session.commit()
    click.echo(f'已创建用户: id={user.id}, email={email}')


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

    site = Site(
        owner_id=owner.id,
        name=name,
        slug=slug,
        folder_path='',  # 拿到 id 后再填
        template_name=tpl.name,
        template_version=tpl.current_version,
        cdn_provider='aliyun',
    )
    db.session.add(site)
    db.session.flush()  # 拿 id

    site.folder_path = f'sites/{site.id}'
    db.session.commit()

    init_site_folder(site.id)
    copied = copy_seed_data(site.id, tpl.name)

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
@click.argument('email')
@with_appcontext
def promote_admin_cmd(email):
    """把指定邮箱的用户提升为平台管理员 (role=admin)."""
    user = User.query.filter_by(email=email).first()
    if not user:
        click.echo(f'用户不存在: {email}')
        return
    if user.role == 'admin':
        click.echo(f'已经是 admin: {email}')
        return
    user.role = 'admin'
    db.session.commit()
    click.echo(f'已将 {email} 提升为 admin')


@click.command('build-site')
@click.argument('site_id', type=int)
@with_appcontext
def build_site_cmd(site_id):
    """生成静态站点到 output/<site_id>/."""
    out = build_site(site_id)
    click.echo(f'已生成: {out}')
