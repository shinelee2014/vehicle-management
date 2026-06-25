"""
照片水印处理工具
"""
import os
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from app.config import settings


def find_chinese_font(size: int = 24) -> ImageFont.FreeTypeFont:
    """查找系统中的中文字体"""
    # 常见中文字体路径（按优先级）
    font_paths = [
        # Linux (Docker)
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        # Windows
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    # 兜底
    return ImageFont.load_default()


def add_watermark(
    image_bytes: bytes,
    time_str: str = None,
    post_name: str = "",
    operator_name: str = "",
) -> bytes:
    """
    给照片添加水印
    返回处理后的图片二进制
    """
    if time_str is None:
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 加载图片
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")

    width, height = img.size

    # 动态计算字体大小（图片宽度的 2%）
    font_size = max(20, int(width * 0.02))
    font = find_chinese_font(font_size)

    # 构造水印文字
    watermark_text = settings.watermark_format.format(
        time=time_str,
        post=post_name,
        operator=operator_name,
    )

    # 绘制
    draw = ImageDraw.Draw(img)

    # 文字大小
    bbox = draw.textbbox((0, 0), watermark_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # 位置
    padding = 20
    if settings.watermark_position == "bottom_right":
        x = width - text_w - padding
        y = height - text_h - padding
    elif settings.watermark_position == "bottom_left":
        x = padding
        y = height - text_h - padding
    else:
        x = width - text_w - padding
        y = height - text_h - padding

    # 阴影（提高可读性）
    draw.text((x + 2, y + 2), watermark_text, font=font, fill=(0, 0, 0, 200))
    # 主文字
    draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255))

    # 输出
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=settings.photo_quality, optimize=True)
    return output.getvalue()


def save_photo(
    image_bytes: bytes,
    sub_dir: str = None,
) -> str:
    """
    保存照片到 NAS 本地盘
    返回相对路径（不含 BASE_DIR 前缀）
    """
    if sub_dir is None:
        sub_dir = datetime.now().strftime("%Y-%m-%d")

    full_dir = os.path.join(settings.photo_base_dir, sub_dir)
    os.makedirs(full_dir, exist_ok=True)

    # 文件名：时间戳 + 随机 6 位
    import uuid
    filename = f"{datetime.now().strftime('%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg"
    full_path = os.path.join(full_dir, filename)

    with open(full_path, "wb") as f:
        f.write(image_bytes)

    # 返回相对路径：YYYY-MM-DD/filename.jpg
    return f"{sub_dir}/{filename}"
