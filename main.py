"""
Main orchestrator — runs the 24/7 YouTube live stream loop.
Config is read from SQLite (set via web dashboard at http://localhost:5000).
"""
import time
import logging
import threading
import importlib

import config as _cfg_module

def _cfg():
    """Reload config from SQLite so dashboard changes take effect without restart."""
    importlib.reload(_cfg_module)
    return _cfg_module

from data.price_fetcher import fetch_ohlcv_by_source, fetch_current_price_by_source
from data.news_fetcher import fetch_latest_news
from chart.chart_renderer import render_chart
from overlay.frame_composer import compose_frame
from overlay.font_manager import ensure_fonts_cached
from audio.narrator import build_chart_narration, build_news_narration, calc_change_pct
from audio.tts import synthesize
from stream.ffmpeg_streamer import FFmpegStreamer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

_state = {
    "chart_img": None,
    "price": 0.0,
    "change_pct": 0.0,
    "symbol": "",
    "coin_id": "",
    "vs_currency": "jpy",
    "binance_symbol": "",
    "tradingview_symbol": "",
    "subtitle": "",
    "df": None,
}
_news_queue: list[str] = []
_streamer: FFmpegStreamer | None = None
_symbol_idx = -1


def _next_symbol() -> dict:
    global _symbol_idx
    symbols = _cfg().SYMBOLS
    if not symbols:
        return {"coin_id": "ripple", "symbol": "XRP/JPY", "vs_currency": "jpy", "binance_symbol": "", "tradingview_symbol": "CRYPTOCAP:XRP"}
    _symbol_idx = (_symbol_idx + 1) % len(symbols)
    s = symbols[_symbol_idx]
    return {
        "coin_id":            s.get("coin_id", "ripple"),
        "symbol":             s.get("symbol", "XRP/JPY"),
        "vs_currency":        s.get("vs_currency", "jpy"),
        "binance_symbol":     s.get("binance_symbol", ""),
        "tradingview_symbol": s.get("tradingview_symbol", "CRYPTOCAP:XRP"),
    }


def _speak(text: str):
    global _streamer
    try:
        wav = synthesize(text)
        if wav and _streamer and _streamer.alive:
            _streamer.play_audio(wav)
    except Exception as e:
        log.warning("TTS error: %s", e)


def _refresh_chart():
    last_rotate = 0.0
    target = _next_symbol()
    while True:
        cfg = _cfg()
        try:
            if time.time() - last_rotate >= cfg.SYMBOL_ROTATE_SEC:
                target = _next_symbol()
                last_rotate = time.time()

            df = fetch_ohlcv_by_source(
                source=cfg.CHART_SOURCE,
                coin_id=target["coin_id"],
                vs_currency=target["vs_currency"],
                binance_symbol=target.get("binance_symbol", ""),
            )
            price = fetch_current_price_by_source(
                source=cfg.CHART_SOURCE,
                coin_id=target["coin_id"],
                vs_currency=target["vs_currency"],
                binance_symbol=target.get("binance_symbol", ""),
            )
            img = render_chart(df, target["symbol"])
            change_pct = calc_change_pct(df, price)
            narration = build_chart_narration(target["symbol"], df, price)
            _state.update({
                "chart_img": img, "price": price, "change_pct": change_pct,
                "symbol": target["symbol"], "coin_id": target["coin_id"],
                "vs_currency": target["vs_currency"],
                "binance_symbol": target.get("binance_symbol", ""),
                "tradingview_symbol": target.get("tradingview_symbol", ""),
                "subtitle": narration, "df": df,
            })
            log.info("Chart refreshed. %s Price: %.2f", target["symbol"], price)
        except Exception as e:
            log.error("Chart refresh error: %s", e)
        time.sleep(cfg.CHART_REFRESH_SEC)


def _refresh_news():
    while True:
        cfg = _cfg()
        try:
            headlines = fetch_latest_news(cfg.NEWS_SOURCES)
            _news_queue.extend(headlines)
            log.info("Fetched %d new headlines", len(headlines))
        except Exception as e:
            log.error("News fetch error: %s", e)
        time.sleep(cfg.NEWS_INTERVAL_SEC)


def _run_stream():
    global _streamer
    _streamer = FFmpegStreamer()
    _streamer.start()
    log.info("Stream started.")

    cfg = _cfg()
    frame_interval = 1.0 / cfg.FPS
    last_composed_frame = None
    last_compose_time = 0.0
    next_frame_time = time.time()
    last_chart_speak_time = 0.0
    last_news_speak_time = 0.0

    while True:
        if not _streamer.alive:
            log.warning("FFmpeg died — restarting stream...")
            _streamer.stop()
            time.sleep(3)
            _streamer.start()
            next_frame_time = time.time()

        cfg = _cfg()
        now = time.time()

        # News speak
        if _news_queue and (now - last_news_speak_time) >= cfg.NEWS_INTERVAL_SEC:
            headline = _news_queue.pop(0)
            text = build_news_narration(headline, _state.get("df"), _state.get("price", 0.0))
            _state["subtitle"] = text
            last_news_speak_time = now
            last_chart_speak_time = now
            last_compose_time = 0.0
            threading.Thread(target=_speak, args=(text,), daemon=True).start()

        # Chart analysis speak
        elif (now - last_chart_speak_time) >= cfg.CHART_REFRESH_SEC:
            df = _state.get("df")
            price = _state.get("price", 0.0)
            symbol = _state.get("symbol", "")
            if df is not None and price > 0 and symbol:
                text = build_chart_narration(symbol, df, price)
                _state["subtitle"] = text
                last_chart_speak_time = now
                last_compose_time = 0.0
                threading.Thread(target=_speak, args=(text,), daemon=True).start()

        chart_img = _state.get("chart_img")
        if chart_img is None:
            time.sleep(0.5)
            next_frame_time = time.time()
            continue

        now = time.time()
        if (now - last_compose_time) >= 0.5 or last_composed_frame is None:
            last_composed_frame = compose_frame(
                chart_img,
                _state.get("symbol", "N/A"),
                _state["price"],
                _state.get("change_pct", 0.0),
                _state["subtitle"],
            )
            last_compose_time = now

        if last_composed_frame:
            _streamer.send_frame(last_composed_frame)

        now = time.time()
        sleep_time = next_frame_time - now
        if sleep_time > 0:
            time.sleep(sleep_time)
        next_frame_time += frame_interval


def main():
    log.info("Ensuring fonts are cached...")
    ensure_fonts_cached()

    log.info("Loading initial data...")
    cfg = _cfg()
    try:
        target = _next_symbol()
        df = fetch_ohlcv_by_source(source=cfg.CHART_SOURCE, coin_id=target["coin_id"],
                                   vs_currency=target["vs_currency"], binance_symbol=target.get("binance_symbol", ""))
        price = fetch_current_price_by_source(source=cfg.CHART_SOURCE, coin_id=target["coin_id"],
                                              vs_currency=target["vs_currency"], binance_symbol=target.get("binance_symbol", ""))
        img = render_chart(df, target["symbol"])
        change_pct = calc_change_pct(df, price)
        narration = build_chart_narration(target["symbol"], df, price)
        _state.update({
            "chart_img": img, "price": price, "change_pct": change_pct,
            "symbol": target["symbol"], "coin_id": target["coin_id"],
            "vs_currency": target["vs_currency"],
            "binance_symbol": target.get("binance_symbol", ""),
            "tradingview_symbol": target.get("tradingview_symbol", ""),
            "subtitle": narration, "df": df,
        })
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
