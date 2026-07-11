# Data licensing & redistribution terms

This document consolidates the licensing status of every data source this toolkit
uses, and records the **release-gate resolution of OF-1 and OF-3**
(`docs/human_validation_protocol.md` §9). It complements — and does not replace —
the per-source table in [`docs/data_governance_checklist.md`](docs/data_governance_checklist.md) §1.

## Code

The toolkit implementation (`src/`, `scripts/`, `frontend/`, `docs/`) is licensed
**MIT** — see [`LICENSE`](LICENSE). Freely reusable.

## Upstream GWT Perturb-seq dataset — OF-3 resolution

- **What it is:** the Marson-lab genome-scale CD4 T-cell CRISPRi Perturb-seq
  screen, bioRxiv **`10.64898/2025.12.23.696273v1`**
  (`dataset_version = gwt_marson2025/bioRxiv-10.64898-2025.12.23.696273v1`), read
  locally from `metadata/suppl_tables/*.csv` and the derived pipeline stages.
- **License / terms:** **not stated** in the upstream distribution — the source's
  own `data_sharing_readme.md` documents *schema*, not *reuse terms*.
- **Resolution (waiver for this release):** this toolkit ships as a
  **research / hypothesis-generating tool that only reads the data locally and
  never re-publishes the raw GWT tables** outside this repository. Under that
  constraint the "license not stated" gap is **not a blocker for the tool's
  release**. It **remains a blocker for any external redistribution of the raw
  data or for publication use** — those require confirming the dataset's own
  license / DUA with the source authors first. This constraint is surfaced in the
  UI's research-use-only banner and in `docs/data_governance_checklist.md` §1.

## Derived / overlay sources

Public, aggregate, or gene-level-membership sources used as lookups (not
redistributed wholesale): Open Targets export, gnomAD LOEUF/pLI constraint,
Backman et al. 2021 UK Biobank LoF-burden (population-level), Hart essentiality,
ClinVar membership, HPA/UniProt/CSPA-derived tractability. Each carries its own
public-data terms (see governance checklist §1); re-confirm before any external
redistribution of a specific derived export.

## Live connectors

ClinicalTrials.gov, PubMed/E-utilities, Open Targets GraphQL are fetched only in
an offline batch job (never in the request path) and TTL-cached, respecting
NLM/NCBI usage policies and Open Targets API terms.

---
_Release-freeze artifact. OF-1 (schema drift) and OF-3 (data license) resolutions
are tracked in `docs/human_validation_protocol.md` §9._
