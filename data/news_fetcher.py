import feedparser
import requests
from bs4 import BeautifulSoup


def _fetch_rss(feed_url: str, max_items: int, seen: set[str]) -> list[str]:
    out: list[str] = []
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:max_items]:
        text = (entry.get("title", "") or "").strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _fetch_scrape(url: str, selectors: list[str], max_items: int, seen: set[str]) -> list[str]:
    out: list[str] = []
    resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    css_selectors = selectors or ["h1", "h2", "h3", "a[title]"]
    for selector in css_selectors:
        for node in soup.select(selector):
            text = node.get_text(" ", strip=True)
            if text and text not in seen:
                seen.add(text)
                out.append(text)
            if len(out) >= max_items:
                return out
    return out


def fetch_latest_news(news_sources: list[object], max_items: int = 10) -> list[str]:
    """Return latest headlines from configured RSS and/or scraped sources.

    Headlines are deduplicated only within a single fetch call so that
    subsequent polls can pick up the same stories again (RSS feeds update
    slowly and the caller already handles one-time narration via a queue).
    """
    seen: set[str] = set()
    headlines: list[str] = []
    for source in news_sources:
        try:
            if isinstance(source, str):
                headlines.extend(_fetch_rss(source, max_items, seen))
                continue

            if not isinstance(source, dict):
                continue

            source_type = str(source.get("type", "rss")).lower()
            url = str(source.get("url", "")).strip()
            if not url:
                continue

            if source_type == "scrape":
                selectors = source.get("selectors", [])
                selectors = selectors if isinstance(selectors, list) else []
                headlines.extend(_fetch_scrape(url, selectors, max_items, seen))
            else:
                headlines.extend(_fetch_rss(url, max_items, seen))
        except Exception:
            continue

        if len(headlines) >= max_items:
            return headlines[:max_items]
    return headlines
