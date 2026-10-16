# -*- coding: utf-8 -*-
"""图形验证码：Pillow 自绘，答案存 session，无第三方依赖。

用途：在"发送短信/邮件验证码"之前挡一道，防止脚本机器人批量刷发码接口
（尤其防短信轰炸烧阿里云余额）。这是发码前的第一道闸门，和后端限流互补。

设计取舍：
- 字符集避开易混字符（0/O/1/I/l/2/Z 等），降低人眼误认率。
- 答案只存 session（不落库），一次性：校验后立即失效，防重放。
- 大小写不敏感校验：手机端输入大写字母麻烦，宽容一点提升可用性。
"""
import io
import random
import secrets
import string

from PIL import Image, ImageDraw, ImageFont

# 会话中存放答案与生成时间的 key
_SESSION_KEY = 'captcha_answer'
_SESSION_TIME_KEY = 'captcha_time'
# 验证码有效期（秒）：太短用户来不及输，太长失去意义
_TTL_SECONDS = 300
# 去掉易混字符后的字符集：无 0/O/1/I/L、无 2/Z、无 5/S
_ALPHABET = 'ABCDEFGHJKMNPQRTUVWXY346789'
_LENGTH = 4
_WIDTH, _HEIGHT = 130, 44


def generate(session):
    """生成一张验证码图片，把答案写入 session，返回 PNG 字节。"""
    # 答案用 secrets（密码学安全），不用可预测的 random；random 仅用于下方图像噪声/颜色。
    answer = ''.join(secrets.choice(_ALPHABET) for _ in range(_LENGTH))
    session[_SESSION_KEY] = answer.upper()
    # 用 time.time 会破坏 workflow 可复现，但这是运行期 Web 请求，正常使用
    import time
    session[_SESSION_TIME_KEY] = time.time()

    img = Image.new('RGB', (_WIDTH, _HEIGHT), _rand_color(230, 255))
    draw = ImageDraw.Draw(img)
    font = _load_font()

    # 逐字符绘制：轻微上下抖动 + 每字随机深色，增加机器识别难度
    step = _WIDTH // (_LENGTH + 1)
    for i, ch in enumerate(answer):
        x = step * (i + 1) - step // 2 + random.randint(-3, 3)
        y = random.randint(2, 10)
        draw.text((x, y), ch, font=font, fill=_rand_color(0, 110))

    # 干扰线与噪点：数量适中，别把人也挡住
    for _ in range(4):
        draw.line(
            [(random.randint(0, _WIDTH), random.randint(0, _HEIGHT)),
             (random.randint(0, _WIDTH), random.randint(0, _HEIGHT))],
            fill=_rand_color(120, 200), width=1)
    for _ in range(90):
        draw.point((random.randint(0, _WIDTH), random.randint(0, _HEIGHT)),
                   fill=_rand_color(120, 220))

    buf = io.BytesIO()
    img.save(buf, 'PNG')
    return buf.getvalue()


def verify(session, user_input):
    """校验用户输入；成功或失败都清掉 session 答案（一次性，防重放）。"""
    answer = session.pop(_SESSION_KEY, None)
    created = session.pop(_SESSION_TIME_KEY, None)
    if not answer or not user_input:
        return False
    import time
    if created is None or time.time() - created > _TTL_SECONDS:
        return False
    return user_input.strip().upper() == answer


def _rand_color(lo, hi):
    return (random.randint(lo, hi), random.randint(lo, hi), random.randint(lo, hi))


def _load_font():
    """优先用较大字号的内置字体；老版本 Pillow 不支持 size 参数则回退。"""
    try:
        # Pillow 10+ 的 load_default 支持 size，字大才看得清
        return ImageFont.load_default(size=28)
    except TypeError:
        return ImageFont.load_default()
