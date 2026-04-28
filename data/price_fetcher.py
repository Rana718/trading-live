import requests
import pandas as pd

from data.binance_fetcher import fetch_binance_ohlcv, fetch_binance_current_price


def fetch_coingecko_ohlcv(coin_id: str, vs_currency: str, days: str = "1") -> pd.DataFrame:
    """Fetch OHLCV from CoinGecko (free, no API key)."""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
    resp = requests.get(url, params={"vs_currency": vs_currency, "days": days}, timeout=10)
    resp.raise_for_status()
    data = resp.json()  # [[timestamp_ms, o, h, l, c], ...]
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df.astype({"open": "float64", "high": "float64", "low": "float64", "close": "float64"})


def fetch_coingecko_current_price(coin_id: str, vs_currency: str) -> float:
    """Fetch current price from CoinGecko (free, no API key)."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    resp = requests.get(url, params={"ids": coin_id, "vs_currencies": vs_currency}, timeout=10)
    resp.raise_for_status()
    return float(resp.json()[coin_id][vs_currency])


def fetch_ohlcv_by_source(source: str, coin_id: str, vs_currency: str, binance_symbol: str = "") -> pd.DataFrame:
    """Fetch OHLCV from selected crypto API source."""
    source_name = source.strip().lower()
    
    if source_name == "binance":
        if not binance_symbol:
            raise RuntimeError("binance source requires binance_symbol in runtime_settings.json")
        return fetch_binance_ohlcv(binance_symbol)
    
    # Default to CoinGecko
    return fetch_coingecko_ohlcv(coin_id, vs_currency)


def fetch_current_price_by_source(source: str, coin_id: str, vs_currency: str, binance_symbol: str = "") -> float:
    """Fetch current price from selected crypto API source."""
    source_name = source.strip().lower()
    
    if source_name == "binance":
        if not binance_symbol:
            raise RuntimeError("binance source requires binance_symbol in runtime_settings.json")
        return fetch_binance_current_price(binance_symbol)
    
    # Default to CoinGecko
    return fetch_coingecko_current_price(coin_id, vs_currency)
