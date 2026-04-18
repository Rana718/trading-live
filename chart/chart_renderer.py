import io
import mplfinance as mpf
from PIL import Image
import pandas as pd
from config import WIDTH, HEIGHT, COIN_SYMBOL


def render_chart(df: pd.DataFrame) -> Image.Image:
    """Render OHLCV candlestick chart, return as PIL Image."""
    buf = io.BytesIO()
    mpf.plot(
        df,
        type="candle",
        style="charles",
        title=COIN_SYMBOL,
        mav=(7, 25),
        volume=False,
        savefig=dict(fname=buf, format="png", dpi=100),
        figsize=(WIDTH / 100, HEIGHT / 100),
    )
    buf.seek(0)
    return Image.open(buf).convert("RGB")
