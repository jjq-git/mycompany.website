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
import shutil
from pathlib import Path

import yaml
from flask import abort, current_app


def site_root(site_id):
    """获取站点的文件夹路径."""
    base = Path(current_app.config['SITES_DIR'])
    return base / str(site_id)


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
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, indent=2),
        encoding='utf-8',
    )


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
                seen.add(f.name)
                items.append(f)

    # 根目录文件 (排除已存在的)
    path = site_root(site_id) / subdir
    if path.exists():
        for f in sorted(path.glob('*.yaml')):
            if f.name not in seen:
                items.append(f)

    return items
