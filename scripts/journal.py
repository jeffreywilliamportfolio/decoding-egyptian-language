#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_tags(value: str):
    if not value:
        return []
    return [tag.strip() for tag in value.split(",") if tag.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Append an entry to the audit journal.")
    parser.add_argument("--journal", default="journal/entries.jsonl", help="Path to journal JSONL")
    parser.add_argument("--type", required=True, choices=["observation", "hypothesis", "decision", "question", "next_step", "correction"])
    parser.add_argument("--text", required=True, help="Entry text")
    parser.add_argument("--line-id", help="Optional line identifier")
    parser.add_argument("--source-id", help="Optional source identifier")
    parser.add_argument("--confidence", type=float, help="Confidence 0-1")
    parser.add_argument("--tags", type=parse_tags, help="Comma-separated tags")

    args = parser.parse_args()

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": args.type,
        "text": args.text,
        "line_id": args.line_id,
        "source_id": args.source_id,
        "confidence": args.confidence,
        "tags": args.tags or [],
    }

    path = Path(args.journal)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


if __name__ == "__main__":
    main()
