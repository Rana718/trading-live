import io
import mplfinance as mpf
from PIL import Image
import pandas as pd
from config import WIDTH, HEIGHT


def render_chart(df: pd.DataFrame, title: str) -> Image.Image:
    """Render OHLCV candlestick chart, return as PIL Image."""
    buf = io.BytesIO()
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
        figsize=(WIDTH / 100, HEIGHT / 100),
    )
    buf.seek(0)
    return Image.open(buf).convert("RGB")
