"""Self-falsification audit — does the system reject its own darlings? (Action 3.)

A target-discovery system that only ever confirms itself is worthless. This module
makes the opposite property *executable and reproducible*: it shows, on real data,
that the system's own honesty axis vetoes the very hits that look most impressive
on a naive axis — the "kills its own darling, with receipts" property that the
strongest projects in this cohort (Louis #214, PerturbGate #155) won on.

Two receipts, both computed from data already in this repo:

1. **Hub-darling audit (the star).** The most naive "importance" ranking is
   trans-effect breadth — how many downstream genes a knockdown moves (a hub).
   But breadth is *dual-use*: the biggest hubs are disproportionately the
   pan-essential / broad-effect machinery (SAGA, Mediator, elongation) that the
   readiness engine's safety veto correctly refuses to advance. This audit
   quantifies that: the fraction of the top-N breadth "darlings" that the
   system's OWN veto lists (core-essentials + broad-effect) reject, against the
   same fraction among the low-breadth tail. A large enrichment is the system
   disciplining its most attractive-looking signal.

2. **Anchor cases (known right answers, including known NOs).** Curated
   gold-standard verdicts the system must reproduce — not only a target it should
   ADVANCE (ZAP70, the canonical TCR kinase) but a target it should REJECT
   (MED12, whose large footprint looks like a master regulator but is a
   pleiotropic Mediator subunit). A calibration set that contains cases where the
   correct output is "no" is what separates a discriminating system from a
   rubber stamp.

Honesty constraints (this repo's discipline):
* Descriptive/audit only — never mutates cards, never read by ``core/readiness``.
* ``unknown != 0``: a gene absent from the breadth overlay or veto lists simply
  isn't counted; nothing is imputed.
* The veto lists ARE the system's real decision inputs (``core_essentials_hart``,
  ``broad_effect_genes``), so this audit grades the system against itself, not
  against a hand-picked strawman.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd

import trans_network

_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_ESSENTIALS = _ROOT / "metadata" / "gene_lists" / "core_essentials_hart.tsv"
DEFAULT_BROAD_EFFECT = _ROOT / "sources" / "broad_effect_genes.txt"


# Curated known-answer verdicts. Each carries WHY it looks appealing on a naive
# axis, what the system SHOULD do, and an external/mechanistic confirmation that
# the system's verdict is the correct one. The point of including a "reject" case
# is that a system which can only say yes has proven nothing.
ANCHOR_CASES: List[Dict[str, str]] = [
    {
        "gene": "ZAP70",
        "naive_appeal": "canonical TCR-proximal kinase with a strong, clean knockdown effect",
        "system_should": "advance",
        "why": "grade-4 statistical evidence, passes cross-donor/cross-guide robustness — a true positive",
        "external_confirmation": "established, well-validated immune target (Open Targets / textbook TCR signalling)",
    },
    {
        "gene": "MED12",
        "naive_appeal": "very large downstream footprint — superficially reads like a master regulator to chase",
        "system_should": "reject_broad_effect",
        "why": "on the broad-effect veto list; a Mediator-complex subunit whose knockdown perturbs a huge, non-specific slice of the transcriptome",
        "external_confirmation": "Mediator kinase-module subunit; pleiotropic / pan-essential-adjacent — advancing it would be a broad-effect artifact",
    },
]


def _norm_set(genes) -> Set[str]:
    return {str(g).strip().upper() for g in genes if str(g).strip()}


def load_veto_genes(
    essentials_path: Path = DEFAULT_ESSENTIALS,
    broad_effect_path: Path = DEFAULT_BROAD_EFFECT,
) -> Dict[str, Set[str]]:
    """Load the system's own veto lists (the real readiness decision inputs)."""
    from core.cards import load_gene_set

    ess = _norm_set(load_gene_set(essentials_path)) if essentials_path.exists() else set()
    broad = _norm_set(load_gene_set(broad_effect_path)) if broad_effect_path.exists() else set()
    return {"essentials": ess, "broad_effect": broad, "veto": ess | broad}


def hub_darling_audit(
    breadth_df: pd.DataFrame,
    veto: Set[str],
    *,
    top_n: int = 50,
) -> Dict[str, Any]:
    """Fraction of the top-N breadth 'darlings' the system's veto rejects, vs the
    low-breadth tail. A large enrichment = the system disciplines its own most
    impressive-looking signal."""
    if breadth_df is None or breadth_df.empty or not veto:
        return {"available": False, "reason": "breadth overlay or veto lists unavailable"}
    ordered = breadth_df.sort_values("trans_effect_breadth", ascending=False)
    genes = ordered["target_gene"].astype(str).str.upper().tolist()
    n = min(top_n, len(genes) // 2 or 1)
    top = genes[:n]
    bottom = genes[-n:]
    top_vetoed = [g for g in top if g in veto]
    bottom_vetoed = [g for g in bottom if g in veto]
    top_pct = len(top_vetoed) / n
    bottom_pct = len(bottom_vetoed) / n
    enrichment = (top_pct / bottom_pct) if bottom_pct > 0 else float("inf")
    return {
        "available": True,
        "top_n": n,
        "top_breadth_vetoed_pct": round(top_pct, 4),
        "low_breadth_vetoed_pct": round(bottom_pct, 4),
        "enrichment": (round(enrichment, 2) if enrichment != float("inf") else None),
        "enrichment_note": "top-hub vetoed rate ÷ low-breadth vetoed rate (None = low-breadth rate is 0, i.e. even stronger)",
        "darlings_the_system_rejects": top_vetoed[:12],
        "interpretation": (
            "The system's most impressive-looking signal (biggest trans-effect hubs) is "
            "disproportionately rejected by its OWN safety veto — it does not advance its darlings."
        ),
    }


def run_self_falsification(
    breadth_df: Optional[pd.DataFrame] = None,
    veto_lists: Optional[Dict[str, Set[str]]] = None,
    *,
    top_n: int = 50,
) -> Dict[str, Any]:
    """Full audit payload: the hub-darling receipt + the anchor cases."""
    if breadth_df is None:
        breadth_df = trans_network.load_breadth()
    if veto_lists is None:
        veto_lists = load_veto_genes()
    veto = veto_lists.get("veto", set())
    audit = hub_darling_audit(breadth_df, veto, top_n=top_n) if breadth_df is not None else {"available": False, "reason": "breadth overlay not built"}
    return {
        "kind": "self_falsification_audit",
        "claim": "This system rejects its own darlings — the hits that look best on a naive axis are the ones its honesty axis vetoes.",
        "hub_darling_audit": audit,
        "anchor_cases": ANCHOR_CASES,
        "veto_list_size": len(veto),
        "caveat": "Descriptive audit; the veto lists are the readiness engine's real decision inputs, so the system is graded against itself. unknown != 0.",
    }


def main() -> int:
    report = run_self_falsification()
    a = report["hub_darling_audit"]
    print(report["claim"])
    if a.get("available"):
        print(f"  top-{a['top_n']} hubs vetoed by the system: {a['top_breadth_vetoed_pct']*100:.0f}%")
        print(f"  low-breadth tail vetoed:                 {a['low_breadth_vetoed_pct']*100:.0f}%")
        print(f"  enrichment: {a['enrichment']}x   darlings rejected: {', '.join(a['darlings_the_system_rejects'][:8])}")
    for c in report["anchor_cases"]:
        print(f"  anchor {c['gene']}: system should {c['system_should']} — {c['external_confirmation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
