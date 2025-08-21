from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import List, Optional

import feedparser
from dateutil import parser as date_parser

from hotspot_agent.models import Topic


def _make_id(source: str, title: str, url: str) -> str:
    hasher = hashlib.sha256()
    hasher.update(f"{source}|{title}|{url}".encode("utf-8"))
    return hasher.hexdigest()[:16]


_POINTS_RE = re.compile(r"(\d+)\s+points")


def _extract_points(entry) -> Optional[int]:
    # Try known extensions
    for key in ("hn_points", "points"):
        if key in entry:
            try:
                return int(entry.get(key))
            except Exception:
                pass
    # Try summary/title fallback
    for field in ("summary", "title"):
        text = entry.get(field)
        if not text:
            continue
        m = _POINTS_RE.search(str(text))
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None
    return None


def fetch_hn_frontpage() -> List[Topic]:
    feed_url = "https://hnrss.org/frontpage"
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

        points = _extract_points(entry)
        tags = ["hn", "frontpage"]
        if points is not None:
            tags.append(f"points:{points}")

        topic = Topic(
            id=_make_id("hn_frontpage", title, url or title),
            title=title,
            url=url or "",
            summary=summary,
            published=published,
            source="hn_frontpage",
            tags=tags,
        )
        topics.append(topic)

    return topics