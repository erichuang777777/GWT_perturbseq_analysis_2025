## Preparing for DE analysis

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

Merge pseudobulks for each sample
```bash
for SAMPLE_ID in CD4i_R2_D4_Stim8hr_CD4i_R2_Ultima; do
    sbatch \
        --partition=pritch \
        --job-name=pbulk_merge_${s} \
        --output=$GROUP_SCRATCH/emma/slurm-pbulk_%j.out \
        --error=$GROUP_SCRATCH/emma/slurm-pbulk_%j.err \
        --nodes=1 \
        --ntasks=1 \
        --cpus-per-task=1 \
        --mem=20G \
        --time=0:30:00 \
        --wrap="python make_pseudobulk.py merge $SAMPLE_ID"
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

## Analysing DE results

- `DE_results_analysis_full.ipynb` - exploratory analysis of DE results 
- `FACS_comparison_full.ipynb` - comparison of DE results with FACS screens from Marson Lab

## Output files 

-  `{experiment_name}_merged.DE_pseudobulk.h5ad` - Pseudobulked data object (sum of counts across donor-condition-guide)
- `{datadir}/DE_results_{run_name}/{experiment_name}.merged_DE_results.h5ad` - DE analysis statistics for each perturbation and condition
- `{datadir}/DE_results_{run_name}/DE_summary_stats_per_target.csv` - Summary of on-target effects and overall effect for each perturbation and condition

## Target card API + dashboard (optional dev flow)

Use these commands from repo root:

```bash
conda activate gwt-env
python -m pip install fastapi uvicorn pyarrow  # pyarrow: reads the §1.12 overlay .parquet snapshots

# run API
uvicorn target_card_api:app --app-dir src/3_DE_analysis --reload --port 8000

# open another terminal and run the dashboard (now an independent frontend package,
# see frontend/README.md — it talks to the API above purely over HTTP)
pip install -r frontend/dashboard/requirements.txt
streamlit run frontend/dashboard/target_card_dashboard.py
```

The dashboard expects API at `http://127.0.0.1:8000`.

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

Interpret the report and dashboard top-candidate tables as discovery triage. Raw statistical evidence
grades and `n_total_de_genes` are signal-breadth indicators, not stand-alone biological conclusions;
for robust interpretation, prioritize rows passing `replicate_pass_flag` and available donor/guide
consistency checks. For a robustness-first shortlist that filters before ranking, cross-link from the
summary/report flow to `GET /api/robust_ranked/{dataset_id}` or the dashboard's **整合 Triage →
Robust-ranked short-list** panel.

Useful API endpoints:

- `GET /api/summary/{dataset_id}`: overview metrics, top candidates, watchlist, count tables.
- `GET /api/options/{dataset_id}`: filter options for conditions, pathway axes, clinical axes, and score-cap reasons.
- `GET /api/targets/{dataset_id}`: filtered target-condition table.
- `GET /api/targets/{dataset_id}/{target}`: all condition rows for one target.
- `GET /api/modules/{dataset_id}`: seed-module hits.
- `GET /api/reports/{dataset_id}`: JSON, HTML, or Markdown evidence report.
- `GET /api/robust_ranked/{dataset_id}`: robustness-first filter-then-rank shortlist for high-confidence interpretation.

Dashboard views:

- `Overview`: dataset metrics, evidence-grade charts, top candidates, watchlist; use top candidates as discovery signals, not final confidence calls.
- `Target Explorer`: filterable target-condition ranking and target detail page.
- `Pathway + Clinical`: module hits and clinical-axis summaries.
- `Export`: CSV plus JSON/HTML/Markdown report downloads with top-candidate caution text; pair exports with the robust-ranked endpoint/view for high-confidence interpretation.
