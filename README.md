# 24/7 Crypto Live Stream System

自動でXRP/JPYチャート解説＋ニュース読み上げをYouTubeライブ配信するシステムです。

## セットアップ

### 必要なもの
- Python 3.11+
- FFmpeg (`sudo apt install ffmpeg` or Windows installer)
- [VOICEVOX](https://voicevox.hiroshiba.jp/) — ローカルで起動しておく

### インストール
```bash
uv sync
```

### 設定 (`config.py`)
| 項目 | 説明 |
|------|------|
| `COIN_ID` | CoinGeckoのコインID（例: `"ripple"`, `"bitcoin"`） |
| `COIN_SYMBOL` | 画面表示名（例: `"XRP/JPY"`） |
| `NEWS_FEEDS` | RSSフィードURLのリスト（自由に追加・削除可） |
| `VOICEVOX_SPEAKER` | VOICEVOXの話者ID |
| `YOUTUBE_STREAM_KEY` | YouTubeのストリームキー ← **必ず設定** |
| `CHART_REFRESH_SEC` | チャート更新間隔（秒） |
| `NEWS_INTERVAL_SEC` | ニュース読み上げ間隔（秒） |

### 起動
```bash
# VOICEVOXを先に起動してから:
uv run python main.py
```

### VPS自動起動 (systemd)
```ini
# /etc/systemd/system/trading-live.service
[Unit]
Description=Trading Live Stream
After=network.target

[Service]
WorkingDirectory=/path/to/trading_live
ExecStart=/path/to/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable --now trading-live
```

## プロジェクト構成
```
config.py          # ← ユーザー設定ファイル（ここだけ編集すればOK）
main.py            # メインループ
data/
  price_fetcher.py # CoinGecko価格取得
  news_fetcher.py  # RSSニュース取得
chart/
  chart_renderer.py # ローソク足チャート生成
overlay/
  frame_composer.py # テロップ合成
audio/
  tts.py           # VOICEVOX TTS
  narrator.py      # ナレーション文生成
stream/
  ffmpeg_streamer.py # FFmpeg → YouTube RTMP
```
