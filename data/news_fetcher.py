import feedparser
import requests
from bs4 import BeautifulSoup

_seen: set[str] = set()


def _unique_add(headlines: list[str], title: str):
    text = (title or "").strip()
    if text and text not in _seen:
        _seen.add(text)
        headlines.append(text)


def _fetch_rss(feed_url: str, max_items: int) -> list[str]:
    out: list[str] = []
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:max_items]:
        _unique_add(out, entry.get("title", ""))
    return out


def _fetch_scrape(url: str, selectors: list[str], max_items: int) -> list[str]:
    out: list[str] = []
    resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    css_selectors = selectors or ["h1", "h2", "h3", "a[title]"]
    for selector in css_selectors:
        for node in soup.select(selector):
            title = node.get_text(" ", strip=True)
            _unique_add(out, title)
            if len(out) >= max_items:
                return out
    return out


def fetch_latest_news(news_sources: list[object], max_items: int = 10) -> list[str]:
    """Return unread headlines from configured RSS and/or scraped sources."""
    headlines = []
    for source in news_sources:
        try:
            if isinstance(source, str):
                headlines.extend(_fetch_rss(source, max_items))
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
                headlines.extend(_fetch_scrape(url, selectors, max_items))
            else:
                headlines.extend(_fetch_rss(url, max_items))
        except Exception:
            continue

        if len(headlines) >= max_items:
            return headlines[:max_items]
    return headlines
