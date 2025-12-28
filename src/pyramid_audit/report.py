import json
from pathlib import Path
from typing import Any, Dict, List

from pyramid_audit.journal import group_entries_by_line, load_entries
from pyramid_audit.observations import load_observations


def load_prior_readings(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    readings: Dict[str, List[Dict[str, Any]]] = {}
    if not path.exists():
        return readings
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            readings.setdefault(record.get("line_id", ""), []).append(record)
    return readings


def build_report(manifest: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    journal_entries = group_entries_by_line(load_entries(Path("journal/entries.jsonl")))
    observations = {rec["line_id"]: rec for rec in load_observations(Path("ledger/observations.jsonl"))}
    prior_readings = load_prior_readings(Path("ledger/prior_readings.jsonl"))
    lines.append("# Forensic Egyptology Audit Report")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("Representative case from local source manifest. Observations and reconstructions are intentionally empty until manual annotation is provided.")
    lines.append("")

    for relief in manifest.get("corpus", []):
        lines.append(f"## {relief['label']}")
        lines.append("")
        if relief.get("notes"):
            lines.append(relief["notes"])
            lines.append("")
        for line in relief.get("lines", []):
            lines.append(f"### Line: {line['label']}")
            lines.append("")
            if line.get("notes"):
                lines.append(line["notes"])
                lines.append("")
            for image_path in line.get("image_paths", []):
                lines.append(f"![evidence]({image_path})")
                lines.append("")
            if line.get("secondary_image_paths"):
                lines.append("**Secondary evidence (uncertain mapping):**")
                lines.append("")
                for image_path in line.get("secondary_image_paths", []):
                    lines.append(f"![secondary]({image_path})")
                    lines.append("")
            if journal_entries.get(line["line_id"]):
                lines.append("**Journal entries:**")
                lines.append("")
                for entry in journal_entries[line["line_id"]]:
                    entry_type = entry.get("type", "entry")
                    text = entry.get("text", "")
                    confidence = entry.get("confidence")
                    tags = entry.get("tags", [])
                    meta = []
                    if confidence is not None:
                        meta.append(f"confidence {confidence}")
                    if tags:
                        meta.append("tags: " + ", ".join(tags))
                    meta_text = f" ({'; '.join(meta)})" if meta else ""
                    lines.append(f"- {entry_type}: {text}{meta_text}")
                lines.append("")
            obs_record = observations.get(line["line_id"])
            if obs_record and obs_record.get("observed_signs"):
                signs = obs_record["observed_signs"]
                auto_count = sum(1 for s in signs if str(s.get("sign_id", "")).startswith("auto-"))
                manual_count = len(signs) - auto_count
                crop_paths = [s.get("crop_path") for s in signs if s.get("crop_path")]
                if manual_count > 0:
                    lines.append(
                        f"**Observation status:** Manual observations {manual_count}; auto clusters {auto_count}."
                    )
                else:
                    lines.append(
                        f"**Observation status:** Auto-annotated clusters {auto_count} (manual review required)."
                    )
                contact_sheet = obs_record.get("cluster_contact_sheet")
                if contact_sheet:
                    lines.append("")
                    lines.append("**Cluster contact sheet:**")
                    lines.append("")
                    lines.append(f"![cluster-sheet]({contact_sheet})")
                    lines.append("")
                elif crop_paths:
                    lines.append("")
                    lines.append("**Cluster crops (sample):**")
                    lines.append("")
                    for crop_path in crop_paths[:6]:
                        lines.append(f"![cluster]({crop_path})")
                    lines.append("")
            else:
                lines.append("**Observation status:** No sign annotations recorded.")
            lines.append("")
            line_readings = prior_readings.get(line["line_id"], [])
            if line_readings:
                lines.append("**Prior readings:**")
                lines.append("")
                for reading in line_readings:
                    reading_type = reading.get("reading_type", "reading")
                    source_id = reading.get("source_id") or "unknown_source"
                    source_item_id = reading.get("source_item_id") or "unknown_item"
                    page = reading.get("page")
                    text = reading.get("text", "")
                    notes = reading.get("notes", "")
                    provenance = f"{source_id}/{source_item_id}"
                    if page is not None:
                        provenance += f" p.{page}"
                    lines.append(f"- {reading_type}: {provenance}")
                    if text:
                        lines.append(f"  text: {text}")
                    if notes:
                        lines.append(f"  notes: {notes}")
                lines.append("")
            lines.append("**Reconstruction status:** No candidate readings generated without observations.")
            lines.append("")
            lines.append("**Discrepancies:** None computed (no observed tokens).")
            lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
