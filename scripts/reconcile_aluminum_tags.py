"""
用统一的自动标签逻辑（app.core.tagging）重算铝型材所有产品的 tags 并写回三语言 YAML。

背景：铝型材产品早已带结构化 detail_specs（宽度/高度/散光距离/灯板宽度），
但历史 tags 是最初导入脚本一次性写死的，且 AP-001（zh-CN）被手改成了精确值、维度残缺，
和其余 18 个不一致。本脚本按当前 tagging.py 的区间分桶口径统一重算，消除脏数据。

行为：
- 对每个产品调 generated_technical_tags(item) 得到区间桶标签（width-1020 等），写回 tags；
- 打上 tags_auto=True，表示归自动管理（之后后台保存若手改会置 False 锁定）；
- 只改 tags / tags_auto 两个字段，其它内容（body、detail_specs、图库等）原样保留；
- 三个语言版本 zh-CN / en / zh-TW 一并处理。

一次性脚本，跑完即可删。运行后需重建站点（build-site）使前台筛选栏刷新。
"""
import os
import sys
import yaml

# 让脚本能 import app.core.tagging（项目根目录加入 sys.path）
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from app.core.tagging import generated_technical_tags  # noqa: E402

LANGS = ('zh-CN', 'en', 'zh-TW')


def _yaml_path(lang):
    return os.path.join(ROOT, 'sites', '6', 'lang', lang, 'data', 'aluminum-profile.yaml')


def reconcile(lang):
    path = _yaml_path(lang)
    if not os.path.exists(path):
        print(f'[跳过] {lang}: 文件不存在 {path}')
        return
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    if not isinstance(data, list):
        print(f'[跳过] {lang}: 顶层不是列表')
        return

    changed = 0
    for item in data:
        if not isinstance(item, dict):
            continue
        new_tags = generated_technical_tags(item)
        if not new_tags:
            # 没有可识别的结构化规格 → 不动，避免把好的手填清空
            continue
        old_tags = item.get('tags')
        if old_tags != new_tags or item.get('tags_auto') is not True:
            item['tags'] = new_tags
            item['tags_auto'] = True
            changed += 1

    with open(path, 'w', encoding='utf-8') as f:
        # width=1000 与最初导入脚本一致，避免长 HTML body 被折行导致大面积无关 diff
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, indent=2, width=1000)
    print(f'[完成] {lang}: 共 {len(data)} 条，更新 {changed} 条 tags')


def main():
    for lang in LANGS:
        reconcile(lang)


if __name__ == '__main__':
    main()
