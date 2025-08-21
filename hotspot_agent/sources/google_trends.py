from __future__ import annotations

import hashlib
from datetime import datetime
from typing import List, Optional

import feedparser
from dateutil import parser as date_parser

from hotspot_agent.models import Topic


def _make_id(source: str, title: str, url: str) -> str:
    hasher = hashlib.sha256()
    hasher.update(f"{source}|{title}|{url}".encode("utf-8"))
    return hasher.hexdigest()[:16]


def fetch_google_trends(locale: str = "zh-CN", geo: str = "CN", tz: str = "-480") -> List[Topic]:
    feed_url = (
        "https://trends.google.com/trends/trendingsearches/daily/rss"
        f"?hl={locale}&tz={tz}&geo={geo}"
    )
    parsed = feedparser.parse(feed_url)

    topics: List[Topic] = []
    for entry in parsed.entries:
        title = entry.get("title", "").strip()
        url: str = entry.get("link", "").strip()
        summary: Optional[str] = entry.get("summary")

        published: Optional[datetime] = None
        if "published" in entry:
            try:
                published = date_parser.parse(entry.published)
            except Exception:
                published = None

        topic = Topic(
            id=_make_id("google_trends", title, url or title),
            title=title,
            url=url or "",
            summary=summary,
            published=published,
            source="google_trends",
            tags=["trending", geo, locale],
        )
        topics.append(topic)

    return topics