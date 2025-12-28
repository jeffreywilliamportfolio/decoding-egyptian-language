#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from pyramid_audit.auto_annotate import AutoAnnotateConfig, auto_annotate_line
from pyramid_audit.ingest import load_manifest
from pyramid_audit.observations import load_observations, save_observations


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto-annotate glyph clusters from evidence images.")
    parser.add_argument("--manifest", default="source_manifest.json", help="Source manifest path")
    parser.add_argument("--ledger", default="ledger/observations.jsonl", help="Observations ledger path")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing observations")
    parser.add_argument("--threshold", type=int, default=140)
    parser.add_argument("--scale", type=float, default=0.5)
    parser.add_argument("--min-area", type=int, default=80)
    parser.add_argument("--dilation", type=int, default=3)
    parser.add_argument("--margin", type=int, default=4)

    args = parser.parse_args()

    manifest = load_manifest(Path(args.manifest))
    observations = load_observations(Path(args.ledger))

    obs_by_line = {rec["line_id"]: rec for rec in observations}
    evidence_map = {}
    for source in manifest.get("sources", []):
        for item in source.get("items", []):
            for evidence in item.get("evidence", []):
                evidence_map[evidence["evidence_id"]] = evidence["output_path"]

    cfg = AutoAnnotateConfig(
        threshold=args.threshold,
        scale=args.scale,
        min_area=args.min_area,
        dilation=args.dilation,
        margin=args.margin,
    )

    for relief in manifest.get("corpus", []):
        for line in relief.get("lines", []):
            line_id = line["line_id"]
            record = obs_by_line.get(line_id)
            if record is None:
                record = {
                    "line_id": line_id,
                    "evidence_ids": line.get("evidence_ids", []),
                    "observed_signs": [],
                    "directionality": {"value": "unknown", "basis": "not evaluated", "confidence": 0.0},
                    "uncertainty": 1.0,
                    "observed_only": True,
                    "notes": "",
                }
                observations.append(record)
                obs_by_line[line_id] = record

            if record.get("observed_signs") and not args.overwrite:
                continue

            evidence_ids = line.get("evidence_ids", [])
            image_paths = [Path(evidence_map[eid]) for eid in evidence_ids if eid in evidence_map]
            if not image_paths:
                continue
            image_path = image_paths[0]
            signs = auto_annotate_line(image_path, line_id, cfg)
            record["observed_signs"] = signs
            record["notes"] = (
                "Auto-segmented glyph clusters from evidence image; uninterpreted and requires review."
            )
            record["uncertainty"] = 0.9

    save_observations(Path(args.ledger), observations)


if __name__ == "__main__":
    main()
