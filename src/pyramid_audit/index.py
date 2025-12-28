import csv
from pathlib import Path
from typing import Any, Dict


def _item_page_map(manifest: Dict[str, Any]) -> Dict[str, int]:
    mapping: Dict[str, int] = {}
    for source in manifest.get("sources", []):
        for item in source.get("items", []):
            mapping[item["item_id"]] = item["page"]
    return mapping


def build_corpus_index(manifest: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    item_pages = _item_page_map(manifest)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "relief_id",
                "line_id",
                "label",
                "source_item_id",
                "page",
                "evidence_ids",
                "image_paths",
                "secondary_evidence_ids",
                "secondary_image_paths",
                "prior_reading_refs",
            ],
        )
        writer.writeheader()
        for relief in manifest.get("corpus", []):
            source_item_id = relief["source_item_id"]
            page = item_pages.get(source_item_id)
            for line in relief.get("lines", []):
                evidence_ids = line.get("evidence_ids", [])
                image_paths = line.get("image_paths", [])
                secondary_ids = line.get("secondary_evidence_ids", [])
                secondary_paths = line.get("secondary_image_paths", [])
                prior_refs = [ref.get("source_id") for ref in line.get("prior_readings", [])]
                writer.writerow(
                    {
                        "relief_id": relief["relief_id"],
                        "line_id": line["line_id"],
                        "label": line["label"],
                        "source_item_id": source_item_id,
                        "page": page,
                        "evidence_ids": ";".join(evidence_ids),
                        "image_paths": ";".join(image_paths),
                        "secondary_evidence_ids": ";".join(secondary_ids),
                        "secondary_image_paths": ";".join(secondary_paths),
                        "prior_reading_refs": ";".join(prior_refs),
                    }
                )
