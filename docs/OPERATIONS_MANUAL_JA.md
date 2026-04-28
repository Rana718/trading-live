# 運用マニュアル（設置後に自分で変更する方向け）

このマニュアルは、専門的な操作を最小化して「銘柄・ニュース引用元・音声設定」を変更する手順です。

## 1. 変更対象ファイル

- `.env`: 配信キー、音声、切替間隔
- `runtime_settings.json`: 銘柄一覧、ニュース引用元

## 0. チャートソースを選ぶ

`.env` の `CHART_SOURCE` を設定:

- `coingecko`: API価格を利用
- `mt5`: MT5端末価格を利用（Windows想定）

## 2. 銘柄を変更する

`runtime_settings.json` の `symbols` を編集します。

例:

```json
{
  "symbols": [
    { "coin_id": "ripple", "symbol": "XRP/JPY", "vs_currency": "jpy" },
    { "coin_id": "bitcoin", "symbol": "BTC/JPY", "vs_currency": "jpy" },
    { "coin_id": "ethereum", "symbol": "ETH/JPY", "vs_currency": "jpy" }
  ],
  "news_feeds": [
    "https://cointelegraph.com/rss/tag/xrp",
    "https://decrypt.co/feed"
  ]
}
```

- `coin_id`: CoinGeckoのID
- `symbol`: 画面表示文字列
- `vs_currency`: 表示通貨（例: `jpy`, `usd`）
- `mt5_symbol`: MT5モード時に使うシンボル名（例: `XRPJPY`）

## 3. ニュース引用元を変更する

`runtime_settings.json` の `news_sources` を編集します。

例:

```json
"news_sources": [
  {"type": "rss", "url": "https://cointelegraph.com/rss/tag/xrp"},
  {"type": "scrape", "url": "https://www.coindesk.com/", "selectors": ["h2", "h3"]}
]
```

- `type=rss`: RSSから取得
- `type=scrape`: Webページから見出し抽出（CSSセレクタ指定）

## 4. 音声や切替間隔を変更する

`.env` を編集:

- `TTS_ENGINE`: `edge`
- `EDGE_TTS_VOICE`: 音声名（例: `ja-JP-NanamiNeural`）
- `EDGE_TTS_RATE`: 読み上げ速度
- `EDGE_TTS_VOLUME`: 音量

## 5. 反映方法

アプリを再起動します。

```bash
uv run python main.py
```

systemd運用時:

```bash
sudo systemctl restart trading-live
```

## 6. よくあるミス

- JSONのカンマ抜け
- `coin_id` のスペルミス
- RSS URLが無効
- `YOUTUBE_STREAM_KEY` 未設定

## 7. 動作確認

- 画面上部で銘柄名が一定間隔で切り替わる
- ニュース字幕が定期的に表示される
- 音声でチャート解説/ニュース読み上げが流れる
