"""Genetic double-support endpoint (follow-up direction E).

Read-only *composition* of two existing evidence modules -- it does not
reimplement either of them:

  * ``evidence/disease.py``    -- local Open Targets genetic-association export
    (``src/6_functional_interaction/results/disease_gene_associations_detailed.csv``).
  * ``evidence/population.py`` -- UK Biobank rare-LoF-burden effect estimates.

A target has "genetic double support" when it is BOTH (a) a disease-associated
top target (per-target max ``statistical_evidence_grade`` >= ``min_grade``) for
one of the local immune indications, AND (b) carries a population LoF-burden
hypothesis whose 95% CI excludes zero for the requested trait.

Discipline (identical to the modules it composes):
  * ``unknown != 0`` -- a target supported on only ONE side is NOT reported as
    double-support (it is simply absent), never coerced to a zero/pass.
  * descriptive-vs-decision separation -- nothing here feeds ``readiness_call``
    / ``overall_readiness_stage`` / ``statistical_evidence_grade``; this is a
    pure descriptive annotation.
  * honest-fallback -- an empty disease table (e.g. a bogus/missing path) or an
    unavailable population burden table yields ``available: False`` with an
    explicit reason, never a fabricated list.
  * provenance / population caveat -- every returned row carries the population
    module's ``CAVEAT_TEXT`` verbatim (group-level statistical association, not a
    patient-level prediction), and the disease side is ``genetic_association``
    (GWAS-level, not experimental causation).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from evidence.disease import load_disease_associations
from evidence.population import (
    CAVEAT_TEXT,
    build_population_hypothesis_card,
    load_burden_estimates,
)

# Repo root resolved from this file's location (this file lives at
# src/3_DE_analysis/genetic_double_support.py -> parents[2] is the repo root),
# mirroring how ``api/deps.ROOT`` anchors its paths. The disease module's own
# ``DEFAULT_ASSOCIATIONS_PATH`` is *cwd-relative* -- a footgun that silently
# loads an empty table (and thus ``available: False``) when run from any other
# directory. We therefore resolve and pass the anchored canonical path here.
REPO_ROOT = Path(__file__).resolve().parents[2]
DISEASE_ASSOCIATIONS_PATH = (
    REPO_ROOT
    / "src"
    / "6_functional_interaction"
    / "results"
    / "disease_gene_associations_detailed.csv"
)

# The local association export mixes 12 *specific* immune indications with one
# generic EFO umbrella term ("autoimmune disease") -- documented as "a general
# 'autoimmune disease' bucket" in docs/IMPLEMENTATION_PLAN.md. ``n_diseases``
# counts specific indications, so the umbrella bucket is excluded from the
# breadth count / disease list / max-association (it is a parent term, not an
# indication). This reproduces the exploration-verified breadth (SH2B3 = 12,
# PTPN22 = 11, IL23R = 9 of the 12 specific indications).
GENERIC_UMBRELLA_DISEASES = frozenset({"autoimmune disease"})


def _empty_result(available: bool, reason: Optional[str], trait: str) -> Dict[str, Any]:
    return {
        "available": available,
        "reason": reason,
        "trait": trait,
        "n_double_support": 0,
        "targets": [],
        "caveat": CAVEAT_TEXT,
    }


def double_support(
    cards_df: pd.DataFrame,
    associations_path: Optional[Path] = None,
    burden: Optional[Dict[str, Any]] = None,
    min_grade: int = 2,
    trait: str = "lymphocyte_count",
) -> Dict[str, Any]:
    """Intersect disease genetic-association support with population LoF-burden.

    ``associations_path`` defaults to the anchored canonical export; pass an
    explicit path to override (a nonexistent path exercises the honest-fallback
    branch). ``burden`` may be a pre-loaded ``load_burden_estimates`` result to
    inject; when ``None`` it is loaded for ``trait``.

    Returns ``{available, reason, trait, n_double_support, targets, caveat}``.
    Each target record is
    ``{target, n_diseases, diseases, max_assoc, population_effect_estimate,
    ci: [lower_95, upper_95], direction, caveat}``, sorted by
    ``(n_diseases, max_assoc)`` descending.
    """
    resolved_path = Path(associations_path) if associations_path is not None else DISEASE_ASSOCIATIONS_PATH
    associations = load_disease_associations(resolved_path)
    if associations.empty:
        # Honest-fallback: missing/bogus disease table -> no fabricated support.
        return _empty_result(False, f"no disease-association table available at {resolved_path}", trait)

    # --- Population side (load or use injected result) ---------------------
    if burden is None:
        burden = load_burden_estimates(trait)
    if not burden.get("available"):
        return _empty_result(False, burden.get("reason") or "population burden estimates unavailable", trait)
    estimates = burden.get("estimates")
    if estimates is None or estimates.empty:
        return _empty_result(False, "population burden estimates unavailable (empty table)", trait)

    # --- Disease side -----------------------------------------------------
    # Count only specific indications, excluding the generic EFO umbrella.
    specific = associations[~associations["disease_name"].str.lower().isin(GENERIC_UMBRELLA_DISEASES)]
    disease_symbols = set(specific["gene_symbol"])

    cards = cards_df.copy()
    # Associations symbols are already upper-cased on load; upper-case the
    # cards' join key to match (join key = gene symbol).
    cards["_target_upper"] = cards["target"].astype(str).str.strip().str.upper()
    cards["_grade"] = pd.to_numeric(cards.get("statistical_evidence_grade"), errors="coerce")
    # Dedup cards to per-target MAX statistical_evidence_grade.
    per_target_grade = cards.groupby("_target_upper")["_grade"].max()
    disease_targets = {
        sym
        for sym, grade in per_target_grade.items()
        if sym in disease_symbols and pd.notna(grade) and grade >= min_grade
    }

    disease_info: Dict[str, Dict[str, Any]] = {}
    if disease_targets:
        rel = specific[specific["gene_symbol"].isin(disease_targets)]
        for sym, sub in rel.groupby("gene_symbol"):
            disease_info[sym] = {
                "n_diseases": int(sub["disease_name"].nunique()),
                "diseases": sorted(sub["disease_name"].astype(str).unique().tolist()),
                "max_assoc": float(sub["association_score"].max()),
            }

    # --- Population hypothesis cards (CI excludes zero only) ---------------
    pop = build_population_hypothesis_card(cards_df, estimates, trait=trait)
    pop = pop[pop["ci_excludes_zero"] == True]  # noqa: E712 -- explicit boolean mask
    pop_info: Dict[str, Dict[str, Any]] = {}
    for _, row in pop.iterrows():
        sym = str(row["target"]).strip().upper()
        # First (highest per stable order) wins if a symbol maps to >1 target_id.
        pop_info.setdefault(
            sym,
            {
                "population_effect_estimate": float(row["population_effect_estimate"]),
                "lower_95": float(row["ci_95_lower"]),
                "upper_95": float(row["ci_95_upper"]),
                "direction": str(row["direction"]),
                "caveat": str(row["caveat"]),
            },
        )

    # --- Intersection (double support) ------------------------------------
    common = disease_targets & set(pop_info)
    records: List[Dict[str, Any]] = []
    for sym in common:
        di = disease_info[sym]
        pi = pop_info[sym]
        records.append(
            {
                "target": sym,
                "n_diseases": di["n_diseases"],
                "diseases": di["diseases"],
                "max_assoc": di["max_assoc"],
                "population_effect_estimate": pi["population_effect_estimate"],
                "ci": [pi["lower_95"], pi["upper_95"]],
                "direction": pi["direction"],
                "caveat": pi["caveat"],
            }
        )
    records.sort(key=lambda r: (r["n_diseases"], r["max_assoc"]), reverse=True)

    return {
        "available": True,
        "reason": None,
        "trait": trait,
        "n_double_support": len(records),
        "targets": records,
        "caveat": CAVEAT_TEXT,
    }
