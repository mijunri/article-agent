from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime
from typing import Tuple

from hotspot_agent.models import Article
from hotspot_agent.utils import ensure_dir, slugify


def save_article(article: Article, output_dir: str) -> Tuple[str, str]:
    date_dir = datetime.utcnow().strftime("%Y%m%d")
    base_dir = os.path.join(output_dir, date_dir)
    ensure_dir(base_dir)

    slug = slugify(article.title) or article.id[:8]
    filename_base = f"{slug}-{article.id[:8]}"

    md_path = os.path.join(base_dir, f"{filename_base}.md")
    json_path = os.path.join(base_dir, f"{filename_base}.json")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(article.content_markdown)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(asdict(article), f, ensure_ascii=False, indent=2, default=str)

    return md_path, json_path