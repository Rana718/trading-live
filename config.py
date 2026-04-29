import os
import json
from dotenv import load_dotenv

load_dotenv()


def _load_runtime_settings() -> dict:
    settings_path = os.getenv("RUNTIME_SETTINGS_FILE", "runtime_settings.json")
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


_runtime = _load_runtime_settings()

# --- Symbols / rotation ---
SYMBOLS = _runtime.get("symbols", [
    {
        "coin_id": os.getenv("COIN_ID", "ripple"),
        "symbol": os.getenv("COIN_SYMBOL", "XRP/JPY"),
        "vs_currency": os.getenv("VS_CURRENCY", "jpy"),
    }
])
SYMBOL_ROTATE_SEC = int(os.getenv("SYMBOL_ROTATE_SEC", "300"))

# --- Market data source ---
# coingecko: CoinGecko API (free, recommended for crypto)
# binance: Binance REST API (free, real-time, requires API key or public endpoints)
CHART_SOURCE = os.getenv("CHART_SOURCE", "coingecko").strip().lower()
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "").strip()

# --- TradingView Widget ---
# Enable TradingView embedded chart for better UX
USE_TRADINGVIEW_WIDGET = os.getenv("USE_TRADINGVIEW_WIDGET", "true").strip().lower() in ("true", "1", "yes")
TRADINGVIEW_SYMBOL = os.getenv("TRADINGVIEW_SYMBOL", "CRYPTOCAP:XRP").strip()

# --- News sources (rss/scrape) ---
NEWS_SOURCES = _runtime.get("news_sources", [
    {"type": "rss", "url": "https://cointelegraph.com/rss/tag/xrp"},
    {"type": "rss", "url": "https://decrypt.co/feed"},
])

# --- TTS ---
TTS_ENGINE = os.getenv("TTS_ENGINE", "edge").strip().lower()
EDGE_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", "ja-JP-NanamiNeural").strip()
EDGE_TTS_RATE = os.getenv("EDGE_TTS_RATE", "+0%").strip()
EDGE_TTS_VOLUME = os.getenv("EDGE_TTS_VOLUME", "+0%").strip()

# --- Stream ---
YOUTUBE_RTMP_URL = "rtmp://a.rtmp.youtube.com/live2"
YOUTUBE_STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY", "")

# --- Video ---
# 配信の解像度とFPSは固定値にする
WIDTH = 1280
HEIGHT = 720
FPS = 24

# --- Timing (seconds) ---
CHART_REFRESH_SEC = int(os.getenv("CHART_REFRESH_SEC", "60"))
NEWS_INTERVAL_SEC = int(os.getenv("NEWS_INTERVAL_SEC", "300"))
