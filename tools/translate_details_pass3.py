"""第三遍清除 - 处理所有残余中文字符"""
import yaml, re, os, sys
from copy import deepcopy
from pathlib import Path

SITE_DIR = Path(r"f:\dengtec\mycompany.website11\sites\6")

FIXES = {
    # --- 铝槽 ---
    "灯珠到灯罩的距离": "Distance from LED to Cover",

    # --- 全息 ---
    "蓝牙音频": "Bluetooth Audio",

    # --- LED灯条 ---
    "精选推荐": "Featured Picks",

    # --- 博客 兰蔻 残留 ---
    "非触发状态": "In non-triggered state",
    "侧板的白色": "the side panel white",
    "不断循环": "cycling continuously",
    "电池充满电后": "After a full charge",
    "可以Normal Use2天左右": "the battery lasts about 2 days",
    "天左右": " days",
    "视使用的频率": "Actual duration depends on usage frequency",
    "具体的使用时长不定": "exact duration varies",
    "若是侧板看不见": "If the side panel",
    "感应无反应的情况下": " and there is no sensor response",
    "就表明电池的电量用完了": "the battery is depleted",
    "每套道具都配备了3": "Each unit comes with 3",
    "块电池": " batteries",
    "请电池取下后": "Remove the battery and",
    "请用充电器及时给电池充电": " charge it promptly with the charger",
    "拧下白色": "Unscrew the white",
    "定制瓶盖": "custom cap",
    "并将其拧到新的小黑瓶上": "and screw it onto the new Genifique bottle",
    "的步骤如下": "steps:",
    "设置需要的值": "set desired value",

    # --- 项目 ---
    "主要特征": "Key Features",
    "中间灯板": "Center Light Board",
    "左右灯板": "Left/Right Light Boards",
    "亮度一致": "Brightness Consistency",
    "任意形状": "Custom shapes",
    "及变化过程": " and transition process",
    "可以批量生成": "Can be mass-produced",
    "可无线更新动态效果": "Wireless dynamic effect updates",
    "可以远程更换图片": "Remote image update supported",
    "可以贴片": "Solderable",
    "可定制尺寸": "Custom sizes",
    "可定制的数码管": "Customizable digital display tube",
    "可以驱动多个的": "Can drive multiple",
    "恒压Power Supply可以驱动多个的Spot Lights": "Constant voltage power supply can drive multiple spot lights",
    "变化的速度": "animation speed",
    "双向带灯": "Dual-sided LED",
    "可以记录操作信息": "Can record operation data",
    "发光面的每个点都可以精准": "Each point on the luminous surface can precisely",
    "则冷却": "the cooling",
    "内置高品质音频播放": "Built-in high-quality audio playback",
    "可以和外接的": "Can connect to external",
    "传感器的设备通信": "sensor devices",
    "作为层板信息条": "As shelf info strip",
    "则冷却Modules开始工作": "the cooling module activates",
    "传感器": "Sensor",
    "可定制": "Customizable",
}

def fix_body(html):
    """修复 body HTML 中残余中文"""
    if not html:
        return html
    result = html
    pairs = sorted(FIXES.items(), key=lambda x: -len(x[0]))
    for cn, en in pairs:
        result = result.replace(cn, en)
    # Additional regex fixes
    result = re.sub(r'灯条 电压12v\s+(\d+)灯/米\s+板宽(\d+)MM\s+封装(\S+)',
                    r'LED Strip, 12V, \1 LEDs/m, Width \2mm, Package \3', result)
    result = re.sub(r'灯条 电压24v\s+(\d+)灯/米\s+板宽(\d+)MM\s+封装(\S+)',
                    r'LED Strip, 24V, \1 LEDs/m, Width \2mm, Package \3', result)
    return result


def fix_file(fname):
    """修复单个 en data 文件"""
    path = SITE_DIR / "lang" / "en" / "data" / fname
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return

    def process(obj):
        if isinstance(obj, str):
            return fix_body(obj)
        elif isinstance(obj, dict):
            # Fix all string values
            result = {}
            for k, v in obj.items():
                if k == 'body' and isinstance(v, str):
                    result[k] = fix_body(v)
                elif k == 'description' and isinstance(v, str):
                    result[k] = fix_body(v)
                elif k == 'title' and isinstance(v, str) and any('一' <= c <= '鿿' for c in v):
                    result[k] = fix_body(v)
                elif isinstance(v, (dict, list)):
                    result[k] = process(v)
                else:
                    result[k] = v
            return result
        elif isinstance(obj, list):
            return [process(it) for it in obj]
        return obj

    fixed = process(data)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(fixed, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    remaining = len(re.findall(r'[一-鿿]', str(fixed)))
    return remaining


def rewrite_portfolio():
    """用英文重写 portfolio 种子数据（旧数据是 Nova AI 内容）"""
    path = SITE_DIR / "lang" / "en" / "data" / "portfolio.yaml"
    data = {
        "items": [
            {"slug": "rimu", "title": "RIMU", "cover": "/assets/uploads/projects-cover-20260622100818-59d54439.webp",
             "summary": "A modular electronic device that makes hardware and programming accessible to everyone.",
             "date": "2026-06-22", "tags": ["Controllers & Sensors", "Modules"]},
            {"slug": "cob-led", "title": "Programmable COB LED Board", "cover": "/assets/uploads/projects-cover-20260622102910-3820cda2.webp",
             "summary": "Chip-On-Board LED panel for logos and lettering — thinner and more versatile than traditional light guide plates.",
             "date": "2026-06-22", "tags": ["Controllers & Sensors", "Lighting"]},
            {"slug": "item-3", "title": "Programmable Illuminated LOGO / Letters", "cover": "/assets/uploads/projects-cover-20260622103221-c287b24c.webp",
             "summary": "Illuminated LOGO / letters for display purposes with programmable color and animation.",
             "tags": ["Controllers & Sensors", "Lighting"]},
            {"slug": "lotion-dropper-dummy", "title": "Lancôme Liquid Dispensing Prop", "cover": "/static/img/product-model.svg",
             "summary": "Custom automatic liquid dispensing device integrating precision fluid control, sensor detection, and dynamic lighting.",
             "tags": ["Controllers", "Custom"]},
        ]
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return 0


def main():
    files = sorted((SITE_DIR / "lang" / "en" / "data").glob("*.yaml"))
    print("=" * 60)
    print("Pass 3: Final Chinese cleanup")
    print("=" * 60)

    for fp in files:
        fname = fp.name
        if fname == "portfolio.yaml":
            rem = rewrite_portfolio()
        else:
            rem = fix_file(fname)
        print(f"  {fname}: {rem} Chinese chars remaining")

    print("\nDone!")


if __name__ == "__main__":
    main()
