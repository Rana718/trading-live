import requests
import pandas as pd
from config import COIN_ID


def fetch_ohlcv() -> pd.DataFrame:
    """Fetch last 24h OHLCV for the configured coin from CoinGecko (free, no key)."""
    url = f"https://api.coingecko.com/api/v3/coins/{COIN_ID}/ohlc"
    resp = requests.get(url, params={"vs_currency": "jpy", "days": "1"}, timeout=10)
    resp.raise_for_status()
    data = resp.json()  # [[timestamp_ms, o, h, l, c], ...]
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df


def fetch_current_price() -> float:
    url = "https://api.coingecko.com/api/v3/simple/price"
    resp = requests.get(url, params={"ids": COIN_ID, "vs_currencies": "jpy"}, timeout=10)
    resp.raise_for_status()
    return resp.json()[COIN_ID]["jpy"]
