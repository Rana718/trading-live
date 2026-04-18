import feedparser
from config import NEWS_FEEDS

_seen: set[str] = set()


def fetch_latest_news(max_items: int = 10) -> list[str]:
    """Return list of unread news headlines from configured RSS feeds."""
    headlines = []
    for feed_url in NEWS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:max_items]:
            title = entry.get("title", "").strip()
            if title and title not in _seen:
                _seen.add(title)
                headlines.append(title)
    return headlines
