"""Module 3, part A: population subgroup hypothesis engine (demo scope).

**What this answers:** "If a population carries a loss-of-function (LoF) variant in
this gene, which de-identified population traits are known to shift, on average?"
This is a **population genetics statement**, not a patient-level prediction --
see the interface guardrail in ``build_population_hypothesis_card``'s output
(the ``caveat`` field, always present, never omitted).

**What this explicitly does NOT do** (scope boundary, not a TODO):
- No patient-level input is accepted anywhere in this module -- there is no
  function that takes an individual's genotype/phenotype.
- No dosing, drug, or treatment-path output. See ``match_disease_drug_evidence``
  in ``disease_translator.py`` for the separate (also non-prescriptive)
  evidence-matching function.
- No regression on individual outcomes -- this only looks up pre-computed,
  already-published, gene-level population burden estimates.

**Data source:** UK Biobank exome-wide rare-LoF-variant burden effect estimates
(Backman et al. 2021), already checked into this repo at
``src/8_lymphocyte_counts_LoF/input/*.tsv`` -- de-identified, population-level,
gene x trait estimates (posterior mean effect + 95% credible interval). This
module performs zero network calls; everything is a local file join.

Follows the honest-fallback contract already established in ``cre_schema.py``:
a missing/malformed input file produces an explicit ``available: False``
result, never a fabricated hypothesis card.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from config import settings

# trait -> local TSV file. Only "lymphocyte_count" has a resolved, documented
# phenotype name (matches the file's own name and the demo this module was
# built from). The second Backman file in this directory
# (Backman_2021_86_fullFeatures.per_gene_estimates.tsv) uses a bare UK
# Biobank field code ("86") with no phenotype label available in this repo's
# docs -- exposed under its raw code rather than guessing what it means, per
# the "never fabricate" rule.
TRAIT_PATHS: Dict[str, Path] = {
    "lymphocyte_count": settings.REPO_ROOT
    / "src"
    / "8_lymphocyte_counts_LoF"
    / "input"
    / "Backman_LymphocyteCount_fullFeatures.per_gene_estimates.tsv",
    "backman_2021_field86_unlabeled": settings.REPO_ROOT
    / "src"
    / "8_lymphocyte_counts_LoF"
    / "input"
    / "Backman_2021_86_fullFeatures.per_gene_estimates.tsv",
}

BURDEN_REQUIRED_COLUMNS = ["ensg", "post_mean", "lower_95", "upper_95"]

CAVEAT_TEXT = (
    "population-level statistical association, not a patient-level prediction "
    "or treatment recommendation"
)


def empty_burden_table() -> pd.DataFrame:
    return pd.DataFrame(columns=BURDEN_REQUIRED_COLUMNS)


def load_burden_estimates(trait: str = "lymphocyte_count", path: Optional[Path] = None) -> Dict[str, Any]:
    """Load UK Biobank LoF-burden estimates for ``trait``.

    Returns ``{"available": bool, "reason": str|None, "trait": str, "estimates": DataFrame}``.
    Never raises; a missing file, an unrecognized ``trait``, or a malformed
    file all produce an explicit ``available: False`` with an empty table --
    never a fabricated or partially-guessed estimate.
    """
    resolved_path = path if path is not None else TRAIT_PATHS.get(trait)
    if resolved_path is None:
        return {
            "available": False,
            "reason": f"unrecognized trait '{trait}'; known traits: {sorted(TRAIT_PATHS)}",
            "trait": trait,
            "estimates": empty_burden_table(),
        }
    resolved_path = Path(resolved_path)
    if not resolved_path.exists():
        return {
            "available": False,
            "reason": f"burden-estimate file not found: {resolved_path}",
            "trait": trait,
            "estimates": empty_burden_table(),
        }
    df = pd.read_csv(resolved_path, sep="\t")
    missing = [c for c in BURDEN_REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return {
            "available": False,
            "reason": f"burden file missing required columns: {missing}",
            "trait": trait,
            "estimates": empty_burden_table(),
        }
    return {"available": True, "reason": None, "trait": trait, "estimates": df}


def _direction(post_mean: float) -> str:
    return "higher" if post_mean > 0 else "lower"


def _hypothesis_text(trait: str, post_mean: float, ci_excludes_zero: bool) -> str:
    trait_label = trait.replace("_", " ")
    direction = _direction(post_mean)
    distinguishable = (
        "distinguishable from zero (95% CI excludes 0)"
        if ci_excludes_zero
        else "not distinguishable from zero"
    )
    return f"population LoF-burden carriers show {direction} {trait_label} on average ({distinguishable})"


def build_population_hypothesis_card(
    target_cards_df: pd.DataFrame,
    burden_df: pd.DataFrame,
    trait: str = "lymphocyte_count",
) -> pd.DataFrame:
    """Join target cards to population LoF-burden estimates by Ensembl gene ID.

    ``target_cards_df`` must have ``target`` (symbol) and ``target_id``
    (Ensembl gene ID, per ``contracts/card_schema.py``). ``burden_df`` is the
    ``estimates`` table from ``load_burden_estimates`` (already-validated,
    non-empty). Returns one row per target present in both tables (an inner
    join -- a target absent from the burden table simply has no hypothesis
    card, never a fabricated one).

    Every row's ``caveat`` field is the fixed guardrail text
    (``CAVEAT_TEXT``) -- present unconditionally, not something a caller can
    omit by choosing different columns.
    """
    if target_cards_df.empty or burden_df.empty:
        return pd.DataFrame(
            columns=[
                "target",
                "target_id",
                "trait",
                "population_effect_estimate",
                "ci_95_lower",
                "ci_95_upper",
                "ci_excludes_zero",
                "direction",
                "disease_area",
                "population_hypothesis",
                "caveat",
            ]
        )

    cards = target_cards_df[["target", "target_id"] + (["clinical_axis"] if "clinical_axis" in target_cards_df.columns else [])].drop_duplicates("target_id")
    merged = cards.merge(burden_df, left_on="target_id", right_on="ensg", how="inner")

    merged["ci_excludes_zero"] = ~((merged["lower_95"] <= 0) & (merged["upper_95"] >= 0))
    merged["direction"] = merged["post_mean"].apply(_direction)
    merged["trait"] = trait
    merged["population_hypothesis"] = merged.apply(
        lambda r: _hypothesis_text(trait, r["post_mean"], r["ci_excludes_zero"]), axis=1
    )
    merged["caveat"] = CAVEAT_TEXT
    merged = merged.rename(
        columns={
            "post_mean": "population_effect_estimate",
            "lower_95": "ci_95_lower",
            "upper_95": "ci_95_upper",
        }
    )
    if "clinical_axis" in merged.columns:
        merged = merged.rename(columns={"clinical_axis": "disease_area"})
    else:
        merged["disease_area"] = "unassigned"

    out_cols = [
        "target",
        "target_id",
        "trait",
        "population_effect_estimate",
        "ci_95_lower",
        "ci_95_upper",
        "ci_excludes_zero",
        "direction",
        "disease_area",
        "population_hypothesis",
        "caveat",
    ]
    return merged[out_cols].reset_index(drop=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build population-hypothesis cards from target_cards.csv.")
    parser.add_argument("cards", type=Path)
    parser.add_argument("--trait", default="lymphocyte_count")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    cards_df = pd.read_csv(args.cards)
    burden = load_burden_estimates(args.trait)
    if not burden["available"]:
        print(f"burden data unavailable: {burden['reason']}")
    else:
        result = build_population_hypothesis_card(cards_df, burden["estimates"], trait=args.trait)
        if args.output:
            result.to_csv(args.output, index=False)
        print(result.to_string(index=False))
