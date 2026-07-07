# External Overlay Integration Concept — Safety (CellxGene) + Membrane/Tractability (TCGA/GTEx)

**Status:** concept only, not implemented — no real data files have been shared yet. This documents
*where* each proposed data source would plug into the existing engine and *what's still open*, so the
actual ingestion module can be written quickly once the real files/columns are available. Nothing here
should be built against fabricated/assumed columns.

**Why this matters:** two `readiness_engine.py` domains are today almost entirely `"unknown"`:

- `safety_window_score` — `0` if the gene is a known essential gene, else `"unknown"`. There is no real
  safety signal beyond "is it essential" today.
- `tractability_modality`/`tractability_score` — only populated from local druggable-class gene lists
  (kinase/GPCR/enzyme/surface/cytokine-R/NR overlays in `metadata/gene_lists/`); no expression-based or
  structural evidence feeds it.

The two datasets the project owner has (CellxGene-based gene safety validation; a membrane-protein
database with motif length / expression / TCGA+GTEx) are a direct match for exactly these two gaps.

---

## 1. Design principles (same as every other overlay already in this toolkit)

- **Additive only.** A gene absent from a new overlay keeps its current behavior exactly — no existing
  score changes for uncovered genes.
- **`unknown` stays `unknown`, never silently `0`.** Same rule as every other domain in
  `readiness_engine.py` (see `docs/data_governance_checklist.md` §3).
- **Offline/local, not a live call.** Load from a checked-in or cached snapshot file at process start or
  via a batch-refresh job — same cache-first pattern as `external_evidence_cache.py`, not a per-request
  API call.
- **Honest "not loaded" fallback.** Mirror `cre_schema.py`'s pattern exactly: `load_x(path=None) ->
  {"available": bool, "reason": ..., "table": df}` — reserve the schema now, load real data whenever
  it's supplied, never fabricate rows in between.
- **Versioned.** Any new score gets its own `fetched_at`/`source_version` stamp and bumps
  `CARD_SCHEMA_VERSION` once it's wired into `target_cards.csv` or the readiness frame, per
  `docs/cache_and_versioning_policy.md`.

---

## 2. Overlay A — gene safety validation (CellxGene-derived)

**Proposed minimal schema** (provisional — will change once the real export's actual columns are seen):

| Column | Meaning |
|---|---|
| `gene_id` or `gene_symbol` | Join key — needs to be resolved to Ensembl ID via B1's `GeneResolver` if the export uses symbols |
| `n_tissues_expressed` / `n_cell_types_expressed` | Expression breadth across CellxGene's tissue/cell-type atlas |
| `max_expression_outside_target_context` | Peak expression in any tissue/cell-type other than the ones relevant to this platform (CD4 T cells / immune contexts) |
| `validated_safe` (bool) or a graded `safety_tier` | Whatever verdict form the validation actually produced |
| `evidence_note`, `source_version` | Free-text + a version stamp for the CellxGene snapshot/query used |

**Where it plugs in:** a new `_safety_window(gene, safety_overlay, essential)` function in
`readiness_engine.py`, following the exact same contract as the existing `_tractability()`:
- gene not in overlay → `"unknown"` (current behavior, unchanged)
- gene in overlay + essential → still `0` (essentiality always wins, unchanged)
- gene in overlay, not essential, high off-context expression breadth → a low/capped score (possibly its
  own new red-flag override, `broad_tissue_expression`, similar in spirit to `broad_effect`)
- gene in overlay, not essential, narrow/validated-safe → a real positive score instead of `"unknown"`

**Open questions to resolve once the real file is shared:**
1. Identifier system — gene symbol vs Ensembl ID (this repo's canonical join key is Ensembl ID).
2. Does the export give a raw per-tissue expression matrix (breadth needs to be computed here) or an
   already-computed verdict/tier (just read a column)?
3. Partial coverage is fine — this only ever *adds* information for genes present in the overlay.

---

## 3. Overlay B — membrane protein database (motif length / expression / TCGA+GTEx)

This one file carries (at least) three distinct signals that map to different places:

### 3a. Surface/membrane annotation → `tractability_modality`
If the DB has a clean "this gene is a validated surface/membrane protein" flag, the lowest-effort
integration is to **not** write new code at all: drop a `surface_membrane_validated.tsv` (one gene
symbol per line) into `metadata/gene_lists/`, register it in `DRUGGABLE_CLASS_MODALITY`
(`build_target_cards.py`), and it flows through the existing `_tractability()`/`annotate_local_overlays()`
machinery unchanged. A finer-grained version (extracellular domain length, epitope accessibility) would
need a dedicated table instead of a flat gene-list file — worth deciding once you see how granular the
real data actually is.

### 3b. TCGA (tumor) vs GTEx (normal) expression → `safety_window_score`
GTEx normal-tissue expression breadth is exactly the same missing "off-tissue toxicity" signal as
Overlay A — these two data sources are complementary evidence for the *same* domain, not competing ones.
**TCGA is the one part of this DB that's a weaker fit for this specific platform**: TCGA tumor-vs-normal
overexpression is an ADC-target concept (find something overexpressed in tumor, absent in normal
tissue), but this toolkit's targets are CD4 T-cell/autoimmune biology, not oncology — there's no "tumor
context" here for a TCGA ratio to mean the same thing. Recommendation: keep the TCGA columns in the
ingested table (cheap, may matter later if this ever crosses into an oncology use case), but don't build
a TCGA-based score into the CD4 safety metric without checking with you first — flagging this explicitly
rather than quietly deciding it either way.

### 3c. `motif_length`
Lowest near-term value for *this* platform's current use case (immune-target readiness scoring, not
ADC linker/epitope design) — reserve the column (same as the CRE schema's empty-but-valid pattern),
don't build any scoring logic around it until there's a concrete use for it here.

---

## 4. Proposed file layout (once real files exist)

```
sources/target_tool_cache/_overlays/gene_safety_cellxgene.csv      # Overlay A, versioned snapshot
sources/target_tool_cache/_overlays/membrane_protein_db.csv        # Overlay B, versioned snapshot
src/3_DE_analysis/safety_overlay.py                                # new module, cre_schema.py-style loader
```

---

## 5. Sequencing once the real data is shared

1. Confirm identifier system + exact column names for both files — this is the actual blocker right
   now, not the logic above.
2. Build `safety_overlay.py` with the honest "not loaded" fallback contract (already proven in this repo
   via `cre_schema.py`).
3. Wire into `readiness_engine.py`'s `safety_window_score` and `_tractability()` — additive only, per §1.
4. Extend `docs/data_dictionary.md` (new columns) and `docs/data_governance_checklist.md` (source/license
   status — note whether either file is proprietary/internal vs. a public CellxGene/TCGA/GTEx export, and
   confirm neither carries patient-level identifiers if TCGA per-sample data is involved rather than
   gene-level summaries).
5. Add golden-file test fixtures (2-3 genes with known overlay values, one "narrow/safe," one
   "broad/off-tissue," one absent from the overlay) following the `tests/` pattern already in place.

Not scheduled/estimated yet — this is a concept to react to once the real files are in hand, not a
committed wave.
