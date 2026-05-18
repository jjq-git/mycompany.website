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
    role = db.Column(db.String(20), default='owner', nullable=False)  # owner / admin
    display_name = db.Column(db.String(80))
    preferred_lang = db.Column(db.String(5), default='zh', nullable=False)
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
    default_language = db.Column(db.String(5), default='zh', nullable=False)
    enabled_languages = db.Column(db.JSON, default=lambda: ['zh'])
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


# slug 保留字 (注册时禁用)
SLUG_RESERVED = {
    'www', 'mail', 'smtp', 'ftp', 'admin', 'api', 'auth', 'app', 'dashboard',
    'help', 'docs', 'blog', 'support', 'status', 'dev', 'staging', 'test',
    'static', 'assets', 'cdn', 'acme',
}
