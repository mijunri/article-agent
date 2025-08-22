#!/usr/bin/env python3
"""
Fetch Baidu realtime hot list and write results to JSON and CSV under a data directory.

Usage:
  python baidu_hot.py --outdir /workspace/data --limit 50
"""

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

import requests

API_URL = "https://top.baidu.com/api/board"
PAGE_URL = "https://top.baidu.com/board?tab=realtime"


def fetch_hotlist_via_api(session: requests.Session) -> Optional[Dict[str, Any]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
    }
    params = {"platform": "wise", "tab": "realtime"}
    try:
        resp = session.get(API_URL, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get("errno", 0) == 0 and data.get("data"):
            return data["data"]
    except Exception:
        return None
    return None


def _safe_get(item: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    for key in keys:
        if key in item and item[key] not in (None, ""):
            return item[key]
    return default


def extract_rows_from_api_data(api_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    cards = api_data.get("cards") or []
    rank = 1
    for card in cards:
        contents = card.get("content") or []
        for entry in contents:
            title = _safe_get(entry, ["word", "query", "title", "name"], "")
            desc = _safe_get(entry, ["desc", "abstract", "summary", "note"], "")
            url = _safe_get(entry, ["url", "jumpUrl", "appUrl"], "")
            hot_score = _safe_get(entry, ["hotScore", "hot score", "heat", "hot"], "")
            tag = ""
            hot_tags = entry.get("hotTags") or entry.get("hotLabel") or []
            if isinstance(hot_tags, list) and hot_tags:
                tag = _safe_get(hot_tags[0], ["text", "name", "label"], "")

            rows.append({
                "rank": rank,
                "title": title,
                "desc": desc,
                "url": url,
                "hot_score": hot_score,
                "tag": tag,
            })
            rank += 1
    return rows


def fetch_hotlist_via_page(session: requests.Session) -> Optional[List[Dict[str, Any]]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = session.get(PAGE_URL, headers=headers, timeout=10)
        resp.raise_for_status()
        html = resp.text
        # Attempt to extract embedded JSON from window.__INITIAL_STATE__
        m = re.search(r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\});", html, re.S)
        if not m:
            return None
        initial = m.group(1)
        data = json.loads(initial)
        # Heuristic traversal for hot list content
        # Try a few known paths
        content_lists = []
        # Path 1: data["data"]["cards"][0]["content"]
        try:
            cards = data.get("data", {}).get("cards", [])
            if cards and isinstance(cards, list):
                for card in cards:
                    if isinstance(card, dict) and "content" in card:
                        content_lists.append(card["content"]) 
        except Exception:
            pass

        items: List[Dict[str, Any]] = []
        for content in content_lists:
            if isinstance(content, list):
                for entry in content:
                    if not isinstance(entry, dict):
                        continue
                    title = _safe_get(entry, ["word", "query", "title", "name"], "")
                    desc = _safe_get(entry, ["desc", "abstract", "summary", "note"], "")
                    url = _safe_get(entry, ["url", "jumpUrl", "appUrl"], "")
                    hot_score = _safe_get(entry, ["hotScore", "hot score", "heat", "hot"], "")
                    items.append({
                        "title": title,
                        "desc": desc,
                        "url": url,
                        "hot_score": hot_score,
                    })
        # add ranks
        rows = []
        for idx, it in enumerate(items, start=1):
            it_row = {
                "rank": idx,
                "title": it.get("title", ""),
                "desc": it.get("desc", ""),
                "url": it.get("url", ""),
                "hot_score": it.get("hot_score", ""),
                "tag": "",
            }
            rows.append(it_row)
        return rows if rows else None
    except Exception:
        return None


def write_outputs(outdir: str, rows: List[Dict[str, Any]]) -> Dict[str, str]:
    os.makedirs(outdir, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(outdir, f"baidu_hot_{timestamp}.json")
    csv_path = os.path.join(outdir, f"baidu_hot_{timestamp}.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    fieldnames = ["rank", "title", "desc", "url", "hot_score", "tag"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    return {"json": json_path, "csv": csv_path}


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Baidu realtime hot list")
    parser.add_argument("--outdir", default=os.path.join(os.getcwd(), "data"), help="Output directory for data files")
    parser.add_argument("--limit", type=int, default=50, help="Maximum number of items to keep")
    args = parser.parse_args()

    session = requests.Session()

    api_data = fetch_hotlist_via_api(session)
    rows: Optional[List[Dict[str, Any]]] = None
    if api_data is not None:
        rows = extract_rows_from_api_data(api_data)

    if not rows:
        rows = fetch_hotlist_via_page(session)

    if not rows:
        print("Failed to fetch Baidu hot list.", file=sys.stderr)
        return 2

    if args.limit > 0:
        rows = rows[: args.limit]

    outputs = write_outputs(args.outdir, rows)

    print(f"Fetched {len(rows)} items.")
    print(f"JSON: {outputs['json']}")
    print(f"CSV:  {outputs['csv']}")

    # Print a compact preview to stdout
    for r in rows[:10]:
        title = r.get("title", "")
        score = r.get("hot_score", "")
        rank = r.get("rank", "")
        print(f"{rank:>2}. {title}  ({score})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())