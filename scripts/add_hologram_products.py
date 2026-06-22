"""
创建 19 个全息投影产品 (HLG27A640 ~ HLG99A1184) + 下载 CDN 图片
参考产品: HLG115A1532 (id=1)
所有规格参数来自 cn.dengtec.com 各产品详情页
"""
import yaml, os, hashlib, random, urllib.request, io
from datetime import datetime
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS = os.path.join(ROOT, 'sites', '6', 'assets', 'uploads')
FILEPATH = os.path.join(ROOT, 'sites', '6', 'lang', 'zh-CN', 'data', 'holograms.yaml')
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

def download_images(model, prefix):
    """下载封面(图1)和详情图(图1-4), 返回 (cover_path, gallery_paths)"""
    base = f'https://cdn.dengtec.com/cnw/2023/03/{model}'
    cover_path = ''
    gallery_paths = []

    # 封面 = 图1
    for fn in [f'{base}-1.jpg', f'{base}.jpg']:
        data = _fetch(fn)
        if data:
            w = _jpg_to_webp(data)
            if w:
                cover_path = _save(w, f'{prefix}-cover')
                break

    # 详情图: 1-4
    for idx in range(1, 5):
        url = f'{base}-{idx}.jpg'
        data = _fetch(url)
        if data:
            w = _jpg_to_webp(data)
            if w:
                gallery_paths.append(_save(w, f'{prefix}-gallery-{idx}'))

    # 如果封面没下载到, 用第一张详情图
    if not cover_path and gallery_paths:
        cover_path = gallery_paths[0]

    return cover_path, gallery_paths


def _yn(val):
    return 'Y' if val else 'N'

def _tag(val, prefix):
    return f'{prefix}-{"y" if val else "n"}'


def make_body(model, diameter, resolution, led_count, control,
              wireless, remote, sync, bt, timer, power, tf, formats):
    """生成与参考产品一致的 HTML body (三个表格)"""
    parts = []
    # 表1: 直径/分辨率/灯珠数/控制
    parts.append('<table data-rte-border="1" data-rte-widths="1">')
    parts.append('<colgroup><col style="width:33%"><col style="width:33%"><col style="width:33%"></colgroup>')
    parts.append('<tbody>')
    parts.append(f'<tr><td style="width:33%;"><p>直径</p></td><td style="width:33%;"><p>显示直径</p></td><td style="width:33%;"><p>{diameter}</p></td></tr>')
    parts.append(f'<tr><td style="width:33%;"><p>分辨率</p></td><td style="width:33%;"><p>像素点</p></td><td style="width:33%;"><p>{resolution}</p></td></tr>')
    parts.append(f'<tr><td style="width:33%;"><p>灯珠数</p></td><td style="width:33%;"><p>直径方向</p></td><td style="width:33%;"><p>{led_count}</p></td></tr>')
    parts.append(f'<tr><td style="width:33%;"><p>控制</p></td><td style="width:33%;"><p>控制平台</p></td><td style="width:33%;"><p>{control}</p></td></tr>')
    parts.append('</tbody></table>')

    # 表2: 无线投屏/遥控/同步/功率
    parts.append('<table data-rte-border="1" data-rte-widths="1">')
    parts.append('<colgroup><col style="width:33%"><col style="width:33%"><col style="width:33%"></colgroup>')
    parts.append('<tbody>')
    parts.append(f'<tr><td style="width:33%;"><p>无线投屏</p></td><td style="width:33%;"><p>通过无线投屏发送内容</p></td><td style="width:33%;"><p>{_yn(wireless)}</p></td></tr>')
    parts.append(f'<tr><td style="width:33%;"><p>遥控</p></td><td style="width:33%;"><p>可以通过遥控器控制</p></td><td style="width:33%;"><p>{_yn(remote)}</p></td></tr>')
    parts.append(f'<tr><td style="width:33%;"><p>同步</p></td><td style="width:33%;"><p>多个设备</p></td><td style="width:33%;"><p>{_yn(sync)}</p></td></tr>')
    parts.append(f'<tr><td style="width:33%;"><p>功率</p></td><td style="width:33%;"><p>电压和功率</p></td><td style="width:33%;"><p>{power}</p></td></tr>')
    parts.append('</tbody></table>')

    # 表3: TF卡/文件格式/蓝牙音频/定时
    parts.append('<table data-rte-border="1" data-rte-widths="1">')
    parts.append('<colgroup><col style="width:33%"><col style="width:33%"><col style="width:33%"></colgroup>')
    parts.append('<tbody>')
    parts.append(f'<tr><td style="width:33%;"><p>TF 卡</p></td><td style="width:33%;"><p>TF 容量</p></td><td style="width:33%;"><p>{tf}</p></td></tr>')
    parts.append(f'<tr><td style="width:33%;"><p>文件格式</p></td><td style="width:33%;"><p>支持的文件格式</p></td><td style="width:33%;"><p>{formats}</p></td></tr>')
    parts.append(f'<tr><td style="width:33%;"><p>蓝牙音频</p></td><td style="width:33%;"><p>通过蓝牙播放音频</p></td><td style="width:33%;"><p>{_yn(bt)}</p></td></tr>')
    parts.append(f'<tr><td style="width:33%;"><p>定时</p></td><td style="width:33%;"><p>定时播放</p></td><td style="width:33%;"><p>{_yn(timer)}</p></td></tr>')
    parts.append('</tbody></table>')
    # 文档链接
    parts.append(f'<p><ul><li><a href="https://cn.dengtec.com/data/datasheet/{model}-CN.pdf" target="_blank" rel="noopener">DataSheet - PDF</a></li></ul></p>')
    return ''.join(parts)


def make_desc(diameter, wireless, remote, sync, bt):
    """生成产品描述"""
    feats = []
    if sync: feats.append('可多台同步')
    if bt: feats.append('带蓝牙音频')
    if wireless: feats.append('可无线投屏')
    if remote: feats.append('可遥控')
    desc = f'{diameter} 全息投影'
    if feats:
        desc += ', ' + ', '.join(feats)
    return desc


def make_tags(diameter_cm, wireless, remote, sync, bt):
    """生成标签列表"""
    return [
        _tag(bt, 'bt'),
        f'd{diameter_cm}',
        _tag(remote, 'remote'),
        _tag(sync, 'sync'),
        _tag(wireless, 'wirelessdisplay'),
    ]


# ===== 19 个产品定义 (所有数据来自生产站详情页) =====
# (model, diameter_str, diameter_cm, resolution, led_count, control,
#  wireless, remote, sync, bt, timer, power, tf, formats)

PRODUCTS = [
    ('HLG150A2880', 'Φ1500mm', 150, '2048*2880', '2880', 'Android / Computer',
     True, True, True, True, False, '320W', '16Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG180A2512', 'Φ1800mm', 180, '2048*2512', '2512', 'Android / Computer',
     True, True, True, True, False, '400W', '16Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG27A640', 'Φ250mm', 25, '1600*224', '224', 'Android / Computer',
     False, True, True, True, False, '10-15W', '8Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG40A640', 'Φ410mm', 41, '640*640', '224', 'Computer',
     False, True, False, False, False, '10-15W', '8Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG40B640', 'Φ410mm', 41, '640*640', '224', 'Android / Computer',
     False, True, False, False, False, '10-15W', '8Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG40C800', 'Φ410mm', 41, '800*800', '224', 'Android / Computer',
     False, True, False, False, False, '10-15W', '8Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG42A640', 'Φ420mm', 42, '1024*640', '244', 'Android / Computer',
     False, True, True, False, False, '18W', '16Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG42B800', 'Φ420mm', 42, '1024*800', '244', 'Android / Computer',
     False, True, True, False, True, '20W', '16Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG45A532', 'Φ450mm', 45, '2000*532', '266', 'Android / Computer',
     False, True, True, True, False, '24W', '16Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG45A800', 'Φ410mm', 41, '800*800', '224', 'Android / Computer',
     False, True, False, False, False, '10-15W', '8Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG45B510', 'Φ450mm', 45, '1400*510', '510', 'Android / Computer',
     False, False, False, False, False, '30W', '8Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG50A1152', 'Φ500mm', 50, '2000*1152', '576', 'Android / Computer',
     True, True, True, True, False, '48W', '16Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG52A624', 'Φ520mm', 52, '2000*624', '624', 'Android / Computer',
     True, True, False, True, False, '72W', '32Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG56A672', 'Φ560mm', 56, '2000*672', '672', 'Android / Computer',
     True, True, True, True, False, '72W', '8Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG60A720', 'Φ600mm', 60, '2000*720', '720', 'Android / Computer',
     True, True, False, True, True, '72W', '32Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG65A928', 'Φ650mm', 65, '2000*982', '928', 'Android / Computer',
     True, True, True, True, True, '96W', '8Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG78A928', 'Φ780mm', 78, '2000*982', '928', 'Android / Computer',
     True, True, True, True, True, '96W', '8Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG85A1532', 'Φ850mm', 85, '2000*1532', '1532', 'Android / Computer',
     True, False, False, False, False, '80-150W', '16Gb', 'MP4 / AVI / JPG / PNG'),
    ('HLG99A1184', 'Φ990mm', 99, '2000*1184', '1184', 'Android / Computer',
     True, True, True, True, True, '120W', '8Gb', 'MP4 / AVI / JPG / PNG'),
]


def main():
    with open(FILEPATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    print(f'Existing products: {len(data)}')
    last_id = max(p['id'] for p in data)
    print(f'Existing max ID: {last_id}')
    print()

    for idx, spec in enumerate(PRODUCTS):
        (model, diameter, diameter_cm, resolution, led_count, control,
         wireless, remote, sync, bt, timer, power, tf, formats) = spec
        last_id += 1
        slug = model.lower()
        prefix = f'holograms-{slug}'

        # 下载图片
        cover_path, gallery_paths = download_images(model, prefix)
        print(f'[{idx+1:2d}/19] {model:15s}  cover={"OK" if cover_path else "MISS"}  gallery={len(gallery_paths)}')

        product = {
            'id': last_id,
            'title': model,
            'slug': slug,
            'cover': cover_path or f'/assets/uploads/holograms-cover-{slug}.webp',
            'date': '2026-06-22',
            'name': '',
            'category': '全息投影',
            'description': make_desc(diameter, wireless, remote, sync, bt),
            'tags_visible': True,
            'tags': make_tags(diameter_cm, wireless, remote, sync, bt),
            'price': '',
            'body': make_body(model, diameter, resolution, led_count, control,
                              wireless, remote, sync, bt, timer, power, tf, formats),
            'rte_clicked_editor_idx': '',
            'detail_gallery': {
                'visible': True,
                'images': [{'url': p} for p in gallery_paths] if gallery_paths else [
                    {'url': f'/assets/uploads/holograms-{slug}-gallery-1.webp'}
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
    print(f'\nWritten: {FILEPATH}')

    # 验证
    with open(FILEPATH, 'r', encoding='utf-8') as f:
        verify = yaml.safe_load(f)
    print(f'Verified: {len(verify)} products')
    for p in verify:
        print(f'  id={p["id"]:2d}  {p["title"]}')


if __name__ == '__main__':
    main()
