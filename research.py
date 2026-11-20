import feedparser
import requests
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": "NUSKHALO-HealthAwarenessBot/1.0 (+https://github.com/sahebchatterjee650-sudo/NUSKHALO)"
}
TIMEOUT = 20


def collect_topics(config):
    topics = []
    feeds = config.get("feeds", [])

    if not feeds:
        print("RSS diagnostic: no feed URLs configured.")

    for feed_url in feeds:
        try:
            response = requests.get(
                feed_url,
                headers=HEADERS,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            parsed = feedparser.parse(response.content)

            entries = parsed.entries[:20]
            print(
                f"RSS diagnostic: {feed_url} | HTTP {response.status_code} "
                f"| entries={len(parsed.entries)} | bozo={bool(parsed.bozo)}"
            )

            if parsed.bozo:
                print(f"RSS parse warning for {feed_url}: {parsed.bozo_exception}")

            for entry in entries:
                title = (entry.get("title") or "").strip()
                summary = (entry.get("summary") or entry.get("description") or "").strip()
                link = (entry.get("link") or "").strip()

                if not title or not link:
                    continue

                topics.append({
                    "title": title,
                    "summary": summary[:1200],
                    "source_url": link,
                    "source_domain": urlparse(link).netloc,
                    "published": entry.get("published", entry.get("updated", "")),
                    "feed_url": feed_url,
                })

        except requests.RequestException as exc:
            print(f"RSS fetch error for {feed_url}: {exc}")
        except Exception as exc:
            print(f"RSS unexpected error for {feed_url}: {exc}")

    # Remove duplicate headlines while preserving feed order.
    unique = []
    seen = set()
    for topic in topics:
        key = topic["title"].casefold()
        if key not in seen:
            seen.add(key)
            unique.append(topic)

    print(f"RSS diagnostic: collected {len(unique)} unique candidate topics.")
    return unique
