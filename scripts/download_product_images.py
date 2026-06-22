"""
从 CDN 下载 LED 灯条和铝槽产品图片 → 转 WebP → 保存 → 更新 YAML
来源: cdn.dengtec.com/cnw/2020/08/ (LED) / cdn.dengtec.com/cnw/2020/09/ (铝槽)
"""
import os, sys, time, hashlib, random, urllib.request, urllib.error
from datetime import datetime
from PIL import Image
import io
import yaml

# ---- 项目根目录 ----
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS = os.path.join(ROOT, 'sites', '6', 'assets', 'uploads')
LED_YAML = os.path.join(ROOT, 'sites', '6', 'lang', 'zh-CN', 'data', 'led-strip.yaml')
ALUM_YAML = os.path.join(ROOT, 'sites', '6', 'lang', 'zh-CN', 'data', 'aluminum-profile.yaml')

os.makedirs(UPLOADS, exist_ok=True)

# ---- 工具函数 ----
def _ts_hex():
    """生成时间戳+随机hex, 用于文件名唯一标识"""
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    rnd = hashlib.md5(str(random.random()).encode()).hexdigest()[:8]
    return f'{ts}-{rnd}'

def _fetch(url, timeout=15):
    """下载 URL 内容, 返回 bytes 或 None"""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; DengtecImgBot/1.0)'
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        return None

def _jpg_to_webp(jpg_bytes, quality=82):
    """JPG bytes → WebP bytes"""
    try:
        img = Image.open(io.BytesIO(jpg_bytes))
        img = img.convert('RGB')
        buf = io.BytesIO()
        img.save(buf, format='WEBP', quality=quality)
        return buf.getvalue()
    except Exception:
        return None

def _save_webp(webp_bytes, prefix):
    """保存 WebP 到 uploads/, 返回相对路径"""
    name = f'{prefix}-{_ts_hex()}.webp'
    path = os.path.join(UPLOADS, name)
    with open(path, 'wb') as f:
        f.write(webp_bytes)
    return f'/assets/uploads/{name}'


# ===== LED 灯条图片下载 =====
LED_CDN = 'https://cdn.dengtec.com/cnw/2020/08'

# 14 个新产品 (id 8-21)
LED_MODELS = [
    'LS-12V-60-W10-5050S',
    'LS-12V-60-W6-5050S',
    'LS-12V-60-W8-2835',
    'LS-12V-60-W8-3528',
    'LS-12V-60C1-W8-5050S',
    'LS-12V-72-W6S-2835',
    'LS-12V-90-W20-WS2811',
    'LS-12V-90-W6S-2835',
    'LS-12V-90-W8-2835',
    'LS-12V-96-W5-2835',
    'LS-24V-120-W8-2835',
    'LS-24V-60C2-W8-5050S',
    'LS-5V-60-W10-WS2812',
    'LS-5V-90-W8-4020',
]

def _led_cover_urls(model):
    """LED 封面图候选 URL (按优先级)"""
    return [
        f'{LED_CDN}/{model}.jpg',
        f'{LED_CDN}/{model}-10x10.jpg',
    ]

def _led_gallery_urls(model, idx):
    """LED 详情图候选 URL, idx: 1=B, 2=C, 3=D, 4=额外"""
    lower = model.lower()
    maps = {
        1: [f'{LED_CDN}/{model}-webimg_B.jpg', f'{LED_CDN}/{lower}-webimg-B.jpg'],
        2: [f'{LED_CDN}/{model}-webimg_C.jpg'],
        3: [f'{LED_CDN}/{model}-webimg_D.jpg', f'{LED_CDN}/{model}-webimg_D-scaled.jpg'],
        4: [f'{LED_CDN}/{lower}-webimg-B2.jpg'],  # 部分产品有额外图
    }
    return maps.get(idx, [])


def process_led_products():
    """下载 LED 灯条图片并返回 cover + gallery 路径映射"""
    result = {}  # model → {cover: path, gallery: [path,...]}
    for i, model in enumerate(LED_MODELS):
        slug = model.lower().replace('.', '-')
        print(f'\n[{i+1}/14] {model}')
        item = {'cover': '', 'gallery': []}

        # 封面图
        for url in _led_cover_urls(model):
            data = _fetch(url)
            if data:
                w = _jpg_to_webp(data)
                if w:
                    path = _save_webp(w, f'led-strip-cover-{slug}')
                    item['cover'] = path
                    print(f'  cover: {url} → {path}')
                    break
        if not item['cover']:
            print(f'  cover: FAILED (all URLs)')

        # 详情图: 最多 4 张
        for gi in range(1, 5):
            for url in _led_gallery_urls(model, gi):
                data = _fetch(url)
                if data:
                    w = _jpg_to_webp(data)
                    if w:
                        path = _save_webp(w, f'led-strip-{slug}-gallery-{gi}')
                        item['gallery'].append(path)
                        print(f'  gallery-{gi}: {url} → {path}')
                        break
            if len(item['gallery']) < gi:
                print(f'  gallery-{gi}: SKIPPED (not found)')

        result[model] = item
    return result


# ===== 铝槽图片下载 =====
ALUM_CDN = 'https://cdn.dengtec.com/cnw/2020/09'

# 18 个新产品 (id 2-19)
ALUM_MODELS = [
    'AP-002-U-W24.8-H8-D5.5-L12',
    'AP-003-U-W22-H11.9-D8.9-L11',
    'AP-004-U-W16-H11.8-D9-L11.6',
    'AP-005-U-W39-H8.9-D4-L26.4',
    'AP-006-U-W23-H9.4-D6.4-L16',
    'AP-007-U-W18.1-H15.7-D11-L12',
    'AP-008-U-W17.5-H9.2-D6.6-L12.7',
    'AP-009-V-W26.8-H17.1-D8.7-L11',
    'AP-010-U-W12.4-H7.8-D4.5-L8.8',
    'AP-011-U-W16.5-H11.5-D8.3-L9.6',
    'AP-012-U-W18-H15.4-D11.1-L12.6',
    'AP-013-U-W13.1-H8.1-D5-L9.8',
    'AP-014-U-W20.5-H10.8-D6.8-L14',
    'AP-015-L-W120-H50-D50-L5',
    'AP-016-U-W16.6-H11.1-D8.5-L10.3',
    'AP-017-L-W16-H16-D8-L10.7',
    'AP-018-U-W17.8-H10.5-D8.2-L12.6',
    'AP-019-U-W7.2-H8.5-D0-L5.8',
]

def _alum_image_urls(model, suffix):
    """铝槽图片候选 URL"""
    urls = []
    # 先试带 -scaled 的
    if suffix != 'C':
        urls.append(f'{ALUM_CDN}/{model}-webimg_{suffix}-scaled.jpg')
    urls.append(f'{ALUM_CDN}/{model}-webimg_{suffix}.jpg')
    return urls


def process_alum_products():
    """下载铝槽图片并返回 cover + gallery 路径映射"""
    result = {}
    for i, model in enumerate(ALUM_MODELS):
        slug = model.lower().replace('.', '-')
        print(f'\n[{i+1}/18] {model}')
        item = {'cover': '', 'gallery': []}

        # 封面用 webimg_C
        for url in _alum_image_urls(model, 'C'):
            data = _fetch(url)
            if data:
                w = _jpg_to_webp(data)
                if w:
                    path = _save_webp(w, f'aluminum-profile-cover-{slug}')
                    item['cover'] = path
                    print(f'  cover(C): {url} → {path}')
                    break
        if not item['cover']:
            print(f'  cover: FAILED')

        # 详情图: A→gallery-1, B→gallery-2, C→gallery-3(复用cover做小图), D→gallery-4
        gal_map = {'A': 1, 'B': 2}
        for suffix, gidx in gal_map.items():
            for url in _alum_image_urls(model, suffix):
                data = _fetch(url)
                if data:
                    w = _jpg_to_webp(data)
                    if w:
                        path = _save_webp(w, f'aluminum-profile-{slug}-gallery-{gidx}')
                        item['gallery'].append(path)
                        print(f'  gallery-{gidx}({suffix}): {url} → {path}')
                        break
            if len(item['gallery']) < gidx:
                print(f'  gallery-{gidx}({suffix}): SKIPPED')

        # gallery-3: 用 webimg_C 的另一个变体
        if item['cover']:
            # 复用 cover 的 scaled 版本或直接复用
            cover_name = os.path.basename(item['cover'])
            item['gallery'].append(item['cover'])  # gallery-3 复用 cover
            print(f'  gallery-3: reuse cover')
        else:
            item['gallery'].append('')
            print(f'  gallery-3: SKIPPED (no cover)')

        # gallery-4: webimg_D
        for url in _alum_image_urls(model, 'D'):
            data = _fetch(url)
            if data:
                w = _jpg_to_webp(data)
                if w:
                    path = _save_webp(w, f'aluminum-profile-{slug}-gallery-4')
                    item['gallery'].append(path)
                    print(f'  gallery-4(D): {url} → {path}')
                    break
        if len(item['gallery']) < 4:
            item['gallery'].append('')
            print(f'  gallery-4: SKIPPED')

        result[model] = item
    return result


# ===== 更新 YAML =====
def _update_yaml(filepath, img_map, model_field='title'):
    """用下载的图片路径更新 YAML 中产品的 cover 和 detail_gallery"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    updated = 0
    for p in data:
        model = p.get(model_field, '')
        if model in img_map:
            imgs = img_map[model]
            if imgs['cover']:
                p['cover'] = imgs['cover']
                updated += 1
            # 更新 detail_gallery
            valid_gallery = [g for g in imgs['gallery'] if g]
            if valid_gallery:
                p['detail_gallery']['images'] = [{'url': g} for g in valid_gallery]

    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, indent=2, width=1000)
    print(f'  Updated {updated} products in {os.path.basename(filepath)}')


# ===== 主流程 =====
def main():
    print('=' * 60)
    print('Phase 1: LED 灯条图片下载 (14 products)')
    print('=' * 60)
    led_imgs = process_led_products()

    print('\n' + '=' * 60)
    print('Phase 2: 铝槽图片下载 (18 products)')
    print('=' * 60)
    alum_imgs = process_alum_products()

    print('\n' + '=' * 60)
    print('Phase 3: 更新 YAML 文件')
    print('=' * 60)
    _update_yaml(LED_YAML, led_imgs, 'title')
    _update_yaml(ALUM_YAML, alum_imgs, 'title')

    # 统计
    led_covers = sum(1 for v in led_imgs.values() if v['cover'])
    led_gals = sum(len([g for g in v['gallery'] if g]) for v in led_imgs.values())
    alum_covers = sum(1 for v in alum_imgs.values() if v['cover'])
    alum_gals = sum(len([g for g in v['gallery'] if g]) for v in alum_imgs.values())

    print(f'\n{"="*60}')
    print(f'完成!')
    print(f'  LED 封面: {led_covers}/14  详情图: {led_gals}')
    print(f'  铝槽 封面: {alum_covers}/18  详情图: {alum_gals}')
    print(f'  总计图片: {led_covers + led_gals + alum_covers + alum_gals}')
    print(f'{"="*60}')


if __name__ == '__main__':
    main()
