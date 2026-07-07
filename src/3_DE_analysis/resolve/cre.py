"""Cis-regulatory element (CRE) data contracts -- schema placeholder (B5).

No CRE dataset (e.g. the Moonen enhancer/CRE screen this was scoped for) is
present anywhere in this repo as of this writing (confirmed by search: no
Moonen/CRE/enhancer data files exist). Rather than defer the data MODEL to
whenever that data arrives -- which would force a schema migration on every
consumer that already joined against target cards -- the model is reserved
now, empty but valid, per the review recommendation: "即使 MVP 不載入 CRE 資料，
也先把資料模型留好."

Every loader here returns a correctly-shaped, empty DataFrame/result with an
explicit "not loaded" status when no real file is supplied. Nothing here
fabricates CRE or variant-CRE-link data.

Schema (matches the review's suggested entities exactly):

    CisRegulatoryElement:
        cre_id: str
        dataset_id: str
        genome_build: str        # e.g. "hg38"
        chrom: str
        start: int
        end: int
        linked_gene_ids: list[str]  # stored as a ';'-joined string in the CSV form

    VariantCRELink:
        variant_id: str           # rsID or chr:pos:ref:alt
        cre_id: str
        gwas_trait: str | None
        source: str
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from common import degrade

CRE_COLUMNS = ["cre_id", "dataset_id", "genome_build", "chrom", "start", "end", "linked_gene_ids"]
VARIANT_CRE_LINK_COLUMNS = ["variant_id", "cre_id", "gwas_trait", "source"]


def empty_cre_table() -> pd.DataFrame:
    return pd.DataFrame(columns=CRE_COLUMNS)


def empty_variant_cre_link_table() -> pd.DataFrame:
    return pd.DataFrame(columns=VARIANT_CRE_LINK_COLUMNS)


def load_cre_elements(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load CRE elements from ``path`` if given and it exists; otherwise return
    an explicit, empty-but-valid "not loaded" result -- never fabricated rows.
    """
    if path is None or not Path(path).exists():
        return degrade.unavailable_available(
            "no CRE dataset file configured/found", data_key="elements", empty=empty_cre_table()
        )
    df = pd.read_csv(path)
    missing = [c for c in CRE_COLUMNS if c not in df.columns]
    if missing:
        return degrade.unavailable_available(
            f"CRE file missing required columns: {missing}", data_key="elements", empty=empty_cre_table()
        )
    return {"available": True, "reason": None, "elements": df}


def load_variant_cre_links(path: Optional[Path] = None) -> Dict[str, Any]:
    if path is None or not Path(path).exists():
        return degrade.unavailable_available(
            "no variant-CRE-link dataset file configured/found",
            data_key="links",
            empty=empty_variant_cre_link_table(),
        )
    df = pd.read_csv(path)
    missing = [c for c in VARIANT_CRE_LINK_COLUMNS if c not in df.columns]
    if missing:
        return degrade.unavailable_available(
            f"variant-CRE-link file missing required columns: {missing}",
            data_key="links",
            empty=empty_variant_cre_link_table(),
        )
    return {"available": True, "reason": None, "links": df}


def cre_for_gene(gene_id: str, cre_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """CRE elements whose linked_gene_ids includes gene_id. Empty list if unavailable."""
    if not cre_result.get("available"):
        return []
    df = cre_result["elements"]
    if df.empty or "linked_gene_ids" not in df.columns:
        return []
    mask = df["linked_gene_ids"].astype(str).str.split(";").apply(lambda ids: gene_id in [i.strip() for i in ids])
    return df[mask].to_dict(orient="records")
