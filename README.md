# Forensic Egyptology Audit

This repo builds a reproducible “forensic Egyptology audit” pipeline for Pyramid Texts. It ingests a source manifest, renders evidence anchors (page images + crops), generates a corpus index, and produces ledgers + reports that separate **observed** data from **inferred** readings.

**Current scope (what it actually does today):**
- Seeds a representative corpus from **Faulkner 1969** supplement page 10 (Utterances 59A–63 for Neith, Nt 304–308).
- Links **near-primary plates** from Jequier 1933 (Planche VII–XIII) and **Sethe 1908** EOS page images as secondary evidence anchors.
- Imports **published English translations** (Mercer 1952, Utterances 59–63) as prior readings with provenance.
- Auto-segments glyph clusters from the primary evidence image (no sign identification yet).
- Generates `REPORT.md` with evidence images, secondary anchors, journal entries, and prior readings.

**What it does NOT do yet:**
- No automatic hieroglyph identification, transliteration, or translation generation.
- No direct PDF plate capture for Sethe 1908 vol. 1 (access still blocked by JS/availability).
- Discrepancy scoring is stubbed until sign observations or manual readings are added.

## Quick start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python scripts/cli.py build --manifest source_manifest.json
```

Outputs:
- `source_manifest.json`
- `corpus_index.csv`
- `evidence/` (rendered page image + crop)
- `ledger/observations.jsonl`
- `ledger/prior_readings.jsonl`
- `analysis/reconstructions.jsonl`
- `analysis/discrepancies.jsonl`
- `REPORT.md`

## Unified CLI

The project ships a single CLI entrypoint that wraps build, auto-annotation, and reporting.

```bash
. .venv/bin/activate
PYTHONPATH=src python scripts/cli.py run-all --manifest source_manifest.json
```

## Add manual observations

```bash
. .venv/bin/activate
PYTHONPATH=src python scripts/cli.py observe \\
  --line-id nt305_utt60_l1 \\
  --sign-id S1 \\
  --description \"Bird-like sign\" \\
  --bbox 10,20,30,40 \\
  --confidence 0.6 \\
  --direction right_to_left \\
  --direction-basis \"faces right\" \\
  --direction-confidence 0.7
```

## Tests

```bash
. .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

## Notes
- The current representative case does **not** invent signs or readings. Observations are empty until manual annotation is added.
- Add new sources and lines by extending `source_manifest.json` and re-running `scripts/build.py`.
- Jequier plate bands are auto-sliced and linked as **uncertain** secondary evidence; they are not content-matched and require manual verification.
- `scripts/build.py` preserves existing observations in `ledger/observations.jsonl`.

## Auto-annotation (hands-off bootstrap)

Auto-annotation finds glyph clusters from the primary evidence image and records bounding boxes with low confidence.

```bash
PYTHONPATH=src python scripts/cli.py auto-annotate --manifest source_manifest.json
```

Export per-cluster crops (so clusters can be reviewed as individual images):

```bash
PYTHONPATH=src python scripts/cli.py export-clusters --manifest source_manifest.json --ledger ledger/observations.jsonl
```

This also creates a contact sheet at `evidence/clusters/<line_id>/contact_sheet.png` and surfaces it in `REPORT.md`.

## Journal

Use `journal/entries.jsonl` to record hypotheses, decisions, and open questions.

```bash
PYTHONPATH=src python scripts/cli.py journal \\
  --type hypothesis \\
  --text \"Possible sign confusion between owl and falcon in Nt305\" \\
  --line-id nt305_utt60_l1 \\
  --confidence 0.3 \\
  --tags sign_confusion,review
```
