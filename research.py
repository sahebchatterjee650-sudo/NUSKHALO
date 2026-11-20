import feedparser
import requests
from datetime import datetime, timedelta, timezone
from time import mktime
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": "NUSKHALO-HealthAwarenessBot/1.0 (+https://github.com/sahebchatterjee650-sudo/NUSKHALO)"
}
TIMEOUT = 20


def _published_datetime(entry):
    """Return a timezone-aware publication datetime, or None if unavailable."""
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        return datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)

    raw = entry.get("published") or entry.get("updated") or ""
    if raw:
        try:
            from email.utils import parsedate_to_datetime
            value = parsedate_to_datetime(raw)
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            return None
    return None


def _trusted_source(link, allowed_domains):
    host = (urlparse(link).hostname or "").lower()
    return any(host == domain or host.endswith("." + domain) for domain in allowed_domains)


def collect_topics(config):
    topics = []
    feeds = config.get("feeds", [])
    max_age_days = int(config.get("max_age_days", 30))
    allowed_domains = [d.lower().strip() for d in config.get(
        "trusted_source_domains", ["who.int", "cdc.gov", "mohfw.gov.in"]
    )]
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max_age_days)

    if not feeds:
        print("RSS diagnostic: no feed URLs configured.")

    for feed_url in feeds:
        try:
            response = requests.get(feed_url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
            print(
                f"RSS diagnostic: {feed_url} | HTTP {response.status_code} "
                f"| entries={len(parsed.entries)} | bozo={bool(parsed.bozo)}"
            )
            if parsed.bozo:
                print(f"RSS parse warning for {feed_url}: {parsed.bozo_exception}")

            for entry in parsed.entries[:30]:
                title = (entry.get("title") or "").strip()
                summary = (entry.get("summary") or entry.get("description") or "").strip()
                link = (entry.get("link") or "").strip()
                published_dt = _published_datetime(entry)

                if not title or not link or urlparse(link).scheme != "https":
                    continue
                if not _trusted_source(link, allowed_domains):
                    print(f"Skipping non-allowlisted source: {link}")
                    continue
                if published_dt is None:
                    print(f"Skipping item with no parseable publication date: {title}")
                    continue
                if published_dt < cutoff or published_dt > now + timedelta(days=1):
                    print(f"Skipping stale/future item ({published_dt.isoformat()}): {title}")
                    continue
                if len(summary) < int(config.get("minimum_summary_chars", 60)):
                    print(f"Skipping item with insufficient source summary: {title}")
                    continue

                topics.append({
                    "title": title,
                    "summary": summary[:3000],
                    "source_url": link,
                    "source_domain": urlparse(link).hostname or "",
                    "published": published_dt.isoformat(),
                    "feed_url": feed_url,
                    "age_days": max(0, (now - published_dt).days),
                })

        except requests.RequestException as exc:
            print(f"RSS fetch error for {feed_url}: {exc}")
        except Exception as exc:
            print(f"RSS unexpected error for {feed_url}: {exc}")

    unique = []
    seen = set()
    for topic in topics:
        key = " ".join(topic["title"].casefold().split())
        if key not in seen:
            seen.add(key)
            unique.append(topic)

    unique.sort(key=lambda item: item["published"], reverse=True)
    print(
        f"RSS diagnostic: {len(unique)} fresh, trusted, unique topics "
        f"within the last {max_age_days} days."
    )
    return unique
