#!/usr/bin/env python3
import argparse
from pathlib import Path

from pyramid_audit.cluster_crops import generate_cluster_crops


def main() -> None:
    parser = argparse.ArgumentParser(description="Export per-cluster crops from observations.")
    parser.add_argument("--manifest", default="source_manifest.json", help="Path to source manifest JSON")
    parser.add_argument("--ledger", default="ledger/observations.jsonl", help="Path to observations ledger")
    parser.add_argument("--output-root", default=".", help="Repo root for evidence paths")
    args = parser.parse_args()

    generate_cluster_crops(Path(args.manifest), Path(args.ledger), Path(args.output_root))


if __name__ == "__main__":
    main()
