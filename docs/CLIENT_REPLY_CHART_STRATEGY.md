# クライアント返信案：チャート戦略について

ご指摘ありがとうございます。完全におっしゃる通りです。

## 我々の対応方針

### 採用：TradingView Widget + 暗号資産API

1. **TradingView Widget の統合**
   - XRP など対応銘柄をウィジェット埋め込みで配信
   - リアルタイム性と信頼性が確保される
   - TradingViewの多様なテクニカル指標がそのまま使える

2. **価格データソース優先度**
   - 1st: CoinGecko API（現在実装）
   - 2nd: Binance REST API（追加予定）
   - 3rd: CoinMarketCap API（オプション）
   - MT4/MT5：不要（削除またはオプション化）

### 理由

- XRP などの暗号資産は、専用ブロックチェーンデータ API の方が確実
- FX用MT4/MT5 は暗号資産向けではない
- TradingView は暗号資産ネイティブで、スプレッド/テクニカル指標が優秀
- お客様が見慣れた UI で、説得力が高い

## 実装予定

1. TradingView widget iframe を overlay に統合
2. CoinGecko + Binance デュアルソース対応
3. `.env` で優先順位を切替可能に
4. 設定で銘柄・テクニカル指標をカスタマイズ可能に

ご確認よろしくお願いいたします。
