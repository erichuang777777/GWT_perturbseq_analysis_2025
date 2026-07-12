"""Pure interpretation of an already-loaded overlay table (architecture refactor Phase 3).

Moved here from ``evidence/safety_overlay.py`` (see
``docs/architecture_refactor_plan.md`` §4.3⑤, "關鍵解耦"): these functions
take an already-loaded overlay dict (produced by one of
``evidence.safety_overlay``'s ``load_*`` functions, e.g.
``load_gtex_safety_overlay()``) plus a gene id, and look up/interpret a
value. They perform no I/O, no network call, and cannot raise or fail --
the *loading* of the overlay (fragile: reads a file that may be missing or
malformed) stays in ``evidence/safety_overlay.py``, but the *interpretation*
of an already-loaded table is a pure function exactly like everything else
in ``common/``, and having it live here (rather than in ``evidence/``) is
what lets ``core/readiness.py`` interpret an injected overlay without
importing the evidence layer at all -- satisfying the "core has zero
fragile/evidence dependencies" acceptance criterion while producing
byte-identical results (this is the same code, only relocated).

``evidence/safety_overlay.py`` re-exports these under their original names
so existing callers (``tests/test_safety_overlay.py``,
``from safety_overlay import tractability_from_membrane_overlay`` etc.) are
unaffected.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

import pandas as pd

UNKNOWN = "unknown"

# Same modality vocabulary as core.cards.DRUGGABLE_CLASS_MODALITY, so this
# overlay's output is a drop-in for core.readiness's local-overlay
# tractability fallback's return shape (modality, score).
MODALITY_ANTIBODY_SURFACE = "antibody (surface)"
MODALITY_ANTIBODY_BIOLOGIC = "antibody / biologic"
MODALITY_SMALL_MOLECULE = "small molecule"

# gnomAD v4's "constrained" cutoff: a gene with LOEUF below this bar is flagged
# loss-of-function intolerant. Set to 0.6 to match gnomAD v4's current
# constrained threshold, consistent with the v4 LOEUF/pLI values now in the
# seed overlay -- broader than the gnomAD v2.1.1-era 0.35 this originally used
# (per ENHANCEMENT_連結器加強建議.md §2), so more genes in the constrained band
# are flagged. This is the ONLY threshold used by gnomad_flag_from_constraint;
# it does not vary by gene.
LOEUF_LOSS_INTOLERANT_THRESHOLD = 0.6

# Off-context GTEx breadth (``safety_window_from_gtex``'s count) at or above
# this bar counts as "broad" (low tissue specificity) for the composite
# liability view below. 26 is the real median of the committed ~9,718-gene GTEx
# overlay (max off-context breadth in that panel is 28), so this is a coarse,
# data-derived top-half split, disclosed as such -- not a biological absolute.
BREADTH_BROAD_THRESHOLD = 26


def composite_safety_liability(gnomad_flag: Any, safety_window: Any) -> str:
    """Compose gnomAD constraint + GTEx off-context breadth into ONE disclosed
    on-target safety-**liability** tier: ``high`` / ``moderate`` / ``low`` /
    ``"unknown"``.

    CRITICAL framing (get this right or it is wrong): human genetic constraint
    predicts on-target safety LIABILITIES, not de-risking. So this is a LIABILITY
    FLAG -- higher genetic constraint (loss-intolerant) PLUS broader off-context
    expression (low tissue specificity) = MORE concern, never a "this target is
    safe" signal (Duffy et al., *Sci Adv* 2020,
    https://www.science.org/doi/10.1126/sciadv.abb6242; Nat Rev Genet 2025,
    https://www.nature.com/articles/s41576-025-00904-4 -- safety-failed targets
    skew toward low tissue specificity + high constraint).

    Inputs are the two existing real, descriptive overlay signals (never
    re-derived here, so there is one implementation each):
      * ``gnomad_flag`` -- ``gnomad_flag_from_constraint`` output
        (``"loss_intolerant"`` / ``"none"`` / ``"unknown"``).
      * ``safety_window`` -- ``safety_window_from_gtex`` output (int off-context
        tissue count, or ``"unknown"``).

    Availability propagation (``unknown != 0``): if EITHER component is
    ``"unknown"`` (gene absent from that overlay, unchecked), the composite is
    ``"unknown"`` -- it never silently treats an unmeasured component as
    "no risk". The two component columns remain independently visible in the
    readiness output, so a reader always sees which half was missing.

    Tiering when both are available:
      * ``high``     -- loss-intolerant AND broadly expressed (both risk signals).
      * ``moderate`` -- exactly one of the two risk signals.
      * ``low``      -- neither (constraint ``"none"`` AND narrow off-context breadth).

    Purely descriptive: this is never read by ``core/readiness._stage()`` /
    ``_red_flags()`` and cannot move ``readiness_call``/
    ``overall_readiness_stage``.
    """
    if gnomad_flag == UNKNOWN or safety_window == UNKNOWN:
        return UNKNOWN
    try:
        breadth_risk = int(safety_window) >= BREADTH_BROAD_THRESHOLD
    except (TypeError, ValueError):
        return UNKNOWN
    constraint_risk = gnomad_flag == "loss_intolerant"
    n_risks = int(constraint_risk) + int(breadth_risk)
    return {2: "high", 1: "moderate", 0: "low"}[n_risks]


def tractability_from_membrane_overlay(gene_ensembl: str, overlay: Dict[str, Any]) -> Tuple[str, Any]:
    """(modality, score) from the real membrane/tractability overlay, else ``(unknown, unknown)``.

    Mirrors core.readiness's local-overlay ``_tractability``'s three-state
    contract: gene absent from the overlay -> unknown (not checked, not
    "undruggable"); gene present but no membrane/druggability signal ->
    ("none", 0); gene present with a signal -> a real modality + score 3.
    """
    if not overlay.get("available") or not gene_ensembl:
        return UNKNOWN, UNKNOWN
    table = overlay["table"]
    row = table[table["ensembl_id"] == gene_ensembl]
    if row.empty:
        return UNKNOWN, UNKNOWN
    r = row.iloc[0]
    is_surface = bool(r["is_surface_protein"])
    has_extracellular = bool(r["has_extracellular_domain"])
    has_transmembrane = bool(r["has_transmembrane_domain"])
    is_druggable = bool(r["is_druggable"])

    if is_surface and has_extracellular:
        return MODALITY_ANTIBODY_SURFACE, 3
    if is_surface or has_transmembrane:
        return MODALITY_ANTIBODY_BIOLOGIC, 3
    if is_druggable:
        return MODALITY_SMALL_MOLECULE, 3
    return "none", 0


def safety_window_from_gtex(gene_ensembl: str, overlay: Dict[str, Any]) -> Any:
    """Count of off-context GTEx tissues (Blood/Spleen excluded) where this
    gene clears the expression threshold, else ``unknown``. Keyed by Ensembl
    gene ID, same convention as ``tractability_from_membrane_overlay``.

    Higher = more broadly expressed across normal, non-CD4-context tissues =
    plausibly a narrower safety window for systemic inhibition; lower =
    narrower off-context expression = plausibly wider. This module does not
    collapse that into a categorical tier (tight/moderate/wide) -- the raw
    count is returned so the interpretation stays visible and revisable, not
    baked into a lossy label; ``core/readiness.py`` currently surfaces it
    as-is, not as a red-flag trigger (soft signal, not a cap).

    Coverage is ~9,718 genes; a gene absent from the overlay is unchecked,
    not "safe" -- returns ``unknown``, never `0`.
    """
    if not overlay.get("available") or not gene_ensembl:
        return UNKNOWN
    table = overlay["table"]
    row = table[table["ensembl_id"] == gene_ensembl]
    if row.empty:
        return UNKNOWN
    return int(row.iloc[0]["n_tissues_expressed"])


def singlecell_breadth_from_hpa(gene_ensembl: str, overlay: Dict[str, Any]) -> Any:
    """Count of off-context HPA single-cell types (T-cells excluded) where this
    gene clears the expression threshold, else ``unknown``. Keyed by Ensembl
    gene ID, same convention as ``safety_window_from_gtex``.

    This is a standalone, ADDITIONAL descriptive signal alongside
    ``safety_window_from_gtex`` -- single-CELL-TYPE resolution (51 HPA
    consensus categories) rather than bulk-TISSUE resolution, a materially
    finer-grained off-target signal for an immunology platform (a tissue can
    look narrow in bulk while containing several off-target immune cell
    populations only single-cell resolution resolves). It is deliberately
    NOT folded into ``composite_safety_liability`` -- that composite is
    already calibrated/tested on the two-way gnomAD+GTEx signal, and adding a
    third correlated breadth axis without re-deriving the tier thresholds
    would silently shift every gene's tier. Surface this column alongside the
    composite, not inside it.

    Coverage is ~20,162 genes (built from
    ``data_acquisition/build_hpa_singlecell_breadth_overlay.py``); a gene
    absent from the overlay is unchecked, not "safe" -- returns ``unknown``,
    never `0`.
    """
    if not overlay.get("available") or not gene_ensembl:
        return UNKNOWN
    table = overlay["table"]
    row = table[table["ensembl_id"] == gene_ensembl]
    if row.empty:
        return UNKNOWN
    return int(row.iloc[0]["n_celltypes_expressed"])


def gnomad_flag_from_constraint(gene_ensembl: str, overlay: Dict[str, Any]) -> str:
    """Soft LoF-constraint flag from gnomAD LOEUF, keyed by Ensembl gene ID.

    Returns ``"loss_intolerant"`` if LOEUF < ``LOEUF_LOSS_INTOLERANT_THRESHOLD``
    (0.35, per the connector recommendation doc's conservative rule);
    ``"none"`` if the gene is in the overlay but does not meet that bar;
    ``"unknown"`` if the overlay is unavailable or the gene is absent
    (unchecked, not "safe" -- same ``unknown != 0`` contract as
    ``safety_window_from_gtex``/``tractability_from_membrane_overlay``).

    This is a purely descriptive annotation: LoF intolerance in the human
    population is not the same claim as pharmacological (small-molecule /
    antibody) intolerance to inhibition, so this flag must never cap
    ``readiness_call``/``overall_readiness_stage`` -- ``core/readiness.py``
    surfaces it alongside, not inside, ``_stage()``.
    """
    if not overlay.get("available") or not gene_ensembl:
        return UNKNOWN
    table = overlay["table"]
    row = table[table["ensembl_id"] == gene_ensembl]
    if row.empty:
        return UNKNOWN
    loeuf = row.iloc[0]["loeuf"]
    if pd.isna(loeuf):
        return UNKNOWN
    return "loss_intolerant" if float(loeuf) < LOEUF_LOSS_INTOLERANT_THRESHOLD else "none"
