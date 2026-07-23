"""Confounder-controlled enrichment utilities (ported from HumanCD4CoDEGNet #234).

CoDEGNet's rigor move: before claiming "targets with property P are enriched for
outcome Q", rule out that P is just a proxy for a technical covariate (sequencing
power, expression, trans-effect breadth). Two reusable primitives:

* ``matched_permutation_test`` — shuffle the target set WITHIN covariate bins and
  recompute overlap with the hit set, so the null preserves the covariate
  distribution. A surviving enrichment is not a covariate artifact.
* ``partial_spearman`` — Spearman correlation of x vs y after regressing both on
  a confounder z (rank-residualized), i.e. association net of the covariate.

This is the reusable, tested version of the covariate-matched control pattern
used ad hoc in the convergent-core analysis (PR #111) — future analyses should
import these instead of re-rolling the permutation loop. Deterministic.
"""

from __future__ import annotations

from typing import Dict, Sequence

import numpy as np
import pandas as pd
from scipy import stats


def matched_permutation_test(
    is_target: Sequence[bool],
    is_hit: Sequence[bool],
    covariate: Sequence[float],
    *,
    nperm: int = 3000,
    nbins: int = 10,
    seed: int = 0,
) -> Dict[str, float]:
    """Covariate-matched permutation test of overlap between a target set and a hit set.

    Shuffles ``is_target`` membership within ``nbins`` quantile bins of
    ``covariate`` (preserving per-bin counts), recomputes the overlap with
    ``is_hit`` each time, and returns the observed overlap, the matched-null mean,
    and a one-sided empirical p-value (obs >= null). Deterministic given ``seed``.
    """
    t = np.asarray(is_target, dtype=bool)
    h = np.asarray(is_hit, dtype=bool)
    c = np.asarray(covariate, dtype=float)
    if not (t.shape == h.shape == c.shape) or t.size == 0:
        raise ValueError("is_target, is_hit, covariate must be equal-length non-empty")
    rng = np.random.default_rng(seed)
    bins = pd.qcut(c, nbins, labels=False, duplicates="drop")
    obs = int((t & h).sum())
    n = t.size
    null = np.empty(nperm)
    for i in range(nperm):
        perm = np.zeros(n, bool)
        for b in np.unique(bins):
            idx = np.where(bins == b)[0]
            k = int(t[idx].sum())
            if k:
                perm[rng.choice(idx, k, replace=False)] = True
        null[i] = (perm & h).sum()
    return {
        "obs": obs,
        "null_mean": float(null.mean()),
        "p": float((np.sum(null >= obs) + 1) / (nperm + 1)),
        "enrichment": (float(obs / null.mean()) if null.mean() > 0 else float("inf")),
    }


def partial_spearman(x: Sequence[float], y: Sequence[float], z: Sequence[float]) -> float:
    """Spearman(x, y) controlling for z: correlate the rank-residuals of x~z and y~z."""
    xr = pd.Series(x).rank().to_numpy(dtype=float)
    yr = pd.Series(y).rank().to_numpy(dtype=float)
    zr = pd.Series(z).rank().to_numpy(dtype=float)

    def _resid(a: np.ndarray) -> np.ndarray:
        A = np.column_stack([np.ones_like(zr), zr])
        beta, *_ = np.linalg.lstsq(A, a, rcond=None)
        return a - A @ beta

    rx, ry = _resid(xr), _resid(yr)
    if np.std(rx) == 0 or np.std(ry) == 0:
        return float("nan")
    return float(stats.spearmanr(rx, ry)[0])
