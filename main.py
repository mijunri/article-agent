import argparse
import os
import sys
from typing import Any, Dict

import yaml
from rich.console import Console

from hotspot_agent.pipeline import run_pipeline


console = Console()


def load_config(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        console.print(f"[red]Config file not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main():
    print("Hello from article-agent!")


if __name__ == "__main__":
    main()
