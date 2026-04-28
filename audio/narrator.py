import pandas as pd


def calc_change_pct(df: pd.DataFrame, price: float) -> float:
    if df.empty:
        return 0.0
    open_price = float(df["open"].iloc[0])
    if open_price == 0:
        return 0.0
    return (price - open_price) / open_price * 100


def build_chart_narration(symbol: str, df: pd.DataFrame, price: float) -> str:
    """Generate a short Japanese narration sentence from price data."""
    if df.empty:
        return f"現在{symbol}は¥{price:,.2f}付近で推移しています。"

    change_pct = calc_change_pct(df, price)
    direction = "上昇" if change_pct >= 0 else "下落"
    high = float(df["high"].max())
    low = float(df["low"].min())

    return (
        f"現在{symbol}は¥{price:,.2f}付近で推移しています。"
        f"本日の始値から{abs(change_pct):.1f}%の{direction}トレンドです。"
        f"本日の高値は¥{high:,.2f}、安値は¥{low:,.2f}です。"
    )


def build_news_narration(headline: str) -> str:
    return f"最新ニュースをお伝えします。{headline}"
