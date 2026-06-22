"""
创建 PT12/PT13/PT14 导电槽产品 + 下载 CDN 图片
参考产品: PT11 (id=1)
所有规格参数来自 cn.dengtec.com 各产品详情页
"""
import yaml, os, hashlib, random, urllib.request, io
from datetime import datetime
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS = os.path.join(ROOT, 'sites', '6', 'assets', 'uploads')
FILEPATH = os.path.join(ROOT, 'sites', '6', 'lang', 'zh-CN', 'data', 'powerptrack.yaml')
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
    """封面=第一张, 全部作为 gallery"""
    base = 'https://cdn.dengtec.com/cnw/2023/03'
    cover_path = ''
    gallery_paths = []
    for idx, fn in enumerate(cdn_filenames):
        data = _fetch(f'{base}/{fn}')
        if data:
            w = _jpg_to_webp(data)
            if w:
                path = _save(w, f'{prefix}-detail-gallery-{len(gallery_paths)+1}')
                gallery_paths.append(path)
                if idx == 0:
                    cover_path = path
    return cover_path, gallery_paths

def make_body(model, current, length, color, voltage, install, plug, desc=''):
    """生成与 PT11 一致的 HTML body (两个表格 + 文档链接)"""
    desc_p = f'<p>{desc}</p>' if desc else ''
    return (
        f'{desc_p}'
        f'<table data-rte-border="1" data-rte-widths="1">'
        f'<colgroup><col style="width:33%"><col style="width:33%"><col style="width:33%"></colgroup>'
        f'<tbody>'
        f'<tr><td style="width:33%;"><p>最大电流</p></td><td style="width:33%;"><p>通过的最大电流</p></td><td style="width:33%;"><p>{current}</p></td></tr>'
        f'<tr><td style="width:33%;"><p>正常长度</p></td><td style="width:33%;"><p>常规产品最长3m.</p></td><td style="width:33%;"><p>{length}</p></td></tr>'
        f'<tr><td style="width:33%;"><p>颜色</p></td><td style="width:33%;"><p>顶部颜色</p></td><td style="width:33%;"><p>{color}</p></td></tr>'
        f'</tbody></table>'
        f'<table data-rte-border="1" data-rte-widths="1">'
        f'<colgroup><col style="width:33%"><col style="width:33%"><col style="width:33%"></colgroup>'
        f'<tbody>'
        f'<tr><td style="width:33%;"><p>最大电压</p></td><td style="width:33%;"><p>不能用＞220v/110v</p></td><td style="width:33%;"><p>{voltage}</p></td></tr>'
        f'<tr><td style="width:33%;"><p>安装方式</p></td><td style="width:33%;"><p>选择安装方式</p></td><td style="width:33%;"><p>{install}</p></td></tr>'
        f'<tr><td style="width:33%;"><p>插头</p></td><td style="width:33%;"><p>插头角度</p></td><td style="width:33%;"><p>{plug}</p></td></tr>'
        f'</tbody></table>'
        f'<p><ul>'
        f'<li><a href="https://cn.dengtec.com/data/datasheet/{model}.dxf" target="_blank" rel="noopener">DRAWING - DXF</a></li>'
        f'<li><a href="https://cn.dengtec.com/data/datasheet/{model}-CN.pdf" target="_blank" rel="noopener">DataSheet - PDF</a></li>'
        f'<li><a href="https://cn.dengtec.com/data/datasheet/{model}.stp" target="_blank" rel="noopener">DataSheet - STP</a></li>'
        f'</ul></p>'
    )

# 3 个新产品 (model, CDN图片, 规格参数)
# 所有数据来自生产站详情页
PRODUCTS = [
    ('PT12', ['PT12-P1.jpg', 'PT12-P2.jpg', 'PT12-P3.jpg', 'PT12-P4.jpg'],
     '10A', '2 M', '白, 黑', '36V', '磁铁', '0°', ''),
    ('PT13', ['PT13-P1.jpg', 'PT13-P2.jpg', 'PT13-P3.jpg', 'PT13-P4.jpg'],
     '10A', '2 M', '白, 黑', '36V', '螺丝,胶带', '0°, 90°', ''),
    ('PT14', ['PT14-0.jpg', 'PT14-2.jpg', 'PT14-4.jpg', 'PT14-5.jpg'],
     '10A', '3 M', '白, 黑', '36V', '磁铁', '0°', '便捷安装,精细小巧'),
]

def main():
    with open(FILEPATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    print(f'Existing: {len(data)} products')
    last_id = max(p['id'] for p in data)

    for idx, (model, cdn_fns, current, length, color, voltage, install, plug, desc) in enumerate(PRODUCTS):
        last_id += 1
        slug = model.lower()
        prefix = f'powerptrack-{slug}'

        cover_path, gallery_paths = download_images(cdn_fns, prefix)
        print(f'[{idx+1}/3] {model}  cover={"OK" if cover_path else "MISS"}  gallery={len(gallery_paths)}')

        product = {
            'id': last_id,
            'title': model,
            'slug': slug,
            'cover': cover_path or f'/assets/uploads/powerptrack-cover-{slug}.webp',
            'date': '2026-06-22',
            'name': '',
            'category': '导电槽',
            'description': desc,
            'tags_visible': False,
            'tags': '',
            'price': '',
            'body': make_body(model, current, length, color, voltage, install, plug, desc),
            'rte_clicked_editor_idx': '',
            'detail_gallery': {
                'visible': True,
                'images': [{'url': p} for p in gallery_paths] if gallery_paths else [
                    {'url': f'/assets/uploads/powerptrack-{slug}-gallery-1.webp'}
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
