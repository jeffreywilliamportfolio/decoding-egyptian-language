import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def load_schema(name: str):
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


def validate(schema_name: str, instance: dict):
    schema = load_schema(schema_name)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    assert not errors, [e.message for e in errors]


def test_observation_schema():
    instance = {
        "line_id": "nt305_utt60_l1",
        "evidence_ids": ["faulkner1969_p10_nt305"],
        "observed_signs": [],
        "directionality": {"value": "unknown", "basis": "not evaluated", "confidence": 0.0},
        "uncertainty": 1.0,
        "observed_only": True,
        "notes": "empty",
    }
    validate("observations.schema.json", instance)


def test_prior_reading_schema():
    instance = {
        "line_id": "nt305_utt60_l1",
        "reading_id": None,
        "source_id": "faulkner1969",
        "source_item_id": "faulkner1969_p10",
        "page": 10,
        "reading_type": "handcopy_only",
        "text": "",
        "notes": "none",
    }
    validate("prior_readings.schema.json", instance)


def test_reconstruction_schema():
    instance = {
        "line_id": "nt305_utt60_l1",
        "candidates": [],
        "transliteration_candidates": [],
        "parse_candidates": [],
        "translation_candidates": [],
        "confidence": 0.0,
        "notes": "none",
    }
    validate("reconstructions.schema.json", instance)


def test_discrepancy_schema():
    instance = {
        "line_id": "nt305_utt60_l1",
        "reading_id": None,
        "severity": "none",
        "diff_ratio": 0.0,
        "likely_cause": "no_data",
        "notes": "none",
    }
    validate("discrepancies.schema.json", instance)
