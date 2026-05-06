
## Start the server
- Double-click `run_stream.bat` in the project folder.
- Or open PowerShell and run:

```powershell
cd C:\path\to\trading-live
.\run_stream.bat
```
Leave the console window open to view logs. Look for `[INFO] Stream started.` and `[FFmpeg]` messages.
## Stop the server
- Focus the console window and press `Ctrl+C`.
- Or close the console window.
- If the process does not stop, run in PowerShell:

```powershell
Get-Process -Name python | Stop-Process
```

## Edit basic settings (safe, client-facing)
Edit the `.env` file with Notepad and change only these lines:

```
YOUTUBE_STREAM_KEY=your_stream_key_here
COIN_ID=ripple
COIN_SYMBOL=XRP/JPY
CHART_REFRESH_SEC=60
NEWS_INTERVAL_SEC=300
EDGE_TTS_VOICE=ja-JP-NanamiNeural
```

Save the file.

## Change coins and news feeds
Edit `runtime_settings.json` in Notepad.
- To add/change a coin, update the `symbols` array. Example:

```json
{
  "coin_id": "bitcoin",
  "symbol": "BTC/JPY",
  "vs_currency": "jpy",
  "tradingview_symbol": "CRYPTOCAP:BTC"
}
```
- To change news sources, edit `news_sources` with entries like:

```json
{ "type": "rss", "url": "https://cointelegraph.com/rss/tag/xrp" }
```
Save the file.

## Apply configuration changes
After saving `.env` or `runtime_settings.json`, restart the server:
- Stop the running `run_stream.bat` console (Ctrl+C) and then double-click `run_stream.bat` again.
