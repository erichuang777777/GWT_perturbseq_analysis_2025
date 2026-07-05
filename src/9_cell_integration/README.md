# Cell-Level Integration Platform

This module is the scaffold for processing raw cell-level data and integrating
GWT cells with external single-cell datasets.

The intended workflow is:

```text
h5ad / 10x input files
-> manifest-driven ingestion
-> metadata harmonization
-> QC
-> AnnData concatenation
-> normalization / HVG / PCA
-> optional batch correction or integration
-> UMAP / Leiden
-> integrated h5ad + summary files
-> downstream perturbation, target-card, and disease-context analysis
```

## Why This Exists

The CSV-first target-card tool is good for triage. Cell-level integration is
needed when you want to answer questions such as:

- whether a target effect is cell-state specific
- whether only a responder subset changes
- whether guide assignment / escaped cells affect the signal
- whether an external atlas supports the same CD4 state
- whether batch correction changes biological interpretation

## Inputs

Create a manifest from `manifest.template.csv`.

Required columns:

- `dataset_id`
- `path`
- `format`: one of `h5ad`, `10x_h5`, `10x_mtx`

Useful metadata columns:

- `source_name`
- `species`
- `tissue`
- `cell_type`
- `condition`
- `donor_id`
- `disease`
- `platform`
- `perturbation_context`
- `obs_query`
- `max_cells`
- `apply_qc`

`obs_query` is a pandas expression evaluated on `adata.obs`, for example:

```text
cell_type == 'CD4 T cell'
```

## Run

Validate the manifest first:

```bash
python src/9_cell_integration/cell_integration_pipeline.py validate-manifest \
  --config src/9_cell_integration/cell_integration.example.yaml \
  --manifest src/9_cell_integration/manifest.template.csv
```

Run integration:

```bash
python src/9_cell_integration/cell_integration_pipeline.py run \
  --config src/9_cell_integration/cell_integration.example.yaml \
  --manifest path/to/manifest.csv \
  --output-h5ad outputs/cell_integration/integrated_cd4.h5ad \
  --summary-json outputs/cell_integration/integrated_cd4.summary.json
```

## Integration Methods

Set `integration.method` in the YAML config.

- `none`: PCA only. Good baseline.
- `combat`: expression-level correction sensitivity run. Do not use as the only
  source for target-effect inference.
- `harmony`: batch-corrected PCA representation. Requires `harmonypy`.
- `scvi`: probabilistic integration using raw counts. Requires `scvi-tools`.

Recommended default:

```yaml
integration:
  method: none
```

Then compare against `harmony` or `scvi` as a sensitivity analysis.

## Outputs

The pipeline writes:

- integrated `.h5ad`
- `.obs.csv`
- `.var.csv`
- summary JSON with cell counts, gene counts, metadata columns, obsm keys, and
  counts by dataset / condition / donor when available

## Important Guardrails

Do not treat integrated embeddings as primary differential-expression evidence.

Use integrated representations for:

- visualization
- cell-state matching
- batch diagnosis
- label transfer / atlas mapping
- responder-state exploration

Use raw-count or pseudobulk models for target-effect inference.

## Next Extensions

- backed/Zarr mode for very large data
- guide assignment QC report
- Mixscape / pertpy perturbation-response detection
- SCEPTRE / pseudobulk validation for top targets
- UCell/AUCell CD4 module scoring
- bridge integrated cell-state evidence back into target cards
