"""平台级数据模型. 见 docs/database.md.

只存平台级数据 (账号、订阅、域名、发布历史等).
店主网站的内容在 sites/<id>/*.yaml.
"""
from datetime import datetime, timezone

from .db import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    """店主账号. 邮箱魔法链接登录, 不存密码."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    email_verified_at = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(20), default='active', nullable=False)  # active / suspended / deleted
    role = db.Column(db.String(20), default='user', nullable=False)  # user / admin（平台级）
    display_name = db.Column(db.String(80))
    preferred_lang = db.Column(db.String(5), default='zh-CN', nullable=False)
    last_login_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class LoginToken(db.Model):
    """魔法链接 token. 一次性使用, 默认 15 分钟过期."""
    __tablename__ = 'login_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    token_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)  # SHA-256
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at = db.Column(db.DateTime(timezone=True))
    ip_address = db.Column(db.String(45))  # IPv6 最长 45 字符
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class AccountIdentity(db.Model):
    """用户可登录身份；邮箱和手机号使用同一套唯一性与验证规则。"""
    __tablename__ = 'account_identities'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    identity_type = db.Column(db.String(10), nullable=False)  # email / phone
    identifier = db.Column(db.String(255), nullable=False, unique=True, index=True)
    verified_at = db.Column(db.DateTime(timezone=True))
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('identities', cascade='all, delete-orphan'))


class PasswordCredential(db.Model):
    """独立保存密码哈希，避免账户资料模型与认证实现耦合。"""
    __tablename__ = 'password_credentials'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    password_changed_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('password_credential', uselist=False, cascade='all, delete-orphan'))


class VerificationCode(db.Model):
    """注册、找回和敏感操作的一次性验证码；只存哈希。"""
    __tablename__ = 'verification_codes'

    id = db.Column(db.Integer, primary_key=True)
    identity_type = db.Column(db.String(10), nullable=False)
    identifier = db.Column(db.String(255), nullable=False, index=True)
    purpose = db.Column(db.String(30), nullable=False, index=True)
    code_hash = db.Column(db.String(64), nullable=False)
    payload = db.Column(db.JSON, default=dict)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    consumed_at = db.Column(db.DateTime(timezone=True))
    attempt_count = db.Column(db.Integer, default=0, nullable=False)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class UserSession(db.Model):
    """可撤销的登录会话；浏览器仅保存随机令牌，数据库保存其 SHA-256。"""
    __tablename__ = 'user_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    last_seen_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('login_sessions', cascade='all, delete-orphan'))


class Template(db.Model):
    """模板缓存. 真正的源在 site_templates/<name>/, 启动时扫描同步."""
    __tablename__ = 'templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # 文件夹名
    display_name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(50), nullable=False)
    cover_image = db.Column(db.String(500))
    description = db.Column(db.Text)
    current_version = db.Column(db.String(50))
    is_public = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class Site(db.Model):
    """店主的一个网站. 内容在 sites/<id>/*.yaml."""
    __tablename__ = 'sites'

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(30), unique=True, nullable=False, index=True)  # [a-z0-9-]{3,30}
    folder_path = db.Column(db.String(500), nullable=False)  # sites/<id>/
    template_name = db.Column(db.String(100), db.ForeignKey('templates.name'), nullable=False)
    template_version = db.Column(db.String(50))
    default_language = db.Column(db.String(5), default='zh-CN', nullable=False)
    enabled_languages = db.Column(db.JSON, default=lambda: ['zh-CN'])
    storage_mode = db.Column(db.String(20), default='shared', nullable=False)  # shared / dedicated
    bucket_name = db.Column(db.String(100))
    bucket_path_prefix = db.Column(db.String(100))
    bucket_region = db.Column(db.String(50))
    cdn_provider = db.Column(db.String(20), default='aliyun', nullable=False)
    status = db.Column(db.String(20), default='draft', nullable=False)  # draft / published / suspended
    last_published_at = db.Column(db.DateTime(timezone=True))
    soft_deleted_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    owner = db.relationship('User', backref=db.backref('sites', cascade='all, delete-orphan', passive_deletes=True))
    template = db.relationship('Template')


class ContactMessage(db.Model):
    """静态站点留言. contact_form 模块通过 API POST 存入, 店主后台查看."""
    __tablename__ = 'contact_messages'

    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    company = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    is_spam = db.Column(db.Boolean, default=False, nullable=False)
    ip_address = db.Column(db.String(45))  # IPv6 最长 45 字符
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    site = db.relationship('Site', backref='messages')


class Organization(db.Model):
    """团队协作边界；站点所有权仍由 Site.owner_id 兜底。"""
    __tablename__ = 'organizations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class OrganizationMember(db.Model):
    __tablename__ = 'organization_members'
    __table_args__ = (db.UniqueConstraint('organization_id', 'user_id', name='uq_org_member'),)
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role = db.Column(db.String(20), default='viewer', nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False)
    joined_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    organization = db.relationship('Organization', backref=db.backref('members', cascade='all, delete-orphan'))
    user = db.relationship('User')


class OrganizationInvitation(db.Model):
    """一次性团队邀请；只保存邀请令牌哈希。"""
    __tablename__ = 'organization_invitations'
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    identity_type = db.Column(db.String(10), nullable=False)
    identifier = db.Column(db.String(255), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default='viewer')
    token_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    invited_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending', index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    accepted_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    accepted_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    organization = db.relationship('Organization', backref=db.backref('invitations', cascade='all, delete-orphan'))
    inviter = db.relationship('User', foreign_keys=[invited_by])
    accepted_user = db.relationship('User', foreign_keys=[accepted_by])


class AccountEntitlement(db.Model):
    """账户级产品资格；与组织角色分离。"""
    __tablename__ = 'account_entitlements'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    can_create_sites = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    user = db.relationship('User', backref=db.backref('entitlement', uselist=False, cascade='all, delete-orphan'))


class OrganizationSite(db.Model):
    __tablename__ = 'organization_sites'
    __table_args__ = (db.UniqueConstraint('organization_id', 'site_id', name='uq_org_site'),)
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    organization = db.relationship('Organization', backref=db.backref('site_links', cascade='all, delete-orphan'))
    site = db.relationship('Site')


class AuditLog(db.Model):
    """只追加的账户操作日志。"""
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), index=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='SET NULL'), index=True)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id', ondelete='SET NULL'), index=True)
    action = db.Column(db.String(80), nullable=False, index=True)
    summary = db.Column(db.String(255), nullable=False)
    details = db.Column(db.JSON, default=dict)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class AiCreditAccount(db.Model):
    __tablename__ = 'ai_credit_accounts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    balance = db.Column(db.Integer, default=0, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class AiCreditTransaction(db.Model):
    __tablename__ = 'ai_credit_transactions'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('ai_credit_accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    amount = db.Column(db.Integer, nullable=False)
    balance_after = db.Column(db.Integer, nullable=False)
    source = db.Column(db.String(40), nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    account = db.relationship('AiCreditAccount', backref=db.backref('transactions', cascade='all, delete-orphan'))


class TotpCredential(db.Model):
    __tablename__ = 'totp_credentials'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    secret = db.Column(db.String(64), nullable=False)
    recovery_code_hashes = db.Column(db.JSON, default=list)
    enabled_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class ExternalIdentity(db.Model):
    __tablename__ = 'external_identities'
    __table_args__ = (db.UniqueConstraint('provider', 'provider_user_id', name='uq_external_identity'),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    provider = db.Column(db.String(30), nullable=False)
    provider_user_id = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(100))
    avatar_url = db.Column(db.String(500))
    is_mock = db.Column(db.Boolean, default=False, nullable=False)
    bound_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class BillingPlan(db.Model):
    __tablename__ = 'billing_plans'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    price_cents = db.Column(db.Integer, default=0, nullable=False)
    billing_period = db.Column(db.String(20), default='year', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)


class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('billing_plans.id'), nullable=False)
    status = db.Column(db.String(20), default='inactive', nullable=False)
    starts_at = db.Column(db.DateTime(timezone=True))
    ends_at = db.Column(db.DateTime(timezone=True))
    plan = db.relationship('BillingPlan')


class BillingOrder(db.Model):
    __tablename__ = 'billing_orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('billing_plans.id'), nullable=False)
    amount_cents = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    provider = db.Column(db.String(30), default='placeholder', nullable=False)
    provider_order_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


# slug 保留字 (注册时禁用)
SLUG_RESERVED = {
    'www', 'mail', 'smtp', 'ftp', 'admin', 'api', 'auth', 'app', 'dashboard',
    'help', 'docs', 'blog', 'support', 'status', 'dev', 'staging', 'test',
    'static', 'assets', 'cdn', 'acme',
}
