import os
from dotenv import load_dotenv

load_dotenv()

# --- Coin / Symbol ---
COIN_ID = os.getenv("COIN_ID", "ripple")
COIN_SYMBOL = os.getenv("COIN_SYMBOL", "XRP/JPY")

# --- News RSS feeds (edit freely) ---
NEWS_FEEDS = [
    "https://cointelegraph.com/rss/tag/xrp",
    "https://decrypt.co/feed",
]

# --- VOICEVOX ---
VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://127.0.0.1:50021")
VOICEVOX_SPEAKER = int(os.getenv("VOICEVOX_SPEAKER", "1"))

# --- Stream ---
YOUTUBE_RTMP_URL = "rtmp://a.rtmp.youtube.com/live2"
YOUTUBE_STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY", "")

# --- Video ---
WIDTH, HEIGHT = 1280, 720
FPS = 30

# --- Timing (seconds) ---
CHART_REFRESH_SEC = 60
NEWS_INTERVAL_SEC = 300
