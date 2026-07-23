"""Per-target reliability / confidence coefficient (ported from G-perturb #133).

G-perturb's insight: a readiness *call* is a point estimate; you also want a
0-1 **reliability coefficient** saying how reproducible the underlying effect is.
Its self-contained formula (``per_target_ranking.py:r_dep``) is a joint
generalizability over two random facets (guides, donors) where error-to-signal
ratios add:

    R_dep = 1 / (1 + (1 - R_guide)/R_guide + (1 - R_donor)/R_donor)

R_guide / R_donor are split-half profile correlations across guides / donors.
**The portal already stores exactly those** as ``crossguide_correlation`` and
``crossdonor_correlation_mean`` on every card — so this computes a per-target
confidence with NO pipeline change. The re-ranking score is ``S_t = effect ×
R_dep`` (effect magnitude weighted by reliability).

Discipline:
* Descriptive-only. This is a confidence BAND shown NEXT TO the advance/validate/
  watchlist/deprioritize call — never folded into it, never a readiness input.
* ``unknown != 0``: a MISSING correlation (NaN) yields ``None`` (unmeasured), NOT
  0. A genuinely non-positive measured correlation yields ``0.0`` (measured but
  unreliable) — the two are kept distinct.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional

HIGH, MODERATE = 0.7, 0.4  # documented confidence-tier cuts


def _coerce(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def r_dep(rg: Any, rd: Any) -> Optional[float]:
    """Joint guide×donor reliability coefficient in [0, 1], or None if unmeasured.

    ``None`` when either correlation is missing/NaN (unknown != 0). A measured
    correlation <= 0 makes the target reliably-UNreliable -> 0.0 (the r_dep
    formula's continuous limit as R -> 0+). Otherwise the G-perturb formula.
    """
    g, d = _coerce(rg), _coerce(rd)
    if g is None or d is None:
        return None
    if g <= 0 or d <= 0:
        return 0.0
    g, d = min(g, 1.0), min(d, 1.0)
    return round(1.0 / (1.0 + (1.0 - g) / g + (1.0 - d) / d), 4)


def confidence_tier(rdep: Optional[float]) -> str:
    if rdep is None:
        return "unknown"
    if rdep >= HIGH:
        return "high"
    if rdep >= MODERATE:
        return "moderate"
    if rdep > 0:
        return "low"
    return "unreliable"


def reliability_for_card(
    crossguide_correlation: Any,
    crossdonor_correlation_mean: Any,
    effect_size: Any = None,
) -> Dict[str, Any]:
    """Reliability descriptor for one target card, from fields the card already has.

    ``s_score = |effect| × R_dep`` is a reliability-weighted re-ranking value
    (None when either input is unmeasured).
    """
    g, d = _coerce(crossguide_correlation), _coerce(crossdonor_correlation_mean)
    rdep = r_dep(g, d)
    eff = _coerce(effect_size)
    s = round(abs(eff) * rdep, 4) if (eff is not None and rdep is not None) else None
    return {
        "r_guide": (round(g, 4) if g is not None else None),
        "r_donor": (round(d, 4) if d is not None else None),
        "r_dep": rdep,
        "confidence_tier": confidence_tier(rdep),
        "s_score": s,
        "note": "Reliability-weighted confidence (G-perturb). Descriptive band shown "
                "beside the readiness call, never folded into it. unknown != 0.",
    }
