"""Disease/indication translator: connect CD4 target cards to disease genetics.

Grounded entirely in a local, real Open Targets genetic-association export
already produced by prior repo research
(``src/6_functional_interaction/results/disease_gene_associations_detailed.csv``,
7,528 rows across 13 autoimmune/inflammatory indications). No new external
fetch is needed or performed here -- this module only joins that existing
table against a built ``target_cards.csv``.

Coverage is intentionally restricted to the 13 diseases actually present in
that table. There is no free-text disease search: an indication not in the
local table returns an empty result with an explicit reason, rather than a
guessed or fabricated match.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

DEFAULT_ASSOCIATIONS_PATH = Path(
    "src/6_functional_interaction/results/disease_gene_associations_detailed.csv"
)


def load_disease_associations(path: Path = DEFAULT_ASSOCIATIONS_PATH) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=["disease_efo", "disease_name", "gene_symbol", "association_score", "genetic_evidence_score", "genetic_evidence_types"])
    df = pd.read_csv(path)
    df["gene_symbol"] = df["gene_symbol"].astype(str).str.strip().str.upper()
    return df


def list_diseases(associations: pd.DataFrame) -> List[Dict[str, Any]]:
    if associations.empty:
        return []
    grouped = associations.groupby("disease_name").agg(
        disease_efo=("disease_efo", "first"),
        n_genes=("gene_symbol", "nunique"),
    )
    return [
        {"disease_name": name, "disease_efo": row["disease_efo"], "n_genes": int(row["n_genes"])}
        for name, row in grouped.sort_values("n_genes", ascending=False).iterrows()
    ]


def translate_disease(
    cards: pd.DataFrame,
    disease_name: str,
    associations: pd.DataFrame,
    readiness: Optional[pd.DataFrame] = None,
    min_grade: int = 2,
    top_n: int = 50,
) -> Dict[str, Any]:
    """Rank target cards by disease genetic association, for one local disease.

    Returns a dict with ``matched`` (bool), ``reason`` (why empty, if empty),
    and ``targets`` (ranked records combining GWT statistical evidence with
    the disease's genetic-association score).
    """
    if associations.empty:
        return {"matched": False, "reason": "no local disease-association table available", "targets": []}

    disease_rows = associations[associations["disease_name"].str.lower() == disease_name.strip().lower()]
    if disease_rows.empty:
        available = sorted(associations["disease_name"].unique().tolist())
        return {
            "matched": False,
            "reason": f"'{disease_name}' is not in the local disease-association table; available: {available}",
            "targets": [],
        }

    disease_genes = disease_rows.drop_duplicates("gene_symbol").set_index("gene_symbol")

    merged = cards.copy()
    merged["target_upper"] = merged["target"].astype(str).str.strip().str.upper()
    merged = merged[merged["target_upper"].isin(disease_genes.index)]
    if "statistical_evidence_grade" in merged.columns:
        merged = merged[pd.to_numeric(merged["statistical_evidence_grade"], errors="coerce") >= min_grade]
    if merged.empty:
        return {
            "matched": True,
            "reason": f"no target-condition rows at grade>={min_grade} overlap {disease_name}'s associated genes",
            "targets": [],
        }

    merged["disease_association_score"] = merged["target_upper"].map(disease_genes["association_score"])
    merged["genetic_evidence_score"] = merged["target_upper"].map(disease_genes["genetic_evidence_score"])
    merged["genetic_evidence_types"] = merged["target_upper"].map(disease_genes["genetic_evidence_types"])

    if readiness is not None and not readiness.empty:
        key_cols = ["target", "condition"]
        readiness_slim = readiness[key_cols + ["overall_readiness_stage", "readiness_call", "red_flag_override"]].drop_duplicates(key_cols)
        merged = merged.merge(readiness_slim, on=key_cols, how="left")

    merged = merged.sort_values(
        by=[c for c in ["disease_association_score", "statistical_evidence_grade", "n_total_de_genes"] if c in merged.columns],
        ascending=False,
    )
    out_cols = [
        c
        for c in [
            "target",
            "condition",
            "statistical_evidence_grade",
            "readiness_call",
            "overall_readiness_stage",
            "red_flag_override",
            "disease_association_score",
            "genetic_evidence_score",
            "genetic_evidence_types",
            "pathway_axis",
            "clinical_axis",
            "druggable_class",
            "tractability_modality",
            "score_cap_reason",
        ]
        if c in merged.columns
    ]
    top = merged[out_cols].head(top_n)
    return {"matched": True, "reason": None, "targets": top.to_dict(orient="records")}
