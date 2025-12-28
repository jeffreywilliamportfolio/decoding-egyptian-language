import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def score_discrepancy(
    observed_tokens: List[str],
    prior_tokens: List[str],
    directionality_mismatch: bool = False,
) -> Dict[str, Any]:
    if not observed_tokens and not prior_tokens:
        return {"severity": "none", "diff_ratio": 0.0, "likely_cause": "no_data"}
    if directionality_mismatch:
        return {"severity": "major", "diff_ratio": 1.0, "likely_cause": "directionality_mismatch"}
    total = max(len(observed_tokens), len(prior_tokens))
    diffs = sum(1 for a, b in zip(observed_tokens, prior_tokens) if a != b)
    diffs += abs(len(observed_tokens) - len(prior_tokens))
    ratio = diffs / total if total else 0.0
    if ratio == 0:
        severity = "none"
        cause = "no_discrepancy"
    elif ratio <= 0.5:
        severity = "minor"
        cause = "sign_confusion"
    elif ratio <= 0.8:
        severity = "major"
        cause = "omission_or_addition"
    else:
        severity = "critical"
        cause = "substantial_divergence"
    return {"severity": severity, "diff_ratio": ratio, "likely_cause": cause}


def build_reconstructions(manifest: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for relief in manifest.get("corpus", []):
            for line in relief.get("lines", []):
                record = {
                    "line_id": line["line_id"],
                    "candidates": [],
                    "transliteration_candidates": [],
                    "parse_candidates": [],
                    "translation_candidates": [],
                    "confidence": 0.0,
                    "notes": "No reconstruction without manual observation input.",
                }
                handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def build_discrepancies(manifest: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for relief in manifest.get("corpus", []):
            for line in relief.get("lines", []):
                prior_readings = line.get("prior_readings", [])
                if not prior_readings:
                    continue
                for reading in prior_readings:
                    observed_tokens = []
                    prior_tokens = reading.get("tokens", [])
                    score = score_discrepancy(observed_tokens, prior_tokens)
                    record = {
                        "line_id": line["line_id"],
                        "reading_id": reading.get("reading_id"),
                        "severity": score["severity"],
                        "diff_ratio": score["diff_ratio"],
                        "likely_cause": score["likely_cause"],
                        "notes": "No observed tokens to compare; discrepancy scoring deferred.",
                    }
                    handle.write(json.dumps(record, ensure_ascii=True) + "\n")
