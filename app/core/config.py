"""配置加载. 优先级: override 参数 > 环境变量 > 默认值."""
import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent.parent

# 加载 .env (如果存在)
load_dotenv(ROOT / '.env')


def load_config(override=None):
    instance_dir = ROOT / 'instance'
    instance_dir.mkdir(parents=True, exist_ok=True)

    config = {
        'SQLALCHEMY_DATABASE_URI': os.environ.get(
            'DATABASE_URL',
            f'sqlite:///{instance_dir / "app.db"}',
        ),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-key-change-me'),

        # 项目目录
        'ROOT_DIR': str(ROOT),
        'SITES_DIR': str(ROOT / 'sites'),
        'TEMPLATES_DIR': str(ROOT / 'site_templates'),
        'UPLOADS_DIR': str(ROOT / 'uploads'),
        'OUTPUT_DIR': str(ROOT / 'output'),

        # 平台
        'PLATFORM_DOMAIN': os.environ.get('PLATFORM_DOMAIN', 'mycompany.website'),

        # AI 翻译 (DeepSeek / OpenAI 兼容)
        'TRANSLATION_API_KEY': os.environ.get('TRANSLATION_API_KEY', ''),
        'TRANSLATION_API_BASE': os.environ.get('TRANSLATION_API_BASE', 'https://api.deepseek.com/v1'),
        'TRANSLATION_MODEL': os.environ.get('TRANSLATION_MODEL', 'deepseek-chat'),
    }

    if override:
        config.update(override)

    # 确保运行时目录存在
    Path(config['SITES_DIR']).mkdir(parents=True, exist_ok=True)

    return config
