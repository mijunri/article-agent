from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from hotspot_agent.models import ScoredTopic, Topic


def _extract_points_from_tags(tags: List[str]) -> Optional[int]:
    for tag in tags:
        if tag.startswith("points:"):
            try:
                return int(tag.split(":", 1)[1])
            except Exception:
                return None
    return None


def _compute_features(topic: Topic, now_utc: datetime) -> Dict[str, float]:
    # Recency: exponential decay over 48h
    if topic.published is not None:
        delta = now_utc - topic.published.replace(tzinfo=topic.published.tzinfo or timezone.utc)
        hours = max(delta.total_seconds() / 3600.0, 0.0)
    else:
        hours = 72.0
    recency_score = pow(0.5, hours / 24.0)  # half-life 24h

    title_length = len(topic.title or "")
    moderate_title_len = 1.0 - abs(title_length - 60) / 60.0
    moderate_title_len = max(0.0, min(1.0, moderate_title_len))

    has_summary = 1.0 if (topic.summary and len(topic.summary) > 20) else 0.2

    points = _extract_points_from_tags(topic.tags)
    # Assume 100 points ~ 1.0, cap at 300
    points_score = min((points or 0) / 100.0, 3.0) / 3.0

    source_weight = 0.7 if topic.source.startswith("hn") else 0.5
    if topic.source.startswith("google_trends"):
        source_weight = 0.6

    return {
        "recency": recency_score,
        "title_moderation": moderate_title_len,
        "has_summary": has_summary,
        "hn_points": points_score,
        "source_weight": source_weight,
    }


def analyze_and_score(topics: Iterable[Topic], now: Optional[datetime] = None) -> List[ScoredTopic]:
    now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

    scored: List[ScoredTopic] = []
    for topic in topics:
        features = _compute_features(topic, now_utc)
        # Weighted sum
        score = (
            0.40 * features["recency"]
            + 0.30 * features["hn_points"]
            + 0.10 * features["title_moderation"]
            + 0.10 * features["has_summary"]
            + 0.10 * features["source_weight"]
        )
        rationale = (
            f"recency={features['recency']:.2f}, hn={features['hn_points']:.2f}, "
            f"title={features['title_moderation']:.2f}, summary={features['has_summary']:.2f}, "
            f"src={features['source_weight']:.2f}"
        )
        scored.append(ScoredTopic(topic=topic, score=score, rationale=rationale, features=features))

    scored.sort(key=lambda s: s.score, reverse=True)
    return scored