from pathlib import Path
import json

from PIL import Image, ImageDraw

from pyramid_audit.cluster_crops import generate_cluster_crops


def test_generate_cluster_crops(tmp_path: Path):
    # Create fake manifest with one evidence image
    img = Image.new("RGB", (100, 50), color="white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 30, 30], fill="black")
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
                            {
                                "evidence_id": "ev1",
                                "kind": "page_image",
                                "output_path": "evidence/line.png",
                            }
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
                {"sign_id": "auto-line-1-1", "description": "cluster", "bbox": [10, 10, 30, 30]}
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
    assert updated["observed_signs"][0].get("crop_path")
    crop_path = tmp_path / updated["observed_signs"][0]["crop_path"]
    assert crop_path.exists()
