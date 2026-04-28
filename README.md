# 24/7 Crypto Live Stream System

暗号資産チャート解説＋ニュース読み上げをYouTubeライブ配信するシステムです。

主な機能:

- 複数銘柄の自動切り替え配信
- `coingecko` / `mt5` のチャートソース切替
- ローソク足 + 移動平均線 + ボリンジャーバンド表示
- VOICEVOXによるチャート/ニュース読み上げ
- 価格・変動率・字幕テロップ表示
- FFmpegによるRTMP自動配信とプロセス再起動

## セットアップ

### 必要なもの

- Python 3.11+
- FFmpeg (`sudo apt install ffmpeg` or Windows installer)
- [VOICEVOX](https://voicevox.hiroshiba.jp/) — ローカルで起動しておく

### インストール

```bash
uv sync
```

### 設定（通常は `.env` と `runtime_settings.json` を編集）

| 項目                    | 説明                                                 |
| ----------------------- | ---------------------------------------------------- |
| `RUNTIME_SETTINGS_FILE` | 運用設定JSONファイル（通常 `runtime_settings.json`） |
| `CHART_SOURCE`          | `coingecko` または `mt5`                             |
| `MT5_TIMEFRAME`         | MT5利用時の時間足（`M1`, `M5`, `H1` など）            |
| `MT5_BARS`              | MT5利用時の取得本数                                   |
| `SYMBOL_ROTATE_SEC`     | 銘柄切替間隔（秒）                                   |
| `VOICEVOX_SPEAKER`      | VOICEVOXの話者ID                                     |
| `YOUTUBE_STREAM_KEY`    | YouTubeのストリームキー ← **必ず設定**               |
| `CHART_REFRESH_SEC`     | チャート更新間隔（秒）                               |
| `NEWS_INTERVAL_SEC`     | ニュース読み上げ間隔（秒）                           |

`runtime_settings.json` 例:

```json
{
  "symbols": [
    {
      "coin_id": "ripple",
      "symbol": "XRP/JPY",
      "vs_currency": "jpy",
      "mt5_symbol": "XRPJPY"
    },
    {
      "coin_id": "bitcoin",
      "symbol": "BTC/JPY",
      "vs_currency": "jpy",
      "mt5_symbol": "BTCJPY"
    }
  ],
  "news_sources": [
    { "type": "rss", "url": "https://cointelegraph.com/rss/tag/xrp" },
    { "type": "scrape", "url": "https://www.coindesk.com/", "selectors": ["h2", "h3"] }
  ]
}
```

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
config.py            # アプリ設定読み込み
runtime_settings.json # 運用時に編集する設定（銘柄/ニュース）
main.py            # メインループ
data/
  price_fetcher.py # ソース別価格取得（coingecko/mt5）
  mt5_fetcher.py   # MetaTrader5価格取得
  news_fetcher.py  # RSSニュース取得
chart/
  chart_renderer.py # ローソク足 + MA + BB
overlay/
  frame_composer.py # テロップ合成（銘柄/価格/変動率/字幕）
audio/
  tts.py           # VOICEVOX TTS
  narrator.py      # ナレーション文生成
stream/
  ffmpeg_streamer.py # FFmpeg → YouTube RTMP
```

## 追加ドキュメント

- クライアント受領情報: [docs/CLIENT_HANDOVER_CHECKLIST.md](docs/CLIENT_HANDOVER_CHECKLIST.md)
- テスト手順: [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)
- 設置後運用マニュアル: [docs/OPERATIONS_MANUAL_JA.md](docs/OPERATIONS_MANUAL_JA.md)
- トラブルシューティング: [docs/TROUBLESHOOTING_JA.md](docs/TROUBLESHOOTING_JA.md)
- Windows VPS(MT5)手順: [docs/WINDOWS_VPS_SETUP_JA.md](docs/WINDOWS_VPS_SETUP_JA.md)
- 受け入れテスト報告書テンプレート: [docs/ACCEPTANCE_TEST_REPORT_TEMPLATE.md](docs/ACCEPTANCE_TEST_REPORT_TEMPLATE.md)
