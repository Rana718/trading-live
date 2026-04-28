# Windows VPS セットアップ（MT5モード）

この手順は、クライアント要件の「Windows VPS上で自動稼働」に合わせた運用手順です。

## 1. 前提

- Windows VPS（管理者権限）
- Python 3.11+
- FFmpeg（PATHに追加）
- VOICEVOX（ローカル起動）
- MetaTrader 5 端末（ログイン済み）

## 2. 依存インストール

```powershell
cd C:\path\to\trading_live
uv sync
uv pip install "MetaTrader5>=5.0.46"
```

## 3. `.env` 設定

```env
CHART_SOURCE=mt5
MT5_TIMEFRAME=M1
MT5_BARS=300
YOUTUBE_STREAM_KEY=xxxx
VOICEVOX_URL=http://127.0.0.1:50021
VOICEVOX_SPEAKER=1
RUNTIME_SETTINGS_FILE=runtime_settings.json
```

## 4. `runtime_settings.json` 設定

`symbols` ごとに `mt5_symbol` を設定します。

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
  "news_feeds": [
    "https://cointelegraph.com/rss/tag/xrp",
    "https://decrypt.co/feed"
  ]
}
```

## 5. 起動確認

```powershell
uv run python main.py
```

## 6. 自動起動（タスクスケジューラ）

1. タスクスケジューラを開く
2. 「タスクの作成」
3. トリガー: 「システム起動時」
4. 操作: `python` 実行、引数 `main.py`、開始フォルダをプロジェクトディレクトリに設定
5. 「最上位の特権で実行する」を有効化
6. 失敗時再起動を有効化

または同梱スクリプトで自動登録:

```powershell
cd C:\path\to\trading_live
powershell -ExecutionPolicy Bypass -File scripts\windows\install_startup_task.ps1 -ProjectDir "C:\path\to\trading_live"
```

起動スクリプト本体:

- `scripts/windows/start_trading_live.ps1`
- `scripts/windows/install_startup_task.ps1`

## 7. MT5運用注意

- MT5端末が起動してログイン済みであること
- `mt5_symbol` はブローカー表記に合わせること
- 銘柄が存在しない場合は価格取得に失敗するため、まずMT5で表示確認
