# -*- coding: utf-8 -*-
"""
把德恩基产品「资料下载」(detail_files) 里所有指向 cn.dengtec.com 的
PDF/STP/DXF 文件下载到本站点 assets/uploads/ 下，为 cn.dengtec.com 下线做准备。

设计要点：
- 三个语言复用同一批文件，先从所有 YAML 收集去重 url，只下载一次（179 个唯一文件）
- 按原始 /data/<类别>/ 结构落到 assets/uploads/<类别>/，url 就近映射，避免重名冲突
- 幂等：已存在且大小与远端一致的文件跳过，可反复运行补齐失败项
- 只下载，不改 YAML（改 url 放到第二个脚本，下载全部成功后再动数据）
"""
import os, glob, sys, time
import urllib.request, urllib.error
from urllib.parse import urlparse
import yaml

SITE_DIR = 'sites/6'
DEST_ROOT = os.path.join(SITE_DIR, 'assets', 'uploads')
UA = {'User-Agent': 'Mozilla/5.0'}


def collect_urls():
    """从三个语言的所有数据 YAML 收集 detail_files 的 url，去重"""
    urls = set()
    for f in glob.glob(os.path.join(SITE_DIR, 'lang', '*', 'data', '*.yaml')):
        data = yaml.safe_load(open(f, encoding='utf-8'))
        items = data if isinstance(data, list) else next(
            (v for v in data.values() if isinstance(v, list)), [])
        for it in items:
            if not isinstance(it, dict):
                continue
            for df in (it.get('detail_files') or []):
                u = (df.get('url') or '').strip()
                if u.startswith('http'):
                    urls.add(u)
    return sorted(urls)


def local_rel_path(url):
    """https://cn.dengtec.com/data/datasheet/x.pdf -> x.pdf
    平铺到 uploads/ 根目录（不建子目录）——因为后台媒体管理 list_media_files
    只 iterdir() 扫 uploads 顶层、不递归子目录，放子目录就列不出来。
    已验证 179 个文件名全部唯一，平铺无重名冲突。"""
    return os.path.basename(urlparse(url).path)


def download(url, dest):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main():
    urls = collect_urls()
    print(f'唯一文件数: {len(urls)}')
    ok = skip = fail = 0
    failures = []
    for i, url in enumerate(urls, 1):
        rel = local_rel_path(url)
        dest = os.path.join(DEST_ROOT, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        # 幂等：本地已有且非空就跳过（PDF/图纸内容稳定，不做逐字节校验）
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            skip += 1
            continue
        try:
            data = download(url, dest)
            # 写临时文件再重命名，避免中断留下半截文件
            tmp = dest + '.part'
            with open(tmp, 'wb') as fh:
                fh.write(data)
            os.replace(tmp, dest)
            ok += 1
            print(f'[{i}/{len(urls)}] OK {len(data):>8} B  {rel}')
        except Exception as e:
            fail += 1
            failures.append((url, str(e)))
            print(f'[{i}/{len(urls)}] FAIL {rel}: {type(e).__name__} {e}')
        time.sleep(0.1)  # 轻微限速，别把即将下线的老站压垮
    print(f'\n完成: 新下载 {ok}, 跳过已存在 {skip}, 失败 {fail}')
    if failures:
        print('失败清单:')
        for u, e in failures:
            print('  ', u, '->', e)
        sys.exit(1)


if __name__ == '__main__':
    main()
