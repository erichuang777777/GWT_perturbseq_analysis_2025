## Preparing for DE analysis


> [!WARNING]
> `DE_config_local.yaml` is a reduced/demo configuration with `reduced_targets_only: true`.
> Outputs from reduced-target runs are appropriate for smoke tests and local examples,
> but they must not be used to claim genome-wide hit rates, genome-wide FDR, or
> full-screen target rankings. Use `DE_config_full.yaml` or copy
> `DE_config_full.template.yaml` for manuscript-scale/full-screen analyses.

1. Identify putative ineffective guides (no on-target knockdown with sufficient confidence) - see `src/1_preprocess/estimate_guide_effect.ipynb`

2. Pseudobulk dataset by replicate
```bash
conda activate gwt-env
DATADIR=/path/to/data/GWT/
EXPERIMENT_NAME=CD4iR2_Psomagen

H5AD_FILES=$(ls $DATADIR/$EXPERIMENT_NAME/tmp/*.postQC.h5ad)
for f in $H5AD_FILES; do
sbatch \
    --partition=pritch \
    --job-name=pbulk_${f} \
    --output=$GROUP_SCRATCH/emma/slurm-pbulk_%j.out \
    --error=$GROUP_SCRATCH/emma/slurm-pbulk_%j.err \
    --nodes=1 \
    --ntasks=1 \
    --cpus-per-task=1 \
    --mem=20G \
    --time=0:30:00 \
    --wrap="python make_pseudobulk.py aggregate ${f} --sample_metadata_csv ${DATADIR}/sample_metadata/GWT_sample_metadata.${EXPERIMENT_NAME}.csv"
done
```

Merge pseudobulks for each sample. The merge step reads input locations from the DE YAML config, so another machine only needs the same relative directory layout or an explicit list of input globs. Relative `pseudobulk_input_globs` entries are resolved under `{datadir}/{experiment_name}`.

Example config (`DE_config_pseudobulk_merge.yaml`):
```yaml
experiment_name: "CD4i_final"
datadir: "/path/to/data/GWT"
run_name: "all_confounders"

# Use the default output layout from `make_pseudobulk.py aggregate`:
# /path/to/data/GWT/CD4i_final/tmp/*DE_pseudobulk.h5ad
pseudobulk_input_globs:
  - "tmp/*DE_pseudobulk.h5ad"

# If the pseudobulks live outside datadir/experiment_name, use absolute globs:
# pseudobulk_input_globs:
#   - "/path/to/CD4iR1_Psomagen/tmp/*DE_pseudobulk.h5ad"
#   - "/path/to/CD4iR2_Psomagen/tmp/*DE_pseudobulk.h5ad"
```

Run locally from `src/3_DE_analysis`:
```bash
conda activate gwt-env
python make_pseudobulk.py merge CD4i_R2_D4_Stim8hr_CD4i_R2_Ultima --DE_config DE_config_pseudobulk_merge.yaml
```

Or submit with SLURM:
```bash
for SAMPLE_ID in CD4i_R2_D4_Stim8hr_CD4i_R2_Ultima; do
    sbatch \
        --partition=pritch \
        --job-name=pbulk_merge_${SAMPLE_ID} \
        --output=$GROUP_SCRATCH/emma/slurm-pbulk_%j.out \
        --error=$GROUP_SCRATCH/emma/slurm-pbulk_%j.err \
        --nodes=1 \
        --ntasks=1 \
        --cpus-per-task=1 \
        --mem=20G \
        --time=0:30:00 \
        --wrap="python make_pseudobulk.py merge $SAMPLE_ID --DE_config DE_config_pseudobulk_merge.yaml"
done
```

3. Select common features to test and split perturbations to test into chunks - store parameters in config file
```bash
prep_DE.ipynb 
```

Output files (required for DE analysis scripts):

- Pseudobulk expression, with annotation of samples to keep for DE analysis in `.obs['keep_for_DE']` (`{datadir}/{experiment_name}_merged.DE_pseudobulk.h5ad`)
- List of transcriptome genes to test for DE (`{datadir}/DE_test_genes.{condition}.txt`)
- Assignment of perturbations to processing chunks (`f'{datadir}/DE_target2chunk.{condition}csv.gz'`)

## Running DE analysis 

Submit DE analysis for each chunk (with SLURM)
```bash
for c in Rest Stim8hr Stim48hr; do 
    ./submit_DE_chunked.sh DE_config_full.yaml $c
done

Merge outputs in AnnData object
```bash
python merge_DE_results.py --config DE_config_full.yaml
```


### Primary DE model and guide-level robustness interpretation

The primary differential-expression (DE) analysis estimates **target-level effects** from guide-by-donor-by-condition pseudobulk samples. Within each culture condition and DE chunk, the DESeq2 design is:

```yaml
design_formula: '~ log10_n_cells + donor_id + target'
```

In this formulation, `target` is the perturbation contrast of interest, `donor_id` adjusts for donor-level baseline differences, and `log10_n_cells` adjusts for the number of cells contributing to each pseudobulk. The primary DE signal reported in `DE_stats` (for example `n_total_de_genes`, `ontarget_effect_size`, and gene-level log fold changes) should therefore be read as a target-level effect against the non-targeting-control baseline, not as a guide-specific coefficient.

Guide-level variability is evaluated downstream rather than modeled as a primary random or fixed effect in the DE formula. The downstream confidence layer uses fields such as `crossguide_correlation`, `replicate_pass_flag`, `offtarget_flag`, upstream pseudobulk inclusion flags including `keep_effective_guides`, and guide knockdown summaries from `guide_kd_efficiency.suppl_table.csv` to distinguish target-level signal from guide-robust evidence.

When ranking targets or writing biological claims, distinguish the **primary DE signal** (magnitude and breadth of the target-level DE result) from the **guide-robust high-confidence signal** (DE signal that also passes guide/donor/off-target/knockdown robustness checks). Interpret top targets through the high-confidence / `replicate_pass_flag=True` subset whenever making biological claims, and treat high primary-DE ranks without guide-robust support as hypotheses requiring follow-up validation.

## Analysing DE results

- `DE_results_analysis_full.ipynb` - exploratory analysis of DE results 
- `FACS_comparison_full.ipynb` - comparison of DE results with FACS screens from Marson Lab

## Output files 

-  `{experiment_name}_merged.DE_pseudobulk.h5ad` - Pseudobulked data object (sum of counts across donor-condition-guide)
- `{datadir}/DE_results_{run_name}/{experiment_name}.merged_DE_results.h5ad` - DE analysis statistics for each perturbation and condition
- `{datadir}/DE_results_{run_name}/DE_summary_stats_per_target.csv` - Summary of on-target effects and overall effect for each perturbation and condition

## Target card API + web portal (optional dev flow)

Use these commands from repo root:

```bash
conda activate gwt-env
python -m pip install fastapi uvicorn pyarrow  # pyarrow: reads the §1.12 overlay .parquet snapshots

# run API (also serves the live upload tool at /upload)
uvicorn target_card_api:app --app-dir src/3_DE_analysis --reload --port 8000

# open another terminal and run the portal (now an independent frontend package,
# see frontend/README.md and frontend/webserver/README.md — it talks to the API
# above purely over HTTP, only for the /upload tool; browsing reads a static
# pre-exported JSON, not the live API)
cd frontend/webserver && npm install && npm run dev
```

The portal's Vite dev server defaults to `http://127.0.0.1:5173`; the live upload tool at
`http://127.0.0.1:8000/upload` expects the API at `http://127.0.0.1:8000`. See `Makefile` for the
one-command `make dev` / `make api` / `make web` equivalents.

Quick API checks:

```bash
curl http://127.0.0.1:8000/api/health
curl -X POST http://127.0.0.1:8000/api/run/target-card \
  -H "Content-Type: application/json" \
  -d '{"de_stats":"metadata/suppl_tables/DE_stats.suppl_table.csv","guide_kd":"metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv","library_metadata":"metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv","skip_benchmark":true}'
```

After a run returns `dataset_id`, reports are available at:

```bash
curl "http://127.0.0.1:8000/api/reports/{dataset_id}?fmt=json&top_n=50"
curl "http://127.0.0.1:8000/api/reports/{dataset_id}?fmt=html&top_n=50" -o target_report.html
```

Useful API endpoints:

- `GET /api/summary/{dataset_id}`: overview metrics, top candidates, watchlist, count tables.
- `GET /api/options/{dataset_id}`: filter options for conditions, pathway axes, clinical axes, and score-cap reasons.
- `GET /api/targets/{dataset_id}`: filtered target-condition table.
- `GET /api/targets/{dataset_id}/{target}`: all condition rows for one target.
- `GET /api/modules/{dataset_id}`: seed-module hits.
- `GET /api/reports/{dataset_id}`: JSON, HTML, or Markdown evidence report.

Dashboard views:

- `Overview`: dataset metrics, evidence-grade charts, top candidates, watchlist.
- `Target Explorer`: filterable target-condition ranking and target detail page.
- `Pathway + Clinical`: module hits and clinical-axis summaries.
- `Export`: CSV plus JSON/HTML/Markdown report downloads.
