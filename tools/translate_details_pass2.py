"""第二遍翻译 - 修复所有残余中文"""
import yaml, re, os, sys
from copy import deepcopy
from pathlib import Path

SITE_DIR = Path(r"f:\dengtec\mycompany.website11\sites\6")

# ============================================================
# 第二遍补充翻译
# ============================================================
EXTRA = {
    # === 铝槽 body ===
    "导光板铝槽": "Light Guide Plate Profile",
    "层板架铝槽": "Shelf Bracket Profile",
    "固定参数": "Fixed Parameters",
    "可定制的参数": "Customizable Parameters",
    "散光距离": "Diffusion Distance",
    "最大灯板": "Max LED Strip",
    "灯板宽": "Strip Width",
    "灯珠到灯罩的距离": "Distance from LED to Cover",
    "可以配套提供任何类型的": "Can provide any type of",
    "的变压器和": "transformers and",
    "和接插件": "and connectors",
    "提供不同": "Available in different",
    "或其配件可以单独提供": "or its accessories can be provided separately",
    "可以连灯带组装好提供": "Can be provided fully assembled with LED strips",
    "也可以整体提供": "Can also be provided as a complete unit",
    "变压器和": "Transformers and",

    # === 全息投影 body ===
    "全息投影": "Holographic Projection",
    "显示直径": "Display Diameter",
    "分辨率": "Resolution",
    "像素点": "Pixel Pitch",
    "可以通过遥控器控制": "Controllable via remote",
    "可多台同步": "Multi-unit sync supported",
    "可无线投屏": "Wireless projection supported",
    "可遥控": "Remote control supported",
    "多个设备": "Multiple devices",
    "定时播放": "Scheduled playback",
    "带蓝牙音频": "With Bluetooth audio",
    "控制平台": "Control Platform",
    "文件格式": "File Format",
    "无线投屏": "Wireless Projection",
    "的文件格式": "file format",

    # === 项目 body ===
    "兰蔻滴液展示道具": "Lancôme Liquid Dispensing Display Prop",
    "主要特征": "Key Features",
    "中间灯板": "Center Light Board",
    "传感器": "Sensor",
    "一个非常薄的箱子": "A very slim case",
    "一旦消费者将手放在传感器下方": "Once the consumer places their hand under the sensor",
    "使得小黑瓶的味道维持在": "keeps the Genifique bottle at optimal temperature",
    "共使用了": "A total of",
    "功率均可按需定制": "Power can be customized as needed",
    "任意形状和图案的灯板设计": "Custom shapes and patterns for light board design",
    "保证每个灯珠亮度一致": "Ensures consistent brightness for each LED",
    "其中中间为": "The center section features",
    "则冷却模块开始工作": "the cooling module activates",
    "双向带灯": "Dual-sided with LEDs",
    "可以和外接的传感器设备通信": "Can communicate with external sensor devices",
    "精选推荐": "Featured Picks",

    # === 导电槽 ===
    "便捷安装": "Easy Installation",
    "精细小巧": "Compact & Slim",

    # === 博客兰蔻剩余文本 ===
    "瓶子中的乳液用完后": "When the lotion in the bottle runs out",
    "需要更换新的瓶子": "replace with a new bottle",
    "具体步骤如下": "Steps are as follows",
    "拧下白色": "Unscrew the white",
    "并将其拧到新的小黑瓶上": "and screw it onto the new Genifique bottle",
    "电池充满电后": "After a full charge",
    "可以正常使用2天左右": "the battery lasts about 2 days",
    "视使用的频率": "Actual duration depends on usage frequency",
    "具体的使用时长不定": "exact duration varies",
    "若是侧板看不见": "If the side panel light is off",
    "感应无反应的情况下": "and there is no response",
    "就表明电池的电量用完了": "the battery is depleted",
    "每套道具都配备了": "Each unit comes with",
    "块电池": "batteries",
    "请电池取下后": "Remove the battery and",
    "请用充电器及时给电池充电": "charge it promptly with the charger",
    "的步骤如下": "steps are as follows",
    "天左右": "days",
    "更换电池的步骤如下": "Battery replacement steps are as follows",
    "定制瓶盖": "custom cap",
    "小黑瓶": "Genifique bottle",
}


def translate_html_body_v2(body):
    """更彻底的 body 翻译"""
    if not body:
        return body

    result = body

    # 按长度降序排列所有翻译
    pairs = sorted(EXTRA.items(), key=lambda x: -len(x[0]))
    for cn, en in pairs:
        result = result.replace(cn, en)

    return result


def fix_data_file(filename):
    """重新翻译一个 en data 文件"""
    zh_path = SITE_DIR / "lang" / "zh-CN" / "data" / filename
    en_path = SITE_DIR / "lang" / "en" / "data" / filename

    with open(en_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # 获取 items
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("items", [])
    else:
        return

    changed = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        # 重新翻译 body
        if 'body' in item and item['body']:
            new_body = translate_html_body_v2(str(item['body']))
            if new_body != item['body']:
                item['body'] = new_body
                changed += 1

        # 重新翻译 description
        if 'description' in item and item['description']:
            new_desc = translate_html_body_v2(str(item['description']))
            if new_desc != item['description']:
                item['description'] = new_desc
                changed += 1

        # 翻译 items 内嵌的 body
        if 'modules' in item:
            for mod in item['modules']:
                if isinstance(mod, dict) and mod.get('type') == 'featured_picks' and 'data' in mod:
                    fd = mod['data']
                    if 'items' in fd:
                        for fi in fd['items']:
                            if isinstance(fi, dict) and 'desc' in fi and fi['desc']:
                                new_desc = translate_html_body_v2(str(fi['desc']))
                                if new_desc != fi['desc']:
                                    fi['desc'] = new_desc
                                    changed += 1

    # 写回
    out = items if isinstance(data, list) else {**data, "items": items}
    with open(en_path, "w", encoding="utf-8") as f:
        yaml.dump(out, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    # 计算剩余中文
    remaining = len(re.findall(r'[一-鿿]', str(out)))
    print(f"  {filename}: {changed} changed, {remaining} Chinese chars remaining")


def main():
    data_dir = SITE_DIR / "lang" / "en" / "data"
    files = sorted([f.name for f in data_dir.glob("*.yaml")])

    print("=" * 60)
    print("Pass 2: Fixing remaining Chinese in data files")
    print("=" * 60)

    for filename in files:
        fix_data_file(filename)

    print("\nDone!")

if __name__ == "__main__":
    main()
