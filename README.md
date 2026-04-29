# 24時間自動配信システム（暗号資産チャート + ニュース読み上げ）

このプロジェクトは、暗号資産のチャート表示・価格テロップ・ニュース読み上げを組み合わせて、YouTube Liveへ24時間自動配信するためのシステムです。

## 機能概要

- ローソク足チャート表示（移動平均線・ボリンジャーバンド付き）
- 複数銘柄の自動切り替え
- 価格・変動率・時刻の上部テロップ表示
- ナレーション字幕の下部テロップ表示
- ニュース見出しの自動取得（RSS / スクレイピング）
- Edge TTSによる音声読み上げ
- FFmpegでYouTube RTMPへ常時配信
- FFmpeg異常終了時の自動再起動

## 動作環境

- Python 3.11 以上
- `uv`
- FFmpeg
- インターネット接続

## セットアップ手順

### 1. 依存関係のインストール

```bash
uv sync
```

### 2. `.env` を設定

このリポジトリの `.env` を編集してください。

主な設定項目:

- `YOUTUBE_STREAM_KEY`: YouTube配信用ストリームキー（必須）
- `COIN_ID`: CoinGeckoの銘柄ID（例: `ripple`, `bitcoin`）
- `COIN_SYMBOL`: 画面表示・読み上げに使う銘柄名（例: `XRP/JPY`）
- `TTS_ENGINE`: 音声エンジン（通常 `edge`）
- `EDGE_TTS_VOICE`: 音声名
- `EDGE_TTS_RATE`: 読み上げ速度
- `EDGE_TTS_VOLUME`: 読み上げ音量
- `CHART_REFRESH_SEC`: チャート更新間隔（秒）
- `NEWS_INTERVAL_SEC`: ニュース読み上げ間隔（秒）

### 3. `runtime_settings.json` を設定

銘柄ローテーションとニュース取得元を編集します。

例:

```json
{
  "symbols": [
    {
      "coin_id": "ripple",
      "symbol": "XRP/JPY",
      "vs_currency": "jpy",
      "tradingview_symbol": "CRYPTOCAP:XRP"
    },
    {
      "coin_id": "bitcoin",
      "symbol": "BTC/JPY",
      "vs_currency": "jpy",
      "tradingview_symbol": "CRYPTOCAP:BTC"
    }
  ],
  "news_sources": [
    {
      "type": "rss",
      "url": "https://cointelegraph.com/rss/tag/xrp"
    },
    {
      "type": "rss",
      "url": "https://decrypt.co/feed"
    }
  ]
}
```

## 起動方法

```bash
uv run python main.py
```

Windowsの場合は、同梱の `run_stream.bat` でも起動できます。

## 自動起動（Linux / systemd）

`/etc/systemd/system/trading-live.service` を作成:

```ini
[Unit]
Description=Trading Live Stream
After=network.target

[Service]
WorkingDirectory=/path/to/trading_live
ExecStart=/path/to/trading_live/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

有効化:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now trading-live
```

## 運用ガイド

### 銘柄を変更する

1. `.env` の `COIN_ID` と `COIN_SYMBOL` を変更
2. 必要なら `runtime_settings.json` の `symbols` も編集
3. プロセス再起動

### ニュース取得元を変更する

`runtime_settings.json` の `news_sources` を編集します。

- RSS例: `{"type": "rss", "url": "https://example.com/feed"}`
- スクレイプ例: `{"type": "scrape", "url": "https://example.com", "selectors": ["h2", "h3"]}`

### 読み上げ頻度を変更する

- チャート更新: `.env` の `CHART_REFRESH_SEC`
- ニュース読み上げ: `.env` の `NEWS_INTERVAL_SEC`

## トラブルシューティング

### 1) 配信が開始されない

確認項目:

- `.env` の `YOUTUBE_STREAM_KEY` が正しいか
- FFmpegがインストール済みか
- サーバーの時刻が大きくずれていないか

確認コマンド:

```bash
ffmpeg -version
uv run python main.py
```

### 2) 映像は出るが音声が出ない

確認項目:

- `TTS_ENGINE=edge` になっているか
- サーバーが外部通信可能か（TTS生成時に必要）
- ログにTTSエラーが出ていないか

### 3) 画面がカクつく / バッファリングする

対処:

- `CHART_REFRESH_SEC` を大きくする（例: 60 → 90）
- 同時実行中の不要プロセスを停止する
- VPSのCPUプランを上げる

### 4) ニュースが更新されない

確認項目:

- `runtime_settings.json` のURLが有効か
- RSSの形式が正しいか
- スクレイプ先のHTML構造が変わっていないか

### 5) 銘柄価格が取得できない

確認項目:

- `COIN_ID` がCoinGeckoの正式IDか
- `vs_currency` が有効か（例: `jpy`, `usd`）
- APIの一時制限が発生していないか

## プロジェクト構成

```text
config.py               設定読み込み
main.py                 メイン処理（更新・配信ループ）
runtime_settings.json   銘柄/ニュース設定

audio/
  narrator.py           読み上げテキスト生成
  tts.py                音声生成

chart/
  chart_renderer.py     チャート描画

data/
  price_fetcher.py      価格取得（CoinGecko/Binance）
  news_fetcher.py       ニュース取得（RSS/スクレイプ）

overlay/
  frame_composer.py     テロップ合成

stream/
  ffmpeg_streamer.py    FFmpeg配信制御
```
