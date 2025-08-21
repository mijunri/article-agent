from __future__ import annotations

import os
from typing import Dict, List, Tuple

from rich.console import Console

from hotspot_agent.analysis import analyze_and_score
from hotspot_agent.distribute import save_article
from hotspot_agent.generator import generate_article
from hotspot_agent.models import Article, Topic
from hotspot_agent.sources.google_trends import fetch_google_trends
from hotspot_agent.sources.hn import fetch_hn_frontpage


console = Console()


def _dedupe_topics(topics: List[Topic]) -> List[Topic]:
    seen = set()
    unique = []
    for t in topics:
        key = (t.title or "", t.url or "", t.source)
        if key in seen:
            continue
        seen.add(key)
        unique.append(t)
    return unique


def run_pipeline(config: Dict) -> Tuple[List[Article], List[Tuple[str, str]]]:
    output_dir = config.get("output_dir", "outputs")
    top_n = int(config.get("top_n", 5))
    llm_enabled = bool(config.get("llm", {}).get("enabled", False))
    llm_model = str(config.get("llm", {}).get("model", "gpt-4o-mini"))

    locale = config.get("locale", "zh-CN")
    geo = config.get("geo", "CN")

    console.log("Fetching topics from sources…")
    topics: List[Topic] = []
    try:
        topics.extend(fetch_google_trends(locale=locale, geo=geo))
    except Exception as e:
        console.log(f"[yellow]Google Trends failed: {e}")
    try:
        topics.extend(fetch_hn_frontpage())
    except Exception as e:
        console.log(f"[yellow]HN failed: {e}")

    topics = _dedupe_topics(topics)
    console.log(f"Fetched {len(topics)} topics (after dedupe)")

    console.log("Scoring topics…")
    scored = analyze_and_score(topics)

    selected = scored[:top_n]
    console.log(f"Selected top {len(selected)} topics for article generation")

    articles: List[Article] = []
    outputs: List[Tuple[str, str]] = []

    for s in selected:
        article = generate_article(s, use_llm=llm_enabled, model=llm_model)
        articles.append(article)
        paths = save_article(article, output_dir=output_dir)
        outputs.append(paths)
        console.log(f"Saved article for '{article.title}' -> {paths[0]}")

    return articles, outputs