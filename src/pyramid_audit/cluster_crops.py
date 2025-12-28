from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image


def _load_manifest(manifest_path: Path) -> Dict[str, Any]:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _load_observations(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def _save_observations(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def _evidence_map(manifest: Dict[str, Any]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for source in manifest.get("sources", []):
        for item in source.get("items", []):
            for evidence in item.get("evidence", []):
                mapping[evidence["evidence_id"]] = evidence["output_path"]
    return mapping


def _make_contact_sheet(crop_paths: List[Path], out_path: Path, tile_size: int = 96, columns: int = 10) -> None:
    if not crop_paths:
        return
    rows = (len(crop_paths) + columns - 1) // columns
    sheet = Image.new("RGB", (tile_size * columns, tile_size * rows), color="white")
    for idx, crop_path in enumerate(crop_paths):
        img = Image.open(crop_path).convert("RGB")
        img.thumbnail((tile_size, tile_size))
        x = (idx % columns) * tile_size
        y = (idx // columns) * tile_size
        sheet.paste(img, (x, y))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def generate_cluster_crops(
    manifest_path: Path,
    observations_path: Path,
    output_root: Path,
) -> List[Dict[str, Any]]:
    manifest = _load_manifest(manifest_path)
    evidence_lookup = _evidence_map(manifest)
    records = _load_observations(observations_path)

    for record in records:
        line_id = record.get("line_id")
        evidence_ids = record.get("evidence_ids", [])
        if not evidence_ids:
            continue
        image_path = evidence_lookup.get(evidence_ids[0])
        if not image_path:
            continue
        img_path = output_root / image_path
        if not img_path.exists():
            continue
        img = Image.open(img_path)
        clusters = record.get("observed_signs", [])
        out_dir = output_root / "evidence" / "clusters" / line_id
        out_dir.mkdir(parents=True, exist_ok=True)
        crop_paths: List[Path] = []
        for idx, cluster in enumerate(clusters, start=1):
            bbox = cluster.get("bbox")
            if not bbox or len(bbox) != 4:
                continue
            x1, y1, x2, y2 = bbox
            crop = img.crop((int(x1), int(y1), int(x2), int(y2)))
            out_path = out_dir / f"{cluster.get('sign_id', f'cluster-{idx}')}.png"
            crop.save(out_path)
            cluster["crop_path"] = str(out_path.relative_to(output_root))
            crop_paths.append(out_path)

        if crop_paths:
            contact_path = out_dir / "contact_sheet.png"
            _make_contact_sheet(crop_paths, contact_path)
            record["cluster_contact_sheet"] = str(contact_path.relative_to(output_root))

    _save_observations(observations_path, records)
    return records
