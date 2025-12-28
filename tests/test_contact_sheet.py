from pathlib import Path
import json

from PIL import Image, ImageDraw

from pyramid_audit.cluster_crops import generate_cluster_crops


def test_contact_sheet_created(tmp_path: Path):
    img = Image.new("RGB", (100, 50), color="white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 30, 30], fill="black")
    draw.rectangle([40, 10, 60, 30], fill="black")
    evidence_path = tmp_path / "evidence" / "line.png"
    evidence_path.parent.mkdir(parents=True)
    img.save(evidence_path)

    manifest = {
        "sources": [
            {
                "source_id": "local",
                "type": "image",
                "title": "test",
                "author": "test",
                "year": 2000,
                "local_path": "",
                "items": [
                    {
                        "item_id": "item1",
                        "page": 1,
                        "contents": "",
                        "relevance": "",
                        "evidence": [
                            {"evidence_id": "ev1", "kind": "page_image", "output_path": "evidence/line.png"}
                        ],
                    }
                ],
            }
        ]
    }
    manifest_path = tmp_path / "source_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    observations = [
        {
            "line_id": "line-1",
            "evidence_ids": ["ev1"],
            "observed_signs": [
                {"sign_id": "auto-1", "description": "cluster", "bbox": [10, 10, 30, 30]},
                {"sign_id": "auto-2", "description": "cluster", "bbox": [40, 10, 60, 30]},
            ],
            "directionality": {"value": "unknown", "basis": "n/a", "confidence": 0.0},
            "uncertainty": 1.0,
            "observed_only": True,
        }
    ]
    obs_path = tmp_path / "ledger" / "observations.jsonl"
    obs_path.parent.mkdir(parents=True)
    with obs_path.open("w", encoding="utf-8") as handle:
        for rec in observations:
            handle.write(json.dumps(rec) + "\n")

    generate_cluster_crops(manifest_path, obs_path, tmp_path)

    updated_line = obs_path.read_text(encoding="utf-8").strip().splitlines()[0]
    updated = json.loads(updated_line)
    contact_path = updated.get("cluster_contact_sheet")
    assert contact_path
    assert (tmp_path / contact_path).exists()
