"""
创建 SL12-SL16 射灯产品 + 下载 CDN 图片
参考产品: SL11 (id=1)
生产站详情页只有图片+文档链接, 无文字规格参数
"""
import yaml, os, sys, time, hashlib, random, urllib.request, urllib.parse, io
from datetime import datetime
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS = os.path.join(ROOT, 'sites', '6', 'assets', 'uploads')
FILEPATH = os.path.join(ROOT, 'sites', '6', 'lang', 'zh-CN', 'data', 'spot-light.yaml')
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

def download_cover(urls, prefix):
    """下载封面图, 返回路径或空"""
    for url in urls:
        data = _fetch(url)
        if data:
            w = _jpg_to_webp(data)
            if w:
                return _save(w, prefix)
    return ''

def download_gallery(urls, prefix, count=4):
    """下载详情图, 返回路径列表"""
    paths = []
    for url in urls:
        if len(paths) >= count:
            break
        data = _fetch(url)
        if data:
            w = _jpg_to_webp(data)
            if w:
                paths.append(_save(w, f'{prefix}-gallery-{len(paths)+1}'))
    return paths


# ===== 产品定义 =====
# 每个产品: (model, cdn_dir, cover_filenames, gallery_filenames)
# CDN 图片来自生产站详情页

PRODUCTS_DEF = [
    # SL12: CDN 2023/02, 白底图-1 系列, SP02 系列
    ('SL12', '2023/02', ['白底图-1.jpg'],
     ['白底图-1.jpg', 'SP02-03.jpg', 'SP02-06.jpg', 'SP02-07.jpg',
      'SP02-05.jpg', 'SP02-04.jpg', 'SP02-08.jpg', 'SP02-02.jpg']),

    # SL13: CDN 2017/06, 白底图-2, SP03 系列
    ('SL13', '2017/06', ['白底图-2.jpg'],
     ['白底图-2.jpg', 'SP03-13-e1676528765483.jpg', 'SP03-09.jpg', 'SP03-04.jpg',
      'SP03-03.jpg', 'SP03-06.jpg', 'SP03-05.jpg', 'SP03-02.jpg', 'SP03-07.jpg']),

    # SL14: CDN 2017/06, 白底图-1, SP04 系列
    ('SL14', '2017/06', ['白底图-1.jpg'],
     ['白底图-1.jpg', 'SP04-10.jpg', 'SP04-09.jpg', 'SP04-08.jpg',
      'SP04-07.jpg', 'SP04-05.jpg', 'SP04-04.jpg', 'SP04-02.jpg']),

    # SL15: CDN 2017/06, 白底图, SP05 系列
    ('SL15', '2017/06', ['白底图.jpg'],
     ['白底图.jpg', 'SP05-03.jpg', 'SP05-02.jpg', 'SP05-01.jpg',
      'SP05-10.jpg', 'SP05-09.jpg', 'SP05-08.jpg', 'SP05-06.jpg', 'SP05-05.jpg']),

    # SL16: CDN 2023/03, SP07 系列
    ('SL16', '2023/03', ['SP07-01.jpg'],
     ['SP07-01.jpg', 'SP07-02.jpg', 'SP07-03.jpg', 'SP07-04.jpg',
      'SP07-06.jpg', 'SP07-07.jpg', 'SP07-08.jpg']),
]


def make_body(model):
    """生成 body HTML: 文档下载链接 (唯一跨产品一致的内容)"""
    return (
        f'<p>详细规格参数请查看产品规格书。</p>'
        f'<p><ul>'
        f'<li><a href="https://cn.dengtec.com/data/datasheet/{model}.dxf" target="_blank" rel="noopener">规格书 - DXF</a></li>'
        f'<li><a href="https://cn.dengtec.com/data/datasheet/{model}-CN.pdf" target="_blank" rel="noopener">规格书 - PDF</a></li>'
        f'<li><a href="https://cn.dengtec.com/data/datasheet/{model}.stp" target="_blank" rel="noopener">规格书 - STP</a></li>'
        f'</ul></p>'
    )


def main():
    with open(FILEPATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    print(f'现有产品数: {len(data)}')
    last_id = max(p['id'] for p in data)
    print(f'现有最大 ID: {last_id}')

    for idx, (model, cdn_dir, cover_fns, gal_fns) in enumerate(PRODUCTS_DEF):
        last_id += 1
        slug = model.lower()
        prefix = f'spot-light-{slug}'
        cdn_base = f'https://cdn.dengtec.com/cnw/{cdn_dir}'

        # 构建 URL, 中文字符需 URL 编码
        def make_url(fn):
            encoded = urllib.parse.quote(fn)
            return f'{cdn_base}/{encoded}'

        # 下载封面
        cover_urls = [make_url(f) for f in cover_fns]
        cover_path = download_cover(cover_urls, f'{prefix}-cover')
        if not cover_path:
            cover_urls2 = [make_url(f) for f in gal_fns[:3]]
            cover_path = download_cover(cover_urls2, f'{prefix}-cover')

        # 下载详情图
        gal_urls = [make_url(f) for f in gal_fns]
        gallery_paths = download_gallery(gal_urls, prefix, count=6)

        print(f'\n[{idx+1}/5] {model}')
        print(f'  cover: {"OK" if cover_path else "FAILED"}')
        print(f'  gallery: {len(gallery_paths)} images')

        product = {
            'id': last_id,
            'title': model,
            'slug': slug,
            'cover': cover_path or f'/assets/uploads/spot-light-cover-{slug}.webp',
            'date': '2026-06-22',
            'name': '',
            'category': '射灯',
            'description': '',
            'tags_visible': True,
            'tags': '',
            'price': '',
            'body': make_body(model),
            'rte_clicked_editor_idx': '',
            'detail_gallery': {
                'visible': True,
                'images': [{'url': p} for p in gallery_paths] if gallery_paths else [
                    {'url': f'/assets/uploads/spot-light-{slug}-gallery-1.webp'}
                ]
            },
            'style_bg-color': '',
            'modules': [
                {'type': 'item_data', 'order': 1, 'variant': 'default', 'data': {}}
            ],
        }
        data.append(product)

    # 写入
    with open(FILEPATH, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, indent=2, width=1000)
    print(f'\n写入: {FILEPATH}')

    # 验证
    with open(FILEPATH, 'r', encoding='utf-8') as f:
        verify = yaml.safe_load(f)
    print(f'验证: {len(verify)} 个产品')
    for p in verify:
        print(f'  id={p["id"]} {p["title"]}')


if __name__ == '__main__':
    main()
