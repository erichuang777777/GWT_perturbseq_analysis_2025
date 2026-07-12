"""Surface the source paper's OWN nominated regulators — verbatim, not recomputed.

The paper (Zhu, Dann, …, Marson — bioRxiv 10.64898/2025.12.23.696273) fits models that
nominate regulators of T-cell **polarization** and **age-related** signatures, and ships
those nominations as supplementary tables this toolkit never read:

  * `metadata/suppl_tables/polarization_prediction_condition_comparison_regulator_coefficients.csv`
    (23,172 rows, 3,994 regulators) — per `regulator` gene × signature × condition:
    `coef_mean` (signed model coefficient), `coef_rank` (0–1 percentile; higher = more
    strongly nominated), `known_regulators` (True = previously-known regulator, False =
    a *novel* nomination — the paper's own labelling).
  * `metadata/suppl_tables/aging_prediction_condition_comparison_regulator_coefficients.csv`
    (10,763 rows, 5,449 regulators) — the same shape for the CD4T aging signature.

This module surfaces those rows **as-is**, keyed by gene, so a dossier can answer: *is this
target one of the paper's own nominated polarization / aging regulators, at what rank, and
did the paper call it known or novel?* It is the most honest form of "strengthen the paper's
info" — no recomputation, no reinterpretation; the paper's numbers, made queryable.

Sanity anchors (the paper's own top nominations, asserted in the test): GATA3 → polarization
`coef_rank == 1.000`, `known == True`; STAT6 ≈ 0.998 known; BCL6 ≈ 0.983 **novel**.

Honesty (repo discipline): descriptive only (never a readiness input); `unknown != 0` — a
gene the paper did not nominate is simply ABSENT from the result, never returned with a 0
coefficient/rank; the paper's `known/novel` flag and context (`celltype`) travel with every
nomination so nothing is flattened.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
_SUPPL = _ROOT / "metadata" / "suppl_tables"
POLARIZATION_CSV = _SUPPL / "polarization_prediction_condition_comparison_regulator_coefficients.csv"
AGING_CSV = _SUPPL / "aging_prediction_condition_comparison_regulator_coefficients.csv"

_CACHE: Dict[str, Optional[pd.DataFrame]] = {}


def _load(axis: str, path: Path) -> Optional[pd.DataFrame]:
    if axis not in _CACHE:
        if not path.exists():
            _CACHE[axis] = None
        else:
            df = pd.read_csv(path, low_memory=False)
            keep = ["regulator", "coef_mean", "coef_rank", "known_regulators",
                    "signature", "celltype", "dataset_key"]
            df = df[[c for c in keep if c in df.columns]].copy()
            df["axis"] = axis
            _CACHE[axis] = df
    return _CACHE[axis]


def _records_for(df: Optional[pd.DataFrame], gene: str) -> List[Dict[str, Any]]:
    if df is None:
        return []
    sub = df[df["regulator"].astype(str).str.upper() == gene.strip().upper()]
    out = []
    for _, r in sub.iterrows():
        out.append({
            "axis": r["axis"],
            "signature": r.get("signature"),
            "context": r.get("celltype"),  # Rest / Stim8hr / Stim48hr (/ K562 for aging)
            "dataset_key": r.get("dataset_key"),
            "coef_mean": None if pd.isna(r.get("coef_mean")) else float(r["coef_mean"]),
            "coef_rank": None if pd.isna(r.get("coef_rank")) else float(r["coef_rank"]),
            "known_regulator": bool(r["known_regulators"]) if not pd.isna(r.get("known_regulators")) else None,
        })
    # deterministic: strongest nomination first
    out.sort(key=lambda x: (x["coef_rank"] if x["coef_rank"] is not None else -1), reverse=True)
    return out


def regulators_for_target(gene: str) -> Dict[str, Any]:
    """The paper's own regulator nominations for ``gene``. Honest empty when not nominated.

    ``available: false`` if the paper's tables aren't present; ``nominations: []`` (not a
    zero-coefficient row) when the paper did not nominate this gene in either model.
    """
    pol = _load("polarization", POLARIZATION_CSV)
    age = _load("aging", AGING_CSV)
    if pol is None and age is None:
        return {"gene": gene, "available": False,
                "reason": "paper regulator-coefficient tables not present", "nominations": []}
    noms = _records_for(pol, gene) + _records_for(age, gene)
    ranks = [n["coef_rank"] for n in noms if n["coef_rank"] is not None]
    return {
        "gene": gene,
        "available": True,
        "n_nominations": len(noms),
        "max_coef_rank": max(ranks) if ranks else None,
        "is_known_regulator": any(n["known_regulator"] for n in noms) if noms else None,
        "nominated_novel": any(n["known_regulator"] is False for n in noms) if noms else None,
        "note": ("Surfaced verbatim from the source paper's own regulator-coefficient tables "
                 "(not recomputed). coef_rank is a 0-1 percentile within the paper's model "
                 "(higher = more strongly nominated); coef_mean is signed. known_regulator is "
                 "the paper's own label (False = a novel nomination). unknown != 0: a gene the "
                 "paper did not nominate is absent, not a 0. Descriptive only — not a readiness input."),
        "nominations": noms,
    }
