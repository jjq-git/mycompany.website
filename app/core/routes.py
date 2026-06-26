"""店主后台路由.

MVP 登录：邮箱魔法链接，不存密码。开发环境默认把登录链接打印到控制台，
并在页面提示中展示，方便本地调试；接入邮件服务后替换发送逻辑即可。
"""
import hashlib
import copy
import mimetypes
import secrets
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, send_file, send_from_directory,
                   session, url_for)
from werkzeug.utils import secure_filename

import re

import yaml as _yaml

from . import datasets, style_registry
from . import menu as menu_lib
from .translator import (generate_seo_description,
                         is_configured as translation_configured,
                         translate_json)
from .builder import build_site, build_template_preview
from .db import db
from .template_loader import scan_templates
from flask_cors import cross_origin
# CSRF 豁免：静态站点公开 API 无法提供 CSRF token, 需要豁免
# csrf 是 app/__init__.py 模块级变量, 在 create_app() 调用时已初始化
from app import csrf
from .models import ContactMessage, LoginToken, Site, Template, User
from .site_storage import (copy_seed_data, init_site_folder, lang_root,
                            list_media_files, list_yaml_files, read_yaml,
                            rename_media_file, delete_media_file,
                            find_media_references, is_media_package_token,
                            media_package_name_from_token, media_package_token,
                            write_yaml)

bp = Blueprint('core', __name__)

mimetypes.add_type('application/wasm', '.wasm')

def _hex_to_rgb(hex_color):
    """将 #rrggbb 转为 (r, g, b) 整数元组；无效输入返回黑色 (0, 0, 0)."""
    h = hex_color.lstrip('#')
    if len(h) < 6:
        return (0, 0, 0)
    try:
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        return (0, 0, 0)


def _darken(hex_color, factor=0.1):
    """将 hex 颜色变暗 factor (0-1)."""
    r, g, b = _hex_to_rgb(hex_color)
    return '#{:02x}{:02x}{:02x}'.format(
        max(0, int(r * (1 - factor))),
        max(0, int(g * (1 - factor))),
        max(0, int(b * (1 - factor))),
    )


def _lighten(hex_color, factor=0.1):
    """将 hex 颜色变亮 factor (0-1)."""
    r, g, b = _hex_to_rgb(hex_color)
    return '#{:02x}{:02x}{:02x}'.format(
        min(255, int(r + (255 - r) * factor)),
        min(255, int(g + (255 - g) * factor)),
        min(255, int(b + (255 - b) * factor)),
    )
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov'}
ALLOWED_FILE_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS | {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 'zip'
}
MAX_GENERIC_FILE_BYTES = 32 * 1024 * 1024
MAX_MEDIA_PACKAGE_BYTES = 64 * 1024 * 1024
MAX_MEDIA_PACKAGE_UNCOMPRESSED_BYTES = 96 * 1024 * 1024
MAX_MEDIA_PACKAGE_DEPTH = 10


AUTH_EXEMPT_ENDPOINTS = {
    'core.login',
    'core.magic_login',
    # template_preview 只渲染模板自带的种子数据, 不涉及任何用户私有内容, 可免登录。
    'core.template_preview',
    # 注意: preview / preview_site / preview_or_build 吐的是店主 output 下的真实
    # 私有数据, 已从免登录名单移除, 改为在各路由内做 _require_site_access 归属校验。
    # site_asset 免登录：路由内部通过 session / Referer 自行定位资源目录，
    # 模板预览（无站点归属）也需要访问 seed_data/assets 下的资源。
    'core.site_asset',
    'core.media_package_index',
    'core.media_package_asset',
    # api_contact_submit 是公开留言接收端点, 静态站点访客无需登录
    'core.api_contact_submit',
}


def _safe_send_from_directory(base_dir, relative_path):
    """加固版 send_from_directory: 解析 symlink 后强制校验目标仍在 base_dir 内,
    阻断符号链接逃逸 + 兜底防御 (Flask safe_join 自身也已经防 ../, 这里多一层保险).
    """
    base_real = Path(base_dir).resolve()
    full_real = (base_real / relative_path).resolve()
    try:
        full_real.relative_to(base_real)
    except ValueError:
        abort(403, '非法路径')
    return send_from_directory(base_real, relative_path)


def _hash_token(raw_token):
    """对魔法链接 token 做 SHA-256；数据库不保存明文 token."""
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


def _normalize_email(email):
    return (email or '').strip().lower()


# 图片单边像素上限, 防御解码炸弹 (1KB PNG 解开成 1GB 那种)
MAX_IMAGE_PIXELS = 16_000_000  # 约 4000x4000
MAX_IMAGE_BYTES = 12 * 1024 * 1024  # 单图最大 12MB


def _check_upload_size(file_storage, max_bytes, label='文件'):
    """通过 stream.seek 获取真实字节数, 超限直接报错."""
    stream = file_storage.stream
    try:
        stream.seek(0, 2)
        size = stream.tell()
    finally:
        stream.seek(0)
    if size > max_bytes:
        raise ValueError(f'{label}过大: {size // 1024}KB > {max_bytes // 1024}KB 上限')
    return size


def _upload_convert_webp_enabled(file_storage):
    """Return whether this upload field should convert raster images to WebP."""
    field_name = getattr(file_storage, 'name', '') or ''
    candidates = []
    if field_name:
        candidates.append(f'{field_name}_convert_webp')
        if field_name.endswith('_file'):
            candidates.append(f'{field_name[:-5]}_convert_webp')
    candidates.append('convert_webp')
    for name in candidates:
        if name in request.form:
            values = request.form.getlist(name)
            return any(value == 'true' for value in values) if values else request.form.get(name) != 'false'
    return True


def _save_uploaded_image(site_id, file_storage, prefix='image', convert_webp=None):
    """保存上传图片到 sites/<id>/assets/uploads/，默认转换为 WebP，返回站点内绝对路径.

    返回示例: /assets/uploads/product-cover-20260509153000.webp
    """
    if not file_storage or not file_storage.filename:
        return ''

    original = secure_filename(file_storage.filename)
    suffix = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError('仅支持 JPG、PNG、GIF、WebP、SVG 图片')

    uploads_dir = Path(current_app.config['SITES_DIR']) / str(site_id) / 'assets' / 'uploads'
    uploads_dir.mkdir(parents=True, exist_ok=True)

    safe_prefix = secure_filename(prefix or 'image') or 'image'
    ts = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    hex_part = secrets.token_hex(4)

    if convert_webp is None:
        convert_webp = _upload_convert_webp_enabled(file_storage)

    # SVG 和取消转换的图片都保留原格式直接写入。
    if suffix == 'svg' or not convert_webp:
        _check_upload_size(file_storage, MAX_IMAGE_BYTES, label='图片')
        filename = f"{safe_prefix}-{ts}-{hex_part}.{suffix}"
        output_path = uploads_dir / filename
        file_storage.save(str(output_path))
        return f'/assets/uploads/{filename}'

    _check_upload_size(file_storage, MAX_IMAGE_BYTES, label='图片')

    try:
        from PIL import Image, ImageSequence
    except ImportError as exc:
        raise RuntimeError('缺少 Pillow 依赖，请先安装 requirements.txt') from exc

    filename = f"{safe_prefix}-{ts}-{hex_part}.webp"
    output_path = uploads_dir / filename

    # #25: 用 with 确保 PIL 句柄及时释放(代码卫生)。损坏图会在此抛 PIL 异常,
    # 由各编辑路由捕获并提示, 不再 500。
    with Image.open(file_storage.stream) as image:
        # 分辨率上限校验, Pillow 默认对超大图触发 DecompressionBombWarning, 这里直接拒绝
        w, h = image.size
        if w * h > MAX_IMAGE_PIXELS:
            raise ValueError(f'图片分辨率过大: {w}x{h} 超过 {MAX_IMAGE_PIXELS} 像素上限')
        first_frame = next(ImageSequence.Iterator(image)).convert('RGBA')
    background = Image.new('RGBA', first_frame.size, (255, 255, 255, 0))
    background.alpha_composite(first_frame)
    background.save(output_path, 'WEBP', quality=86, method=6)
    return f'/assets/uploads/{filename}'


def _save_uploaded_media(site_id, file_storage, prefix='media'):
    """保存图片或视频；图片转 WebP，视频原样保存到 assets/uploads。"""
    if not file_storage or not file_storage.filename:
        return ''
    original = secure_filename(file_storage.filename)
    if not original:
        return ''
    suffix = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    if suffix in ALLOWED_IMAGE_EXTENSIONS:
        try:
            return _save_uploaded_image(site_id, file_storage, prefix=prefix)
        except Exception as exc:
            current_app.logger.warning('图片保存失败: %s', exc)
            return ''
    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        current_app.logger.warning('不支持的文件类型: %s', suffix)
        return ''

    # 视频体积上限 12MB; 更大体积请走 CDN 直传
    try:
        _check_upload_size(file_storage, MAX_IMAGE_BYTES, label='视频')
    except ValueError as exc:
        current_app.logger.warning('视频上传被拒: %s', exc)
        return ''

    uploads_dir = Path(current_app.config['SITES_DIR']) / str(site_id) / 'assets' / 'uploads'
    uploads_dir.mkdir(parents=True, exist_ok=True)
    safe_prefix = secure_filename(prefix or 'media') or 'media'
    filename = f"{safe_prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}.{suffix}"
    output_path = uploads_dir / filename
    file_storage.save(output_path)
    return f'/assets/uploads/{filename}'


def _save_any_file(site_id, file_storage, prefix='file'):
    """保存普通文件到 assets/uploads，图片/视频之外的文档等走这里。"""
    if not file_storage or not file_storage.filename:
        return ''
    original = secure_filename(file_storage.filename)
    if not original:
        raise ValueError('文件名无效')
    suffix = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    if suffix not in ALLOWED_FILE_EXTENSIONS or suffix in ALLOWED_IMAGE_EXTENSIONS or suffix in ALLOWED_VIDEO_EXTENSIONS:
        raise ValueError('不支持的文件类型')
    _check_upload_size(file_storage, MAX_GENERIC_FILE_BYTES, label='文件')

    uploads_dir = Path(current_app.config['SITES_DIR']) / str(site_id) / 'assets' / 'uploads'
    uploads_dir.mkdir(parents=True, exist_ok=True)
    safe_prefix = secure_filename(prefix or 'file') or 'file'
    stem = Path(original).stem
    safe_stem = secure_filename(stem) or safe_prefix
    filename = f"{safe_prefix}-{safe_stem}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}.{suffix}"
    output_path = uploads_dir / filename
    file_storage.save(output_path)
    return f'/assets/uploads/{filename}'


def _safe_zip_member_name(name):
    name = (name or '').replace('\\', '/').strip('/')
    if not name or name.startswith('.') or '\x00' in name:
        raise ValueError('网页包中包含非法文件名')
    path = Path(name)
    if path.is_absolute() or any(part in ('', '.', '..') or part.startswith('.') for part in path.parts):
        raise ValueError('网页包中包含非法路径')
    if len(path.parts) > MAX_MEDIA_PACKAGE_DEPTH:
        raise ValueError('网页包目录层级过深')
    return name


def _zip_strip_root(member_names):
    first_parts = [Path(name).parts for name in member_names]
    if not first_parts:
        return ''
    first = first_parts[0][0]
    if all(len(parts) > 1 and parts[0] == first for parts in first_parts):
        return first
    return ''


def _save_media_package(site_id, file_storage):
    """保存并解压网页包 zip，返回 {name, url, entry_url, category}。"""
    if not file_storage or not file_storage.filename:
        raise ValueError('请选择网页包 zip 文件')
    original = secure_filename(file_storage.filename)
    suffix = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    if suffix != 'zip':
        raise ValueError('网页包必须是 zip 文件')
    _check_upload_size(file_storage, MAX_MEDIA_PACKAGE_BYTES, label='网页包')

    try:
        archive = zipfile.ZipFile(file_storage.stream)
    except zipfile.BadZipFile as exc:
        raise ValueError('zip 文件无法读取') from exc

    with archive:
        infos = [info for info in archive.infolist() if not info.is_dir()]
        if not infos:
            raise ValueError('网页包不能为空')
        total_size = 0
        names = []
        for info in infos:
            total_size += info.file_size
            if total_size > MAX_MEDIA_PACKAGE_UNCOMPRESSED_BYTES:
                raise ValueError('网页包解压后体积过大')
            names.append(_safe_zip_member_name(info.filename))

        strip_root = _zip_strip_root(names)
        normalized = []
        for name in names:
            parts = Path(name).parts
            if strip_root:
                parts = parts[1:]
            if not parts:
                continue
            normalized.append('/'.join(parts))
        if 'index.html' not in {name.lower() for name in normalized}:
            raise ValueError('网页包根目录必须包含 index.html')

        package_root = Path(current_app.config['SITES_DIR']) / str(site_id) / 'assets' / 'media-packages'
        package_root.mkdir(parents=True, exist_ok=True)
        safe_stem = secure_filename(Path(original).stem) or 'media-package'
        package_name = f"{safe_stem}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}"
        target_dir = package_root / package_name
        target_dir.mkdir(parents=True, exist_ok=False)

        try:
            for info, name in zip(infos, names):
                parts = Path(name).parts
                if strip_root:
                    parts = parts[1:]
                if not parts:
                    continue
                rel = Path(*parts)
                target = (target_dir / rel).resolve()
                try:
                    target.relative_to(target_dir.resolve())
                except ValueError as exc:
                    raise ValueError('网页包中包含非法路径') from exc
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as src, target.open('wb') as dst:
                    dst.write(src.read())
        except Exception:
            if target_dir.exists():
                import shutil
                shutil.rmtree(target_dir, ignore_errors=True)
            raise

    entry_url = f'/media-packages/{package_name}/'
    return {
        'name': package_name,
        'display_name': package_name,
        'api_name': media_package_token(package_name),
        'url': entry_url,
        'entry_url': entry_url,
        'category': 'package',
        'category_label': '网页包',
        'is_package': True,
    }


def _uploaded_image_or_form(site_id, form_field, file_field=None, prefix='image'):
    """若上传了图片则返回 WebP URL，否则返回文本框中的原 URL。"""
    upload = request.files.get(file_field or f'{form_field}_file')
    if upload and upload.filename:
        # #25: 损坏图/超大图/不支持格式会抛异常, 这里捕获并提示, 回退到表单 URL,
        # 避免 product/post 编辑路径整个 500。
        try:
            return _save_uploaded_image(site_id, upload, prefix=prefix)
        except Exception as exc:
            current_app.logger.warning('图片上传保存失败(%s): %s', form_field, exc)
            flash(f'图片上传失败：{exc}', 'error')
    return request.form.get(form_field, '').strip()


def _field_looks_like_image(field):
    """匹配媒体字段（图片+视频+音频+嵌入），供 _parse_modules_form 处理上传文件。"""
    name = (field or '').lower()
    return any(part in name for part in ('image', 'cover', 'background', 'media', 'photo', 'logo', 'video', 'audio', 'embed'))


def _current_user():
    """从 session 读取当前用户；无效 session 自动清理."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    user = User.query.get(user_id)
    if not user or user.status != 'active':
        session.pop('user_id', None)
        return None
    return user


def _require_site_access(site):
    """校验当前登录用户有权访问该 site（本人站点或平台 admin）。

    预览路由会吐出店主 output 下的真实 HTML/资源, 必须做归属校验,
    否则任何登录用户自增 site_id 就能读他人未发布的私密站点(跨用户 IDOR)。

    测试阶段可通过 PREVIEW_REQUIRE_LOGIN 环境变量控制：默认免登录（不校验），
    开发完成后设 PREVIEW_REQUIRE_LOGIN=1 恢复完整鉴权。
    """
    # 测试阶段预览免登录：跳过站点归属校验，方便分享预览链接
    if not current_app.config.get('PREVIEW_REQUIRE_LOGIN'):
        return None
    user = _current_user()
    if not user:
        abort(401)
    if user.role != 'admin' and site.owner_id != user.id:
        abort(403)
    return user


@bp.before_request
def require_login():
    """保护后台页面：除登录和静态预览外都需要登录.

    测试阶段预览页（/preview/ /preview_site/ /preview_or_build/）默认免登录，
    开发完成后在 .env 设 PREVIEW_REQUIRE_LOGIN=1 恢复登录要求。
    """
    if request.endpoint in AUTH_EXEMPT_ENDPOINTS:
        return None
    if request.endpoint and request.endpoint.startswith('static'):
        return None
    # 预览端点按配置决定是否免登录（测试阶段免登录，方便分享预览链接给同事看）
    PREVIEW_ENDPOINTS = {'core.preview', 'core.preview_site', 'core.preview_or_build'}
    if request.endpoint in PREVIEW_ENDPOINTS and not current_app.config.get('PREVIEW_REQUIRE_LOGIN'):
        return None
    if not _current_user():
        return redirect(url_for('core.login', next=request.full_path if request.query_string else request.path))
    return None


@bp.context_processor
def inject_context():
    """给所有模板注入站点上下文."""
    user = _current_user()
    site_id = request.args.get('site', type=int)
    if not site_id:
        if user and user.role == 'admin':
            site = Site.query.order_by(Site.id.desc()).first()
        elif user:
            site = Site.query.filter_by(owner_id=user.id).order_by(Site.id.desc()).first()
        else:
            site = None
        site_id = site.id if site else None
    else:
        site = Site.query.get(site_id)
        if site and user and user.role != 'admin' and site.owner_id != user.id:
            site = None

    ctx = {
        'counts': {},
        'left_menu_items': [],
        'template_meta': {},
        'available_sites': [],
        'admin_languages': [],
        'current_lang': '',
        'current_language_label': '',
    }

    if user:
        query = Site.query
        if user.role != 'admin':
            query = query.filter_by(owner_id=user.id)
        ctx['available_sites'] = query.order_by(Site.id.desc()).all()

    if site and site_id:
        ctx['counts']['products'] = len(datasets.load(site_id, 'products') or [])
        ctx['counts']['posts'] = len(datasets.load(site_id, 'posts') or [])
        ctx['counts']['features'] = len(datasets.load(site_id, 'features') or [])

        # 左栏动态菜单：从 settings.yaml 读取 menu 列表
        settings = read_yaml(site_id, 'settings.yaml') or {}
        meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
        if meta_path.exists():
            ctx['template_meta'] = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {}

        # 后台顶部语言选择器：优先显示站点已启用语言，异常数据回退到主题语言/站点默认语言。
        template_languages = ctx['template_meta'].get('languages') or []
        enabled_codes = site.enabled_languages or [l.get('code') for l in template_languages if l.get('code')]
        admin_languages = [l for l in template_languages if l.get('code') in enabled_codes]
        if not admin_languages:
            admin_languages = template_languages
        default_lang = (
            ctx['template_meta'].get('default_language')
            or site.default_language
            or (admin_languages[0].get('code') if admin_languages else 'zh-CN')
        )
        current_lang = request.args.get('lang', '').strip() or default_lang
        valid_codes = {l.get('code') for l in admin_languages}
        if valid_codes and current_lang not in valid_codes:
            current_lang = default_lang if default_lang in valid_codes else admin_languages[0].get('code')
        if not admin_languages and current_lang:
            admin_languages = [{'code': current_lang, 'name': current_lang}]
        current_lang_opt = next((l for l in admin_languages if l.get('code') == current_lang), None)
        current_label = (current_lang_opt or {}).get('name') or current_lang or '默认语言'
        ctx['admin_languages'] = admin_languages
        ctx['current_lang'] = current_lang
        ctx['current_language_label'] = f"{current_label} ({current_lang})" if current_lang else current_label

        raw_menu = settings.get('menu') or ctx['template_meta'].get('default_menu', [])
        # 强制裁剪深度, 防御恶意 yaml 通过深嵌套触发递归栈溢出
        raw_menu = menu_lib.cap_menu_depth(raw_menu)
        datasets_meta = ctx['template_meta'].get('datasets', [])
        normalized = menu_lib.ensure_home(
            menu_lib.normalize_for_render(
                menu_lib.upgrade_old_format(raw_menu, datasets_meta)
            )
        )
        ctx['left_menu_items'] = normalized

        # 收集所有层级中 type=list 的菜单项（供数据网格模块选择数据源）
        ctx['all_list_datasets'] = menu_lib.collect_list_targets(normalized)  # #22

    ctx['platform_domain'] = current_app.config.get('PLATFORM_DOMAIN', '') or 'mycompany.website'

    # 后台 UI 主色固定，不跟随网站前台主题色。
    theme_color = '#0d9488'
    ctx['admin_primary'] = theme_color
    ctx['admin_primary_rgb'] = ', '.join(str(v) for v in _hex_to_rgb(theme_color))
    ctx['admin_primary_hover'] = _darken(theme_color, 0.12)
    ctx['admin_primary_active'] = _darken(theme_color, 0.20)
    ctx['admin_primary_light'] = _lighten(theme_color, 0.85)
    ctx['admin_auto_save'] = bool((settings.get('admin') or {}).get('auto_save')) if site and site_id else False

    return ctx


def _current_context():
    """取当前登录用户和站点；普通用户只能访问自己的站点，admin 可访问全部.

    URL 中带 ?site=N 时存入 session，后续资源请求（如 /assets/uploads/...）
    不带 ?site= 也能从 session 中取到正确的站点.
    """
    user = _current_user()
    if not user:
        abort(401)
    site_id = request.args.get('site', type=int)
    if site_id:
        session['current_site_id'] = site_id  # 记住当前浏览的站点
        site = Site.query.get(site_id)
    else:
        # 从 session 中取缓存的站点 ID，确保资源请求也能找到正确的站点
        site_id = session.get('current_site_id')
        if site_id is not None:
            site = Site.query.get(int(site_id))
        else:
            site = None
        if not site:
            query = Site.query
            if user.role != 'admin':
                query = query.filter_by(owner_id=user.id)
            site = query.order_by(Site.id.desc()).first()
    if not site:
        abort(404, "尚无站点，请先从模板库创建站点")
    if user.role != 'admin' and site.owner_id != user.id:
        abort(403, "无权访问该站点")
    return user, site


def _safe_next_url(candidate):
    """只允许跳回本站相对路径; 外站 URL / 协议跳转 / 协议相对 URL 全部拒绝.

    防止 ?next=https://evil.com 形式的 open redirect 钓鱼.
    """
    from urllib.parse import urlparse
    if not candidate:
        return None
    candidate = candidate.strip()
    # 拒绝绝对 URL (含 scheme 或 netloc), 拒绝协议相对 URL "//evil.com/x"
    if candidate.startswith('//'):
        return None
    parsed = urlparse(candidate)
    if parsed.scheme or parsed.netloc:
        return None
    # 必须以 / 开头, 防 "javascript:..." 等其它伪协议
    if not candidate.startswith('/'):
        return None
    return candidate


def _create_magic_link(email, request):
    """创建一次性魔法链接 token，返回完整登录 URL."""
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, status='active')
        db.session.add(user)
        db.session.flush()

    raw_token = secrets.token_urlsafe(32)
    token = LoginToken(
        user_id=user.id,
        email=email,
        token_hash=_hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        ip_address=request.headers.get('X-Forwarded-For', request.remote_addr or '')[:45],
    )
    db.session.add(token)
    db.session.commit()
    return url_for('core.magic_login', token=raw_token, _external=True)


# #9: /login 的轻量内存限流。MVP 不引入 Redis/flask-limiter 新依赖(符合"依赖能少则少"),
# 单进程内用滑动窗口足够挡住"接入真实邮件后的邮件轰炸/刷库"。key 为 IP 或邮箱, 值为时间戳列表。
# 注意: 多 worker 部署下各进程独立计数, 规模化时再换集中式限流。
_LOGIN_ATTEMPTS = {}
_LOGIN_WINDOW_SECONDS = 600   # 10 分钟窗口
_LOGIN_MAX_PER_WINDOW = 5     # 同一 IP/邮箱 10 分钟内最多 5 次


def _login_rate_limited(*keys):
    """检查并记录登录尝试; 任一 key 超过窗口上限则返回 True(应拒绝)."""
    now = datetime.now(timezone.utc).timestamp()
    limited = False
    for key in keys:
        if not key:
            continue
        hits = [t for t in _LOGIN_ATTEMPTS.get(key, []) if now - t < _LOGIN_WINDOW_SECONDS]
        if len(hits) >= _LOGIN_MAX_PER_WINDOW:
            limited = True
        hits.append(now)
        _LOGIN_ATTEMPTS[key] = hits
    return limited


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """邮箱魔法链接登录入口."""
    if _current_user() and request.method == 'GET':
        return redirect(_safe_next_url(request.args.get('next')) or url_for('core.overview'))

    magic_link = None
    email = ''
    if request.method == 'POST':
        email = _normalize_email(request.form.get('email'))
        if not email or '@' not in email:
            flash('请输入有效邮箱地址', 'danger')
        else:
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()
            if _login_rate_limited(client_ip, email):
                # 中性提示, 不暴露"邮箱是否已注册", 也不告知具体是被限流
                current_app.logger.warning('登录请求被限流: ip=%s email=%s', client_ip, email)
                flash('请求过于频繁，请稍后再试。', 'danger')
            else:
                magic_link = _create_magic_link(email, request)
                current_app.logger.info('Magic login link for %s: %s', email, magic_link)
                flash('登录链接已生成。开发环境中可直接点击下方链接；生产环境将通过邮件发送。', 'success')
    return render_template('auth/login.html', email=email, magic_link=magic_link)


@bp.route('/auth/magic/<token>')
def magic_login(token):
    """消费一次性 token 并写入 session."""
    now = datetime.now(timezone.utc)
    login_token = LoginToken.query.filter_by(token_hash=_hash_token(token)).first()
    if not login_token or login_token.used_at:
        flash('登录链接无效或已使用，请重新获取。', 'danger')
        return redirect(url_for('core.login'))
    expires_at = login_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        flash('登录链接已过期，请重新获取。', 'danger')
        return redirect(url_for('core.login'))

    user = User.query.get(login_token.user_id) or User.query.filter_by(email=login_token.email).first()
    if not user or user.status != 'active':
        flash('账号不可用，请联系管理员。', 'danger')
        return redirect(url_for('core.login'))

    login_token.used_at = now
    user.email_verified_at = user.email_verified_at or now
    user.last_login_at = now
    db.session.commit()

    session.clear()
    session['user_id'] = user.id
    flash('已登录', 'success')
    if user.role == 'admin':
        if Site.query.first():
            return redirect(url_for('core.overview'))
        else:
            flash("尚无站点，请先从模板库创建站点", "warning")
            return redirect(url_for('core.templates_gallery'))
    if Site.query.filter_by(owner_id=user.id).first():
        return redirect(url_for('core.overview'))
    return redirect(url_for('core.templates_gallery'))


@bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('已退出登录', 'success')
    return redirect(url_for('core.login'))


@bp.route('/assets/<path:filename>')
def site_asset(filename):
    """预览/后台共用的站点上传资源入口。预览页免登录，资源请求也免登录。

    通过 session 定位资源目录，确保预览页里 <img src="/assets/...">
    和 CSS 中 url(/assets/...) 直接访问而不被拦到登录页。
    静态导出时由 output/assets 直接承载。
    """
    assets_root = None
    referer = request.headers.get('Referer', '')
    m = re.search(r'/preview(?:/(?:site|or_build))?/(\d+)', referer)
    if m:
        site = Site.query.get(int(m.group(1)))
        if site:
            site_assets = Path(current_app.config['SITES_DIR']) / str(site.id) / 'assets'
            if (site_assets / filename).exists():
                return _safe_send_from_directory(site_assets, filename)

    site_id = session.get('current_site_id')
    if site_id is not None:
        site = Site.query.get(int(site_id))
        if site:
            site_assets = Path(current_app.config['SITES_DIR']) / str(site.id) / 'assets'
            if (site_assets / filename).exists():
                return _safe_send_from_directory(site_assets, filename)

    # 1. 模板预览 session（最优先：CSS 背景图 Referer 是 main.css，不包含 /preview/）
    tpl_name = session.get('current_template_preview')
    if tpl_name:
        tpl_assets = Path(current_app.config['OUTPUT_DIR']) / '_preview' / tpl_name / 'assets'
        if tpl_assets.exists():
            assets_root = tpl_assets

    # 2. 站点预览 / 管理后台 session
    if assets_root is None:
        site_id = session.get('current_site_id')
        if site_id is not None:
            site = Site.query.get(int(site_id))
            if site:
                assets_root = Path(current_app.config['SITES_DIR']) / str(site.id) / 'assets'

    # 3. Referer 兜底（清除 session 后首次请求等极端情况）
    referer = request.headers.get('Referer', '')
    if assets_root is None:
        m = re.search(r'/templates/([a-zA-Z0-9_-]+)/preview/', referer)
        if m:
            tpl_assets = Path(current_app.config['OUTPUT_DIR']) / '_preview' / m.group(1) / 'assets'
            if tpl_assets.exists():
                assets_root = tpl_assets
    if assets_root is None:
        m = re.search(r'/preview(?:/(?:site|or_build))?/(\d+)', referer)
        if m:
            site = Site.query.get(int(m.group(1)))
            if site:
                assets_root = Path(current_app.config['SITES_DIR']) / str(site.id) / 'assets'

    # 4. 最终兜底
    if assets_root is None:
        site = Site.query.order_by(Site.id.desc()).first()
        if site:
            assets_root = Path(current_app.config['SITES_DIR']) / str(site.id) / 'assets'

    if assets_root is None:
        abort(404, '资源不存在')
    return _safe_send_from_directory(assets_root, filename)


def _media_package_assets_root():
    """Resolve the current site's media package root for admin and preview requests."""
    assets_root = None
    site_id = session.get('current_site_id')
    if site_id is not None:
        site = Site.query.get(int(site_id))
        if site:
            assets_root = Path(current_app.config['SITES_DIR']) / str(site.id) / 'assets'

    referer = request.headers.get('Referer', '')
    if assets_root is None:
        m = re.search(r'/preview(?:/(?:site|or_build))?/(\d+)', referer)
        if m:
            site = Site.query.get(int(m.group(1)))
            if site:
                assets_root = Path(current_app.config['SITES_DIR']) / str(site.id) / 'assets'

    if assets_root is None:
        site = Site.query.order_by(Site.id.desc()).first()
        if site:
            assets_root = Path(current_app.config['SITES_DIR']) / str(site.id) / 'assets'

    if assets_root is None:
        abort(404, '网页包不存在')
    return assets_root / 'media-packages'


@bp.route('/media-packages/<package_name>/')
def media_package_index(package_name):
    package_name = secure_filename(package_name or '')
    if not package_name:
        abort(404, '网页包不存在')
    packages_root = _media_package_assets_root()
    package_dir = (packages_root / package_name).resolve()
    try:
        package_dir.relative_to(packages_root.resolve())
    except ValueError:
        abort(403, '非法路径')
    if not (package_dir / 'index.html').exists():
        abort(404, '网页包不存在')
    return _safe_send_from_directory(package_dir, 'index.html')


@bp.route('/media-packages/<package_name>/<path:filename>')
def media_package_asset(package_name, filename):
    package_name = secure_filename(package_name or '')
    if not package_name:
        abort(404, '网页包不存在')
    packages_root = _media_package_assets_root()
    package_dir = (packages_root / package_name).resolve()
    try:
        package_dir.relative_to(packages_root.resolve())
    except ValueError:
        abort(403, '非法路径')
    return _safe_send_from_directory(package_dir, filename)


@bp.errorhandler(404)
def not_found(error):
    """捕获 404，无站点时重定向到模板库."""
    desc = error.description if hasattr(error, 'description') else str(error)
    if '尚无站点' in str(desc):
        flash("尚无站点，请先从模板库创建站点", "warning")
        return redirect(url_for('core.templates_gallery'))
    return f"<h1>404 Not Found</h1><p>{desc}</p>", 404


@bp.route('/')
def index():
    user, site = _current_context()
    return render_template('base.html', user=user, site=site, active='')


@bp.route('/overview')
def overview():
    return redirect(url_for('core.index'))


@bp.route('/company/workspace')
def company_workspace():
    """Open company settings in the center workspace instead of the side panel."""
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    settings = read_yaml(site.id, 'settings.yaml', default={}, lang=lang) or {}
    company_key = _lang_key('company', site, lang, default_lang)
    contact_key = _lang_key('contact', site, lang, default_lang)
    current_company = _merge_settings_section(settings.get('company'), settings.get(company_key))
    source_company = settings.get('company', {})
    current_contact = _merge_settings_section(settings.get('contact'), settings.get(contact_key))
    source_contact = settings.get('contact', {})
    return render_template('dashboard/settings_workspace.html',
                           title='公司信息',
                           panel_template='dashboard/panel_company.html',
                           user=user, site=site, active='company',
                           company=current_company,
                           contact=current_contact,
                           source_company=source_company,
                           source_contact=source_contact,
                           current_lang=lang,
                           languages=languages,
                           default_lang=default_lang,
                           settings_workspace=True)


@bp.route('/theme/workspace')
def theme_workspace():
    """Open theme settings in the center workspace instead of the side panel."""
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml', default={}) or {}
    tpl_meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    tpl_meta = _yaml.safe_load(tpl_meta_path.read_text(encoding='utf-8')) if tpl_meta_path.exists() else {}
    default_theme = tpl_meta.get('default_theme') or {}
    theme = settings.get('theme') or {}
    return render_template('dashboard/settings_workspace.html',
                           title='主题颜色',
                           panel_template='dashboard/panel_theme.html',
                           user=user, site=site, active='theme',
                           theme=theme,
                           default_theme=default_theme,
                           settings_workspace=True)


@bp.route('/settings/basic')
def basic_settings():
    """Company and theme settings in one side panel with tabs."""
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    lang, languages, default_lang = _get_panel_lang(site)
    company_key = _lang_key('company', site, lang, default_lang)
    contact_key = _lang_key('contact', site, lang, default_lang)
    current_company = _merge_settings_section(settings.get('company'), settings.get(company_key))
    current_contact = _merge_settings_section(settings.get('contact'), settings.get(contact_key))
    source_company = settings.get('company', {})
    source_contact = settings.get('contact', {})

    tpl_meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    tpl_meta = _yaml.safe_load(tpl_meta_path.read_text(encoding='utf-8')) if tpl_meta_path.exists() else {}
    default_theme = tpl_meta.get('default_theme') or {}
    theme = settings.get('theme') or {}
    tab = request.args.get('tab') or 'company'
    if tab not in ('company', 'theme'):
        tab = 'company'

    # 中间栏嵌入模式：渲染无外壳的独立页面（类似留言管理的 embed 模式）
    if request.args.get('embed') == '1':
        return render_template('dashboard/basic_settings_embed.html',
                               user=user, site=site,
                               company=current_company,
                               contact=current_contact,
                               source_company=source_company,
                               source_contact=source_contact,
                               theme=theme,
                               default_theme=default_theme,
                               admin_settings=settings.get('admin') or {},
                               current_lang=lang,
                               languages=languages,
                               default_lang=default_lang,
                               basic_settings_tab=tab,
                               active='basic_settings')

    return render_template('dashboard/panel_basic_settings.html',
                           user=user, site=site,
                           company=current_company,
                           contact=current_contact,
                           source_company=source_company,
                           source_contact=source_contact,
                           theme=theme,
                           default_theme=default_theme,
                           admin_settings=settings.get('admin') or {},
                           current_lang=lang,
                           languages=languages,
                           default_lang=default_lang,
                           basic_settings_tab=tab,
                           active='basic_settings')


@bp.route('/media')
def media():
    user, site = _current_context()
    files = list_media_files(site.id)
    if request.args.get('_fragment'):
        return render_template('dashboard/panel_media.html',
                               user=user, site=site, files=files)
    return render_template('dashboard/media.html',
                           user=user, site=site, files=files, active='media')


@bp.route('/media/workspace')
def media_workspace():
    user, site = _current_context()
    files = list_media_files(site.id)
    return render_template('dashboard/media_workspace.html',
                           user=user, site=site, files=files, active='media')


@bp.route('/api/media/references')
def api_media_references():
    _, site = _current_context()
    name = request.args.get('filename') or request.args.get('name') or ''
    if not name:
        return jsonify({'error': '缺少文件名'}), 400
    refs = find_media_references(site.id, name)
    return jsonify({'filename': name, 'refs': refs, 'count': len(refs)})


@bp.route('/api/contact/<int:site_id>', methods=['POST', 'OPTIONS'])
@csrf.exempt
@cross_origin(origins='*')
def api_contact_submit(site_id):
    """公开留言接收端点 —— 供静态站点 contact_form 表单 POST 提交.

    CSRF 豁免原因：静态 HTML 页面无法生成 CSRF token, 且此端点无登录态、只写公开数据.
    CORS 开放原因：静态站点可能托管在不同域（CDN / 自定义域名）.
    反垃圾：蜜罐字段 __hp + 同站速率限制.
    """
    # ---- OPTIONS 预检 ----
    if request.method == 'OPTIONS':
        return jsonify({'ok': True})

    # ---- 蜜罐反垃圾：bot 会填充隐藏字段, 人类看不到 ----
    if request.form.get('__hp', '').strip():
        return jsonify({'ok': True})  # 静默丢弃, 不让 bot 知道被拦截

    # ---- 字段提取 ----
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    company = request.form.get('company', '').strip()
    message_text = request.form.get('message', '').strip()
    internal_site_id = request.form.get('__site_id', '').strip()

    # ---- 基本校验 ----
    if not name or not email or not message_text:
        return jsonify({'error': '请填写姓名、邮箱和留言内容'}), 400

    if len(message_text) > 5000:
        return jsonify({'error': '留言内容过长（上限 5000 字符）'}), 400

    if '@' not in email:
        return jsonify({'error': '邮箱格式不正确'}), 400

    # ---- 站点校验：优先用隐藏字段, 兜底 URL 参数 ----
    try:
        resolved_site_id = int(internal_site_id) if internal_site_id else site_id
    except (ValueError, TypeError):
        resolved_site_id = site_id

    site = Site.query.get(resolved_site_id)
    if not site:
        return jsonify({'error': '站点不存在'}), 404

    # ---- 速率限制：同站每分钟最多 10 条 ----
    one_min_ago = datetime.now(timezone.utc) - timedelta(minutes=1)
    recent = ContactMessage.query.filter(
        ContactMessage.site_id == resolved_site_id,
        ContactMessage.created_at >= one_min_ago
    ).count()
    if recent > 10:
        return jsonify({'error': '提交过于频繁，请稍后再试'}), 429

    # ---- 存储 ----
    msg = ContactMessage(
        site_id=resolved_site_id,
        name=name,
        email=email,
        phone=phone or None,
        company=company or None,
        message=message_text,
        ip_address=request.remote_addr,
    )
    db.session.add(msg)
    db.session.commit()

    current_app.logger.info('新留言: site_id=%d name=%s email=%s', resolved_site_id, name, email)
    return jsonify({'ok': True})


@bp.route('/api/media/upload', methods=['POST'])
def api_media_upload():
    _, site = _current_context()
    upload = request.files.get('file')
    if not upload or not upload.filename:
        return jsonify({'error': '请选择文件'}), 400
    original = secure_filename(upload.filename)
    suffix = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    try:
        if suffix == 'zip':
            result = _save_media_package(site.id, upload)
            return jsonify({'ok': True, **result})
        if suffix in ALLOWED_IMAGE_EXTENSIONS or suffix in ALLOWED_VIDEO_EXTENSIONS:
            url = _save_uploaded_media(site.id, upload, prefix='media')
        else:
            url = _save_any_file(site.id, upload, prefix='media')
        if not url:
            return jsonify({'error': '文件上传失败或类型不支持'}), 400
        filename = url.rsplit('/', 1)[-1]
        files = [item for item in list_media_files(site.id) if item.get('api_name') == filename]
        payload = files[0] if files else {'name': filename, 'api_name': filename, 'url': url}
        return jsonify({'ok': True, **payload})
    except Exception as exc:
        current_app.logger.warning('media upload failed: %s', exc)
        return jsonify({'error': str(exc)}), 400


@bp.route('/api/media/rename', methods=['POST'])
def api_media_rename():
    _, site = _current_context()
    data = request.get_json(silent=True) or request.form
    old_name = (data.get('old_name') or data.get('filename') or '').strip()
    new_name = (data.get('new_name') or '').strip()
    if not old_name or not new_name:
        return jsonify({'error': '缺少文件名'}), 400
    refs = find_media_references(site.id, old_name)
    try:
        new_api_name = rename_media_file(site.id, old_name, new_name)
    except Exception as exc:
        current_app.logger.warning('media rename failed: %s', exc)
        return jsonify({'error': str(exc)}), 400
    if is_media_package_token(new_api_name):
        package_name = media_package_name_from_token(new_api_name)
        return jsonify({
            'ok': True,
            'name': package_name,
            'api_name': new_api_name,
            'url': f'/media-packages/{package_name}/',
            'entry_url': f'/media-packages/{package_name}/',
            'category': 'package',
            'updated_refs': refs,
            'count': len(refs),
        })
    return jsonify({
        'ok': True,
        'name': new_api_name,
        'api_name': new_api_name,
        'url': f'/assets/uploads/{new_api_name}',
        'updated_refs': refs,
        'count': len(refs),
    })


@bp.route('/api/media/delete', methods=['POST'])
def api_media_delete():
    _, site = _current_context()
    data = request.get_json(silent=True) or request.form
    name = (data.get('filename') or data.get('name') or '').strip()
    if not name:
        return jsonify({'error': '缺少文件名'}), 400
    refs = find_media_references(site.id, name)
    if refs:
        return jsonify({'ok': False, 'error': '文件已被引用，不能删除', 'refs': refs, 'count': len(refs)}), 409
    try:
        delete_media_file(site.id, name)
    except Exception as exc:
        current_app.logger.warning('media delete failed: %s', exc)
        return jsonify({'error': str(exc)}), 400
    return jsonify({'ok': True})


def _as_items(raw):
    """把数据集 YAML 标准化成条目列表，健康检查只读不改原数据。"""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        items = raw.get('items', [])
        return items if isinstance(items, list) else []
    return []


def _plain_text(value):
    """把模块字段压成短文本，供 SEO 简介自动生成使用。"""
    if value is None:
        return ''
    if isinstance(value, str):
        return re.sub(r'<[^>]+>', ' ', value).strip()
    if isinstance(value, (int, float)):
        return str(value)
    return ''


def _auto_page_description(page):
    """从页面模块内容生成简介。

    这不是让店主手写 SEO，而是先从已有业务内容里抽取摘要；店主觉得不合适
    时再手动改写。后续接入真正 AI 文案接口时，只需要替换这个函数。
    """
    if not isinstance(page, dict):
        return ''
    parts = []
    for module in page.get('modules') or []:
        data = module.get('data') if isinstance(module, dict) else {}
        if not isinstance(data, dict):
            continue
        for key in ('desc', 'subtitle', 'summary', 'description', 'body', 'content', 'title'):
            text = _plain_text(data.get(key))
            if text:
                parts.append(text)
        if len(' '.join(parts)) >= 180:
            break
    text = re.sub(r'\s+', ' ', ' '.join(parts)).strip()
    return text[:180].rstrip()


def _page_text_for_seo(page):
    """收集页面核心文本，作为 AI 生成 SEO 简介的上下文。"""
    if not isinstance(page, dict):
        return ''
    parts = []
    for module in page.get('modules') or []:
        data = module.get('data') if isinstance(module, dict) else {}
        if not isinstance(data, dict):
            continue
        for key in ('title', 'desc', 'subtitle', 'summary', 'description', 'body', 'content'):
            text = _plain_text(data.get(key))
            if text:
                parts.append(text)
        for value in data.values():
            if isinstance(value, list):
                for item in value[:8]:
                    if not isinstance(item, dict):
                        continue
                    for key in ('title', 'desc', 'text', 'summary'):
                        text = _plain_text(item.get(key))
                        if text:
                            parts.append(text)
    return re.sub(r'\s+', ' ', ' '.join(parts)).strip()[:2200]


def _dataset_items(raw):
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        items = raw.get('items')
        return items if isinstance(items, list) else []
    return []


def _detail_item_text_for_seo(item):
    if not isinstance(item, dict):
        return ''
    parts = []
    for key in ('seo_title', 'title', 'name', 'seo_description', 'summary', 'description', 'excerpt', 'body', 'content'):
        text = _plain_text(item.get(key))
        if text:
            parts.append(text)
    return re.sub(r'\s+', ' ', ' '.join(parts)).strip()[:2200]


def _seo_status(description, auto_desc):
    if description:
        return 'ok', '已设置', '使用手动简介'
    if auto_desc:
        return 'auto', '可自动生成', '可从页面内容生成简介'
    return 'warn', '缺少内容', '页面内容不足，建议手动填写'


def _seo_row_for_page(site, lang, page_key, title, page, row_id=None, depth=0, parent_id=''):
    page = page if isinstance(page, dict) else {}
    auto_desc = _auto_page_description(page)
    description = page.get('description') or ''
    status, status_label, status_detail = _seo_status(description, auto_desc)
    row_id = row_id or f'page:{page_key}'
    return {
        'id': row_id,
        'key': page_key,
        'type': 'page',
        'kind': 'page',
        'depth': depth,
        'parent_id': parent_id,
        'title': page.get('title') or title or page_key,
        'description': description,
        'auto_description': auto_desc,
        'status': status,
        'status_label': status_label,
        'status_detail': status_detail,
        'save_url': url_for('core.seo_page_update', page_key=page_key, site=site.id, lang=lang),
        'generate_url': url_for('core.seo_page_generate', page_key=page_key, site=site.id, lang=lang),
    }


def _seo_row_for_detail(site, lang, dataset_key, item, depth=0, parent_id=''):
    item = item if isinstance(item, dict) else {}
    slug = item.get('slug') or item.get('id') or ''
    title = item.get('seo_title') or item.get('title') or item.get('name') or str(slug) or '未命名详情页'
    description = item.get('seo_description') or ''
    auto_desc = _plain_text(item.get('summary') or item.get('description') or item.get('excerpt') or item.get('body') or item.get('content'))[:180].rstrip()
    status, status_label, status_detail = _seo_status(description, auto_desc)
    row_id = f'detail:{dataset_key}:{slug}'
    return {
        'id': row_id,
        'key': str(slug),
        'type': 'detail',
        'kind': 'detail',
        'dataset_key': dataset_key,
        'depth': depth,
        'parent_id': parent_id,
        'title': title,
        'description': description,
        'auto_description': auto_desc,
        'status': status,
        'status_label': status_label,
        'status_detail': status_detail,
        'save_url': url_for('core.seo_detail_update', dataset_key=dataset_key, item_key=slug, site=site.id, lang=lang),
        'generate_url': url_for('core.seo_detail_generate', dataset_key=dataset_key, item_key=slug, site=site.id, lang=lang),
    }


def _seo_page_rows(site, lang, settings, pages, data, meta):
    """返回 SEO 工作区页面行，按菜单树保留层级，包含列表详情页。"""
    tpl_html_dir = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'templates'
    menu_items = menu_lib.ensure_home(
        menu_lib.normalize_for_render(
            menu_lib.upgrade_old_format(settings.get('menu') or [], meta.get('datasets', []))
        )
    )
    rows = []
    seen = set()

    def add_page_row(page_key, label, item_type='page', depth=0, parent_id=''):
        if not page_key or page_key in seen or page_key not in pages:
            return ''
        seen.add(page_key)
        row_id = f'page:{page_key}'
        row = _seo_row_for_page(site, lang, page_key, label, pages.get(page_key), row_id=row_id, depth=depth, parent_id=parent_id)
        row['type'] = item_type
        rows.append(row)
        return row_id

    def walk(items, depth=0, parent_id=''):
        for item in items or []:
            if not isinstance(item, dict):
                continue
            item_type = item.get('type')
            label = item.get('label') or item.get('target') or item.get('url') or ''
            row_id = ''
            if item_type == 'home':
                row_id = add_page_row('home', label or 'Home', item_type='home', depth=depth, parent_id=parent_id)
            elif item_type in ('page', 'list') and item.get('target'):
                target = item.get('target')
                row_id = add_page_row(target, label, item_type=item_type, depth=depth, parent_id=parent_id)
                if item_type == 'list':
                    dt_tmpl, var_name, slug_field = menu_lib.derive_detail_info(target, tpl_html_dir)
                    if dt_tmpl and var_name:
                        for entry in _dataset_items(data.get(target)):
                            if not isinstance(entry, dict):
                                continue
                            slug = entry.get(slug_field) or entry.get('slug') or entry.get('id')
                            if not slug:
                                continue
                            detail_row = _seo_row_for_detail(site, lang, target, entry, depth=depth + 1, parent_id=row_id)
                            rows.append(detail_row)
            if item.get('children'):
                walk(item.get('children') or [], depth=depth + 1, parent_id=row_id or parent_id)

    walk(menu_items)

    # 兜底补充渲染任务里出现但菜单树未直接覆盖的页面，通常是兼容旧数据。
    tasks = menu_lib.collect_render_tasks(menu_items, tpl_html_dir, data, pages)
    for task in tasks:
        if task.get('type') in ('home', 'page', 'list'):
            add_page_row(task.get('page_key'), task.get('page_key'), item_type=task.get('type'), depth=0)
    return rows


def _seo_health_report(site, lang=None):
    """生成 SEO 健康检查报告。

    这里检查的是店主能理解并能通过现有表单补齐的内容项；技术性 SEO
    文件由构建器自动生成，只检查最近构建输出是否存在。
    """
    default_lang = 'zh-CN'
    meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    if meta_path.exists():
        try:
            meta_data = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {}
            default_lang = meta_data.get('default_language') or default_lang
        except Exception:
            default_lang = site.default_language or default_lang
    lang = lang or default_lang
    storage_lang = _storage_lang(site, lang, default_lang)
    settings = read_yaml(site.id, 'settings.yaml') or {}
    company_key = _lang_key('company', site, lang, default_lang)
    company = _merge_settings_section(settings.get('company'), settings.get(company_key))
    tpl_html_dir = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'templates'
    meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}

    checks = []

    def add(status, title, detail, action_url=''):
        checks.append({
            'status': status,
            'title': title,
            'detail': detail,
            'action_url': action_url,
        })

    if company.get('name'):
        add('ok', '公司名称已填写', '页面标题、OG 站点名和结构化数据会使用公司名称。')
    else:
        add('warn', '缺少公司名称', '公司名称是全站 SEO 的基础字段。', url_for('core.company', site=site.id, lang=lang))

    if company.get('logo'):
        add('ok', 'Logo 已填写', '社交分享图和 Organization 结构化数据有默认图片。')
    else:
        add('warn', '缺少 Logo', '没有页面分享图时会缺少默认 OG 图片。', url_for('core.company', site=site.id, lang=lang))

    if settings.get('slogan') or company.get('slogan') or company.get('description') or company.get('intro'):
        add('ok', '站点简介已填写', '页面 description 缺省时可以回退到站点简介。')
    else:
        add('warn', '缺少站点简介', '建议在公司信息里补一句话简介，作为页面描述兜底。', url_for('core.company', site=site.id, lang=lang))

    pages = {}
    for page_file in list_yaml_files(site.id, 'pages', lang=storage_lang):
        page_key = page_file.stem
        pages[page_key] = read_yaml(site.id, f'pages/{page_file.name}', default={}, lang=storage_lang) or {}

    data = {}
    for data_file in list_yaml_files(site.id, 'data', lang=storage_lang):
        dataset_key = data_file.stem
        data[dataset_key] = read_yaml(site.id, f'data/{data_file.name}', default=[], lang=storage_lang)

    seo_pages = _seo_page_rows(site, lang, settings, pages, data, meta)

    # 只检查菜单会实际渲染的页面/详情页，避免把孤立草稿 YAML 当成 SEO 问题。
    menu_items = menu_lib.ensure_home(
        menu_lib.normalize_for_render(
            menu_lib.upgrade_old_format(settings.get('menu') or [], meta.get('datasets', []))
        )
    )
    tasks = menu_lib.collect_render_tasks(menu_items, tpl_html_dir, data, pages)
    checked_pages = set()
    checked_items = set()
    list_pages_without_description = []
    for task in tasks:
        page_key = task.get('page_key')
        task_type = task.get('type')
        if task_type in ('home', 'page', 'list') and page_key and page_key not in checked_pages:
            checked_pages.add(page_key)
            if page_key not in pages:
                continue
            page = pages.get(page_key, {})
            if isinstance(page, dict) and not page.get('description'):
                if task_type == 'list':
                    list_pages_without_description.append(page_key)
                else:
                    add('warn', f'{page_key} 缺少页面简介', '建议补 80-160 字简介，用于 meta description 和分享摘要。',
                        None)

        if task_type == 'detail':
            item = task.get('item') if isinstance(task.get('item'), dict) else {}
            dataset_key = task.get('dataset_key') or ''
            item_key = (dataset_key, item.get('slug') or item.get('id') or item.get('title') or item.get('name'))
            if item_key in checked_items:
                continue
            checked_items.add(item_key)
            item_title = item.get('title') or item.get('name') or item.get('slug') or '未命名条目'
            if not (item.get('summary') or item.get('description') or item.get('excerpt')):
                current_path = task.get('current_path') or ''
                preview_url = ''
                if current_path:
                    preview_url = f"/preview/{site.id}/{lang}{current_path if current_path.startswith('/') else '/' + current_path}"
                add('warn', f'{dataset_key} / {item_title} 缺少摘要',
                    '详情页 description 和 llms.txt 摘要会变弱，建议补一段简短说明。',
                    url_for('core.dataset_edit', dataset_key=dataset_key, item_id=item.get('id'),
                            _fragment='1', site=site.id, lang=lang, preview_url=preview_url))

    if list_pages_without_description:
        add('info', f'{len(list_pages_without_description)} 个列表页缺少简介',
            '列表页会自动兜底；有时间时可给主要栏目补简介。')

    image_alt_missing = 0
    for task in tasks:
        if task.get('type') != 'detail':
            continue
        item = task.get('item') if isinstance(task.get('item'), dict) else {}
        image_value = item.get('image') or item.get('image_url') or item.get('cover') or item.get('thumbnail')
        has_alt = item.get('alt') or item.get('image_alt') or item.get('imageAlt') or item.get('cover_alt')
        if image_value and not has_alt:
            image_alt_missing += 1
    if image_alt_missing:
        add('info', f'{image_alt_missing} 张详情页图片缺少 alt', '这是可选优化项，不影响自动 SEO 文件生成；有时间再补即可。')

    output_root = Path(current_app.config['OUTPUT_DIR']) / str(site.id)
    missing_output_files = []
    for filename in ('sitemap.xml', 'robots.txt', 'llms.txt'):
        path = output_root / filename
        if path.exists() and path.stat().st_size > 0:
            add('ok', f'{filename} 已生成', '最近一次构建输出中可以找到该文件。')
        else:
            missing_output_files.append(filename)
    if missing_output_files:
        add('warn', 'SEO 附属文件尚未生成', '点击预览、导出或发布后会自动生成 sitemap.xml、robots.txt 和 llms.txt。')

    warn_count = sum(1 for c in checks if c['status'] == 'warn')
    info_count = sum(1 for c in checks if c['status'] == 'info')
    ok_count = sum(1 for c in checks if c['status'] == 'ok')
    score = max(0, 100 - warn_count * 8 - info_count * 2)
    return {
        'score': score,
        'ok_count': ok_count,
        'warn_count': warn_count,
        'info_count': info_count,
        'checks': checks,
        'pages': seo_pages,
        'ai_configured': translation_configured(),
    }


@bp.route('/seo')
def seo_health():
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    report = _seo_health_report(site, lang=lang)
    if request.args.get('_fragment'):
        return render_template('dashboard/panel_seo.html', user=user, site=site, report=report,
                               current_lang=lang, languages=languages, default_lang=default_lang)
    return render_template('dashboard/seo.html', user=user, site=site, report=report, active='seo',
                           current_lang=lang, languages=languages, default_lang=default_lang)


@bp.route('/seo/workspace')
def seo_workspace():
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    report = _seo_health_report(site, lang=lang)
    return render_template('dashboard/seo_workspace.html', user=user, site=site, report=report,
                           current_lang=lang, languages=languages, default_lang=default_lang)


@bp.route('/seo/page/<path:page_key>', methods=['POST'])
def seo_page_update(page_key):
    """保存单个页面的 SEO 标题/简介，供健康检查工作区使用。"""
    _validate_key(page_key)
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    page = read_yaml(site.id, f'pages/{page_key}.yaml', default={}, lang=storage_lang) or {}
    if not isinstance(page, dict):
        page = {}
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    if title:
        page['title'] = title
    else:
        page.pop('title', None)
    if description:
        page['description'] = description
    else:
        page.pop('description', None)
    write_yaml(site.id, f'pages/{page_key}.yaml', page, lang=storage_lang)
    return jsonify({'ok': True})


@bp.route('/seo/page/<path:page_key>/generate', methods=['POST'])
def seo_page_generate(page_key):
    """从页面现有模块生成简介，返回给弹框填入 textarea。"""
    _validate_key(page_key)
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    page = read_yaml(site.id, f'pages/{page_key}.yaml', default={}, lang=storage_lang) or {}
    settings = read_yaml(site.id, 'settings.yaml') or {}
    company_key = _lang_key('company', site, lang, default_lang)
    company = _merge_settings_section(settings.get('company'), settings.get(company_key))
    company_name = company.get('name') or settings.get('title') or site.name
    page_title = page.get('title') or page_key
    fallback = _auto_page_description(page) or (
        settings.get('slogan') or company.get('slogan') or
        company.get('description') or company.get('intro') or company.get('name') or ''
    )
    page_text = _page_text_for_seo(page) or fallback
    if translation_configured():
        try:
            description = generate_seo_description(page_title, page_text, company_name=company_name, lang=lang)
            return jsonify({'ok': True, 'description': description, 'source': 'ai'})
        except Exception as exc:
            current_app.logger.warning('AI 生成 SEO 简介失败，回退本地摘要: %s', exc)
            return jsonify({'ok': True, 'description': fallback, 'source': 'fallback',
                            'warning': f'AI 生成失败，已回退本地摘要: {exc}'})
    return jsonify({'ok': True, 'description': fallback, 'source': 'fallback',
                    'warning': 'AI 未配置，已使用本地摘要'})


def _load_dataset_for_seo(site_id, dataset_key, storage_lang):
    raw = read_yaml(site_id, f'data/{dataset_key}.yaml', default=[], lang=storage_lang)
    if raw is None:
        raw = []
    return raw


def _find_dataset_item(raw, item_key):
    items = _dataset_items(raw)
    item_key = str(item_key)
    for item in items:
        if not isinstance(item, dict):
            continue
        candidates = [item.get('slug'), item.get('id'), item.get('title'), item.get('name')]
        if any(str(value) == item_key for value in candidates if value is not None):
            return item
    return None


@bp.route('/seo/detail/<path:dataset_key>/<path:item_key>', methods=['POST'])
def seo_detail_update(dataset_key, item_key):
    """保存列表详情页的独立 SEO 标题/简介，不覆盖业务标题和正文摘要。"""
    _validate_key(dataset_key)
    _validate_key(item_key)
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    raw = _load_dataset_for_seo(site.id, dataset_key, storage_lang)
    item = _find_dataset_item(raw, item_key)
    if item is None:
        abort(404)
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    if title:
        item['seo_title'] = title
    else:
        item.pop('seo_title', None)
    if description:
        item['seo_description'] = description
    else:
        item.pop('seo_description', None)
    write_yaml(site.id, f'data/{dataset_key}.yaml', raw, lang=storage_lang)
    return jsonify({'ok': True})


@bp.route('/seo/detail/<path:dataset_key>/<path:item_key>/generate', methods=['POST'])
def seo_detail_generate(dataset_key, item_key):
    """从详情页数据生成 SEO 简介。"""
    _validate_key(dataset_key)
    _validate_key(item_key)
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    raw = _load_dataset_for_seo(site.id, dataset_key, storage_lang)
    item = _find_dataset_item(raw, item_key)
    if item is None:
        abort(404)
    settings = read_yaml(site.id, 'settings.yaml') or {}
    company_key = _lang_key('company', site, lang, default_lang)
    company = _merge_settings_section(settings.get('company'), settings.get(company_key))
    company_name = company.get('name') or settings.get('title') or site.name
    page_title = item.get('seo_title') or item.get('title') or item.get('name') or str(item_key)
    fallback = _plain_text(
        item.get('summary') or item.get('description') or item.get('excerpt') or
        item.get('body') or item.get('content') or page_title
    )[:180].rstrip()
    page_text = _detail_item_text_for_seo(item) or fallback
    if translation_configured():
        try:
            description = generate_seo_description(page_title, page_text, company_name=company_name, lang=lang)
            return jsonify({'ok': True, 'description': description, 'source': 'ai'})
        except Exception as exc:
            current_app.logger.warning('AI 生成详情页 SEO 简介失败，回退本地摘要: %s', exc)
            return jsonify({'ok': True, 'description': fallback, 'source': 'fallback',
                            'warning': f'AI 生成失败，已回退本地摘要: {exc}'})
    return jsonify({'ok': True, 'description': fallback, 'source': 'fallback',
                    'warning': 'AI 未配置，已使用本地摘要'})


@bp.route('/company', methods=['GET', 'POST'])
def company():
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}

    is_fragment = request.args.get('_fragment') is not None
    lang, languages, default_lang = _get_panel_lang(site)
    company_key = _lang_key('company', site, lang, default_lang)
    contact_key = _lang_key('contact', site, lang, default_lang)

    if request.method == 'POST':
        settings.setdefault('company', {})
        settings.setdefault('contact', {})
        settings.setdefault(company_key, {})
        settings.setdefault(contact_key, {})
        for field in ('name', 'short_name', 'description'):
            settings[company_key][field] = request.form.get(f'company.{field}', '').strip()
        settings['company']['icp'] = request.form.get('company.icp', '').strip()
        if company_key != 'company':
            for field in ('logo', 'favicon', 'icp'):
                settings[company_key].pop(field, None)
        logo_upload = request.files.get('company_logo_file')
        if logo_upload and logo_upload.filename:
            try:
                settings['company']['logo'] = _save_uploaded_image(site.id, logo_upload, prefix='company-logo')
            except Exception as exc:
                flash(f'Logo 上传失败: {exc}')
                if request.form.get('_workspace') == '1':
                    return redirect(url_for('core.company_workspace', site=site.id, lang=lang))
                if is_fragment:
                    return redirect(url_for('core.company', _fragment='1', site=site.id, lang=lang))
                return redirect(url_for('core.company', site=site.id, lang=lang))
        elif 'company.logo' in request.form:
            settings['company']['logo'] = request.form.get('company.logo', '').strip()
        # Favicon 上传（favicon 通常较小，复用图片上传逻辑转 WebP）
        favicon_upload = request.files.get('company_favicon_file')
        if favicon_upload and favicon_upload.filename:
            try:
                settings['company']['favicon'] = _save_uploaded_image(site.id, favicon_upload, prefix='company-favicon')
            except Exception as exc:
                flash(f'Favicon 上传失败: {exc}')
                if request.form.get('_workspace') == '1':
                    return redirect(url_for('core.company_workspace', site=site.id, lang=lang))
                if is_fragment:
                    return redirect(url_for('core.company', _fragment='1', site=site.id, lang=lang))
                return redirect(url_for('core.company', site=site.id, lang=lang))
        elif 'company.favicon' in request.form:
            settings['company']['favicon'] = request.form.get('company.favicon', '').strip()
        for field in ('phone', 'email', 'wechat'):
            settings['contact'][field] = request.form.get(f'contact.{field}', '').strip()
        if contact_key != 'contact':
            for field in ('phone', 'email', 'mobile', 'wechat'):
                settings[contact_key].pop(field, None)
        for field in ('address',):
            settings[contact_key][field] = request.form.get(f'contact.{field}', '').strip()
        admin_settings = settings.setdefault('admin', {})
        admin_settings['auto_save'] = bool(request.form.get('admin.auto_save'))
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        if request.form.get('_basic_settings') == '1':
            if request.form.get('_embed') == '1':
                return redirect(url_for('core.basic_settings', embed='1', site=site.id, lang=lang, tab='company'))
            return redirect(url_for('core.basic_settings', _fragment='1', site=site.id, lang=lang, tab='company'))
        if request.form.get('_workspace') == '1':
            return redirect(url_for('core.company_workspace', site=site.id, lang=lang))
        if is_fragment:
            return redirect(url_for('core.company', _fragment='1', site=site.id, lang=lang))
        return redirect(url_for('core.company', site=site.id, lang=lang))

    current_company = _merge_settings_section(settings.get('company'), settings.get(company_key))
    current_contact = _merge_settings_section(settings.get('contact'), settings.get(contact_key))
    source_company = settings.get('company', {})
    source_contact = settings.get('contact', {})

    if is_fragment:
        return render_template('dashboard/panel_company.html',
                               user=user, site=site,
                               company=current_company,
                               contact=current_contact,
                               source_company=source_company,
                               source_contact=source_contact,
                               current_lang=lang,
                               languages=languages,
                               default_lang=default_lang,
                               admin_settings=settings.get('admin') or {})
    return render_template('dashboard/company.html',
                           user=user, site=site,
                           company=current_company,
                           contact=current_contact,
                           source_company=source_company,
                           source_contact=source_contact,
                           current_lang=lang,
                           languages=languages,
                           default_lang=default_lang,
                           admin_settings=settings.get('admin') or {},
                           active='company')


# ---- 留言管理 ----

@bp.route('/messages')
def messages():
    """店主后台：留言列表页, 按时间倒序展示非垃圾留言.

    支持 ?embed=1 参数: 在中间栏 iframe 内展示时, 使用无外壳的嵌入版模板.
    """
    user, site = _current_context()
    msgs = ContactMessage.query.filter_by(site_id=site.id, is_spam=False)\
        .order_by(ContactMessage.created_at.desc()).all()
    # 未读计数, 供侧边栏 badge 使用
    unread_count = ContactMessage.query.filter_by(site_id=site.id, is_read=False, is_spam=False).count()
    # 中间栏嵌入模式: 去掉外壳 (侧栏/顶栏), 只渲染内容区域
    if request.args.get('embed') == '1':
        return render_template('dashboard/messages_embed.html',
                               user=user, site=site, messages=msgs,
                               unread_count=unread_count, active='messages')
    return render_template('dashboard/messages.html',
                           user=user, site=site, messages=msgs,
                           unread_count=unread_count, active='messages')


@bp.route('/messages/<int:msg_id>/read', methods=['POST'])
def message_mark_read(msg_id):
    """标记留言为已读."""
    _, site = _current_context()
    msg = ContactMessage.query.filter_by(id=msg_id, site_id=site.id).first()
    if msg:
        msg.is_read = True
        db.session.commit()
    embed = request.form.get('_embed', '')
    return redirect(url_for('core.messages', embed=embed) if embed else url_for('core.messages'))


@bp.route('/messages/<int:msg_id>/spam', methods=['POST'])
def message_mark_spam(msg_id):
    """软删除：标记留言为垃圾."""
    _, site = _current_context()
    msg = ContactMessage.query.filter_by(id=msg_id, site_id=site.id).first()
    if msg:
        msg.is_spam = True
        db.session.commit()
        flash('已标记为垃圾')
    embed = request.form.get('_embed', '')
    return redirect(url_for('core.messages', embed=embed) if embed else url_for('core.messages'))


@bp.route('/products')
def products():
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    products = datasets.load(site.id, 'products', lang=storage_lang)
    if request.args.get('_fragment'):
        blocks = _get_available_blocks(site.template_name)
        return render_template('dashboard/panel_data_list.html',
                               user=user, site=site,
                               dataset_key='products', items=products,
                               blocks=blocks,
                               current_lang=lang, languages=languages, default_lang=default_lang)
    return render_template('dashboard/products.html',
                           user=user, site=site, products=products, active='products')


@bp.route('/products/new', methods=['POST'])
def product_new():
    _, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    n = len(datasets.load(site.id, 'products', lang=storage_lang)) + 1
    new_id = datasets.add(site.id, 'products', {
        'name': '新产品', 'slug': f'product-{n}',
        'summary': '', 'description': '', 'cover': '', 'category': '',
        'price': '', 'specs': {},
    }, lang=storage_lang)
    return redirect(url_for('core.product_edit', product_id=new_id, site=site.id, lang=lang))


@bp.route('/products/<int:product_id>/delete', methods=['POST'])
def product_delete(product_id):
    _, site = _current_context()
    lang, _, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    datasets.remove(site.id, 'products', product_id, lang=storage_lang)
    flash('已删除')
    return redirect(url_for('core.products', site=site.id, lang=lang))


@bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def product_edit(product_id):
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    product = datasets.find(site.id, 'products', product_id, lang=storage_lang)
    if not product:
        abort(404, f'产品不存在: id={product_id}')

    if request.method == 'POST':
        fields = {f: request.form.get(f, '').strip()
                  for f in ('name', 'slug', 'category', 'summary', 'description', 'cover', 'price')}
        fields['cover'] = _uploaded_image_or_form(site.id, 'cover', 'cover_file', 'product-cover')
        # specs: 多行 "键: 值"
        specs = {}
        for line in request.form.get('specs', '').strip().splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                if k.strip():
                    specs[k.strip()] = v.strip()
        fields['specs'] = specs
        datasets.update(site.id, 'products', product_id, fields, lang=storage_lang)
        flash('已保存')
        return redirect(url_for('core.product_edit', product_id=product_id, site=site.id, lang=lang))

    return render_template('dashboard/product_edit.html',
                           user=user, site=site, product=product, active='products')


# ----- 功能 -----

@bp.route('/features')
def features():
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    items = datasets.load(site.id, 'features', lang=storage_lang)
    if request.args.get('_fragment'):
        blocks = _get_available_blocks(site.template_name)
        return render_template('dashboard/panel_data_list.html',
                               user=user, site=site,
                               dataset_key='features', items=items,
                               blocks=blocks,
                               current_lang=lang, languages=languages, default_lang=default_lang)
    return render_template('dashboard/features.html',
                           user=user, site=site, items=items, active='features')


@bp.route('/features/new', methods=['POST'])
def feature_new():
    _, site = _current_context()
    lang, _, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    new_id = datasets.add(site.id, 'features',
                          {'icon': '', 'title': '新功能', 'desc': ''}, lang=storage_lang)
    return redirect(url_for('core.feature_edit', item_id=new_id, site=site.id, lang=lang))


@bp.route('/features/<int:item_id>/delete', methods=['POST'])
def feature_delete(item_id):
    _, site = _current_context()
    lang, _, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    datasets.remove(site.id, 'features', item_id, lang=storage_lang)
    flash('已删除')
    return redirect(url_for('core.features', site=site.id, lang=lang))


@bp.route('/features/<int:item_id>/edit', methods=['GET', 'POST'])
def feature_edit(item_id):
    user, site = _current_context()
    lang, _, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    item = datasets.find(site.id, 'features', item_id, lang=storage_lang)
    if not item:
        abort(404)
    if request.method == 'POST':
        fields = {f: request.form.get(f, '').strip() for f in ('icon', 'title', 'desc')}
        datasets.update(site.id, 'features', item_id, fields, lang=storage_lang)
        flash('已保存')
        return redirect(url_for('core.feature_edit', item_id=item_id, site=site.id, lang=lang))
    return render_template('dashboard/feature_edit.html',
                           user=user, site=site, item=item, active='features')


# ----- 博客 -----

@bp.route('/blog')
def blog():
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    items = datasets.load(site.id, 'posts', lang=storage_lang)
    if request.args.get('_fragment'):
        blocks = _get_available_blocks(site.template_name)
        return render_template('dashboard/panel_data_list.html',
                               user=user, site=site,
                               dataset_key='posts', items=items,
                               blocks=blocks,
                               current_lang=lang, languages=languages, default_lang=default_lang)
    return render_template('dashboard/blog.html',
                           user=user, site=site, items=items, active='blog')


@bp.route('/blog/new', methods=['POST'])
def post_new():
    from datetime import date as _date
    _, site = _current_context()
    lang, _, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    n = len(datasets.load(site.id, 'posts', lang=storage_lang)) + 1
    new_id = datasets.add(site.id, 'posts', {
        'slug': f'post-{n}', 'title': '新文章', 'date': str(_date.today()),
        'cover': '', 'excerpt': '', 'body': '',
    }, lang=storage_lang)
    return redirect(url_for('core.post_edit', item_id=new_id, site=site.id, lang=lang))


@bp.route('/blog/<int:item_id>/delete', methods=['POST'])
def post_delete(item_id):
    _, site = _current_context()
    lang, _, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    datasets.remove(site.id, 'posts', item_id, lang=storage_lang)
    flash('已删除')
    return redirect(url_for('core.blog', site=site.id, lang=lang))


@bp.route('/blog/<int:item_id>/edit', methods=['GET', 'POST'])
def post_edit(item_id):
    user, site = _current_context()
    lang, _, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    item = datasets.find(site.id, 'posts', item_id, lang=storage_lang)
    if not item:
        abort(404)
    if request.method == 'POST':
        fields = {f: request.form.get(f, '').strip()
                  for f in ('title', 'slug', 'date', 'cover', 'excerpt', 'body')}
        fields['cover'] = _uploaded_image_or_form(site.id, 'cover', 'cover_file', 'post-cover')
        datasets.update(site.id, 'posts', item_id, fields, lang=storage_lang)
        flash('已保存')
        return redirect(url_for('core.post_edit', item_id=item_id, site=site.id, lang=lang))
    return render_template('dashboard/post_edit.html',
                           user=user, site=site, item=item, active='blog')


@bp.route('/pages/home', methods=['GET', 'POST'])
def page_home():
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    page = read_yaml(site.id, 'pages/home.yaml', lang=storage_lang) or {}

    # 检测格式: modules 数组 vs 旧固定 key
    is_modules_format = 'modules' in page

    if request.method == 'POST':
        if is_modules_format or request.form.get('_format') == 'modules':
            # modules 数组格式保存
            existing_modules = page.get('modules', [])
            page['modules'] = _parse_modules_form(request.form, existing_modules)
            page.pop('hero', None)
            for k in ('featured_section', 'features_section', 'about_brief', 'blog_section', 'subscribe_section'):
                page.pop(k, None)
        else:
            # 旧固定 key 格式保存
            page.setdefault('hero', {})
            for f in ('title', 'subtitle', 'badge', 'cta_text', 'cta_url', 'video_url', 'background_image'):
                page['hero'][f] = request.form.get(f'hero.{f}', '').strip()
            for key in ('featured_section', 'features_section', 'about_brief', 'blog_section', 'subscribe_section'):
                page.setdefault(key, {})
                page[key]['enabled'] = bool(request.form.get(f'{key}.enabled'))
                for f in ('title', 'subtitle', 'body', 'cta_text', 'cta_url'):
                    v = request.form.get(f'{key}.{f}')
                    if v is not None:
                        page[key][f] = v.strip()
                limit = request.form.get(f'{key}.limit')
                if limit:
                    try:
                        page[key]['limit'] = int(limit)
                    except ValueError:
                        pass
        write_yaml(site.id, 'pages/home.yaml', page, lang=storage_lang)
        flash('已保存')
        if request.args.get('_fragment'):
            return redirect(url_for('core.page_home', _fragment='1', site=site.id, lang=lang))
        return redirect(url_for('core.page_home', site=site.id, lang=lang))

    # 准备渲染上下文
    from .icon_registry import ICON_REGISTRY, icon_names
    from .style_registry import STYLE_REGISTRY
    blocks = _get_available_blocks(site.template_name)
    if is_modules_format:
        page.setdefault('modules', [])
    else:
        page.setdefault('hero', {})
        for key in ('featured_section', 'features_section', 'about_brief', 'blog_section', 'subscribe_section'):
            page.setdefault(key, {})
    # 将 meta.yaml 默认值合并到模块数据，让属性面板显示 CSS 兜底值
    _merge_block_defaults(page.get('modules'), blocks)

    # 收集可用的列表型数据集（供 data-source="" 下拉选择）
    settings_data = read_yaml(site.id, 'settings.yaml') or {}
    tpl_root = Path(current_app.config['TEMPLATES_DIR']) / site.template_name
    meta_data = _yaml.safe_load((tpl_root / 'meta.yaml').read_text(encoding='utf-8')) if (tpl_root / 'meta.yaml').exists() else {}
    raw_menu = settings_data.get('menu', [])
    normalized = menu_lib.ensure_home(menu_lib.normalize_for_render(
        menu_lib.upgrade_old_format(raw_menu, meta_data.get('datasets', []))
    ))
    all_list_datasets = menu_lib.collect_list_targets(normalized)  # #22

    return render_template('dashboard/panel_page_edit.html',
                           user=user, site=site, page=page,
                           page_key='home', page_display_name='首页',
                           is_modules_format=is_modules_format,
                           blocks=blocks,
                           all_list_datasets=all_list_datasets,
                           style_registry=STYLE_REGISTRY,
                           icon_list=icon_names(),
                           icon_registry=ICON_REGISTRY,
                           active='pages_home',
                           current_lang=lang,
                           languages=languages,
                           default_lang=default_lang)


@bp.route('/pages')
def pages():
    return redirect(url_for('core.index'))


@bp.route('/account')
def account():
    user, site = _current_context()
    site_count = Site.query.filter_by(owner_id=user.id).count() if user else 0
    if request.args.get('_fragment'):
        return render_template('dashboard/panel_account.html',
                               user=user, site=site, site_count=site_count)
    return render_template('dashboard/account.html',
                           user=user, site=site, site_count=site_count, active='account')


@bp.route('/sites/delete', methods=['POST'])
def site_delete():
    """删除当前站点：清除数据库记录 + 站点文件夹 + output 文件."""
    from .db import db

    import shutil as _shutil

    user, site = _current_context()
    site_id = site.id
    site_name = site.name

    # 删除站点文件夹
    site_folder = Path(current_app.config['SITES_DIR']) / str(site_id)
    if site_folder.exists():
        try:
            _shutil.rmtree(site_folder)
        except OSError as exc:
            current_app.logger.warning('删除站点文件夹 %s 失败: %s', site_folder, exc)

    # 删除 output
    output_dir = Path(current_app.config['OUTPUT_DIR']) / str(site_id)
    if output_dir.exists():
        try:
            _shutil.rmtree(output_dir)
        except OSError as exc:
            current_app.logger.warning('删除 output 目录 %s 失败: %s', output_dir, exc)

    # 删除数据库记录
    db.session.delete(site)
    db.session.commit()

    flash(f'站点 "{site_name}" 已删除', 'success')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.args.get('_fragment'):
        return jsonify({'ok': True, 'redirect': url_for('core.overview')})
    return redirect(url_for('core.overview'))
def _save_link_list(site_id, settings_key):
    """收集表单 label[] 和 url[], 写回 settings.yaml[settings_key]."""
    settings = read_yaml(site_id, 'settings.yaml') or {}
    labels = request.form.getlist('label[]')
    urls = request.form.getlist('url[]')
    items = []
    for label, url in zip(labels, urls):
        label, url = label.strip(), url.strip()
        if label or url:
            items.append({'label': label, 'url': url})
    settings[settings_key] = items
    write_yaml(site_id, 'settings.yaml', settings)


@bp.route('/settings/header', methods=['GET', 'POST'])
def header_edit():
    """网站头部变体选择 + 语言切换按钮配置."""
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    is_fragment = request.args.get('_fragment') is not None
    lang, languages, default_lang = _get_panel_lang(site)

    # Header 变体列表（模板 meta 中定义）
    tpl_meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    tpl_meta = _yaml.safe_load(tpl_meta_path.read_text(encoding='utf-8')) if tpl_meta_path.exists() else {}
    header_variants = tpl_meta.get('header_variants', [
        {'key': 'logo_left_menu_right', 'label': 'Logo 左 + 菜单右', 'description': '经典布局，适合大多数企业网站'},
        {'key': 'logo_center_menu_below', 'label': 'Logo 居中 + 菜单下方', 'description': '对称布局，适合品牌展示'},
        {'key': 'minimal_hamburger', 'label': '极简（汉堡菜单）', 'description': 'Logo 左 + 汉堡菜单，移动端友好'},
    ])

    # 模板定义的全部语言
    template_languages = tpl_meta.get('languages', [
        {'code': 'zh-CN', 'name': '简体中文', 'flag': '🇨🇳'},
        {'code': 'zh-TW', 'name': '繁體中文', 'flag': '🇹🇼'},
        {'code': 'en', 'name': 'English', 'flag': '🇺🇸'},
    ])
    # 当前启用的语言列表以 Site 模型为准，避免 settings.header.enabled_languages 旧缓存污染面板显示
    all_template_codes = [l['code'] for l in template_languages]
    enabled_languages = [c for c in (site.enabled_languages or all_template_codes) if c in all_template_codes]
    # 复选框展示模板全部语言（不按 enabled 过滤），让管理员能看到并勾选新增的语言版本
    visible_template_languages = list(template_languages)

    # 语言切换按钮样式列表
    lang_switcher_styles = [
        {'key': 'inline_row', 'label': '水平行内（中文 | EN | JP）'},
        {'key': 'vertical_dropdown', 'label': '垂直下拉'},
        {'key': 'flag_icon', 'label': '旗帜 + 简称'},
    ]

    if request.method == 'POST':
        header = settings.setdefault('header', {})
        header['variant'] = request.form.get('header_variant', header_variants[0]['key'])
        header['language_switcher'] = {
            'enabled': bool(request.form.get('lang_switcher_enabled')),
            'style': request.form.get('lang_switcher_style', 'vertical_dropdown'),
        }
        # 保存启用的语言版本（多选）
        selected_langs = request.form.getlist('enabled_lang')
        all_codes = [l['code'] for l in template_languages]
        if selected_langs:
            # 只保留模板中存在的语言代码
            header['enabled_languages'] = [c for c in selected_langs if c in all_codes]
        else:
            # 至少保留默认语言
            default_lang = tpl_meta.get('default_language', all_codes[0] if all_codes else 'zh-CN')
            header['enabled_languages'] = [default_lang]
        # 同步到 Site 模型
        site.enabled_languages = header['enabled_languages']
        from .db import db
        db.session.commit()
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        current_lang = request.args.get('lang')
        redirect_args = {'site': site.id}
        if current_lang:
            redirect_args['lang'] = current_lang
        if is_fragment:
            return redirect(url_for('core.header_edit', _fragment='1', **redirect_args))
        return redirect(url_for('core.header_edit', **redirect_args))

    current_header = settings.get('header') or {}
    header_variant_keys = [v['key'] for v in header_variants]
    if current_header.get('variant') not in header_variant_keys:
        current_header = dict(current_header)
        current_header['variant'] = header_variant_keys[0] if header_variant_keys else 'logo_left_menu_right'
    # 显示仍以 Site.enabled_languages 为准；保存时会同步 settings.header.enabled_languages
    enabled_languages = [c for c in (site.enabled_languages or all_template_codes) if c in all_template_codes]
    # 复选框展示模板全部语言（不按 enabled 过滤），让管理员能看到并勾选新增的语言版本
    visible_template_languages = list(template_languages)
    if is_fragment:
        return render_template('dashboard/panel_header.html',
                               user=user, site=site,
                               header_variants=header_variants,
                               template_languages=visible_template_languages,
                               enabled_languages=enabled_languages,
                               lang_switcher_styles=lang_switcher_styles,
                               current_header=current_header,
                               settings=settings)
    return render_template('dashboard/header_edit.html',
                           user=user, site=site,
                           header_variants=header_variants,
                           template_languages=visible_template_languages,
                           enabled_languages=enabled_languages,
                           lang_switcher_styles=lang_switcher_styles,
                           current_header=current_header,
                           active='header')


@bp.route('/settings/footer_variant', methods=['GET', 'POST'])
def footer_variant_edit():
    """网站底部变体选择."""
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    is_fragment = request.args.get('_fragment') is not None
    lang, languages, default_lang = _get_panel_lang(site)
    footer_key = _lang_key('footer', site, lang, default_lang)

    # Footer 变体列表
    tpl_meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    tpl_meta = _yaml.safe_load(tpl_meta_path.read_text(encoding='utf-8')) if tpl_meta_path.exists() else {}
    footer_variants = tpl_meta.get('footer_variants', [
        {'key': 'columns', 'label': '栏目模式', 'description': '多列链接和文本栏目'},
        {'key': 'minimal', 'label': '极简模式', 'description': '仅显示版权和备案信息'},
        {'key': 'columns_social', 'label': '栏目 + 社交', 'description': '左侧公司 Logo 和社交图标，右侧栏目'},
    ])

    if request.method == 'POST':
        footer = settings.setdefault(footer_key, {})
        footer['variant'] = request.form.get('footer_variant', 'columns')
        footer['copyright'] = request.form.get('copyright', '').strip()
        footer['icp'] = request.form.get('icp', '').strip()

        if any(k == 'social_enabled' or k.startswith('social_') for k in request.form):
            social = settings.setdefault('social', {})
            social['enabled'] = bool(request.form.get('social_enabled'))
            for platform in ('github', 'twitter', 'facebook', 'linkedin', 'youtube'):
                social[platform] = request.form.get(f'social_{platform}', '').strip()

        # 解析底部栏目
        col_count = 0
        try:
            col_count = int(request.form.get('footer_column_count', '0'))
        except (ValueError, TypeError):
            pass
        columns = []
        for ci in range(col_count):
            col = {
                'type': request.form.get(f'footer_col_{ci}_type', 'menu').strip(),
                'title': request.form.get(f'footer_col_{ci}_title', '').strip(),
            }
            link_count = 0
            try:
                link_count = int(request.form.get(f'footer_col_{ci}_link_count', '0'))
            except (ValueError, TypeError):
                pass
            links = []
            for li in range(link_count):
                label = request.form.get(f'footer_col_{ci}_link_{li}_label', '').strip()
                url = request.form.get(f'footer_col_{ci}_link_{li}_url', '').strip()
                if label or url:
                    links.append({'label': label, 'url': url})
            col['links'] = links
            columns.append(col)
        if columns:
            footer['columns'] = columns
        else:
            footer.pop('columns', None)

        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        if is_fragment:
            return redirect(url_for('core.footer_variant_edit', _fragment='1', site=site.id, lang=lang))
        return redirect(url_for('core.footer_variant_edit', site=site.id, lang=lang))

    current_footer = settings.get(footer_key) or settings.get('footer') or {}
    source_footer = settings.get('footer') or {}
    footer_variant_keys = [v['key'] for v in footer_variants]
    if current_footer.get('variant') not in footer_variant_keys:
        current_footer = dict(current_footer)
        current_footer['variant'] = footer_variant_keys[0] if footer_variant_keys else 'columns'

    if is_fragment:
        return render_template('dashboard/panel_footer_variant.html',
                               user=user, site=site,
                               footer_variants=footer_variants,
                               current_footer=current_footer,
                               source_footer=source_footer,
                               settings=settings,
                               current_lang=lang,
                               languages=languages,
                               default_lang=default_lang)
    return render_template('dashboard/footer_variant.html',
                           user=user, site=site,
                           footer_variants=footer_variants,
                           current_footer=current_footer,
                           source_footer=source_footer,
                           settings=settings,
                           current_lang=lang,
                           languages=languages,
                           default_lang=default_lang,
                           active='footer_variant')


@bp.route('/settings/menu', methods=['GET', 'POST'])
def menu_edit():
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    is_fragment = request.args.get('_fragment') is not None

    lang, languages, default_lang = _get_panel_lang(site)

    # ── 自动迁移: 把旧 menu_<lang> 转为 menu_labels ──
    menu_labels = settings.get('menu_labels') or {}
    migrated = False
    for lopt in (languages or []):
        code = lopt['code']
        old_key = f'menu_{code}'
        if old_key in settings and settings[old_key]:
            old_menu = settings[old_key]
            old_labels = menu_lib.extract_labels(old_menu)
            if old_labels:
                menu_labels[code] = old_labels
            del settings[old_key]
            migrated = True
    # 兜底: 只对默认语言用当前 menu 标签初始化 menu_labels，避免把简体中文
    # 错误复制到繁体中文等非默认语言（_language_label_map 已做 fallback 合并）
    if migrated or not menu_labels:
        fallback_labels = menu_lib.extract_labels(settings.get('menu', []))
        if fallback_labels:
            if default_lang not in menu_labels or not menu_labels[default_lang]:
                menu_labels[default_lang] = dict(fallback_labels)
            migrated = True
    if migrated:
        settings['menu_labels'] = menu_labels

    if request.method == 'POST':
        menu_json = request.form.get('menu_json', '').strip()
        if menu_json:
            try:
                raw_items = _yaml.safe_load(menu_json) or []
            except _yaml.YAMLError:
                raw_items = []
            items = menu_lib.clean_for_storage(raw_items)
        else:
            # 旧表单兼容分支（一般不会走到了）
            labels = request.form.getlist('label[]')
            raw_items = [{'label': '首页', 'type': 'home'}]
            types = request.form.getlist('type[]')
            targets_list = request.form.getlist('target_list[]')
            urls_link = request.form.getlist('url_link[]')
            dropdown_styles = request.form.getlist('dropdown_style[]')
            children_values = request.form.getlist('children_json[]')
            for i, label in enumerate(labels):
                label = label.strip()
                if not label:
                    continue
                t = types[i] if i < len(types) else 'link'
                raw = {'label': label, 'type': t}
                if t in ('list', 'page'):
                    target = targets_list[i].strip() if i < len(targets_list) else ''
                    if target:
                        raw['target'] = target
                elif t == 'link':
                    url = urls_link[i].strip() if i < len(urls_link) else ''
                    if url:
                        raw['url'] = url
                dropdown_style = dropdown_styles[i].strip() if i < len(dropdown_styles) else ''
                if dropdown_style:
                    raw['dropdown_style'] = dropdown_style
                children_raw = children_values[i].strip() if i < len(children_values) else ''
                if children_raw:
                    try:
                        children = _yaml.safe_load(children_raw) or []
                    except _yaml.YAMLError:
                        children = []
                    if isinstance(children, list):
                        raw['children'] = children
                raw_items.append(raw)
            items = menu_lib.clean_for_storage(raw_items)

        # 保存：结构写入 menu，标签写入 menu_labels.<lang>
        # 默认语言直接覆盖 menu；非默认语言用 merge_structure 保留已有标签
        if lang == default_lang:
            settings['menu'] = items
        else:
            settings['menu'] = menu_lib.merge_structure(settings.get('menu', []), items)
        labels = menu_lib.extract_labels(items)
        if labels:
            menu_labels = settings.get('menu_labels') or {}
            menu_labels[lang] = labels
            settings['menu_labels'] = menu_labels
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存，首页已保持为固定入口')
        if is_fragment:
            return redirect(url_for('core.menu_edit', _fragment='1', site=site.id, lang=lang))
        return redirect(url_for('core.menu_edit', site=site.id, lang=lang))

    # GET: 加载菜单 —— 共享结构 + 当前语言标签覆盖
    meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
    raw_menu = settings.get('menu') or meta.get('default_menu', [])
    items = menu_lib.ensure_home(
        menu_lib.upgrade_old_format(raw_menu, meta.get('datasets', []))
    )
    # 所有语言：用 menu_labels 覆盖标签（让用户看到当前语言的翻译）
    labels = (settings.get('menu_labels') or {}).get(lang, {})
    if labels:
        items = menu_lib.apply_labels(items, labels)

    # 默认语言菜单（AI 翻译原文来源）
    default_menu_raw = settings.get('menu') or meta.get('default_menu', [])
    source_menu = menu_lib.ensure_home(
        menu_lib.upgrade_old_format(default_menu_raw, meta.get('datasets', []))
    )

    if is_fragment:
        return render_template('dashboard/panel_menu.html',
                               user=user, site=site, items=items,
                               source_menu=source_menu,
                               current_lang=lang, languages=languages, default_lang=default_lang)
    return render_template('dashboard/menu.html',
                           user=user, site=site, items=items, active='menu',
                           source_menu=source_menu,
                           current_lang=lang, languages=languages, default_lang=default_lang)


@bp.route('/settings/footer', methods=['GET', 'POST'])
def footer_edit():
    """旧页脚链接页面 —— 已迁移至 footer_variant_edit，自动转换旧数据格式"""
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}

    # 迁移旧的 footer_links 数据到新 footer.columns 格式
    old_links = settings.pop('footer_links', None)
    if old_links:
        footer = settings.setdefault('footer', {})
        existing_cols = footer.get('columns', [])
        if not existing_cols:
            footer['variant'] = 'columns'
            footer['columns'] = [{
                'type': 'menu',
                'title': '快速链接',
                'links': old_links
            }]
            write_yaml(site.id, 'settings.yaml', settings)
            flash('页脚链接数据已自动迁移到新版格式')

    return redirect(url_for('core.footer_variant_edit', site=site.id))


@bp.route('/settings/social', methods=['GET', 'POST'])
def social_edit():
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    is_fragment = request.args.get('_fragment') is not None
    if request.method == 'POST':
        social = settings.setdefault('social', {})
        for platform in ('github', 'twitter', 'facebook', 'linkedin', 'youtube'):
            social[platform] = request.form.get(platform, '').strip()
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        if is_fragment:
            return redirect(url_for('core.social_edit', _fragment='1', site=site.id))
        return redirect(url_for('core.social_edit', site=site.id))
    social = settings.get('social') or {}
    if is_fragment:
        return render_template('dashboard/panel_social.html',
                               user=user, site=site, social=social)
    return render_template('dashboard/social.html',
                           user=user, site=site, social=social, active='social')


@bp.route('/settings/theme', methods=['GET', 'POST'])
def theme_edit():
    user, site = _current_context()
    settings = read_yaml(site.id, 'settings.yaml') or {}
    is_fragment = request.args.get('_fragment') is not None
    tpl_meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    tpl_meta = _yaml.safe_load(tpl_meta_path.read_text(encoding='utf-8')) if tpl_meta_path.exists() else {}
    default_theme = tpl_meta.get('default_theme') or {}

    if request.method == 'POST':
        # 颜色值会被 _base.html 用 |safe 注入 <style> 块（关闭转义），
        # 必须在入库前按白名单校验，否则 `red}</style><script>...` 可闭合标签注入脚本。
        # 复用 block_renderer 的同一套颜色白名单，保持全项目一致。
        from .block_renderer import _SAFE_COLOR
        theme = settings.setdefault('theme', {})
        for key in ('color-primary', 'color-bg', 'color-surface', 'color-text', 'color-text-secondary', 'color-border'):
            v = request.form.get(key, '').strip()
            if v and _SAFE_COLOR.match(v):
                theme[key] = v
            else:
                # 空值或非法颜色一律清除该键，回退到模板默认色
                theme.pop(key, None)
        # 清理旧版短 key（迁移前遗留数据）
        for old_key in ('accent', 'bg', 'surface', 'text', 'text_muted', 'border'):
            theme.pop(old_key, None)
        write_yaml(site.id, 'settings.yaml', settings)
        flash('已保存')
        if request.form.get('_basic_settings') == '1':
            lang, _, default_lang = _get_panel_lang(site)
            if request.form.get('_embed') == '1':
                return redirect(url_for('core.basic_settings', embed='1', site=site.id, lang=lang, tab='theme'))
            return redirect(url_for('core.basic_settings', _fragment='1', site=site.id, lang=lang, tab='theme'))
        if request.form.get('_workspace') == '1':
            return redirect(url_for('core.theme_workspace', site=site.id))
        if is_fragment:
            return redirect(url_for('core.theme_edit', _fragment='1', site=site.id))
        return redirect(url_for('core.theme_edit', site=site.id))

    theme = settings.get('theme') or {}
    if is_fragment:
        return render_template('dashboard/panel_theme.html',
                               user=user, site=site, theme=theme, default_theme=default_theme)
    return render_template('dashboard/theme.html',
                           user=user, site=site, theme=theme, default_theme=default_theme, active='theme')


SLUG_PATTERN = re.compile(r'^[a-z0-9][a-z0-9-]{1,28}[a-z0-9]$')

# page_key / dataset_key 经 <path:> 转换器接收, 会原样带进 `..` 和 `/`。
# 这里做路由层白名单, 与 site_storage._safe_path 的存储层兜底形成双保险。
# 字符集放宽到下划线 + 允许单字符, 覆盖现有所有 key(about/contact/home/
# portfolio/posts/pricing/products/features), 零误伤。
_KEY_PATTERN = re.compile(r'^[a-z0-9][a-z0-9_-]{0,40}$')
VISIBLE_TEMPLATE_NAMES = ('claude', 'dengtec')


def _visible_templates_query():
    return Template.query.filter(Template.name.in_(VISIBLE_TEMPLATE_NAMES)).order_by(Template.name)


def _validate_key(key):
    """校验动态 page_key / dataset_key, 非法直接 404(不暴露细节)."""
    if not _KEY_PATTERN.match(key or ''):
        abort(404)
    return key


@bp.route('/templates')
def templates_gallery():
    user, site = _current_context()
    scan_templates()
    templates = _visible_templates_query().all()
    if request.args.get('_fragment'):
        return render_template('dashboard/panel_templates.html',
                               user=user, site=site, templates=templates)
    return render_template('dashboard/templates_gallery.html',
                           user=user, site=site, templates=templates, active='templates')


@bp.route('/templates/<template_name>/preview/')
@bp.route('/templates/<template_name>/preview/<path:filepath>')
def template_preview(template_name, filepath='index.html'):
    """模板预览 —— 用模板 seed_data 渲染."""
    session['current_template_preview'] = template_name  # 后续 /assets/ 请求需要定位资源目录
    if template_name not in VISIBLE_TEMPLATE_NAMES or not Template.query.filter_by(name=template_name).first():
        abort(404)
    out = build_template_preview(
        template_name,
        base_url=f'/templates/{template_name}/preview',
    )
    full = out / filepath
    if full.is_dir():
        full = full / 'index.html'
        filepath = f'{filepath.rstrip("/")}/index.html'
    return _safe_send_from_directory(out, filepath)


@bp.route('/sites/new', methods=['GET', 'POST'])
def site_new():
    from .models import SLUG_RESERVED
    template_name = request.args.get('template')
    template = _visible_templates_query().filter_by(name=template_name).first() if template_name else None
    templates = _visible_templates_query().all()

    def template_language_options(tpl_name):
        meta_path = Path(current_app.config['TEMPLATES_DIR']) / tpl_name / 'meta.yaml'
        if not meta_path.exists():
            return [{'code': 'zh-CN', 'name': '简体中文'}], 'zh-CN'
        meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {}
        languages = meta.get('languages') or [{'code': 'zh-CN', 'name': '简体中文'}]
        default_lang = meta.get('default_language') or (languages[0].get('code') if languages else 'zh-CN')
        return languages, default_lang

    template_language_map = {}
    template_default_language_map = {}
    for tpl in templates:
        langs, default_lang = template_language_options(tpl.name)
        template_language_map[tpl.name] = langs
        template_default_language_map[tpl.name] = default_lang

    user = _current_user()
    if not user:
        return redirect(url_for('core.login'))

    is_fragment = request.args.get('_fragment') is not None

    initial_template_name = template.name if template else (templates[0].name if templates else '')
    initial_default_lang = template_default_language_map.get(initial_template_name, 'zh-CN')
    form = {
        'name': '',
        'slug': '',
        'template_name': template.name if template else '',
        'enabled_languages': [initial_default_lang],
    }
    error = None

    if request.method == 'POST':
        form['name'] = request.form.get('name', '').strip()
        form['slug'] = request.form.get('slug', '').strip().lower()
        form['template_name'] = request.form.get('template_name', '').strip()
        form['enabled_languages'] = request.form.getlist('enabled_lang')

        # 解析模板：未选时使用第一个可用模板
        selected_template = _visible_templates_query().filter_by(name=form['template_name']).first()
        if not selected_template:
            selected_template = _visible_templates_query().first()
        selected_languages, selected_default_lang = (
            template_language_options(selected_template.name) if selected_template else ([], 'zh-CN')
        )
        selected_codes = [l.get('code') for l in selected_languages if l.get('code')]
        selected_enabled_langs = [c for c in form.get('enabled_languages', []) if c in selected_codes]
        if not selected_template:
            error = '暂无可用模板，请联系管理员'
        elif not form['name']:
            error = '请填写站点名'
        elif not SLUG_PATTERN.match(form['slug']):
            error = 'Slug 不合法（要求 3–30 字符，[a-z 0-9 -]，不以 - 开头/结尾）'
        elif form['slug'] in SLUG_RESERVED:
            error = f'Slug "{form["slug"]}" 是保留字'
        elif Site.query.filter_by(slug=form['slug']).first():
            error = f'Slug "{form["slug"]}" 已被占用'
        else:
            if not selected_enabled_langs:
                error = '请选择至少一种模板支持的语言版本'
                if is_fragment:
                    return jsonify({'ok': False, 'error': error})
                current_site = Site.query.filter_by(owner_id=user.id).order_by(Site.id.desc()).first()
                return render_template('dashboard/site_new.html',
                                       user=user,
                                       site=current_site,
                                       template=template, templates=templates, form=form, error=error,
                                       template_language_map=template_language_map,
                                       template_default_language_map=template_default_language_map,
                                       active='templates')
            else:
                from .db import db
                default_language = selected_default_lang if selected_default_lang in selected_enabled_langs else selected_enabled_langs[0]
                site = Site(
                    owner_id=user.id, name=form['name'], slug=form['slug'],
                    folder_path='', template_name=selected_template.name,
                    template_version=selected_template.current_version, cdn_provider='aliyun',
                    default_language=default_language,
                    enabled_languages=selected_enabled_langs,
                )
                from sqlalchemy.exc import IntegrityError
                db.session.add(site)
                # #12+#29: flush(触发 INSERT, slug 唯一约束在此生效) 和文件初始化都纳入保护。
                # 上面虽已查过 slug 唯一性, 但 查→insert 之间存在 TOCTOU(并发建同名 slug),
                # 唯一约束会抛 IntegrityError; 文件操作也可能失败。两种都回滚 DB + 友好提示, 不 500。
                try:
                    db.session.flush()  # 拿到 site.id, 但先不 commit
                    site.folder_path = f'sites/{site.id}'
                    init_site_folder(site.id)
                    copy_seed_data(site.id, selected_template.name)
                    settings = read_yaml(site.id, 'settings.yaml') or {}
                    header = settings.setdefault('header', {})
                    header['enabled_languages'] = selected_enabled_langs
                    header.setdefault('language_switcher', {})['enabled'] = len(selected_enabled_langs) > 1
                    write_yaml(site.id, 'settings.yaml', settings)
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    error = f'Slug "{form["slug"]}" 刚被占用，请换一个'
                    if is_fragment:
                        return jsonify({'ok': False, 'error': error})
                    current_site = Site.query.filter_by(owner_id=user.id).order_by(Site.id.desc()).first()
                    return render_template('dashboard/site_new.html',
                                           user=user, site=current_site,
                                           template=template, templates=templates, form=form, error=error,
                                           template_language_map=template_language_map,
                                           template_default_language_map=template_default_language_map,
                                           active='templates')
                except Exception:
                    db.session.rollback()
                    current_app.logger.exception('建站文件初始化失败, 已回滚 DB (slug=%s)', form['slug'])
                    error = '建站失败：文件初始化出错，请重试或联系管理员'
                    if is_fragment:
                        return jsonify({'ok': False, 'error': error})
                    current_site = Site.query.filter_by(owner_id=user.id).order_by(Site.id.desc()).first()
                    return render_template('dashboard/site_new.html',
                                           user=user, site=current_site,
                                           template=template, templates=templates, form=form, error=error,
                                           template_language_map=template_language_map,
                                           template_default_language_map=template_default_language_map,
                                           active='templates')
                flash(f'已创建站点 #{site.id} ({form["slug"]})')
                if is_fragment:
                    return jsonify({'ok': True, 'redirect': url_for('core.overview', site=site.id)})
                return redirect(url_for('core.overview', site=site.id))

        # POST 验证失败 -> fragment 模式返回 JSON，普通模式重渲染页面
        if is_fragment:
            return jsonify({'ok': False, 'error': error})

    current_site = Site.query.filter_by(owner_id=user.id).order_by(Site.id.desc()).first()
    if is_fragment:
        return render_template('dashboard/panel_site_new.html',
                               user=user,
                               site=current_site,
                               template=template, templates=templates, form=form, error=error,
                               template_language_map=template_language_map,
                               template_default_language_map=template_default_language_map,
                               active='templates')
    return render_template('dashboard/site_new.html',
                           user=user,
                           site=current_site,
                           template=template, templates=templates, form=form, error=error,
                           template_language_map=template_language_map,
                           template_default_language_map=template_default_language_map,
                           active='templates')


@bp.route('/build', methods=['GET', 'POST'])
def build():
    """触发构建当前站点, 跳到预览首页."""
    _, site = _current_context()
    try:
        build_site(site.id, base_url=f'/preview/{site.id}')
    except Exception as exc:
        current_app.logger.exception('站点 %s 构建失败', site.id)
        if request.method == 'POST' or request.args.get('_fragment'):
            return jsonify({'ok': False, 'error': str(exc)}), 500
        abort(500, f'构建失败: {exc}')

    if request.method == 'POST' or request.args.get('_fragment'):
        return jsonify({'ok': True, 'preview_url': f'/preview_site/{site.id}'})

    return redirect(url_for('core.preview_site', site_id=site.id))


@bp.route('/export.zip')
def export_zip():
    """导出当前站点的静态文件 ZIP."""
    from io import BytesIO
    from zipfile import ZIP_DEFLATED, ZipFile


    _, site = _current_context()
    # #13: 传入 report 收集缺页, 有失败时在 ZIP 内附一份说明, 不让店主拿到缺页站还不自知。
    report = []
    output_root = build_site(site.id, base_url='', report=report)

    buffer = BytesIO()
    with ZipFile(buffer, 'w', ZIP_DEFLATED) as zf:
        for path in output_root.rglob('*'):
            if path.is_file():
                zf.write(path, path.relative_to(output_root).as_posix())
        if report:
            warn_lines = ['本次导出有以下页面构建失败、未包含在内：', '']
            warn_lines += [f"- [{f['lang'] or '默认'}] {f['template']} ({f['type']}): {f['error']}"
                           for f in report]
            zf.writestr('_构建警告.txt', '\n'.join(warn_lines) + '\n')
    buffer.seek(0)

    filename = f'{site.slug or "site"}-static.zip'
    return send_file(
        buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=filename,
    )


def _default_lang_code(site):
    """取站点默认语言，优先使用已启用的第一个语言."""
    tpl_meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    if tpl_meta_path.exists():
        tpl_meta = _yaml.safe_load(tpl_meta_path.read_text(encoding='utf-8')) or {}
        languages = tpl_meta.get('languages', [])
        if languages:
            # 按站点启用的语言过滤
            enabled_codes = site.enabled_languages or [l['code'] for l in languages]
            enabled = [l for l in languages if l['code'] in enabled_codes]
            # 兜底：如果过滤后为空，使用全部语言
            if enabled:
                return enabled[0].get('code', 'zh-CN')
            return languages[0].get('code', 'zh-CN')
    return 'zh-CN'


def _preview_needs_rebuild(site_id, out):
    """Return true when generated preview is missing or older than site YAML."""
    index = out / 'index.html'
    if not index.exists():
        return True
    try:
        built_at = index.stat().st_mtime
        root = Path(current_app.config['SITES_DIR']) / str(site_id)
        return any(
            path.stat().st_mtime > built_at
            for path in root.rglob('*.yaml')
            if not path.name.startswith('.tmp-')
        )
    except OSError:
        return True


@bp.route('/preview_site/<int:site_id>')
def preview_site(site_id):
    """确保已构建，重定向到根 index.html（多语言站走 JS 浏览器语言检测）."""
    session['current_site_id'] = site_id  # 后续 /assets/ 资源请求需要
    from flask import redirect, request, url_for
    site = Site.query.get_or_404(site_id)
    _require_site_access(site)
    out = Path(current_app.config['OUTPUT_DIR']) / str(site_id)

    # 构建条件：不存在任何产出。?_ 只是浏览器 cache-busting 参数，不触发重建。
    if _preview_needs_rebuild(site_id, out):
        build_site(site_id, base_url=f'/preview/{site_id}')

    # 返回根 index.html：多语言站走 JS 浏览器语言检测，单语言站直接渲染
    return redirect(url_for('core.preview', site_id=site_id))


@bp.route('/preview_or_build/<int:site_id>')
def preview_or_build(site_id):
    """确保已构建，返回根 index.html（多语言站走 JS 浏览器语言检测）或默认语言首页."""
    session['current_site_id'] = site_id  # 后续 /assets/ 资源请求需要
    site = Site.query.get_or_404(site_id)
    _require_site_access(site)
    out = Path(current_app.config['OUTPUT_DIR']) / str(site_id)

    # 优先返回根 index.html（多语言站含 JS 浏览器语言检测），
    # 不存在则回退到默认语言首页（单语言站点无根选择页）
    root_index = out / 'index.html'
    if _preview_needs_rebuild(site_id, out):
        build_site(site_id, base_url=f'/preview/{site_id}')

    if (out / 'index.html').exists():
        return _safe_send_from_directory(out, 'index.html')

    # 回退：单语言站点直接返回首页
    lang_code = _default_lang_code(site)
    lang_index = out / lang_code / 'index.html'
    if lang_index.exists():
        return _safe_send_from_directory(out / lang_code, 'index.html')
    return _safe_send_from_directory(out, 'index.html')


@bp.route('/preview/<int:site_id>/')
@bp.route('/preview/<int:site_id>/<path:filepath>')
def preview(site_id, filepath='index.html'):
    """预览 output/<site_id>/ 下的静态文件，自动构建."""
    session['current_site_id'] = site_id  # 后续 /assets/ 资源请求需要
    site = Site.query.get_or_404(site_id)
    _require_site_access(site)
    out = Path(current_app.config['OUTPUT_DIR']) / str(site_id)
    parts = [part for part in str(filepath).replace('\\', '/').split('/') if part]
    if parts:
        asset_index = 0 if parts[0] == 'assets' else (1 if len(parts) > 1 and parts[1] == 'assets' else -1)
        if asset_index >= 0:
            asset_path = '/'.join(parts[asset_index + 1:])
            return _safe_send_from_directory(out / 'assets', asset_path)

    # 根路径请求 → 返回根 index.html（多语言站走 JS 浏览器语言检测），不再跳默认语言
    if filepath == 'index.html':
        if _preview_needs_rebuild(site_id, out):
            try:
                build_site(site_id, base_url=f'/preview/{site_id}')
            except Exception:
                current_app.logger.exception('预览构建站点 %s 失败', site_id)
        if (out / 'index.html').exists():
            return _safe_send_from_directory(out, 'index.html')
    elif _preview_needs_rebuild(site_id, out):
        try:
            build_site(site_id, base_url=f'/preview/{site_id}')
        except Exception:
            current_app.logger.exception('预览构建站点 %s 失败', site_id)

    # 先解析出最终目标文件，再判断是否需要重建
    full = out / filepath
    if full.is_dir():
        full = full / 'index.html'
        filepath = f'{filepath.rstrip("/")}/index.html'
    if not full.exists():
        try:
            build_site(site_id, base_url=f'/preview/{site_id}')
        except Exception:
            current_app.logger.exception('预览构建站点 %s 失败', site_id)  # #15: 留痕
    if not out.exists():
        out.mkdir(parents=True, exist_ok=True)
    if not full.exists():
        # 尝试默认语言子目录
        for sub in out.iterdir():
            if sub.is_dir() and (sub / 'index.html').exists():
                return _safe_send_from_directory(out, f'{sub.name}/index.html')
        abort(404, '未生成页面，请检查模板数据')
    return _safe_send_from_directory(out, filepath)


def _get_panel_lang(site):
    """从请求参数获取面板当前编辑语言, 默认返回模板的默认语言.

    只返回站点已启用的语言列表，未启用的不显示在面板语言标签中.
    """
    meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    all_languages = []
    default_lang = 'zh-CN'
    if meta_path.exists():
        meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {}
        all_languages = meta.get('languages', [])
        default_lang = meta.get('default_language', all_languages[0]['code'] if all_languages else 'zh-CN')

    # 按站点启用的语言过滤（从 DB enabled_languages 读取，兜底显示全部）
    enabled_codes = site.enabled_languages or [l['code'] for l in all_languages]
    languages = [l for l in all_languages if l['code'] in enabled_codes]
    # 兜底：如果过滤后为空（旧站点 enabled_languages 可能与模板不一致），使用全部语言
    if not languages:
        languages = all_languages

    lang = request.args.get('lang', '').strip()
    valid_codes = {l['code'] for l in languages}
    if lang and lang in valid_codes:
        return lang, languages, default_lang
    return default_lang, languages, default_lang


def _storage_lang(site, lang, default_lang):
    """返回语言内容的实际存储路径参数.

    与 builder._load_lang_overrides 的逻辑对齐:
    - 非默认语言: 始终返回 lang 参数 (读写 lang/<code>/ 子目录)
    - 默认语言: 如果 lang/<default_lang>/ 目录存在, 返回 lang 参数;
      否则返回 None (读写根目录)

    这是什么场景: 当站点根目录 pages/ 存的是旧默认语言 (如英文),
    而新默认语言 (如中文) 存在于 lang/zh-CN/ 时, 后台面板需要从
    语言子目录读写, 而不是从根目录读到旧语言内容.
    """
    if lang != default_lang:
        return lang
    if lang_root(site.id, lang).exists():
        return lang
    return None


def _lang_key(base_key, site, lang, default_lang):
    """返回 settings.yaml 中带语言后缀的 key (company/contact/footer).

    与构建器对齐: 如果 lang/<lang>/ 目录存在, 始终用 "{key}_{lang}" 后缀 key.
    否则默认语言用根 key, 非默认语言才带后缀.

    为什么: 当根 company/contact 存的是旧默认语言 (如英文),
    company_zh-CN/contact_zh-CN 存的是新默认语言 (如中文) 时,
    构建器优先取 _zh-CN 版本, 面板也必须读写同一个 key.
    """
    if lang_root(site.id, lang).exists():
        return f'{base_key}_{lang}'
    if lang == default_lang:
        return base_key
    return f'{base_key}_{lang}'


def _merge_settings_section(shared, localized):
    """Merge shared settings with current-language overrides."""
    if not isinstance(shared, dict):
        shared = {}
    if not isinstance(localized, dict):
        localized = {}
    shared_first_fields = {'logo', 'favicon', 'icp', 'phone', 'mobile', 'email', 'wechat'}
    result = dict(shared)
    for key, value in localized.items():
        if key in shared_first_fields and result.get(key):
            continue
        if value not in (None, ''):
            result[key] = value
    return result


def _render(template_name, **kwargs):
    """渲染模板, 顺带注入图标列表和样式注册表(供面板表单用)。

    #19: 原来按 ?_fragment 分两支但两支完全相同(伪分支), docstring 也误导。
    fragment 与整页用的是同一个 template_name, 调用方自行传不同模板名, 这里不分支。
    """
    from .icon_registry import ICON_REGISTRY, icon_names
    from .style_registry import STYLE_REGISTRY
    kwargs.setdefault('icon_list', icon_names())
    kwargs.setdefault('icon_registry', ICON_REGISTRY)
    kwargs.setdefault('style_registry', STYLE_REGISTRY)
    return render_template(template_name, **kwargs)


@bp.route('/api/translate', methods=['POST'])
@csrf.exempt  # 只读翻译端点，无数据修改，免除 CSRF 保护（fetch+JSON 调用不含表单 token）
def api_translate():
    """AI 翻译端点 — 接受 JSON 文本字典，返回翻译后的字典."""
    data = request.get_json(silent=True) or {}
    texts = data.get('texts', {})
    source_lang = data.get('source_lang', 'zh-CN')
    target_lang = data.get('target_lang', 'en')

    if not texts or not isinstance(texts, dict):
        return {'error': '请提供 texts 字典'}, 400
    if len(texts) > 50:
        return {'error': '单次最多翻译 50 个字段'}, 400

    try:
        translated = translate_json(texts, source_lang, target_lang)
        return {'ok': True, 'translated': translated}
    except ValueError as e:
        return {'error': str(e)}, 400
    except RuntimeError as e:
        return {'error': str(e)}, 502
    except Exception as e:
        current_app.logger.error('翻译失败: %s', e)
        return {'error': '翻译失败，请稍后重试'}, 500


@bp.route('/api/richtext/upload-image', methods=['POST'])
def api_richtext_upload_image():
    """Upload an image for rich-text editors and return a site-local URL."""
    _, site = _current_context()
    upload = request.files.get('image')
    if not upload or not upload.filename:
        return jsonify({'error': 'No image file provided'}), 400
    try:
        url = _save_uploaded_image(site.id, upload, prefix='richtext')
    except Exception as exc:
        current_app.logger.warning('rich text image upload failed: %s', exc)
        return jsonify({'error': str(exc)}), 400
    return jsonify({'ok': True, 'url': url})


@bp.route('/api/richtext/upload-video', methods=['POST'])
def api_richtext_upload_video():
    """Upload a video for rich-text editors and return a site-local URL."""
    _, site = _current_context()
    upload = request.files.get('video') or request.files.get('media')
    if not upload or not upload.filename:
        return jsonify({'error': 'No video file provided'}), 400
    url = _save_uploaded_media(site.id, upload, prefix='richtext-video')
    if not url:
        return jsonify({'error': 'Video upload failed or file type is not supported'}), 400
    return jsonify({'ok': True, 'url': url})


@bp.route('/api/richtext/upload-package', methods=['POST'])
def api_richtext_upload_package():
    """Upload a zip webpage package for rich-text iframe embeds."""
    _, site = _current_context()
    upload = request.files.get('package') or request.files.get('media')
    if not upload or not upload.filename:
        return jsonify({'error': 'No package file provided'}), 400
    try:
        result = _save_media_package(site.id, upload)
    except Exception as exc:
        current_app.logger.warning('rich text package upload failed: %s', exc)
        return jsonify({'error': str(exc)}), 400
    return jsonify({'ok': True, 'url': result.get('url') or result.get('entry_url'), 'name': result.get('name')})


@bp.route('/api/site/<int:site_id>/dataset/<string:dataset_name>/items')
def api_dataset_items(site_id, dataset_name):
    """返回某数据集下的条目摘要（供精选推荐等模块的"从数据集选取"功能调用）。

    返回 JSON 数组，每条包含 id/title/cover/summary/slug/category 等轻量字段，
    前端选取器据此展示列表、自动填入表单。
    """
    user, site = _current_context()
    if not user or site.id != site_id:
        abort(404)
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    try:
        items = datasets.load(site_id, dataset_name, lang=storage_lang)
    except Exception:
        return jsonify({'error': f'无法加载数据集: {dataset_name}'}), 404
    # 提取轻量摘要字段（名称有多种可能：title / name、cover / image / photo）
    result = []
    for it in items:
        title = it.get('title') or it.get('name') or ''
        cover = it.get('cover') or it.get('image') or it.get('photo') or ''
        summary = it.get('summary') or it.get('excerpt') or it.get('description') or ''
        slug = it.get('slug', '')
        category = it.get('category', '')
        result.append({
            'id': it.get('id'),
            'title': str(title).strip(),
            'cover': str(cover).strip(),
            'summary': str(summary).strip(),
            'slug': str(slug).strip(),
            'category': str(category).strip(),
        })
    return jsonify({'dataset': dataset_name, 'items': result})


@bp.route('/_dataset/<path:dataset_key>')
def dataset_panel(dataset_key):
    """通用数据集管理面板 — 支持 ?lang= 参数编辑不同语言版本."""
    _validate_key(dataset_key)
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    items = datasets.load(site.id, dataset_key, lang=storage_lang)
    if storage_lang:
        source_storage_lang = _storage_lang(site, default_lang, default_lang)
        source_items = datasets.load(site.id, dataset_key, lang=source_storage_lang)
        if not items and source_items:
            items = source_items
    # 计算数据集的菜单层级路径，用于中间预览 URL
    settings = read_yaml(site.id, 'settings.yaml') or {}
    menu_items = settings.get('menu') or []
    from app.core.menu import find_menu_path
    meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
    raw_menu = menu_lib.upgrade_old_format(menu_items, meta.get('datasets', []))
    preview_path = find_menu_path(raw_menu, dataset_key)
    all_list_datasets = menu_lib.collect_list_targets(menu_lib.normalize_for_render(raw_menu))
    blocks = _get_available_blocks(site.template_name)
    from .icon_registry import icon_names
    return _render('dashboard/panel_data_list.html',
                   user=user, site=site,
                   dataset_key=dataset_key, items=items,
                   blocks=blocks,
                   all_list_datasets=all_list_datasets,
                   icon_list=icon_names(),
                   edit_prefix=f'_dataset/{dataset_key}',
                   current_lang=lang, languages=languages, default_lang=default_lang,
                   preview_path=preview_path,
                   active=dataset_key)

@bp.route('/_dataset/<path:dataset_key>/new', methods=['POST'])
def dataset_new(dataset_key):
    """通用数据集新建条目 — 支持 ?lang= 参数保存到对应语言."""
    _validate_key(dataset_key)
    _, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    n = len(datasets.load(site.id, dataset_key, lang=storage_lang)) + 1
    new_id = datasets.add(site.id, dataset_key, {
        'title': f'新条目 {n}', 'slug': f'item-{n}',
    }, lang=storage_lang)
    return redirect(url_for('core.dataset_panel', dataset_key=dataset_key, _fragment='1', site=site.id, lang=lang))

@bp.route('/_dataset/<path:dataset_key>/<int:item_id>/edit', methods=['GET', 'POST'])
def dataset_edit(dataset_key, item_id):
    """通用数据集编辑 — 支持 ?lang= 参数编辑不同语言版本."""
    _validate_key(dataset_key)
    user, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    source_storage_lang = _storage_lang(site, default_lang, default_lang)

    item = datasets.find(site.id, dataset_key, item_id, lang=storage_lang)
    source_item = datasets.find(site.id, dataset_key, item_id, lang=source_storage_lang)
    if not item and storage_lang and source_item:
        item = source_item
    if not item:
        abort(404, f'数据不存在: {dataset_key}#{item_id}')
    source_item = source_item or item

    if request.method == 'POST':
        if storage_lang and not datasets.find(site.id, dataset_key, item_id, lang=storage_lang):
            source_items = datasets.load(site.id, dataset_key, lang=source_storage_lang)
            if source_items:
                datasets.save(site.id, dataset_key, source_items, lang=storage_lang)
        # 用旧数据做底，表单字段覆盖，避免种子字段（name/category/cover 等）被静默删除
        fields = {}
        for key, val in item.items():
            if key not in ('id', 'slug', 'modules', 'csrf_token'):
                fields[key] = val
        for key in request.form:
            if key.startswith('detail_gallery_') or key in ('detail_gallery_count',):
                continue
            if key == '_show_detail_btn_mode':
                continue
            # 跳过模块配置字段和 CSRF 令牌（不参与数据存储）
            if key.startswith('module_') or key in ('module_count', 'csrf_token'):
                continue
            val = request.form.get(key, '').strip()
            fields[key] = val
        detail_btn_mode = request.form.get('_show_detail_btn_mode')
        if detail_btn_mode == 'inherit':
            fields.pop('show_detail_btn', None)
        elif detail_btn_mode in ('true', 'false'):
            fields['show_detail_btn'] = detail_btn_mode == 'true'
        # slug 唯一性校验
        new_slug = fields.get('slug', '').strip() or None
        if new_slug:
            # 格式校验: slug 会拼进详情页输出路径 {item_path}/{slug}/index.html,
            # 不校验则 `../../<任意路径>` 可让 builder 把 HTML 写到 output 目录外
            # (构建期任意文件写入)。复用站点级同一套 SLUG_PATTERN 严格白名单。
            if not SLUG_PATTERN.match(new_slug):
                flash(f'Slug "{new_slug}" 格式非法：只能用小写字母、数字、连字符，3-30 字符', 'error')
                return redirect(url_for('core.dataset_edit', dataset_key=dataset_key,
                                        item_id=item_id, _fragment='1', site=site.id, lang=lang))
            all_items = datasets.load(site.id, dataset_key, lang=storage_lang)
            dup = next((it for it in all_items
                        if it.get('slug') == new_slug and it.get('id') != item_id), None)
            if dup:
                flash(f'Slug "{new_slug}" 已被 #{dup["id"]} 使用，请换一个', 'error')
                return redirect(url_for('core.dataset_edit', dataset_key=dataset_key,
                                        item_id=item_id, _fragment='1', site=site.id, lang=lang))
        # tags: 逗号/空格分隔的字符串 → 列表
        if 'tags' in fields and fields['tags']:
            raw_tags = fields['tags']
            if isinstance(raw_tags, str):
                tags_list = [t.strip() for t in raw_tags.replace(',', ' ').split() if t.strip()]
                fields['tags'] = tags_list
        # 处理图片上传
        if 'tags_visible' in fields:
            fields['tags_visible'] = str(fields.get('tags_visible')).lower() != 'false'
        if 'detail_gallery_count' in request.form or 'detail_gallery_visible' in request.form:
            gallery_count = 0
            try:
                gallery_count = int(request.form.get('detail_gallery_count', '0'))
            except (ValueError, TypeError):
                gallery_count = 0
            gallery_images = []
            for gi in range(gallery_count):
                url = request.form.get(f'detail_gallery_{gi}_url', '').strip()
                upload = request.files.get(f'detail_gallery_{gi}_url_file')
                if upload and upload.filename:
                    try:
                        url = _save_uploaded_image(site.id, upload, prefix=f'{dataset_key}-detail-gallery-{gi + 1}')
                    except Exception as exc:
                        current_app.logger.warning('细节图库图片上传失败: %s', exc)
                if url:
                    gallery_images.append({'url': url})
            fields['detail_gallery'] = {
                'visible': str(request.form.get('detail_gallery_visible', 'true')).lower() != 'false',
                'images': gallery_images,
            }
        for field_name in ('cover', 'image', 'photo', 'logo'):
            upload = request.files.get(field_name) or request.files.get(f'{field_name}_file')
            if upload and upload.filename:
                try:
                    fields[field_name] = _save_uploaded_image(site.id, upload, prefix=f'{dataset_key}-{field_name}')
                except Exception as exc:
                    current_app.logger.warning('数据集图片上传失败 %s: %s', field_name, exc)
        # 保存模块配置到数据项 (item) 中
        # module_count 缺失表示表单不包含模块数据（例如用户未展开面板就保存），
        # 此时保留已有 modules 而非清空
        module_count_str = request.form.get('module_count')
        if module_count_str and module_count_str.isdigit():
            try:
                existing_modules = item.get('modules', [])
                modules = _parse_modules_form(request.form, existing_modules)
                # item_data：style 字段提升到 item 顶层；其余数据（images、specs 等）
                # 保留在模块 data 中，供 render_block 使用
                for m in modules:
                    if m.get('type') == 'item_data':
                        keep = {}
                        for key, value in (m.get('data') or {}).items():
                            if key.startswith('style_'):
                                fields[key] = value
                            else:
                                keep[key] = value
                        # 清理扁平残留键（已被 _parse_modules_form 结构化到
                        # images / specs 列表中），避免 YAML 冗余污染
                        for stale_prefix in ('images_', 'specs_'):
                            for k in list(keep.keys()):
                                if k.startswith(stale_prefix) and k not in ('images', 'specs'):
                                    keep.pop(k, None)
                        m['data'] = keep
                fields['modules'] = modules
            except Exception as exc:
                current_app.logger.warning('数据集编辑保存模块配置失败: %s', exc)
        elif module_count_str is not None:
            # 明确传了 module_count 但非数字 → 清空
            fields['modules'] = []
        # 否则 module_count 不在表单中 → 保留旧 modules 不动

        datasets.update(site.id, dataset_key, item_id, fields, lang=storage_lang)
        flash('已保存')
        return redirect(url_for('core.dataset_panel', dataset_key=dataset_key, _fragment='1', site=site.id, lang=lang))

    blocks = _get_available_blocks(site.template_name)
    # 中间预览 URL：计算数据集在菜单中的完整层级路径
    slug = item.get('slug', '')
    settings = read_yaml(site.id, 'settings.yaml') or {}
    menu_items = settings.get('menu') or []
    is_list_page = any(
        mi.get('type') == 'list' and mi.get('target') == dataset_key
        for mi in menu_items
    )
    # 计算数据集的完整菜单路径（含父级前缀），用于预览 URL
    from app.core.menu import find_menu_path
    meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
    raw_menu = menu_lib.upgrade_old_format(menu_items, meta.get('datasets', []))
    preview_path = find_menu_path(raw_menu, dataset_key)
    all_list_datasets = menu_lib.collect_list_targets(menu_lib.normalize_for_render(raw_menu))
    from .style_registry import STYLE_REGISTRY
    from .icon_registry import icon_names
    return _render('dashboard/panel_data_list.html',
                   user=user, site=site,
                   dataset_key=dataset_key, items=[item],
                   edit_prefix=f'_dataset/{dataset_key}',
                   edit_item=item, edit_item_id=item_id,
                   source_item=source_item,
                   current_lang=lang, languages=languages, default_lang=default_lang,
                   active=dataset_key,
                   blocks=blocks,
                   all_list_datasets=all_list_datasets,
                   is_list_page=is_list_page,
                   page_key=dataset_key,
                   preview_slug=slug,
                   preview_path=preview_path,
                   style_registry=STYLE_REGISTRY,
                   icon_list=icon_names())

@bp.route('/_dataset/<path:dataset_key>/<int:item_id>/delete', methods=['POST'])
def dataset_delete(dataset_key, item_id):
    """通用数据集删除 — 支持 ?lang= 参数删除指定语言版本."""
    _validate_key(dataset_key)
    _, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    datasets.remove(site.id, dataset_key, item_id, lang=storage_lang)
    flash('已删除')
    return redirect(url_for('core.dataset_panel', dataset_key=dataset_key, _fragment='1', site=site.id, lang=lang))


@bp.route('/_dataset/<path:dataset_key>/<int:target_id>/paste-from/<int:source_id>', methods=['POST'])
def dataset_paste_from(dataset_key, target_id, source_id):
    """Copy one dataset item onto another, preserving the target id and slug."""
    _validate_key(dataset_key)
    _, site = _current_context()
    lang, languages, default_lang = _get_panel_lang(site)
    storage_lang = _storage_lang(site, lang, default_lang)
    items = datasets.load(site.id, dataset_key, lang=storage_lang)
    source = next((it for it in items if it.get('id') == source_id), None)
    target = next((it for it in items if it.get('id') == target_id), None)
    if not source or not target:
        return jsonify({'error': '数据不存在'}), 404
    new_item = copy.deepcopy(source)
    new_item['id'] = target.get('id')
    new_item['slug'] = target.get('slug')
    for i, item in enumerate(items):
        if item.get('id') == target_id:
            items[i] = new_item
            break
    datasets.save(site.id, dataset_key, items, lang=storage_lang)
    return jsonify({'ok': True})


@bp.route('/_panel/<path:page_key>', methods=['GET', 'POST'])
def page_panel(page_key):
    """动态菜单项面板路由：根据 page_key 分发到对应数据集列表或单页编辑.

    模块库是公用的——所有菜单页面都可以从同一个 blocks/ 中选择模块，
    只是每个页面填不同的数据，保存在 pages/<page_key>.yaml 的 modules 数组中。

    支持语言参数 ?lang=en 来编辑特定语言版本的页面内容。
    """
    _validate_key(page_key)
    user, site = _current_context()

    lang, languages, default_lang = _get_panel_lang(site)
    # 非默认语言时使用 lang 参数进行读写；默认语言读写根目录
    storage_lang = _storage_lang(site, lang, default_lang)
    source_storage_lang = _storage_lang(site, default_lang, default_lang)

    # POST：保存模块配置
    if request.method == 'POST':
        page = read_yaml(site.id, f'pages/{page_key}.yaml', lang=storage_lang) or {}
        existing_modules = page.get('modules', [])
        if storage_lang and not existing_modules:
            source_page_for_save = read_yaml(site.id, f'pages/{page_key}.yaml', lang=source_storage_lang) or {}
            existing_modules = source_page_for_save.get('modules', []) or existing_modules
        page['modules'] = _parse_modules_form(request.form, existing_modules)
        # 页面级 SEO 信息和模块配置共用同一个保存按钮；保存模块时不能把
        # title/description 清掉，否则健康检查引导填写后预览 head 仍然没有简介。
        if 'page_title' in request.form:
            title = request.form.get('page_title', '').strip()
            if title:
                page['title'] = title
            else:
                page.pop('title', None)
        if 'page_description' in request.form:
            description = request.form.get('page_description', '').strip()
            if description:
                page['description'] = description
            else:
                page.pop('description', None)
        write_yaml(site.id, f'pages/{page_key}.yaml', page, lang=storage_lang)
        flash('已保存')
        return redirect(url_for('core.page_panel', page_key=page_key, _fragment='1', site=site.id, lang=lang))

    # 判断 page_key 是否为 list 类型菜单
    settings = read_yaml(site.id, 'settings.yaml') or {}
    menu_items = settings.get('menu') or []
    if not menu_items:
        meta_path = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
        if meta_path.exists():
            template_meta = _yaml.safe_load(meta_path.read_text(encoding='utf-8')) or {}
            menu_items = template_meta.get('default_menu', [])

    def _find_list_in_menu(items, target_key):
        for item in (items or []):
            if item.get('type') == 'list' and item.get('target') == target_key:
                return True
            if item.get('children'):
                if _find_list_in_menu(item['children'], target_key):
                    return True
        return False

    is_list_page = _find_list_in_menu(menu_items, page_key)

    # 收集数据集列表，供数据网格模块选择数据源，也供模板 datasetNamesJson 序列化
    from app.core.menu import upgrade_old_format, normalize_for_render, ensure_home
    meta_path2 = Path(current_app.config['TEMPLATES_DIR']) / site.template_name / 'meta.yaml'
    meta2 = _yaml.safe_load(meta_path2.read_text(encoding='utf-8')) if meta_path2.exists() else {}
    datasets_meta = meta2.get('datasets', [])
    raw_menu = upgrade_old_format(menu_items, datasets_meta)
    normalized_menu = ensure_home(normalize_for_render(raw_menu))

    # 从菜单中查找 page_key 对应的实际显示名（如 home → 首页）
    def _find_page_label(items, target_key):
        for item in (items or []):
            # home 类型菜单项无 target 字段，通过 type == 'home' 匹配
            if item.get('target') == target_key or (target_key == 'home' and item.get('type') == 'home'):
                return item.get('label', target_key)
            if item.get('children'):
                found = _find_page_label(item['children'], target_key)
                if found:
                    return found
        return None
    page_display_name = _find_page_label(normalized_menu, page_key) or page_key

    all_list_datasets = menu_lib.collect_list_targets(normalized_menu)  # #22

    page = read_yaml(site.id, f'pages/{page_key}.yaml', lang=storage_lang)
    source_page = read_yaml(site.id, f'pages/{page_key}.yaml', lang=source_storage_lang) or {}
    if storage_lang and source_page.get('modules') and not (page or {}).get('modules'):
        page = copy.deepcopy(source_page)

    # 迁移：product_grid → data_grid（模块合并后的向后兼容）
    for _pg, _sl in [(page, storage_lang), (source_page, None)]:
        if _pg and _pg.get('modules'):
            _migrated = False
            for mod in _pg['modules']:
                if mod.get('type') == 'product_grid':
                    mod['type'] = 'data_grid'
                    _migrated = True
            if _migrated:
                write_yaml(site.id, f'pages/{page_key}.yaml', _pg, lang=_sl)

    if page:
        blocks = _get_available_blocks(site.template_name)
        is_modules_format = 'modules' in page
        page.setdefault('modules', [])
        _merge_block_defaults(page.get('modules'), blocks)
        from .style_registry import STYLE_REGISTRY
        from .icon_registry import icon_names
        return _render('dashboard/panel_page_edit.html',
                       user=user, site=site,
                       page_key=page_key, page_display_name=page_display_name,
                       page=page, blocks=blocks, is_modules_format=is_modules_format,
                       is_list_page=is_list_page,
                       all_list_datasets=all_list_datasets,
                       style_registry=STYLE_REGISTRY,
                       icon_list=icon_names(),
                       source_page=source_page,
                       current_lang=lang, languages=languages, default_lang=default_lang,
                       active=page_key)

    # 没有匹配任何已有内容：自动初始化
    new_page = {'modules': []}
    write_yaml(site.id, f'pages/{page_key}.yaml', new_page, lang=storage_lang)
    blocks = _get_available_blocks(site.template_name)
    _merge_block_defaults(new_page.get('modules'), blocks)
    from .style_registry import STYLE_REGISTRY
    from .icon_registry import icon_names
    return _render('dashboard/panel_page_edit.html',
                   user=user, site=site,
                   page_key=page_key, page_display_name=page_display_name,
                   page=new_page, blocks=blocks, is_modules_format=True,
                   is_list_page=is_list_page,
                   all_list_datasets=all_list_datasets,
                   style_registry=STYLE_REGISTRY,
                   icon_list=icon_names(),
                   source_page=source_page,
                   current_lang=lang, languages=languages, default_lang=default_lang,
                   active=page_key)


def _get_available_blocks(template_name):
    """获取模板的可用模块列表."""
    from .template_loader import scan_blocks
    try:
        return scan_blocks(template_name)
    except Exception:
        return []


def _merge_block_defaults(modules, blocks):
    """将 meta.yaml 中非空 default 值合并到模块显示数据中（仅补全缺失的 key，不覆盖已有值）。
    这样属性面板的 Jinja2 模板用 mdata.get('key', '') 就能拿到 CSS 兜底值。
    """
    if not modules or not blocks:
        return
    # block name → {field_key: default_value}
    defaults_by_type = {}
    for b in blocks:
        field_defaults = {}
        for f in b.get('fields', []):
            d = f.get('default')
            if d is not None and d != '':
                field_defaults[f['key']] = d
        if field_defaults:
            defaults_by_type[b['name']] = field_defaults

    for m in modules:
        if not isinstance(m, dict):
            continue
        field_defaults = defaults_by_type.get(m.get('type', ''))
        if not field_defaults:
            continue
        data = m.get('data')
        if not isinstance(data, dict):
            continue
        for key, val in field_defaults.items():
            if key not in data:
                data[key] = val


def _parse_modules_form(form, existing_modules=None):
    """从 POST 表单解析 modules 数组（含 responsive 字段）.

    如果提供 existing_modules，表单未涉及的字段（如 items、features 等嵌套数组）
    会从已有数据中保留，防止编辑器保存时丢失表单不表达的数据。
    """
    data_field_allowed_types = {
        'columns': {'text_content', 'logo_cloud'},
        'max_items': {'data_grid'},
        'items_per_page': {'data_grid'},
    }

    # 构建已有模块查找索引：(type, order) → existing_data
    # 注意：旧格式数据中 hero_banner 的 data 可能是直接列表（slides），
    # 需要包装为 dict 才能安全使用 .items()
    existing_by_key = {}
    if existing_modules:
        for em in existing_modules:
            if isinstance(em, dict) and em.get('type'):
                key = (em.get('type', ''), em.get('order', 0))
                raw_data = em.get('data', {})
                if isinstance(raw_data, dict):
                    existing_by_key[key] = raw_data
                elif isinstance(raw_data, list):
                    existing_by_key[key] = {'slides': raw_data}
                else:
                    existing_by_key[key] = {}

    def _parse_value(value):
        value = (value or '').strip()
        if not value:
            return ''
        # 保留布尔字符串原样，避免 yaml.safe_load 把 'true'/'false' 转成 Python bool
        # 否则模板中 == 'true' 的字符串比较会失败，导致分页等开关不生效
        if value.lower() in ('true', 'false', 'yes', 'no', 'on', 'off'):
            return value
        try:
            parsed = _yaml.safe_load(value)
        except _yaml.YAMLError:
            return value
        # 安全防护：若 yaml.safe_load 将值解析为 dict/list 等复合对象，
        # 说明原值恰好是合法 YAML 结构（如含冒号的多行文本），应保留原始字符串
        if isinstance(parsed, (dict, list)):
            return value
        return value if parsed is None else parsed

    count = 0
    try:
        count = int(form.get('module_count', '0'))
    except (ValueError, TypeError):
        pass

    # data-* 声明式 block 的 schema 表（按类型）：供下方通用 list/grid 条目解析。
    # 取不到（无站点上下文/扫描失败）则留空，回落到各 block 的硬编码解析分支。
    def _merge_meta_lists_into_schema(schema, meta_fields):
        if not isinstance(schema, dict):
            return schema
        merged = dict(schema)
        fields = list(merged.get('fields') or [])
        existing = set()

        def collect_field_names(items):
            for item in items or []:
                if not isinstance(item, dict):
                    continue
                name = item.get('name') or item.get('key')
                if name:
                    existing.add(name)
                collect_field_names(item.get('children') or item.get('item_fields') or [])

        collect_field_names(fields)
        for mf in meta_fields or []:
            if not isinstance(mf, dict):
                continue
            key = mf.get('key') or mf.get('name')
            if not key or key in existing or mf.get('type') not in ('list', 'grid'):
                continue
            item_fields = []
            for child in mf.get('item_fields') or mf.get('children') or []:
                if not isinstance(child, dict):
                    continue
                c = dict(child)
                c['name'] = c.get('name') or c.get('key') or ''
                if c['name']:
                    item_fields.append(c)
            fields.append({
                'name': key,
                'type': mf.get('type'),
                'label': mf.get('label') or key,
                'children': item_fields,
            })
            existing.add(key)
        merged['fields'] = fields
        return merged

    schema_by_type = {}
    try:
        _tpl_name = _current_context()[1].template_name
        for b in _get_available_blocks(_tpl_name):
            if b.get('is_data_attr') and b.get('schema') is not None:
                schema_by_type[b['name']] = _merge_meta_lists_into_schema(b['schema'], b.get('fields') or [])
    except Exception:
        current_app.logger.exception('_parse_modules_form: 构建 schema_by_type 失败，通用 list 解析将不生效——新添加的列表条目可能丢失')
        schema_by_type = {}

    modules = []
    for i in range(count):
        idx = f'module_{i}'
        m_type = form.get(f'{idx}_type', '').strip()
        if not m_type:
            continue
        variant = form.get(f'{idx}_variant', '').strip() or 'default'
        order_str = form.get(f'{idx}_order', str(i + 1))
        try:
            order = int(order_str)
        except (ValueError, TypeError):
            order = i + 1

        # 第一步：从表单构建 data，同时记录表单涉及的字段集合
        data = {}
        form_fields_for_module = set()  # 记录表单实际涉及的字段名（不含子字段后缀）
        for key in form:
            prefix = f'{idx}_data_'
            if key.startswith(prefix) and '_resp_' not in key:
                field = key[len(prefix):]
                if not any(k in key for k in ('_resp_tablet_', '_resp_mobile_', '_resp_columns', '_resp_max_items', '_resp_items_per_page')):
                    # 去掉子字段后缀（如 images_0_url → images）
                    base_field = field.split('_')[0] if '_' in field else field
                    form_fields_for_module.add(base_field)
                    form_fields_for_module.add(field)
                    data[field] = _parse_value(form.get(key, ''))


        # ===== 通用 data-* list/grid 条目解析 =====
        # 若该模块是 data-* 声明式且 schema 含 list/grid 字段，按 schema 通用还原：
        #   module_<i>_<listName>_count + module_<i>_<listName>_<j>_<subField>
        # → data[listName] = [{subField: val, ...}, ...]
        # 命中的 listName 记入 handled_lists，跳过后面对应的硬编码分支（避免重复解析）。
        # 现有模块走旧 Jinja2 编辑器用单数命名（feature_count 等），count_key 不存在 →
        # 不命中，仍由硬编码分支处理，两套互不干扰。
        handled_lists = set()
        _schema = schema_by_type.get(m_type)
        if _schema is not None:
            # 递归遍历所有字段（穿透 group 的 children），确保嵌套 list/grid 也能被解析
            def _schema_children(field):
                children = field.get('children') or field.get('item_fields') or []
                normalized = []
                for child in children:
                    if not isinstance(child, dict):
                        continue
                    c = dict(child)
                    c['name'] = c.get('name') or c.get('key') or ''
                    if c.get('name'):
                        normalized.append(c)
                return normalized

            def _iter_list_fields(fields):
                for f in fields:
                    if f.get('type', '') in ('list', 'grid'):
                        yield f
                    children = _schema_children(f)
                    if children:
                        yield from _iter_list_fields(children)

            for lf in _iter_list_fields(_schema.get('fields', [])):
                list_name = lf.get('name', '')
                # 兼容两种表单 key 格式:
                #   schema 表单 → module_0_images_count（无 _data_）
                #   admin_modules.js 硬编码 → module_0_data_images_count（有 _data_）
                count_key = f'{idx}_{list_name}_count'
                alt_count_key = f'{idx}_data_{list_name}_count'
                is_alt_fmt = False
                if count_key not in form:
                    if alt_count_key in form:
                        count_key = alt_count_key
                        is_alt_fmt = True
                    else:
                        continue  # 表单未表达该 list
                try:
                    item_n = int(form.get(count_key, '0') or '0')
                except (ValueError, TypeError):
                    item_n = 0
                # 子字段名 + 类型 + data-href 字段名
                sub_specs = [(c.get('name', ''), c.get('type', ''), c.get('href_field', '')) for c in _schema_children(lf)]
                items = []
                for j in range(item_n):
                    item_prefix = f'{idx}_data_{list_name}_{j}_' if is_alt_fmt else f'{idx}_{list_name}_{j}_'
                    entry = {}
                    for sub_name, sub_type, href_field in sub_specs:
                        # 图片/视频/网页包字段：优先处理文件上传，否则取 URL 文本值
                        if sub_type in ('image', 'video', 'embed'):
                            upload = request.files.get(f'{item_prefix}{sub_name}_file')
                            if upload and upload.filename:
                                try:
                                    if sub_type == 'embed':
                                        # 网页包：zip → 解压为可嵌入页面
                                        result = _save_media_package(
                                            _current_context()[1].id, upload
                                        )
                                        val = result.get('entry_url', '')
                                    else:
                                        val = _save_uploaded_media(
                                            _current_context()[1].id, upload,
                                            prefix=f'{m_type}-{sub_name}-{j + 1}'
                                        )
                                except Exception as exc:
                                    current_app.logger.warning('上传失败: %s', exc)
                                    val = _parse_value(form.get(f'{item_prefix}{sub_name}', ''))
                            else:
                                val = _parse_value(form.get(f'{item_prefix}{sub_name}', ''))
                        else:
                            val = _parse_value(form.get(f'{item_prefix}{sub_name}', ''))
                        if val not in (None, ''):
                            entry[sub_name] = val
                        if href_field:
                            hval = _parse_value(form.get(f'{item_prefix}{href_field}', ''))
                            if hval not in (None, ''):
                                entry[href_field] = hval
                    if entry:  # 跳过完全空白的条目
                        items.append(entry)
                data[list_name] = items
                form_fields_for_module.add(list_name)  # 表单已表达该列表；空列表也要覆盖旧数据
                handled_lists.add(list_name)

        # 通用 data-* 顶层 image/video/embed 字段：处理文件上传（list 内字段已在上面处理）
        if _schema is not None:
            for lf in _schema.get('fields', []):
                if lf.get('type', '') in ('list', 'grid', 'group'):
                    continue
                if lf.get('type', '') not in ('image', 'video', 'embed'):
                    continue
                field_name = lf.get('name', '')
                upload = request.files.get(f'{idx}_data_{field_name}_file')
                if upload and upload.filename:
                    try:
                        if lf.get('type', '') == 'embed':
                            # 网页包：zip → 解压为可嵌入页面
                            result = _save_media_package(
                                _current_context()[1].id, upload
                            )
                            data[field_name] = result.get('entry_url', '')
                        else:
                            data[field_name] = _save_uploaded_media(
                                _current_context()[1].id, upload,
                                prefix=f'{m_type}-{field_name}'
                            )
                    except Exception as exc:
                        current_app.logger.warning('上传失败 %s: %s', field_name, exc)

            style_tokens = list(_schema.get('style_tokens', []) or [])
            for token in _schema.get('element_style_tokens', []) or []:
                if token not in style_tokens:
                    style_tokens.append(token)
            for token in style_tokens:
                sdef = style_registry.get_style_def(token)
                if not sdef or sdef.get('control') != 'image':
                    continue
                upload = request.files.get(f'{idx}_data_style_{token}_file')
                if upload and upload.filename:
                    try:
                        data[f'style_{token}'] = _save_uploaded_media(
                            _current_context()[1].id, upload,
                            prefix=f'{m_type}-style-{token}'
                        )
                    except Exception as exc:
                        current_app.logger.warning('样式图片上传失败 %s: %s', token, exc)

        if m_type == 'hero_banner':
            slide_count = 0
            try:
                slide_count = int(form.get(f'{idx}_slide_count', '0'))
            except (ValueError, TypeError):
                slide_count = 0

            slides = []
            for slide_i in range(slide_count):
                slide_prefix = f'{idx}_slide_{slide_i}_'
                slide = {}
                for field in (
                    'type', 'media', 'title', 'subtitle', 'badge',
                    'primaryBtn', 'primaryBtnLink', 'primaryBtnLinkTarget',
                    'secondaryBtn', 'secondaryBtnLink',
                    'cta_text', 'cta_url', 'video_url', 'background_image'
                ):
                    value = form.get(f'{slide_prefix}{field}', '').strip()
                    if value:
                        slide[field] = _parse_value(value)

                upload = request.files.get(f'{slide_prefix}file')
                if upload and upload.filename:
                    media_url = _save_uploaded_media(
                        _current_context()[1].id,
                        upload,
                        prefix=f'{m_type}-slide-{slide_i + 1}',
                    )
                    suffix = upload.filename.rsplit('.', 1)[-1].lower() if '.' in upload.filename else ''
                    slide['type'] = 'video' if suffix in ALLOWED_VIDEO_EXTENSIONS else 'image'
                    slide['media'] = media_url

                if slide.get('media') or slide.get('title') or slide.get('subtitle'):
                    slides.append(slide)

            if slides:
                data['slides'] = slides
            else:
                slides_value = data.get('slides')
                if isinstance(slides_value, list):
                    data['slides'] = slides_value
                elif isinstance(slides_value, str) and slides_value.strip():
                    parsed_slides = _parse_value(slides_value)
                    if isinstance(parsed_slides, list):
                        data['slides'] = parsed_slides

            uploaded_slides = []
            for upload in request.files.getlist(f'{idx}_data_slides_files'):
                if upload and upload.filename:
                    media_url = _save_uploaded_media(
                        _current_context()[1].id,
                        upload,
                        prefix=f'{m_type}-slide',
                    )
                    suffix = upload.filename.rsplit('.', 1)[-1].lower() if '.' in upload.filename else ''
                    uploaded_slides.append({
                        'type': 'video' if suffix in ALLOWED_VIDEO_EXTENSIONS else 'image',
                        'media': media_url,
                        'title': data.get('title', ''),
                        'subtitle': data.get('subtitle', ''),
                        'primaryBtn': data.get('primaryBtn') or data.get('cta_text', ''),
                        'primaryBtnLink': data.get('primaryBtnLink') or data.get('cta_url', ''),
                        'cta_text': data.get('cta_text', ''),
                        'cta_url': data.get('cta_url', ''),
                        'badge': data.get('badge', ''),
                    })
            if uploaded_slides:
                existing = data.get('slides') if isinstance(data.get('slides'), list) else []
                data['slides'] = existing + uploaded_slides

        if m_type == 'item_detail':
            # data-* schema 表单（_schemaListEditor）已走通用 list 解析，
            # 这里仅作旧 Jinja2 / admin_modules.js 表单的兜底（handled_lists 守卫）。
            if 'images' not in handled_lists:
                images_count = 0
                try:
                    images_count = int(form.get(f'{idx}_data_images_count', '0'))
                except (ValueError, TypeError):
                    pass
                images = []
                for ii in range(images_count):
                    url = form.get(f'{idx}_data_images_{ii}_url', '').strip()
                    upload = request.files.get(f'{idx}_data_images_{ii}_url_file')
                    if upload and upload.filename:
                        try:
                            url = _save_uploaded_image(
                                _current_context()[1].id, upload,
                                prefix=f'{m_type}-img-{ii + 1}'
                            )
                        except Exception as exc:
                            current_app.logger.warning('模块图片上传失败: %s', exc)
                    if url:
                        images.append({'url': url})
                if images:
                    data['images'] = images
                else:
                    data.pop('images', None)

            if 'specs' not in handled_lists:
                specs_count = 0
                try:
                    specs_count = int(form.get(f'{idx}_data_specs_count', '0'))
                except (ValueError, TypeError):
                    pass
                specs = []
                for si in range(specs_count):
                    name = form.get(f'{idx}_data_specs_{si}_name', '').strip()
                    value = form.get(f'{idx}_data_specs_{si}_value', '').strip()
                    if name or value:
                        specs.append({'name': name, 'value': value})
                if specs:
                    data['specs'] = specs
                else:
                    data.pop('specs', None)

        if m_type == 'item_data':
            # item_data 的 images / specs 表单字段命名与 item_detail 完全一致
            # （admin_modules.js 硬编码编辑器使用相同前缀 module_X_data_images_Y_url）,
            # 这里复用相同的解析逻辑，确保不依赖 schema_by_type 的通用解析路径
            if 'images' not in handled_lists:
                images_count = 0
                try:
                    images_count = int(form.get(f'{idx}_data_images_count', '0'))
                except (ValueError, TypeError):
                    pass
                images = []
                for ii in range(images_count):
                    url = form.get(f'{idx}_data_images_{ii}_url', '').strip()
                    upload = request.files.get(f'{idx}_data_images_{ii}_url_file')
                    if upload and upload.filename:
                        try:
                            url = _save_uploaded_image(
                                _current_context()[1].id, upload,
                                prefix=f'{m_type}-img-{ii + 1}'
                            )
                        except Exception as exc:
                            current_app.logger.warning('item_data 图片上传失败: %s', exc)
                    if url:
                        images.append({'url': url})
                if images:
                    data['images'] = images
                else:
                    data.pop('images', None)

            if 'specs' not in handled_lists:
                specs_count = 0
                try:
                    specs_count = int(form.get(f'{idx}_data_specs_count', '0'))
                except (ValueError, TypeError):
                    pass
                specs = []
                for si in range(specs_count):
                    name = form.get(f'{idx}_data_specs_{si}_name', '').strip()
                    value = form.get(f'{idx}_data_specs_{si}_value', '').strip()
                    if name or value:
                        specs.append({'name': name, 'value': value})
                if specs:
                    data['specs'] = specs
                else:
                    data.pop('specs', None)

        if m_type == 'feature_grid' and 'features' not in handled_lists:
            feature_count = 0
            try:
                feature_count = int(form.get(f'{idx}_features_count', '0'))
            except (ValueError, TypeError):
                feature_count = 0

            features = []
            for fi in range(feature_count):
                prefix = f'{idx}_features_{fi}_'
                item = {}
                for field in ('icon', 'title', 'desc'):
                    value = form.get(f'{prefix}{field}', '').strip()
                    if value:
                        item[field] = value
                if item.get('title') or item.get('desc') or item.get('icon'):
                    features.append(item)

            if features:
                data['features'] = features
            else:
                features_value = data.get('features')
                if isinstance(features_value, list):
                    data['features'] = features_value
                elif isinstance(features_value, str) and features_value.strip():
                    parsed_features = _parse_value(features_value)
                    if isinstance(parsed_features, list):
                        data['features'] = parsed_features

        # 解析 stat_counter 的统计项列表
        if m_type == 'stat_counter' and 'stats' not in handled_lists:
            stat_count = 0
            try:
                stat_count = int(form.get(f'{idx}_stats_count', '0'))
            except (ValueError, TypeError):
                stat_count = 0
            stats = []
            for si in range(stat_count):
                prefix = f'{idx}_stats_{si}_'
                item = {}
                for field in ('icon', 'number', 'suffix', 'label'):
                    value = form.get(f'{prefix}{field}', '').strip()
                    if value:
                        item[field] = value
                if item.get('label') or item.get('number'):
                    stats.append(item)
            if stats:
                data['stats'] = stats

        # 解析 logo_cloud 的 Logo 列表
        if m_type == 'logo_cloud' and 'logos' not in handled_lists:
            logo_count = 0
            try:
                logo_count = int(form.get(f'{idx}_logos_count', '0'))
            except (ValueError, TypeError):
                logo_count = 0
            logos = []
            for li in range(logo_count):
                prefix = f'{idx}_logos_{li}_'
                item = {}
                # 键名对齐 data-* 模板：图片存 logo、链接存 link（renderer 读这两个 key）
                for field in ('logo', 'link'):
                    value = form.get(f'{prefix}{field}', '').strip()
                    if value:
                        item[field] = value
                upload = request.files.get(f'{prefix}logo_file')
                if upload and upload.filename:
                    try:
                        item['logo'] = _save_uploaded_image(
                            _current_context()[1].id,
                            upload,
                            prefix=f'logo-{li + 1}',
                        )
                    except Exception as exc:
                        current_app.logger.warning('Logo 图片上传失败: %s', exc)
                if item.get('logo'):
                    logos.append(item)
            if logos:
                data['logos'] = logos

        # 解析 process_steps 的步骤列表
        if m_type == 'process_steps' and 'steps' not in handled_lists:
            step_count = 0
            try:
                step_count = int(form.get(f'{idx}_step_count', '0'))
            except (ValueError, TypeError):
                step_count = 0
            steps = []
            for si in range(step_count):
                prefix = f'{idx}_step_{si}_'
                item = {}
                for field in ('title', 'desc', 'icon'):
                    value = form.get(f'{prefix}{field}', '').strip()
                    if value:
                        item[field] = value
                if item.get('title') or item.get('desc'):
                    steps.append(item)
            if steps:
                data['steps'] = steps


        # 处理模块顶层图片字段：扫描 data 中所有字段，找到图片字段（image/cover 等），
        # 从 request.files 中取对应 _file 后缀的文件。跳过 _convert_webp 等辅助字段。
        # 注意：data 里可能混入了 image_file（文件输入框的值）和 image_convert_webp
        # （勾选框值），需要按后缀精确过滤，避免误把文件名或 'true' 当作图片 URL。
        for field in list(data.keys()):
            # 跳过文件输入框值和 WebP 转换标记——它们不是图片 URL
            if field.endswith('_file') or field.endswith('_convert_webp'):
                continue
            if _field_looks_like_image(field):
                upload = request.files.get(f'{idx}_data_{field}_file')
                if upload and upload.filename:
                    try:
                        data[field] = _save_uploaded_image(
                            _current_context()[1].id,
                            upload,
                            prefix=f'{m_type}-{field}',
                        )
                    except Exception as exc:
                        current_app.logger.warning('模块图片保存失败 %s: %s', field, exc)

        # 兼容旧表单：仅模块自身真正支持时才接收这些顶层字段
        columns_val = form.get(f'{idx}_resp_columns', '').strip()
        if columns_val and m_type in data_field_allowed_types['columns']:
            try:
                data['columns'] = int(columns_val)
            except ValueError:
                pass
        max_items_val = form.get(f'{idx}_resp_max_items', '').strip()
        if max_items_val and m_type in data_field_allowed_types['max_items']:
            try:
                data['max_items'] = int(max_items_val)
            except ValueError:
                pass
        items_per_page_val = form.get(f'{idx}_resp_items_per_page', '').strip()
        if items_per_page_val and m_type in data_field_allowed_types['items_per_page']:
            try:
                data['items_per_page'] = int(items_per_page_val)
            except ValueError:
                pass

        # 解析响应式配置
        responsive = {}
        for device in ('tablet', 'mobile'):
            device_data = {}
            # 设备独立数据字段
            for key in form:
                prefix = f'{idx}_resp_{device}_data_'
                if key.startswith(prefix):
                    field = key[len(prefix):]
                    val = form.get(key, '').strip()
                    if val:
                        device_data[field] = _parse_value(val)

            # 设备 hidden
            if form.get(f'{idx}_resp_{device}_hidden'):
                device_data['hidden'] = True

            if device_data:
                responsive[device] = device_data

        # 第二步：从已有数据中保留表单未涉及的字段（防止嵌套数组丢失）
        existing_key = (m_type, order)
        if existing_key in existing_by_key and isinstance(existing_by_key[existing_key], dict):
            for ek, ev in existing_by_key[existing_key].items():
                if ek not in form_fields_for_module and ek not in data:
                    data[ek] = ev
                elif ek in form_fields_for_module and ek not in data:
                    # 表单表达了该字段（如 images_count）但解析后 data 中没有该 key
                    # （如图片列表为空未设置 data['images']）→ 从旧数据恢复
                    data[ek] = ev

        if m_type == 'stat_counter' and data.get('columns') and not data.get('style_cols'):
            data['style_cols'] = str(data.get('columns'))

        for stale_field, allowed_types in data_field_allowed_types.items():
            if m_type not in allowed_types:
                data.pop(stale_field, None)
        for device_data in responsive.values():
            for stale_field in data_field_allowed_types:
                device_data.pop(stale_field, None)
        responsive = {device: cfg for device, cfg in responsive.items() if cfg}

        module = {
            'type': m_type,
            'order': order,
            'variant': variant,
            'data': data,
        }
        if responsive:
            module['responsive'] = responsive

        modules.append(module)

    return modules
