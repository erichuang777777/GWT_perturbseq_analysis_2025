"""Gene identifier resolution with Ensembl gene ID as the primary key (B1).

Gene symbols drift: HGNC renames genes (e.g. histone gene renaming ~2020:
``HIST1H3D`` -> ``H3C4``), the same symbol can mean different things in
different contexts, and CRISPR guide libraries are frequently designed
against an older symbol than the one later curated as canonical. A resolver
keyed on symbol alone silently mismatches; this module resolves any query
(symbol, alias, or Ensembl ID) to a canonical Ensembl gene ID, and reports
*how* it got there, rather than guessing.

Grounded entirely in real, local, already-in-repo data -- no external HGNC
download was fetched or is required. The alias table comes directly from
``sgrna_library_metadata.suppl_table.csv``: for every targeted gene, the
sgRNA-design-time symbol (``target_gene_name_from_sgRNA``) and the
subsequently curated symbol (``target_gene_name``) are both real, and 344 of
12,654 genes in this library differ between the two (confirmed real HGNC
renames, e.g. ``ICK``->``CILK1``, ``QARS``->``QARS1``, ``HIST1H2BN``->``H2BC15``).
Ensembl gene ID (``target_gene_id``) is confirmed 1:1 with the canonical
symbol in this data (0/12,654 genes have more than one canonical symbol for
the same ID), and no alias symbol collides with a different gene's canonical
symbol (confirmed empirically) -- so resolution here is unambiguous by
construction, not by assumption.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from common import coerce

DEFAULT_LIBRARY_PATH = Path("metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv")


class GeneResolver:
    """Resolves a gene query (symbol, alias, or Ensembl ID) to a canonical identity.

    Construct via ``load_resolver()`` rather than directly, so the alias table
    is built consistently from the real library metadata every time.
    """

    def __init__(self, canonical_by_id: Dict[str, str], id_by_canonical: Dict[str, str], id_by_alias: Dict[str, str], expressed_ids: Optional[set] = None):
        self._canonical_by_id = canonical_by_id
        self._id_by_canonical = id_by_canonical
        self._id_by_alias = id_by_alias
        self._id_by_canonical_upper = {k.upper(): v for k, v in id_by_canonical.items()}
        self._id_by_alias_upper = {k.upper(): v for k, v in id_by_alias.items()}
        self._expressed_ids = expressed_ids or set()

    def resolve(self, query: str) -> Dict[str, Any]:
        """Resolve one query string. Never raises; always returns a structured result."""
        if not query or not str(query).strip():
            return {"query": query, "matched": False, "resolution_path": "empty_query", "ensembl_gene_id": None, "canonical_symbol": None}
        q = str(query).strip()

        if q in self._canonical_by_id:
            return self._found(q, self._canonical_by_id[q], "exact_ensembl_id", query)
        if q in self._id_by_canonical:
            gid = self._id_by_canonical[q]
            return self._found(gid, q, "exact_canonical_symbol", query)
        if q in self._id_by_alias:
            gid = self._id_by_alias[q]
            return self._found(gid, self._canonical_by_id[gid], "exact_alias_symbol", query)

        q_upper = q.upper()
        if q_upper in self._id_by_canonical_upper:
            gid = self._id_by_canonical_upper[q_upper]
            return self._found(gid, self._canonical_by_id[gid], "case_insensitive_canonical_symbol", query)
        if q_upper in self._id_by_alias_upper:
            gid = self._id_by_alias_upper[q_upper]
            return self._found(gid, self._canonical_by_id[gid], "case_insensitive_alias_symbol", query)

        return {
            "query": query,
            "matched": False,
            "resolution_path": "no_match",
            "ensembl_gene_id": None,
            "canonical_symbol": None,
            "is_expressed_in_dataset": None,
        }

    def _found(self, gene_id: str, canonical_symbol: str, path: str, original_query: str) -> Dict[str, Any]:
        return {
            "query": original_query,
            "matched": True,
            "resolution_path": path,
            "ensembl_gene_id": gene_id,
            "canonical_symbol": canonical_symbol,
            "is_expressed_in_dataset": (gene_id in self._expressed_ids) if self._expressed_ids else None,
        }

    def resolve_many(self, queries: List[str]) -> List[Dict[str, Any]]:
        return [self.resolve(q) for q in queries]

    def canonical_symbols(self) -> Dict[str, str]:
        """Read-only {canonical_symbol: ensembl_gene_id} map, for search/listing use."""
        return dict(self._id_by_canonical)

    def alias_symbols(self) -> Dict[str, str]:
        """Read-only {alias_symbol: ensembl_gene_id} map, for search/listing use."""
        return dict(self._id_by_alias)

    def canonical_symbol_for(self, gene_id: str) -> Optional[str]:
        return self._canonical_by_id.get(gene_id)

    def alias_count(self) -> int:
        return len(self._id_by_alias)

    def gene_count(self) -> int:
        return len(self._canonical_by_id)


RESULT_STATUS_STATES = ("not_in_library", "not_expressed", "no_significant_effect", "has_effect")


def result_status(resolver: GeneResolver, query: str, de_df: pd.DataFrame, target_col: str = "target") -> Dict[str, Any]:
    """Three-state (+has_effect) result status for ANY gene query (B2).

    Distinguishes three genuinely different reasons a researcher finds
    "no result," which each call for a different next action:
        not_in_library        -- the gene was never in the guide library; it
                                  cannot be perturbed in this screen at all.
        not_expressed         -- it's in the library, but baseline expression
                                  in NTC cells is too low to ever assess
                                  knockdown (reuses the resolver's
                                  is_expressed_in_dataset, itself sourced from
                                  the same 0.001 NTC-expression floor as
                                  build_target_cards.py's kd_status).
        no_significant_effect -- it's in the library, measurably expressed,
                                  perturbed, and tested, but no condition
                                  shows a significant on-target/downstream
                                  effect.
        has_effect            -- at least one condition shows a real effect.

    ``de_df`` can be either a built ``target_cards.csv`` frame (columns
    ``target``, ``ontarget_significant``, ``n_total_de_genes``) or the raw
    ``DE_stats.suppl_table.csv`` (columns ``target_contrast_gene_name``,
    ``ontarget_significant``, ``n_total_de_genes``) -- both are handled.
    """
    resolution = resolver.resolve(query)
    if not resolution["matched"]:
        return {**resolution, "result_status": "not_in_library"}
    if resolution["is_expressed_in_dataset"] is False:
        return {**resolution, "result_status": "not_expressed"}

    df = de_df
    if target_col not in df.columns and "target_contrast_gene_name" in df.columns:
        df = df.rename(columns={"target_contrast_gene_name": target_col})
    canonical = str(resolution["canonical_symbol"]).upper()
    gene_rows = df[df[target_col].astype(str).str.upper() == canonical] if target_col in df.columns else df.iloc[0:0]

    if gene_rows.empty:
        return {
            **resolution,
            "result_status": "no_significant_effect",
            "n_condition_rows": 0,
            "note": "gene is in the library and expressed, but has no row in this DE/card table (filtered out or not tested here)",
        }
    if "ontarget_significant" in gene_rows.columns:
        # Uses common.coerce.as_bool (the stricter Series-safe coercion; see
        # that module's docstring) rather than the narrower isin({"true","1"})
        # this used to inline directly.
        has_effect = bool(coerce.as_bool(gene_rows["ontarget_significant"]).any())
    else:
        has_effect = bool(pd.to_numeric(gene_rows.get("n_total_de_genes", 0), errors="coerce").fillna(0).gt(0).any())
    return {
        **resolution,
        "result_status": "has_effect" if has_effect else "no_significant_effect",
        "n_condition_rows": int(len(gene_rows)),
    }


def build_alias_table(library_path: Path = DEFAULT_LIBRARY_PATH) -> pd.DataFrame:
    """Build the (ensembl_gene_id, canonical_symbol, alias_symbol_or_none) table."""
    lib = pd.read_csv(library_path)
    genes = (
        lib[["target_gene_id", "target_gene_name", "target_gene_name_from_sgRNA"]]
        .dropna(subset=["target_gene_id", "target_gene_name"])
        .drop_duplicates("target_gene_id")
    )
    genes = genes.rename(columns={"target_gene_id": "ensembl_gene_id", "target_gene_name": "canonical_symbol"})
    genes["alias_symbol"] = genes["target_gene_name_from_sgRNA"].where(
        genes["target_gene_name_from_sgRNA"] != genes["canonical_symbol"], None
    )
    return genes[["ensembl_gene_id", "canonical_symbol", "alias_symbol"]].reset_index(drop=True)


def load_resolver(library_path: Path = DEFAULT_LIBRARY_PATH, guide_kd_path: Optional[Path] = None) -> GeneResolver:
    """Build a GeneResolver from the real local library metadata (+ optional expression floor)."""
    alias_df = build_alias_table(library_path)
    canonical_by_id = dict(zip(alias_df["ensembl_gene_id"], alias_df["canonical_symbol"]))
    id_by_canonical = dict(zip(alias_df["canonical_symbol"], alias_df["ensembl_gene_id"]))
    id_by_alias = {
        row["alias_symbol"]: row["ensembl_gene_id"] for _, row in alias_df.dropna(subset=["alias_symbol"]).iterrows()
    }

    expressed_ids = None
    if guide_kd_path is not None and Path(guide_kd_path).exists():
        guide_kd = pd.read_csv(guide_kd_path)
        if "perturbed_gene_id" in guide_kd.columns and "ntc_mean_expr" in guide_kd.columns:
            # Read directly from config/thresholds.py (the single source of truth,
            # architecture refactor Phase 0) rather than from build_target_cards.py's
            # re-export, so resolve/ does not need to depend on core/.
            from config.thresholds import KD_NOT_MEASURABLE_EXPRESSION_FLOOR

            expressed_ids = set(
                guide_kd.loc[guide_kd["ntc_mean_expr"] > KD_NOT_MEASURABLE_EXPRESSION_FLOOR, "perturbed_gene_id"].unique()
            )

    return GeneResolver(canonical_by_id, id_by_canonical, id_by_alias, expressed_ids=expressed_ids)


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Resolve gene queries against the real local alias table.")
    parser.add_argument("queries", nargs="+")
    parser.add_argument("--library", type=Path, default=DEFAULT_LIBRARY_PATH)
    parser.add_argument("--guide-kd", type=Path, default=Path("metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv"))
    args = parser.parse_args()

    resolver = load_resolver(args.library, args.guide_kd)
    print(f"loaded {resolver.gene_count()} genes, {resolver.alias_count()} real aliases")
    for result in resolver.resolve_many(args.queries):
        print(json.dumps(result))
