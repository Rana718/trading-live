import pandas as pd
from config import COIN_SYMBOL


def build_chart_narration(df: pd.DataFrame, price: float) -> str:
    """Generate a short Japanese narration sentence from price data."""
    if df.empty:
        return f"現在{COIN_SYMBOL}は¥{price:,.2f}付近で推移しています。"

    open_price = float(df["open"].iloc[0])
    change_pct = (price - open_price) / open_price * 100
    direction = "上昇" if change_pct >= 0 else "下落"
    high = float(df["high"].max())
    low = float(df["low"].min())

    return (
        f"現在{COIN_SYMBOL}は¥{price:,.2f}付近で推移しています。"
        f"本日の始値から{abs(change_pct):.1f}%の{direction}トレンドです。"
        f"本日の高値は¥{high:,.2f}、安値は¥{low:,.2f}です。"
    )


def build_news_narration(headline: str) -> str:
    return f"最新ニュースをお伝えします。{headline}"
