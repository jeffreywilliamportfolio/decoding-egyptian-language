import json
from pathlib import Path
from typing import Any, Dict, List


def build_observations(manifest: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    existing: Dict[str, Dict[str, Any]] = {}
    if output_path.exists():
        with output_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                existing[record.get("line_id")] = record

    records: List[Dict[str, Any]] = []
    for relief in manifest.get("corpus", []):
        for line in relief.get("lines", []):
            line_id = line["line_id"]
            if line_id in existing:
                record = existing[line_id]
                record["evidence_ids"] = line.get("evidence_ids", [])
            else:
                record = {
                    "line_id": line_id,
                    "evidence_ids": line.get("evidence_ids", []),
                    "observed_signs": [],
                    "directionality": {
                        "value": "unknown",
                        "basis": "not evaluated",
                        "confidence": 0.0,
                    },
                    "uncertainty": 1.0,
                    "observed_only": True,
                    "notes": "No manual sign annotation yet; observations intentionally empty.",
                }
            records.append(record)

    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def build_prior_readings(manifest: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for relief in manifest.get("corpus", []):
            for line in relief.get("lines", []):
                prior_readings: List[Dict[str, Any]] = line.get("prior_readings", [])
                if prior_readings:
                    for reading in prior_readings:
                        record = {
                            "line_id": line["line_id"],
                            "reading_id": reading.get("reading_id"),
                            "source_id": reading.get("source_id"),
                            "source_item_id": reading.get("source_item_id"),
                            "page": reading.get("page"),
                            "reading_type": reading.get("reading_type"),
                            "text": reading.get("text", ""),
                            "notes": reading.get("notes", ""),
                        }
                        handle.write(json.dumps(record, ensure_ascii=True) + "\n")
                else:
                    record = {
                        "line_id": line["line_id"],
                        "reading_id": None,
                        "source_id": relief.get("source_id", None),
                        "source_item_id": relief["source_item_id"],
                        "page": None,
                        "reading_type": "handcopy_only",
                        "text": "",
                        "notes": "No published transliteration/translation recorded for this line in the manifest.",
                    }
                    handle.write(json.dumps(record, ensure_ascii=True) + "\n")
