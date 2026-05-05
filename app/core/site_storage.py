"""店主网站文件夹的读写工具.

约定: 每个店主网站一个文件夹 sites/<site_id>/, 内容如下:

    sites/<site_id>/
    ├── settings.yaml         站点设置
    ├── pages/*.yaml          页面字段值
    ├── data/*.yaml           数据集 (产品/案例/博客)
    ├── translations/*.yaml   翻译缓存 (Phase 2)
    └── assets/               上传的图片/文件
"""
import shutil
from pathlib import Path

import yaml
from flask import current_app


def site_root(site_id):
    """获取站点的文件夹路径."""
    base = Path(current_app.config['SITES_DIR'])
    return base / str(site_id)


def init_site_folder(site_id):
    """为新站点创建初始目录结构."""
    folder = site_root(site_id)
    for sub in ('pages', 'data', 'translations', 'assets'):
        (folder / sub).mkdir(parents=True, exist_ok=True)
    return folder


def write_yaml(site_id, relative_path, data):
    """写 YAML 文件到 sites/<id>/<relative_path>."""
    path = site_root(site_id) / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, indent=2),
        encoding='utf-8',
    )


def read_yaml(site_id, relative_path, default=None):
    """读 YAML 文件. 不存在返回 default."""
    path = site_root(site_id) / relative_path
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


def list_yaml_files(site_id, subdir):
    """列出某子目录下的所有 YAML 文件."""
    path = site_root(site_id) / subdir
    if not path.exists():
        return []
    return sorted(path.glob('*.yaml'))
