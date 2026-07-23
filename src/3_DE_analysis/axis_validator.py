"""Validate-a-scoring-axis-before-using-it (ported from "A Validated Th1/Th2
Target Map" #240).

#240's discipline: before a scoring axis is allowed to NOMINATE targets, correlate
it against an external published ground truth; if the correlation is weak, the
axis is DEMOTED to "exploratory" and its hits become support-only, not
nominations (they kept polarization rho=0.72, demoted activation rho=0.13). Their
scripts compute the metric but leave the demotion decision in prose — this module
codes the ``if`` they never wrote.

Reusable, dependency-light (numpy/scipy). ``unknown != 0``: an axis with too few
overlapping targets against the reference returns ``verdict="not_evaluable"``,
never a fake pass.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Set

import numpy as np
from scipy import stats

MIN_MATCHED = 20        # #240's n>20 guard (discover.py:143)
RHO_MIN = 0.35          # defensible default between their 0.13 (fail) and 0.72 (pass)
AUROC_MIN = 0.65


def validate_axis(
    axis_scores: Mapping[str, float],
    ground_truth: Mapping[str, float],
    *,
    known_set: Optional[Set[str]] = None,
    min_matched: int = MIN_MATCHED,
    rho_min: float = RHO_MIN,
    auroc_min: float = AUROC_MIN,
) -> Dict[str, Any]:
    """Validate one scoring axis against an external ground-truth coefficient vector.

    Returns Spearman rho (axis score vs ground-truth coef over overlapping
    targets), optional AUROC at recovering a known-positive set, sign agreement,
    and a verdict in {validated, exploratory, not_evaluable}. The demotion gate
    (rho>=rho_min AND, when computable, auroc>=auroc_min) is the piece #240 left
    in prose.
    """
    genes = [g for g in axis_scores if g in ground_truth]
    n = len(genes)
    if n < min_matched:
        return {"verdict": "not_evaluable", "n_matched": n,
                "reason": f"only {n} targets overlap the reference (need >= {min_matched})"}
    s = np.array([float(axis_scores[g]) for g in genes], dtype=float)
    c = np.array([float(ground_truth[g]) for g in genes], dtype=float)
    ok = np.isfinite(s) & np.isfinite(c)
    s, c, genes = s[ok], c[ok], [g for g, k in zip(genes, ok) if k]
    if s.size < min_matched:
        return {"verdict": "not_evaluable", "n_matched": int(s.size), "reason": "too few finite pairs"}

    rho = float(stats.spearmanr(s, c)[0])
    sign_agreement = float(np.mean(np.sign(s) == np.sign(c)))

    auroc = None
    if known_set:
        y = np.array([1 if g in known_set else 0 for g in genes])
        if 0 < y.sum() < y.size:
            try:
                from sklearn.metrics import roc_auc_score
                auroc = float(roc_auc_score(y, s))
            except Exception:  # noqa: BLE001 -- sklearn optional; fall back to rank-AUC
                auroc = _rank_auc(y, s)

    passed = (rho >= rho_min) and (auroc is None or auroc >= auroc_min)
    return {
        "verdict": "validated" if passed else "exploratory",
        "n_matched": len(genes),
        "spearman_rho": round(rho, 4),
        "sign_agreement": round(sign_agreement, 4),
        "auroc": (round(auroc, 4) if auroc is not None else None),
        "thresholds": {"rho_min": rho_min, "auroc_min": auroc_min},
        "note": "A weak axis is demoted to 'exploratory' (support-only), not used to nominate. "
                "unknown != 0: an axis with too few reference-overlapping targets is not_evaluable.",
    }


def _rank_auc(y: np.ndarray, s: np.ndarray) -> float:
    """AUROC via the Mann-Whitney U statistic (no sklearn dependency)."""
    order = np.argsort(s)
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(s) + 1)
    n_pos = int(y.sum())
    n_neg = int(len(y) - n_pos)
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    return float((ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))
