"""Signed module *effect* scoring — directional regulator → concept-module readout.

The descriptive concept layer (`concept_annotation`, `individual_concept_profile`,
`/api/modules`) is deliberately **direction-free**: it scores *membership* by binary
overlap because the aggregate DE table (`DE_stats.suppl_table.csv`, the substrate of
`target_cards.csv`) carries only up/down *counts* per perturbation, not a per-downstream-
gene sign. Signed module scoring was therefore descoped there (see
`docs/KNOWN_LIMITATIONS.md` → "Scope & positioning").

But the repo already ships a **signed** table that the card builder never reads:
`metadata/suppl_tables/full_signed_DE/*.parquet` (~2.06M rows, ~10,851 perturbed targets ×
3 conditions), with a per-downstream-gene `log_fc` and `zscore` (direction included). This
module uses it to answer a question the direction-free layer cannot: **does knocking down
a target ACTIVATE or REPRESS each CD4 concept module's program?**

Method (descriptive, re-derivable, never feeds a readiness call):
  * A module's "program markers" are its curated seed genes (`load_concept_modules`).
  * For each perturbed `target × condition × module`, take the signed `log_fc` of the
    downstream genes that are seed genes of that module, and average them.
  * **CRISPRi direction convention:** `log_fc` is the effect of *knocking the target down*.
    So markers going DOWN on knockdown (mean_logfc < 0) means the target normally
    **activates** the module; markers going UP (mean_logfc > 0) means it **represses** it.

Honesty constraints (this repo's discipline):
  * `unknown != 0`: a `target × condition × module` with **no measured module-seed
    downstream gene** is simply ABSENT from the output — never a fabricated 0. Coverage is
    sparse (only ~3,739 / 10,851 targets hit any module marker), which is the honest state
    of the data, not a bug.
  * `n_downstream_hit` (and `n_module_seed_total`) travel with every score so a 1-gene
    average is never mistaken for a well-supported one.
  * Seed genes are *curated markers*, so this reads a module's program through its markers,
    not through a learned signature — an explicit, stated assumption.
  * Deterministic; never mutates cards; never read by `core/readiness.py` or `_stage()`.

Sanity anchors (master regulators recovered with the correct sign, from the real data):
  GATA3→Th2, TBX21→Th1, FOXP3→Treg all score **negative** (activators) — knockdown lowers
  their module's markers. These are asserted in `tests/test_signed_module_effect.py`.
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# repo root = two levels up from this file (src/3_DE_analysis/signed_module_effect.py)
_ROOT = Path(__file__).resolve().parent.parent.parent
SIGNED_DE_GLOB = str(_ROOT / "metadata" / "suppl_tables" / "full_signed_DE" / "*.parquet")
DEFAULT_OUTPUT = _ROOT / "sources" / "target_tool_cache" / "_overlays" / "signed_module_effect.parquet"

# |mean_logfc| below this is reported but called "weak_or_mixed" rather than a
# confident activator/repressor. Documented + re-derivable; descriptive only.
DIRECTION_MIN_ABS_LOGFC = 0.5

_CONDITION_ORDER = {"Rest": 0, "Stim8hr": 1, "Stim48hr": 2}


def _load_seed_membership(modules: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for m in modules:
        for g in m["seed_genes"]:
            rows.append((g, m["module_id"], m["module_name"], m["category"]))
    seed = pd.DataFrame(rows, columns=["downstream_gene", "module_id", "module_name", "category"])
    # a module's seed-gene count (denominator context for coverage)
    totals = seed.groupby("module_id").size().rename("n_module_seed_total")
    return seed, totals


def _direction(mean_logfc: float) -> str:
    if pd.isna(mean_logfc):
        return "unknown"
    if mean_logfc <= -DIRECTION_MIN_ABS_LOGFC:
        return "activator"  # knockdown lowers module markers -> target activates the module
    if mean_logfc >= DIRECTION_MIN_ABS_LOGFC:
        return "repressor"  # knockdown raises module markers -> target represses the module
    return "weak_or_mixed"


def compute_signed_module_effects(
    signed_de: pd.DataFrame, modules: List[Dict[str, Any]]
) -> pd.DataFrame:
    """Signed directional effect of each perturbation on each concept module's markers.

    Returns one row per ``target × condition × module`` that has >= 1 measured
    module-seed downstream gene (never a fabricated 0-hit row). Columns:
    ``target_gene, culture_condition, module_id, module_name, category,
    n_downstream_hit, n_module_seed_total, mean_logfc, mean_zscore, direction``.
    """
    seed, totals = _load_seed_membership(modules)
    joined = signed_de.merge(seed, on="downstream_gene", how="inner")
    if joined.empty:
        return pd.DataFrame(
            columns=[
                "target_gene", "culture_condition", "module_id", "module_name",
                "category", "n_downstream_hit", "n_module_seed_total",
                "mean_logfc", "mean_zscore", "direction",
            ]
        )
    agg = (
        joined.groupby(
            ["target_gene", "culture_condition", "module_id", "module_name", "category"],
            as_index=False,
        )
        .agg(
            n_downstream_hit=("log_fc", "size"),
            mean_logfc=("log_fc", "mean"),
            mean_zscore=("zscore", "mean"),
        )
    )
    agg = agg.merge(totals, on="module_id", how="left")
    agg["direction"] = agg["mean_logfc"].map(_direction)
    # deterministic ordering
    agg["_cond"] = agg["culture_condition"].map(_CONDITION_ORDER).fillna(9)
    agg = agg.sort_values(
        ["target_gene", "_cond", "module_id"], kind="mergesort"
    ).drop(columns="_cond").reset_index(drop=True)
    return agg[
        [
            "target_gene", "culture_condition", "module_id", "module_name", "category",
            "n_downstream_hit", "n_module_seed_total", "mean_logfc", "mean_zscore", "direction",
        ]
    ]


def build(output: Path = DEFAULT_OUTPUT) -> pd.DataFrame:
    """Read full_signed_DE + concept modules, compute, and persist the compact overlay."""
    from individual_concept_profile import load_concept_modules

    parts = sorted(glob.glob(SIGNED_DE_GLOB))
    if not parts:
        raise FileNotFoundError(f"no signed-DE parquet parts found at {SIGNED_DE_GLOB}")
    signed_de = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    result = compute_signed_module_effects(signed_de, load_concept_modules())
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output, index=False)
    return result


# ----------------------------- serving helpers ----------------------------- #
_CACHE: Dict[str, pd.DataFrame] = {}


def load_effects(path: Path = DEFAULT_OUTPUT) -> Optional[pd.DataFrame]:
    """Load the precomputed overlay (cached). Returns None if it hasn't been built."""
    key = str(path)
    if key not in _CACHE:
        if not path.exists():
            return None
        _CACHE[key] = pd.read_parquet(path)
    return _CACHE[key]


def effects_for_target(gene: str, path: Path = DEFAULT_OUTPUT) -> Dict[str, Any]:
    """Per-target signed module-effect profile for the API. Honest empty when unknown.

    ``available: false`` if the overlay isn't built; ``modules: []`` (not zeros) when the
    gene perturbed nothing measurable in any module's markers.
    """
    df = load_effects(path)
    if df is None:
        return {"gene": gene, "available": False, "reason": "signed_module_effect overlay not built", "modules": []}
    sub = df[df["target_gene"].astype(str).str.upper() == str(gene).strip().upper()]
    records = [
        {
            "condition": r["culture_condition"],
            "module_id": r["module_id"],
            "module_name": r["module_name"],
            "category": r["category"],
            "n_downstream_hit": int(r["n_downstream_hit"]),
            "n_module_seed_total": int(r["n_module_seed_total"]),
            "mean_logfc": float(r["mean_logfc"]),
            "mean_zscore": float(r["mean_zscore"]),
            "direction": r["direction"],
        }
        for _, r in sub.iterrows()
    ]
    return {
        "gene": gene,
        "available": True,
        "n_module_condition_hits": len(records),
        "direction_convention": "CRISPRi knockdown: mean_logfc<0 => target ACTIVATES the module (markers drop on knockdown); >0 => REPRESSES. unknown != 0: absent module/condition pairs are unmeasured, not zero.",
        "modules": records,
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Build the signed module-effect overlay from full_signed_DE.")
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args(argv)
    result = build(args.output)
    n_targets = result["target_gene"].nunique()
    print(f"wrote {len(result):,} rows ({n_targets:,} targets) -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
