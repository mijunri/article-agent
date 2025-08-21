from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Topic:
    id: str
    title: str
    url: str
    summary: Optional[str]
    published: Optional[datetime]
    source: str
    tags: List[str] = field(default_factory=list)


@dataclass
class ScoredTopic:
    topic: Topic
    score: float
    rationale: str
    features: Dict[str, float] = field(default_factory=dict)


@dataclass
class Article:
    id: str
    title: str
    content_markdown: str
    summary: str
    tags: List[str]
    topic_url: str
    source: str
    created_at: datetime