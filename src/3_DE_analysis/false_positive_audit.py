"""Self-false-positive audit — phenome-breadth specificity (ported from
"Bench to Biobank" #123).

Bench2Biobank's insight: a hit that survives every *positive* validation can still
be spurious, so it runs a **self-false-positive framework** that actively tries to
knock its own hits down via three orthogonal checks — (1) the association falls in
the **MHC region** (chr6:~25-34 Mb, where LD is so strong that associations are
promiscuous), (2) the **nearest-gene trap** (a GWAS signal that actually points at
a famous neighbour, not this gene), and (3) **phenome-category breadth** (a gene
that associates with *everything* is specific to *nothing*). Its flagship hit was
honestly down-weighted this way.

Of the three, only **phenome-breadth is computable from data the portal already
has**: the Level-4 track-A GWAS re-check carries, per target, the total number of
genetically-associated diseases and how many are immune. So this module builds the
phenome-breadth specificity flag now, and — honoring ``unknown != 0`` — reports the
other two sub-checks as ``measured: false`` with the exact data they'd need, rather
than faking a pass.

Discipline
----------
* **Descriptive-only.** This is a *false-positive-risk* band shown on the dossier;
  it NEVER feeds ``_stage()`` / ``_red_flags()`` / the readiness call. A gene with
  elevated FP risk is *flagged for a human*, not auto-demoted.
* ``unknown != 0``: a target with no track-A row -> ``verdict "unknown"`` (unmeasured),
  NOT a clean pass. ``n_genetic_assoc_diseases == 0`` is the *measured* "no genetic
  association at all" state, kept distinct from unmeasured.
* The two sub-checks we cannot compute are returned as explicit
  ``{"measured": false, "requires": ...}`` — never silently omitted, never faked.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional

# --- documented thresholds (tunable; ours, not from the source paper) ----------
BROAD_N = 10          # > this many associated diseases => a broad phenome footprint
FOCUSED_N = 3         # <= this many => a focused footprint
LOW_IMMUNE_FRAC = 0.2  # immune fraction below this, on a broad footprint => low immune specificity


def _coerce_int(x: Any) -> Optional[int]:
    """None/NaN/blank -> None (unmeasured). A real number -> int."""
    if x is None:
        return None
    if isinstance(x, str) and not x.strip():
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return int(round(v))


def _coerce_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, str) and not x.strip():
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def phenome_breadth(
    n_assoc: Any,
    n_immune: Any,
    top_any_score: Any = None,
    top_immune_score: Any = None,
) -> Dict[str, Any]:
    """Phenome-breadth specificity, the one Bench2Biobank sub-check we can compute.

    Returns a descriptive dict. ``verdict`` is one of:
      * ``"unknown"``                     -- n_assoc unmeasured (no track-A row)
      * ``"no_association"``              -- measured 0 associations (no genetic support)
      * ``"immune_focused"``             -- associations concentrated in immune disease
      * ``"mixed"``                      -- neither clearly focused nor clearly broad
      * ``"broad_low_immune_specificity"`` -- many diseases, few immune => elevated FP risk

    ``elevated_fp_risk`` is ``True`` only for the last verdict, ``None`` when unknown,
    else ``False``. It is a flag for a human — never a readiness input.
    """
    na = _coerce_int(n_assoc)
    ni = _coerce_int(n_immune)
    top_any = _coerce_float(top_any_score)
    top_immune = _coerce_float(top_immune_score)

    if na is None:
        return {
            "verdict": "unknown",
            "n_genetic_assoc_diseases": None,
            "n_immune_genetic_assoc": None,
            "immune_fraction": None,
            "phenome_breadth_tier": None,
            "elevated_fp_risk": None,
            "top_any_GA_score": top_any,
            "top_immune_GA_score": top_immune,
            "note": "no track-A GWAS row for this target — phenome breadth unmeasured (not a pass).",
        }

    if na == 0:
        return {
            "verdict": "no_association",
            "n_genetic_assoc_diseases": 0,
            "n_immune_genetic_assoc": ni,
            "immune_fraction": None,
            "phenome_breadth_tier": "none",
            "elevated_fp_risk": False,
            "top_any_GA_score": top_any,
            "top_immune_GA_score": top_immune,
            "note": "no genetic disease association at all — nothing to be spurious about (but also no genetic support).",
        }

    tier = "broad" if na > BROAD_N else ("focused" if na <= FOCUSED_N else "moderate")
    immune_fraction = (ni / na) if ni is not None else None

    if immune_fraction is not None and na > BROAD_N and immune_fraction < LOW_IMMUNE_FRAC:
        verdict, risk = "broad_low_immune_specificity", True
        note = (
            f"{na} associated diseases but only {ni} immune "
            f"(fraction {immune_fraction:.2f} < {LOW_IMMUNE_FRAC}) — a broad, non-immune-specific "
            "footprint; the apparent immune hit may be pleiotropic/spurious. Flag for human review."
        )
    elif (immune_fraction is not None and immune_fraction >= 0.5) or (
        ni is not None and ni >= 1 and na <= FOCUSED_N
    ):
        verdict, risk = "immune_focused", False
        note = "genetic associations concentrated in immune disease — low phenome-breadth FP risk."
    else:
        verdict, risk = "mixed", False
        note = "neither clearly immune-focused nor clearly broad — no strong phenome-breadth signal either way."

    return {
        "verdict": verdict,
        "n_genetic_assoc_diseases": na,
        "n_immune_genetic_assoc": ni,
        "immune_fraction": round(immune_fraction, 4) if immune_fraction is not None else None,
        "phenome_breadth_tier": tier,
        "elevated_fp_risk": risk,
        "top_any_GA_score": top_any,
        "top_immune_GA_score": top_immune,
        "note": note,
    }


def _stub(requires: str) -> Dict[str, Any]:
    """An honestly-unmeasured sub-check (`unknown != 0`), never a faked pass."""
    return {"measured": False, "flagged": None, "requires": requires}


def full_audit(
    n_assoc: Any = None,
    n_immune: Any = None,
    top_any_score: Any = None,
    top_immune_score: Any = None,
) -> Dict[str, Any]:
    """The full three-part self-false-positive audit. Only ``phenome_breadth`` is
    computed; ``mhc_region`` and ``nearest_gene`` are returned as explicit
    ``measured: false`` stubs with the data they would need."""
    pb = phenome_breadth(n_assoc, n_immune, top_any_score, top_immune_score)
    return {
        "phenome_breadth": pb,
        "mhc_region": _stub(
            "an offline Ensembl-ID -> chromosome-coordinate table to test membership "
            "in chr6:~25-34 Mb; the target cards carry no genomic coordinate."
        ),
        "nearest_gene": _stub(
            "SNP-level GWAS lead-variant coordinates to test the nearest-gene trap; "
            "only gene-level associations are available, not lead-SNP positions."
        ),
        # top-line convenience: overall elevated risk == the one check we can run
        "elevated_fp_risk": pb["elevated_fp_risk"],
    }


def audit_gwas_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience over a Level-4 track-A CSV row (its own column names)."""
    return full_audit(
        n_assoc=row.get("n_genetic_assoc_diseases"),
        n_immune=row.get("n_immune_genetic_assoc"),
        top_any_score=row.get("top_any_GA_score"),
        top_immune_score=row.get("top_immune_GA_score"),
    )
