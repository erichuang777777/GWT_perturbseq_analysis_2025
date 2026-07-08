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
HONEST COVERAGE LIMITS (verified 2026-07-08, not assumed) -- READ BEFORE USE:
=============================================================================
1. CELL-CONTEXT MISMATCH (the big one). All 15 GSE106127 cell lines are CANCER
   lines (A375, A549, MCF7, PC3, HEPG2, HT29, VCAP, HA1E, HCC515). ZERO
   T-cell / lymphoid lines. Our perturb-seq is primary human CD4+ T cells.
   Cross-context connectivity mapping is inherently biased -- treat any match as
   a weak hypothesis, never confirmation.
2. TARGET COVERAGE = 4/15. Genes WITH LINCS signatures:
   PLCG1 (24 sigs, IMMUNE candidate), SENP5 (24, broad-effect),
   CCNC (24, broad-effect), PMVK (9, broad-effect) -- all shRNA, cancer lines.
   Of the 5 immune candidates, only PLCG1 is covered; CD3E / LAT / CD247 / VAV1
   have ZERO LINCS signatures (not perturbed in cancer lines). So LINCS covers
   ONE top-ranked immune target (PLCG1 -- notable given its Angioedema safety
   flag) but cannot speak to the other four immune candidates at all.
3. LANDMARK SPACE. L1000 directly measures 978 landmark genes; the rest are
   inferred. None of our shortlist genes are landmarks -- their own knockdown is
   read out only in the inferred space. (Connectivity uses the 978-gene RESPONSE
   vector, so this does not block scoring, but lowers resolution vs full-tx.)

=> RECOMMENDATION: LINCS is a supporting, hypothesis-generating cross-reference
   for the 4 covered genes only (PLCG1 = immune; SENP5/CCNC/PMVK = broad-effect).
   The primary query signatures must
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

def lincs_connectivity_score(query: pd.Series, reference: pd.Series) -> float:
    """Spearman-based connectivity between a query DE signature (from Task A,
    restricted to shared landmark genes) and a LINCS reference signature.
    +1 = mimics, -1 = reverses. Shared-gene intersection only.

    NOTE: distinct from ``signature_explorer.connectivity_score`` (which is a
    magnitude-weighted *cosine* similarity over an arbitrary shared gene set,
    for comparing a single-gene query proxy against in-repo reference
    signatures). This one is Spearman rank correlation over the L1000 978-gene
    landmark response space specifically -- named ``lincs_`` to keep the two
    unambiguous. Returns NaN (never 0) when fewer than 20 landmark genes are
    shared, so a low-overlap comparison is honestly non-scored, not a fake 0.
    """
    shared = query.index.intersection(reference.index)
    if len(shared) < 20:
        return float("nan")
    from scipy.stats import spearmanr
    return float(spearmanr(query[shared], reference[shared]).correlation)


# --- Committed-data access (the real 4-gene demo signatures + coverage) ---------
#
# What actually landed in the repo is genetic-PERTURBATION (shRNA knockdown)
# reference signatures from GSE106127 for the 4 shortlist genes that had LINCS
# coverage -- NOT compound signatures. So these functions expose knockdown
# reference signatures for cross-referencing our own CD4 knockdown against
# LINCS's (cancer-line) knockdown of the same gene; they do NOT enable
# compound-reversal matching (that needs GSE92742/GSE70138 compound data,
# which is not committed -- see signature_explorer.match_reference_compounds).

_LINCS_DIR = Path(__file__).resolve().parents[3] / "sources" / "target_tool_cache" / "_lincs"
DEMO_SIGNATURES_PATH = _LINCS_DIR / "lincs_demo_signatures_4genes.csv"
COVERAGE_PATH = _LINCS_DIR / "lincs_shortlist_coverage.csv"

# --- COMPOUND half (LINCS L1000 compound-perturbation reversal) -----------------
#
# Parallel to DEMO_SIGNATURES_PATH (the genetic-knockdown half above), this is
# where a committed LINCS *compound* signature matrix would live. It is NOT
# present in this repo and this sandbox cannot fetch it (network-blocked -- see
# docs/sandbox_blocked_tasks.md §F): the real source is LINCS L1000 Phase 1/2
# (GSE92742 / GSE70138) or CLUE compound profiles. The functions below build
# the wiring + honest-fallback contract for when such a matrix lands, exactly
# like the genetic-knockdown half was built against its 4-gene seed. They never
# fabricate compound signatures.
COMPOUND_SIGNATURES_PATH = _LINCS_DIR / "lincs_compound_signatures.csv"

# The 4 shortlist genes with real committed LINCS knockdown signatures
# (verified against lincs_shortlist_coverage.csv, lincs_covered == "yes").
COVERED_GENES = ("SENP5", "PLCG1", "CCNC", "PMVK")

CAVEAT_TEXT = (
    "LINCS reference is genetic-perturbation (shRNA knockdown) signal from "
    "GSE106127 in CANCER cell lines; our platform is primary human CD4+ T "
    "cells. Cross-context connectivity is a weak hypothesis-generating "
    "cross-reference only, never confirmation, and covers 4 shortlist genes "
    "(PLCG1, SENP5, CCNC, PMVK). It does not substitute for the in-context "
    "per-target DE signature (Task A)."
)


def load_demo_signatures(path: Path | None = None) -> dict:
    """Load the committed 4-gene LINCS knockdown reference signatures.

    Returns ``{"available": bool, "reason": str|None, "table": DataFrame}``
    (index = 978 L1000 landmark gene symbols, columns = the covered genes).
    Honest-fallback: a missing file degrades to ``available: False`` with an
    empty table, never a fabricated matrix.
    """
    resolved = Path(path) if path is not None else DEMO_SIGNATURES_PATH
    if not resolved.exists():
        return {"available": False, "reason": f"LINCS demo signatures not found: {resolved}", "table": pd.DataFrame()}
    df = pd.read_csv(resolved, index_col=0)
    return {"available": True, "reason": None, "table": df}


def load_coverage(path: Path | None = None) -> dict:
    """Load the shortlist LINCS-coverage table (which shortlist genes have real
    LINCS signatures, how many, in how many cell lines). Honest-fallback."""
    resolved = Path(path) if path is not None else COVERAGE_PATH
    if not resolved.exists():
        return {"available": False, "reason": f"LINCS coverage table not found: {resolved}", "table": pd.DataFrame()}
    return {"available": True, "reason": None, "table": pd.read_csv(resolved)}


def knockdown_reference(gene: str, signatures: dict | None = None) -> dict:
    """Return the LINCS knockdown reference signature (978-landmark z-score
    vector) for one shortlist gene, or an honest unavailable result.

    ``{"available": bool, "reason": str|None, "gene": str,
    "signature": Series|None, "caveat": CAVEAT_TEXT}``. A gene without
    committed LINCS coverage (11 of the 15 shortlist genes) returns
    ``available: False`` -- unchecked/unavailable, never a fabricated vector.
    """
    gene_u = str(gene).strip().upper()
    sigs = signatures if signatures is not None else load_demo_signatures()
    if not sigs["available"]:
        return {"available": False, "reason": sigs["reason"], "gene": gene_u, "signature": None, "caveat": CAVEAT_TEXT}
    table = sigs["table"]
    if gene_u not in table.columns:
        return {
            "available": False,
            "reason": (
                f"{gene_u} has no committed LINCS knockdown signature "
                f"(covered genes: {', '.join(COVERED_GENES)})"
            ),
            "gene": gene_u,
            "signature": None,
            "caveat": CAVEAT_TEXT,
        }
    return {"available": True, "reason": None, "gene": gene_u, "signature": table[gene_u], "caveat": CAVEAT_TEXT}


# =============================================================================
# COMPOUND half: L1000 compound-perturbation reversal (P2.1 / roadmap ⑦)
# =============================================================================
#
# This is the compound analogue of the genetic-knockdown block above. It
# answers "which committed LINCS compound profile most REVERSES a query
# signature" -- the drug-repurposing / signature-reversal line. No compound
# matrix is committed (see COMPOUND_SIGNATURES_PATH note), so today every entry
# point here honestly degrades to available: False. The wiring, contract, and
# ranking logic are all in place for a future GSE92742 / GSE70138 / CLUE drop.

COMPOUND_CAVEAT_TEXT = (
    "REVERSAL is hypothesis-generating only, NEVER a treatment claim. TWO "
    "stacked uncertainties must be disclosed on every compound hit: (1) "
    "CELL-CONTEXT MISMATCH (OQ3) -- LINCS L1000 compound profiles "
    "(GSE92742/GSE70138/CLUE) are overwhelmingly cancer / immortalized cell "
    "lines, NOT primary human CD4+ T cells, so a reversal ranked here may not "
    "transfer to the CD4 context at all; (2) a negative connectivity score is "
    "a transcriptional-signature-reversal CLUE, not evidence a compound is "
    "safe, effective, or acts on the target. Use only to prioritize follow-up "
    "hypotheses, never as a therapeutic conclusion."
)

COMPOUND_METHOD = "lincs_spearman_connectivity_reversal"


def load_compound_signatures(path: Path | None = None) -> dict:
    """Load a LINCS L1000 **compound**-perturbation reference matrix.

    Expected on-disk shape (parallel to ``load_demo_signatures`` for the
    genetic half): a CSV whose first column is the 978 L1000 landmark gene
    symbols (index) and whose remaining columns are compound identifiers
    (``pert_iname`` / BRD id), each holding that compound's moderated
    z-score response over the 978 landmarks -- i.e. a ``978 x n_compounds``
    matrix.

    Returns ``{"available": bool, "reason": str|None, "table": DataFrame}``.
    Honest-fallback: the file is NOT committed in this repo (see
    ``COMPOUND_SIGNATURES_PATH``), so with no ``path`` override this returns
    ``available: False`` with an empty table and a reason pointing at the
    missing path -- never a fabricated compound matrix.
    """
    resolved = Path(path) if path is not None else COMPOUND_SIGNATURES_PATH
    if not resolved.exists():
        return {
            "available": False,
            "reason": (
                f"LINCS compound signature matrix not found: {resolved}. Compound "
                "profiles (LINCS L1000 GSE92742/GSE70138 or CLUE) are not committed "
                "to this repo and cannot be fetched in this sandbox "
                "(network-blocked; see docs/sandbox_blocked_tasks.md §F). The "
                "committed LINCS data is genetic-perturbation (knockdown) signal only."
            ),
            "table": pd.DataFrame(),
        }
    df = pd.read_csv(resolved, index_col=0)
    return {"available": True, "reason": None, "table": df}


def _as_query_series(query_signature) -> pd.Series:
    """Normalize a ``{landmark_gene: signed_score}`` dict (or a Series) to a
    Series, so ``lincs_connectivity_score`` (which indexes on gene labels) can
    consume it uniformly."""
    if isinstance(query_signature, pd.Series):
        return query_signature.astype(float)
    return pd.Series(dict(query_signature), dtype=float)


def compound_reversal_matches(
    query_signature,
    compound_signatures: dict | pd.DataFrame | None = None,
    top_n: int = 25,
) -> dict:
    """Rank committed LINCS compounds by how strongly they REVERSE a query.

    Given ``query_signature`` (a ``{landmark_gene: signed_score}`` vector, or a
    pandas Series -- e.g. an in-context CD4 knockdown signature restricted to
    L1000 landmarks) and a compound-signature matrix, score every compound with
    :func:`lincs_connectivity_score` (Spearman connectivity over shared
    landmark genes; +1 = mimics, -1 = reverses) and rank by MOST NEGATIVE score
    first -- the best reversal candidates. Connectivity is reused, never
    reimplemented.

    ``compound_signatures`` may be the dict returned by
    :func:`load_compound_signatures`, a raw ``978 x n_compounds`` DataFrame, or
    ``None`` (load the committed default). When no compound matrix is available
    -- the current repo state -- this returns an honest unavailable dict; it
    never fabricates a ranking.

    Returns ``{"available": bool, "reason": str|None, "method":
    COMPOUND_METHOD, "matches": [{"compound": str, "connectivity_score": float,
    "is_reversal": bool}, ...], "n_compounds_scored": int, "caveat":
    COMPOUND_CAVEAT_TEXT}``. ``matches`` is sorted most-reversing-first;
    compounds sharing too few landmarks to score (NaN connectivity) are
    dropped rather than assigned a fake 0.
    """
    # Normalize the compound-signature source into a DataFrame + availability.
    if compound_signatures is None:
        loaded = load_compound_signatures()
    elif isinstance(compound_signatures, pd.DataFrame):
        loaded = {"available": not compound_signatures.empty, "reason": None, "table": compound_signatures}
    else:
        loaded = compound_signatures

    if not loaded.get("available"):
        return {
            "available": False,
            "reason": loaded.get("reason", f"no compound signature matrix available (expected at {COMPOUND_SIGNATURES_PATH})"),
            "method": COMPOUND_METHOD,
            "matches": [],
            "n_compounds_scored": 0,
            "caveat": COMPOUND_CAVEAT_TEXT,
        }

    table = loaded["table"]
    query = _as_query_series(query_signature)

    scored = []
    for compound in table.columns:
        score = lincs_connectivity_score(query, table[compound])
        if score is None or np.isnan(score):
            continue
        scored.append(
            {
                "compound": str(compound),
                "connectivity_score": float(score),
                # A reversal is a NEGATIVE connectivity (query moves opposite to
                # the compound); a positive score is a mimic, i.e. NON-reversing.
                "is_reversal": bool(score < 0),
            }
        )

    if not scored:
        return {
            "available": False,
            "reason": (
                "no compound could be scored against the query signature "
                "(insufficient shared L1000 landmark genes for every compound; "
                "connectivity needs >= 20 shared landmarks)"
            ),
            "method": COMPOUND_METHOD,
            "matches": [],
            "n_compounds_scored": 0,
            "caveat": COMPOUND_CAVEAT_TEXT,
        }

    # Most-reversing (most negative connectivity) first.
    scored.sort(key=lambda d: d["connectivity_score"])
    return {
        "available": True,
        "reason": None,
        "method": COMPOUND_METHOD,
        "matches": scored[: max(1, int(top_n))],
        "n_compounds_scored": len(scored),
        "caveat": COMPOUND_CAVEAT_TEXT,
    }
