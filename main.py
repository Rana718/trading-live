"""
Main orchestrator — runs the 24/7 YouTube live stream loop.
"""
import time
import logging
import threading

from config import FPS, CHART_REFRESH_SEC, NEWS_INTERVAL_SEC
from data.price_fetcher import fetch_ohlcv, fetch_current_price
from data.news_fetcher import fetch_latest_news
from chart.chart_renderer import render_chart
from overlay.frame_composer import compose_frame
from audio.narrator import build_chart_narration, build_news_narration
from audio.tts import synthesize
from stream.ffmpeg_streamer import FFmpegStreamer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

_state = {
    "chart_img": None,
    "price": 0.0,
    "subtitle": "",
    "df": None,
}
_news_queue: list[str] = []
_streamer: FFmpegStreamer | None = None


def _speak(text: str):
    """Synthesize text and play into the live stream (non-blocking)."""
    global _streamer
    try:
        wav = synthesize(text)
        if _streamer and _streamer.alive:
            _streamer.play_audio(wav)
    except Exception as e:
        log.warning("TTS error: %s", e)


def _refresh_chart():
    while True:
        try:
            df = fetch_ohlcv()
            price = fetch_current_price()
            img = render_chart(df)
            narration = build_chart_narration(df, price)
            _state.update({"chart_img": img, "price": price, "subtitle": narration, "df": df})
            log.info("Chart refreshed. Price: ¥%.2f", price)
            threading.Thread(target=_speak, args=(narration,), daemon=True).start()
        except Exception as e:
            log.error("Chart refresh error: %s", e)
        time.sleep(CHART_REFRESH_SEC)


def _refresh_news():
    while True:
        try:
            headlines = fetch_latest_news()
            _news_queue.extend(headlines)
            log.info("Fetched %d new headlines", len(headlines))
        except Exception as e:
            log.error("News fetch error: %s", e)
        time.sleep(NEWS_INTERVAL_SEC)


def _run_stream():
    global _streamer
    _streamer = FFmpegStreamer()
    _streamer.start()
    log.info("Stream started.")

    frame_interval = 1.0 / FPS
    last_news_time = time.time()

    while True:
        if not _streamer.alive:
            log.warning("FFmpeg died — restarting stream...")
            _streamer.stop()
            time.sleep(3)
            _streamer.start()

        # Inject news periodically
        if _news_queue and (time.time() - last_news_time) >= NEWS_INTERVAL_SEC:
            headline = _news_queue.pop(0)
            text = build_news_narration(headline)
            _state["subtitle"] = text
            last_news_time = time.time()
            threading.Thread(target=_speak, args=(text,), daemon=True).start()

        chart_img = _state.get("chart_img")
        if chart_img is None:
            time.sleep(1)
            continue

        frame = compose_frame(chart_img, _state["price"], _state["subtitle"])
        _streamer.send_frame(frame)
        time.sleep(frame_interval)


def main():
    log.info("Loading initial data...")
    try:
        df = fetch_ohlcv()
        price = fetch_current_price()
        img = render_chart(df)
        narration = build_chart_narration(df, price)
        _state.update({"chart_img": img, "price": price, "subtitle": narration, "df": df})
    except Exception as e:
        log.error("Initial load failed: %s", e)

    threading.Thread(target=_refresh_chart, daemon=True).start()
    threading.Thread(target=_refresh_news, daemon=True).start()

    while True:
        try:
            _run_stream()
        except KeyboardInterrupt:
            log.info("Stopped by user.")
            if _streamer:
                _streamer.stop()
            break
        except Exception as e:
            log.error("Stream crashed: %s — restarting in 10s", e)
            time.sleep(10)


if __name__ == "__main__":
    main()
