import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def load_entries(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


def group_entries_by_line(entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for entry in entries:
        line_id = entry.get("line_id")
        if not line_id:
            continue
        grouped.setdefault(line_id, []).append(entry)
    return grouped


def append_entry(
    entry_type: str,
    text: str,
    line_id: str | None = None,
    source_id: str | None = None,
    confidence: float | None = None,
    tags: List[str] | None = None,
    journal_path: Path | None = None,
) -> None:
    path = journal_path or Path("journal/entries.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": entry_type,
        "text": text,
        "line_id": line_id,
        "source_id": source_id,
        "confidence": confidence,
        "tags": tags or [],
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")
