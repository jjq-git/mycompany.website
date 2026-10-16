---
name: template-image-optimize
description: "图片优化(批量转换 WebP / 调整尺寸 / 压缩)"
---

当用户说"优化图片"、"压缩图片"、"转 WebP"、"图片太大"时触发.

图片优化是核心信念 #5(速度是产品的一部分)的关键实现.
系统在"店主上传图片时"自动处理(参见 `routes.py:_save_uploaded_image()`),
本技能用于模板开发过程中的批量图片处理.

当前实现(`routes.py:53-83`):
- 上传时自动转 WebP(quality=86, method=6)
- 单文件处理,不做批量

## 当前系统自动处理

`routes.py:_save_uploaded_image()` 在上传时自动处理:

```python
image = Image.open(file_storage.stream)
first_frame = next(ImageSequence.Iterator(image)).convert('RGBA')
background = Image.new('RGBA', first_frame.size, (255, 255, 255, 0))
background.alpha_composite(first_frame)
background.save(output_path, 'WEBP', quality=86, method=6)
```

参数说明:
- `quality=86`:WebP 质量,86 是视觉无损的平衡点
- `method=6`:最慢但压缩率最高
- 自动处理 GIF 首帧(静态化)
- 输出 RGBA 模式(保留透明度)

图片大小限制(`docs/publish.md`):
| 类型 | 单文件上限 |
|------|-----------|
| 图片 | 5 MB |
| PDF/文档 | 20 MB |
| 视频 | 50 MB |

## 批量优化模板图片

用于优化 `site_templates/<name>/seed_data/` 中的示例图片.

```python
# 在 flask shell 中运行
from pathlib import Path
from PIL import Image, ImageSequence

def optimize_to_webp(input_path, output_path, quality=86):
    """将图片转为 WebP,保留 RGBA"""
    image = Image.open(input_path)
    first_frame = next(ImageSequence.Iterator(image)).convert('RGBA')
    background = Image.new('RGBA', first_frame.size, (255, 255, 255, 0))
    background.alpha_composite(first_frame)
    background.save(output_path, 'WEBP', quality=quality, method=6)
    orig_size = input_path.stat().st_size
    new_size = output_path.stat().st_size
    reduction = (1 - new_size / orig_size) * 100
    print(f'{input_path.name}: {orig_size/1024:.0f}KB → {new_size/1024:.0f}KB (-{reduction:.0f}%)')

# 批量处理模板静态资源中的图片
template = 'dengtec'
static_dir = Path(f'site_templates/{template}/static')
for img in static_dir.rglob('*'):
    if img.suffix.lower() in ('.jpg', '.jpeg', '.png', '.gif'):
        optimize_to_webp(img, img.with_suffix('.webp'))
```

## 生成多尺寸图片

按 `docs/publish.md` 定义的尺寸:

| 用途 | 尺寸 | 格式 |
|------|------|------|
| 缩略图(卡片用) | 600 × 450 | WebP |
| 中图(详情用) | 1200 × 900 | WebP |
| 原图(备份) | 原始尺寸 | WebP |

```python
from PIL import Image

def resize_image(input_path, output_dir, sizes=None):
    """生成多个尺寸的 WebP"""
    if sizes is None:
        sizes = {
            'thumb': (600, 450),
            'medium': (1200, 900),
        }

    image = Image.open(input_path).convert('RGBA')
    name = input_path.stem

    for label, size in sizes.items():
        resized = image.copy()
        resized.thumbnail(size, Image.LANCZOS)
        out = output_dir / f'{name}-{label}.webp'
        # 白色背景底
        bg = Image.new('RGBA', resized.size, (255, 255, 255, 255))
        bg.alpha_composite(resized)
        bg.save(out, 'WEBP', quality=86)
        print(f'{label}: {size[0]}x{size[1]} → {out.stat().st_size/1024:.0f}KB')
```

## 检查图片大小

```python
from pathlib import Path

def check_image_sizes(directory, max_kb=500):
    """检查目录中超过指定大小的图片"""
    for img in Path(directory).rglob('*'):
        if img.suffix.lower() in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
            size_kb = img.stat().st_size / 1024
            if size_kb > max_kb:
                print(f'⚠ {img.name}: {size_kb:.0f}KB (超过 {max_kb}KB)')

# 检查所有模板的静态资源
check_image_sizes('site_templates', max_kb=200)
```

## 推荐图片规格(给店主的指引)

虽然不是本技能的操作内容,但在设计模板上传入口时应该提示店主:

| 图片类型 | 推荐尺寸 | 最大文件 |
|----------|----------|----------|
| Logo | 200×60 或 120×120 | 100KB |
| 产品封面 | 1200×900 | 500KB |
| 横幅/首屏图 | 1920×1080 | 1MB |
| 头像 | 200×200 | 50KB |
| Favicon | 32×32 | 10KB |

## 依赖

图片处理依赖 Pillow(已在 `requirements.txt` 中):
```
pip install Pillow
```

## 关联技能

- `seed-data`:种子数据中的示例图片优化
- `new-template`:创建模板时的默认图片处理
- `publish-flow`:发布流程中的图片处理环节
