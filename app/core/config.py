"""配置加载. 优先级: override 参数 > 环境变量 > 默认值."""
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent.parent

# 加载 .env (如果存在)
load_dotenv(ROOT / '.env')


def _resolve_secret_key():
    """SECRET_KEY: 生产环境必须从 SECRET_KEY 环境变量获取, 否则拒绝启动;
    开发环境允许使用临时默认值, 但打出警告提醒补 .env."""
    key = os.environ.get('SECRET_KEY', '').strip()
    env = os.environ.get('FLASK_ENV', '').strip().lower()
    is_prod = env in ('production', 'prod') or os.environ.get('FLASK_DEBUG', '').strip() == '0'
    if not key:
        if is_prod:
            raise RuntimeError(
                '生产环境必须设置 SECRET_KEY 环境变量（建议 32+ 字节随机字符串）。'
                '参考 .env.example，可用 python -c "import secrets; print(secrets.token_urlsafe(48))" 生成。'
            )
        logger.warning('SECRET_KEY 未设置，开发环境使用临时默认值；生产部署前必须改！')
        key = 'dev-only-do-not-use-in-prod'
    return key


def load_config(override=None):
    instance_dir = ROOT / 'instance'
    instance_dir.mkdir(parents=True, exist_ok=True)

    config = {
        'SQLALCHEMY_DATABASE_URI': os.environ.get(
            'DATABASE_URL',
            f'sqlite:///{instance_dir / "app.db"}',
        ),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': _resolve_secret_key(),

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
