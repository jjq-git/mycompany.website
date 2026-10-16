"""完整的详情页翻译脚本 - 处理所有 data/ 文件的 title, desc, category, tags, body HTML"""
import yaml, re, os, sys
from copy import deepcopy
from pathlib import Path

SITE_DIR = Path(r"f:\dengtec\mycompany.website11\sites\6")

# ============================================================
# 完整的中→英翻译映射
# ============================================================
TRANSLATE = {
    # === 产品分类 ===
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

    # === 项目描述 ===
    "日目 / RIMU": "RIMU",
    "RIMU 是一个模块化的电子设备，它帮助那些不擅长硬件和编程的人轻松使用各种类型的电子设备.":
        "RIMU is a modular electronic device that helps people with no hardware or programming skills use various types of electronic devices with ease.",
    "彩色可编程COB灯板": "Programmable COB LED Board",
    "Chip-On-Board LED光板，可用于标识和字符后面，取代传统的导光板结构，更薄，用途更广。":
        "Chip-On-Board LED panel, used behind logos and lettering to replace traditional light guide plate structures — thinner and more versatile.",
    "可编程发光LOGO/字": "Programmable Illuminated LOGO / Letters",
    "作为展示用的发光字LOGO.": "Illuminated LOGO / letters for display purposes.",
    "P2.5mm 薄膜屏 由控制器和LED网格组成，可以贴在任何表面，展示各种动态效果":
        "P2.5mm flexible LED film screen — consists of a controller and LED grid, can be applied to any surface to display various dynamic effects.",
    "动态灯箱 通过可编程灯珠实现各种动态显示效果 可以无限拼接":
        "Dynamic light box — achieves various dynamic display effects via programmable LEDs, supports unlimited tiling.",
    "磁控灯 由干簧管和LED组成，用于展示柜内的产品照明 门开灯亮 门关灯灭":
        "Magnetic-controlled light — consists of reed switch and LEDs, used for product lighting inside display cabinets. Light on when door opens, off when door closes.",
    "透明屏 展示柜内的透明显示 画面清晰 可层叠使用":
        "Transparent display — clear transparent display inside showcases, stackable.",
    "用于兰蔻, 雅诗兰黛展示道具的电路板, 双面灯等":
        "Circuit boards, double-sided lights for Lancôme and Estée Lauder display props.",

    # === 博客标题 ===
    "检测治具使用说明": "Inspection Jig User Manual",
    "检测治具的详细使用说明，包含正常操作、数据读取、功能键设置和传感器校准等":
        "Detailed user manual for the inspection jig, covering normal operation, data reading, function key settings, and sensor calibration.",
    "2023 EURO SHOP": "2023 EURO SHOP",
    "2023 EURO SHOP 展览项目分享，展示可编程发光LOGO和发光字等创新产品":
        "2023 EURO SHOP exhibition project sharing — showcasing innovative products like programmable illuminated LOGOs and light-up letters.",
    "纱巾橱窗": "Scarf Window Display",
    "纱巾橱窗项目，结合灯光和展示效果，为品牌店铺打造独特的橱窗展示。":
        "Scarf window display project — combining lighting and display effects to create distinctive window displays for brand stores.",
    "兰蔻模型道具的使用说明": "Lancôme Model Prop User Manual",
    "兰蔻小黑瓶道具的操作说明，包含日常操作、更换瓶子、更换电池等详细步骤":
        "Operating instructions for the Lancôme Genifique prop — includes daily operation, bottle replacement, battery replacement, and other detailed steps.",
    "植村秀 店铺的霓虹灯": "Neon Lights at Shu Uemura Store",
    "植村秀店铺使用的霓虹灯产品，结合LED灯条技术，为品牌店铺打造独特的灯光效果":
        "Neon light products used in Shu Uemura stores, combining LED strip technology to create distinctive lighting effects for brand stores.",
    "阿迪达斯店铺的渐变灯管和视频播放器": "Gradient Light Tubes & Video Players at Adidas Store",
    "阿迪达斯店铺使用的渐变灯管和视频播放器项目，通过档位开关切换播放视频，相应的LED点亮产品底座":
        "Gradient light tube and video player project for Adidas stores — video switched via gear selector, with corresponding LEDs illuminating the product base.",

    # === 产品详情 body 技术表格 ===
    # LED灯条通用
    "定制灯条需要1-2天的交期!": "Custom LED strips require 1-2 days lead time!",
    "固定的参数": "Fixed Parameters",
    "可定制的参数": "Customizable Parameters",
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
    "显色指数": "CRI (Color Rendering Index)",
    "白光灯有效": "Applicable to white LEDs",
    "功率": "Power",
    "灯珠功率可以根据需求定制.": "LED power can be customized based on requirements.",
    # 铝槽
    "铝型材尺寸": "Aluminum Profile Dimensions",
    "高": "Height",
    "宽": "Width",
    "散热槽": "Heat Dissipation Slot",
    "铝板厚": "Board Thickness",
    # 全息投影
    "显示尺寸": "Display Size",
    "像素点距": "Pixel Pitch",
    "控制方式": "Control Method",
    "电源输入": "Power Input",
    "外壳材质": "Housing Material",
    "重量": "Weight",
    # 射灯
    "详细规格参数请查看产品规格书。": "Please refer to the product datasheet for detailed specifications.",
    # 线材
    "规格书 - PDF": "Datasheet - PDF",
    "规格书 - DXF": "Datasheet - DXF",
    "规格书 - STP": "Datasheet - STP",
    "2D 图纸 - DXF": "2D Drawing - DXF",
    "3D 图纸 - STP": "3D Drawing - STP",
    "DRAWING - DXF": "DRAWING - DXF",
    "DataSheet - PDF": "DataSheet - PDF",
    "DataSheet - STP": "DataSheet - STP",
    # 导电槽
    "最大电流": "Max Current",
    "通过的最大电流": "Maximum current rating",
    "正常长度": "Standard Length",
    "常规产品最长3m.": "Standard product max length: 3m.",
    "颜色": "Color",
    "顶部颜色": "Top Color",
    "白, 黑": "White, Black",
    "最大电压": "Max Voltage",
    "不能用＞220v/110v": "Do NOT use >220V/110V",
    "安装方式": "Mounting Method",
    "选择安装方式": "Select mounting method",
    "螺丝,磁铁,胶带": "Screws, Magnets, Tape",
    "插头": "Plug",
    "插头角度": "Plug Angle",
    "0°, 90°": "0°, 90°",
    "0°": "0°",
    "磁铁": "Magnets",

    # === 相关产品 ===
    "相关产品": "Related Products",

    # === 产品 item_data description ===
    "灯条 电压 12v 灯/米 Width 5MM 灯珠 2835": "LED Strip, 12V, 120 LEDs/m, Width 5mm, LED 2835",
    "灯条 电压12v 120灯/米 板宽5MM 封装3528": "LED Strip, 12V, 120 LEDs/m, Width 5mm, Package 3528",
    "灯条 电压 12v 灯/米 Width 6MM 灯珠 2835": "LED Strip, 12V, 120 LEDs/m, Width 6mm, LED 2835",
    "灯条 电压 12v 灯/米 Width 8MM 灯珠 2835": "LED Strip, 12V, 120 LEDs/m, Width 8mm, LED 2835",
    "灯条 电压12v 120灯/米 板宽8MM 封装335": "LED Strip, 12V, 120 LEDs/m, Width 8mm, Package 335",
    "灯条 电压 12v 60灯/米 Width 10MM 灯珠 2835": "LED Strip, 12V, 60 LEDs/m, Width 10mm, LED 2835",
    "灯条 电压 12v 灯/米 Width 10MM 灯珠 5050": "LED Strip, 12V, 60 LEDs/m, Width 10mm, LED 5050S",
    "灯条 电压 12v 灯/米 Width 10MM 灯珠 5050S": "LED Strip, 12V, 60 LEDs/m, Width 10mm, LED 5050S",
    "灯条 电压12v 180灯/米 板宽8MM 封装2835": "LED Strip, 12V, 180 LEDs/m, Width 8mm, Package 2835",
    "灯条 电压 24v 120灯/米 Width 5MM 灯珠 2835": "LED Strip, 24V, 120 LEDs/m, Width 5mm, LED 2835",
    "灯条 电压 24v 120灯/米 Width 8MM 灯珠 2835": "LED Strip, 24V, 120 LEDs/m, Width 8mm, LED 2835",
    "灯条 电压 24v 60灯/米 Width 5MM 灯珠 2835": "LED Strip, 24V, 60 LEDs/m, Width 5mm, LED 2835",
    "灯条 电压 24v 60灯/米 Width 8MM 灯珠 2835": "LED Strip, 24V, 60 LEDs/m, Width 8mm, LED 2835",
    "灯条 电压 24v 60灯/米 Width 10MM 灯珠 2835": "LED Strip, 24V, 60 LEDs/m, Width 10mm, LED 2835",
    "灯条 电压 24v 180灯/米 Width 8MM 灯珠 2835": "LED Strip, 24V, 180 LEDs/m, Width 8mm, LED 2835",
    "灯条 电压 24v 灯珠 5050 RGB 60灯/米 60灯/米 Width 10MM": "LED Strip, 24V, 5050 RGB, 60 LEDs/m, Width 10mm",

    # === 铝槽描述 ===
    "铝型材尺寸 宽-15.8mm 高-6.8mm 散热槽-4mm 铝板厚-1.2mm": "Profile dimensions: W-15.8mm, H-6.8mm, heat sink slot-4mm, thickness-1.2mm",
    "铝型材尺寸 宽-24.8mm 高-8mm 散热槽-5.5mm 铝板厚-1.2mm": "Profile dimensions: W-24.8mm, H-8mm, heat sink slot-5.5mm, thickness-1.2mm",
    "铝型材尺寸 宽-22mm 高-11.9mm 散热槽-8.9mm 铝板厚-1.1mm": "Profile dimensions: W-22mm, H-11.9mm, heat sink slot-8.9mm, thickness-1.1mm",

    # === 博客 body HTML 中的文本 ===
    "正常操作": "Normal Operation",
    "读取SD卡中文件": "Reading Files from SD Card",
    "功能键": "Function Keys",
    "设置值": "Setting Values",
    "定义标准值": "Defining Standard Values",
    "修改计数值": "Modifying Count Values",
    "开机-上电, 输入电压:220V": "Power On - Input Voltage: 220V",
    "放置检测工件, 需要确保底部放平, 背后靠到定位块.": "Place the inspection workpiece, ensure the bottom is flat and the back is against the positioning block.",
    "按下绿色按钮, 进行检测, 只有2个结果, Pass 或 NG. 对应的计数值也会更新.": "Press the green button to inspect. Only 2 results: Pass or NG. The corresponding count will also update.",
    "拆开检具后盖, 用一字螺丝刀敲出SD卡.": "Open the back cover, use a flathead screwdriver to pop out the SD card.",
    "从SD中读取数据, 用 EXCEL 打开 csv 文件. 传感器的位置与列的对应关于请参考Excel中黄色行.": "Read data from the SD card, open the CSV file with Excel. Refer to the yellow rows in Excel for sensor position and column mapping.",
    "放回SD卡, 检查SD卡是否正常工作": "Reinsert the SD card and check if it is working properly",
    "诊断 -> 硬件 -> SD卡": "Diagnostics -> Hardware -> SD Card",
    "诊断 -&gt; 硬件 -&gt; SD卡": "Diagnostics -> Hardware -> SD Card",
    "显示测试的数量, PASSED(合格品):xx, NOGOOD(不良品):xx, TOTAL:xx.": "Display test counts: PASSED: xx, NOGOOD: xx, TOTAL: xx.",
    "显示当前传感器的值, 范围:0-1000, 若没有放置工件, 数组为1000.": "Display current sensor values, range: 0-1000. If no workpiece is placed, the value is 1000.",
    "设置的范围值, +/-0.15 的距离, 建议值为90": "Set range value, +/-0.15 distance, recommended value: 90",
    "阈值最小值, 范围在500-700": "Minimum threshold value, range: 500-700",
    "按上下键, 直到出现 时间: Sat. 22 20 和 日期: 2023-08-09": "Press up/down keys until Time: Sat. 22 20 and Date: 2023-08-09 appears",
    "按ESC进入": "Press ESC to enter",
    "进入设置内容, 非指定的内容, 请勿随意设置.": "Enter settings. Do not change unspecified items.",
    "设置传感器": "Set Sensors",
    "LOGO! 设置 -> 编程 -> 设置参数": "LOGO! Settings -> Programming -> Set Parameters",
    "LOGO! 设置 -&gt; 编程 -&gt; 设置参数": "LOGO! Settings -> Programming -> Set Parameters",
    "只需要设置 SENSOR – A/B/C/D/E/F 的On,  ∆, 不要设置其他的值.": "Only set the On and ∆ values for SENSOR A/B/C/D/E/F. Do not change other values.",
    "查找最小值": "Find Minimum Value",
    "放置好标准块, 对其MinValue, 按下F2": "Place the standard block, align to MinValue, press F2",
    "查找最大值": "Find Maximum Value",
    "放置好标准块, 对其MaxValue, 按下F2": "Place the standard block, align to MaxValue, press F2",
    "计算 ∆": "Calculate ∆",
    "∆ = MaxValue – MinValue": "∆ = MaxValue – MinValue",
    "参考上面的步骤, 设置各个Sensor 的On(MinValue), Delta(∆).": "Refer to the steps above, set each sensor's On (MinValue) and Delta (∆).",
    "良品: LOGO! 设置 -> 编程 -> 设置参数 -> PASS_WP_NUM -> Cnt (设置需要的值)": "Good: LOGO! Settings -> Programming -> Set Parameters -> PASS_WP_NUM -> Cnt (set desired value)",
    "不良品: LOGO! 设置 -> 编程 -> 设置参数 -> NG_WP_NUM -> Cnt (设置需要的值)": "Defective: LOGO! Settings -> Programming -> Set Parameters -> NG_WP_NUM -> Cnt (set desired value)",
    "良品: LOGO! 设置 -&gt; 编程 -&gt; 设置参数 -&gt; PASS_WP_NUM -&gt; Cnt (设置需要的值)": "Good: LOGO! Settings -> Programming -> Set Parameters -> PASS_WP_NUM -> Cnt (set desired value)",
    "不良品: LOGO! 设置 -&gt; 编程 -&gt; 设置参数 -&gt; NG_WP_NUM -&gt; Cnt (设置需要的值)": "Defective: LOGO! Settings -> Programming -> Set Parameters -> NG_WP_NUM -> Cnt (set desired value)",
    # 兰蔻
    "产品标识": "Product Identification",
    "日常操作": "Daily Operation",
    "正常使用": "Normal Use",
    "非触发状态, 侧板的白色灯光有呈 渐亮->渐暗->渐亮 不断循环.": "In non-triggered state, the side panel white light cycles: fade-in -> fade-out -> fade-in.",
    "手放在传感器下方, 贴近人造石台面的位置, 等待1秒钟, 就会有乳液滴到手背上.": "Place your hand under the sensor, close to the artificial stone surface. Wait 1 second, and lotion will drop onto the back of your hand.",
    "滴液体的过程中, 侧板的灯光为 白色常亮. 乳液滴出后, 灯光回复呼吸渐变的效果": "During dispensing, the side panel light stays solid white. After the lotion drops, the light returns to the breathing gradient effect.",
    "滴完一滴后, 需要间隔5秒钟, 才可以再次触发.": "After one drop, wait 5 seconds before triggering again.",
    "非触发状态, 侧板的白色灯光有呈 渐亮-&gt;渐暗-&gt;渐亮 不断循环.": "In non-triggered state, the side panel white light cycles: fade-in -> fade-out -> fade-in.",
    "手放在传感器下方, 贴近人造石台面的位置, 等待1秒钟, 就会有乳液滴到手背上.": "Place your hand under the sensor, close to the artificial stone surface. Wait 1 second, and lotion will drop onto the back of your hand.",
    "更换小黑瓶": "Replacing the Genifique Bottle",
    "更换电池": "Replacing the Battery",
    "其他问题": "Other Issues",
    "瓶子中的乳液用完后, 需要更换新的瓶子. 具体步骤如下:": "When the lotion bottle is empty, replace with a new bottle. Steps:",
    "A – Logo 盖和瓶帽向上取下来.": "A - Remove the logo cap and bottle cap upwards.",
    "B – 将弯管从空瓶内抽出来.": "B - Pull the curved tube out from the empty bottle.",
    'C – 拧下白色"定制瓶盖", 并将其拧到新的小黑瓶上.': 'C - Unscrew the white custom cap and screw it onto the new Genifique bottle.',
    "D – 将弯管插到小黑瓶内. 需要让玻璃管插到瓶盖的边缘上.": "D - Insert the curved tube into the Genifique bottle. The glass tube should rest on the edge of the cap.",
    "E – 将小黑瓶返回顶部的位置.": "E - Return the Genifique bottle to the top position.",
    "F – 将瓶帽套回去.": "F - Put the bottle cap back on.",
    "G – 将LOGO盖放在顶部. 请注意 LOGO 的角度. 有3组磁铁, 可以微调角度.": "G - Place the logo cap on top. Note the logo angle. There are 3 sets of magnets for fine-tuning.",
    "H – 按压手动开关, 将管中的空气完全排除.": "H - Press the manual switch to completely expel air from the tube.",
    "I – 清洁滴管口处.": "I - Clean the dropper opening.",
    "若遇到需要长时间关机的情形, 请用空瓶并将其装满水, 重复上面的步骤, 将软管内的乳液全部排除. 否则长时间不用, 管内的乳液会凝固. 导致机器无法工作.": "If the unit will be unused for an extended period, use an empty bottle filled with water and repeat the steps above to flush all lotion from the tubing. Otherwise, the lotion will solidify in the tube and render the machine inoperable.",
    "电池充满电后, 可以正常使用2天左右. 视使用的频率, 具体的使用时长不定, 若是侧板看不见灯光, 感应无反应的情况下, 就表明电池的电量用完了. 每套道具都配备了3块电池. 请电池取下后, 请用充电器及时给电池充电. 更换电池的步骤如下:": "After a full charge, the battery lasts about 2 days. Actual duration depends on usage frequency. If the side panel light is off and there is no response, the battery is depleted. Each unit comes with 3 batteries. Remove the battery and charge it promptly. Battery replacement steps:",
    "A – 按一下电源开关, 关闭道具的电源. (弹出为关闭)": "A - Press the power switch to turn off the unit. (Popped out = off)",
    "B – 取下 LOGO 盖 及 瓶帽": "B - Remove the logo cap and bottle cap",
    "C – 拔出插在设备的插头, 取下电池. 换回充满电的电池.": "C - Unplug the connector, remove the battery, and replace with a fully charged battery.",
    "D – 将充电口的插头放在凹槽内.": "D - Place the charging port plug in the recess.",
    "E – 将LOGO盖放在顶部. 请注意 LOGO 的角度. 有3组磁铁, 可以微调角度.": "E - Place the logo cap on top. Note the logo angle. There are 3 sets of magnets for fine-tuning.",
    "F – 按下电源开关.": "F - Press the power switch.",
    "G – 无电量电池充电备用.": "G - Charge the depleted battery for backup.",
    "电池的电压为12V. 只能用12.6V的充电器为其充电.": "The battery voltage is 12V. Only use a 12.6V charger.",
    "禁止使用其他电压的充电器为其充电.": "Do NOT use chargers with other voltages.",
    "如果您遇到其他问题, 请联系德恩基的项目王经理: 139 1377 5186": "If you encounter other issues, please contact Dengtec Project Manager Mr. Wang: 139 1377 5186",
    # 2023 EURO SHOP
    "可编程发光LOGO, 发光字": "Programmable Illuminated LOGO & Letters",
    # 纱巾橱窗
    "纱巾橱窗": "Scarf Window Display",
    # 植村秀
    "植村秀 店铺的霓虹灯": "Neon Lights at Shu Uemura Store",
    # 阿迪达斯
    "阿迪达斯店铺的渐变灯管和视频播放器": "Gradient Light Tubes & Video Players at Adidas Store",
    # === 全息投影 body ===
    "显示区域": "Display Area",
    "亮度": "Brightness",
    "像素间距": "Pixel Pitch",
    "刷新率": "Refresh Rate",
    "可视角度": "Viewing Angle",
    "通信接口": "Communication Interface",
    "工作温度": "Operating Temperature",
    "存储温度": "Storage Temperature",
    "工作湿度": "Operating Humidity",
    "防护等级": "Protection Rating",
    "整机功率": "Power Consumption",
    "整机尺寸": "Dimensions",
    "整机重量": "Net Weight",
    "包装尺寸": "Package Dimensions",
    "包装重量": "Gross Weight",
    "支持": "Supported",
    "不支持": "Not Supported",

    # === 项目 body 中的文本 ===
    "主机和模块之间采用了磁铁和卡扣的结构, 能够非常轻易地进行装配和卸载. 4.3英寸的触摸屏, 能够非常容易的实现和设备进行信息交互.": "The main unit and modules use a magnetic snap-fit structure, allowing very easy assembly and disassembly. The 4.3-inch touchscreen makes information interaction with the device extremely simple and intuitive.",
    "主机和模块之间采用磁铁和卡扣的连接方式，能够实现快速且便捷的装配与卸载。4.3英寸的触摸屏使得与设备的信息交互变得极为简单和直观。": "The main unit and modules use magnetic snap-fit connections, enabling fast and convenient assembly and disassembly. The 4.3-inch touchscreen makes information interaction with the device extremely simple and intuitive.",

    # === 项目 body ===
    "发光面的每个点都可以精准控制其颜色及变化过程": "Each point on the luminous surface can precisely control its color and transition process",
    "可以批量生成": "Can be mass-produced",
    "可和外部传感器联动": "Can be linked with external sensors",
    "可无线更新动态效果": "Dynamic effects can be updated wirelessly",
    "定制交期: 2周": "Custom order lead time: 2 weeks",
    "灯珠封装: 5050, 3528, 1515等": "LED package: 5050, 3528, 1515, etc.",
    "颜色: RGB, 白色": "Color: RGB, White",
    "颜色: RGB, 白色&nbsp;": "Color: RGB, White",
}


# ============================================================
# 数字描述的正则生成（处理如 "灯条 电压 24v 120灯/米 Width 5MM 灯珠 2835" 这类模式化描述）
# ============================================================
def translate_description(desc):
    """翻译产品描述，处理模式化文本"""
    if not desc:
        return desc
    # 精确匹配
    if desc in TRANSLATE:
        return TRANSLATE[desc]

    # 尝试模式替换
    result = desc

    # 通用模式
    patterns = [
        (r'灯条 电压\s*(\d+)v\s+(\d+)灯/米\s+Width\s+(\d+)MM\s+灯珠\s+(\S+)',
         r'LED Strip, \1V, \2 LEDs/m, Width \3mm, LED \4'),
        (r'灯条 电压(\d+)v\s+(\d+)灯/米\s+板宽(\d+)MM\s+封装(\S+)',
         r'LED Strip, \1V, \2 LEDs/m, Width \3mm, Package \4'),
        (r'铝型材尺寸 宽-([\d.]+)mm 高-([\d.]+)mm 散热槽-([\d.]+)mm 铝板厚-([\d.]+)mm',
         r'Profile dimensions: W-\1mm, H-\2mm, heat sink slot-\3mm, thickness-\4mm'),
        (r'直径(\d+)mm 全息投影, (.*)',
         r'\1mm diameter holographic display, \2'),
        (r'(\d+)x(\d+)mm 全息投影, (.*)',
         r'\1x\2mm holographic display, \2'),
    ]

    for pattern, replacement in patterns:
        new_result = re.sub(pattern, replacement, result)
        if new_result != result:
            return new_result

    return result


# ============================================================
# HTML body 翻译
# ============================================================
def translate_html_body(body):
    """翻译 HTML body 中的中文文本"""
    if not body:
        return body

    result = body

    # 用字典中的每个中文→英文对进行替换
    # 按长度降序排列，确保长匹配优先
    pairs = sorted(TRANSLATE.items(), key=lambda x: -len(x[0]))
    for cn, en in pairs:
        result = result.replace(cn, en)

    return result


# ============================================================
# 翻译标签
# ============================================================
def translate_tags(tags):
    """翻译标签列表"""
    if not tags:
        return tags
    if isinstance(tags, str):
        return TRANSLATE.get(tags, tags)
    return [TRANSLATE.get(str(t), str(t)) if t in TRANSLATE else str(t) for t in tags]


# ============================================================
# 翻译单个 item
# ============================================================
def translate_item(item):
    """翻译一个数据项的所有字段"""
    if not isinstance(item, dict):
        return item

    result = deepcopy(item)

    # title - 产品型号保持原样，中文标题翻译
    if 'title' in result and result['title']:
        title = str(result['title'])
        if title in TRANSLATE:
            result['title'] = TRANSLATE[title]

    # description
    if 'description' in result and result['description']:
        desc = str(result['description'])
        if desc in TRANSLATE:
            result['description'] = TRANSLATE[desc]
        else:
            result['description'] = translate_description(desc)

    # category
    if 'category' in result and result['category']:
        cat = str(result['category'])
        if cat in TRANSLATE:
            result['category'] = TRANSLATE[cat]

    # tags
    if 'tags' in result and result['tags']:
        result['tags'] = translate_tags(result['tags'])

    # body - HTML 富文本
    if 'body' in result and result['body']:
        result['body'] = translate_html_body(str(result['body']))

    # featured_picks items (在 modules 中)
    if 'modules' in result:
        for mod in result['modules']:
            if isinstance(mod, dict) and mod.get('type') == 'featured_picks' and 'data' in mod:
                fd = mod['data']
                if 'title' in fd and fd['title']:
                    fd['title'] = TRANSLATE.get(str(fd['title']), str(fd['title']))
                if 'desc' in fd and fd['desc']:
                    fd['desc'] = translate_description(str(fd['desc']))
                if 'items' in fd:
                    for fi in fd['items']:
                        if isinstance(fi, dict):
                            if 'title' in fi and fi['title']:
                                fi['title'] = fi['title']  # 产品型号不变
                            if 'desc' in fi and fi['desc']:
                                fi['desc'] = translate_description(str(fi['desc']))

    return result


# ============================================================
# 翻译并写入 data 文件
# ============================================================
def translate_data_file(filename):
    """翻译一个数据文件并写回 en 目录"""
    zh_path = SITE_DIR / "lang" / "zh-CN" / "data" / filename
    en_path = SITE_DIR / "lang" / "en" / "data" / filename

    with open(zh_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        return

    # 处理 categories
    if isinstance(data, dict) and "categories" in data:
        for cat in data["categories"]:
            if "name" in cat:
                cat["name"] = TRANSLATE.get(str(cat["name"]), str(cat["name"]))

    # 获取 items
    if isinstance(data, list):
        items = data
        wrapper = None
    elif isinstance(data, dict):
        items = data.get("items", [])
        wrapper = data
    else:
        return

    # 翻译每个 item
    translated_items = [translate_item(it) for it in items]

    # 重建数据
    if wrapper is not None:
        wrapper["items"] = translated_items
        output_data = wrapper
    else:
        output_data = translated_items

    # 写入
    with open(en_path, "w", encoding="utf-8") as f:
        yaml.dump(output_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"  [OK] {filename} ({len(items)} items)")


# ============================================================
# 主流程
# ============================================================
def main():
    data_dir = SITE_DIR / "lang" / "zh-CN" / "data"
    files = sorted([f.name for f in data_dir.glob("*.yaml")])

    print("=" * 60)
    print("Translating data files (detail pages)")
    print("=" * 60)

    for filename in files:
        translate_data_file(filename)

    print("\nAll detail page translations complete!")
    print("Check: http://localhost:5000/preview/6/en/")

if __name__ == "__main__":
    main()
