import io
import mplfinance as mpf
from PIL import Image
import pandas as pd
from config import WIDTH, HEIGHT


def render_chart(df: pd.DataFrame, title: str) -> Image.Image:
    """Render OHLCV candlestick chart, return as PIL Image (full width)."""
    buf = io.BytesIO()
    # Render at 1.4x size to account for mplfinance margins, then resize to exact dimensions
    render_width = int(WIDTH * 1.3)
    render_height = int(HEIGHT * 1.3)
    
    bb = mpf.make_addplot(df["close"].rolling(20).mean() + 2 * df["close"].rolling(20).std(), color="dodgerblue")
    bb_low = mpf.make_addplot(df["close"].rolling(20).mean() - 2 * df["close"].rolling(20).std(), color="dodgerblue")
    mpf.plot(
        df,
        type="candle",
        style="charles",
        title=title,
        mav=(7, 25),
        addplot=[bb, bb_low],
        volume=False,
        savefig=dict(fname=buf, format="png", dpi=100),
        figsize=(render_width / 100, render_height / 100),
    )
    buf.seek(0)
    img = Image.open(buf).convert("RGB")
    # Resize to exact frame dimensions to fill complete width/height
    img = img.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    return img
