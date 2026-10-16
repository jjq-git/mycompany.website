#!/usr/bin/env python3
"""站点6翻译脚本：将 zh-CN 内容翻译为 zh-TW（繁体）和 en（英文）"""

import os
import yaml
from copy import deepcopy
from pathlib import Path

SITE_DIR = Path(r"f:\dengtec\mycompany.website11\sites\6")

# ============================================================
# 简体→繁体字符映射（常用字）
# ============================================================
S2T_MAP = {
    "个": "個", "们": "們", "门": "門", "为": "為", "从": "從",
    "页": "頁", "业": "業", "东": "東", "丝": "絲", "两": "兩",
    "严": "嚴", "丧": "喪", "个": "個", "丰": "豐", "临": "臨",
    "丽": "麗", "么": "麼", "义": "義", "乌": "烏", "乐": "樂",
    "乔": "喬", "习": "習", "乡": "鄉", "书": "書", "买": "買",
    "争": "爭", "于": "於", "亏": "虧", "云": "雲", "产": "產",
    "亩": "畝", "亲": "親", "亿": "億", "仅": "僅", "仆": "僕",
    "从": "從", "仑": "侖", "仓": "倉", "仪": "儀", "价": "價",
    "众": "眾", "优": "優", "伙": "夥", "会": "會", "传": "傳",
    "伤": "傷", "伦": "倫", "伪": "偽", "体": "體", "余": "餘",
    "佣": "傭", "侠": "俠", "侣": "侶", "侦": "偵", "侧": "側",
    "侨": "僑", "侩": "儈", "侪": "儕", "侬": "儂", "俦": "儔",
    "俨": "儼", "俪": "儷", "俫": "倈", "俭": "儉", "债": "債",
    "倾": "傾", "偻": "僂", "偾": "僨", "偿": "償", "傧": "儐",
    "储": "儲", "兑": "兌", "兰": "蘭", "关": "關", "兴": "興",
    "养": "養", "兽": "獸", "内": "內", "冈": "岡", "册": "冊",
    "写": "寫", "军": "軍", "农": "農", "冯": "馮", "冲": "衝",
    "决": "決", "况": "況", "冻": "凍", "净": "淨", "凄": "淒",
    "准": "準", "凉": "涼", "减": "減", "凑": "湊", "几": "幾",
    "凤": "鳳", "凫": "鳧", "击": "擊", "凿": "鑿", "刍": "芻",
    "划": "劃", "刚": "剛", "创": "創", "别": "別", "刽": "劊",
    "制": "製", "剧": "劇", "刘": "劉", "则": "則", "剑": "劍",
    "剂": "劑", "力": "力", "办": "辦", "务": "務", "动": "動",
    "励": "勵", "劲": "勁", "劳": "勞", "势": "勢", "勋": "勳",
    "包": "包", "医": "醫", "华": "華", "单": "單", "卖": "賣",
    "卫": "衛", "却": "卻", "历": "歷", "压": "壓", "厌": "厭",
    "厍": "厙", "县": "縣", "叁": "叄", "参": "參", "双": "雙",
    "发": "發", "变": "變", "叠": "疊", "只": "隻", "台": "臺",
    "叶": "葉", "号": "號", "叹": "嘆", "吗": "嗎", "员": "員",
    "呗": "唄", "呜": "嗚", "呜": "嗚", "咏": "詠", "咙": "嚨",
    "咛": "嚀", "哟": "喲", "咨": "諮", "咸": "鹹", "哒": "噠",
    "哓": "嘵", "哕": "噦", "哗": "嘩", "哟": "喲", "唢": "嗩",
    "唤": "喚", "啧": "嘖", "啬": "嗇", "啭": "囀", "啰": "囉",
    "啸": "嘯", "喷": "噴", "喽": "嘍", "喾": "嚳", "嗫": "囁",
    "嗳": "噯", "团": "團", "园": "園", "围": "圍", "国": "國",
    "图": "圖", "圆": "圓", "圣": "聖", "场": "場", "坞": "塢",
    "块": "塊", "坚": "堅", "坛": "壇", "坝": "壩", "売": "賣",
    "复": "復", "够": "夠", "头": "頭", "夹": "夾", "夺": "奪",
    "奋": "奮", "奖": "獎", "妆": "妝", "妇": "婦", "妈": "媽",
    "娲": "媧", "婴": "嬰", "孙": "孫", "学": "學", "宁": "寧",
    "实": "實", "宠": "寵", "审": "審", "宪": "憲", "宫": "宮",
    "宽": "寬", "宾": "賓", "对": "對", "寻": "尋", "导": "導",
    "寿": "壽", "将": "將", "尔": "爾", "尘": "塵", "尝": "嘗",
    "尧": "堯", "尴": "尷", "尸": "屍", "尽": "盡", "屦": "屨",
    "层": "層", "届": "屆", "属": "屬", "屡": "屢", "屿": "嶼",
    "岁": "歲", "岂": "豈", "岖": "嶇", "岗": "崗", "岘": "峴",
    "岚": "嵐", "岛": "島", "岭": "嶺", "岳": "嶽", "峡": "峽",
    "峦": "巒", "崭": "嶄", "峰": "峰", "巡": "巡", "帅": "帥",
    "帐": "帳", "帘": "簾", "帜": "幟", "带": "帶", "帧": "幀",
    "帮": "幫", "干": "幹", "平": "平", "并": "並", "广": "廣",
    "庄": "莊", "庆": "慶", "庐": "廬", "库": "庫", "庙": "廟",
    "废": "廢", "开": "開", "异": "異", "弃": "棄", "张": "張",
    "弥": "彌", "弪": "弳", "弯": "彎", "弹": "彈", "强": "強",
    "归": "歸", "当": "當", "录": "錄", "彻": "徹", "征": "徵",
    "态": "態", "怂": "慫", "忧": "憂", "念": "念", "怀": "懷",
    "态": "態", "怂": "慫", "怅": "悵", "惊": "驚", "悯": "憫",
    "惯": "慣", "惩": "懲", "惫": "憊", "懒": "懶", "悬": "懸",
    "忏": "懺", "惧": "懼", "惩": "懲", "恋": "戀", "戏": "戲",
    "战": "戰", "户": "戶", "扎": "紮", "扑": "撲", "扒": "扒",
    "扩": "擴", "扫": "掃", "扬": "揚", "扰": "擾", "抚": "撫",
    "抛": "拋", "抟": "摶", "抠": "摳", "抢": "搶", "护": "護",
    "报": "報", "拟": "擬", "拢": "攏", "拣": "揀", "拥": "擁",
    "拦": "攔", "拧": "擰", "拨": "撥", "择": "擇", "括": "括",
    "拭": "拭", "挚": "摯", "挛": "攣", "拦": "攔", "搅": "攪",
    "断": "斷", "无": "無", "既": "既", "时": "時", "晋": "晉",
    "晒": "曬", "晓": "曉", "晕": "暈", "暂": "暫", "术": "術",
    "杀": "殺", "杂": "雜", "权": "權", "条": "條", "来": "來",
    "杨": "楊", "极": "極", "构": "構", "枣": "棘", "标": "標",
    "栈": "棧", "栏": "欄", "树": "樹", "样": "樣", "桩": "樁",
    "梦": "夢", "检": "檢", "棂": "櫺", "椟": "櫝", "榄": "欖",
    "欠": "欠", "欢": "歡", "欧": "歐", "欲": "慾", "款": "款",
    "岁": "歲", "毁": "毀", "毵": "毿", "毡": "氈", "气": "氣",
    "氢": "氫", "氧": "氧", "氨": "氨", "毵": "毿", "毶": "氀",
    "汉": "漢", "沦": "淪", "汹": "洶", "沟": "溝", "没": "沒",
    "沣": "灃", "沤": "漚", "沥": "瀝", "沦": "淪", "沧": "滄",
    "泼": "潑", "洁": "潔", "洒": "灑", "浇": "澆", "浔": "潯",
    "涂": "塗", "涩": "澀", "涨": "漲", "渗": "滲", "惭": "慚",
    "惯": "慣", "恳": "懇", "叠": "疊", "疟": "瘧", "疮": "瘡",
    "疯": "瘋", "疗": "療", "痒": "癢", "痖": "瘂", "痨": "癆",
    "疮": "瘡", "疟": "瘧", "痈": "癰", "瘫": "癱", "瘾": "癮",
    "皑": "皚", "皱": "皺", "盏": "盞", "盐": "鹽", "监": "監",
    "盖": "蓋", "盘": "盤", "眬": "矓", "睁": "睜", "睐": "睞",
    "瞒": "瞞", "瞩": "矚", "矫": "矯", "矶": "磯", "矿": "礦",
    "码": "碼", "矾": "礬", "砗": "硨", "砖": "磚", "砚": "硯",
    "硕": "碩", "硷": "礆", "确": "確", "碍": "礙", "碱": "鹼",
    "礼": "禮", "祷": "禱", "禅": "禪", "祸": "禍", "祯": "禎",
    "称": "稱", "秽": "穢", "种": "種", "积": "積", "称": "稱",
    "稳": "穩", "稻": "稻", "窃": "竊", "窍": "竅", "窑": "窯",
    "穷": "窮", "窥": "窺", "窜": "竄", "窝": "窩", "窦": "竇",
    "竞": "競", "笔": "筆", "笋": "筍", "笼": "籠", "筛": "篩",
    "简": "簡", "算": "算", "箩": "籮", "笺": "箋", "箫": "簫",
    "签": "簽", "篮": "籃", "籍": "籍", "类": "類", "粜": "糶",
    "粝": "糲", "紧": "緊", "纠": "糾", "红": "紅", "纤": "纖",
    "约": "約", "级": "級", "纪": "紀", "纫": "紉", "纬": "緯",
    "纯": "純", "纲": "綱", "纳": "納", "纵": "縱", "纷": "紛",
    "纸": "紙", "纹": "紋", "纺": "紡", "纽": "紐", "线": "線",
    "练": "練", "组": "組", "绅": "紳", "细": "細", "织": "織",
    "终": "終", "绊": "絆", "绍": "紹", "绎": "繹", "经": "經",
    "绑": "綁", "结": "結", "绘": "繪", "给": "給", "络": "絡",
    "绝": "絕", "绞": "絞", "统": "統", "绢": "絹", "绣": "繡",
    "继": "繼", "绩": "績", "绪": "緒", "续": "續", "绮": "綺",
    "绯": "緋", "绰": "綽", "绳": "繩", "维": "維", "绵": "綿",
    "绷": "繃", "绸": "綢", "综": "綜", "绽": "綻", "绿": "綠",
    "缀": "綴", "缄": "緘", "缅": "緬", "缆": "纜", "缂": "緙",
    "缎": "緞", "缓": "緩", "缔": "締", "编": "編", "缘": "緣",
    "缥": "縹", "缚": "縛", "缧": "縲", "缝": "縫", "缠": "纏",
    "缤": "繽", "缫": "繅", "缵": "纘", "网": "網", "罗": "羅",
    "罚": "罰", "罢": "罷", "罴": "羆", "骂": "罵", "罢": "罷",
    "羁": "羈", "羟": "羥", "羡": "羨", "翘": "翹", "翙": "翽",
    "耢": "耮", "联": "聯", "聪": "聰", "耸": "聳", "聂": "聶",
    "职": "職", "聋": "聾", "肃": "肅", "肠": "腸", "肤": "膚",
    "肾": "腎", "肿": "腫", "胀": "脹", "胁": "脅", "胜": "勝",
    "脑": "腦", "脓": "膿", "脚": "腳", "脸": "臉", "腊": "臘",
    "腌": "醃", "腾": "騰", "舆": "輿", "舍": "捨", "舰": "艦",
    "舱": "艙", "舻": "艫", "艰": "艱", "艳": "艷", "艺": "藝",
    "节": "節", "芗": "薌", "芜": "蕪", "芦": "蘆", "苁": "蓯",
    "苇": "葦", "苈": "藶", "苋": "莧", "苌": "萇", "苍": "蒼",
    "苎": "苧", "苏": "蘇", "苹": "蘋", "茎": "莖", "茏": "蘢",
    "茑": "蔦", "茔": "塋", "茕": "煢", "茧": "繭", "茫": "茫",
    "荜": "蓽", "荭": "葒", "荮": "葤", "药": "藥", "莅": "蒞",
    "莱": "萊", "莲": "蓮", "莳": "蒔", "获": "獲", "莹": "瑩",
    "莺": "鶯", "莼": "蒓", "萦": "縈", "萧": "蕭", "萨": "薩",
    "万": "萬", "落": "落", "叶": "葉", "着": "著", "盖": "蓋",
    "蒙": "蒙", "蓝": "藍", "蔑": "蔑", "蔓": "蔓", "蔡": "蔡",
    "荫": "蔭", "蕴": "蘊", "蕾": "蕾", "薇": "薇", "蕲": "蘄",
    "虍": "虍", "虑": "慮", "虚": "虛", "虫": "蟲", "虽": "雖",
    "虾": "蝦", "蚀": "蝕", "蚁": "蟻", "蚂": "螞", "蚕": "蠶",
    "蚬": "蜆", "蛊": "蠱", "蛎": "蠣", "蛰": "蟄", "蛏": "蟶",
    "蛮": "蠻", "蜕": "蛻", "蜗": "蝸", "蜡": "蠟", "蝇": "蠅",
    "蝉": "蟬", "蝎": "蠍", "蝼": "螻", "螨": "蟎", "衅": "釁",
    "衔": "銜", "衣": "衣", "补": "補", "表": "錶", "衬": "襯",
    "衮": "袞", "袄": "襖", "袅": "裊", "袜": "襪", "袭": "襲",
    "装": "裝", "裆": "襠", "裴": "裴", "裸": "裸", "裹": "裹",
    "裥": "襇", "裱": "裱", "裳": "裳", "褶": "褶", "西": "西",
    "覆": "覆", "见": "見", "观": "觀", "规": "規", "觅": "覓",
    "视": "視", "览": "覽", "觉": "覺", "觊": "覬", "觎": "覦",
    "角": "角", "解": "解", "触": "觸", "言": "言", "誊": "謄",
    "计": "計", "订": "訂", "认": "認", "讥": "譏", "讨": "討",
    "让": "讓", "训": "訓", "议": "議", "讯": "訊", "记": "記",
    "讲": "講", "讳": "諱", "讶": "訝", "讷": "訥", "许": "許",
    "讹": "訛", "论": "論", "讼": "訟", "讽": "諷", "设": "設",
    "访": "訪", "证": "證", "评": "評", "识": "識", "诈": "詐",
    "诉": "訴", "诊": "診", "词": "詞", "译": "譯", "试": "試",
    "诗": "詩", "诚": "誠", "话": "話", "诞": "誕", "诡": "詭",
    "询": "詢", "该": "該", "详": "詳", "诧": "詫", "诬": "誣",
    "语": "語", "误": "誤", "诱": "誘", "诲": "誨", "说": "說",
    "诵": "誦", "请": "請", "诸": "諸", "诺": "諾", "读": "讀",
    "诽": "誹", "课": "課", "谁": "誰", "调": "調", "谄": "諂",
    "谅": "諒", "谆": "諄", "谈": "談", "谊": "誼", "谋": "謀",
    "谍": "諜", "谎": "謊", "谐": "諧", "谓": "謂", "谒": "謁",
    "谗": "讒", "谙": "諳", "谚": "諺", "谜": "謎", "谢": "謝",
    "谣": "謠", "谤": "謗", "谦": "謙", "谨": "謹", "谬": "謬",
    "谭": "譚", "谱": "譜", "谴": "譴", "谷": "穀", "贝": "貝",
    "贞": "貞", "负": "負", "贡": "貢", "财": "財", "责": "責",
    "贤": "賢", "败": "敗", "货": "貨", "质": "質", "贩": "販",
    "贪": "貪", "贫": "貧", "贬": "貶", "购": "購", "贯": "貫",
    "贰": "貳", "贱": "賤", "贲": "賁", "贴": "貼", "贵": "貴",
    "贷": "貸", "贸": "貿", "费": "費", "贺": "賀", "贼": "賊",
    "贾": "賈", "贿": "賄", "赁": "賃", "赂": "賂", "资": "資",
    "赅": "賅", "赇": "賕", "赈": "賑", "赊": "賒", "宾": "賓",
    "赍": "齎", "赠": "贈", "赡": "贍", "赢": "贏", "赣": "贛",
    "赤": "赤", "赧": "赧", "赫": "赫", "走": "走", "赵": "趙",
    "赶": "趕", "起": "起", "趁": "趁", "趋": "趨", "超": "超",
    "越": "越", "趣": "趣", "足": "足", "跃": "躍", "跄": "蹌",
    "路": "路", "践": "踐", "跷": "蹺", "跸": "蹕", "跳": "跳",
    "踊": "踊", "踏": "踏", "踢": "踢", "踩": "踩", "踪": "蹤",
    "踱": "踱", "蹿": "躥", "身": "身", "躬": "躬", "躲": "躲",
    "躺": "躺", "车": "車", "轧": "軋", "轨": "軌", "轩": "軒",
    "转": "轉", "轮": "輪", "软": "軟", "轰": "轟", "轴": "軸",
    "轻": "輕", "载": "載", "轿": "轎", "较": "較", "辅": "輔",
    "辆": "輛", "辈": "輩", "辉": "輝", "辊": "輥", "辐": "輻",
    "辑": "輯", "输": "輸", "辕": "轅", "辖": "轄", "辗": "輾",
    "辙": "轍", "辛": "辛", "辞": "辭", "辟": "闢", "辣": "辣",
    "辨": "辨", "辩": "辯", "辫": "辮", "辰": "辰", "辱": "辱",
    "辽": "遼", "达": "達", "迁": "遷", "过": "過", "迈": "邁",
    "运": "運", "还": "還", "这": "這", "进": "進", "远": "遠",
    "违": "違", "连": "連", "迟": "遲", "迩": "邇", "选": "選",
    "逊": "遜", "递": "遞", "逦": "邐", "逻": "邏", "遗": "遺",
    "邓": "鄧", "邝": "鄺", "邮": "郵", "邹": "鄒", "邻": "鄰",
    "郁": "鬱", "郏": "郟", "郑": "鄭", "郧": "鄖", "郸": "鄲",
    "酝": "醞", "酱": "醬", "酽": "釅", "酾": "釃", "里": "裡",
    "钆": "釓", "钇": "釔", "针": "針", "钉": "釘", "钊": "釗",
    "钋": "釙", "钌": "釕", "钍": "釷", "钎": "釺", "钏": "釧",
    "钐": "釤", "钒": "釩", "钓": "釣", "钔": "鍆", "钕": "釹",
    "钚": "鈈", "钠": "鈉", "钡": "鋇", "钢": "鋼", "钣": "鈑",
    "钤": "鈐", "钥": "鑰", "钦": "欽", "钧": "鈞", "钨": "鎢",
    "钩": "鉤", "钪": "鈧", "钫": "鈁", "钬": "鈥", "钭": "鈄",
    "钮": "鈕", "钯": "鈀", "钰": "鈺", "钲": "鉦", "钳": "鉗",
    "钴": "鈷", "钵": "缽", "钷": "鉕", "钸": "鈽", "钹": "鈸",
    "钺": "鉞", "钻": "鑽", "钼": "鉬", "钽": "鉭", "钾": "鉀",
    "钿": "鈿", "铀": "鈾", "铂": "鉑", "铄": "鑠", "铆": "鉚",
    "铈": "鈰", "铉": "鉉", "铌": "鈮", "铍": "鈹", "钏": "釧",
    "铑": "銠", "铒": "鉺", "铕": "銪", "铖": "鋮", "铘": "鋣",
    "铙": "鐃", "铛": "鐺", "铜": "銅", "铝": "鋁", "铞": "銱",
    "铟": "銦", "铡": "鍘", "铥": "銩", "铦": "銛", "铧": "鏵",
    "铨": "銓", "铩": "鎩", "铪": "鉿", "铫": "銚", "铬": "鉻",
    "铭": "銘", "铮": "錚", "铯": "銫", "铰": "鉸", "铲": "鏟",
    "铳": "銃", "铴": "鐋", "铵": "銨", "银": "銀", "铷": "銣",
    "铸": "鑄", "铹": "鐒", "铺": "鋪", "铻": "鋙", "链": "鏈",
    "铿": "鏗", "销": "銷", "锁": "鎖", "锄": "鋤", "锅": "鍋",
    "锆": "鋯", "锇": "鋨", "锈": "鏽", "锉": "銼", "锊": "鋝",
    "锋": "鋒", "锌": "鋅", "锐": "銳", "锑": "銻", "锒": "鋃",
    "铺": "鋪", "锘": "鍩", "锛": "錛", "锜": "錤", "锝": "鍀",
    "锞": "錁", "锟": "錕", "锡": "錫", "锢": "錮", "锣": "鑼",
    "锤": "錘", "锥": "錐", "锦": "錦", "锨": "杴", "锩": "鐫",
    "锫": "錇", "锬": "錟", "锭": "錠", "键": "鍵", "锯": "鋸",
    "锰": "錳", "锱": "錙", "锲": "鍥", "锳": "鍈", "锴": "鍇",
    "锵": "鏘", "锶": "鍶", "锷": "鍔", "镀": "鍍", "镁": "鎂",
    "镂": "鏤", "镄": "鐨", "镅": "鎇", "镆": "鏌", "镇": "鎮",
    "镉": "鎘", "镊": "鑷", "镍": "鎳", "镌": "鐫", "镎": "錼",
    "镓": "鎵", "镔": "鑌", "镗": "鏜", "镘": "鏝", "镙": "鏍",
    "镛": "鏞", "镜": "鏡", "镝": "鏑", "镞": "鏃", "镥": "鑥",
    "镫": "鐙", "镬": "鑊", "镮": "鐶", "镱": "鐿", "长": "長",
    "门": "門", "闩": "閂", "闪": "閃", "闭": "閉", "问": "問",
    "闯": "闖", "闰": "閏", "闱": "闈", "闲": "閒", "间": "間",
    "闵": "閔", "闷": "悶", "闸": "閘", "闹": "鬧", "闺": "閨",
    "闻": "聞", "闼": "闥", "闽": "閩", "闾": "閭", "闿": "闓",
    "阎": "閻", "阐": "闡", "阔": "闊", "队": "隊", "阳": "陽",
    "阴": "陰", "阵": "陣", "阶": "階", "际": "際", "陆": "陸",
    "陇": "隴", "陈": "陳", "陉": "陘", "陕": "陝", "陧": "隉",
    "陨": "隕", "险": "險", "随": "隨", "隐": "隱", "隶": "隸",
    "隽": "雋", "难": "難", "雏": "雛", "雳": "靂", "雾": "霧",
    "霁": "霽", "霉": "黴", "霭": "靄", "靓": "靚", "静": "靜",
    "面": "麵", "靥": "靨", "鞑": "韃", "鞒": "鞽", "鞯": "韉",
    "韦": "韋", "韧": "韌", "韩": "韓", "韪": "韙", "韫": "韞",
    "韵": "韻", "页": "頁", "顶": "頂", "顷": "頃", "顸": "頇",
    "项": "項", "顺": "順", "须": "須", "顽": "頑", "顾": "顧",
    "顿": "頓", "颁": "頒", "颂": "頌", "预": "預", "颅": "顱",
    "领": "領", "颇": "頗", "颈": "頸", "颊": "頰", "颏": "頦",
    "颐": "頤", "频": "頻", "颓": "頹", "颔": "頷", "颖": "穎",
    "颗": "顆", "题": "題", "颚": "顎", "颛": "顓", "颜": "顏",
    "额": "額", "颞": "顳", "风": "風", "飒": "颯", "飓": "颶",
    "飔": "颸", "飕": "颼", "飘": "飄", "飙": "飆", "飞": "飛",
    "食": "食", "餐": "餐", "饭": "飯", "饮": "飲", "饯": "餞",
    "饰": "飾", "饱": "飽", "饲": "飼", "饵": "餌", "饶": "饒",
    "饷": "餉", "饺": "餃", "饼": "餅", "饿": "餓", "馀": "餘",
    "馁": "餒", "馂": "餕", "馃": "餜", "馄": "餛", "馅": "餡",
    "馆": "館", "馇": "餷", "馈": "饋", "馊": "餿", "馋": "饞",
    "馍": "餝", "馏": "餾", "馐": "饈", "馑": "饉", "馒": "饅",
    "馓": "饊", "馔": "饌", "馕": "饢", "首": "首", "香": "香",
    "馥": "馥", "马": "馬", "驭": "馭", "驮": "馱", "驯": "馴",
    "驰": "馳", "驱": "驅", "驳": "駁", "驴": "驢", "驶": "駛",
    "驷": "駟", "驸": "駙", "驹": "駒", "驻": "駐", "驼": "駝",
    "驽": "駑", "驾": "駕", "驿": "驛", "骀": "駘", "骁": "驍",
    "骂": "罵", "骄": "驕", "骅": "驊", "骆": "駱", "骇": "駭",
    "骈": "駢", "骊": "驪", "骋": "騁", "验": "驗", "骏": "駿",
    "骎": "駸", "骑": "騎", "骓": "騅", "骖": "驂", "骗": "騙",
    "骘": "騭", "骚": "騷", "骛": "騖", "骞": "騫", "骟": "騸",
    "骡": "騾", "骢": "驄", "骣": "驏", "骤": "驟", "骥": "驥",
    "骧": "驤", "骨": "骨", "骰": "骰", "骱": "骱", "骶": "骶",
    "骷": "骷", "骸": "骸", "骺": "骺", "骼": "骼", "髁": "髁",
    "髂": "髂", "髅": "髏", "髋": "髖", "髌": "臏", "高": "高",
    "鬓": "鬢", "鬼": "鬼", "魁": "魁", "魄": "魄",
    "魇": "魘", "鱼": "魚", "鱽": "魛", "鱾": "魢", "鲁": "魯",
    "鲂": "魴", "鲅": "鮁", "鲆": "鮃", "鲇": "鯰", "鲈": "鱸",
    "鲎": "鱟", "鲑": "鮭", "鲒": "鮚", "鲔": "鮪", "鲗": "鰂",
    "鲙": "鱠", "鲚": "鱭", "鲛": "鮫", "鲜": "鮮", "鲞": "鯗",
    "鲟": "鱘", "鲠": "骾", "鲡": "鱺", "鲢": "鰱", "鲣": "鰹",
    "鲤": "鯉", "鲥": "鰣", "鲦": "鰷", "鲧": "鯀", "鲨": "鯊",
    "鲩": "鯇", "鲫": "鯽", "鲭": "鯖", "鲮": "鯪", "鲱": "鯡",
    "鲲": "鯤", "鲳": "鯧", "鲴": "鯝", "鲵": "鯢", "鲷": "鯛",
    "鲸": "鯨", "鲻": "鯔", "鲼": "鱝", "鲾": "鰏", "鳁": "鰮",
    "鳃": "鰓", "鳄": "鱷", "鳇": "鰉", "鳊": "鯿", "鳌": "鰲",
    "鳍": "鰭", "鳎": "鰨", "鳐": "鰩", "鳑": "鰟", "鳒": "鰜",
    "鸟": "鳥", "鸠": "鳩", "鸡": "雞", "鸢": "鳶", "鸣": "鳴",
    "鸥": "鷗", "鸦": "鴉", "鸨": "鴇", "鸩": "鴆", "鸪": "鴣",
    "鸫": "鶇", "鸬": "鸕", "鸭": "鴨", "鸮": "鴞", "鸯": "鴦",
    "鸰": "鴒", "鸱": "鴟", "鸲": "鴝", "鸳": "鴛", "鸸": "鴯",
    "鸹": "鴰", "鸺": "鵂", "鸽": "鴿", "鸾": "鸞", "鸿": "鴻",
    "鹂": "鸝", "鹃": "鵑", "鹆": "鵒", "鹈": "鵜", "鹅": "鵝",
    "鹌": "鵪", "鹎": "鵯", "鹑": "鵪", "鹒": "鶊", "鹕": "鶘",
    "鹗": "鶚", "鹘": "鶻", "鹚": "鶿", "鹞": "鷂", "鹟": "鶲",
    "鹠": "鶹", "鹡": "鶺", "鹣": "鶼", "鹤": "鶴", "鹩": "鷯",
    "鹫": "鷲", "鹬": "鷸", "鹰": "鷹", "鹮": "䴉", "鹭": "鷺",
    "鹱": "鸌", "鹳": "鸛", "鹾": "鹺", "鹿": "鹿", "麦": "麥",
    "黄": "黃", "黉": "黌", "黑": "黑", "黔": "黔", "默": "默",
    "黛": "黛", "黜": "黜", "黝": "黝", "黟": "黟", "黠": "黠",
    "黢": "黢", "黥": "黥", "黧": "黧", "黩": "黷", "黪": "黲",
    "黾": "黽", "鼍": "鼉", "鼎": "鼎", "鼓": "鼓", "鼹": "鼴",
    "齐": "齊", "齿": "齒", "龃": "齟", "龄": "齡", "龅": "齙",
    "龆": "齠", "龇": "齜", "龈": "齦", "龉": "齬", "龊": "齪",
    "龙": "龍", "龚": "龔", "龟": "龜",
    # 特定词汇
    "什么": "什麼", "为什么": "為什麼", "怎么": "怎麼", "这里": "這裡",
    "那里": "那裡", "哪里": "哪裡", "这个": "這個", "那个": "那個",
    "哪个": "哪個", "这些": "這些", "那些": "哪些",
    "干": "幹", "后": "後", "征": "徵",
    "灯": "燈", "电": "電", "线": "線", "线材": "線材",
    "接头": "接頭", "插件": "插件", "连接": "連接",
    "铝": "鋁", "槽": "槽", "射": "射", "光": "光",
    "导电": "導電", "电源": "電源", "控制器": "控制器",
    "编程": "編程", "开发": "開發", "设计": "設計",
    "结构": "結構", "产品": "產品", "项目": "項目",
    "服务": "服務", "技术": "技術", "创新": "創新",
    "显示": "顯示", "系统": "系統", "模块": "模塊",
    "感应": "感應", "传感器": "傳感器", "互动": "互動",
    "电路": "電路", "板": "板", "灯光": "燈光",
    "定制": "定製", "品牌": "品牌", "效果": "效果",
    "关于": "關於", "联系": "聯繫", "博客": "部落格",
    "全息": "全息", "投影": "投影", "日目": "日目",
    "静音仓": "靜音倉", "导电槽": "導電槽",
}

# 补充常见词汇级映射
PHRASE_S2T = {
    # 产品相关
    "灯条": "燈條", "灯珠": "燈珠", "灯板": "燈板",
    "铝槽": "鋁槽", "射灯": "射燈", "电源": "電源",
    "线材及接插件": "線材及接插件", "导电槽": "導電槽",
    "全息投影": "全息投影", "电路板": "電路板",
    "导光板": "導光板", "发光": "發光", "霓虹灯": "霓虹燈",
    "灯管": "燈管", "光板": "光板", "发光字": "發光字",
    "可编程": "可編程", "控制器": "控制器", "传感器": "傳感器",
    "磁吸": "磁吸", "卡扣": "卡扣", "滴液": "滴液",
    "展示道具": "展示道具", "电子产品": "電子產品",
    # 页脚/导航
    "首页": "首頁", "产品": "產品", "项目": "項目", "近期项目": "近期項目",
    "博客": "部落格", "关于我们": "關於我們", "联系我们": "聯繫我們",
    "近期项目": "近期項目", "最新博客": "最新部落格",
    "核心展示": "核心展示", "精选项目": "精選項目",
    "定制服务": "定製服務", "创新技术": "創新技術",
    # 通用
    "查看更多": "檢視更多", "查看详情": "檢視詳情",
    "了解详情": "瞭解詳情", "详细了解": "詳細瞭解",
    "立即开始": "立即開始", "了解更多": "瞭解更多",
    "发送": "發送", "提交": "提交", "搜索": "搜尋",
    "暂无": "暫無", "全部": "全部", "选择": "選擇",
}

def s2t(text):
    """简体中文转繁体中文"""
    if not isinstance(text, str):
        return text
    result = text
    # 先做词汇级替换（长匹配优先）
    for phrase, trad in sorted(PHRASE_S2T.items(), key=lambda x: -len(x[0])):
        result = result.replace(phrase, trad)
    # 再做字符级替换
    for simp, trad in S2T_MAP.items():
        result = result.replace(simp, trad)
    return result


# ============================================================
# settings.yaml 翻译
# ============================================================
def translate_settings():
    """更新 settings.yaml 的 footer 和 menu_labels"""
    path = SITE_DIR / "settings.yaml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # --- company_zh-TW (从 company_zh-CN 简→繁) ---
    if "company_zh-CN" in data:
        data["company_zh-TW"] = deepcopy(data["company_zh-CN"])
        if "name" in data["company_zh-TW"]:
            data["company_zh-TW"]["name"] = s2t(data["company_zh-TW"]["name"])
        if "short_name" in data["company_zh-TW"]:
            data["company_zh-TW"]["short_name"] = s2t(data["company_zh-TW"]["short_name"])
        if "description" in data["company_zh-TW"]:
            data["company_zh-TW"]["description"] = s2t(data["company_zh-TW"]["description"])

    # --- contact_zh-TW (从 contact_zh-CN 简→繁) ---
    if "contact_zh-CN" in data:
        data["contact_zh-TW"] = deepcopy(data["contact_zh-CN"])
        for key in ["address", "business_hours", "weekend"]:
            if key in data["contact_zh-TW"] and isinstance(data["contact_zh-TW"][key], str):
                data["contact_zh-TW"][key] = s2t(data["contact_zh-TW"][key])

    # --- contact (en) address fix ---
    if "contact" in data and isinstance(data["contact"], dict):
        data["contact"]["address"] = "No.5 Xinxing Road, Development Zone, Kunshan, Jiangsu, China"

    # --- footer_zh-TW (从 footer_zh-CN 简→繁) ---
    if "footer_zh-CN" in data:
        data["footer_zh-TW"] = deepcopy(data["footer_zh-CN"])
        for col in data["footer_zh-TW"]["columns"]:
            if "title" in col:
                col["title"] = s2t(col["title"])
            if "links" in col:
                for link in col["links"]:
                    if "label" in link:
                        link["label"] = s2t(link["label"])

    # --- footer (en) ---
    data["footer"] = {
        "variant": "columns_social",
        "columns": [
            {
                "type": "menu",
                "title": "Products",
                "links": [
                    {"label": "LED Strips", "url": "/products/led-strip/"},
                    {"label": "Aluminum Profiles", "url": "/products/aluminum-profile/"},
                    {"label": "Spot Lights", "url": "/products/spot-light/"},
                    {"label": "Holograms", "url": "/products/holograms/"},
                    {"label": "Cables & Connectors", "url": "/products/cable-connector/"},
                    {"label": "Power Track", "url": "/products/powerptrack/"},
                    {"label": "Power Supply", "url": "/products/power-supplier/"},
                ]
            },
            {
                "type": "menu",
                "title": "Company",
                "links": [
                    {"label": "About Us", "url": "/about/"},
                    {"label": "Blog", "url": "/blog/"},
                    {"label": "Contact", "url": "/contact/"},
                ]
            },
            {
                "type": "menu",
                "title": "Projects",
                "links": [
                    {"label": "RIMU", "url": "/projects/rimu/"},
                    {"label": "Programmable COB LED Board", "url": "/projects/cob-led/"},
                    {"label": "Programmable Light Logo", "url": "/projects/item-3/"},
                ]
            },
        ]
    }

    # --- menu_labels en 补全 ---
    data["menu_labels"]["en"].update({
        "led-strip": "LED Strips",
        "aluminum-profile": "Aluminum Profiles",
        "spot-light": "Spot Lights",
        "holograms": "Hologram Display",
        "cable-connector": "Cables & Connectors",
        "powerptrack": "Power Track",
        "power-supplier": "Power Supply",
    })

    # --- menu_labels zh-TW 修复 ---
    data["menu_labels"]["zh-TW"]["contact"] = "聯絡我們"
    data["menu_labels"]["zh-TW"]["about"] = "關於我們"

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print("[OK] settings.yaml updated")


# ============================================================
# translations.yaml 翻译
# ============================================================
def translate_translations():
    """更新 translations.yaml：en/zh-CN 改为德恩基内容，新增 zh-TW"""
    path = SITE_DIR / "translations.yaml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # --- en 翻译 ---
    data["en"] = {
        "company": "Dengtec",
        "siteLogoText": "Dengtec",
        "nav": {
            "home": "Home", "products": "Products", "solutions": "Projects",
            "pricing": "RIMU", "about": "About", "blog": "Blog", "contact": "Contact",
        },
        "actions": {
            "tryClaude": "Learn More", "learnMore": "Learn More",
            "getStarted": "Get Started", "contactUs": "Contact Us",
            "viewAll": "View All", "readMore": "Read More",
            "sendMessage": "Send Message", "menu": "Menu",
        },
        "sections": {
            "features": "Core Capabilities", "products": "Products",
            "portfolio": "Recent Projects", "posts": "Latest Articles",
            "stats": "By the Numbers", "process": "Our Journey",
            "contact": "Get in Touch", "about": "About Us",
        },
        "categories": {"ai": "LED", "api": "Controller", "research": "Projects"},
        "products": {
            "claude_opus": "LED Strips", "claude_sonnet": "Aluminum Profiles",
            "claude_haiku": "Spot Lights",
        },
        "project": {"viewProject": "View Project"},
        "pages": {
            "home": "Home", "products": "Products", "portfolio": "Projects",
            "posts": "Blog", "about": "About", "pricing": "RIMU", "contact": "Contact",
        },
        "contact": {
            "phone": "Phone", "mobile": "Mobile", "email": "Email",
            "address": "Address", "businessHours": "Business Hours",
            "sendMessage": "Send us a message", "name": "Name", "message": "Message",
            "formName": "Name", "formEmail": "Email", "formPhone": "Phone",
            "formCompany": "Company", "formMessage": "Message",
            "formSend": "Send Message",
            "formMissingAction": "Please configure the form submission URL first.",
        },
        "about": {
            "title": "About Dengtec",
            "subtitle": "Electronic Solutions for Display & Interactive Products",
        },
        "footer": {
            "copyright": "All rights reserved.",
            "privacy": "Privacy Policy", "terms": "Terms of Service",
        },
    }

    # --- zh-CN 翻译 ---
    data["zh-CN"] = {
        "company": "德恩基",
        "siteLogoText": "德恩基",
        "nav": {
            "home": "首页", "products": "产品", "solutions": "项目",
            "pricing": "日目", "about": "关于我们", "blog": "博客", "contact": "联系",
        },
        "actions": {
            "tryClaude": "了解更多", "learnMore": "了解更多",
            "getStarted": "立即开始", "contactUs": "联系我们",
            "viewAll": "查看全部", "readMore": "阅读更多",
            "sendMessage": "发送消息", "menu": "菜单",
        },
        "sections": {
            "features": "核心能力", "products": "产品",
            "portfolio": "近期项目", "posts": "最新文章",
            "stats": "数据总览", "process": "发展历程",
            "contact": "取得联系", "about": "关于我们",
        },
        "categories": {"ai": "LED", "api": "控制器", "research": "项目"},
        "products": {
            "claude_opus": "LED 灯条", "claude_sonnet": "铝槽",
            "claude_haiku": "射灯",
        },
        "project": {"viewProject": "查看项目"},
        "pages": {
            "home": "首页", "products": "产品", "portfolio": "项目",
            "posts": "博客", "about": "关于我们", "pricing": "日目", "contact": "联系",
        },
        "contact": {
            "phone": "电话", "mobile": "手机", "email": "邮箱",
            "address": "地址", "businessHours": "营业时间",
            "sendMessage": "给我们留言", "name": "姓名", "message": "留言内容",
            "formName": "姓名", "formEmail": "邮箱", "formPhone": "电话",
            "formCompany": "公司", "formMessage": "留言",
            "formSend": "发送留言",
            "formMissingAction": "请先在后台配置表单提交地址。",
        },
        "about": {
            "title": "关于德恩基",
            "subtitle": "展示道具与互动产品的电子解决方案",
        },
        "footer": {
            "copyright": "版权所有。",
            "privacy": "隐私政策", "terms": "服务条款",
        },
    }

    # --- zh-TW (从 zh-CN 简→繁) ---
    data["zh-TW"] = deepcopy(data["zh-CN"])
    def s2t_recursive(obj):
        if isinstance(obj, str):
            return s2t(obj)
        elif isinstance(obj, dict):
            return {k: s2t_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [s2t_recursive(v) for v in obj]
        return obj
    data["zh-TW"] = s2t_recursive(data["zh-TW"])

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print("[OK] translations.yaml updated")


# ============================================================
# 页面翻译
# ============================================================
def translate_pages():
    """将 zh-CN 页面翻译为 zh-TW 和 en"""
    zh_cn_pages_dir = SITE_DIR / "lang" / "zh-CN" / "pages"
    zh_tw_pages_dir = SITE_DIR / "lang" / "zh-TW" / "pages"
    en_pages_dir = SITE_DIR / "lang" / "en" / "pages"

    zh_tw_pages_dir.mkdir(parents=True, exist_ok=True)
    en_pages_dir.mkdir(parents=True, exist_ok=True)

    # 获取所有 zh-CN 页面文件
    page_files = sorted(zh_cn_pages_dir.glob("*.yaml"))

    for pf in page_files:
        # 读取原始文本（用于繁体转换）
        with open(pf, "r", encoding="utf-8") as f:
            raw = f.read()

        # 解析 YAML（用于英文翻译）
        data = yaml.safe_load(raw)

        filename = pf.name
        print(f"  Processing page: {filename}")

        # --- 繁体版本 (简→繁) ---
        tw_raw = s2t(raw)
        tw_path = zh_tw_pages_dir / filename
        with open(tw_path, "w", encoding="utf-8") as f:
            f.write(tw_raw)

        # --- 英文版本 ---
        en_data = translate_page_to_en(data, filename)
        en_path = en_pages_dir / filename
        with open(en_path, "w", encoding="utf-8") as f:
            yaml.dump(en_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"[OK] Translated {len(page_files)} page files")


def translate_page_to_en(data, filename):
    """将页面数据翻译为英文"""
    if data is None:
        return data
    result = deepcopy(data)

    # 页面级字段
    if "title" in result:
        result["title"] = PAGE_TITLE_EN.get(filename, result.get("title", ""))
    if "description" in result:
        result["description"] = PAGE_DESC_EN.get(filename, result.get("description", ""))

    # 翻译 modules
    if "modules" in result:
        for mod in result["modules"]:
            translate_module_en(mod)

    return result


def translate_module_en(mod):
    """翻译单个 module 的 data 字段"""
    if not mod or "data" not in mod:
        return

    d = mod["data"]
    mod_type = mod.get("type", "")

    # 通用文本字段
    for key in ["tag", "title", "desc", "heading", "subheading"]:
        if key in d and isinstance(d[key], str) and d[key]:
            d[key] = translate_text_en(d[key])

    # 按钮文本
    for key in ["btn", "primaryBtn", "secondaryBtn"]:
        if key in d and isinstance(d[key], str) and d[key]:
            d[key] = translate_text_en(d[key])

    # hero_banner slides
    if "slides" in d:
        for slide in d["slides"]:
            if not isinstance(slide, dict):
                continue
            for key in ["title", "subtitle", "primaryBtn", "secondaryBtn"]:
                if key in slide and isinstance(slide[key], str) and slide[key]:
                    slide[key] = translate_text_en(slide[key])

    # feature_grid features
    if "features" in d:
        for feat in d["features"]:
            if not isinstance(feat, dict):
                continue
            for key in ["title", "desc", "text"]:
                if key in feat and isinstance(feat[key], str) and feat[key]:
                    feat[key] = translate_text_en(feat[key])

    # highlight_card features
    if "features" in d:
        for feat in d["features"]:
            if isinstance(feat, dict) and "text" in feat:
                feat["text"] = translate_text_en(str(feat["text"]))

    # process_steps steps
    if "steps" in d:
        for step in d["steps"]:
            if not isinstance(step, dict):
                continue
            for key in ["title", "desc"]:
                if key in step and isinstance(step[key], str) and step[key]:
                    step[key] = translate_text_en(step[key])

    # stat_counter stats
    if "stats" in d:
        for stat in d["stats"]:
            if not isinstance(stat, dict):
                continue
            if "label" in stat and isinstance(stat["label"], str) and stat["label"]:
                stat["label"] = translate_text_en(stat["label"])

    # data_grid
    if "dataset" in d and isinstance(d["dataset"], str) and d["dataset"]:
        d["dataset"] = d["dataset"]  # dataset slug 不变


# ============================================================
# 数据文件翻译
# ============================================================
def translate_data_files():
    """将 zh-CN 数据文件翻译为 zh-TW 和 en"""
    zh_cn_data_dir = SITE_DIR / "lang" / "zh-CN" / "data"
    zh_tw_data_dir = SITE_DIR / "lang" / "zh-TW" / "data"
    en_data_dir = SITE_DIR / "lang" / "en" / "data"

    zh_tw_data_dir.mkdir(parents=True, exist_ok=True)
    en_data_dir.mkdir(parents=True, exist_ok=True)

    data_files = sorted(zh_cn_data_dir.glob("*.yaml"))

    for df in data_files:
        filename = df.name
        print(f"  Processing data: {filename}")

        # 读取原始文本
        with open(df, "r", encoding="utf-8") as f:
            raw = f.read()

        # --- 繁体版本 (简→繁) ---
        tw_raw = s2t(raw)
        tw_path = zh_tw_data_dir / filename
        with open(tw_path, "w", encoding="utf-8") as f:
            f.write(tw_raw)

        # --- 英文版本 ---
        with open(df, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data:
            en_data = translate_data_to_en(data, filename)
            en_path = en_data_dir / filename
            with open(en_path, "w", encoding="utf-8") as f:
                yaml.dump(en_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"[OK] Translated {len(data_files)} data files")


def translate_data_to_en(data, filename):
    """将数据文件翻译为英文"""
    result = deepcopy(data)

    # 处理 categories (products.yaml)
    if "categories" in result:
        for cat in result["categories"]:
            if "name" in cat:
                cat["name"] = translate_text_en(str(cat["name"]))

    # 处理 items - 数据文件可能是顶层列表或包含 items 键的字典
    if isinstance(result, list):
        items = result
    elif isinstance(result, dict):
        items = result.get("items", [])
    else:
        items = []

    for item in items:
        if not isinstance(item, dict):
            continue
        # 翻译文本字段
        for key in ["title", "name", "summary", "excerpt", "description", "category"]:
            if key in item and isinstance(item[key], str) and item[key]:
                item[key] = translate_text_en(item[key])

        # 翻译标签
        if "tags" in item:
            if isinstance(item["tags"], list):
                item["tags"] = [translate_text_en(str(t)) if isinstance(t, str) else t for t in item["tags"]]
            elif isinstance(item["tags"], str):
                item["tags"] = translate_text_en(item["tags"])

        # 翻译 specs
        if "specs" in item:
            for spec in item["specs"]:
                if not isinstance(spec, dict):
                    continue
                for key in ["name", "value"]:
                    if key in spec and isinstance(spec[key], str) and spec[key]:
                        spec[key] = translate_text_en(spec[key])

        # 翻译 body (HTML - 只翻译 HTML 外的中文文本)
        # 对于产品数据, body 中主要是技术规格，保留英文不变的部分
        # 保留 body 原文，不做翻译 (技术文档)

        # 翻译 featured_picks items
        if "modules" in item:
            for mod in item["modules"]:
                if mod and mod.get("type") == "featured_picks" and "data" in mod:
                    fd = mod["data"]
                    if "title" in fd and fd["title"]:
                        fd["title"] = translate_text_en(str(fd["title"]))
                    if "desc" in fd and fd["desc"]:
                        fd["desc"] = translate_text_en(str(fd["desc"]))
                    if "items" in fd:
                        for fi in fd["items"]:
                            if isinstance(fi, dict):
                                if "title" in fi and fi["title"]:
                                    fi["title"] = translate_text_en(str(fi["title"]))
                                if "desc" in fi and fi["desc"]:
                                    fi["desc"] = translate_text_en(str(fi["desc"]))

        # 翻译 item_data 中的 body (博客文章等)
        if "body" in item and isinstance(item["body"], str) and item["body"]:
            item["body"] = translate_html_body_en(item["body"], filename)

        # 翻译 detail_gallery 相关
        if "detail_gallery" in item and isinstance(item["detail_gallery"], dict):
            if "title" in item["detail_gallery"] and item["detail_gallery"]["title"]:
                item["detail_gallery"]["title"] = translate_text_en(str(item["detail_gallery"]["title"]))

    return result


def translate_html_body_en(body, filename):
    """翻译 HTML body 中的中文文本为英文"""
    import re

    # 常见中文→英文映射表（博客文章 body 中）
    BODY_TRANSLATIONS = {
        # 博客: 检测治具使用说明
        "检测治具使用说明": "Inspection Jig User Manual",
        "正常操作": "Normal Operation",
        "读取SD卡中文件": "Reading Files from SD Card",
        "功能键": "Function Keys",
        "设置值": "Setting Values",
        "定义标准值": "Defining Standard Values",
        "修改计数值": "Modifying Count Values",
        "开机-上电, 输入电压:220V": "Power On - Input Voltage: 220V",
        "放置检测工件, 需要确保底部放平, 背后靠到定位块.": "Place the inspection workpiece, ensure the bottom is flat and the back is against the positioning block.",
        "按下绿色按钮, 进行检测, 只有2个结果, Pass 或 NG. 对应的计数值也会更新.": "Press the green button to inspect. Only 2 results: Pass or NG. The corresponding count will also update.",
        "拆开检具后盖, 用一字螺丝刀敲出SD卡.": "Open the back cover of the jig, use a flathead screwdriver to pop out the SD card.",
        "从SD中读取数据, 用 EXCEL 打开 csv 文件. 传感器的位置与列的对应关于请参考Excel中黄色行.": "Read data from the SD card, open the CSV file with Excel. Refer to the yellow rows in Excel for sensor position and column mapping.",
        "放回SD卡, 检查SD卡是否正常工作": "Reinsert the SD card and check if it is working properly",
        "诊断 -> 硬件 -> SD卡": "Diagnostics -> Hardware -> SD Card",
        "显示测试的数量, PASSED(合格品):xx, NOGOOD(不良品):xx, TOTAL:xx.": "Display test counts: PASSED: xx, NOGOOD: xx, TOTAL: xx.",
        "显示当前传感器的值, 范围:0-1000, 若没有放置工件, 数组为1000.": "Display current sensor values, range: 0-1000. If no workpiece is placed, the value is 1000.",
        "设置的范围值, +/-0.15 的距离, 建议值为90": "Set range value, +/-0.15 distance, recommended value: 90",
        "阈值最小值, 范围在500-700": "Minimum threshold value, range: 500-700",
        "按上下键, 直到出现 时间: Sat. 22 20 和 日期: 2023-08-09": "Press up/down keys until Time: Sat. 22 20 and Date: 2023-08-09 appears",
        "按ESC进入": "Press ESC to enter",
        "进入设置内容, 非指定的内容, 请勿随意设置.": "Enter settings. Do not change unspecified items.",
        "设置传感器": "Set Sensors",
        "LOGO! 设置 -> 编程 -> 设置参数": "LOGO! Settings -> Programming -> Set Parameters",
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
        # 博客: 兰蔻
        "产品标识": "Product Identification",
        "日常操作": "Daily Operation",
        "正常使用": "Normal Use",
        "非触发状态, 侧板的白色灯光有呈 渐亮->渐暗->渐亮 不断循环.": "In non-triggered state, the side panel white light cycles: fade-in -> fade-out -> fade-in.",
        "手放在传感器下方, 贴近人造石台面的位置, 等待1秒钟, 就会有乳液滴到手背上.": "Place your hand under the sensor, close to the artificial stone surface. Wait 1 second, and lotion will drop onto the back of your hand.",
        "滴液体的过程中, 侧板的灯光为 白色常亮. 乳液滴出后, 灯光回复呼吸渐变的效果": "During dispensing, the side panel light stays solid white. After the lotion drops, the light returns to breathing gradient effect.",
        "滴完一滴后, 需要间隔5秒钟, 才可以再次触发.": "After one drop, wait 5 seconds before triggering again.",
        "更换小黑瓶": "Replacing the Genifique Bottle",
        "更换电池": "Replacing the Battery",
        "其他问题": "Other Issues",
        "瓶子中的乳液用完后, 需要更换新的瓶子. 具体步骤如下:": "When the lotion in the bottle runs out, replace with a new bottle. Steps:",
        "A – Logo 盖和瓶帽向上取下来.": "A - Remove the logo cap and bottle cap upwards.",
        "B – 将弯管从空瓶内抽出来.": "B - Pull the curved tube out from the empty bottle.",
        "C – 拧下白色\"定制瓶盖\", 并将其拧到新的小黑瓶上.": "C - Unscrew the white custom cap and screw it onto the new Genifique bottle.",
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
        "C – 拔出插在设备的插头, 取下电池. 换回充满电的电池.": "C - Unplug the connector from the device, remove the battery, and replace with a fully charged battery.",
        "D – 将充电口的插头放在凹槽内.": "D - Place the charging port plug in the recess.",
        "E – 将LOGO盖放在顶部. 请注意 LOGO 的角度. 有3组磁铁, 可以微调角度.": "E - Place the logo cap on top. Note the logo angle. There are 3 sets of magnets for fine-tuning.",
        "F – 按下电源开关.": "F - Press the power switch.",
        "G – 无电量电池充电备用.": "G - Charge the depleted battery for backup.",
        "电池的电压为12V. 只能用12.6V的充电器为其充电.": "The battery voltage is 12V. Only use a 12.6V charger.",
        "禁止使用其他电压的充电器为其充电.": "Do NOT use chargers with other voltages.",
        "如果您遇到其他问题, 请联系德恩基的项目王经理: 139 1377 5186": "If you encounter other issues, please contact Dengtec Project Manager Mr. Wang: 139 1377 5186",
        # 博客: 兰蔻模型道具
        "兰蔻模型道具的使用说明": "Lancôme Model Prop User Manual",
        "更换小黑瓶": "Replacing the Genifique Bottle",
        "更换电池": "Replacing the Battery",
        # 2023 EURO SHOP
        "2023 EURO SHOP": "2023 EURO SHOP",
        "2023 EURO SHOP 展览项目分享，展示可编程发光LOGO和发光字等创新产品": "2023 EURO SHOP Exhibition Project Sharing — showcasing programmable illuminated logos and light-up letters",
        "可编程发光LOGO, 发光字": "Programmable Illuminated Logo & Letters",
        # 纱巾橱窗
        "纱巾橱窗": "Scarf Window Display",
        "纱巾橱窗项目，结合灯光和展示效果，为品牌店铺打造独特的橱窗展示。": "Scarf window display project — combining lighting and display effects to create distinctive window displays for brand stores.",
        # 植村秀
        "植村秀 店铺的霓虹灯": "Neon Lights at Shu Uemura Store",
        "植村秀店铺使用的霓虹灯产品，结合LED灯条技术，为品牌店铺打造独特的灯光效果": "Neon light products used in Shu Uemura stores, combining LED strip technology to create distinctive lighting effects for brand stores.",
        # 阿迪达斯
        "阿迪达斯店铺的渐变灯管和视频播放器": "Gradient Light Tubes & Video Players at Adidas Store",
        "阿迪达斯店铺使用的渐变灯管和视频播放器项目，通过档位开关切换播放视频，相应的LED点亮产品底座": "Gradient light tubes and video player project for Adidas stores — video playback switched via gear selector, with corresponding LEDs illuminating the product base.",
    }

    # 替换中文标题（<h3>, <h4> 标签中的中文）
    for cn, en in BODY_TRANSLATIONS.items():
        body = body.replace(cn, en)

    # 替换 <p> 中的常见中文内容
    # 保留 HTML 标签结构，只翻译文本内容
    return body


# ============================================================
# 英文本翻译映射
# ============================================================

PAGE_TITLE_EN = {
    "about.yaml": "About Us",
    "aluminum-profile.yaml": "Aluminum Profiles",
    "blog.yaml": "Blog",
    "cable-connector.yaml": "Cables & Connectors",
    "contact.yaml": "Contact Us",
    "holograms.yaml": "Hologram Display",
    "home.yaml": "Home",
    "led-strip.yaml": "LED Strips",
    "modules.yaml": "Modules",
    "portfolio.yaml": "Portfolio",
    "posts.yaml": "Posts",
    "powerptrack.yaml": "Power Track",
    "power-supplier.yaml": "Power Supply",
    "pricing.yaml": "Pricing",
    "products.yaml": "Products",
    "projects.yaml": "Recent Projects",
    "spot-light.yaml": "Spot Lights",
}

PAGE_DESC_EN = {
    "home.yaml": "Dengtec website homepage — showcasing electronic product development, display prop controllers, interactive systems, and recent projects.",
    "about.yaml": "Learn about Dengtec — electronics for the display props industry since 2014.",
    "contact.yaml": "Contact Dengtec — reach out for product inquiries, custom development, and pricing.",
    "led-strip.yaml": "LED strips — various specifications, custom lengths, color temperatures, and voltages.",
    "aluminum-profile.yaml": "Aluminum profiles for LED strips — various shapes and sizes.",
    "spot-light.yaml": "LED spot lights for display showcases and retail environments.",
    "holograms.yaml": "Holographic display devices — multiple sizes, multi-unit sync, Bluetooth control, wireless projection.",
    "cable-connector.yaml": "Cables and connectors for LED installations.",
    "powerptrack.yaml": "Power track / conductive track systems.",
    "power-supplier.yaml": "Power supply units for LED systems.",
    "projects.yaml": "Recent projects — showcasing electronic solutions for display and interactive products.",
    "blog.yaml": "Blog — industry insights, technical articles, and project stories.",
    "products.yaml": "Products — electronic components and solutions for display props industry.",
}

# 常用中→英词汇映射
TEXT_EN_MAP = {
    # 页面内容
    "德恩基电子科技": "Dengtec Electronic Technology",
    "提供展示道具行业的电子产品": "Electronics for the Display Props Industry",
    "近期项目": "Recent Projects",
    "联系我们": "Contact Us",
    "日目 / RIMU 项目": "RIMU Project",
    "查看详情": "View Details",
    "查看项目": "View Projects",
    "全息投影设备": "Holographic Display Devices",
    "多种尺寸可选，支持多台同步、蓝牙控制、无线投屏": "Multiple sizes available, supports multi-unit sync, Bluetooth control, and wireless projection",
    "电路设计": "Circuit Design",
    "专业的电路设计与开发": "Professional circuit design and development",
    "编程开发": "Programming & Development",
    "嵌入式编程与控制系统": "Embedded programming and control systems",
    "结构设计": "Structural Design",
    "产品外观与结构设计": "Product appearance and structural design",
    "传感器应用": "Sensor Applications",
    "各类传感器集成方案": "Various sensor integration solutions",
    "互动系统": "Interactive Systems",
    "人机交互系统开发": "Human-computer interaction system development",
    "核心展示": "Core Showcase",
    "从概念到落地": "From Concept to Reality",
    "从概念设计到产品落地，提供完整的电子产品解决方案": "From concept design to product realization, providing complete electronic product solutions",
    "精选项目": "Featured Project",
    "定制服务": "Custom Services",
    "电路板设计，编程，导光板": "Circuit Board Design, Programming, Light Guide Plates",
    "从电路板设计、嵌入式编程到导光板制作，提供完整的电子产品定制开发服务，为兰蔻、雅诗兰黛等知名品牌打造专属展示道具。": "From circuit board design and embedded programming to light guide plate fabrication, we provide complete custom electronic product development services, creating exclusive display props for renowned brands like Lancôme and Estée Lauder.",
    "了解服务详情": "Learn More About Services",
    "磁吸传感器": "Magnetic Sensors",
    "动态光效": "Dynamic Light Effects",
    "MP3播放器": "MP3 Player",
    "内置电池": "Built-in Battery",
    "创新技术": "Innovative Technology",
    "产品模型及自动滴液": "Product Models & Automatic Liquid Dispensing",
    "为品牌展示定制开发的自动滴液装置，集成精密流体控制、传感器感应、动态灯光效果等技术，为兰蔻等品牌打造沉浸式产品体验。": "Custom-developed automatic liquid dispensing devices for brand displays, integrating precision fluid control, sensor detection, and dynamic lighting effects to create immersive product experiences for brands like Lancôme.",
    "最新博客": "Latest Blog Posts",
    "了解行业动态、技术分享和项目经验": "Industry insights, technical articles, and project experience",
    "关于我们": "About Us",
    "了解 Nova AI 如何构建冷静、实用且安全的 AI 产品。": "Learn about how Dengtec provides electronic solutions for display and interactive products.",
    "联系方式": "Contact Information",
    "联系 Nova AI 团队，咨询产品、定价和企业方案。": "Contact the Dengtec team for product inquiries, pricing, and custom solutions.",
    "昆山德恩基电子科技有限公司": "Kunshan Dengtec Electronic Technology Co., Ltd.",
    "昆山德恩基电子科技有限公司于2014年成立，主要致力于展示道具行业的产品开发，设计及生产制作，尤其是电子方面的零部件，我们服务过的品牌有雅诗兰黛，兰蔻，迪奥，倩碧，Sk-II，碧欧泉，赫莲娜，科颜氏，羽西，植村秀，ADIDAS，NIKE，小米，DYSON，A.O.史密斯，优衣库，大疆，来伊份，苹果，美诺等众多品牌．": "Kunshan Dengtec Electronic Technology Co., Ltd. was established in 2014. We specialize in product development, design, and manufacturing for the display props industry, particularly electronic components. We have served brands including Estée Lauder, Lancôme, Dior, Clinique, SK-II, Biotherm, Helena Rubinstein, Kiehl's, Yue Sai, Shu Uemura, Adidas, Nike, Xiaomi, Dyson, A.O. Smith, Uniqlo, DJI, Laiyifen, Apple, Miele, and many more.",
    "参与过的项目": "Projects We've Worked On",
    "我们可以协助您实现您的创意.": "We can help bring your ideas to life.",
    "过去的几年里, 我们服务了几十个品牌和上百个项目. 积累了很多的经验.": "Over the years, we have served dozens of brands and hundreds of projects, accumulating extensive experience.",
    "创建历史": "Years Established",
    "客户": "Clients",
    "品牌": "Brands",
    "项目": "Projects",
    "历史进程": "Our Journey",
    "德恩基创始人 谷永林 供职于化妆品展示架行业, 从事结构设计的工作.": "Dengtec founder Gu Yonglin worked in the cosmetics display rack industry, specializing in structural design.",
    "起初为原先服务的公司提供LED灯条及灯光控制器。 注册了dengtec.com的域名,deng+tec hnology": "Initially provided LED strips and lighting controllers for the company he previously worked for. Registered the domain dengtec.com (deng + technology).",
    "实现视频点播功能 使用树莓派实现博朗的视频点播功能，将视频播放器的成本降低了非常多.": "Implemented video-on-demand functionality using Raspberry Pi for Braun, dramatically reducing video player costs.",
    "Since 2014": "Since 2014",
    # 产品页面标题
    "LED 灯条": "LED Strips",
    "铝槽": "Aluminum Profiles",
    "射灯": "Spot Lights",
    "全息投影": "Hologram Display",
    "线材及接插件": "Cables & Connectors",
    "导电槽": "Power Track",
    "电源": "Power Supply",
    "博客": "Blog",
    # 产品数据翻译
    "相关产品": "Related Products",
    "定制灯条需要1-2天的交期!": "Custom LED strips require 1-2 days lead time!",
    "固定的参数": "Fixed Parameters",
    "可定制的参数": "Customizable Parameters",
    "电压": "Voltage",
    "输入电压": "Input Voltage",
    "灯珠数": "LED Count",
    "1米的灯珠数量": "LEDs per meter",
    "灯条宽度": "Strip Width",
    "灯珠封装": "LED Package",
    "白光灯珠": "White LED",
    "可以定制的色温": "Customizable color temperature",
    "非白光灯珠": "Non-white LED",
    "彩色灯珠": "Color LED",
    "显色指数": "CRI (Color Rendering Index)",
    "白光灯有效": "Applicable to white LEDs",
    "功率": "Power",
    "灯珠功率可以根据需求定制.": "LED power can be customized based on requirements.",
    "详细规格参数请查看产品规格书。": "Please refer to the product datasheet for detailed specifications.",
    "规格书 - PDF": "Datasheet - PDF",
    "规格书 - DXF": "Datasheet - DXF",
    "规格书 - STP": "Datasheet - STP",
    "2D 图纸 - DXF": "2D Drawing - DXF",
    "3D 图纸 - STP": "3D Drawing - STP",
    # 标签翻译
    "AI 模型": "LED Products",
    "开发者工具": "Development Tools",
    "企业能力": "Components",
    "推理": "LED Strips",
    "代码生成": "Controllers",
    "企业": "Enterprise",
    "均衡": "Balanced",
    "生产": "Production",
    "通用": "General Purpose",
    "高速": "High Speed",
    "实时": "Real-time",
    "轻量": "Lightweight",
    "多模态": "Multimodal",
    "自动化": "Automation",
    "分析": "Analysis",
    "安全": "Safety",
    "评估": "Evaluation",
    "LED相关": "LED Related",
    "控制器": "Controllers",
    "设计相关": "Design Related",
    "临时项目": "Temporary Projects",
    "控制器及传感器": "Controllers & Sensors",
    "模块": "Modules",
    "灯光": "Lighting",
    "灯/米": "LEDs/m",
    "板宽": "Width",
    "封装": "Package",
}


def translate_text_en(text):
    """将中文文本翻译为英文"""
    if not text or not isinstance(text, str):
        return text

    # 先尝试完整匹配
    if text in TEXT_EN_MAP:
        return TEXT_EN_MAP[text]

    # 如果文本基本是英文/数字，不做翻译
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    if ascii_chars > len(text) * 0.7:
        return text

    # 对于混合内容，保留原文（避免翻译错误）
    # 后续可逐步扩展翻译表
    return text


# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 60)
    print("Site 6 Translation Script")
    print("=" * 60)

    print("\n[1/4] Translating settings.yaml...")
    translate_settings()

    print("\n[2/4] Translating translations.yaml...")
    translate_translations()

    print("\n[3/4] Translating page files (pages/)...")
    translate_pages()

    print("\n[4/4] Translating data files (data/)...")
    translate_data_files()

    print("\n" + "=" * 60)
    print("All translations completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
