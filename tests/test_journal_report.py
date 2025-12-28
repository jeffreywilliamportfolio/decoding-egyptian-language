from pathlib import Path

from pyramid_audit.report import build_report


def test_report_includes_journal(tmp_path: Path):
    journal = tmp_path / "journal"
    journal.mkdir()
    entries_path = journal / "entries.jsonl"
    entries_path.write_text(
        "{\"timestamp\":\"2025-12-28T00:00:00+00:00\",\"type\":\"hypothesis\",\"text\":\"Test note\",\"line_id\":\"line-1\"}\n",
        encoding="utf-8",
    )

    manifest = {
        "corpus": [
            {
                "label": "Relief",
                "lines": [
                    {
                        "line_id": "line-1",
                        "label": "Line 1",
                        "evidence_ids": [],
                        "image_paths": [],
                        "prior_readings": [],
                    }
                ],
            }
        ]
    }

    output = tmp_path / "REPORT.md"
    # Use cwd to point to tmp journal
    cwd = Path.cwd()
    try:
        # Swap journal path by temp chdir and copy entries
        (tmp_path / "journal").mkdir(exist_ok=True)
        (tmp_path / "journal" / "entries.jsonl").write_text(entries_path.read_text(encoding="utf-8"), encoding="utf-8")
        import os
        os.chdir(tmp_path)
        build_report(manifest, output)
    finally:
        import os
        os.chdir(cwd)

    content = output.read_text(encoding="utf-8")
    assert "Journal entries" in content
    assert "Test note" in content
