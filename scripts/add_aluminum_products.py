"""
从生产站列表页+详情页提取数据, 追加 18 个铝槽产品到 aluminum-profile.yaml
每个产品的规格参数来自 cn.dengtec.com 产品列表页和详情页
按参考产品 AP-001-U-W15.8-H6.8-D4-L12 的结构生成
"""
import yaml
import os

FILEPATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'sites', '6', 'lang', 'zh-CN', 'data', 'aluminum-profile.yaml')

# ---- Tag 计算 ----
def _tags(shape, width, height, diffdist, lswidth, application):
    """根据参数生成标签列表"""
    # 宽度范围
    if width < 10:
        wt = 'width-10'
    elif width < 20:
        wt = 'width-1020'
    elif width < 30:
        wt = 'width-2030'
    else:
        wt = 'width-30'
    # 高度范围
    if height < 10:
        ht = 'height-10'
    elif height < 20:
        ht = 'height-1020'
    else:
        ht = 'height-30'
    # 散光距离
    dt = 'diffusedis-10' if diffdist < 10 else ('diffusedis-30' if diffdist >= 30 else None)
    # 灯板宽度
    lt = 'lswidth-10' if lswidth <= 10 else 'lswidth-1020'

    tags = [f'application-{application}', f'shape-{shape}', wt, ht, lt]
    if dt:
        tags.insert(2, dt)  # 放在 application 之后
    return tags


# ---- 正文 HTML 模板 ----
def _body_html(model, shape, width, height, diffdist, lswidth, app_desc):
    """组装完整 body HTML，与参考产品结构一致"""
    parts = []
    # 开头提示语
    parts.append('<p><font color="#51a0d2">提供铝槽或其配件可以单独提供，也可以整体提供。</font></p>')
    parts.append('<hr id="null">')

    # 固定参数表
    parts.append('<h3><b>固定参数&nbsp;</b></h3>')
    parts.append('<div><table data-rte-border="1" data-rte-widths="1">')
    parts.append('<colgroup><col style="width:33%"><col style="width:33%"><col style="width:33%"></colgroup>')
    parts.append('<tbody>')
    parts.append(f'<tr><td style="width:33%;"><p>宽度</p></td><td style="width:33%;"><p>最大宽度</p></td><td style="width:33%;"><p>{width}</p></td></tr>')
    parts.append(f'<tr><td style="width:33%;"><p>高度</p></td><td style="width:33%;"><p>最大高度</p></td><td style="width:33%;"><p>{height}</p></td></tr>')
    parts.append(f'<tr><td style="width:33%;"><p>散光距离</p></td><td style="width:33%;"><p>灯珠到灯罩的距离</p></td><td style="width:33%;"><p>{diffdist}</p></td></tr>')
    parts.append(f'<tr><td style="width:33%;"><p>灯板宽度</p></td><td style="width:33%;"><p>最大灯板宽度</p></td><td style="width:33%;"><p>{lswidth}</p></td></tr>')
    parts.append('</tbody></table>')

    # 相关服务表
    parts.append('<h3><b>相关服务&nbsp;</b></h3></div>')
    parts.append('<div><table data-rte-border="1" data-rte-widths="1">')
    parts.append('<colgroup><col style="width:33%"><col style="width:33%"><col style="width:33%"></colgroup>')
    parts.append('<tbody>')
    parts.append('<tr><td style="width:33%;"><h4 style="text-align: center;"><b>灯带</b></h4></td>'
                  '<td style="width:33%;"><h4 style="text-align: center;"><b>线材和接插件</b></h4></td>'
                  '<td style="width:33%;"><h4 style="text-align: center;"><b>变压器和插头</b></h4></td></tr>')
    parts.append('<tr><td style="width:33%;"><p style="text-align: center;">可以连灯带组装好提供</p></td>'
                  '<td style="width:33%;"><p style="text-align: center;">可以配套提供任何类型的线材和接插件</p></td>'
                  '<td style="width:33%;"><p style="text-align: center;">提供不同功率的变压器和插头</p></td></tr>')
    parts.append('</tbody></table></div>')

    # 文档链接
    parts.append('<div><p></p><ul>')
    parts.append(f'<li><a href="https://cn.dengtec.com/data/datasheet/{model}-CN.pdf" target="_blank" rel="noopener">规格书 - PDF</a></li>')
    parts.append(f'<li><a href="https://cn.dengtec.com/data/2d/{model}.dxf" target="_blank" rel="noopener">2D 图纸 - DXF</a></li>')
    parts.append(f'<li><a href="https://cn.dengtec.com/data/3d/{model}.stp" target="_blank" rel="noopener">3D 图纸 - STP</a></li>')
    parts.append('</ul><p></p></div>')

    return ''.join(parts)


def _slug(model):
    """AP-001-U-W15.8-H6.8-D4-L12 -> ap-001-u-w15-8-h6-8-d4-l12"""
    return model.lower().replace('.', '-')


def make_product(id_, model, shape, width, height, diffdist, lswidth, application, app_desc):
    """构造一个完整铝槽产品条目"""
    slug = _slug(model)
    # 生成描述文字
    desc = f'{app_desc} 宽-{width}mm 高-{height}mm 散光距离-{diffdist}mm 灯板宽-{lswidth}mm'
    return {
        'id': id_,
        'title': model,
        'slug': slug,
        'cover': f'/assets/uploads/aluminum-profile-cover-{slug}.webp',
        'date': '2026-06-22',
        'name': '',
        'category': '铝槽',
        'description': desc,
        'tags_visible': False,
        'tags': _tags(shape, width, height, diffdist, lswidth, application),
        'price': '',
        'body': _body_html(model, shape, width, height, diffdist, lswidth, app_desc),
        'rte_clicked_editor_idx': '',
        'detail_gallery': {
            'visible': True,
            'images': [
                {'url': f'/assets/uploads/aluminum-profile-{slug}-gallery-1.webp'},
                {'url': f'/assets/uploads/aluminum-profile-{slug}-gallery-2.webp'},
                {'url': f'/assets/uploads/aluminum-profile-{slug}-gallery-3.webp'},
                {'url': f'/assets/uploads/aluminum-profile-{slug}-gallery-4.webp'},
            ]
        },
        'style_bg-color': '',
        'modules': [
            {'type': 'item_data', 'order': 1, 'variant': 'default', 'data': {}}
        ],
    }


# ===== 18 个新产品定义 =====
# 数据来源: cn.dengtec.com/product-category/channel-light/ (第1+2页)
# 详情参数来自对应产品详情页
# shape: U/V/L  application: linear-lighting/shelf-dresser/light-guide-plate

PRODUCTS = [
    # ==== 第1页 (id 2-12) ====

    # id=2  AP-002-U-W24.8-H8-D5.5-L12  线型灯 U型
    make_product(2, 'AP-002-U-W24.8-H8-D5.5-L12', 'U', 24.8, 8, 5.5, 12,
                 'linear-lighting', '线型灯铝槽'),

    # id=3  AP-003-U-W22-H11.9-D8.9-L11  线型灯 U型
    make_product(3, 'AP-003-U-W22-H11.9-D8.9-L11', 'U', 22, 11.9, 8.9, 11,
                 'linear-lighting', '线型灯铝槽'),

    # id=4  AP-004-U-W16-H11.8-D9-L11.6  线型灯 U型
    make_product(4, 'AP-004-U-W16-H11.8-D9-L11.6', 'U', 16, 11.8, 9, 11.6,
                 'linear-lighting', '线型灯铝槽'),

    # id=5  AP-005-U-W39-H8.9-D4-L26.4  线型灯 U型
    make_product(5, 'AP-005-U-W39-H8.9-D4-L26.4', 'U', 39, 8.9, 4, 26.4,
                 'linear-lighting', '线型灯铝槽'),

    # id=6  AP-006-U-W23-H9.4-D6.4-L16  线型灯 U型
    make_product(6, 'AP-006-U-W23-H9.4-D6.4-L16', 'U', 23, 9.4, 6.4, 16,
                 'linear-lighting', '线型灯铝槽'),

    # id=7  AP-007-U-W18.1-H15.7-D11-L12  线型灯 U型
    make_product(7, 'AP-007-U-W18.1-H15.7-D11-L12', 'U', 18.1, 15.7, 11, 12,
                 'linear-lighting', '线型灯铝槽'),

    # id=8  AP-008-U-W17.5-H9.2-D6.6-L12.7  线型灯 U型
    make_product(8, 'AP-008-U-W17.5-H9.2-D6.6-L12.7', 'U', 17.5, 9.2, 6.6, 12.7,
                 'linear-lighting', '线型灯铝槽'),

    # id=9  AP-009-V-W26.8-H17.1-D8.7-L11  线型灯 V型
    make_product(9, 'AP-009-V-W26.8-H17.1-D8.7-L11', 'V', 26.8, 17.1, 8.7, 11,
                 'linear-lighting', '线型灯铝槽'),

    # id=10 AP-010-U-W12.4-H7.8-D4.5-L8.8  线型灯 U型
    make_product(10, 'AP-010-U-W12.4-H7.8-D4.5-L8.8', 'U', 12.4, 7.8, 4.5, 8.8,
                 'linear-lighting', '线型灯铝槽'),

    # id=11 AP-011-U-W16.5-H11.5-D8.3-L9.6  线型灯 U型
    make_product(11, 'AP-011-U-W16.5-H11.5-D8.3-L9.6', 'U', 16.5, 11.5, 8.3, 9.6,
                 'linear-lighting', '线型灯铝槽'),

    # id=12 AP-012-U-W18-H15.4-D11.1-L12.6  线型灯 U型
    make_product(12, 'AP-012-U-W18-H15.4-D11.1-L12.6', 'U', 18, 15.4, 11.1, 12.6,
                 'linear-lighting', '线型灯铝槽'),

    # ==== 第2页 (id 13-19) ====

    # id=13 AP-013-U-W13.1-H8.1-D5-L9.8  线型灯 U型
    make_product(13, 'AP-013-U-W13.1-H8.1-D5-L9.8', 'U', 13.1, 8.1, 5, 9.8,
                 'linear-lighting', '线型灯铝槽'),

    # id=14 AP-014-U-W20.5-H10.8-D6.8-L14  线型灯 U型
    make_product(14, 'AP-014-U-W20.5-H10.8-D6.8-L14', 'U', 20.5, 10.8, 6.8, 14,
                 'linear-lighting', '线型灯铝槽'),

    # id=15 AP-015-L-W120-H50-D50-L5  层板架 L型
    make_product(15, 'AP-015-L-W120-H50-D50-L5', 'L', 120, 50, 50, 5,
                 'shelf-dresser', '层板架铝槽'),

    # id=16 AP-016-U-W16.6-H11.1-D8.5-L10.3  线型灯 U型
    make_product(16, 'AP-016-U-W16.6-H11.1-D8.5-L10.3', 'U', 16.6, 11.1, 8.5, 10.3,
                 'linear-lighting', '线型灯铝槽'),

    # id=17 AP-017-L-W16-H16-D8-L10.7  线型灯 L型
    make_product(17, 'AP-017-L-W16-H16-D8-L10.7', 'L', 16, 16, 8, 10.7,
                 'linear-lighting', '线型灯铝槽'),

    # id=18 AP-018-U-W17.8-H10.5-D8.2-L12.6  线型灯 U型
    make_product(18, 'AP-018-U-W17.8-H10.5-D8.2-L12.6', 'U', 17.8, 10.5, 8.2, 12.6,
                 'linear-lighting', '线型灯铝槽'),

    # id=19 AP-019-U-W7.2-H8.5-D0-L5.8  导光板 U型
    # 散光距离为0, 属于导光板专用铝槽
    make_product(19, 'AP-019-U-W7.2-H8.5-D0-L5.8', 'U', 7.2, 8.5, 0, 5.8,
                 'light-guide-plate', '导光板铝槽'),
]


def main():
    with open(FILEPATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if data is None:
        print("ERROR: file empty or parse failed")
        return

    print(f"Existing products: {len(data)}")
    data.extend(PRODUCTS)
    print(f"After append: {len(data)}")

    with open(FILEPATH, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, indent=2, width=1000)

    print(f"Written: {FILEPATH}")

    # Verify
    with open(FILEPATH, 'r', encoding='utf-8') as f:
        verify = yaml.safe_load(f)
    print(f"Verified: {len(verify)} products")

    for p in verify:
        print(f"  id={p['id']:2d}  {p['title']}")


if __name__ == '__main__':
    main()
