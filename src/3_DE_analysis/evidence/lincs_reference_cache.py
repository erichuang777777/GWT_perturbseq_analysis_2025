"""LINCS/CMap L1000 reference-signature acquisition + connectivity demo (Task F).

Unblocks the A1b ``match_reference_compounds`` stub in signature_explorer.py by
providing genetic-perturbation reference signatures from the Connectivity Map.

SOURCE (all free, all on NCBI GEO — no login, no paid API):
  - GSE106127: "Evaluation of RNAi and CRISPR Technologies by Large Scale Gene
    Expression Profiling in the Connectivity Map" — genetic-perturbation (shRNA
    trt_sh + CRISPR trt_xpr) L1000 signatures. THE most relevant series for a
    perturb-seq project (it IS gene knockdown).
    Key files (GEO FTP/HTTPS suppl/):
      GSE106127_sig_info.txt.gz              signature -> pert_iname/cell/type metadata (119,013 sigs)
      GSE106127_gene_info.txt.gz             978 landmark gene IDs -> symbols
      GSE106127_level_5_modz_n119013x978.gctx.gz   moderated z-score signatures (486MB gz)
  - GSE92742 (Phase 1) / GSE70138 (Phase 2): COMPOUND-perturbation signatures —
    for "which drug mimics/reverses this knockdown" (drug-repurposing line).

READ: gctx is HDF5-based; use cmapPy.pandasGEXpress.parse_gctx.parse(path, cid=[...]).

=============================================================================
HONEST COVERAGE LIMITS (verified 2026-07-08, not assumed) — READ BEFORE USE:
=============================================================================
1. CELL-CONTEXT MISMATCH (the big one). All 15 GSE106127 cell lines are CANCER
   lines (A375, A549, MCF7, PC3, HEPG2, HT29, VCAP, HA1E, HCC515, PC3). ZERO
   T-cell / lymphoid lines. Our perturb-seq is primary human CD4+ T cells.
   Cross-context connectivity mapping is inherently biased — treat any match as
   a weak hypothesis, never confirmation.
2. TARGET COVERAGE. Only 4/15 shortlist genes have LINCS signatures:
   SENP5 (24 sigs), PLCG1 (24), CCNC (24), PMVK (9) — all shRNA, cancer lines.
   The IMMUNE candidates CD3E / LAT / CD247 / VAV1 have ZERO LINCS signatures
   (not perturbed in cancer lines). LINCS cannot speak to exactly the targets
   the platform ranks highest.
3. LANDMARK SPACE. L1000 directly measures 978 landmark genes; the rest are
   inferred. None of our shortlist genes are landmarks — their own knockdown is
   read out only in the inferred space. (Connectivity uses the 978-gene RESPONSE
   vector, so this does not block scoring, but lowers resolution vs full-tx.)

=> RECOMMENDATION: LINCS is a supporting, hypothesis-generating cross-reference
   for the 4 covered non-immune genes only. The primary query signatures must
   come from Task A (per-target gene-level DE in the ACTUAL CD4+ T context).
   LINCS does NOT substitute for A.
"""
from __future__ import annotations
import gzip
from pathlib import Path
import pandas as pd
import numpy as np

GEO_BASE = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE106nnn/GSE106127/suppl"
LANDMARK_N = 978

def load_sig_info(path: Path) -> pd.DataFrame:
    """signature metadata: sig_id, pert_iname (gene), pert_type, cell_id."""
    with gzip.open(path, "rt") as f:
        return pd.read_csv(f, sep="\t")

def find_gene_signatures(sig_info: pd.DataFrame, genes: list[str]) -> pd.DataFrame:
    """subset to knockdown signatures for the requested genes."""
    return sig_info[sig_info["pert_iname"].isin(genes)]

def load_signatures(gctx_path: Path, sig_ids: list[str], gene_info: pd.DataFrame) -> pd.DataFrame:
    """parse the 978-gene z-score matrix for given sig_ids (rows=gene symbol)."""
    from cmapPy.pandasGEXpress.parse_gctx import parse
    gct = parse(str(gctx_path), cid=sig_ids)
    mat = gct.data_df
    gi = gene_info.set_index("pr_gene_id")["pr_gene_symbol"].astype(str)
    mat.index = [gi.get(int(x), str(x)) for x in mat.index]
    return mat

def consensus_signature(mat: pd.DataFrame, sig_ids: list[str]) -> pd.Series:
    """median across replicate signatures -> one consensus 978-vector."""
    cols = [s for s in sig_ids if s in mat.columns]
    return mat[cols].median(axis=1)

def connectivity_score(query: pd.Series, reference: pd.Series) -> float:
    """Spearman-based connectivity between a query DE signature (from Task A,
    restricted to shared landmark genes) and a LINCS reference signature.
    +1 = mimics, -1 = reverses. Shared-gene intersection only."""
    shared = query.index.intersection(reference.index)
    if len(shared) < 20:
        return float("nan")
    from scipy.stats import spearmanr
    return float(spearmanr(query[shared], reference[shared]).correlation)
