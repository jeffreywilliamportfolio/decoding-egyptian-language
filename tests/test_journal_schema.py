import json
from pathlib import Path

from jsonschema import Draft202012Validator


def test_journal_schema():
    schema = json.loads(Path("schemas/journal.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    instance = {
        "timestamp": "2025-12-28T00:00:00+00:00",
        "type": "observation",
        "text": "Placeholder entry",
        "line_id": "nt305_utt60_l1",
        "source_id": "faulkner1969",
        "confidence": 0.5,
        "tags": ["seed"],
    }
    errors = list(validator.iter_errors(instance))
    assert not errors
