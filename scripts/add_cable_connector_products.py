"""
创建 TC03/TC10/TC25 线材产品 + 下载 CDN 图片
参考产品: DBOX (id=1)
详情页只有图片+文档链接, 无文字规格参数
"""
import yaml, os, hashlib, random, urllib.request, io
from datetime import datetime
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS = os.path.join(ROOT, 'sites', '6', 'assets', 'uploads')
FILEPATH = os.path.join(ROOT, 'sites', '6', 'lang', 'zh-CN', 'data', 'cable-connector.yaml')
os.makedirs(UPLOADS, exist_ok=True)

def _ts_hex():
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    return f'{ts}-{hashlib.md5(str(random.random()).encode()).hexdigest()[:8]}'

def _fetch(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except:
        return None

def _jpg_to_webp(jpg_bytes, quality=82):
    try:
        img = Image.open(io.BytesIO(jpg_bytes)).convert('RGB')
        buf = io.BytesIO()
        img.save(buf, format='WEBP', quality=quality)
        return buf.getvalue()
    except:
        return None

def _save(webp_bytes, prefix):
    name = f'{prefix}-{_ts_hex()}.webp'
    with open(os.path.join(UPLOADS, name), 'wb') as f:
        f.write(webp_bytes)
    return f'/assets/uploads/{name}'

def download_images(cdn_filenames, prefix):
    """下载图片: 封面用第一张, 全部作为 gallery"""
    base = 'https://cdn.dengtec.com/cnw/2023/03'
    cover_path = ''
    gallery_paths = []

    for idx, fn in enumerate(cdn_filenames):
        url = f'{base}/{fn}'
        data = _fetch(url)
        if data:
            w = _jpg_to_webp(data)
            if w:
                path = _save(w, f'{prefix}-detail-gallery-{len(gallery_paths)+1}')
                gallery_paths.append(path)
                if idx == 0:
                    cover_path = path

    return cover_path, gallery_paths

def make_body(model):
    """body: 文档下载链接"""
    return (
        f'<p>详细规格参数请查看产品规格书。</p>'
        f'<p><ul>'
        f'<li><a href="https://cn.dengtec.com/data/datasheet/{model}.dxf" target="_blank" rel="noopener">规格书 - DXF</a></li>'
        f'<li><a href="https://cn.dengtec.com/data/datasheet/{model}-CN.pdf" target="_blank" rel="noopener">规格书 - PDF</a></li>'
        f'<li><a href="https://cn.dengtec.com/data/datasheet/{model}.stp" target="_blank" rel="noopener">规格书 - STP</a></li>'
        f'</ul></p>'
    )

# 3 个新产品定义: (model, CDN图片文件名列表)
PRODUCTS = [
    ('TC03', ['TC03-T-1.jpg', 'TC03-T-2.jpg', 'TC03-T-3.jpg', 'TC03-T-4.jpg']),
    ('TC10', ['TC10-T-1.jpg', 'TC10-T-3.jpg', 'TC10-T-2.jpg', 'TC10-T-4-1.jpg']),
    ('TC25', ['TC25-T-1-1.jpg', 'TC25-T-4.jpg', 'TC25-T-2.jpg', 'TC25-T-5.jpg']),
]

def main():
    with open(FILEPATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    print(f'Existing: {len(data)} products')
    last_id = max(p['id'] for p in data)

    for idx, (model, cdn_fns) in enumerate(PRODUCTS):
        last_id += 1
        slug = model.lower()
        prefix = f'cable-connector-{slug}'

        cover_path, gallery_paths = download_images(cdn_fns, prefix)
        print(f'[{idx+1}/3] {model}  cover={"OK" if cover_path else "MISS"}  gallery={len(gallery_paths)}')

        product = {
            'id': last_id,
            'title': model,
            'slug': slug,
            'cover': cover_path or f'/assets/uploads/cable-connector-cover-{slug}.webp',
            'date': '2026-06-22',
            'name': '',
            'category': '线材',
            'description': '',
            'tags_visible': True,
            'tags': '',
            'price': '',
            'body': make_body(model),
            'rte_clicked_editor_idx': '',
            'detail_gallery': {
                'visible': True,
                'images': [{'url': p} for p in gallery_paths] if gallery_paths else [
                    {'url': f'/assets/uploads/cable-connector-{slug}-gallery-1.webp'}
                ]
            },
            'style_bg-color': '',
            'modules': [
                {'type': 'item_data', 'order': 1, 'variant': 'default', 'data': {}}
            ],
        }
        data.append(product)

    with open(FILEPATH, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, indent=2, width=1000)
    print(f'\nWritten: {FILEPATH}')

    with open(FILEPATH, 'r', encoding='utf-8') as f:
        verify = yaml.safe_load(f)
    print(f'Verified: {len(verify)} products')
    for p in verify:
        print(f'  id={p["id"]} {p["title"]}')

if __name__ == '__main__':
    main()
