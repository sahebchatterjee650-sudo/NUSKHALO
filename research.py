import feedparser
from urllib.parse import urlparse

def collect_topics(config):
    topics = []
    for feed_url in config.get("feeds", []):
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries[:10]:
            title = (entry.get("title") or "").strip()
            summary = (entry.get("summary") or "").strip()
            link = entry.get("link", "")
            if not title or not link:
                continue
            # Only collect candidate topics; RSS headlines are not medical evidence.
            topics.append({
                "title": title,
                "summary": summary[:1200],
                "source_url": link,
                "source_domain": urlparse(link).netloc
            })
    return topics
