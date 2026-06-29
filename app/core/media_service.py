"""Media upload and image alt helpers for the dashboard."""
import re
import secrets
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from flask import current_app, request
from werkzeug.utils import secure_filename

from .site_storage import media_package_token


ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov'}
ALLOWED_FILE_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS | {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 'zip'
}
MAX_GENERIC_FILE_BYTES = 32 * 1024 * 1024
MAX_MEDIA_PACKAGE_BYTES = 64 * 1024 * 1024
MAX_MEDIA_PACKAGE_UNCOMPRESSED_BYTES = 96 * 1024 * 1024
MAX_MEDIA_PACKAGE_DEPTH = 10
MAX_IMAGE_PIXELS = 16_000_000
MAX_IMAGE_BYTES = 12 * 1024 * 1024


def check_upload_size(file_storage, max_bytes, label='文件'):
    stream = file_storage.stream
    try:
        stream.seek(0, 2)
        size = stream.tell()
    finally:
        stream.seek(0)
    if size > max_bytes:
        raise ValueError(f'{label}过大: {size // 1024}KB > {max_bytes // 1024}KB 上限')
    return size


def upload_convert_webp_enabled(file_storage):
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


def save_uploaded_image(site_id, file_storage, prefix='image', convert_webp=None):
    """Save an uploaded image under sites/<id>/assets/uploads and return its site URL."""
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
        convert_webp = upload_convert_webp_enabled(file_storage)

    if suffix == 'svg' or not convert_webp:
        check_upload_size(file_storage, MAX_IMAGE_BYTES, label='图片')
        filename = f'{safe_prefix}-{ts}-{hex_part}.{suffix}'
        output_path = uploads_dir / filename
        file_storage.save(str(output_path))
        return f'/assets/uploads/{filename}'

    check_upload_size(file_storage, MAX_IMAGE_BYTES, label='图片')

    try:
        from PIL import Image, ImageSequence
    except ImportError as exc:
        raise RuntimeError('缺少 Pillow 依赖，请先安装 requirements.txt') from exc

    filename = f'{safe_prefix}-{ts}-{hex_part}.webp'
    output_path = uploads_dir / filename

    with Image.open(file_storage.stream) as image:
        w, h = image.size
        if w * h > MAX_IMAGE_PIXELS:
            raise ValueError(f'图片分辨率过大: {w}x{h} 超过 {MAX_IMAGE_PIXELS} 像素上限')
        first_frame = next(ImageSequence.Iterator(image)).convert('RGBA')
    background = Image.new('RGBA', first_frame.size, (255, 255, 255, 0))
    background.alpha_composite(first_frame)
    background.save(output_path, 'WEBP', quality=86, method=6)
    return f'/assets/uploads/{filename}'


def filename_alt(file_storage):
    if not file_storage or not getattr(file_storage, 'filename', ''):
        return ''
    stem = Path(secure_filename(file_storage.filename)).stem
    return re.sub(r'[-_]+', ' ', stem).strip()


def context_alt(*contexts, fallback=''):
    for ctx in contexts:
        if not isinstance(ctx, dict):
            continue
        for key in ('title', 'name', 'label', 'short_name', 'heading'):
            val = ctx.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    return str(fallback or '').strip()


def image_alt_key(field_name):
    field = str(field_name or '').strip()
    if not field:
        return 'alt'
    if field in ('cover', 'photo', 'logo'):
        return f'{field}_alt'
    if field in ('image', 'media', 'url', 'src'):
        return 'alt'
    if field.endswith('_url'):
        return f'{field[:-4]}_alt'
    return f'{field}_alt'


def form_alt_value(form, field_name, *contexts, upload=None, existing=None):
    keys = []
    field = str(field_name or '').strip()
    if field:
        keys.extend([f'{field}_alt', image_alt_key(field)])
    keys.append('alt')
    for key in dict.fromkeys(keys):
        if key in form:
            val = form.get(key, '').strip()
            if val:
                return val
    if existing:
        return str(existing).strip()
    return context_alt(*contexts, fallback=filename_alt(upload))


def save_uploaded_media(site_id, file_storage, prefix='media'):
    """Save an image or video. Images follow the WebP conversion setting."""
    if not file_storage or not file_storage.filename:
        return ''
    original = secure_filename(file_storage.filename)
    if not original:
        return ''
    suffix = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    if suffix in ALLOWED_IMAGE_EXTENSIONS:
        try:
            return save_uploaded_image(site_id, file_storage, prefix=prefix)
        except Exception as exc:
            current_app.logger.warning('图片保存失败: %s', exc)
            return ''
    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        current_app.logger.warning('不支持的文件类型: %s', suffix)
        return ''

    try:
        check_upload_size(file_storage, MAX_IMAGE_BYTES, label='视频')
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


def save_any_file(site_id, file_storage, prefix='file'):
    """Save non-image/non-video files under assets/uploads."""
    if not file_storage or not file_storage.filename:
        return ''
    original = secure_filename(file_storage.filename)
    if not original:
        raise ValueError('文件名无效')
    suffix = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    if suffix not in ALLOWED_FILE_EXTENSIONS or suffix in ALLOWED_IMAGE_EXTENSIONS or suffix in ALLOWED_VIDEO_EXTENSIONS:
        raise ValueError('不支持的文件类型')
    check_upload_size(file_storage, MAX_GENERIC_FILE_BYTES, label='文件')

    uploads_dir = Path(current_app.config['SITES_DIR']) / str(site_id) / 'assets' / 'uploads'
    uploads_dir.mkdir(parents=True, exist_ok=True)
    safe_prefix = secure_filename(prefix or 'file') or 'file'
    stem = Path(original).stem
    safe_stem = secure_filename(stem) or safe_prefix
    filename = f"{safe_prefix}-{safe_stem}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}.{suffix}"
    output_path = uploads_dir / filename
    file_storage.save(output_path)
    return f'/assets/uploads/{filename}'


def safe_zip_member_name(name):
    name = (name or '').replace('\\', '/').strip('/')
    if not name or name.startswith('.') or '\x00' in name:
        raise ValueError('网页包中包含非法文件名')
    path = Path(name)
    if path.is_absolute() or any(part in ('', '.', '..') or part.startswith('.') for part in path.parts):
        raise ValueError('网页包中包含非法路径')
    if len(path.parts) > MAX_MEDIA_PACKAGE_DEPTH:
        raise ValueError('网页包目录层级过深')
    return name


def zip_strip_root(member_names):
    first_parts = [Path(name).parts for name in member_names]
    if not first_parts:
        return ''
    first = first_parts[0][0]
    if all(len(parts) > 1 and parts[0] == first for parts in first_parts):
        return first
    return ''


def uploaded_zip_has_index(file_storage):
    """Return true when an uploaded zip looks like a media package."""
    try:
        file_storage.stream.seek(0)
        archive = zipfile.ZipFile(file_storage.stream)
        with archive:
            infos = [info for info in archive.infolist() if not info.is_dir()]
            if not infos:
                return False
            names = [safe_zip_member_name(info.filename) for info in infos]
            strip_root = zip_strip_root(names)
            normalized = []
            for name in names:
                parts = Path(name).parts
                if strip_root:
                    parts = parts[1:]
                if parts:
                    normalized.append('/'.join(parts))
            return 'index.html' in {name.lower() for name in normalized}
    except Exception:
        return False
    finally:
        try:
            file_storage.stream.seek(0)
        except Exception:
            pass


def save_media_package(site_id, file_storage):
    """Save and unpack a webpage package zip."""
    if not file_storage or not file_storage.filename:
        raise ValueError('请选择网页包 zip 文件')
    original = secure_filename(file_storage.filename)
    suffix = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    if suffix != 'zip':
        raise ValueError('网页包必须是 zip 文件')
    check_upload_size(file_storage, MAX_MEDIA_PACKAGE_BYTES, label='网页包')

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
            names.append(safe_zip_member_name(info.filename))

        strip_root = zip_strip_root(names)
        normalized = []
        for name in names:
            parts = Path(name).parts
            if strip_root:
                parts = parts[1:]
            if parts:
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
