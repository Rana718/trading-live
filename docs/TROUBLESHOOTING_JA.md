# トラブルシューティングガイド

## 1. 配信が始まらない

症状:

- YouTubeに映像が来ない

確認:

- `.env` の `YOUTUBE_STREAM_KEY` が正しいか
- `ffmpeg` がインストールされているか (`which ffmpeg`)
- `uv run python main.py` のログで FFmpeg エラーがないか

対応:

- ストリームキーを再発行して再設定
- ffmpegを再インストール

## 2. 音声が出ない

確認:

- VOICEVOXが起動しているか
- `.env` の `VOICEVOX_URL` と `VOICEVOX_SPEAKER` が正しいか

対応:

- VOICEVOXを再起動
- 話者IDを変更して再試行

## 3. ニュースが出ない

確認:

- `runtime_settings.json` の `news_sources` が有効か（RSS URLまたはスクレイプ設定）

対応:

- ブラウザでRSS URLを開けるか確認
- `type=scrape` の場合、`selectors` を `h2` / `h3` などで再確認

## 4. 銘柄が切り替わらない

確認:

- `.env` の `SYMBOL_ROTATE_SEC`
- `runtime_settings.json` の `symbols` が2件以上あるか

対応:

- `symbols` を追加
- 間隔を短くして動作確認

## 5. アプリが停止した

確認:

- ログに例外がないか
- ネットワーク断がなかったか

対応:

- 手動再起動: `uv run python main.py`
- systemd運用: `sudo systemctl restart trading-live`

## 6. JSON編集で起動しない

確認:

- `runtime_settings.json` のカンマ/括弧が正しいか

対応:

- 最後の行の余分なカンマを削除
- 必須キー `symbols` / `news_feeds` があるか確認

## 7. MT5モードで価格取得できない

確認:

- `.env` の `CHART_SOURCE=mt5` になっているか
- MT5端末が起動・ログイン済みか
- `runtime_settings.json` の `mt5_symbol` が正しいか
- `MetaTrader5` パッケージがインストールされているか

対応:

- MT5端末を再起動して再ログイン
- ブローカー仕様に合わせて `mt5_symbol` を修正
- `uv pip install MetaTrader5` を実行
