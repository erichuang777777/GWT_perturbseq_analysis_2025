# `stage_manifest.csv` is SUPERSEDED — do not use as the freeze authority

**Authoritative freeze manifest:** [`../FREEZE_MANIFEST.csv`](../FREEZE_MANIFEST.csv)
(machine pins: `version_id` + `md5` + `shape` + `bytes` per asset, verified by
`make freeze` / `scripts/freeze_pipeline.py` and the `tests/test_freeze_integrity.py`
guard).

## Why this file is retained but not authoritative

`_docs/stage_manifest.csv` was an early **planning / location** sheet. It differs from
the authoritative manifest in ways that make it unsafe as a source of truth:

- It lists assets as `(待產出)` / unproduced and points at transient `/tmp/data/`
  locations that no longer reflect the frozen repo layout.
- It carries **no `md5` or `version_id`**, so it cannot detect drift.
- Its column set (`stage,asset,type,current_location,description`) is a description,
  not a pin.

It is kept only as historical provenance of the original stage plan. Any consumer that
needs to know "what is frozen, at what checksum" must read `FREEZE_MANIFEST.csv`.

See also `../STAGE_SUMMARY_AND_FREEZE.md` (freeze narrative) and
`../PIPELINE_LINEAGE.md` (stage lineage).
