#!/usr/bin/env python3
import argparse
from pathlib import Path

from pyramid_audit.observations import add_sign_observation


def parse_bbox(value: str):
    parts = [p.strip() for p in value.split(",") if p.strip()]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("bbox must be x1,y1,x2,y2")
    return [float(p) for p in parts]


def main() -> None:
    parser = argparse.ArgumentParser(description="Add manual sign observations to ledger/observations.jsonl")
    parser.add_argument("--ledger", default="ledger/observations.jsonl", help="Path to observations JSONL")
    parser.add_argument("--line-id", required=True, help="Line identifier to update")
    parser.add_argument("--sign-id", required=True, help="Sign identifier (manual/temporary ok)")
    parser.add_argument("--description", required=True, help="Freeform description of observed sign")
    parser.add_argument("--bbox", type=parse_bbox, help="Bounding box x1,y1,x2,y2 in evidence image coordinates")
    parser.add_argument("--confidence", type=float, help="Confidence 0-1 for the sign observation")
    parser.add_argument("--direction", choices=["left_to_right", "right_to_left", "top_to_bottom", "bottom_to_top", "unknown"], help="Line directionality")
    parser.add_argument("--direction-basis", help="Basis for directionality (e.g., facing figures)")
    parser.add_argument("--direction-confidence", type=float, help="Confidence for directionality")

    args = parser.parse_args()

    add_sign_observation(
        Path(args.ledger),
        line_id=args.line_id,
        sign_id=args.sign_id,
        description=args.description,
        bbox=args.bbox,
        confidence=args.confidence,
        direction=args.direction,
        direction_basis=args.direction_basis,
        direction_confidence=args.direction_confidence,
    )


if __name__ == "__main__":
    main()
