from __future__ import annotations

import argparse
import logging

from .pipeline import crawl
from .validator import validate


def main() -> None:
    parser = argparse.ArgumentParser(description="PolicyPulse crawler CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    crawl_parser = subparsers.add_parser("crawl", help="Fetch and update news data")
    crawl_parser.add_argument("--data", default="data/news.jsonl", help="Path to news.jsonl")
    crawl_parser.add_argument("--index", default="data/index.json", help="Path to index.json")

    validate_parser = subparsers.add_parser("validate", help="Validate data schema")
    validate_parser.add_argument("--data", default="data/news.jsonl", help="Path to news.jsonl")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.command == "crawl":
        crawl(data_path=args.data, index_path=args.index)
    elif args.command == "validate":
        validate(data_path=args.data)
