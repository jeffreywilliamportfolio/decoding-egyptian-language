import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_observations(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def save_observations(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def _ensure_line_record(records: List[Dict[str, Any]], line_id: str) -> Dict[str, Any]:
    for record in records:
        if record.get("line_id") == line_id:
            return record
    raise ValueError(f"line_id not found in observations: {line_id}")


def add_sign_observation(
    path: Path,
    line_id: str,
    sign_id: str,
    description: str,
    bbox: Optional[List[float]] = None,
    confidence: Optional[float] = None,
    direction: Optional[str] = None,
    direction_basis: Optional[str] = None,
    direction_confidence: Optional[float] = None,
) -> None:
    records = load_observations(path)
    record = _ensure_line_record(records, line_id)
    sign_entry: Dict[str, Any] = {"sign_id": sign_id, "description": description}
    if bbox:
        sign_entry["bbox"] = bbox
    if confidence is not None:
        sign_entry["confidence"] = confidence
    record.setdefault("observed_signs", []).append(sign_entry)

    if direction:
        record["directionality"] = {
            "value": direction,
            "basis": direction_basis or "manual",
            "confidence": direction_confidence if direction_confidence is not None else 0.5,
        }

    save_observations(path, records)
