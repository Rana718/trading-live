"""All config comes from SQLite (set via web dashboard). No .env or runtime_settings.json needed."""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from dashboard.db import get

def _int(key, default):
    try:
        return int(get(key))
    except Exception:
        return default

def _json(key):
    try:
        return json.loads(get(key))
    except Exception:
        return []

# --- Symbols / rotation ---
SYMBOLS         = _json("symbols")
SYMBOL_ROTATE_SEC = _int("symbol_rotate_sec", 300)

# --- Market data source ---
CHART_SOURCE    = get("chart_source") or "coingecko"

# --- TradingView (kept for compatibility, not used in renderer) ---
USE_TRADINGVIEW_WIDGET = False
TRADINGVIEW_SYMBOL     = ""

# --- News ---
NEWS_SOURCES    = _json("news_sources")

# --- TTS ---
TTS_ENGINE      = "edge"
EDGE_TTS_VOICE  = get("tts_voice")  or "ja-JP-NanamiNeural"
EDGE_TTS_RATE   = get("tts_rate")   or "+0%"
EDGE_TTS_VOLUME = get("tts_volume") or "+0%"

# --- Stream ---
YOUTUBE_RTMP_URL   = "rtmp://a.rtmp.youtube.com/live2"
YOUTUBE_STREAM_KEY = get("youtube_stream_key")

# --- Video quality presets ---
_QUALITY_PRESETS = {
    "1080p": {"width": 1920, "height": 1080, "fps": 30, "bitrate": "4500k"},
    "720p":  {"width": 1280, "height":  720, "fps": 24, "bitrate": "2500k"},
    "480p":  {"width":  854, "height":  480, "fps": 24, "bitrate": "1000k"},
    "360p":  {"width":  640, "height":  360, "fps": 15, "bitrate":  "500k"},
}
_q = _QUALITY_PRESETS.get(get("video_quality") or "720p", _QUALITY_PRESETS["720p"])
WIDTH   = _q["width"]
HEIGHT  = _q["height"]
FPS     = _q["fps"]
VIDEO_BITRATE = _q["bitrate"]

# --- Timing ---
CHART_REFRESH_SEC = _int("chart_refresh_sec", 60)
NEWS_INTERVAL_SEC = _int("news_interval_sec", 300)
