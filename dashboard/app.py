"""Flask dashboard — config UI + stream Start/Stop control."""
import json
import os
import signal
import subprocess
import sys
import threading

from flask import Flask, jsonify, redirect, render_template, request, url_for

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dashboard.db import get_all, set_many

app = Flask(__name__)

_stream_proc: subprocess.Popen | None = None
_stream_lock = threading.Lock()

PYTHON = sys.executable
MAIN_PY = os.path.join(os.path.dirname(os.path.dirname(__file__)), "main.py")


def _stream_running() -> bool:
    return _stream_proc is not None and _stream_proc.poll() is None


@app.route("/")
def index():
    cfg = get_all()
    try:
        symbols = json.loads(cfg.get("symbols", "[]"))
    except Exception:
        symbols = []
    try:
        news_sources = json.loads(cfg.get("news_sources", "[]"))
    except Exception:
        news_sources = []
    return render_template("index.html", cfg=cfg, symbols=symbols,
                           news_sources=news_sources, running=_stream_running())


@app.route("/save", methods=["POST"])
def save():
    f = request.form
    # Build symbols list from dynamic form rows
    symbols = []
    i = 0
    while f.get(f"sym_coin_id_{i}"):
        symbols.append({
            "coin_id":            f.get(f"sym_coin_id_{i}", ""),
            "symbol":             f.get(f"sym_symbol_{i}", ""),
            "vs_currency":        f.get(f"sym_vs_{i}", "jpy"),
            "binance_symbol":     f.get(f"sym_binance_{i}", ""),
            "tradingview_symbol": f.get(f"sym_tv_{i}", ""),
        })
        i += 1

    news_sources = []
    j = 0
    while f.get(f"news_url_{j}"):
        news_sources.append({
            "type": f.get(f"news_type_{j}", "rss"),
            "url":  f.get(f"news_url_{j}", ""),
        })
        j += 1

    set_many({
        "youtube_stream_key": f.get("youtube_stream_key", ""),
        "chart_source":       f.get("chart_source", "coingecko"),
        "video_quality":      f.get("video_quality", "720p"),
        "chart_refresh_sec":  f.get("chart_refresh_sec", "60"),
        "news_interval_sec":  f.get("news_interval_sec", "300"),
        "symbol_rotate_sec":  f.get("symbol_rotate_sec", "300"),
        "tts_voice":          f.get("tts_voice", "ja-JP-NanamiNeural"),
        "tts_rate":           f.get("tts_rate", "+0%"),
        "tts_volume":         f.get("tts_volume", "+0%"),
        "symbols":            json.dumps(symbols),
        "news_sources":       json.dumps(news_sources),
    })
    return redirect(url_for("index"))


@app.route("/stream/start", methods=["POST"])
def stream_start():
    global _stream_proc
    with _stream_lock:
        if _stream_running():
            return jsonify({"status": "already_running"})
        _stream_proc = subprocess.Popen([PYTHON, MAIN_PY])
    return jsonify({"status": "started"})


@app.route("/stream/stop", methods=["POST"])
def stream_stop():
    global _stream_proc
    with _stream_lock:
        if not _stream_running():
            return jsonify({"status": "not_running"})
        try:
            _stream_proc.send_signal(signal.SIGINT)
            _stream_proc.wait(timeout=10)
        except Exception:
            _stream_proc.kill()
        _stream_proc = None
    return jsonify({"status": "stopped"})


@app.route("/stream/status")
def stream_status():
    return jsonify({"running": _stream_running()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
