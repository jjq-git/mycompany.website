"""店主网站文件夹的读写工具.

约定: 每个店主网站一个文件夹 sites/<site_id>/, 内容如下:

    sites/<site_id>/
    ├── settings.yaml         站点设置
    ├── pages/*.yaml          页面字段值 (默认语言)
    ├── data/*.yaml           数据集 (默认语言)
    ├── translations/*.yaml   翻译缓存 (Phase 2)
    ├── lang/<code>/          其他语言版本
    │   ├── pages/*.yaml
    │   ├── data/*.yaml
    │   └── settings.yaml     语言特有设置 (如 menu 覆盖)
    └── assets/               上传的图片/文件
"""
import os
import shutil
import tempfile
from pathlib import Path

import yaml
from flask import abort, current_app
from werkzeug.utils import secure_filename


MEDIA_CATEGORIES = {
    'image': {
        'label': '图片',
        'extensions': {'jpg', 'jpeg', 'png', 'webp', 'gif', 'svg'},
    },
    'video': {
        'label': '视频',
        'extensions': {'mp4', 'webm', 'ogg', 'mov'},
    },
    'document': {
        'label': '文档',
        'extensions': {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv'},
    },
}

_MEDIA_PACKAGE_PREFIX = '__package__:'


def _is_content_yaml(path):
    """Return true for real content YAML files, excluding atomic-write leftovers."""
    name = Path(path).name
    return name.endswith(('.yaml', '.yml')) and not name.startswith('.tmp-')


def site_root(site_id):
    """获取站点的文件夹路径."""
    base = Path(current_app.config['SITES_DIR'])
    return base / str(site_id)


def media_package_token(package_name):
    """Return the API token used to address a media package."""
    return f'{_MEDIA_PACKAGE_PREFIX}{package_name}'


def is_media_package_token(name):
    return isinstance(name, str) and name.startswith(_MEDIA_PACKAGE_PREFIX)


def media_package_name_from_token(name):
    return name[len(_MEDIA_PACKAGE_PREFIX):] if is_media_package_token(name) else name


def lang_root(site_id, lang_code):
    """获取站点某语言版本的根目录 (lang/<code>/)."""
    return site_root(site_id) / 'lang' / lang_code


def _safe_path(site_id, relative_path, lang=None):
    """把 relative_path 解析到站点(或语言)根目录下, 并强制校验不逃出边界.

    为什么需要: page_key / dataset_key 经 Flask <path:> 转换器接收, 保留了
    `..` 和 `/`, 一路传到这里拼成 relative_path。若不校验, 已登录店主可用
    `../../<别人站点id>/...` 跨租户读写他人 .yaml, 或写到 sites/ 目录之外。
    这里是所有 YAML 读写的单一出口, 在此兜底一次即可全覆盖。
    """
    base = (lang_root(site_id, lang) if lang else site_root(site_id)).resolve()
    full = (base / relative_path).resolve()
    try:
        full.relative_to(base)
    except ValueError:
        abort(400, '非法路径')
    return full


def init_site_folder(site_id):
    """为新站点创建初始目录结构."""
    folder = site_root(site_id)
    for sub in ('pages', 'data', 'translations', 'assets'):
        (folder / sub).mkdir(parents=True, exist_ok=True)
    return folder


def write_yaml(site_id, relative_path, data, lang=None):
    """写 YAML 文件到 sites/<id>/<relative_path>.

    如果指定了 lang (非默认语言), 写入 lang/<lang>/<relative_path>.
    """
    path = _safe_path(site_id, relative_path, lang=lang)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, indent=2)
    # 原子写: 这是店主网站内容(pages/data/settings)的唯一权威副本, 无备份、不入仓。
    # 直接 'w' 模式会先把目标截断为 0 再写, 进程中途崩溃/被 kill/磁盘满就会
    # 留下截断或半写的损坏文件(yaml.safe_load 静默返回 None, 内容全失)。
    # 改为: 先写同目录临时文件 -> fsync 落盘 -> os.replace 原子替换。
    # 与产品 P0 信念"网站像 PDF, 5 年后还能打开"一致。
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix='.tmp-', suffix='.yaml')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)  # 同目录原子替换, 替换前后目标始终是完整文件
    except Exception:
        # 写失败时清理临时文件, 不留垃圾; 原文件保持原样(未被截断)
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def read_yaml(site_id, relative_path, default=None, lang=None):
    """读 YAML 文件.

    如果指定了 lang: 先尝试 lang/<lang>/<relative_path>, 不存在则回退到根路径.
    不指定 lang: 只读根路径.
    """
    # 先尝试语言特定版本 (路径同样过 _safe_path 兜底, 防 .. 逃逸)
    if lang:
        lang_path = _safe_path(site_id, relative_path, lang=lang)
        if lang_path.exists():
            return yaml.safe_load(lang_path.read_text(encoding='utf-8'))

    # 回退到根路径
    path = _safe_path(site_id, relative_path)
    if not path.exists():
        return default
    return yaml.safe_load(path.read_text(encoding='utf-8'))


def copy_seed_data(site_id, template_name):
    """把模板的 seed_data/ 复制到店主文件夹.

    seed_data/ 的目录结构跟店主网站一致, 直接复制即可.
    """
    src = Path(current_app.config['TEMPLATES_DIR']) / template_name / 'seed_data'
    if not src.exists():
        return False

    dst = site_root(site_id)
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, dirs_exist_ok=True)
    return True


def list_yaml_files(site_id, subdir, lang=None):
    """列出某子目录下的所有 YAML 文件.

    如果指定了 lang, 同时列出语言特定目录和根目录的文件 (去重).
    """
    items = []
    seen = set()

    # 语言特定文件优先
    if lang:
        lang_dir = lang_root(site_id, lang) / subdir
        if lang_dir.exists():
            for f in sorted(lang_dir.glob('*.yaml')):
                if not _is_content_yaml(f):
                    continue
                seen.add(f.name)
                items.append(f)

    # 根目录文件 (排除已存在的)
    path = site_root(site_id) / subdir
    if path.exists():
        for f in sorted(path.glob('*.yaml')):
            if not _is_content_yaml(f):
                continue
            if f.name not in seen:
                items.append(f)

    return items


def _format_size(size_bytes):
    size = float(size_bytes or 0)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024 or unit == 'GB':
            if unit == 'B':
                return f'{int(size)} B'
            return f'{size:.1f} {unit}'
        size /= 1024
    return f'{int(size_bytes or 0)} B'


def _media_category_for_extension(ext):
    ext = (ext or '').lower().lstrip('.')
    for category, meta in MEDIA_CATEGORIES.items():
        if ext in meta['extensions']:
            return category
    return 'other'


def _safe_media_filename(filename):
    filename = (filename or '').strip()
    if not filename or filename.startswith(('.', '/')) or '\\' in filename or '/' in filename or '..' in filename:
        abort(400, '非法文件名')
    safe = secure_filename(filename)
    if not safe or safe != filename:
        abort(400, '非法文件名')
    return safe


def _safe_package_name(package_name):
    package_name = (package_name or '').strip()
    if not package_name or package_name.startswith(('.', '/')) or '\\' in package_name or '/' in package_name or '..' in package_name:
        abort(400, '非法网页包名称')
    safe = secure_filename(package_name)
    if not safe or safe != package_name:
        abort(400, '非法网页包名称')
    return safe


def _directory_size(path):
    total = 0
    if not path.exists():
        return 0
    for item in path.rglob('*'):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                continue
    return total


def list_media_files(site_id):
    """List uploaded files and iframe-previewable media packages for a site."""
    assets_root = site_root(site_id) / 'assets'
    uploads_dir = assets_root / 'uploads'
    packages_dir = assets_root / 'media-packages'
    items = []

    if uploads_dir.exists():
        for path in sorted(uploads_dir.iterdir(), key=lambda p: p.name.lower()):
            if not path.is_file() or path.name.startswith('.'):
                continue
            ext = path.suffix.lower().lstrip('.')
            stat = path.stat()
            category = _media_category_for_extension(ext)
            items.append({
                'name': path.name,
                'display_name': path.name,
                'size_bytes': stat.st_size,
                'size_display': _format_size(stat.st_size),
                'mtime': stat.st_mtime,
                'category': category,
                'category_label': MEDIA_CATEGORIES.get(category, {}).get('label', '其他'),
                'ext': ext,
                'url': f'/assets/uploads/{path.name}',
                'api_name': path.name,
                'is_package': False,
            })

    if packages_dir.exists():
        for path in sorted(packages_dir.iterdir(), key=lambda p: p.name.lower()):
            if not path.is_dir() or path.name.startswith('.') or not (path / 'index.html').exists():
                continue
            size = _directory_size(path)
            mtime = max((p.stat().st_mtime for p in path.rglob('*') if p.exists()), default=path.stat().st_mtime)
            entry_url = f'/media-packages/{path.name}/'
            items.append({
                'name': path.name,
                'display_name': path.name,
                'size_bytes': size,
                'size_display': _format_size(size),
                'mtime': mtime,
                'category': 'package',
                'category_label': '网页包',
                'ext': 'package',
                'url': entry_url,
                'entry_url': entry_url,
                'api_name': media_package_token(path.name),
                'is_package': True,
            })

    return sorted(items, key=lambda item: (item['category'], item['display_name'].lower()))


def get_media_file_path(site_id, filename):
    filename = _safe_media_filename(filename)
    path = (site_root(site_id) / 'assets' / 'uploads' / filename).resolve()
    base = (site_root(site_id) / 'assets' / 'uploads').resolve()
    try:
        path.relative_to(base)
    except ValueError:
        abort(400, '非法文件路径')
    if not path.exists() or not path.is_file():
        abort(404, '文件不存在')
    return path


def get_media_package_path(site_id, package_name):
    package_name = _safe_package_name(package_name)
    path = (site_root(site_id) / 'assets' / 'media-packages' / package_name).resolve()
    base = (site_root(site_id) / 'assets' / 'media-packages').resolve()
    try:
        path.relative_to(base)
    except ValueError:
        abort(400, '非法网页包路径')
    if not path.exists() or not path.is_dir():
        abort(404, '网页包不存在')
    return path


def find_media_references(site_id, name):
    """Find YAML files that reference an uploaded file or media package."""
    is_package = is_media_package_token(name)
    target_name = media_package_name_from_token(name)
    if is_package:
        target_name = _safe_package_name(target_name)
        needle = f'/media-packages/{target_name}/'
    else:
        target_name = _safe_media_filename(target_name)
        needle = f'/assets/uploads/{target_name}'

    refs = []
    root = site_root(site_id)
    if not root.exists():
        return refs
    yaml_paths = list(root.rglob('*.yaml')) + list(root.rglob('*.yml'))
    for path in sorted(yaml_paths):
        if not _is_content_yaml(path):
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        if needle in text:
            refs.append(str(path.relative_to(root)).replace('\\', '/'))
    return refs


def rename_media_file(site_id, old_name, new_name):
    """Rename an unreferenced upload file or media package."""
    if find_media_references(site_id, old_name):
        abort(409, '文件已被引用，不能重命名')

    if is_media_package_token(old_name):
        old_pkg = _safe_package_name(media_package_name_from_token(old_name))
        new_pkg = _safe_package_name(media_package_name_from_token(new_name))
        src = get_media_package_path(site_id, old_pkg)
        dst = src.parent / new_pkg
        if dst.exists():
            abort(409, '目标名称已存在')
        os.rename(src, dst)
        return media_package_token(new_pkg)

    old_file = _safe_media_filename(old_name)
    new_file = _safe_media_filename(new_name)
    src = get_media_file_path(site_id, old_file)
    dst = src.parent / new_file
    if dst.exists():
        abort(409, '目标名称已存在')
    os.rename(src, dst)
    return new_file


def delete_media_file(site_id, name):
    """Delete an unreferenced upload file or media package."""
    if find_media_references(site_id, name):
        abort(409, '文件已被引用，不能删除')

    if is_media_package_token(name):
        package_name = _safe_package_name(media_package_name_from_token(name))
        path = get_media_package_path(site_id, package_name)
        shutil.rmtree(path)
        return True

    filename = _safe_media_filename(name)
    path = get_media_file_path(site_id, filename)
    path.unlink()
    return True
