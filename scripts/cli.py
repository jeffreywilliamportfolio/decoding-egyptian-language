#!/usr/bin/env python3
import argparse
import copy
from pathlib import Path

from pyramid_audit.analysis import build_discrepancies, build_reconstructions
from pyramid_audit.auto_annotate import AutoAnnotateConfig, auto_annotate_line
from pyramid_audit.cluster_crops import generate_cluster_crops
from pyramid_audit.evidence import build_evidence
from pyramid_audit.index import build_corpus_index
from pyramid_audit.ingest import load_manifest
from pyramid_audit.journal import append_entry
from pyramid_audit.ledger import build_observations, build_prior_readings
from pyramid_audit.observations import add_sign_observation, load_observations, save_observations
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


def run_build(manifest_path: Path) -> None:
    root = Path.cwd()
    manifest = load_manifest(manifest_path)
    build_evidence(manifest, root)
    manifest_with_images = attach_image_paths(manifest)
    build_corpus_index(manifest_with_images, root / "corpus_index.csv")
    build_observations(manifest_with_images, root / "ledger" / "observations.jsonl")
    build_prior_readings(manifest_with_images, root / "ledger" / "prior_readings.jsonl")
    build_reconstructions(manifest_with_images, root / "analysis" / "reconstructions.jsonl")
    build_discrepancies(manifest_with_images, root / "analysis" / "discrepancies.jsonl")
    build_report(manifest_with_images, root / "REPORT.md")


def run_auto_annotate(manifest_path: Path, ledger_path: Path, args) -> None:
    manifest = load_manifest(manifest_path)
    observations = load_observations(ledger_path)
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
            record["notes"] = "Auto-segmented glyph clusters from evidence image; uninterpreted and requires review."
            record["uncertainty"] = 0.9

    save_observations(ledger_path, observations)


def run_export_clusters(manifest_path: Path, ledger_path: Path, output_root: Path) -> None:
    generate_cluster_crops(manifest_path, ledger_path, output_root)


def run_report(manifest_path: Path) -> None:
    manifest = load_manifest(manifest_path)
    manifest_with_images = attach_image_paths(manifest)
    build_report(manifest_with_images, Path("REPORT.md"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified CLI for the forensic Egyptology audit pipeline.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Render evidence and build outputs.")
    build_parser.add_argument("--manifest", default="source_manifest.json", help="Path to source manifest JSON.")

    auto_parser = subparsers.add_parser("auto-annotate", help="Auto-annotate glyph clusters.")
    auto_parser.add_argument("--manifest", default="source_manifest.json", help="Source manifest path")
    auto_parser.add_argument("--ledger", default="ledger/observations.jsonl", help="Observations ledger path")
    auto_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing observations")
    auto_parser.add_argument("--threshold", type=int, default=140)
    auto_parser.add_argument("--scale", type=float, default=0.5)
    auto_parser.add_argument("--min-area", type=int, default=80)
    auto_parser.add_argument("--dilation", type=int, default=3)
    auto_parser.add_argument("--margin", type=int, default=4)

    export_parser = subparsers.add_parser("export-clusters", help="Export per-cluster crops.")
    export_parser.add_argument("--manifest", default="source_manifest.json", help="Path to source manifest JSON")
    export_parser.add_argument("--ledger", default="ledger/observations.jsonl", help="Path to observations ledger")
    export_parser.add_argument("--output-root", default=".", help="Repo root for evidence paths")

    report_parser = subparsers.add_parser("report", help="Rebuild REPORT.md from the manifest + observations.")
    report_parser.add_argument("--manifest", default="source_manifest.json", help="Path to source manifest JSON.")

    observe_parser = subparsers.add_parser("observe", help="Add a manual sign observation.")
    observe_parser.add_argument("--ledger", default="ledger/observations.jsonl", help="Path to observations JSONL")
    observe_parser.add_argument("--line-id", required=True, help="Line identifier to update")
    observe_parser.add_argument("--sign-id", required=True, help="Sign identifier (manual/temporary ok)")
    observe_parser.add_argument("--description", required=True, help="Freeform description of observed sign")
    observe_parser.add_argument("--bbox", help="Bounding box x1,y1,x2,y2 in evidence image coordinates")
    observe_parser.add_argument("--confidence", type=float, help="Confidence 0-1 for the sign observation")
    observe_parser.add_argument(
        "--direction",
        choices=["left_to_right", "right_to_left", "top_to_bottom", "bottom_to_top", "unknown"],
        help="Line directionality",
    )
    observe_parser.add_argument("--direction-basis", help="Basis for directionality (e.g., facing figures)")
    observe_parser.add_argument("--direction-confidence", type=float, help="Confidence for directionality")

    journal_parser = subparsers.add_parser("journal", help="Append an entry to the audit journal.")
    journal_parser.add_argument("--type", required=True, help="Entry type (hypothesis, decision, question, etc.)")
    journal_parser.add_argument("--text", required=True, help="Entry text")
    journal_parser.add_argument("--line-id", help="Optional line identifier")
    journal_parser.add_argument("--confidence", type=float, help="Confidence 0-1 for the entry")
    journal_parser.add_argument("--tags", help="Comma-separated tags")

    runall_parser = subparsers.add_parser("run-all", help="Build, auto-annotate, export clusters, rebuild report.")
    runall_parser.add_argument("--manifest", default="source_manifest.json", help="Path to source manifest JSON.")
    runall_parser.add_argument("--ledger", default="ledger/observations.jsonl", help="Observations ledger path")
    runall_parser.add_argument("--output-root", default=".", help="Repo root for evidence paths")
    runall_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing observations")
    runall_parser.add_argument("--threshold", type=int, default=140)
    runall_parser.add_argument("--scale", type=float, default=0.5)
    runall_parser.add_argument("--min-area", type=int, default=80)
    runall_parser.add_argument("--dilation", type=int, default=3)
    runall_parser.add_argument("--margin", type=int, default=4)

    args = parser.parse_args()
    manifest_path = Path(getattr(args, "manifest", "source_manifest.json"))

    if args.command == "build":
        run_build(manifest_path)
    elif args.command == "auto-annotate":
        run_auto_annotate(manifest_path, Path(args.ledger), args)
    elif args.command == "export-clusters":
        run_export_clusters(manifest_path, Path(args.ledger), Path(args.output_root))
    elif args.command == "report":
        run_report(manifest_path)
    elif args.command == "observe":
        bbox = None
        if args.bbox:
            parts = [p.strip() for p in args.bbox.split(",") if p.strip()]
            if len(parts) != 4:
                raise SystemExit("bbox must be x1,y1,x2,y2")
            bbox = [float(p) for p in parts]
        add_sign_observation(
            Path(args.ledger),
            line_id=args.line_id,
            sign_id=args.sign_id,
            description=args.description,
            bbox=bbox,
            confidence=args.confidence,
            direction=args.direction,
            direction_basis=args.direction_basis,
            direction_confidence=args.direction_confidence,
        )
    elif args.command == "journal":
        tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
        append_entry(
            entry_type=args.type,
            text=args.text,
            line_id=args.line_id,
            confidence=args.confidence,
            tags=tags,
        )
    elif args.command == "run-all":
        run_build(manifest_path)
        run_auto_annotate(manifest_path, Path(args.ledger), args)
        run_export_clusters(manifest_path, Path(args.ledger), Path(args.output_root))
        run_report(manifest_path)
    else:
        raise SystemExit(f"Unknown command {args.command}")


if __name__ == "__main__":
    main()
