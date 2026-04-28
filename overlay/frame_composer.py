from PIL import Image, ImageDraw, ImageFont
from config import WIDTH, HEIGHT
import datetime

_FONT_SIZE_LARGE = 36
_FONT_SIZE_SMALL = 24


def _font(size: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def compose_frame(chart_img: Image.Image, symbol: str, price: float, change_pct: float, subtitle: str) -> Image.Image:
    """Overlay price telop + subtitle onto chart image, return final frame."""
    frame = chart_img.resize((WIDTH, HEIGHT)).copy()
    draw = ImageDraw.Draw(frame)

    # Top-left: symbol + price
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    direction = "+" if change_pct >= 0 else "-"
    top_text = f"{symbol}  ¥{price:,.2f}  |  {direction}{abs(change_pct):.2f}%  |  {now}"
    draw.rectangle([0, 0, WIDTH, 50], fill=(0, 0, 0, 180))
    draw.text((10, 8), top_text, font=_font(_FONT_SIZE_LARGE), fill=(255, 220, 0))

    # Bottom: subtitle / narration telop
    if subtitle:
        draw.rectangle([0, HEIGHT - 60, WIDTH, HEIGHT], fill=(0, 0, 0, 200))
        draw.text((10, HEIGHT - 50), subtitle, font=_font(_FONT_SIZE_SMALL), fill=(255, 255, 255))

    return frame
