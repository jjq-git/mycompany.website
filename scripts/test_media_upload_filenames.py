"""Regression checks for uploads whose original filename contains only CJK text."""
import io
import sys
import tempfile
import zipfile
from pathlib import Path

from flask import Flask
from PIL import Image
from werkzeug.datastructures import FileStorage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core import media_service


def check(label, condition):
    if not condition:
        raise AssertionError(label)
    print(f'PASS: {label}')


def upload(contents, filename, field_name='upload_file'):
    return FileStorage(
        stream=io.BytesIO(contents),
        filename=filename,
        name=field_name,
    )


image_stream = io.BytesIO()
Image.new('RGB', (4, 4), '#078b81').save(image_stream, 'PNG')
image_bytes = image_stream.getvalue()

zip_stream = io.BytesIO()
with zipfile.ZipFile(zip_stream, 'w') as archive:
    archive.writestr('index.html', '<!doctype html><title>测试</title>')

with tempfile.TemporaryDirectory(prefix='media-upload-filename-') as tmp:
    app = Flask(__name__)
    app.config['SITES_DIR'] = str(Path(tmp) / 'sites')

    with app.test_request_context('/', method='POST'):
        image = upload(image_bytes, '触控控制器定制设计展板.png')
        image_url = media_service.save_uploaded_image(6, image, prefix='highlight-card')
        image_path = Path(app.config['SITES_DIR']) / '6' / image_url.lstrip('/')
        check('CJK image filename keeps its PNG suffix', image_url.endswith('.webp'))
        check('CJK image upload is written', image_path.is_file())
        check('CJK image filename becomes useful alt text',
              media_service.filename_alt(upload(image_bytes, '触控控制器定制设计展板.png'))
              == '触控控制器定制设计展板')

        video_url = media_service.save_uploaded_media(
            6, upload(b'fake mp4 bytes', '产品演示视频.mp4'), prefix='demo-video'
        )
        check('CJK video filename keeps its MP4 suffix', video_url.endswith('.mp4'))

        file_url = media_service.save_any_file(
            6, upload(b'%PDF-1.4', '产品规格书.pdf'), prefix='datasheet'
        )
        check('CJK attachment filename keeps its PDF suffix', file_url.endswith('.pdf'))

        package = media_service.save_media_package(
            6, upload(zip_stream.getvalue(), '交互演示包.zip')
        )
        check('CJK package filename keeps its ZIP suffix',
              package['entry_url'].startswith('/assets/media-packages/')
              and package['entry_url'].endswith('/'))
        package_dir = (
            Path(app.config['SITES_DIR']) / '6' / 'assets' / 'media-packages' / package['name']
        )
        check('CJK package upload is unpacked', (package_dir / 'index.html').is_file())

print('All CJK upload filename checks passed.')
