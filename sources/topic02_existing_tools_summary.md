# Topic 2: Existing Tools for Perturb-seq and CD4 T Cell Drug-Discovery Workflows

Date: 2026-07-04

## Bottom Line

Existing tools can cover local analysis steps, but they do not yet provide a complete therapeutic target decision workflow.

The key opportunity is not to replace pertpy, Mixscape, SCEPTRE, Open Targets, or LINCS. The opportunity is to connect them into a target-centric, direction-aware, immune-context-aware hypothesis engine.

## Recommended MVP Stack

### CSV-First Modules

These can start from the current repository without downloading the 1.6 TiB cell-level dataset.

| Module | Tool / Platform | Use | Difficulty |
|---|---|---|---|
| Gene-level target ranking | scMAGeCK-lite or custom aggregation | target and guide ranking from DE / phenotype summaries | low-medium |
| Pathway / TF scoring | decoupleR + PROGENy + DoRothEA | convert DE signatures into pathway and TF activities | low |
| Target-disease evidence | Open Targets | disease links, genetics, drugs, tractability, safety | low |
| Safety / essentiality | DepMap | target liability, essentiality, cancer dependency context | low |
| Immune genetics context | DICE | immune-cell expression and eQTL context | low-medium |
| Drug signature export | LINCS / CMap / CLUE | query perturbation signatures against drug signatures | medium |
| Baseline cell context | CELLxGENE Census | target expression in CD4/immune/disease contexts | medium |
| Target cards | custom report layer | target-centered hypothesis memos | low-medium |

### h5ad-Dependent Modules

Add these once cell-level data are available.

| Module | Tool / Platform | Use | Difficulty |
|---|---|---|---|
| Perturbation association testing | SCEPTRE | calibrated perturbation-gene associations | medium |
| Perturbation QC | Mixscape / Mixscale | identify escaped / non-responding cells and perturbation strength | medium |
| Workflow framework | pertpy | AnnData-native perturbation pipeline | medium |
| CD4 program scoring | UCell / pyUCell | per-cell activation, Th17, Treg, exhaustion, cytokine program scores | low |
| Regulatory interpretation | SCENIC / AUCell | TF regulon activity and mechanistic interpretation | medium-high |

### Optional v2 Prediction Layer

Not recommended as MVP core:

- GEARS
- CPA
- scGen
- scGPT
- Geneformer
- CellOracle
- MUSIC
- GSFA
- Augur
- PerturBase

Reason: useful for prediction, latent biology, or external validation, but they add training, benchmarking, interpretation, or data-dependency overhead. They should be treated as hypothesis generators and validated against simpler baselines.

## What Existing Tools Cover

| Layer | Existing coverage | Main gap |
|---|---|---|
| QC / guide assignment | Scanpy, Seurat, Cell Ranger, pertpy, scMAGeCK | requires cell-level h5ad; not enough for therapeutic interpretation |
| Perturbation effect modeling | Mixscape, SCEPTRE, pertpy, scMAGeCK, MUSIC, GSFA | model output does not become drug-development rationale automatically |
| DE / pseudobulk | DESeq2, edgeR, limma, MAST, muscat, PyDESeq2 | aggregate CSV cannot recover all covariate models |
| Cell-state attribution | UCell, AUCell, CellTypist, SingleR, decoupleR | CD4 disease-relevant state ontology still needs curation |
| Network inference | SCENIC, CellOracle, arboreto, WGCNA, NicheNet | causal interpretation is fragile and usually needs cell-level data |
| Signature query | LINCS/CLUE, Enrichr, MSigDB, CREEDS, SigCom LINCS | signature matching does not decide target actionability |
| Target prioritization | Open Targets, ChEMBL, DGIdb, Pharos, DepMap, GTEx | missing directionality, immune context, safety integration |
| Dashboard/report | CELLxGENE, Vitessce, Streamlit, Dash, Shiny, Quarto | generic displays, not target hypothesis workflows |

## GWT-Specific Product Architecture

```text
Data Layer
├── GWT target-level DE CSV
├── supplementary metadata
├── sgRNA / target metadata
├── future full cell-level h5ad
└── external sources: Open Targets, LINCS, DepMap, CELLxGENE, DICE, ChEMBL

Analysis Layer
├── CSV-first
│   ├── signature registry
│   ├── DE summarization
│   ├── pathway / TF enrichment
│   ├── immune program scoring
│   ├── target ranking
│   └── drug signature export
└── h5ad-dependent
    ├── QC / guide assignment review
    ├── replicate-aware pseudobulk DE
    ├── perturbation response modeling
    ├── cell-state shift analysis
    ├── responder-cell detection
    └── state-specific network inference

Knowledge Layer
├── target -> perturbation effect
├── target -> disease genetics
├── target -> known drugs / modality
├── target -> expression and safety risk
├── target -> immune program
└── target -> therapeutic direction

Report / Dashboard Layer
├── ranked target table
├── target card
├── pathway / TF panels
├── immune context panel
├── druggability / known-drug panel
├── safety / genetics panel
└── HTML / CSV / JSON / target memo export
```

## Four-Week Prototype Roadmap

Week 1: data and baseline target effect layer
- Ingest DE, sgRNA, guide KD, metadata, and gene lists.
- Produce `target_summary.csv`: effect size, FDR, top DE genes, cells, guides, conditions.

Week 2: pathway and phenotype interpretation
- Add decoupleR / PROGENy / DoRothEA-style pathway and TF scoring.
- Add curated CD4 program scores from signatures where possible.

Week 3: therapeutic evidence aggregation
- Add Open Targets, DepMap, DICE, CELLxGENE annotation snapshots or API calls.
- Produce target cards with disease links, druggability, known drugs, safety flags, immune context.

Week 4: hypothesis report
- Rank targets by perturbation effect, disease relevance, immune desirability, druggability, and safety.
- Export `target_rankings.csv`, `target_cards.json`, and `hypothesis_report.html`.
- Add LINCS/CMap query export for robust signatures.

## Key Citations and Sources

- SCEPTRE: PMID `34930414`, DOI `10.1186/s13059-021-02545-2`
- scMAGeCK: PMID `31980032`, DOI `10.1186/s13059-020-1928-4`
- Mixscape immune checkpoint screen: PMID `33649593`, DOI `10.1038/s41588-021-00778-2`
- pertpy: DOI `10.1038/s41592-025-02909-7`
- MIMOSCA / Perturb-seq original: PMC `PMC5181115`
- GSFA: PMID `37770710`, DOI `10.1038/s41592-023-02017-4`
- decoupleR: PMID `36699385`, DOI `10.1093/bioadv/vbac016`
- UCell: PMID `34285779`
- SCENIC: PMC `PMC5937676`
- CellOracle: PMID `36755098`, DOI `10.1038/s41586-022-05688-9`
- Open Targets Platform: PMID `33196847`, DOI `10.1093/nar/gkaa1027`
- LINCS / CMap L1000: PMID `29195078`, DOI `10.1016/j.cell.2017.10.049`
- DepMap: PMID `39468210`
- CELLxGENE Discover / Census: DOI `10.1093/nar/gkae1142`
- DICE: PMID `30449622`

## Output Files

- `sources/topic02_tool_inventory.csv`
- `sources/topic02_pubmed_tools_round1.json`
- `sources/topic02_existing_tools_summary.md`

