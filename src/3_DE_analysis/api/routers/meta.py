"""Coverage-at-a-glance endpoint (docs/ux_trust_fix_plan.md Wave 1c).

Blind-spot fix: sparse-overlay domains (gnomAD constraint, GTEx breadth,
disease associations, LINCS) are disclosed as sparse in docs/REPRODUCIBILITY.md
and in code comments, but the dashboard chips for them don't carry the real
coverage number at the point of the glance -- a user sees a confident-looking
chip without knowing whether the domain was checked for 0.1% or 45% of
targets. This endpoint COMPUTES real coverage from the loaded reference
tables (never a hardcoded/copied-from-docs number, so it can't drift out of
sync with the actual data) and states its denominator basis explicitly, since
different domains join on different keys against different-sized universes.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from api import deps
from evidence.disease import list_diseases
from evidence.lincs_reference_cache import load_coverage as load_lincs_coverage

router = APIRouter(tags=["Meta"])


@router.get("/api/meta/coverage/{dataset_id}")
def get_coverage(dataset_id: str) -> Dict[str, Any]:
    """Real, computed coverage counts for the sparse descriptive overlays,
    scoped to one dataset's target universe. Every count is derived from the
    actual loaded table at request time -- never a value copied from a doc,
    which could silently drift as the underlying files change.
    """
    out_csv = deps._dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    cards = deps._load_cards(out_csv)

    target_symbols = set(cards["target"].dropna().astype(str).str.upper()) if "target" in cards.columns else set()
    target_ensembl = set(cards["target_id"].dropna().astype(str)) if "target_id" in cards.columns else set()
    total_targets = len(target_symbols)

    domains: Dict[str, Any] = {}

    gnomad = deps._gnomad_overlay()
    if gnomad.get("available") and total_targets and target_ensembl:
        gnomad_genes = set(gnomad["table"]["ensembl_id"].dropna().astype(str))
        covered = len(gnomad_genes & target_ensembl)
        domains["gnomad_constraint"] = {
            "available": True,
            "covered": covered,
            "total": total_targets,
            "pct": round(100 * covered / total_targets, 2),
            "join_key": "ensembl_id",
            "source": "gnomad_constraint_seed.csv",
        }
    else:
        domains["gnomad_constraint"] = {"available": False, "reason": gnomad.get("reason") or "no target_id/target column to join on"}

    gtex = deps._gtex_overlay()
    if gtex.get("available") and total_targets and target_ensembl:
        gtex_genes = set(gtex["table"]["ensembl_id"].dropna().astype(str))
        covered = len(gtex_genes & target_ensembl)
        domains["gtex_tissue_breadth"] = {
            "available": True,
            "covered": covered,
            "total": total_targets,
            "pct": round(100 * covered / total_targets, 2),
            "join_key": "ensembl_id",
            "source": "gtex_per_tissue.parquet",
        }
    else:
        domains["gtex_tissue_breadth"] = {"available": False, "reason": gtex.get("reason") or "no target_id/target column to join on"}

    assoc = deps._disease_associations()
    if not assoc.empty and total_targets:
        assoc_genes = set(assoc["gene_symbol"].dropna().astype(str).str.upper())
        covered = len(assoc_genes & target_symbols)
        domains["disease_association"] = {
            "available": True,
            "covered": covered,
            "total": total_targets,
            "pct": round(100 * covered / total_targets, 2),
            "n_diseases": len(list_diseases(assoc)),
            "join_key": "gene_symbol",
            "source": "disease_gene_associations_detailed.csv",
        }
    else:
        domains["disease_association"] = {"available": False, "reason": "association table not found or empty"}

    lincs = load_lincs_coverage()
    if lincs.get("available"):
        tbl = lincs["table"]
        shortlist_total = int(len(tbl))
        shortlist_covered = int((tbl["lincs_covered"] == "yes").sum()) if "lincs_covered" in tbl.columns else 0
        domains["lincs"] = {
            "available": True,
            "covered": shortlist_covered,
            "total": shortlist_total,
            "pct": round(100 * shortlist_covered / shortlist_total, 2) if shortlist_total else None,
            "join_key": "gene_symbol",
            "source": "lincs_shortlist_coverage.csv",
            # LINCS is scoped to a small hand-picked demo shortlist, NOT this
            # dataset's full target universe -- calling this out explicitly
            # since every other domain in this response uses total_targets.
            "denominator_basis": "demo shortlist genes only, NOT total_targets",
        }
    else:
        domains["lincs"] = {"available": False, "reason": lincs.get("reason")}

    return {
        "dataset_id": dataset_id,
        "total_targets": total_targets,
        "denominator_basis": "unique target gene symbols in this dataset's target_cards.csv (gnomad_constraint/gtex_tissue_breadth/disease_association); lincs uses its own small demo-shortlist denominator, noted per-domain",
        "domains": domains,
    }
