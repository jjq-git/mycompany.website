"""
从生产站详情页提取数据, 追加 14 个 LED 灯条产品到 led-strip.yaml
每个产品的参数(电压/灯珠数/板宽/封装/色温/功率)均来自 cn.dengtec.com 产品详情页
按参考产品 LS-12V-60-W10-5050M 的结构生成
"""
import yaml
import os

FILEPATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'sites', '6', 'lang', 'zh-CN', 'data', 'led-strip.yaml')

# ---- 正文 HTML 模板 ----
def _fixed_table(voltage, pitch_label, pitch_value, width, chip):
    """固定参数表格"""
    return (
        f'<p><font color="#51a0d2">定制灯条需要1-2天的交期!</font></p>'
        f'<h3><b>固定的参数&nbsp;</b></h3>'
        f'<div><table data-rte-border="1" data-rte-widths="1">'
        f'<colgroup><col style="width:33%"><col style="width:33%"><col style="width:33%"></colgroup>'
        f'<tbody>'
        f'<tr><td style="width:33%;"><p>电压</p></td><td style="width:33%;"><p>输入电压</p></td><td style="width:33%;"><p>{voltage}</p></td></tr>'
        f'<tr><td style="width:33%;"><p>灯珠数</p></td><td style="width:33%;"><p>1米的灯珠数量</p></td><td style="width:33%;"><p>{pitch_label}</p></td></tr>'
        f'<tr><td style="width:33%;"><p>灯条宽度</p></td><td style="width:33%;"><p>灯条宽度</p></td><td style="width:33%;"><p>{width}</p></td></tr>'
        f'<tr><td style="width:33%;"><p>灯珠封装</p></td><td style="width:33%;"><p>灯珠封装</p></td><td style="width:33%;"><p>{chip}</p></td></tr>'
        f'</tbody></table>'
    )

def _custom_table(cct_cell, color_cell, cri_cell, power_cell):
    """可定制参数表格"""
    return (
        f'<h3><b>可定制的参数</b></h3></div>'
        f'<div><table data-rte-border="1" data-rte-widths="1">'
        f'<colgroup><col style="width:33%"><col style="width:33%"><col style="width:33%"></colgroup>'
        f'<tbody>'
        f'<tr><td style="width:33%;"><p>白光灯珠</p></td><td style="width:33%;"><p>可以定制的色温</p></td><td style="width:33%;">{cct_cell}</td></tr>'
        f'<tr><td style="width:33%;"><p>非白光灯珠</p></td><td style="width:33%;"><p>彩色灯珠</p></td><td style="width:33%;">{color_cell}</td></tr>'
        f'<tr><td style="width:33%;"><p>显色指数</p></td><td style="width:33%;"><p>白光灯有效</p></td><td style="width:33%;">{cri_cell}</td></tr>'
        f'<tr><td style="width:33%;"><p>功率</p></td><td style="width:33%;"><p>灯珠功率可以根据需求定制.</p></td><td style="width:33%;">{power_cell}</td></tr>'
        f'</tbody></table>'
    )

def _docs_links(model):
    """文档下载链接"""
    return (
        f'<p><ul>'
        f'<li><a href="https://cn.dengtec.com/data/datasheet/{model}-CN.pdf" target="_blank" rel="noopener">规格书 - PDF</a></li>'
        f'<li><a href="https://cn.dengtec.com/data/2d/{model}.dxf" target="_blank" rel="noopener">2D 图纸 - DXF</a></li>'
        f'<li><a href="https://cn.dengtec.com/data/3d/{model}.stp" target="_blank" rel="noopener">3D 图纸 - STP</a></li>'
        f'</ul></p></div>'
    )

def make_body(model, voltage, pitch_label, width, chip,
              cct_cell='<br>', color_cell='<br>', cri_cell='<br>', power_cell='<br>'):
    """组装完整 body HTML"""
    return (
        _fixed_table(voltage, pitch_label, pitch_label, width, chip)
        + _custom_table(cct_cell, color_cell, cri_cell, power_cell)
        + _docs_links(model)
    )

def make_gallery(slug):
    """详情图库占位路径"""
    return {
        'visible': True,
        'images': [
            {'url': f'/assets/uploads/led-strip-{slug}-gallery-1.webp'},
            {'url': f'/assets/uploads/led-strip-{slug}-gallery-2.webp'},
            {'url': f'/assets/uploads/led-strip-{slug}-gallery-3.webp'},
            {'url': f'/assets/uploads/led-strip-{slug}-gallery-4.webp'},
        ]
    }

def make_product(id_, model, voltage, pitch_label, width, chip,
                 desc, tags, cct_cell='<br>', color_cell='<br>',
                 cri_cell='<br>', power_cell='<br>'):
    """构造一个完整产品条目"""
    slug = model.lower()
    return {
        'id': id_,
        'title': model,
        'slug': slug,
        'cover': f'/assets/uploads/led-strip-cover-{slug}.webp',
        'date': '2026-06-22',
        'name': '',
        'category': '',
        'description': desc,
        'tags_visible': False,
        'tags': tags,
        'price': '',
        'body': make_body(model, voltage, pitch_label, width, chip,
                          cct_cell, color_cell, cri_cell, power_cell),
        'rte_clicked_editor_idx': '',
        'detail_gallery': make_gallery(slug),
        'style_bg-color': '',
        'modules': [
            {'type': 'item_data', 'order': 1, 'variant': 'default', 'data': {}}
        ],
    }


# ===== 14 个新产品定义 =====
# 所有功率、色温数据来自生产站 cn.dengtec.com 产品详情页

PRODUCTS = [
    # id=8  LS-12V-60-W10-5050S  来源: 详情页 功率14.4W
    make_product(8, 'LS-12V-60-W10-5050S', '12V', '60灯/米', '10MM', '5050S',
                 '灯条 电压12v 60灯/米 板宽10MM 封装5050S',
                 ['chip-5050S', 'color-', 'color-blue', 'pitch-60', 'voltage-12v', 'width-10'],
                 cct_cell='<br>', color_cell='<p>blue</p>', cri_cell='<br>',
                 power_cell='<p>14.4W</p>'),

    # id=9  LS-12V-60-W6-5050S  来源: 详情页 功率14.4W
    make_product(9, 'LS-12V-60-W6-5050S', '12V', '60灯/米', '6MM', '5050S',
                 '灯条 电压12v 60灯/米 板宽6MM 封装5050S',
                 ['chip-5050S', 'color-', 'color-blue', 'pitch-60', 'voltage-12v', 'width-6'],
                 cct_cell='<br>', color_cell='<p>blue</p>', cri_cell='<br>',
                 power_cell='<p>14.4W</p>'),

    # id=10  LS-12V-60-W8-2835  来源: 详情页 2700K/3000K/4500K/6500K, red/green/blue, 80+/90+, 14.4W
    make_product(10, 'LS-12V-60-W8-2835', '12V', '60灯/米', '8MM', '2835',
                 '灯条 电压12v 60灯/米 板宽8MM 封装2835',
                 ['chip-2835', 'color-2700K', 'color-3000K', 'color-4500K', 'color-6500K',
                  'color-blue', 'color-green', 'color-red', 'pitch-60', 'voltage-12v', 'width-8'],
                 cct_cell='<p>2700K,3000K,4500K,6500K</p>',
                 color_cell='<p>red,green,blue</p>',
                 cri_cell='<p>80+,90+</p>',
                 power_cell='<p>14.4W</p>'),

    # id=11  LS-12V-60-W8-3528  来源: 详情页 2700K/3000K/4500K/6500K, 80+/90+, 3.6W/4.8W/9.6W/7.2W
    # 3528 非白光灯珠列为空白(不支持彩色)
    make_product(11, 'LS-12V-60-W8-3528', '12V', '60灯/米', '8MM', '3528',
                 '灯条 电压12v 60灯/米 板宽8MM 封装3528',
                 ['chip-3528', 'color-2700K', 'color-3000K', 'color-4500K', 'color-6500K',
                  'pitch-60', 'voltage-12v', 'width-8'],
                 cct_cell='<p>2700K,3000K,4500K,6500K</p>',
                 color_cell='<br>',
                 cri_cell='<p>80+,90+</p>',
                 power_cell='<p>3.6W,4.8W,9.6W,7.2W</p>'),

    # id=12  LS-12V-60C1-W8-5050S  来源: 详情页 60C1灯/米(1灯1剪), 功率14.4W
    make_product(12, 'LS-12V-60C1-W8-5050S', '12V', '60C1灯/米', '8MM', '5050S',
                 '灯条 电压12v 60C1灯/米 板宽8MM 封装5050S',
                 ['chip-5050S', 'color-', 'color-blue', 'pitch-60C1', 'voltage-12v', 'width-8'],
                 cct_cell='<br>', color_cell='<p>blue</p>', cri_cell='<br>',
                 power_cell='<p>14.4W</p>'),

    # ===== 第2页 =====

    # id=13  LS-12V-72-W6S-2835  来源: 详情页 2700K-6500K, red/green/blue, 80+/90+, 4.8W/6.4W/8.6W/11.5W
    make_product(13, 'LS-12V-72-W6S-2835', '12V', '72灯/米', '6SMM', '2835',
                 '灯条 电压12v 72灯/米 板宽6SMM 封装2835',
                 ['chip-2835', 'color-2700K', 'color-3000K', 'color-4500K', 'color-6500K',
                  'color-blue', 'color-green', 'color-red', 'pitch-72', 'voltage-12v', 'width-6S'],
                 cct_cell='<p>2700K,3000K,4500K,6500K</p>',
                 color_cell='<p>red,green,blue</p>',
                 cri_cell='<p>80+,90+</p>',
                 power_cell='<p>4.8W,6.4W,8.6W,11.5W</p>'),

    # id=14  LS-12V-90-W20-WS2811  来源: 详情页 可编程RGB, 14.4W
    make_product(14, 'LS-12V-90-W20-WS2811', '12V', '90灯/米', '20MM', 'WS2811',
                 '灯条 电压12v 90灯/米 板宽20MM 封装WS2811',
                 ['chip-WS2811', 'color-programmable', 'pitch-90', 'voltage-12v', 'width-20'],
                 cct_cell='<br>', color_cell='<p>programmable</p>', cri_cell='<br>',
                 power_cell='<p>14.4W</p>'),

    # id=15  LS-12V-90-W6S-2835  来源: 详情页 2700K-6500K, red/green/blue, 80+/90+, 6.4W/14.4W/7.2W/11.5W
    make_product(15, 'LS-12V-90-W6S-2835', '12V', '90灯/米', '6SMM', '2835',
                 '灯条 电压12v 90灯/米 板宽6SMM 封装2835',
                 ['chip-2835', 'color-2700K', 'color-3000K', 'color-4500K', 'color-6500K',
                  'color-blue', 'color-green', 'color-red', 'pitch-90', 'voltage-12v', 'width-6S'],
                 cct_cell='<p>2700K,3000K,4500K,6500K</p>',
                 color_cell='<p>red,green,blue</p>',
                 cri_cell='<p>80+,90+</p>',
                 power_cell='<p>6.4W,14.4W,7.2W,11.5W</p>'),

    # id=16  LS-12V-90-W8-2835  来源: 详情页 2700K-6500K, red/green/blue, 80+/90+, 6.4W/9.6W/14.4W
    make_product(16, 'LS-12V-90-W8-2835', '12V', '90灯/米', '8MM', '2835',
                 '灯条 电压12v 90灯/米 板宽8MM 封装2835',
                 ['chip-2835', 'color-2700K', 'color-3000K', 'color-4500K', 'color-6500K',
                  'color-blue', 'color-green', 'color-red', 'pitch-90', 'voltage-12v', 'width-8'],
                 cct_cell='<p>2700K,3000K,4500K,6500K</p>',
                 color_cell='<p>red,green,blue</p>',
                 cri_cell='<p>80+,90+</p>',
                 power_cell='<p>6.4W,9.6W,14.4W</p>'),

    # id=17  LS-12V-96-W5-2835  来源: 详情页 2700K-6500K, red/green/blue, 80+/90+, 6.4W/7.2W/11.5W/15.4W
    make_product(17, 'LS-12V-96-W5-2835', '12V', '96灯/米', '5MM', '2835',
                 '灯条 电压12v 96灯/米 板宽5MM 封装2835',
                 ['chip-2835', 'color-2700K', 'color-3000K', 'color-4500K', 'color-6500K',
                  'color-blue', 'color-green', 'color-red', 'pitch-96', 'voltage-12v', 'width-5'],
                 cct_cell='<p>2700K,3000K,4500K,6500K</p>',
                 color_cell='<p>red,green,blue</p>',
                 cri_cell='<p>80+,90+</p>',
                 power_cell='<p>6.4W,7.2W,11.5W,15.4W</p>'),

    # id=18  LS-24V-120-W8-2835  来源: 详情页 2700K-6500K, red/green/blue, 80+/90+, 9.6W/14.4W/7.2W/19.2W
    make_product(18, 'LS-24V-120-W8-2835', '24V', '120灯/米', '8MM', '2835',
                 '灯条 电压24v 120灯/米 板宽8MM 封装2835',
                 ['chip-2835', 'color-2700K', 'color-3000K', 'color-4500K', 'color-6500K',
                  'color-blue', 'color-green', 'color-red', 'pitch-120', 'voltage-24v', 'width-8'],
                 cct_cell='<p>2700K,3000K,4500K,6500K</p>',
                 color_cell='<p>red,green,blue</p>',
                 cri_cell='<p>80+,90+</p>',
                 power_cell='<p>9.6W,14.4W,7.2W,19.2W</p>'),

    # id=19  LS-24V-60C2-W8-5050S  来源: 详情页(型号本身24V/8mm/60C2), 功率14.4W
    # 注: 生产站详情页固定参数表有误(显示12V/10mm), 以产品型号为准
    make_product(19, 'LS-24V-60C2-W8-5050S', '24V', '60C2灯/米', '8MM', '5050S',
                 '灯条 电压24v 60C2灯/米 板宽8MM 封装5050S',
                 ['chip-5050S', 'color-', 'color-blue', 'pitch-60C2', 'voltage-24v', 'width-8'],
                 cct_cell='<br>', color_cell='<p>blue</p>', cri_cell='<br>',
                 power_cell='<p>14.4W</p>'),

    # id=20  LS-5V-60-W10-WS2812  来源: 详情页 可编程RGB, 11.5W
    make_product(20, 'LS-5V-60-W10-WS2812', '5V', '60灯/米', '10MM', 'WS2812',
                 '灯条 电压5v 60灯/米 板宽10MM 封装WS2812',
                 ['chip-WS2812', 'color-programmable', 'pitch-60', 'voltage-5v', 'width-10'],
                 cct_cell='<br>', color_cell='<p>programmable</p>', cri_cell='<br>',
                 power_cell='<p>11.5W</p>'),

    # id=21  LS-5V-90-W8-4020  来源: 详情页 可编程彩色, 16.7W
    make_product(21, 'LS-5V-90-W8-4020', '5V', '90灯/米', '8MM', '4020',
                 '灯条 电压5v 90灯/米 板宽8MM 封装4020',
                 ['chip-4020', 'color-programmable', 'pitch-90', 'voltage-5v', 'width-8'],
                 cct_cell='<br>', color_cell='<p>programmable</p>', cri_cell='<br>',
                 power_cell='<p>16.7W</p>'),
]


def main():
    # 读取现有数据
    with open(FILEPATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if data is None:
        print("ERROR: 文件为空或解析失败")
        return

    print(f"现有产品数: {len(data)}")

    # 追加新产品
    data.extend(PRODUCTS)
    print(f"追加后产品数: {len(data)}")

    # 写回 - 使用与源文件一致的格式
    with open(FILEPATH, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, indent=2, width=1000)

    print(f"已写入: {FILEPATH}")

    # 验证
    with open(FILEPATH, 'r', encoding='utf-8') as f:
        verify = yaml.safe_load(f)
    print(f"验证通过: {len(verify)} 个产品")

    # 列出所有产品
    for p in verify:
        print(f"  id={p['id']:2d}  {p['title']}")


if __name__ == '__main__':
    main()
