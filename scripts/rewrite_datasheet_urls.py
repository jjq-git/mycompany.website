# -*- coding: utf-8 -*-
"""
第二步：把三个语言所有产品 YAML 里 detail_files 的 url 从
https://cn.dengtec.com/data/<...>/<文件名> 改成本地 /assets/uploads/<文件名>，
同时清理源站 404（无法本地化）的死链条目。

三类处理（对 en / zh-CN / zh-TW 三个语言一致执行，因三语言复用同一批 url）：
1. 已成功下载到本地的 url → 改成 /assets/uploads/<basename>
2. 源站 404 的 12 个铝型材 PDF → 从该产品 detail_files 移除该条（保留 dxf/stp）
3. 源站 404 的 3 个 TC 连接器整套资料 → 该产品 detail_files 清空

用 yaml 加载→处理→dump，dump 参数与系统 write_yaml 完全一致
（safe_dump, allow_unicode=True, sort_keys=False, indent=2），把格式落差降到最小。
"""
import os, glob
from urllib.parse import urlparse
import yaml

UPLOADS_DIR = 'sites/6/assets/uploads'

# 源站 404、无法本地化的死链 basename（下载脚本实测得出）
DEAD = {
    'AP-005-U-W39-H8.9-D4-L26.4-CN.pdf', 'AP-006-U-W23-H9.4-D6.4-L16-CN.pdf',
    'AP-007-U-W18.1-H15.7-D11-L12-CN.pdf', 'AP-008-U-W17.5-H9.2-D6.6-L12.7-CN.pdf',
    'AP-009-V-W26.8-H17.1-D8.7-L11-CN.pdf', 'AP-010-U-W12.4-H7.8-D4.5-L8.8-CN.pdf',
    'AP-011-U-W16.5-H11.5-D8.3-L9.6-CN.pdf', 'AP-012-U-W18-H15.4-D11.1-L12.6-CN.pdf',
    'AP-013-U-W13.1-H8.1-D5-L9.8-CN.pdf', 'AP-014-U-W20.5-H10.8-D6.8-L14-CN.pdf',
    'AP-015-L-W120-H50-D50-L5-CN.pdf', 'AP-018-U-W17.8-H10.5-D8.2-L12.6-CN.pdf',
    'TC03-CN.pdf', 'TC03.dxf', 'TC03.stp', 'TC10-CN.pdf', 'TC10.dxf', 'TC10.stp',
    'TC25-CN.pdf', 'TC25.dxf', 'TC25.stp',
}


def basename_of(url):
    return os.path.basename(urlparse((url or '').strip()).path)


def process_item(it, stat):
    """处理单个产品条目的 detail_files，就地修改，累加统计"""
    if not isinstance(it, dict):
        return
    dfs = it.get('detail_files')
    if not isinstance(dfs, list):
        return
    new_dfs = []
    for df in dfs:
        if not isinstance(df, dict):
            new_dfs.append(df)
            continue
        url = (df.get('url') or '').strip()
        base = basename_of(url)
        if url.startswith('http') and base in DEAD:
            stat['removed'] += 1          # 死链条目：丢弃
            continue
        if url.startswith('http://') or url.startswith('https://'):
            local = os.path.join(UPLOADS_DIR, base)
            if not os.path.exists(local):
                # 既不在 DEAD 名单又没下载成功 —— 异常，报错中止（绝不留死链）
                raise RuntimeError(f'意外缺失本地文件: {base} <- {url}')
            df['url'] = f'/assets/uploads/{base}'
            stat['rewritten'] += 1
        new_dfs.append(df)
    it['detail_files'] = new_dfs


def main():
    files = sorted(glob.glob('sites/6/lang/*/data/*.yaml'))
    stat = {'rewritten': 0, 'removed': 0}
    touched = []
    for f in files:
        data = yaml.safe_load(open(f, encoding='utf-8'))
        items = data if isinstance(data, list) else next(
            (v for v in data.values() if isinstance(v, list)), [])
        before = (stat['rewritten'], stat['removed'])
        for it in items:
            process_item(it, stat)
        if (stat['rewritten'], stat['removed']) != before:
            # 用系统 write_yaml 同款参数写回，格式对齐
            with open(f, 'w', encoding='utf-8') as fh:
                yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False, indent=2)
            touched.append(f)

    print(f'完成：改写 url {stat["rewritten"]} 处，移除死链条目 {stat["removed"]} 处，'
          f'涉及 {len(touched)} 个文件')
    for f in touched:
        print('  ', f)


if __name__ == '__main__':
    main()
