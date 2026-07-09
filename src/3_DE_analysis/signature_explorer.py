"""A1a (signature-to-compound infrastructure, internally-validated half) + A4
(pairwise combination explorer), per ``docs/next_phases_plan.md`` §A1/§A4.

**What this answers (A1a):** "Does knocking down this target look, on a
shared transcriptional readout, like it moves the cell toward or away from a
known reference phenotype (Th2 polarization, CD4T aging)?" This is a
**hypothesis-generating connectivity clue**, never a treatment claim -- see
``CAVEAT_TEXT`` below, carried on every score this module returns, following
the same unconditional-caveat pattern as ``population_hypothesis.py``'s
``CAVEAT_TEXT``.

**What this answers (A4):** "If I looked at two targets' predicted directions
on the same shared readout, would combining them look reinforcing or
opposing?" This is **purely exploratory, no clinical claim** (plan doc:
"純研究探索,無臨床宣稱") -- see ``COMBINATION_CAVEAT_TEXT``.

**What this explicitly does NOT do:**
- A1b (matching against LINCS/CMap *compound* reference signatures) is now
  **wired but honestly unavailable**: ``match_reference_compounds`` routes to
  the compound-reversal ranking in ``evidence.lincs_reference_cache``
  (``load_compound_signatures`` + ``compound_reversal_matches``) whenever a
  committed COMPOUND signature matrix exists, and otherwise returns the honest
  ``source_status: unavailable`` shape. No compound matrix is committed (only
  genetic-knockdown signatures are), so today it always degrades to
  unavailable -- see its docstring and ``COMPOUND_SIGNATURES_PATH``.
- Never feeds ``readiness_call`` / ``overall_readiness_stage`` /
  ``statistical_evidence_grade``. Nothing here writes back into
  ``readiness_engine.py`` or ``target_card_api.py`` -- this module is fully
  standalone (imports only ``config.settings`` and ``common.degrade``,
  read-only).
- Never predicts real pharmacological synergy/antagonism (A4). The
  "additive / reinforcing / opposing" labels in ``explore_combination`` are a
  same-direction-or-not heuristic on a shared *transcriptional* readout, not
  a dose-response or clinical synergy model.

**A real data-availability finding this module is built around (please read
before extending it):** the plan doc's own framing lists "每個標的的 DE 方向
(``n_up_genes``/``n_down_genes``/``ontarget_effect_size``)" as the in-repo
query-signature substrate. On inspection, ``metadata/suppl_tables/
DE_stats.suppl_table.csv`` (33,983 rows -- confirmed exactly 3 rows per
target, one per ``culture_condition`` in {Rest, Stim8hr, Stim48hr}, 11,526
unique targets) carries only **per-target-per-condition aggregate** DE
statistics: ``ontarget_effect_size`` is the on-target gene's own signed
logFC-like effect (``build_target_cards.py`` literally assigns
``median_logFC = ontarget_effect_size``), and ``n_up_genes``/``n_down_genes``
are **unsigned counts with no gene identity attached** -- there is no
checked-in genome-wide, per-downstream-gene, per-target signed DE matrix
anywhere in this repo (no ``.h5ad``, no wide per-target pivot table; the
pivot machinery that *would* produce one lives in ``merge_DE_results.py``
but its output is not checked in, presumably because a full target x gene
matrix would be enormous). Fabricating per-gene identities to hit the
``n_up_genes``/``n_down_genes`` counts would violate this repo's
never-fabricate-data rule, so ``build_query_signature`` does not do that.

Instead, ``build_query_signature`` honestly builds what the real data
supports: a **single-gene query signature keyed by the target's own gene
symbol**, using its real, signed ``ontarget_effect_size`` (weighted across
culture conditions by ``ontarget_significant``). This is disclosed
explicitly in every returned dict via ``"scope": "on_target_gene_only"`` and
a ``"scope_note"`` field -- callers must not assume a genome-wide vector.
A direct, useful consequence: a target that is *itself* a strong marker gene
of a reference axis (e.g. GATA3 for Th2, TBX21 for Th1) gets a real,
interpretable connectivity score (see the internal validation in
``tests/test_signature_explorer.py``); a target whose functional role
is purely indirect/downstream is invisible to this proxy (a real limitation
of the current in-repo data, not of the algorithm). If a genome-wide
per-target DE matrix is added to the repo later, ``connectivity_score``
already operates on arbitrary-size ``{gene: score}`` dicts and needs no
changes.

**Algorithm choice: weighted cosine similarity, not weighted
Kolmogorov-Smirnov (KS).** The classic CMap/connectivity-map method (Lamb
et al. 2006, Science) is a weighted-KS running-sum enrichment statistic that
needs a large *ranked* gene list on both sides (it walks a rank ordering
built from hundreds-to-thousands of "up"/"down" tag genes) to be
well-defined and numerically stable. Given the single-gene-query reality
documented above, a KS statistic over a 1-gene query set would be a
degenerate/meaningless rank-walk. Cosine similarity, by contrast, is
well-defined for *any* nonzero overlap size (down to 1 shared gene -- where
it degenerates gracefully to a sign-concordance check, i.e. exactly +-1),
and is already magnitude-weighted (a gene contributes to the dot product in
proportion to how large its signed statistic is on both sides) without
extra machinery. ``connectivity_score`` reports ``n_shared_genes``
alongside every score so callers can see exactly how much (or little)
statistical weight backs a given number -- 1 shared gene is very low
confidence, and that is reported honestly, not hidden.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from config import settings
from common.degrade import unavailable_source

CAVEAT_TEXT = (
    "hypothesis-generating connectivity clue + a score -- NOT a claim that any "
    "compound, target knockdown, or perturbation 'works'. Per "
    "docs/next_phases_plan.md §A1: output is 「假設性化合物線索 + "
    "連結性分數」, not 「這個藥有效」 "
    "(hypothesis-generating compound clue + a connectivity score, not "
    "'this drug works'). Method: single-gene-proxy query signature (see "
    "module docstring) x weighted cosine similarity -- not a validated "
    "drug-response prediction."
)

COMBINATION_CAVEAT_TEXT = (
    "purely exploratory pairwise-signature heuristic on a shared reference "
    "readout -- NOT a pharmacological synergy/antagonism prediction and NOT "
    "a clinical claim. Per docs/next_phases_plan.md §A4: "
    "純研究探索，無臨床宣稱 (pure research "
    "exploration, no clinical claims)."
)

CONNECTIVITY_METHOD = "weighted_cosine_similarity"

# --- Reference signature loaders (real, in-repo; honest-fallback contract) ------

REFERENCE_SIGNATURE_PATHS: Dict[str, Path] = {
    "th2_vs_th1": settings.REPO_ROOT
    / "src"
    / "4_polarization_signatures"
    / "results"
    / "combined_Th2_vs_Th1_signature.csv",
    "cd4t_aging": settings.REPO_ROOT
    / "metadata"
    / "suppl_tables"
    / "CD4T_aging_signature_DE_results_full.suppl_table.csv",
}

# Gene-identifier column + per-name z-score aggregation rule. th2_vs_th1's
# combined file has three independent-cohort z-score columns (Hollbacher,
# Ota 2021, Diff043) -- all real, already-published per-cohort statistics --
# averaged per gene (skipping any NaNs) into one comparable score. cd4t_aging
# has a single cohort/contrast (Yaza2022 Discovery age_bin), one row per
# gene, used as-is.
_REFERENCE_GENE_COL = {"th2_vs_th1": "gene_name", "cd4t_aging": "gene_name"}
_REFERENCE_ZSCORE_COLS = {
    "th2_vs_th1": ["zscore_hollbacher", "zscore_ota", "zscore_Diff043"],
    "cd4t_aging": ["zscore"],
}


def load_reference_signature(name: str, path: Optional[Path] = None) -> Dict[str, Any]:
    """Load one of this repo's real, in-repo gene-level reference signatures.

    Returns ``{"available": bool, "reason": str|None, "name": name,
    "signature": {gene_symbol: signed_score}, "source_path": str|None}``.
    Never raises; an unrecognized ``name``, a missing file, or a file missing
    the expected columns all produce an explicit ``available: False`` with
    an empty signature -- never a fabricated or partially-guessed score.
    """
    resolved_path = path if path is not None else REFERENCE_SIGNATURE_PATHS.get(name)
    if resolved_path is None:
        return {
            "available": False,
            "reason": f"unrecognized reference signature '{name}'; known: {sorted(REFERENCE_SIGNATURE_PATHS)}",
            "name": name,
            "signature": {},
            "source_path": None,
        }
    resolved_path = Path(resolved_path)
    if not resolved_path.exists():
        return {
            "available": False,
            "reason": f"reference signature file not found: {resolved_path}",
            "name": name,
            "signature": {},
            "source_path": str(resolved_path),
        }
    df = pd.read_csv(resolved_path)
    gene_col = _REFERENCE_GENE_COL.get(name, "gene_name")
    zscore_cols = _REFERENCE_ZSCORE_COLS.get(name, ["zscore"])
    missing = [c for c in [gene_col] + zscore_cols if c not in df.columns]
    if missing:
        return {
            "available": False,
            "reason": f"reference signature file missing expected columns: {missing}",
            "name": name,
            "signature": {},
            "source_path": str(resolved_path),
        }
    df = df.dropna(subset=[gene_col]).drop_duplicates(subset=[gene_col])
    scores = df[zscore_cols].mean(axis=1, skipna=True)
    signature = dict(zip(df[gene_col].astype(str), scores.astype(float)))
    signature = {g: s for g, s in signature.items() if not np.isnan(s)}
    return {
        "available": True,
        "reason": None,
        "name": name,
        "signature": signature,
        "source_path": str(resolved_path),
    }


# --- A1a: query-signature construction from real in-repo Perturb-seq DE stats ---

REQUIRED_DE_STATS_COLUMNS = [
    "target_contrast_gene_name",
    "culture_condition",
    "ontarget_effect_size",
    "ontarget_significant",
]

# Non-significant conditions are down-weighted, not dropped -- a weak signal
# is still real signal, just less trustworthy than a significant one.
_SIGNIFICANT_WEIGHT = 1.0
_NONSIGNIFICANT_WEIGHT = 0.25


def build_query_signature(
    target: str,
    de_stats: pd.DataFrame,
    culture_conditions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build a query signature for ``target`` from real Perturb-seq DE stats.

    ``de_stats`` must be the ``DE_stats.suppl_table.csv``-shaped table (or an
    equivalent with the same columns) -- see the module docstring for why
    this returns a **single-gene, on-target-only** signature, not a
    genome-wide downstream vector. ``culture_conditions`` optionally
    restricts which of {Rest, Stim8hr, Stim48hr} rows are used (default:
    whatever is present for ``target``).

    Returns ``{"available": bool, "reason": str|None, "target": target,
    "signature": {target: signed_score}, "scope": "on_target_gene_only",
    "scope_note": str, "conditions_used": [...], "per_condition": [...]}``.
    A target absent from ``de_stats`` (or with no usable numeric effect
    size) produces an honest ``available: False`` -- never a fabricated
    score.
    """
    scope_note = (
        "this signature has exactly one gene (the target itself) because "
        "no genome-wide per-downstream-gene signed DE table is checked into "
        "this repo -- see signature_explorer.py module docstring"
    )
    missing_cols = [c for c in REQUIRED_DE_STATS_COLUMNS if c not in de_stats.columns]
    if missing_cols:
        return {
            "available": False,
            "reason": f"de_stats table missing required columns: {missing_cols}",
            "target": target,
            "signature": {},
            "scope": "on_target_gene_only",
            "scope_note": scope_note,
            "conditions_used": [],
            "per_condition": [],
        }

    rows = de_stats[de_stats["target_contrast_gene_name"] == target].copy()
    if culture_conditions is not None:
        rows = rows[rows["culture_condition"].isin(culture_conditions)]
    rows = rows.dropna(subset=["ontarget_effect_size"])
    if rows.empty:
        return {
            "available": False,
            "reason": f"target '{target}' not found in DE stats table (or has no numeric on-target effect size)",
            "target": target,
            "signature": {},
            "scope": "on_target_gene_only",
            "scope_note": scope_note,
            "conditions_used": [],
            "per_condition": [],
        }

    weights = np.where(rows["ontarget_significant"].fillna(False).astype(bool), _SIGNIFICANT_WEIGHT, _NONSIGNIFICANT_WEIGHT)
    effects = rows["ontarget_effect_size"].astype(float).to_numpy()
    aggregated_score = float(np.average(effects, weights=weights))

    per_condition = []
    for _, r in rows.iterrows():
        per_condition.append(
            {
                "culture_condition": r["culture_condition"],
                "ontarget_effect_size": float(r["ontarget_effect_size"]),
                "ontarget_significant": bool(r["ontarget_significant"]),
                "n_up_genes": r.get("n_up_genes"),
                "n_down_genes": r.get("n_down_genes"),
                "n_total_de_genes": r.get("n_total_de_genes"),
            }
        )

    return {
        "available": True,
        "reason": None,
        "target": target,
        "signature": {target: aggregated_score},
        "scope": "on_target_gene_only",
        "scope_note": scope_note,
        "conditions_used": sorted(rows["culture_condition"].unique().tolist()),
        "per_condition": per_condition,
    }


# --- Connectivity score: weighted cosine similarity over shared genes -----------


def connectivity_score(
    query_signature: Dict[str, float],
    reference_signature: Dict[str, float],
    min_shared_genes: int = 1,
) -> Dict[str, Any]:
    """Weighted cosine similarity between two ``{gene: signed_score}`` signatures.

    Score in ``[-1, 1]``: positive means the query and reference move
    together (same sign, weighted by magnitude) on the genes they share;
    negative means they move opposite (a "reversal-like" connectivity, the
    CMap-style signal of interest); values near 0 mean no shared directional
    signal. Only genes present in *both* signatures contribute -- this is
    honest by construction, never padded with assumed-zero scores for genes
    missing from one side.

    Returns ``{"available": bool, "reason": str|None, "score": float|None,
    "n_shared_genes": int, "shared_genes": [...], "method":
    "weighted_cosine_similarity", "interpretation": str|None, "caveat":
    CAVEAT_TEXT}``. ``available`` is ``False`` (never a fabricated score)
    when fewer than ``min_shared_genes`` genes overlap, or when either
    vector is all-zero over the shared genes (cosine undefined).
    """
    shared = sorted(set(query_signature) & set(reference_signature))
    n_shared = len(shared)
    if n_shared < max(1, min_shared_genes):
        return {
            "available": False,
            "reason": (
                f"only {n_shared} shared gene(s) between query and reference signature "
                f"(need >= {min_shared_genes}); connectivity score would be statistically "
                "meaningless / undefined"
            ),
            "score": None,
            "n_shared_genes": n_shared,
            "shared_genes": shared,
            "method": CONNECTIVITY_METHOD,
            "interpretation": None,
            "caveat": CAVEAT_TEXT,
        }

    q = np.array([query_signature[g] for g in shared], dtype=float)
    r = np.array([reference_signature[g] for g in shared], dtype=float)
    denom = float(np.linalg.norm(q) * np.linalg.norm(r))
    if denom == 0.0:
        return {
            "available": False,
            "reason": "zero-magnitude signature vector over the shared genes; cosine similarity undefined",
            "score": None,
            "n_shared_genes": n_shared,
            "shared_genes": shared,
            "method": CONNECTIVITY_METHOD,
            "interpretation": None,
            "caveat": CAVEAT_TEXT,
        }

    score = float(np.dot(q, r) / denom)
    if score > 1e-9:
        interpretation = "same-direction connectivity (query and reference move together on the shared genes)"
    elif score < -1e-9:
        interpretation = "reversal-like connectivity (query moves opposite to reference on the shared genes)"
    else:
        interpretation = "no directional signal (orthogonal on the shared genes)"

    return {
        "available": True,
        "reason": None,
        "score": score,
        "n_shared_genes": n_shared,
        "shared_genes": shared,
        "method": CONNECTIVITY_METHOD,
        "interpretation": interpretation,
        "caveat": CAVEAT_TEXT,
    }


def score_target_against_reference(
    target: str,
    de_stats: pd.DataFrame,
    reference_name: str = "th2_vs_th1",
) -> Dict[str, Any]:
    """Convenience: build ``target``'s query signature and score it against a
    named in-repo reference signature in one call. Composes
    ``build_query_signature`` + ``load_reference_signature`` +
    ``connectivity_score`` -- used by both the internal validation tests and
    ``explore_combination`` (A4) below.
    """
    query = build_query_signature(target, de_stats)
    if not query["available"]:
        return {
            "available": False,
            "reason": query["reason"],
            "target": target,
            "reference_name": reference_name,
            "query_signature": query,
            "connectivity": None,
        }
    reference = load_reference_signature(reference_name)
    if not reference["available"]:
        return {
            "available": False,
            "reason": reference["reason"],
            "target": target,
            "reference_name": reference_name,
            "query_signature": query,
            "connectivity": None,
        }
    connectivity = connectivity_score(query["signature"], reference["signature"])
    return {
        "available": connectivity["available"],
        "reason": connectivity.get("reason"),
        "target": target,
        "reference_name": reference_name,
        "query_signature": query,
        "connectivity": connectivity,
    }


# --- A1b: compound-reversal matching (routes to the compound half when data lands)


def match_reference_compounds(
    target: str,
    query_signature: Optional[Dict[str, float]] = None,
    compound_signatures: Any = None,
    top_n: int = 25,
    **kwargs: Any,
) -> Dict[str, Any]:
    """A1b: match ``target``'s signature against LINCS L1000 / CMap
    **compound** reference signatures to find compounds whose profile
    **reverses** the target's signature (drug-repurposing / signature-reversal).

    This now genuinely routes to the compound-reversal path in
    ``evidence.lincs_reference_cache`` (``load_compound_signatures`` +
    ``compound_reversal_matches``, which reuses the shared
    ``lincs_connectivity_score`` -- connectivity is never reimplemented here).
    But that path is **only** taken when a committed COMPOUND signature matrix
    exists. It does NOT today: the LINCS data that landed in the repo
    (``sources/target_tool_cache/_lincs/``) is genetic-PERTURBATION (shRNA
    knockdown) signal from GSE106127, NOT compound signal. Answering "which
    compound reverses this target's signature" needs COMPOUND reference
    signatures (LINCS GSE92742 / GSE70138 or CLUE), which are not committed and
    cannot be fetched in this sandbox (see ``COMPOUND_SIGNATURES_PATH`` and
    docs/sandbox_blocked_tasks.md §F). So per the honest-fallback contract this
    still returns the explicit ``{"source_status": "unavailable", ...}`` shape
    with a precise reason pointing at ``COMPOUND_SIGNATURES_PATH`` -- it never
    fabricates a compound match.

    Query substrate: a compound-reversal comparison needs a query in L1000
    978-landmark space. Callers may pass ``query_signature`` (a
    ``{landmark_gene: signed_score}`` vector) directly; otherwise this falls
    back to the target's own LINCS knockdown signature
    (``lincs_reference_cache.knockdown_reference``) as the landmark-space query
    -- i.e. "find compounds that reverse this gene's knockdown response". The
    single-gene, on-target-only in-repo query signatures produced by
    ``build_query_signature`` are NOT in landmark space and are deliberately
    not used here (that genetic-vs-compound distinction is preserved, not
    conflated).

    Note the separate, weaker capability already available for the 4 covered
    genes (PLCG1, SENP5, CCNC, PMVK): knockdown-vs-knockdown cross-referencing
    via ``knockdown_reference`` -- that is not compound matching and lives in
    the evidence layer, not this compound-specific entry point.
    """
    from evidence.lincs_reference_cache import (
        COMPOUND_CAVEAT_TEXT,
        COMPOUND_SIGNATURES_PATH,
        compound_reversal_matches,
        knockdown_reference,
        load_compound_signatures,
    )

    compounds = (
        compound_signatures
        if compound_signatures is not None
        else load_compound_signatures()
    )
    available = (
        (not compounds.empty)
        if isinstance(compounds, pd.DataFrame)
        else compounds.get("available", False)
    )
    if not available:
        reason = (
            compounds.get("reason") if isinstance(compounds, dict) else None
        ) or (
            f"compound reference signatures (LINCS GSE92742/GSE70138 or CLUE) not "
            f"present in this repo (expected at {COMPOUND_SIGNATURES_PATH}); the "
            "committed LINCS data is genetic-perturbation (knockdown) signal only "
            "-- see evidence.lincs_reference_cache."
        )
        return unavailable_source(reason=reason)

    # Compound data is present -> genuinely route to the reversal ranking.
    if query_signature is None:
        kd = knockdown_reference(target)
        if not kd["available"]:
            return unavailable_source(
                reason=(
                    f"compound matrix is available but no landmark-space query "
                    f"signature for '{target}': {kd['reason']}. Pass query_signature "
                    "explicitly (a {landmark_gene: signed_score} vector)."
                )
            )
        query_signature = kd["signature"]

    ranked = compound_reversal_matches(
        query_signature, compound_signatures=compounds, top_n=top_n
    )
    if not ranked["available"]:
        return unavailable_source(reason=ranked["reason"])

    return {
        "source_status": "available",
        "reason": None,
        "target": target,
        "method": ranked["method"],
        "items": ranked["matches"],
        "n_compounds_scored": ranked["n_compounds_scored"],
        "caveat": COMPOUND_CAVEAT_TEXT,
    }


# --- A4: pairwise combination explorer ------------------------------------------


def explore_combination(
    target_a: str,
    target_b: str,
    de_stats: pd.DataFrame,
    reference_signature: Optional[Dict[str, float]] = None,
    reference_name: str = "th2_vs_th1",
) -> Dict[str, Any]:
    """Explore whether two targets' predicted directions look reinforcing or
    opposing on a shared reference readout.

    Each target's real query signature (``build_query_signature``) is
    projected onto the same reference signature (default: the in-repo
    ``th2_vs_th1`` polarization signature; pass ``reference_signature``
    directly, or ``reference_name="cd4t_aging"``, to use a different shared
    readout) via ``connectivity_score``. This is a **same-direction-or-not
    heuristic**, not a real pharmacological additivity/synergy model -- see
    ``COMBINATION_CAVEAT_TEXT``, always present in the output.

    Note: ``target_a`` and ``target_b``'s own query signatures (each a
    single gene -- see module docstring) essentially never overlap with each
    other directly (they are different genes), so this function does not
    attempt a direct gene-overlap comparison between the two targets, which
    would be evaluated against zero shared genes for essentially every real
    pair. Instead it uses the shared reference signature as the common
    axis both targets are compared to -- this is the "some shared readout"
    approach the plan doc explicitly allows.

    Returns a dict with ``target_a``, ``target_b``, ``reference_name``,
    per-target ``connectivity`` results, ``interaction_pattern`` (one of
    ``"reinforcing_same_direction"``, ``"opposing_directions"``,
    ``"insufficient_data"``), and ``caveat`` (``COMBINATION_CAVEAT_TEXT``).
    Never raises on a missing/unknown target -- degrades to
    ``interaction_pattern: "insufficient_data"`` with a ``reason``.
    """
    if reference_signature is None:
        ref = load_reference_signature(reference_name)
        if not ref["available"]:
            return {
                "target_a": target_a,
                "target_b": target_b,
                "reference_name": reference_name,
                "interaction_pattern": "insufficient_data",
                "reason": f"reference signature unavailable: {ref['reason']}",
                "connectivity_a": None,
                "connectivity_b": None,
                "caveat": COMBINATION_CAVEAT_TEXT,
            }
        reference_signature = ref["signature"]

    query_a = build_query_signature(target_a, de_stats)
    query_b = build_query_signature(target_b, de_stats)

    if not query_a["available"] or not query_b["available"]:
        reasons = []
        if not query_a["available"]:
            reasons.append(f"{target_a}: {query_a['reason']}")
        if not query_b["available"]:
            reasons.append(f"{target_b}: {query_b['reason']}")
        return {
            "target_a": target_a,
            "target_b": target_b,
            "reference_name": reference_name,
            "interaction_pattern": "insufficient_data",
            "reason": "; ".join(reasons),
            "connectivity_a": None,
            "connectivity_b": None,
            "caveat": COMBINATION_CAVEAT_TEXT,
        }

    conn_a = connectivity_score(query_a["signature"], reference_signature)
    conn_b = connectivity_score(query_b["signature"], reference_signature)

    if not conn_a["available"] or not conn_b["available"]:
        reasons = []
        if not conn_a["available"]:
            reasons.append(f"{target_a}: {conn_a['reason']}")
        if not conn_b["available"]:
            reasons.append(f"{target_b}: {conn_b['reason']}")
        return {
            "target_a": target_a,
            "target_b": target_b,
            "reference_name": reference_name,
            "interaction_pattern": "insufficient_data",
            "reason": "; ".join(reasons),
            "connectivity_a": conn_a,
            "connectivity_b": conn_b,
            "caveat": COMBINATION_CAVEAT_TEXT,
        }

    score_a, score_b = conn_a["score"], conn_b["score"]
    combined_naive_sum = score_a + score_b
    if score_a * score_b > 1e-9:
        interaction_pattern = "reinforcing_same_direction"
    elif score_a * score_b < -1e-9:
        interaction_pattern = "opposing_directions"
    else:
        interaction_pattern = "negligible_or_ambiguous"

    return {
        "target_a": target_a,
        "target_b": target_b,
        "reference_name": reference_name,
        "connectivity_a": conn_a,
        "connectivity_b": conn_b,
        "combined_naive_sum": combined_naive_sum,
        "interaction_pattern": interaction_pattern,
        "reason": None,
        "caveat": COMBINATION_CAVEAT_TEXT,
    }
