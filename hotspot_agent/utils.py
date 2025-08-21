from __future__ import annotations

import os
import re


def slugify(text: str) -> str:
    text = text.strip().lower()
    # Replace non-word with hyphen
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def ensure_dir(path: str) -> None:
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)