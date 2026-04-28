# Testing Guide (End-To-End)

This guide helps you validate the full streaming system from local run to production VPS.

## 1) Preflight Checks

- Python environment exists and dependencies are installed.
- FFmpeg is installed and available in PATH.
- VOICEVOX is running and reachable.
- .env file contains required keys.

### Commands

```bash
uv sync
which ffmpeg
```

## 2) Configuration Validation

Check these values in .env and config:

- YOUTUBE_STREAM_KEY is not empty.
- RUNTIME_SETTINGS_FILE points to an existing JSON file.
- CHART_SOURCE is set to `coingecko` or `mt5`.
- SYMBOL_ROTATE_SEC is set as expected.
- VOICEVOX_URL is reachable.
- runtime_settings.json contains valid symbols/news_sources entries.

## 3) Module-Level Smoke Tests

Run quick checks for each module before full stream.

### 3.1 Price Fetcher

```bash
uv run python -c "from data.price_fetcher import fetch_current_price, fetch_ohlcv; print(fetch_current_price('ripple','jpy')); print(fetch_ohlcv('ripple','jpy').tail(2))"
```

Expected:

- Current price prints as a number.
- OHLC dataframe prints rows without exceptions.

### 3.1-bis MT5 Price Fetcher (Windows/MT5運用時)

```bash
uv run python -c "from data.mt5_fetcher import fetch_mt5_current_price, fetch_mt5_ohlcv; print(fetch_mt5_current_price('XRPJPY')); print(fetch_mt5_ohlcv('XRPJPY','M1',50).tail(2))"
```

Expected:

- MT5 terminalログイン中で価格/ローソク足が取得できる。

### 3.2 News Fetcher

```bash
uv run python -c "from data.news_fetcher import fetch_latest_news; n=fetch_latest_news([{'type':'rss','url':'https://cointelegraph.com/rss/tag/xrp'}],5); print(len(n)); print(n[:3])"
```

Expected:

- Non-negative count.
- Headlines list prints.

### 3.3 Chart Renderer

```bash
uv run python -c "from data.price_fetcher import fetch_ohlcv; from chart.chart_renderer import render_chart; img=render_chart(fetch_ohlcv('ripple','jpy'),'XRP/JPY'); img.save('tmp_chart.png'); print('saved tmp_chart.png')"
```

Expected:

- tmp_chart.png is created and opens correctly.

### 3.4 Narration + TTS

```bash
uv run python -c "from data.price_fetcher import fetch_ohlcv, fetch_current_price; from audio.narrator import build_chart_narration; from audio.tts import synthesize; df=fetch_ohlcv('ripple','jpy'); p=fetch_current_price('ripple','jpy'); txt=build_chart_narration('XRP/JPY',df,p); wav=synthesize(txt); print('wav bytes', len(wav))"
```

Expected:

- Non-zero wav byte size.

### 3.5 Overlay Composer

```bash
uv run python -c "from PIL import Image; from overlay.frame_composer import compose_frame; img=Image.new('RGB',(1280,720),(20,20,20)); out=compose_frame(img, 'XRP/JPY', 123.45, 1.25, 'test subtitle'); out.save('tmp_frame.png'); print('saved tmp_frame.png')"
```

Expected:

- tmp_frame.png contains top/bottom text overlays.

## 4) Stream Pipeline Test

## Option A: Safe Local Dry Run (Recommended First)

Run app with an invalid or test stream key and observe logs for:

- chart refresh loop
- news fetch loop
- no fatal crashes

```bash
uv run python main.py
```

Expected:

- Repeating logs for chart/news.
- If RTMP rejects key, app should keep running and retry logic should trigger.
- MT5モードでは `mt5_symbol` 設定ミスがないこと。

## Option B: Real YouTube Test

- Use a private/unlisted test stream in YouTube Studio.
- Start app and verify:
  - video arrives
  - audio narration is audible
  - subtitle updates
  - stream remains stable for at least 30-60 minutes

## 5) Resilience Tests

### 5.1 FFmpeg Crash Recovery

- While running, kill ffmpeg process.
- Verify main loop restarts streamer automatically.

### 5.2 Network Interruption

- Disable network briefly and re-enable.
- Verify app continues and recovers without manual restart.

### 5.3 Reboot Auto-Start (VPS)

- Reboot server.
- Confirm service auto-starts and stream resumes.

## 6) Optional Syntax/Health Checks

```bash
/run/media/rana/DEV/freelance/jepanes/trading_live/.venv/bin/python -m compileall -q .
```

Expected:

- No output means no syntax compile issues detected.

## 7) Automated Tests (Current Status)

Current repository does not include pytest test files yet.

To enable automated tests later:

```bash
/run/media/rana/DEV/freelance/jepanes/trading_live/.venv/bin/python -m pip install pytest
/run/media/rana/DEV/freelance/jepanes/trading_live/.venv/bin/python -m pytest -q
```

## 8) Go-Live Checklist

- All smoke tests pass.
- 1-hour private stream test passes.
- Auto-restart test passes.
- Reboot auto-start test passes.
- Client sign-off on visuals, voice, and news sources.
