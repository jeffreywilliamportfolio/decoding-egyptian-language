#!/usr/bin/env python3
import argparse
import copy
from pathlib import Path

from pyramid_audit.analysis import build_discrepancies, build_reconstructions
from pyramid_audit.evidence import build_evidence
from pyramid_audit.index import build_corpus_index
from pyramid_audit.ingest import load_manifest
from pyramid_audit.ledger import build_observations, build_prior_readings
from pyramid_audit.report import build_report


def attach_image_paths(manifest: dict) -> dict:
    manifest = copy.deepcopy(manifest)
    evidence_map = {}
    for source in manifest.get("sources", []):
        for item in source.get("items", []):
            for evidence in item.get("evidence", []):
                evidence_map[evidence["evidence_id"]] = evidence["output_path"]
    for relief in manifest.get("corpus", []):
        for line in relief.get("lines", []):
            line["image_paths"] = [evidence_map[eid] for eid in line.get("evidence_ids", []) if eid in evidence_map]
            line["secondary_image_paths"] = [
                evidence_map[eid] for eid in line.get("secondary_evidence_ids", []) if eid in evidence_map
            ]
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build forensic Egyptology audit artifacts.")
    parser.add_argument("--manifest", default="source_manifest.json", help="Path to source manifest JSON.")
    args = parser.parse_args()

    root = Path.cwd()
    manifest_path = root / args.manifest
    manifest = load_manifest(manifest_path)

    build_evidence(manifest, root)
    manifest_with_images = attach_image_paths(manifest)

    build_corpus_index(manifest_with_images, root / "corpus_index.csv")
    build_observations(manifest_with_images, root / "ledger" / "observations.jsonl")
    build_prior_readings(manifest_with_images, root / "ledger" / "prior_readings.jsonl")
    build_reconstructions(manifest_with_images, root / "analysis" / "reconstructions.jsonl")
    build_discrepancies(manifest_with_images, root / "analysis" / "discrepancies.jsonl")
    build_report(manifest_with_images, root / "REPORT.md")


if __name__ == "__main__":
    main()
