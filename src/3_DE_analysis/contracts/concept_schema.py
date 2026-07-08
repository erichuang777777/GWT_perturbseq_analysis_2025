"""The seed-modules CSV column contract (the concept-bottleneck layer, made checkable).

``sources/topic15_cd4_tcell_upstream_downstream_seed_modules.csv`` defines the 20
CD4 T-cell immune concept modules (M01-M20) that this toolkit projects targets --
and, in later phases, individual samples -- onto. It is this repo's analog of
COMPASS's (mims-harvard, *Nature Medicine* 2026) 44-concept "concept bottleneck":
gene expression is projected onto a small set of biologically meaningful immune
concepts rather than fed raw into a scorer. ``api/deps.py::_load_modules`` /
``_module_scores`` already parse this CSV to score targets against the modules;
until now nothing actually checked that the CSV matched the structure that code
assumes.

This module makes the contract checkable, in the exact style of
``contracts/card_schema.py``: ``CONCEPT_COLUMNS`` is the real column list the CSV
carries, ``CORE_REQUIRED_COLUMNS`` is the minimal subset the scoring path keys
off of, and ``validate_concept_modules`` checks a DataFrame against the contract
(all required columns present, no duplicate ``module_id``, every module has at
least one seed gene, no empty ``module_name``).

Like ``card_schema.validate_cards``, this is a descriptive/structural check only:
the concept profile it guards is **descriptive, never decisional** -- it never
feeds ``readiness_call`` / ``overall_readiness_stage`` /
``statistical_evidence_grade`` (see ``docs/concept_dictionary.md`` and the
"describe vs decide" separation established for ``safety_window_score`` /
``gnomad_constraint_flag`` in ``docs/data_dictionary.md``).

See ``docs/concept_dictionary.md`` for what each module means and
``docs/compass_concept_integration_plan.md`` §2A for the formalization rationale.
"""

from __future__ import annotations

from typing import List

import pandas as pd

# Exact column set carried by the seed-modules CSV, in its native order.
CONCEPT_COLUMNS: List[str] = [
    "module_id",
    "module_name",
    "category",
    "seed_genes",
    "primary_question",
    "notes",
]

# The minimal subset the scoring path (``deps._load_modules`` /
# ``_module_scores``) actually keys off of: it reads ``module_id``,
# ``module_name`` and ``seed_genes`` to build the concept bottleneck. The rest
# (``category``, ``primary_question``, ``notes``) are documentation context that
# degrade gracefully. Useful for a lighter-weight "is this usable" check.
CORE_REQUIRED_COLUMNS: List[str] = [
    "module_id",
    "module_name",
    "seed_genes",
]


def _split_seed_genes(cell: object) -> List[str]:
    """Parse a ``seed_genes`` cell into a gene list, matching ``deps._load_modules``.

    Comma-separated, whitespace-trimmed, empty tokens dropped. A missing/NaN
    cell yields an empty list (honest fallback -- ``unknown != 0``).
    """
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return []
    return [g.strip() for g in str(cell).split(",") if g.strip()]


def validate_concept_modules(df: pd.DataFrame, *, strict: bool = False) -> List[str]:
    """Check ``df`` against the concept-module contract. Returns a list of problems (empty = valid).

    With ``strict=False`` (default) this never raises -- callers decide what to
    do with a non-empty result (log, reject, degrade), exactly like
    ``card_schema.validate_cards``. With ``strict=True`` a non-empty problem
    list is raised as a ``ValueError`` so a caller that treats a malformed
    concept set as fatal can opt in.

    Checks, regardless of ``strict``:

    * required columns (``CORE_REQUIRED_COLUMNS``) all present;
    * no duplicate ``module_id``;
    * every module has at least one seed gene;
    * no empty/blank ``module_name``.
    """
    problems: List[str] = []

    missing = [c for c in CORE_REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        problems.append(f"missing columns: {missing}")

    if "module_id" in df.columns:
        ids = df["module_id"].astype(str).str.strip()
        dupes = sorted(ids[ids.duplicated()].unique())
        if dupes:
            problems.append(f"duplicate module_id: {dupes}")
        blank_ids = int((ids == "").sum())
        if blank_ids:
            problems.append(f"{blank_ids} row(s) have an empty module_id")

    if "module_name" in df.columns:
        names = df["module_name"].fillna("").astype(str).str.strip()
        n_blank = int((names == "").sum())
        if n_blank:
            problems.append(f"{n_blank} module(s) have an empty module_name")

    if "seed_genes" in df.columns:
        empty_seed_ids: List[str] = []
        for _, row in df.iterrows():
            if not _split_seed_genes(row.get("seed_genes")):
                empty_seed_ids.append(str(row.get("module_id", "?")))
        if empty_seed_ids:
            problems.append(f"module(s) with no seed genes: {empty_seed_ids}")

    if strict and problems:
        raise ValueError("concept-module contract violated: " + "; ".join(problems))
    return problems


def count_modules(df: pd.DataFrame) -> int:
    """Number of concept modules (rows) in ``df``."""
    return int(len(df))


def count_seed_genes(df: pd.DataFrame, *, unique: bool = False) -> int:
    """Total seed-gene mentions across all modules.

    With ``unique=True`` counts distinct gene symbols (case-insensitive, matching
    ``_module_scores``' ``.upper()`` comparison) instead of raw mentions.
    """
    if "seed_genes" not in df.columns:
        return 0
    genes: List[str] = []
    for cell in df["seed_genes"]:
        genes.extend(_split_seed_genes(cell))
    if unique:
        return len({g.upper() for g in genes})
    return len(genes)
