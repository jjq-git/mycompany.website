"""最终版详情翻译 - 从 zh-CN 重译所有 en data 文件，用正则处理模式化内容"""
import yaml, re, os, sys
from copy import deepcopy
from pathlib import Path

SITE_DIR = Path(r"f:\dengtec\mycompany.website11\sites\6")

# ============================================================
# 全量翻译映射
# ============================================================
T = {
    # --- 分类 ---
    "LED灯条": "LED Strips",
    "铝槽": "Aluminum Profiles",
    "射灯": "Spot Lights",
    "全息投影": "Hologram Display",
    "线材": "Cables",
    "线材及接插件": "Cables & Connectors",
    "导电槽": "Power Track",
    "电源": "Power Supply",
    "控制器及传感器": "Controllers & Sensors",
    "模块": "Modules",
    "灯光": "Lighting",
    "设计相关": "Design Related",
    "LED相关": "LED Related",
    "控制器": "Controllers",
    "临时项目": "Temporary Projects",

    # --- 项目 ---
    "日目 / RIMU": "RIMU",
    "RIMU 是一个模块化的电子设备，它帮助那些不擅长硬件和编程的人轻松使用各种类型的电子设备.":
        "RIMU is a modular electronic device that helps people with no hardware or programming skills use various types of electronic devices with ease.",
    "彩色可编程COB灯板": "Programmable COB LED Board",
    "Chip-On-Board LED光板，可用于标识和字符后面，取代传统的导光板结构，更薄，用途更广。":
        "Chip-On-Board LED panel used behind logos and lettering to replace traditional light guide plate structures — thinner and more versatile.",
    "可编程发光LOGO/字": "Programmable Illuminated LOGO / Letters",
    "作为展示用的发光字LOGO.": "Illuminated LOGO / letters for display purposes.",
    "主机和模块之间采用了磁铁和卡扣的结构, 能够非常轻易地进行装配和卸载. 4.3英寸的触摸屏, 能够非常容易的实现和设备进行信息交互.":
        "The main unit and modules use a magnetic snap-fit structure, allowing easy assembly and disassembly. The 4.3-inch touchscreen enables intuitive human-device interaction.",
    "主机和模块之间采用磁铁和卡扣的连接方式，能够实现快速且便捷的装配与卸载。4.3英寸的触摸屏使得与设备的信息交互变得极为简单和直观。":
        "The main unit and modules use magnetic snap-fit connections for fast, convenient assembly and disassembly. The 4.3-inch touchscreen makes device interaction simple and intuitive.",

    # --- 博客 ---
    "检测治具使用说明": "Inspection Jig User Manual",
    "检测治具的详细使用说明，包含正常操作、数据读取、功能键设置和传感器校准等":
        "Detailed user manual for the inspection jig, covering normal operation, data reading, function key settings, and sensor calibration.",
    "2023 EURO SHOP": "2023 EURO SHOP",
    "2023 EURO SHOP 展览项目分享，展示可编程发光LOGO和发光字等创新产品":
        "2023 EURO SHOP exhibition — showcasing programmable illuminated LOGOs, light-up letters, and other innovative products.",
    "纱巾橱窗": "Scarf Window Display",
    "纱巾橱窗项目，结合灯光和展示效果，为品牌店铺打造独特的橱窗展示。":
        "Scarf window display project — combining lighting and display effects to create distinctive window displays for brand stores.",
    "兰蔻模型道具的使用说明": "Lancôme Model Prop User Manual",
    "兰蔻小黑瓶道具的操作说明，包含日常操作、更换瓶子、更换电池等详细步骤":
        "Operating instructions for the Lancôme Genifique prop — includes daily operation, bottle replacement, battery replacement, and other detailed steps.",
    "植村秀 店铺的霓虹灯": "Neon Lights at Shu Uemura Store",
    "植村秀店铺使用的霓虹灯产品，结合LED灯条技术，为品牌店铺打造独特的灯光效果":
        "Neon light products used in Shu Uemura stores, combining LED strip technology to create distinctive lighting effects.",
    "阿迪达斯店铺的渐变灯管和视频播放器": "Gradient Light Tubes & Video Players at Adidas Store",
    "阿迪达斯店铺使用的渐变灯管和视频播放器项目，通过档位开关切换播放视频，相应的LED点亮产品底座":
        "Gradient light tubes and video player project for Adidas stores — video switched via gear selector, with LEDs illuminating the product base.",

    # --- 铝槽 ---
    "线型灯铝槽": "Linear Light Aluminum Profile",
    "导光板铝槽": "Light Guide Plate Profile",
    "层板架铝槽": "Shelf Bracket Profile",
    "固定参数": "Fixed Parameters",
    "可定制的参数": "Customizable Parameters",
    "宽度": "Width",
    "最大宽度": "Max Width",
    "最大高度": "Max Height",
    "最大灯板宽度": "Max Strip Width",
    "散光距离": "Diffusion Distance",
    "提供铝槽或其配件可以单独提供，也可以整体提供。": "Aluminum profiles and accessories can be provided separately or as a complete assembly.",
    "或其配件可以单独提供": "or its accessories can be provided separately",
    "也可以整体提供": "or as a complete assembly",
    "可以配套提供任何类型的": "Can be supplied with any type of",
    "的变压器和": " transformesr and",
    "和接插件": " and connectors",
    "可以连灯带组装好提供": "Can be provided fully assembled with LED strips",
    "提供不同": "Available in different",
    "变压器和": "Transformers and",
    "相关服务": "Related Services",

    # --- 全息投影 ---
    "直径": "Diameter",
    "显示直径": "Display Diameter",
    "分辨率": "Resolution",
    "像素点": "Pixel Pitch",
    "灯珠数": "LED Count",
    "直径方向": "Diameter Direction",
    "控制": "Control",
    "控制平台": "Control Platform",
    "文件格式": "File Format",
    "的文件格式": " file format",
    "可以通过遥控器控制": "Remote controllable",
    "可多台同步": "Multi-unit sync",
    "可无线投屏": "Wireless projection",
    "可遥控": "Remote control",
    "多个设备": "Multiple devices",
    "定时播放": "Scheduled playback",
    "带蓝牙音频": "Bluetooth audio",
    "无线投屏": "Wireless Projection",
    "和": " and ",
    "通过蓝牙播放音频": "Audio via Bluetooth",
    "通过无线投屏发送内容": "Content via wireless projection",
    "通过遥控器控制": "Controlled via remote",

    # --- 技术表格通用 ---
    "电压": "Voltage",
    "输入电压": "Input Voltage",
    "灯珠数": "LED Count",
    "1米的灯珠数量": "LEDs per meter",
    "灯条宽度": "Strip Width",
    "灯珠封装": "LED Package",
    "白光灯珠": "White LEDs",
    "可以定制的色温": "Customizable color temperature",
    "非白光灯珠": "Non-white LEDs",
    "彩色灯珠": "Color LEDs",
    "显色指数": "CRI",
    "白光灯有效": "Applicable to white LEDs",
    "功率": "Power",
    "灯珠功率可以根据需求定制.": "LED power can be customized per requirements.",
    "详细规格参数请查看产品规格书。": "Please refer to the product datasheet for detailed specifications.",
    "规格书 - PDF": "Datasheet - PDF",
    "规格书 - DXF": "Datasheet - DXF",
    "规格书 - STP": "Datasheet - STP",
    "2D 图纸 - DXF": "2D Drawing - DXF",
    "3D 图纸 - STP": "3D Drawing - STP",
    "DRAWING - DXF": "DRAWING - DXF",
    "DataSheet - PDF": "DataSheet - PDF",
    "DataSheet - STP": "DataSheet - STP",
    "定制灯条需要1-2天的交期!": "Custom LED strips require 1-2 days lead time!",
    "固定的参数": "Fixed Parameters",
    "可定制的参数": "Customizable Parameters",
    "相关产品": "Related Products",
    "精选推荐": "Featured Picks",

    # --- 导电槽 ---
    "最大电流": "Max Current",
    "通过的最大电流": "Maximum current rating",
    "正常长度": "Standard Length",
    "常规产品最长3m.": "Standard product max 3m.",
    "颜色": "Color",
    "顶部颜色": "Top Color",
    "白, 黑": "White, Black",
    "最大电压": "Max Voltage",
    "不能用＞220v/110v": "Do NOT use >220V/110V",
    "安装方式": "Mounting Method",
    "选择安装方式": "Select mounting method",
    "螺丝,磁铁,胶带": "Screws, Magnets, Tape",
    "螺丝,胶带": "Screws, Tape",
    "插头": "Plug",
    "插头角度": "Plug Angle",
    "0°, 90°": "0°, 90°",
    "0°": "0°",
    "磁铁": "Magnets",
    "便捷安装": "Easy Installation",
    "精细小巧": "Compact & Slim",

    # --- 兰蔻博客 ---
    "产品标识": "Product Identification",
    "日常操作": "Daily Operation",
    "正常使用": "Normal Use",
    "更换小黑瓶": "Replacing the Genifique Bottle",
    "更换电池": "Replacing the Battery",
    "其他问题": "Other Issues",
    "进入设置界面": "Enter Settings",
    "良品": "Good",
    "不良品": "Defective",
    "正常操作": "Normal Operation",
    "读取SD卡中文件": "Reading Files from SD Card",
    "功能键": "Function Keys",
    "设置值": "Setting Values",
    "定义标准值": "Defining Standard Values",
    "修改计数值": "Modifying Count Values",
    "开机-上电, 输入电压:220V": "Power On — Input Voltage: 220V",
    "放置检测工件, 需要确保底部放平, 背后靠到定位块.":
        "Place the inspection workpiece — ensure the bottom is flat and the back is against the positioning block.",
    "按下绿色按钮, 进行检测, 只有2个结果, Pass 或 NG. 对应的计数值也会更新.":
        "Press the green button to inspect. Two possible results: Pass or NG. The corresponding count will update.",
    "拆开检具后盖, 用一字螺丝刀敲出SD卡.":
        "Open the back cover of the jig; use a flathead screwdriver to pop out the SD card.",
    "从SD中读取数据, 用 EXCEL 打开 csv 文件. 传感器的位置与列的对应关于请参考Excel中黄色行.":
        "Read data from the SD card, open the CSV file with Excel. Refer to the yellow rows in Excel for sensor position and column mapping.",
    "放回SD卡, 检查SD卡是否正常工作": "Reinsert the SD card and verify it is working properly",
    "诊断 -> 硬件 -> SD卡": "Diagnostics → Hardware → SD Card",
    "显示测试的数量, PASSED(合格品):xx, NOGOOD(不良品):xx, TOTAL:xx.":
        "Display test counts: PASSED: xx, NOGOOD: xx, TOTAL: xx.",
    "显示当前传感器的值, 范围:0-1000, 若没有放置工件, 数组为1000.":
        "Display current sensor values, range: 0–1000. If no workpiece is placed, value is 1000.",
    "设置的范围值, +/-0.15 的距离, 建议值为90": "Set range value, ±0.15 distance, recommended value: 90",
    "阈值最小值, 范围在500-700": "Minimum threshold value, range: 500–700",
    "按上下键, 直到出现 时间: Sat. 22 20 和 日期: 2023-08-09":
        "Press up/down keys until Time: Sat. 22 20 and Date: 2023-08-09 appears",
    "按ESC进入": "Press ESC to enter",
    "进入设置内容, 非指定的内容, 请勿随意设置.": "Enter settings. Do not change unspecified items.",
    "设置传感器": "Set Sensors",
    "LOGO! 设置 -> 编程 -> 设置参数": "LOGO! Settings → Programming → Set Parameters",
    "只需要设置 SENSOR – A/B/C/D/E/F 的On,  ∆, 不要设置其他的值.":
        "Only set the On and ∆ values for SENSOR A/B/C/D/E/F. Do not change other values.",
    "查找最小值": "Find Minimum Value",
    "放置好标准块, 对其MinValue, 按下F2": "Place the standard block, align to MinValue, press F2",
    "查找最大值": "Find Maximum Value",
    "放置好标准块, 对其MaxValue, 按下F2": "Place the standard block, align to MaxValue, press F2",
    "计算 ∆": "Calculate ∆",
    "∆ = MaxValue – MinValue": "∆ = MaxValue – MinValue",
    "参考上面的步骤, 设置各个Sensor 的On(MinValue), Delta(∆).":
        "Refer to the steps above to set each sensor's On (MinValue) and Delta (∆).",
    "良品: LOGO! 设置 -> 编程 -> 设置参数 -> PASS_WP_NUM -> Cnt (设置需要的值)":
        "Good: LOGO! Settings → Programming → Set Parameters → PASS_WP_NUM → Cnt (set desired value)",
    "不良品: LOGO! 设置 -> 编程 -> 设置参数 -> NG_WP_NUM -> Cnt (设置需要的值)":
        "Defective: LOGO! Settings → Programming → Set Parameters → NG_WP_NUM → Cnt (set desired value)",
    "可编程发光LOGO, 发光字": "Programmable Illuminated LOGO & Letters",
    "纱巾橱窗": "Scarf Window Display",

    # --- 兰蔻全文 ---
    "非触发状态, 侧板的白色灯光有呈 渐亮->渐暗->渐亮 不断循环.":
        "In non-triggered state, the side panel white light cycles: brighten → dim → brighten continuously.",
    "手放在传感器下方, 贴近人造石台面的位置, 等待1秒钟, 就会有乳液滴到手背上.":
        "Place your hand under the sensor near the stone countertop. Wait 1 second for a lotion drop.",
    "滴液体的过程中, 侧板的灯光为 白色常亮. 乳液滴出后, 灯光回复呼吸渐变的效果":
        "During dispensing, the side panel light stays solid white. After dropping, it returns to breathing gradient.",
    "滴完一滴后, 需要间隔5秒钟, 才可以再次触发.": "After one drop, wait 5 seconds before triggering again.",
    "瓶子中的乳液用完后, 需要更换新的瓶子. 具体步骤如下:":
        "When the lotion bottle is empty, replace with a new bottle. Steps:",
    "A – Logo 盖和瓶帽向上取下来.": "A – Remove the logo cap and bottle cap upwards.",
    "B – 将弯管从空瓶内抽出来.": "B – Pull the curved tube out from the empty bottle.",
    'C – 拧下白色"定制瓶盖", 并将其拧到新的小黑瓶上.':
        'C – Unscrew the white "custom cap" and screw it onto the new Genifique bottle.',
    "D – 将弯管插到小黑瓶内. 需要让玻璃管插到瓶盖的边缘上.":
        "D – Insert the curved tube into the Genifique bottle. The glass tube should rest on the cap edge.",
    "E – 将小黑瓶返回顶部的位置.": "E – Return the Genifique bottle to its top position.",
    "F – 将瓶帽套回去.": "F – Put the bottle cap back on.",
    "G – 将LOGO盖放在顶部. 请注意 LOGO 的角度. 有3组磁铁, 可以微调角度.":
        "G – Place the logo cap on top. Note the logo angle. 3 sets of magnets allow fine angle adjustment.",
    "H – 按压手动开关, 将管中的空气完全排除.": "H – Press the manual switch to completely expel air from the tube.",
    "I – 清洁滴管口处.": "I – Clean the dropper opening.",
    "若遇到需要长时间关机的情形, 请用空瓶并将其装满水, 重复上面的步骤, 将软管内的乳液全部排除. 否则长时间不用, 管内的乳液会凝固. 导致机器无法工作.":
        "If the unit will be unused for an extended period, fill an empty bottle with water and repeat the steps above to flush all lotion from the tubing. Otherwise, dried lotion will clog the tube and render the machine inoperable.",
    "电池充满电后, 可以正常使用2天左右. 视使用的频率, 具体的使用时长不定, 若是侧板看不见灯光, 感应无反应的情况下, 就表明电池的电量用完了. 每套道具都配备了3块电池. 请电池取下后, 请用充电器及时给电池充电. 更换电池的步骤如下:":
        "After a full charge, the battery lasts about 2 days. Actual duration varies by usage frequency. If the side panel light is off and there is no sensor response, the battery is depleted. Each unit comes with 3 batteries. Remove the battery and charge it promptly. Battery replacement steps:",
    "A – 按一下电源开关, 关闭道具的电源. (弹出为关闭)": "A – Press the power switch to turn off the unit. (Popped out = off)",
    "B – 取下 LOGO 盖 及 瓶帽": "B – Remove the logo cap and bottle cap",
    "C – 拔出插在设备的插头, 取下电池. 换回充满电的电池.":
        "C – Unplug the connector from the device, remove the battery, and replace with a fully charged one.",
    "D – 将充电口的插头放在凹槽内.": "D – Place the charging port plug in the recess.",
    "E – 将LOGO盖放在顶部. 请注意 LOGO 的角度. 有3组磁铁, 可以微调角度.":
        "E – Place the logo cap on top. Note the logo angle. 3 sets of magnets allow fine adjustment.",
    "F – 按下电源开关.": "F – Press the power switch.",
    "G – 无电量电池充电备用.": "G – Charge the depleted battery for backup.",
    "电池的电压为12V. 只能用12.6V的充电器为其充电.": "The battery voltage is 12V. Only use a 12.6V charger.",
    "禁止使用其他电压的充电器为其充电.": "Do NOT use chargers with other voltages.",
    "如果您遇到其他问题, 请联系德恩基的项目王经理: 139 1377 5186":
        "For other issues, contact Dengtec Project Manager Mr. Wang: 139 1377 5186",
}


def translate_text(text):
    """翻译文本——先用词典，再用正则"""
    if not text or not isinstance(text, str):
        return text
    result = text

    # 1. 词典匹配（长优先）
    pairs = sorted(T.items(), key=lambda x: -len(x[0]))
    for cn, en in pairs:
        result = result.replace(cn, en)

    # 2. 铝槽描述正则: 宽-NNmm 高-NNmm 散光距离-NNmm 灯板宽-NNmm
    result = re.sub(r'宽-([\d.]+)mm', r'W-\1mm', result)
    result = re.sub(r'高-([\d.]+)mm', r'H-\1mm', result)
    result = re.sub(r'散光距离-([\d.]+)mm', r'Diffusion Distance-\1mm', result)
    result = re.sub(r'灯板宽-([\d.]+)mm', r'Strip Width-\1mm', result)

    # 3. 全息描述正则: ΦNNNmm 全息投影, ...
    result = re.sub(r'Φ([\d.]+)mm\s*全息投影', r'Φ\1mm Holographic Display', result)
    result = re.sub(r', 可无线投屏', r', Wireless projection', result)
    result = re.sub(r', 可多台同步', r', Multi-unit sync', result)
    result = re.sub(r', 带蓝牙音频', r', Bluetooth audio', result)
    # "支持" that hasn't been translated
    result = re.sub(r', 支持', r', Supports', result)
    result = re.sub(r', 不支持', r', Not supported', result)

    # 4. 项目 body 残余: "一致：确保每个 LED 灯珠亮度均匀"
    result = re.sub(r'一致[：:]确保每个\s*LED\s*灯珠亮度均匀', r'Consistency: Ensures each LED has uniform brightness', result)
    result = re.sub(r'动态灯光效果[：:]多种光效模式可切换', r'Dynamic Lighting: Multiple light effect modes switchable', result)
    result = re.sub(r'可定制[：:]根据应用场景灵活调整', r'Customizable: Flexibly adjustable per application scenario', result)
    result = re.sub(r'图案可定制[：:]', r'Custom patterns: ', result)
    result = re.sub(r'可定制尺寸[：:]提供超大[、]大[、]中[、]小多种规格', r'Custom sizes: Available in XL, L, M, S specifications', result)
    result = re.sub(r'可定制[：:]支持多种色温和\s*RGB\s*配置', r'Customizable: Supports various color temperatures and RGB configurations', result)
    result = re.sub(r'多种色温,\s*多种电流', r'Multiple color temperatures, various current ratings', result)
    result = re.sub(r'交期[：:]\s*2\s*周', r'Lead time: 2 weeks', result)
    result = re.sub(r'可定制[：:]支持小批量生产应用', r'Customizable: Supports small-batch production', result)
    result = re.sub(r'塑胶外壳[：:]耐用且轻便', r'Plastic Housing: Durable and lightweight', result)
    # 剩余项目文本
    result = re.sub(r'可定制[：:]可根据需求定制尺寸[、]电压和连接方式', r'Customizable: Size, voltage and connection method per requirements', result)
    result = re.sub(r'可定制的数码管[，,]有不同大小的尺寸[，,]可以控制变化的速度[。.]',
                    r'Customizable digital display tube, available in various sizes with adjustable animation speed.', result)
    result = re.sub(r'可控数码管', r'Controllable Digital Display Tube', result)
    result = re.sub(r'圣诞包装盒', r'Christmas Gift Box', result)
    result = re.sub(r'兰蔻滴液展示道具', r"Lancôme Liquid Dispensing Display Prop", result)
    result = re.sub(r'可以贴片和焊接的微处理器模块单元[，,]非常适合快速开发项目的过程中使用[。.]基于\s*ATmega328\s*处理器[。.]',
                    r'A solderable SMD microprocessor module unit, ideal for rapid project development. Based on the ATmega328 processor.', result)
    result = re.sub(r'可以贴片[：:]', r'Solderable: ', result)
    result = re.sub(r'可以远程更换图片', r'Remote image update supported', result)
    result = re.sub(r'块灯板同步显示动画', r' LED boards display synchronized animation', result)
    result = re.sub(r'在待机状态下显示手图案[，,]\s*一旦消费者将手放在传感器下方[，,]\s*手图案就会变成明星电影[，,]并滴一滴\s*Génifique\s*液体[。.]',
                    r'In standby, displays a hand pattern. Once the consumer places their hand under the sensor, the hand pattern transforms into a star animation and dispenses a drop of Génifique fluid.', result)
    result = re.sub(r'如果温度高达\s*22', r'If temperature reaches 22', result)
    result = re.sub(r'传感器', r'Sensor', result)
    result = re.sub(r'中间灯板', r'Center light board', result)
    result = re.sub(r'一个非常薄的箱子', r'A very slim case', result)
    result = re.sub(r'使得小黑瓶的味道维持在', r' maintains the Genifique bottle at optimal condition', result)
    result = re.sub(r'共使用了', r'Used a total of ', result)
    result = re.sub(r'功率均可按需定制', r'Power can be customized as needed', result)
    result = re.sub(r'任意形状和图案的灯板设计', r'Custom shapes and patterns for light board design', result)
    result = re.sub(r'保证每个灯珠亮度一致', r'Ensures consistent brightness for each LED', result)
    result = re.sub(r'其中中间为', r'The center section is ', result)
    result = re.sub(r'则冷却模块开始工作', r', the cooling module activates', result)
    result = re.sub(r'双向带灯', r'Dual-sided with LEDs', result)
    result = re.sub(r'可以和外接的传感器设备通信', r'Can communicate with external sensor devices', result)

    return result


def translate_body(html):
    """翻译 HTML body——先词典后正则"""
    if not html:
        return html
    # 按长度降序排列
    pairs = sorted(T.items(), key=lambda x: -len(x[0]))
    result = html
    for cn, en in pairs:
        result = result.replace(cn, en)
    # also handle HTML entity variants
    result = result.replace('诊断 -&gt; 硬件 -&gt; SD卡', 'Diagnostics → Hardware → SD Card')
    result = result.replace('LOGO! 设置 -&gt; 编程 -&gt; 设置参数',
                            'LOGO! Settings → Programming → Set Parameters')
    result = result.replace('良品: LOGO! 设置 -&gt; 编程 -&gt; 设置参数 -&gt; PASS_WP_NUM -&gt; Cnt (设置需要的值)',
                            'Good: LOGO! Settings → Programming → Set Parameters → PASS_WP_NUM → Cnt (set desired value)')
    result = result.replace('不良品: LOGO! 设置 -&gt; 编程 -&gt; 设置参数 -&gt; NG_WP_NUM -&gt; Cnt (设置需要的值)',
                            'Defective: LOGO! Settings → Programming → Set Parameters → NG_WP_NUM → Cnt (set desired value)')
    # Non-white LEDs fix
    result = result.replace('非白光灯珠', 'Non-white LEDs')
    # LED description patterns in featured_picks
    result = re.sub(r'灯条 电压\s*(\d+)v\s+(\d+)灯/米\s+板宽(\d+)MM\s+封装(\S+)',
                    r'LED Strip, \1V, \2 LEDs/m, Width \3mm, Package \4', result)
    result = re.sub(r'灯条 电压\s*(\d+)v\s+灯/米\s+Width\s+(\d+)MM\s+灯珠\s+(\S+)',
                    r'LED Strip, \1V, LEDs/m, Width \2mm, LED \3', result)
    # 120灯/米 → 120 LEDs/m
    result = re.sub(r'(\d+)灯/米', r'\1 LEDs/m', result)
    return result


def process_items(items):
    """处理 items 列表"""
    for item in items:
        if not isinstance(item, dict):
            continue
        for key in ['title', 'description', 'category']:
            if key in item and item[key]:
                item[key] = translate_text(str(item[key]))
        if 'tags' in item and item['tags']:
            if isinstance(item['tags'], list):
                item['tags'] = [translate_text(str(t)) for t in item['tags']]
            elif isinstance(item['tags'], str):
                item['tags'] = translate_text(item['tags'])
        if 'body' in item and item['body']:
            item['body'] = translate_body(str(item['body']))
        # featured_picks
        if 'modules' in item:
            for mod in item['modules']:
                if isinstance(mod, dict) and mod.get('type') == 'featured_picks':
                    fd = mod.get('data', {})
                    if fd.get('title'):
                        fd['title'] = translate_text(str(fd['title']))
                    if fd.get('desc'):
                        fd['desc'] = translate_text(str(fd['desc']))
                    for fi in fd.get('items', []) or []:
                        if isinstance(fi, dict):
                            if fi.get('title'):
                                fi['title'] = translate_text(str(fi['title']))
                            if fi.get('desc'):
                                fi['desc'] = translate_text(str(fi['desc']))


def main():
    zh_dir = SITE_DIR / "lang" / "zh-CN" / "data"
    en_dir = SITE_DIR / "lang" / "en" / "data"

    print("=" * 60)
    print("Final detail page translation (from zh-CN source)")
    print("=" * 60)

    for fpath in sorted(zh_dir.glob("*.yaml")):
        fname = fpath.name
        with open(fpath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            continue

        # Deep copy
        out = deepcopy(data)

        # 获取 items
        if isinstance(out, list):
            items = out
        elif isinstance(out, dict):
            if "categories" in out:
                for cat in out["categories"]:
                    if "name" in cat:
                        cat["name"] = translate_text(str(cat["name"]))
            items = out.get("items", [])
        else:
            continue

        process_items(items)

        # Write
        en_path = en_dir / fname
        with open(en_path, "w", encoding="utf-8") as f:
            yaml.dump(out, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        # Count remaining Chinese
        remaining = len(re.findall(r'[一-鿿]', str(out)))
        print(f"  {fname}: {remaining} Chinese chars remaining")

    print("\nDone!")

if __name__ == "__main__":
    main()
