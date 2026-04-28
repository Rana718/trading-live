# Client Handover Checklist

Use this checklist before deployment so nothing blocks go-live.

## 1) Access And Credentials

- YouTube channel owner access (Editor or Owner)
- YouTube Live stream key
- VPS provider login (or ask client to create server and share access)
- OS-level admin user on VPS
- SSH key or RDP credentials (depending on Linux/Windows setup)

## 2) Content Configuration

- Target coin list (example: XRP, BTC, ETH)
- Display symbols (example: XRP/JPY, BTC/USDT)
- Base currency (JPY, USD, USDT)
- Chart timeframe preference (1m, 5m, 15m, 1h)
- Chart rotation interval (seconds)
- News source list (RSS URLs or websites)
- For website scraping, preferred page URLs and headline selectors (if known)
- News read interval (seconds)
- Language and voice style for narration
- Voice speed/tone preference

## 3) Branding Assets

- Channel title style and subtitle text
- Logo (PNG with transparent background preferred)
- Brand colors (hex values)
- Font preference (if any)
- Overlay style preference (minimal, trading desk, TV style)

## 4) Legal And Policy

- Confirmation that selected news sources are allowed for reuse/quotation
- Disclaimer text to show on stream (not financial advice)
- Jurisdiction-specific compliance text (if required)
- Copyright-safe assets confirmation (music/images/fonts)

## 5) Runtime And Operations

- Required uptime target (example: 24/7)
- Allowed maintenance window (if any)
- Restart policy on failures
- Alert destination for incidents (email/Telegram/Slack)
- Log retention period

## 6) Acceptance Criteria (Sign-Off)

- Stream starts automatically after reboot
- Stream recovers automatically after process crash
- Chart updates at agreed interval
- News appears at agreed interval
- Audio narration is clear and synchronized
- Overlay text shows correct symbol and price

## 7) Secrets To Provide For .env

- YOUTUBE_STREAM_KEY
- VOICEVOX_URL (if remote; if local default is fine)
- VOICEVOX_SPEAKER
- COIN_ID
- COIN_SYMBOL

## 8) Nice-To-Have Inputs (Optional)

- Backup RTMP endpoint
- Secondary news feed list
- Holiday/special schedule rules
- Priority list for coin rotation

---

## Ready-To-Send Message To Client

Please share the following so I can finalize and run your 24/7 stream:

1. YouTube Live stream key and channel access.
2. VPS access (admin user + login method).
3. Coins and symbol format you want on screen.
4. News source URLs you want to use.
5. Voice preference (speaker, speed, language tone).
6. Branding assets (logo, colors, title style).
7. Compliance/disclaimer text you want displayed.

After receiving these, I will complete setup, run end-to-end tests, and send you a simple operation manual.
