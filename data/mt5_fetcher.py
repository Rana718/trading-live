from __future__ import annotations

import pandas as pd

_TIMEFRAME_MAP = {
    "M1": "TIMEFRAME_M1",
    "M5": "TIMEFRAME_M5",
    "M15": "TIMEFRAME_M15",
    "M30": "TIMEFRAME_M30",
    "H1": "TIMEFRAME_H1",
    "H4": "TIMEFRAME_H4",
    "D1": "TIMEFRAME_D1",
}


def _import_mt5():
    try:
        import MetaTrader5 as mt5  # type: ignore

        return mt5
    except Exception as exc:
        raise RuntimeError(
            "MetaTrader5 package is not available. Install with `pip install MetaTrader5` on Windows "
            "and ensure MT5 terminal is installed and logged in."
        ) from exc


def _resolve_timeframe(mt5, timeframe_name: str):
    attr = _TIMEFRAME_MAP.get(timeframe_name.upper(), "TIMEFRAME_M1")
    return getattr(mt5, attr)


def fetch_mt5_ohlcv(mt5_symbol: str, timeframe_name: str, bars: int = 300) -> pd.DataFrame:
    mt5 = _import_mt5()
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")

    try:
        timeframe = _resolve_timeframe(mt5, timeframe_name)
        rates = mt5.copy_rates_from_pos(mt5_symbol, timeframe, 0, bars)
        if rates is None or len(rates) == 0:
            raise RuntimeError(f"No MT5 OHLCV data for symbol={mt5_symbol}")

        df = pd.DataFrame(rates)
        df["timestamp"] = pd.to_datetime(df["time"], unit="s")
        df = df[["timestamp", "open", "high", "low", "close"]].copy()
        df.set_index("timestamp", inplace=True)
        return df.astype({"open": "float64", "high": "float64", "low": "float64", "close": "float64"})
    finally:
        mt5.shutdown()


def fetch_mt5_current_price(mt5_symbol: str) -> float:
    mt5 = _import_mt5()
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")

    try:
        tick = mt5.symbol_info_tick(mt5_symbol)
        if tick is None:
            raise RuntimeError(f"No MT5 tick for symbol={mt5_symbol}")

        bid = float(getattr(tick, "bid", 0.0) or 0.0)
        ask = float(getattr(tick, "ask", 0.0) or 0.0)
        if bid > 0 and ask > 0:
            return (bid + ask) / 2
        if bid > 0:
            return bid
        if ask > 0:
            return ask
        raise RuntimeError(f"Invalid MT5 tick values for symbol={mt5_symbol}")
    finally:
        mt5.shutdown()
