"""YAML-safe cleanup: parse → modify → dump (不会破坏结构)"""
import yaml, re, os
from pathlib import Path

SITE_DIR = Path(r"f:\dengtec\mycompany.website11\sites\6")

REPLACEMENTS = [
    # --- 铝槽 ---
    ("灯板", "Strip"),
    ("灯带", "LED Strip"),
    ("灯珠到灯罩的距离", "Distance from LED to Cover"),
    ("高度", "Height"),
    ("最大高度", "Max Height"),
    ("最大宽度", "Max Width"),
    ("最大灯板宽度", "Max Strip Width"),
    ("线型灯铝槽", "Linear Light Aluminum Profile"),
    ("导光板铝槽", "Light Guide Plate Profile"),
    ("层板架铝槽", "Shelf Bracket Profile"),
    ("固定参数", "Fixed Parameters"),
    ("可定制的参数", "Customizable Parameters"),
    ("提供铝槽或其配件可以单独提供，也可以整体提供。", ""),
    ("或其配件可以单独提供", "or its accessories separately"),
    ("也可以整体提供", "or as a complete assembly"),
    ("可以配套提供任何类型的", "Available with any type of"),
    ("的变压器和", " transformers and"),
    ("和接插件", " and connectors"),
    ("可以连灯带组装好提供", "Available fully assembled with LED strips"),
    ("提供不同", "Available in various"),
    ("变压器和", "Transformers and"),
    ("相关服务", "Related Services"),

    # --- 全息投影 ---
    ("遥控", "Remote"),
    ("同步", "Sync"),
    ("TF 卡", "TF Card"),
    ("TF 容量", "TF Capacity"),
    ("定时", "Timer"),
    ("直径", "Diameter"),
    ("显示直径", "Display Diameter"),
    ("分辨率", "Resolution"),
    ("像素点", "Pixel Pitch"),
    ("灯珠数", "LED Count"),
    ("直径方向", "Diameter Direction"),
    ("控制", "Control"),
    ("控制平台", "Control Platform"),
    ("文件格式", "File Format"),
    ("的文件格式", " file format"),
    ("通过遥控器控制", "Remote controllable"),
    ("可多台同步", "Multi-unit sync"),
    ("可无线投屏", "Wireless projection"),
    ("可遥控", "Remote control"),
    ("多个设备", "Multiple devices"),
    ("定时播放", "Scheduled playback"),
    ("带蓝牙音频", "Bluetooth audio"),
    ("蓝牙音频", "Bluetooth Audio"),
    ("通过蓝牙播放音频", "Audio via Bluetooth"),
    ("通过无线投屏发送内容", "Content via wireless projection"),
    ("通过遥控器控制", "Remote controllable"),
    ("支持的文件格式", "Supported file formats"),

    # --- LED灯条 ---
    ("灯条", "LED Strip"),
    ("灯珠", "LED"),
    ("板宽", "Width"),
    ("封装", "Package"),
    ("精选推荐", "Featured Picks"),

    # --- 导电槽 ---
    ("便捷安装", "Easy Installation"),
    ("精细小巧", "Compact & Slim"),
    ("最大电流", "Max Current"),
    ("通过的最大电流", "Max current rating"),
    ("正常长度", "Standard Length"),
    ("常规产品最长3m.", "Standard product max 3m."),
    ("顶部颜色", "Top Color"),
    ("白, 黑", "White, Black"),
    ("最大电压", "Max Voltage"),
    ("不能用＞220v/110v", "Do NOT use >220V/110V"),
    ("安装方式", "Mounting Method"),
    ("选择安装方式", "Select mounting method"),
    ("螺丝,磁铁,胶带", "Screws, Magnets, Tape"),
    ("螺丝,胶带", "Screws, Tape"),
    ("插头", "Plug"),
    ("插头角度", "Plug Angle"),
    ("0°, 90°", "0°, 90°"),
    ("0°", "0°"),
    ("磁铁", "Magnets"),

    # --- 博客 兰蔻 ---
    ("非触发状态", "In non-triggered state"),
    ("侧板的白色", "the side panel white"),
    ("不断循环", "cycling continuously"),
    ("可以Normal Use2天左右", "lasts about 2 days"),
    ("请用充电器及时给电池充电", "charge it promptly"),
    ("设置需要的值", "set desired value"),
    ("有呈 渐亮->渐暗->渐亮", " cycles: fade-in to fade-out to fade-in"),
    ("产品标识", "Product Identification"),
    ("日常操作", "Daily Operation"),
    ("正常使用", "Normal Use"),
    ("更换小黑瓶", "Replacing the Genifique Bottle"),
    ("更换电池", "Replacing the Battery"),
    ("其他问题", "Other Issues"),
    ("进入设置界面", "Enter Settings"),
    ("良品", "Good"),
    ("不良品", "Defective"),
    ("正常操作", "Normal Operation"),
    ("读取SD卡中文件", "Reading Files from SD Card"),
    ("功能键", "Function Keys"),
    ("设置值", "Setting Values"),
    ("定义标准值", "Defining Standard Values"),
    ("修改计数值", "Modifying Count Values"),

    # --- 博客 body ---
    ("开机-上电, 输入电压:220V", "Power On — Input Voltage: 220V"),
    ("放置检测工件, 需要确保底部放平, 背后靠到定位块.",
     "Place the inspection workpiece — ensure the bottom is flat and back is against the positioning block."),
    ("按下绿色按钮, 进行检测, 只有2个结果, Pass 或 NG. 对应的计数值也会更新.",
     "Press the green button to inspect. Two results: Pass or NG. Count will update accordingly."),
    ("拆开检具后盖, 用一字螺丝刀敲出SD卡.",
     "Open the back cover; use a flathead screwdriver to pop out the SD card."),
    ("从SD中读取数据, 用 EXCEL 打开 csv 文件. 传感器的位置与列的对应关于请参考Excel中黄色行.",
     "Read data from SD card, open CSV with Excel. Refer to yellow rows for sensor-column mapping."),
    ("放回SD卡, 检查SD卡是否正常工作", "Reinsert SD card and verify proper operation"),
    ("诊断 -> 硬件 -> SD卡", "Diagnostics → Hardware → SD Card"),
    ("显示测试的数量, PASSED(合格品):xx, NOGOOD(不良品):xx, TOTAL:xx.",
     "Display test counts: PASSED: xx, NOGOOD: xx, TOTAL: xx."),
    ("显示当前传感器的值, 范围:0-1000, 若没有放置工件, 数组为1000.",
     "Display current sensor values, range: 0–1000. No workpiece = 1000."),
    ("设置的范围值, +/-0.15 的距离, 建议值为90", "Set range value, +/-0.15 distance, recommended: 90"),
    ("阈值最小值, 范围在500-700", "Minimum threshold, range: 500–700"),
    ("按上下键, 直到出现 时间: Sat. 22 20 和 日期: 2023-08-09",
     "Press up/down keys until Time: Sat. 22 20 and Date: 2023-08-09"),
    ("按ESC进入", "Press ESC to enter"),
    ("进入设置内容, 非指定的内容, 请勿随意设置.", "Enter settings. Do not change unspecified items."),
    ("设置传感器", "Set Sensors"),
    ("LOGO! 设置 -> 编程 -> 设置参数", "LOGO! Settings → Programming → Set Parameters"),
    ("只需要设置 SENSOR – A/B/C/D/E/F 的On,  ∆, 不要设置其他的值.",
     "Only set On and ∆ for SENSOR A/B/C/D/E/F. Do not change other values."),
    ("查找最小值", "Find Minimum Value"),
    ("放置好标准块, 对其MinValue, 按下F2", "Place standard block, align to MinValue, press F2"),
    ("查找最大值", "Find Maximum Value"),
    ("放置好标准块, 对其MaxValue, 按下F2", "Place standard block, align to MaxValue, press F2"),
    ("计算 ∆", "Calculate ∆"),
    ("∆ = MaxValue – MinValue", "∆ = MaxValue – MinValue"),
    ("参考上面的步骤, 设置各个Sensor 的On(MinValue), Delta(∆).",
     "Set each sensor's On (MinValue) and Delta (∆) per steps above."),
    ("良品: LOGO! 设置 -> 编程 -> 设置参数 -> PASS_WP_NUM -> Cnt (设置需要的值)",
     "Good: LOGO! Settings → Programming → Set Parameters → PASS_WP_NUM → Cnt (set value)"),
    ("不良品: LOGO! 设置 -> 编程 -> 设置参数 -> NG_WP_NUM -> Cnt (设置需要的值)",
     "Defective: LOGO! Settings → Programming → Set Parameters → NG_WP_NUM → Cnt (set value)"),
    ("可编程发光LOGO, 发光字", "Programmable Illuminated LOGO & Letters"),
    ("纱巾橱窗", "Scarf Window Display"),

    # --- 兰蔻全文 ---
    ("非触发状态, 侧板的白色灯光有呈 渐亮->渐暗->渐亮 不断循环.",
     "In non-triggered state, the side panel white light cycles: brighten→dim→brighten continuously."),
    ("手放在传感器下方, 贴近人造石台面的位置, 等待1秒钟, 就会有乳液滴到手背上.",
     "Place hand under sensor near the stone countertop. Wait 1 second for a lotion drop."),
    ("滴液体的过程中, 侧板的灯光为 白色常亮. 乳液滴出后, 灯光回复呼吸渐变的效果",
     "During dispensing, side panel stays solid white. After dropping, returns to breathing gradient."),
    ("滴完一滴后, 需要间隔5秒钟, 才可以再次触发.",
     "After one drop, wait 5 seconds before triggering again."),
    ("瓶子中的乳液用完后, 需要更换新的瓶子. 具体步骤如下:",
     "When the lotion bottle is empty, replace with a new bottle. Steps:"),
    ("A – Logo 盖和瓶帽向上取下来.", "A – Remove the logo cap and bottle cap upwards."),
    ("B – 将弯管从空瓶内抽出来.", "B – Pull the curved tube out from the empty bottle."),
    ("C – 拧下白色\"定制瓶盖\", 并将其拧到新的小黑瓶上.",
     "C – Unscrew the white \"custom cap\" and screw it onto the new Genifique bottle."),
    ("D – 将弯管插到小黑瓶内. 需要让玻璃管插到瓶盖的边缘上.",
     "D – Insert the curved tube into the Genifique bottle. Glass tube should rest on cap edge."),
    ("E – 将小黑瓶返回顶部的位置.", "E – Return the Genifique bottle to its top position."),
    ("F – 将瓶帽套回去.", "F – Put the bottle cap back on."),
    ("G – 将LOGO盖放在顶部. 请注意 LOGO 的角度. 有3组磁铁, 可以微调角度.",
     "G – Place the logo cap on top. Note logo angle. 3 magnets allow fine adjustment."),
    ("H – 按压手动开关, 将管中的空气完全排除.",
     "H – Press manual switch to completely expel air from the tube."),
    ("I – 清洁滴管口处.", "I – Clean the dropper opening."),
    ("若遇到需要长时间关机的情形, 请用空瓶并将其装满水, 重复上面的步骤, 将软管内的乳液全部排除. 否则长时间不用, 管内的乳液会凝固. 导致机器无法工作.",
     "If the unit will be unused for an extended period, fill an empty bottle with water and repeat the steps above to flush all lotion from the tubing. Otherwise, dried lotion will clog the tube and render the machine inoperable."),
    ("电池充满电后, 可以正常使用2天左右. 视使用的频率, 具体的使用时长不定, 若是侧板看不见灯光, 感应无反应的情况下, 就表明电池的电量用完了. 每套道具都配备了3块电池. 请电池取下后, 请用充电器及时给电池充电. 更换电池的步骤如下:",
     "After a full charge, the battery lasts about 2 days. Actual duration varies by usage frequency. If side panel light is off and there is no sensor response, the battery is depleted. Each unit comes with 3 batteries. Remove and charge it promptly. Battery replacement steps:"),
    ("A – 按一下电源开关, 关闭道具的电源. (弹出为关闭)",
     "A – Press the power switch to turn off the unit. (Popped out = off)"),
    ("B – 取下 LOGO 盖 及 瓶帽", "B – Remove the logo cap and bottle cap"),
    ("C – 拔出插在设备的插头, 取下电池. 换回充满电的电池.",
     "C – Unplug connector from device, remove battery, replace with fully charged one."),
    ("D – 将充电口的插头放在凹槽内.", "D – Place charging port plug in the recess."),
    ("G – 无电量电池充电备用.", "G – Charge depleted battery for backup."),
    ("电池的电压为12V. 只能用12.6V的充电器为其充电.",
     "Battery voltage is 12V. Only use a 12.6V charger."),
    ("禁止使用其他电压的充电器为其充电.", "Do NOT use chargers with other voltages."),
    ("如果您遇到其他问题, 请联系德恩基的项目王经理: 139 1377 5186",
     "For other issues, contact Dengtec Project Manager Mr. Wang: 139 1377 5186"),

    # --- 项目 ---
    ("主要特征", "Key Features"),
    ("特点", "Features"),
    ("项目亮点", "Project Highlights"),
    ("项目特点", "Project Features"),
    ("中间灯板", "Center light board"),
    ("左右灯板", "Left/right light boards"),
    ("左右各", "each side"),
    ("亮度一致", "Brightness consistency"),
    ("任意形状", "Custom shapes"),
    ("白色", "White"),
    ("结构设计", "Structural Design"),
    ("设计", "Design"),
    ("展示道具", "Display Prop"),
    ("自动滴液模型", "Auto-Drip Model"),
    ("自动滴液", "Auto-Drip"),
    ("透明的产品模型", "Transparent Product Model"),
    ("转横流的供电方式", "constant current conversion power supply"),
    ("转横流", "constant current conversion"),
    ("将恒定", "Converts constant"),
    ("多种色温", "Multiple color temperatures"),
    ("支持多种色温", "Supports multiple color temperatures"),
    ("防水密封处理", "Waterproof sealing treatment"),
    ("品牌", "Brand"),
    ("莲花", "Lotus"),
    ("日期", "Date"),
    ("开发周期", "Development Cycle"),
    ("动态", "Dynamic"),
    ("效果", "Effect"),
    ("应用", "Application"),
    ("尺寸", "Size"),
    ("支持", "Supports"),
    ("材料", "Material"),
    ("配置", "Configuration"),
    ("类型", "Type"),
    ("驱动", "Driver"),
    ("稳定", "Stable"),
    ("照明", "Lighting"),
    ("视频", "Video"),
    ("音乐", "Music"),
    ("声音", "Sound"),
    ("处理器", "Processor"),
    ("单元", "Unit"),
    ("交期", "Lead Time"),
    ("定制", "Custom"),
    ("定制的", "custom"),
    ("按需定制", "Customized on demand"),
    ("可定制", "Customizable"),
    ("传感器", "Sensor"),
    ("模块", "Module"),
    ("电源", "Power Supply"),
    ("导光板", "Light guide plate"),
    ("灯珠", "LED"),
    ("灯板", "Light Board"),
    ("控制器", "Controller"),
    ("定制交期", "Custom order lead time"),
    ("灯灯接头处发光", "LED connector illuminated"),
    ("灯板设计", "light board design"),
    ("塑胶", "Plastic"),
    ("塑胶外壳", "Plastic housing"),
    ("磁性", "Magnetic"),
    ("颜色", "Color"),
    ("电流", "Current"),
    ("多种电流", "Multiple current ratings"),
    ("转速", "Speed"),
    ("功率", "Power"),
    ("场景", "Scene"),
    ("图案", "Pattern"),
    ("数码管", "Digital tube"),
    ("数码管显示", "Digital tube display"),
    ("播放器", "Player"),
    ("小米", "Xiaomi"),
    ("雅诗兰黛", "Estée Lauder"),
    ("兰蔻", "Lancôme"),
    ("美诺", "Miele"),
    ("芝华士", "Chivas"),
    ("抛光", "Polishing"),
    ("电镀等工艺", "electroplating etc."),
    ("用铝型材", "Using aluminum profiles"),
    ("铝型材开发设计", "Aluminum profile development design"),
    ("轻盈便携的包装结构", "Lightweight portable packaging"),
    ("小巧尺寸", "Compact size"),
    ("接口丰富", "Rich interfaces"),
    ("易于集成", "Easy to integrate"),
    ("设计方便嵌入各类产品", "Designed for integration into various products"),
    ("满足快速开发需求", "Meets rapid development needs"),
    ("焊接容易", "Easy to solder"),
    ("焊接的微处理器", "solderable microprocessor"),
    ("可以贴片", "Solderable"),
    ("可以批量生成", "Mass-producible"),
    ("可无线更新动态效果", "Wireless dynamic effect updates"),
    ("可以远程更换图片", "Remote image update"),
    ("远程更换视频", "Remote video update"),
    ("可以记录操作信息", "Can record operation data"),
    ("可以驱动多个的", "Can drive multiple"),
    ("和外接的", "and external"),
    ("设备通信", "device communication"),
    ("外接的", "external"),
    ("可以和外接的", "Can connect to external"),
    ("传感器的设备通信", "sensor devices"),
    ("则可以", "then"),
    ("则冷却", "the cooling"),
    ("冷却模块开始工作", "cooling module activates"),
    ("内置高品质音频播放", "Built-in high-quality audio playback"),
    ("作为层板信息条", "As shelf info strip"),
    ("双向带灯", "Dual-sided with LEDs"),
    ("发光面的每个点都可以精准", "Each point on the luminous surface precisely"),
    ("及变化过程", " and transition process"),
    ("变化的速度", "animation speed"),
    ("可定制的数码管", "Customizable digital display tube"),
    ("可定制尺寸", "Custom sizes"),
    ("圣诞包装盒", "Christmas Gift Box"),
    ("可控数码管", "Controllable Digital Display Tube"),
    ("播放视频动画", "Play video animation"),
    ("播放动态视频", "Play dynamic video"),
    ("以播放图片", "to display images"),
    ("通过旋钮选择要显示的图片信息", "Select image via rotary knob"),
    ("数码管显示", "digital tube display"),
    ("常态显示", "Normal display"),
    ("触发后", "After triggering"),
    ("开盒自动触发", "Auto-triggered on box opening"),
    ("滴出精华液", "dispenses essence fluid"),
    ("限制瓶子里精华液的温度在", "keeps essence fluid temperature at"),
    ("摄氏", "°C"),
    ("摄氏度以下", "below °C"),
    ("特别适合空间受限的场合", "especially suitable for space-constrained applications"),
    ("特别适应空间小的情形", "especially suitable for tight spaces"),
    ("适用于长时间运行的灯具场景", "suitable for long-running lighting scenarios"),
    ("连接多种输入输出", "Connects multiple I/O"),
    ("设计者", "Designer"),
    ("转换为", "Converts to"),
    ("开发生产了多款", "developed and produced multiple models of"),
    ("我们为", "We developed for"),
    ("对应的产品底部发光", "corresponding product base illuminates"),
    ("它包括动态光效", "including dynamic light effects"),
    ("适用范围", "Applications"),
    ("展示柜", "Display cabinet"),
    ("货架", "Shelving"),
    ("橱窗", "Window display"),
    ("展台", "Exhibition stand"),
    ("需要车", "Requires CNC"),
    ("铣", "milling"),
    ("结构较为复杂", "Relatively complex structure"),
    ("它", "it"),
    ("它的", "its"),
    ("等", ", etc."),
    ("手", "Hand"),
    ("左,中, right three", "Left, Center, Right"),
    ("左", "Left"),
    ("中", "Center"),
    ("右", "Right"),
    ("颗", ""),
    ("块", ""),
    ("以", "and"),
    ("均", "all "),
    ("靠", "reliable"),
    ("转", "to"),
    ("可", "Can"),
    ("的", ""),
    ("并", "and"),
    ("。", "."),
    ("，", ","),
    ("：", ":"),
    # --- 博客 body 精确残余 ---
    ('有呈 渐亮-&gt;渐暗-&gt;渐亮 cycling continuously', 'cycling: fade-in → fade-out → fade-in continuously'),
    ('whiteLighting有呈 渐亮-&gt;渐暗-&gt;渐亮', 'white light cycles: fade-in → fade-out → fade-in'),
    ('拧下White"Custom瓶盖", and将其拧到新小黑瓶上', 'Unscrew the white "Custom cap" and screw it onto the new Genifique bottle'),
    ("将其拧到新小黑瓶上", "screw it onto the new Genifique bottle"),
    ("电池充满电后, lasts about", "After a full charge, lasts about"),
    ("视使用频率, 具体使用时长不定, 若是侧板看不见Lighting, 感应无反应情况下, 就表明电池电量用完了. 每套道具都配备了3电池. 请电池取下后, charge it promptly. Replacing the Battery步骤如下:",
     "Usage frequency affects actual duration. If side panel light is off and no sensor response, battery is depleted. Each unit has 3 batteries. Remove and charge promptly. Battery replacement steps:"),
    ("感应无反应情况下", "no sensor response"),
    ("就表明电池电量用完了", "battery is depleted"),
    ("每套道具都配备了3电池", "Each unit has 3 batteries"),
    ("请电池取下后", "Remove battery and"),
    ("Replacing the Battery步骤如下:", "Battery replacement steps:"),
    ("新小黑瓶", "new Genifique bottle"),
    ("小黑瓶", "Genifique bottle"),
    ("电池", "battery"),
    ("瓶盖", "cap"),
    ("渐亮", "fade-in"),
    ("渐暗", "fade-out"),
    ("有呈", " cycles:"),
    ("拧下", "Unscrew"),
    ("步骤如下", "steps"),
    ("Custom瓶盖", "Custom cap"),

    # --- LED灯条残余 ---
    ("Voltage12v 120灯/米", "12V, 120 LEDs/m"),
    ("Voltage 12v 灯/米", "12V, LEDs/m"),
    ("120灯/米", "120 LEDs/m"),
    ("Voltage12v", "12V"),
    ("Voltage24v", "24V"),

    # --- 项目残余 ---
    ("三个", "Three"),
    ("使用", "Using"),
    ("光效", "light effects"),
    ("切换", "switchable"),
    ("动画", "animation"),
    ("包括", "including"),
    ("图片点播道具开发", "image-on-demand prop development"),
    ("基于", "Based on"),
    ("外壳", "Housing"),
    ("外部", "External"),
    ("多个", "Multiple"),
    ("多种", "Multiple"),
    ("多种光效模式", "Multiple light effect modes"),
    ("小多种规格", "multiple sizes"),
    ("小批量生产", "Small-batch production"),
    ("开始工作", "activates"),
    ("彩色显示", "Color display"),
    ("恒压", "Constant voltage"),
    ("恒定", "Constant"),
    ("恒流", "constant current"),
    ("提供超大", "Available in XL"),
    ("播放", "Playback"),
    ("方便嵌入各类产品", "Easy integration into various products"),
    ("无线更新", "wireless update"),
    ("时钟频率", "Clock frequency"),
    ("显示", "Display"),
    ("显示动画", "Display animation"),
    ("有不同大小", "available in various sizes"),
    ("根据", "per"),
    ("灯接头处发光", "LED connector illuminated"),
    ("灯箱", "light box"),
    ("灵活调整", "flexible adjustment"),
    ("焊接微", "soldering micro"),
    ("确保每个", "ensures each"),
    ("紧凑", "Compact"),
    ("耐用且轻便", "Durable and lightweight"),
    ("联动", "integration"),
    ("超薄", "Ultra-thin"),
    ("输出", "output"),
    ("速度", "Speed"),
    ("铝型材开发", "Aluminum profile development"),
    ("非常适合快速开发项目过程", "ideal for rapid project development"),
    ("适用于长时间运行灯具", "suitable for long-running lighting"),
    ("项目", "Project"),
    ("规格", "specs"),
    ("Multiple规格", "Multiple specs"),
]


def apply_replacements(text):
    """Apply all replacements to a string (longest first)"""
    if not isinstance(text, str):
        return text
    result = text
    # Longest first to avoid partial matches
    for old, new in REPLACEMENTS:
        result = result.replace(old, new)
    # Regex cleanup
    result = re.sub(r'(\d+)灯/米', r'\1 LEDs/m', result)
    result = re.sub(r'(\d+)周', r'\1 weeks', result)
    result = re.sub(r'(\d+)\s*周', r'\1 weeks', result)
    result = re.sub(r'(\d+)颗', r'\1', result)
    result = re.sub(r'(\d+)块', r'\1', result)
    result = re.sub(r'灯条 LED Strip', r'LED Strip', result)  # Fix double translate
    result = re.sub(r'其Color', r'its color', result)
    result = re.sub(r'Profiles灯', r'Profiles', result)
    result = re.sub(r'Center间', r'Center', result)
    result = re.sub(r'°C度and下', r'°C and below', result)
    result = re.sub(r'大、Center、小', r'L, Center, S', result)
    result = re.sub(r'Left、Center、Right', r'Left, Center, Right', result)
    result = re.sub(r'XL、大、Center、小', r'XL, L, Center, S', result)
    result = re.sub(r'亮度all 匀', r'brightness uniformity', result)
    result = re.sub(r'视Using频率,\s*具体Using时长不定,\s*若是侧板看不见Lighting,\s*no sensor response,\s*battery is depleted',
                    r'Actual duration depends on usage frequency. If side panel light is off with no sensor response, battery is depleted', result)
    result = re.sub(r'视Using频率', r'Actual duration depends on usage frequency', result)
    result = re.sub(r'具体Using时长不定', r'exact duration varies', result)
    result = re.sub(r'若是侧板看不见Lighting', r'If side panel light is off', result)
    result = re.sub(r'远程更换Video', r'Remote Video update', result)
    result = re.sub(r'模式Can\s*switchable', r'modes switchable', result)
    result = re.sub(r'Can按需Custom', r'fully customizable on demand', result)
    result = re.sub(r'适用于\s*LED', r'Suitable for LED', result)
    result = re.sub(r'Control其', r'control its', result)
    result = re.sub(r'小巧Size', r'Compact Size', result)
    result = re.sub(r'Design者', r'Designer', result)
    result = re.sub(r'SpeedCan控', r'Speed control', result)
    result = re.sub(r'度\s*and\s*下', r'°C and below', result)
    return result


def process(obj):
    """Recursively process dict/list, translating all strings"""
    if isinstance(obj, str):
        return apply_replacements(obj)
    elif isinstance(obj, dict):
        return {k: process(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [process(it) for it in obj]
    return obj


def main():
    en_dir = SITE_DIR / "lang" / "en" / "data"
    print("=" * 60)
    print("YAML-safe cleanup (parse → modify → dump)")
    print("=" * 60)

    for fp in sorted(en_dir.glob("*.yaml")):
        with open(fp, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            continue

        cleaned = process(data)
        with open(fp, "w", encoding="utf-8") as f:
            yaml.dump(cleaned, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        remaining = len(re.findall(r'[一-鿿]', str(cleaned)))
        print(f"  {fp.name}: {remaining} Chinese chars remaining")

    print("\nDone!")


if __name__ == "__main__":
    main()
