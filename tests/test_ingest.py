from pathlib import Path

from pyramid_audit.ingest import load_manifest


def test_manifest_validates():
    manifest = load_manifest(Path("source_manifest.json"))
    assert manifest["manifest_version"]
    assert manifest["sources"]


def test_evidence_linking():
    manifest = load_manifest(Path("source_manifest.json"))
    evidence_ids = set()
    for source in manifest["sources"]:
        for item in source["items"]:
            for evidence in item["evidence"]:
                evidence_ids.add(evidence["evidence_id"])
    for relief in manifest["corpus"]:
        for line in relief["lines"]:
            for eid in line["evidence_ids"]:
                assert eid in evidence_ids
            for eid in line.get("secondary_evidence_ids", []):
                assert eid in evidence_ids
