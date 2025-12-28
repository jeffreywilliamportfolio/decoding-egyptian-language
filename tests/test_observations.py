from pathlib import Path

from pyramid_audit.observations import add_sign_observation, load_observations, save_observations


def test_add_sign_observation(tmp_path: Path):
    ledger_path = tmp_path / "observations.jsonl"
    records = [
        {
            "line_id": "nt305_utt60_l1",
            "evidence_ids": ["faulkner1969_p10_nt305_utt60"],
            "observed_signs": [],
            "directionality": {"value": "unknown", "basis": "not evaluated", "confidence": 0.0},
            "uncertainty": 1.0,
            "observed_only": True,
            "notes": "",
        }
    ]
    save_observations(ledger_path, records)

    add_sign_observation(
        ledger_path,
        line_id="nt305_utt60_l1",
        sign_id="S1",
        description="Bird-like sign",
        bbox=[10, 20, 30, 40],
        confidence=0.6,
        direction="right_to_left",
        direction_basis="faces right",
        direction_confidence=0.7,
    )

    updated = load_observations(ledger_path)
    assert updated[0]["observed_signs"]
    assert updated[0]["observed_signs"][0]["sign_id"] == "S1"
    assert updated[0]["directionality"]["value"] == "right_to_left"
