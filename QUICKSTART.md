# Quick Start: Trading Live System (TradingView + Crypto APIs)

## What Changed?

The system has been refactored to use **TradingView + crypto-native APIs** (CoinGecko + Binance) instead of MT4/MT5, as recommended by the client. This is more appropriate for XRP and other cryptocurrencies.

---

## Setup (First Time)

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# OR with pip
pip install -r requirements.txt  # Generate from pyproject.toml
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

**Critical fields:**

- `YOUTUBE_STREAM_KEY`: Your YouTube Live streaming key
- `VOICEVOX_URL`: Usually `http://127.0.0.1:50021` (VOICEVOX service)
- `RUNTIME_SETTINGS_FILE`: Leave as `runtime_settings.json`
- `CHART_SOURCE`: Use `coingecko` (default, free) or `binance` (real-time, requires API key)

### 3. Configure Coins & News

Open `runtime_settings.json` and edit:

```json
{
  "symbols": [
    {
      "coin_id": "ripple",
      "symbol": "XRP/JPY",
      "vs_currency": "jpy",
      "tradingview_symbol": "CRYPTOCAP:XRP"
    }
  ],
  "news_sources": [
    {
      "type": "rss",
      "url": "https://cointelegraph.com/rss/tag/xrp"
    }
  ]
}
```

- `coin_id`: From CoinGecko (e.g., "ripple", "bitcoin")
- `symbol`: Display name (e.g., "XRP/JPY")
- `vs_currency`: Target currency (jpy, usd, etc.)
- `tradingview_symbol`: TradingView ticker (e.g., "CRYPTOCAP:XRP")
- `news_sources`: RSS feeds or web scrapes for that coin

### 4. Start the System

```bash
python main.py
```

Your stream will start within 60 seconds. Open your YouTube channel to see the live feed.

---

## Configuration Reference

### .env Variables

| Variable                 | Required?               | Default                  | Example                              |
| ------------------------ | ----------------------- | ------------------------ | ------------------------------------ |
| `YOUTUBE_STREAM_KEY`     | Yes                     | —                        | `abcd-1234-efgh-5678`                |
| `VOICEVOX_URL`           | No                      | `http://127.0.0.1:50021` | `http://voicevox:50021`              |
| `VOICEVOX_SPEAKER`       | No                      | `1`                      | `1` (female), `3` (male)             |
| `RUNTIME_SETTINGS_FILE`  | No                      | `runtime_settings.json`  | `/path/to/settings.json`             |
| `CHART_SOURCE`           | No                      | `coingecko`              | `coingecko` or `binance`             |
| `BINANCE_API_KEY`        | If chart_source=binance | —                        | Leave empty if using CoinGecko       |
| `USE_TRADINGVIEW_WIDGET` | No                      | `false`                  | `true` to display TradingView iframe |
| `SYMBOL_ROTATE_SEC`      | No                      | `300`                    | Seconds between coin rotations       |
| `CHART_REFRESH_SEC`      | No                      | `60`                     | Seconds between chart updates        |
| `NEWS_INTERVAL_SEC`      | No                      | `300`                    | Seconds between news refreshes       |

### runtime_settings.json Fields

| Field                          | Purpose                         | Format                           |
| ------------------------------ | ------------------------------- | -------------------------------- |
| `symbols[].coin_id`            | CoinGecko coin identifier       | String (e.g., "ripple")          |
| `symbols[].symbol`             | Display name on chart telop     | String (e.g., "XRP/JPY")         |
| `symbols[].vs_currency`        | Target currency                 | String (jpy, usd, gbp, etc.)     |
| `symbols[].tradingview_symbol` | TradingView ticker (future use) | String (e.g., "CRYPTOCAP:XRP")   |
| `news_sources[].type`          | News source type                | "rss" or "scrape"                |
| `news_sources[].url`           | Feed or page URL                | String (valid URL)               |
| `news_sources[].selectors`     | CSS selectors (scrape only)     | Array (e.g., ["h1", "a[title]"]) |

---

## Daily Operations

### Add a New Coin

1. Open `runtime_settings.json`
2. Add a new entry to `symbols` array:
   ```json
   {
     "coin_id": "ethereum",
     "symbol": "ETH/JPY",
     "vs_currency": "jpy",
     "tradingview_symbol": "CRYPTOCAP:ETH"
   }
   ```
3. (Optional) Add news sources for this coin to `news_sources` array
4. Restart the system (Ctrl+C, then `python main.py`)

### Change Market Data Source

To use Binance (real-time prices) instead of CoinGecko:

1. Open `.env`
2. Set `CHART_SOURCE=binance`
3. Provide `BINANCE_API_KEY` (get from binance.com API Management)
4. Restart the system

### Change News Sources

Edit `runtime_settings.json` and modify the `news_sources` array:

- **RSS feeds**: Set `type: "rss"`, `url: "https://..."` (no selectors needed)
- **Web scraping**: Set `type: "scrape"`, `url: "https://..."`, `selectors: ["h1", "h2"]` (CSS selectors to extract headlines)

### Stop/Restart

```bash
# Stop current stream
Ctrl+C

# Restart
python main.py
```

The system automatically reconnects to YouTube if the stream drops.

---

## Chart and Display

### What You'll See

- **Chart**: 4-hour candlestick with 7/25-period moving averages + 20-period Bollinger Bands
- **Telop** (top overlay): Current price, percentage change (+/-)
- **Symbol**: Coin name and currency pair (e.g., "XRP/JPY")
- **Subtitle**: Latest news headline (rotates every 5 minutes)

### Customization

**Coming Soon** (if client requests):

- TradingView widget display (requires iframe screenshot)
- Multi-coin overlay charts
- Custom Bollinger Band periods

---

## Troubleshooting

### Stream Not Appearing on YouTube

1. Check `YOUTUBE_STREAM_KEY` in `.env`
2. Check that VOICEVOX is running: `curl http://127.0.0.1:50021`
3. Check logs for errors (should print to terminal)

### "No data available" for Coin

1. Check `coin_id` from CoinGecko: https://api.coingecko.com/api/v3/simple/price?ids=ripple&vs_currencies=jpy
2. Verify `vs_currency` is supported by CoinGecko
3. Try restarting the system

### "Binance API error"

1. Check `BINANCE_API_KEY` in `.env`
2. Verify Binance API key is valid
3. Check internet connectivity
4. System will fall back to CoinGecko if Binance fails

### News Not Updating

1. Check internet connectivity
2. Verify RSS feed URLs are still accessible (curl the URL):
   ```bash
   curl https://cointelegraph.com/rss/tag/xrp
   ```
3. Try removing/re-adding the news source in `runtime_settings.json`

---

## Need Help?

See the detailed documentation:

- **Operations**: [OPERATIONS_MANUAL_JA.md](OPERATIONS_MANUAL_JA.md) (Japanese)
- **Testing**: [TESTING_GUIDE.md](TESTING_GUIDE.md)
- **Troubleshooting**: [TROUBLESHOOTING_JA.md](TROUBLESHOOTING_JA.md) (Japanese)
- **Architecture**: [REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md)
