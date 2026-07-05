# Release Notes - M3.5 Upload / Import System

Date: 2026-07-05

## Scope

This release adds a staging-first upload/import workflow for the target evidence platform.

The feature supports:

- small CSV/TSV/TXT/JSON/JSONL upload from the dashboard
- local large-file registration for raw-cell files
- source type inference
- schema validation
- context match scoring
- import preview
- explicit approval gate
- source provenance metadata

No uploaded source is merged into target cards automatically.

## Changed Files

```text
src/3_DE_analysis/import_manager.py
src/3_DE_analysis/target_card_api.py
src/3_DE_analysis/target_card_dashboard.py
```

## API Endpoints

```text
POST /api/imports
GET  /api/imports
GET  /api/imports/{import_id}
GET  /api/imports/{import_id}/preview
POST /api/imports/{import_id}/approve
```

## Import Routes

```text
target_evidence    -> csv_evidence_layer
guide_evidence     -> csv_evidence_layer
external_evidence  -> external_evidence_layer
metadata_manifest  -> metadata_harmonization_layer
raw_cell_data       -> raw_cell_staging
unknown_table      -> staging_only
unknown_file       -> staging_only
```

## Approval Rules

An import can be approved only when it is a clean staged import.

Approval is blocked for:

- unknown source classification
- low or unknown context match in strict mode
- exploratory imports
- raw-cell files without manifest review
- metadata manifests missing integration-critical fields
- schema blocking issues
- duplicate normalized columns
- blank required values in preview
- non-numeric numeric fields in preview

Raw-cell files are staged only. They require manifest-level metadata before integration.

## Security Controls

- `declared_source_type` is whitelisted.
- table source types require table extensions.
- `raw_cell_data` requires raw-cell extensions.
- uploaded base64 content is limited to 25 MB.
- uploaded content supports table formats only.
- local file path registration is restricted to allowed roots.
- default allowed root is the project root.
- additional roots can be configured with `GWT_IMPORT_ALLOW_ROOTS`.
- target-card build input paths now use the same allowed-root model.

## Verification

Passed:

```text
python -m py_compile
API health check
target evidence import / preview / approve
external evidence import / approve
weak manifest approval blocked
CSV pretending raw-cell blocked
project-root-external target-card input path blocked
```

Release smoke artifacts were removed after verification.

## Running Services

Latest checked local services:

```text
API:       http://127.0.0.1:8005
Dashboard: http://127.0.0.1:8504
```

## Known Non-Blocking Issues

- Streamlit warns that `use_container_width` will be removed after 2025-12-31.
- Upload size is enforced in the app and dashboard, but production deployment should also enforce request-body limits at the server/proxy layer.
- This release stages and approves imports only; downstream merge into target cards is intentionally not implemented yet.
- Column mapping wizard is not implemented yet.

## Release Decision

Ready for local research-use release of M3.5 upload/import staging.

