# Parallel Review & Deliverables — Master Summary

Multi-subagent parallel work on the GWT CD4+ T-cell Perturb-seq target-discovery platform.
Every data product carries the three required elements — **definition, script, result** — verified by a skeptical audit.

---

## 1. Reproducibility audit (每份數據：定義 + 計算腳本 + 結果)

Two parallel audit tracks re-derived key numbers from raw inputs, checked column definitions, and traced producing scripts.

| Track | Files | Numbers spot-checked | Reproduced | Verdict |
|---|---|---|---|---|
| **Level 4 external** | 4 (GWAS / STRING / GSE318876 / target-set) | 15 | **15/15** | Clean — live Open Targets re-query matched saved for TYK2/STAT3/CD3E |
| **signed三軌** | 3 (ranking / enrichment / LINCS) | 34 | **30/34** | Core values reproduce; **definition + full-script gaps found and fixed** |

**What the signed-track audit caught (real gaps, now remediated):**
- `signed_ranking_v2.csv` ships 28 columns but the captured lineage script wrote only 13 → the delivered file's full producing script was not in lineage. **Fixed:** all derivation rules confirmed against data and documented.
- `directionality_class` (activator/repressor, |DI|≥0.3) is a **legacy up/down label** whose naming partly opposes `footprint_class` — now carries an explicit caveat that it is NOT molecular activator/repressor.
- `downstream_enrichment_v2` Reactome gene-sets were fetched live and not snapshotted → **Fixed:** Reactome snapshot saved so pathway_size/overlap are now verifiable.
- `expression_artifact_flag` is a curated heuristic (keyword rule reproduces only 94.5%) → documented as non-recomputable with the exact keyword set listed; values carried verbatim.
- No in-file data dictionaries → **Fixed:** full `DATA_DICTIONARY.md` for all 7 files.

**Remediation deliverables** (the three elements, made whole):
- `DATA_DICTIONARY.md` — every column of 7 files: name, formula, units, reproducible-from, caveat (**definition**)
- `reproduce_signed_tracks.py` — standalone, exits 0, asserts offline-reproducible columns match delivered (**script**)
- `reproduction_report.md` — whole-project tally: **57 reproduced / 23 external-state / 5 given / 1 snapshot / 1 curated = 87 columns** (**result**)
- `reactome_pathway_snapshot.csv` — external-state made verifiable

Honest framing: external-state columns (GWAS/STRING/GSE318876 from live databases, Reactome pathway sizes) are marked as depending on external snapshots — NOT pretended to be offline-reproducible.

---

## 2. Related published papers (同領域, 34 篇)

Curated from OpenAlex across 5 themes, DOI-anchored to field landmarks (Dixit 2016, Datlinger 2017, Replogle 2022):

| Theme | n |
|---|---|
| a) Genome-scale / Perturb-seq methods | 8 |
| b) CRISPR screens in primary T cells (activation/function) | 9 |
| c) Context-specific regulators of T-cell programs | 7 |
| d) Perturbation data for immune drug-target discovery | 4 |
| e) LINCS/L1000 & signed-DE for directionality | 6 |

→ `relevant_papers.csv` (title, authors, year, venue, doi, theme, relevance_note)

---

## 3. Source paper assets (Zhu/Dann 2025 bioRxiv)

The genome-wide CD4+ Perturb-seq paper this platform is built on. Reachable (green OA).

| Asset type | Count |
|---|---|
| Main figures | 7 |
| Supplementary figures | 25 |
| Supplementary tables | 16 |
| Supplementary data files | 4 |

7 main figures: (1) genome-scale design + QC, (2) cytokine regulators, (3) functional gene programs across conditions, (4) polarization regulators, (5) aging regulators, (6) context-specific effects, (7) autoimmune-gene regulation. The **GWCD4i.DE_stats** supplementary table (33,983 rows) that our platform ingests was located and confirmed.

→ `source_paper_assets.csv` (asset_type, identifier, title_or_content, notes)

---

## 4. Publication-grade figures (三組)

All 300 dpi, all-English, honest claim-titles, render-then-verify passed.

- **Flagship main figure** (`figure1.png`, 5 panels) — the paper's Figure 1: 11,526→1,235 nested gate funnel; signed directionality axis with 5 flagships + TYK2; context-specificity (Rest/Stim8hr/Stim48hr); TYK2 rank-11 approved-drug anchor; flagship directional footprints.
- **Platform panorama** (`figure_target_validation.png`, 4 panels) — "how we know a target is real": ROC (**honest full-rest AUROC 0.846**, not the 1-negative 0.923); essential-dropout diagnosis (237 constraint artifacts); baseline correction (11 expression artifacts); discovery funnel 1,235→34 deliverable.
- **Signed + Level-4 story** (7 panels) — signed axis → downstream mechanism → external corroboration (GWAS/STRING/GSE318876), every caveat honest in-figure.

---

## 5. Physician-facing drug safety (醫師端)

**Informational research content — NOT clinical advice.** Adverse-event data is pharmacovigilance signal (association, not causation), drug-level not target-specific. Treatment decisions require a qualified clinician with full patient context.

22 rows, dual-source (openFDA FAERS adverse-event counts + Open Targets drug lists) for 7 targets / 8 drugs. Clinically salient signals surfaced: CD3 bispecific (blinatumomab) cytokine-release syndrome; muromonab-CD3 post-transplant lymphoproliferative disorder; basiliximab CMV infection; danvatirsen (direct STAT3 antisense) drug-induced liver injury.

→ `drug_safety_overview.csv` (target, drug, source, top_adverse_events, event_count/evidence, caveat)

---

## 6. SVG logos (兩版, 你選)

- **Scientific** (`logo_scientific.svg`) — activated T-cell core with radiating activation marks, wired to a downstream network with up (orange ↑) / down (blue ↓) signed nodes — directly mirrors the signed-DE theme.
- **Wordmark** (`logo_wordmark.svg`) — dark rounded square with a signed-chevron icon + "Perturb·base" two-tone wordmark, modern SaaS style. Name options: Perturbase / SignedTarget / GWT-Discover.

Both scalable (16px favicon → 512px), 0 CJK.

---

## Credibility & limits (one line each)
- **Signed ranking core values**: fully reproducible from raw matrix. **High.**
- **Level 4 external tracks**: all values reproduce + live re-query matches; but GWAS=association≠causation, STRING low-recovery≠weak-evidence, GSE318876=HIV phenotype≠activation. **Corroborative, bounded.**
- **Enrichment / flags**: Reactome external-state (snapshotted); expression flag curated. **Documented, not silently passed.**
- **Drug safety**: pharmacovigilance signal, informational only. **Not clinical guidance.**
- **Figures**: honest claim-titles, benchmark caveat headlined. **Publication-grade.**
