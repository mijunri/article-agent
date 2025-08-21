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
    parser = argparse.ArgumentParser(description="热点文章生成与分发")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--output", default=None, help="输出目录，覆盖配置项 output_dir")
    parser.add_argument("--top", type=int, default=None, help="生成文章数量，覆盖配置项 top_n")
    parser.add_argument("--llm", action="store_true", help="启用 LLM 生成")
    parser.add_argument("--model", default=None, help="LLM 模型名")

    args = parser.parse_args()

    config = load_config(args.config)

    if args.output:
        config["output_dir"] = args.output
    if args.top is not None:
        config["top_n"] = args.top
    if args.llm:
        config.setdefault("llm", {})["enabled"] = True
    if args.model is not None:
        config.setdefault("llm", {})["model"] = args.model

    articles, files = run_pipeline(config)
    console.print(f"生成完成：{len(articles)} 篇文章。输出目录：{config.get('output_dir')}")


if __name__ == "__main__":
    main()
