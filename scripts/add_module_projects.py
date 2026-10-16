"""
从 cn.dengtec.com/modules/ 导入 5 个模块产品作为项目
（跳过已存在的 RIMU）
下载封面图片到本地，生成 YAML 数据条目
"""
import os
import sys
import time
import hashlib
import urllib.request
import urllib.parse
import ssl
from pathlib import Path

# 项目根目录
BASE_DIR = Path(r"f:\dengtec\mycompany.website11")
UPLOADS_DIR = BASE_DIR / "sites" / "6" / "assets" / "uploads"
PROJECTS_YAML = BASE_DIR / "sites" / "6" / "lang" / "zh-CN" / "data" / "projects.yaml"

# 创建上传目录
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# 忽略 SSL 证书验证（某些 CDN 可能有问题）
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

# ---------------------------------------------------------------------------
# 5 个新项目的数据定义
# ---------------------------------------------------------------------------
# 封面图CDN地址 -> 本地文件名
# 详情画廊图CDN地址 -> 本地文件名

PROJECTS = [
    {
        "id": 10,
        "title": "可控数码管",
        "slug": "7segment-displays",
        "description": "可定制的数码管，有不同大小的尺寸，可以控制变化的速度。",
        "tags": ["LED", "模块"],
        "body": (
            "<h3><b>主要特征</b></h3>"
            "<ol>"
            "<li>可定制尺寸：提供超大、大、中、小多种规格</li>"
            "<li>速度可控：支持控制数码管显示变化的速度</li>"
            "<li>塑胶外壳：耐用且轻便</li>"
            "<li>交期：2 周</li>"
            "</ol>"
            '<table data-rte-border="1" data-rte-widths="1">'
            '<colgroup><col style="width:50%"><col style="width:50%"></colgroup>'
            "<tbody>"
            '<tr><td style="width:50%;"><p>设计者</p></td><td style="width:50%;"><p>Young</p></td></tr>'
            '<tr><td style="width:50%;"><p>材料</p></td><td style="width:50%;"><p>塑胶</p></td></tr>'
            '<tr><td style="width:50%;"><p>尺寸</p></td><td style="width:50%;"><p>可定制</p></td></tr>'
            '<tr><td style="width:50%;"><p>交期</p></td><td style="width:50%;"><p>2 周</p></td></tr>'
            "</tbody>"
            "</table>"
        ),
        "cover_url": "https://cdn.dengtec.com/cnw/2023/04/Ntube04.jpg",
        "gallery_urls": [
            "https://cdn.dengtec.com/cnw/2023/04/Ntube03.jpg",
            "https://cdn.dengtec.com/cnw/2023/04/Ntube02.jpg",
            "https://cdn.dengtec.com/cnw/2023/04/Ntube04.jpg",
            "https://cdn.dengtec.com/cnw/2023/04/more-1024x684.jpg",
        ],
    },
    {
        "id": 11,
        "title": "圣诞包装盒",
        "slug": "christmas-package",
        "description": "一个非常薄的箱子，它包括动态光效、磁性传感器、MP3音乐播放。",
        "tags": ["LED", "传感器", "控制器", "模块"],
        "body": (
            "<h3><b>主要特征</b></h3>"
            "<ol>"
            "<li>磁性传感器：开盒自动触发灯光和音乐</li>"
            "<li>MP3 音乐播放：内置高品质音频播放</li>"
            "<li>动态灯光效果：多种光效模式可切换</li>"
            "<li>超薄设计：轻盈便携的包装结构</li>"
            "</ol>"
            '<table data-rte-border="1" data-rte-widths="1">'
            '<colgroup><col style="width:50%"><col style="width:50%"></colgroup>'
            "<tbody>"
            '<tr><td style="width:50%;"><p>品牌</p></td><td style="width:50%;"><p>芝华士</p></td></tr>'
            '<tr><td style="width:50%;"><p>日期</p></td><td style="width:50%;"><p>2021-12</p></td></tr>'
            '<tr><td style="width:50%;"><p>开发周期</p></td><td style="width:50%;"><p>2 周</p></td></tr>'
            "</tbody>"
            "</table>"
        ),
        "cover_url": "https://cdn.dengtec.com/cnw/2023/04/chivas_09-e1682588655802.jpg",
        "gallery_urls": [
            "https://cdn.dengtec.com/cnw/2023/04/chivas_09-e1682588655802.jpg",
            "https://cdn.dengtec.com/cnw/2023/04/chivas_01.jpg",
            "https://cdn.dengtec.com/cnw/2023/04/chivas_03.jpg",
            "https://cdn.dengtec.com/cnw/2023/04/chivas_05.jpg",
            "https://cdn.dengtec.com/cnw/2023/04/chivas_04.jpg",
        ],
    },
    {
        "id": 12,
        "title": "COB 定制灯板",
        "slug": "cob-led-plate",
        "description": "定制的LED灯板，特别适应空间小的情形。颜色、图案、功率均可按需定制。",
        "tags": ["LED", "模块"],
        "body": (
            "<h3><b>主要特征</b></h3>"
            "<ol>"
            "<li>颜色可定制：支持多种色温和 RGB 配置</li>"
            "<li>图案可定制：任意形状和图案的灯板设计</li>"
            "<li>功率可定制：根据应用场景灵活调整</li>"
            "<li>超薄设计：特别适合空间受限的场合</li>"
            "<li>交期：2 周</li>"
            "</ol>"
            '<table data-rte-border="1" data-rte-widths="1">'
            '<colgroup><col style="width:50%"><col style="width:50%"></colgroup>'
            "<tbody>"
            '<tr><td style="width:50%;"><p>颜色</p></td><td style="width:50%;"><p>可定制</p></td></tr>'
            '<tr><td style="width:50%;"><p>图案</p></td><td style="width:50%;"><p>可定制</p></td></tr>'
            '<tr><td style="width:50%;"><p>功率</p></td><td style="width:50%;"><p>可定制</p></td></tr>'
            '<tr><td style="width:50%;"><p>交期</p></td><td style="width:50%;"><p>2 周</p></td></tr>'
            "</tbody>"
            "</table>"
        ),
        "cover_url": "https://cdn.dengtec.com/cnw/2023/02/COB_LED_05.jpg",
        "gallery_urls": [
            "https://cdn.dengtec.com/cnw/2023/02/COB_LED_05.jpg",
            "https://cdn.dengtec.com/cnw/2023/02/COB_LED_06.jpg",
            "https://cdn.dengtec.com/cnw/2023/02/COB_LED_03.jpg",
            "https://cdn.dengtec.com/cnw/2023/02/COB_LED_04.jpg",
            "https://cdn.dengtec.com/cnw/2023/02/COB_LED_07.jpg",
            "https://cdn.dengtec.com/cnw/2023/02/COB_LED_08.jpg",
            "https://cdn.dengtec.com/cnw/2023/02/COB_LED_11.jpg",
            "https://cdn.dengtec.com/cnw/2023/02/COB_LED_12.jpg",
            "https://cdn.dengtec.com/cnw/2023/02/COB_LED_02.jpg",
        ],
    },
    {
        "id": 13,
        "title": "EM19000 UM",
        "slug": "em19000",
        "description": "可以贴片和焊接的微处理器模块单元，非常适合快速开发项目的过程中使用。基于 ATmega328 处理器。",
        "tags": ["控制器", "模块"],
        "body": (
            "<h3><b>主要特征</b></h3>"
            "<ol>"
            "<li>焊接容易：可满足快速开发需求</li>"
            "<li>可以贴片：支持小批量生产应用</li>"
            "<li>接口丰富：可连接多种输入输出模块</li>"
            "<li>小巧尺寸：38.1 × 25.4 mm</li>"
            "</ol>"
            '<table data-rte-border="1" data-rte-widths="1">'
            '<colgroup><col style="width:50%"><col style="width:50%"></colgroup>'
            "<tbody>"
            '<tr><td style="width:50%;"><p>处理器</p></td><td style="width:50%;"><p>ATmega328</p></td></tr>'
            '<tr><td style="width:50%;"><p>Flash</p></td><td style="width:50%;"><p>32 KB</p></td></tr>'
            '<tr><td style="width:50%;"><p>SRAM</p></td><td style="width:50%;"><p>2 KB</p></td></tr>'
            '<tr><td style="width:50%;"><p>EEPROM</p></td><td style="width:50%;"><p>1 KB</p></td></tr>'
            '<tr><td style="width:50%;"><p>时钟频率</p></td><td style="width:50%;"><p>16 MHz</p></td></tr>'
            '<tr><td style="width:50%;"><p>尺寸</p></td><td style="width:50%;"><p>38.1 × 25.4 mm</p></td></tr>'
            "</tbody>"
            "</table>"
        ),
        "cover_url": "https://cdn.dengtec.com/cnw/2021/12/EM19000_6.jpg",
        "gallery_urls": [
            "https://cdn.dengtec.com/cnw/2021/12/EM19000_6.jpg",
        ],
    },
    {
        "id": 14,
        "title": "EM19021 恒压转横流模块",
        "slug": "em19021",
        "description": "恒压转恒流驱动模块，适用于 LED 照明和控制器场景，保证每个灯珠亮度一致。",
        "tags": ["LED", "控制器", "模块"],
        "body": (
            "<h3><b>主要特征</b></h3>"
            "<ol>"
            "<li>恒压转恒流：将恒定电压转换为恒定电流输出</li>"
            "<li>亮度一致：确保每个 LED 灯珠亮度均匀</li>"
            "<li>稳定可靠：适用于长时间运行的灯具场景</li>"
            "<li>易于集成：紧凑设计方便嵌入各类产品</li>"
            "</ol>"
            '<table data-rte-border="1" data-rte-widths="1">'
            '<colgroup><col style="width:50%"><col style="width:50%"></colgroup>'
            "<tbody>"
            '<tr><td style="width:50%;"><p>类型</p></td><td style="width:50%;"><p>恒压转恒流</p></td></tr>'
            '<tr><td style="width:50%;"><p>应用</p></td><td style="width:50%;"><p>LED 驱动 / 控制器</p></td></tr>'
            "</tbody>"
            "</table>"
        ),
        "cover_url": "https://cdn.dengtec.com/cnw/2021/09/EM01-1.jpg",
        "gallery_urls": [
            "https://cdn.dengtec.com/cnw/2021/09/EM01-1.jpg",
            "https://cdn.dengtec.com/cnw/2021/09/em04.jpg",
            "https://cdn.dengtec.com/cnw/2021/09/em05.jpg",
            "https://cdn.dengtec.com/cnw/2021/09/em02.jpg",
            "https://cdn.dengtec.com/cnw/2021/09/em03.jpg",
        ],
    },
]


def download_image(url, save_path, max_retries=3):
    """下载图片到本地，支持重试"""
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
                data = resp.read()
                if len(data) < 100:
                    print(f"  [警告] {url} 下载内容过小 ({len(data)} bytes)，跳过")
                    return None
                with open(save_path, "wb") as f:
                    f.write(data)
                print(f"  [OK] {os.path.basename(save_path)} ({len(data)} bytes)")
                return save_path
        except Exception as e:
            print(f"  [重试 {attempt+1}/{max_retries}] {url}: {e}")
            time.sleep(1)
    print(f"  [失败] {url}")
    return None


def make_local_filename(url, prefix):
    """根据URL生成唯一本地文件名"""
    # 取URL最后一段作为基础名
    parsed = urllib.parse.urlparse(url)
    basename = os.path.basename(parsed.path)
    # 去掉查询参数
    basename = basename.split("?")[0]
    # 添加前缀和时间戳避免冲突
    name, ext = os.path.splitext(basename)
    if not ext:
        ext = ".jpg"
    timestamp = int(time.time() * 1000)
    hash_str = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{prefix}-{timestamp}-{hash_str}{ext}"


def generate_yaml_entry(proj, cover_filename, gallery_filenames):
    """生成一个项目的 YAML 条目"""
    lines = []
    lines.append(f"- id: {proj['id']}")
    lines.append(f"  title: {proj['title']}")
    lines.append(f"  slug: {proj['slug']}")
    lines.append(f"  cover: /assets/uploads/{cover_filename}")
    lines.append(f"  date: ''")
    lines.append(f"  name: ''")
    lines.append(f"  category: ''")
    lines.append(f"  description: {proj['description']}")
    lines.append(f"  tags_visible: true")
    lines.append(f"  tags:")
    for tag in proj["tags"]:
        lines.append(f"  - {tag}")
    lines.append(f"  price: ''")
    # body 需要特殊处理换行
    body = proj["body"]
    lines.append(f"  body: {yaml_quote(body)}")
    lines.append(f"  rte_clicked_editor_idx: ''")
    lines.append(f"  detail_gallery:")
    lines.append(f"    visible: true")
    lines.append(f"    images:")
    for gf in gallery_filenames:
        lines.append(f"    - url: /assets/uploads/{gf}")
    lines.append(f"  style_bg-color: ''")
    lines.append(f"  modules:")
    lines.append(f"  - type: item_data")
    lines.append(f"    order: 1")
    lines.append(f"    variant: default")
    lines.append(f"    data: {{}}")
    return "\n".join(lines)


def yaml_quote(text):
    """用双引号包裹 YAML 字符串，正确转义"""
    # 转义反斜杠和双引号
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def main():
    print("=" * 60)
    print("开始处理 5 个模块项目...")
    print("=" * 60)

    new_entries = []

    for proj in PROJECTS:
        print(f"\n--- [{proj['id']}] {proj['title']} ---")

        # 下载封面图
        cover_filename = make_local_filename(proj["cover_url"], f"projects-cover-{proj['slug']}")
        cover_path = UPLOADS_DIR / cover_filename
        print(f"  封面图: {proj['cover_url']}")
        result = download_image(proj["cover_url"], cover_path)
        if not result:
            print(f"  [错误] 封面图下载失败，跳过该项目")
            continue

        # 下载详情画廊图
        gallery_filenames = []
        for i, gurl in enumerate(proj["gallery_urls"]):
            gname = make_local_filename(gurl, f"projects-gallery-{proj['slug']}-{i+1}")
            gpath = UPLOADS_DIR / gname
            print(f"  画廊图 {i+1}: {gurl}")
            result = download_image(gurl, gpath)
            if result:
                gallery_filenames.append(gname)

        if not gallery_filenames:
            # 至少用封面图作为画廊第一张
            gallery_filenames = [cover_filename]

        # 生成 YAML 条目
        entry = generate_yaml_entry(proj, cover_filename, gallery_filenames)
        new_entries.append(entry)
        print(f"  [完成] 生成 YAML 条目")

    if not new_entries:
        print("\n[错误] 没有成功生成任何项目条目！")
        sys.exit(1)

    # 读取现有 projects.yaml
    print(f"\n读取现有文件: {PROJECTS_YAML}")
    with open(PROJECTS_YAML, "r", encoding="utf-8") as f:
        existing = f.read()

    # 追加新条目
    new_content = existing.rstrip() + "\n" + "\n".join(new_entries) + "\n"

    # 写回
    print(f"写入文件: {PROJECTS_YAML}")
    with open(PROJECTS_YAML, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"\n{'=' * 60}")
    print(f"完成！新增 {len(new_entries)} 个项目")
    for proj in PROJECTS:
        print(f"  - [{proj['id']}] {proj['title']} ({proj['slug']})")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
