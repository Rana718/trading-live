"""Binance API support for real-time crypto prices."""
import requests
import pandas as pd


BINANCE_BASE_URL = "https://api.binance.com/api/v3"


def fetch_binance_ohlcv(symbol: str, interval: str = "1d", limit: int = 100) -> pd.DataFrame:
    """Fetch OHLCV from Binance for a trading pair symbol (e.g., 'XRPJPY', 'BTCUSDT')."""
    url = f"{BINANCE_BASE_URL}/klines"
    resp = requests.get(url, params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=10)
    resp.raise_for_status()
    data = resp.json()  # [[time, o, h, l, c, v, ...], ...]
    
    df = pd.DataFrame(
        [[row[0], float(row[1]), float(row[2]), float(row[3]), float(row[4])] for row in data],
        columns=["timestamp", "open", "high", "low", "close"],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df


def fetch_binance_current_price(symbol: str) -> float:
    """Fetch current price from Binance ticker for a trading pair symbol."""
    url = f"{BINANCE_BASE_URL}/ticker/price"
    resp = requests.get(url, params={"symbol": symbol}, timeout=10)
    resp.raise_for_status()
    return float(resp.json()["price"])
