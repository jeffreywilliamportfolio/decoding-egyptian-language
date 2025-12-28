import json
from pathlib import Path
from typing import Any, Dict

from jsonschema import Draft202012Validator

SCHEMA_NAME = "source_manifest.schema.json"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_schema(name: str) -> Dict[str, Any]:
    schema_path = repo_root() / "schemas" / name
    with schema_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_manifest(path: Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: Dict[str, Any]) -> None:
    schema = load_schema(SCHEMA_NAME)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(manifest), key=lambda e: e.path)
    if errors:
        message_lines = ["source_manifest.json failed validation:"]
        for err in errors:
            path = "/".join(str(p) for p in err.path)
            message_lines.append(f"- {path}: {err.message}")
        raise ValueError("\n".join(message_lines))
