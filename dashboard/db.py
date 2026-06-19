"""SQLite-backed config store. Single source of truth — replaces .env and runtime_settings.json."""
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.db")

_DEFAULTS = {
    "youtube_stream_key": "",
    "chart_source": "coingecko",
    "chart_refresh_sec": "60",
    "news_interval_sec": "300",
    "symbol_rotate_sec": "300",
    "tts_voice": "ja-JP-NanamiNeural",
    "tts_rate": "+0%",
    "tts_volume": "+0%",
    "video_quality": "720p",
    "symbols": json.dumps([
        {"coin_id": "ripple",  "symbol": "XRP/JPY", "vs_currency": "jpy", "binance_symbol": "", "tradingview_symbol": "CRYPTOCAP:XRP"},
        {"coin_id": "bitcoin", "symbol": "BTC/JPY", "vs_currency": "jpy", "binance_symbol": "", "tradingview_symbol": "CRYPTOCAP:BTC"},
    ]),
    "news_sources": json.dumps([
        {"type": "rss", "url": "https://cointelegraph.com/rss/tag/xrp"},
        {"type": "rss", "url": "https://decrypt.co/feed"},
    ]),
}


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)")
        for k, v in _DEFAULTS.items():
            c.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (k, v))


def get(key: str) -> str:
    with _conn() as c:
        row = c.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
        return row["value"] if row else _DEFAULTS.get(key, "")


def get_all() -> dict:
    with _conn() as c:
        rows = c.execute("SELECT key, value FROM config").fetchall()
        return {r["key"]: r["value"] for r in rows}


def set_many(data: dict):
    with _conn() as c:
        for k, v in data.items():
            c.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (k, v))


init_db()
