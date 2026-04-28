from PIL import Image, ImageDraw
from config import WIDTH, HEIGHT
from .font_manager import get_font
import datetime

_FONT_SIZE_LARGE = 36
_FONT_SIZE_SMALL = 18


def _font(size: int):
    return get_font(size)


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> str:
    if not text:
        return ""
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = char
    if current:
        lines.append(current)
    return "\n".join(lines[:2])


def compose_frame(chart_img: Image.Image, symbol: str, price: float, change_pct: float, subtitle: str) -> Image.Image:
    """Overlay price telop + subtitle onto chart image, return final frame."""
    now_dt = datetime.datetime.now()
    frame = chart_img  # Chart already sized to exact WIDTH x HEIGHT
    draw = ImageDraw.Draw(frame)

    # Top-left: symbol + price (with second-level timestamp for some motion)
    now = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    direction = "+" if change_pct >= 0 else "-"
    top_text = f"{symbol}  ¥{price:,.2f}  |  {direction}{abs(change_pct):.2f}%  |  {now}"
    draw.rectangle([0, 0, WIDTH, 58], fill=(0, 0, 0, 200))
    draw.text((12, 7), top_text, font=_font(_FONT_SIZE_LARGE), fill=(255, 220, 0))

    # Bottom: subtitle / narration telop (full width, increased height for better readability)
    if subtitle:
        subtitle_font = _font(_FONT_SIZE_SMALL)
        wrapped = _wrap_text(draw, subtitle, subtitle_font, WIDTH - 28)
        draw.rectangle([0, HEIGHT - 60, WIDTH, HEIGHT], fill=(0, 0, 0, 210))
        draw.multiline_text((14, HEIGHT - 52), wrapped, font=subtitle_font, fill=(255, 255, 255), spacing=3)

    return frame
