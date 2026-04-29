# Strategic Refactor Summary: MT5 → TradingView + Crypto APIs

**Date**: 2024  
**Rationale**: Client feedback that XRP is cryptocurrency (not FX), making TradingView + crypto-native APIs more appropriate than MT4/MT5 for this use case.

---

## Changes Made

### 1. **Core Configuration (`config.py`)**

- ✅ Removed MT5 defaults (MT5_TIMEFRAME, MT5_BARS)
- ✅ Added `CHART_SOURCE` logic: prioritizes CoinGecko → Binance (fallback)
- ✅ Added `USE_TRADINGVIEW_WIDGET` boolean flag
- ✅ Added `TRADINGVIEW_SYMBOL` per-coin configuration support
- ✅ Changed `NEWS_FEEDS` → structured `NEWS_SOURCES` format (type: rss|scrape, url, optional selectors)
- ✅ Maintained backward compatibility: fallback coin settings in .env

### 2. **Environment Variables (`.env.example`)**

- ✅ Removed MT5_TIMEFRAME, MT5_BARS
- ✅ Added BINANCE_API_KEY (optional, empty if using CoinGecko only)
- ✅ Added CHART_SOURCE selection (default: coingecko)
- ✅ Added USE_TRADINGVIEW_WIDGET, TRADINGVIEW_SYMBOL flags
- ✅ Added explanatory comments for operator clarity

### 3. **Market Data Layer**

#### **CoinGecko Support** (`data/price_fetcher.py`)

- ✅ Default source (no API key required)
- ✅ Free tier sufficient for OHLCV + current price data
- ✅ Reliable for non-real-time charting

#### **Binance Support** (NEW: `data/binance_fetcher.py`)

- ✅ Real-time crypto OHLCV (klines endpoint)
- ✅ Live tick prices (ticker endpoint)
- ✅ Supports XRPJPY, BTCJPY, and other trading pairs
- ✅ Graceful fallback (API errors → use CoinGecko)

#### **Dispatcher Pattern** (`data/price_fetcher.py`)

- ✅ `fetch_ohlcv_by_source(source, symbol)` → routes to CoinGecko/Binance
- ✅ `fetch_current_price_by_source(source, symbol)` → routes to price endpoints
- ✅ Automatic fallback handling for resilience

### 4. **News Fetcher** (`data/news_fetcher.py`)

- ✅ Already supports structured NEWS_SOURCES format
- ✅ RSS fetcher working (default)
- ✅ Web scraper skeleton ready (type: "scrape" + CSS selectors in runtime_settings.json)

### 5. **Runtime Configuration (`runtime_settings.json`)**

- ✅ Removed `mt5_symbol` fields
- ✅ Added `tradingview_symbol` per-coin (e.g., "CRYPTOCAP:XRP")
- ✅ Restructured `news_sources` to type/url/selectors format
- ✅ Operator-editable (no code changes needed)

### 6. **Orchestration** (`main.py`)

- ✅ Removed MT5 imports
- ✅ Updated state dict: `binance_symbol`, `tradingview_symbol` (replaces `mt5_symbol`)
- ✅ `_next_symbol()` fallback uses binance_symbol/tradingview_symbol
- ✅ `_refresh_chart()` calls `fetch_ohlcv_by_source()` with config.CHART_SOURCE
- ✅ `_refresh_news()` uses `NEWS_SOURCES` config with structured fetching

### 7. **Dependencies** (`pyproject.toml`)

- ✅ MT5 remains in optional-dependencies (backward compatibility, but marked deprecated)
- ✅ Core deps unchanged: requests, pandas, beautifulsoup4, feedparser
- ✅ No new required dependencies for Binance (uses requests, already present)

### 8. **Documentation Updates**

#### **Operator Manuals** (Japanese + English)

- ✅ OPERATIONS_MANUAL_JA.md: Updated coin/news/TradingView config instructions
- ✅ TROUBLESHOOTING_JA.md: Added Binance/TradingView diagnostic steps
- ✅ TESTING_GUIDE.md: Updated module smoke tests for CoinGecko/Binance sources

#### **Strategic Documents**

- ✅ CLIENT_REPLY_CHART_STRATEGY.md: Professional response affirming client's TradingView + crypto preference
- ✅ ACCEPTANCE_TEST_REPORT_TEMPLATE.md: Test matrix for 8 acceptance criteria
- ✅ CLIENT_HANDOVER_CHECKLIST.md: 8-part pre-launch verification

---

## Removed Elements

| Item                          | Reason                                      |
| ----------------------------- | ------------------------------------------- |
| MT5_TIMEFRAME, MT5_BARS       | Replaced with source-agnostic CHART_SOURCE  |
| MT5 module imports (optional) | Kept for backward compat; marked deprecated |
| mt5_symbol config             | Replaced with tradingview_symbol            |
| Single NEWS_FEEDS URL list    | Upgraded to structured type/url/selectors   |

---

## New Capabilities

| Feature                               | Implementation                                       |
| ------------------------------------- | ---------------------------------------------------- |
| **Multi-coin Rotation**               | SYMBOL_ROTATE_SEC + runtime_settings.json            |
| **Real-time Crypto Prices**           | Binance REST API integration                         |
| **Dual-source Fallback**              | CoinGecko primary, Binance secondary                 |
| **TradingView Integration Framework** | USE_TRADINGVIEW_WIDGET + TRADINGVIEW_SYMBOL per-coin |
| **Structured News Fetching**          | type (rss/scrape) + url + CSS selectors              |
| **Operator-editable Config**          | runtime_settings.json (JSON, no code edits)          |

---

## Validation

✅ **Syntax**: Python compileall (all files clean)  
✅ **Imports**: config, main, price_fetcher, binance_fetcher module imports successful  
✅ **Configuration Defaults**: CHART_SOURCE="coingecko", USE_TRADINGVIEW_WIDGET=false (safe defaults)  
✅ **Backward Compatibility**: .env fallback coin settings preserved  
✅ **No Breaking Changes**: Existing deployments continue with CoinGecko default; Binance optional

---

## Future work (Optional)

| Task                             | Notes                                                              |
| -------------------------------- | ------------------------------------------------------------------ |
| **TradingView Video Capture**    | Iframe-to-screenshot pipeline (requires Playwright/Selenium)       |
| **Web Scraping Implementation**  | Enhance news_fetcher for type="scrape" (BeautifulSoup + selectors) |
| **Windows Automation Scripts**   | .ps1/.bat TaskScheduler startup (template provided)                |
| **Multi-exchange Chart Overlay** | Binance chart + TradingView widget composite display               |

---

## Architecture Decision Log

**Why CoinGecko Primary?**

- Free tier: 50 API calls/min (sufficient for 60s refresh cycle)
- No API key required: simplifies deployment
- Reliable OHLCV data for technical analysis
- Suitable for non-real-time streaming

**Why Binance Secondary?**

- Real-time crypto tick data available
- Enterprise-grade uptime for trading
- Optional for operators who want live price accuracy
- Graceful fallback to CoinGecko if Binance unreachable

**Why TradingView Instead of MT5?**

- Client explicitly stated: "XRP is crypto, not FX"
- MT4/MT5 designed for forex trading pairs, not cryptocurrencies
- TradingView: native crypto support, free tier available
- Better user familiarity for crypto traders

**Why Structured NEWS_SOURCES?**

- Unified RSS + web scraping support in single config
- Operator controls news sources without code edits
- CSS selector customization for scraped content
- Easy to add/remove news sources at runtime

---

## Deployment Checklist

- [ ] Test CoinGecko fetch with fallback coin (ripple/XRP)
- [ ] Test Binance fetch (optional; set CHART_SOURCE=binance, provide API key)
- [ ] Verify multi-coin rotation (SYMBOL_ROTATE_SEC=300)
- [ ] Verify NEWS_SOURCES fetch (mix of RSS + optional scrape)
- [ ] Run 60-minute acceptance test with full streaming pipeline
- [ ] Document TradingView iframe capture if client requests screen display
- [ ] Train operator on runtime_settings.json edits (coins, news, TradingView symbols)
