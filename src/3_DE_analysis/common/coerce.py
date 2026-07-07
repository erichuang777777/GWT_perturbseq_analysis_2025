"""Single source of truth for scalar/Series bool and float coercion (architecture refactor Phase 1).

Before this module existed, the same kinds of coercion were reimplemented in
several places:

- **Scalar bool coercion.** ``build_target_cards.py``'s ``_to_bool`` (line
  247) and a narrower, inline variant in ``gene_identifier_resolver.py``
  (``gene_rows["ontarget_significant"].astype(str).str.lower().isin({"true",
  "1"})``, line 160) -- the inline version is missing the "yes"/"y"/"t"
  tokens and the ``.strip()`` whitespace guard that ``_to_bool`` has.

- **Series-vectorized bool coercion.** ``calibration.py``'s ``_as_bool``
  (line 45), whose docstring documents a real bug class it exists to fix: a
  bare ``series.astype(bool)`` on an *object-dtype* column (e.g. a bool
  column that picked up a ``NaN`` and got silently upcast to ``object``)
  coerces the *strings* ``"True"``/``"False"`` both to Python ``True``,
  silently inverting a strict filter. ``_as_bool`` normalizes explicitly
  (``.astype(str).str.strip().str.lower().isin(...)``) instead of trusting
  pandas dtype inference. This is the stricter, more defensive of the two
  bool-coercion styles, so it is the one made canonical here (``as_bool``);
  ``to_bool`` (the scalar form) mirrors the same token set for consistency.

- **Float coercion.** ``build_target_cards.py``'s ``_to_float`` (line 256)
  and ``readiness_engine.py``'s ``_num`` (line 70). They are not
  byte-identical: ``_to_float`` stringifies before parsing
  (``float(str(v).strip())``), while ``_num`` calls ``float(value)``
  directly. For ordinary numeric strings both behave the same in practice
  (Python's ``float()`` constructor already strips surrounding whitespace on
  its own), but they diverge on Python ``bool`` values: ``_num(True) ==
  1.0`` (because ``bool`` is an ``int`` subclass and ``float()`` accepts it
  directly), whereas ``_to_float(True)`` is ``nan`` (because
  ``str(True) == "True"`` does not parse as a float). ``_to_float``'s
  behavior is treated as canonical here: a stray Python ``bool`` flowing
  into a numeric card field (grade, correlation, count) is almost certainly
  a data bug, and silently reinterpreting it as ``1.0``/``0.0`` would mask
  that bug in the same way the ``_as_bool`` docstring above describes for
  bool coercion. Every existing call site of ``_num`` in
  ``readiness_engine.py`` passes a numeric card column (statistical grade,
  a correlation, a gene count) and never a literal bool, so adopting
  ``_to_float``'s behavior is not an observable behavior change for any
  current caller -- see ``docs/next_phases_plan.md`` "Phase 1" and the
  ``grep`` audit referenced there.

Every original module still exposes its own name (``build_target_cards._to_bool``,
``build_target_cards._to_float``, ``calibration._as_bool``,
``readiness_engine._num``) as a backward-compatible re-export of this
module's implementation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = ["to_bool", "to_float", "as_bool"]

_TRUE_TOKENS = {"true", "1", "yes", "y", "t"}


def to_bool(v: object) -> bool:
    """Scalar bool coercion: real bools pass through; ``None``/NaN -> ``False``;
    otherwise stringified, stripped, lower-cased, and matched against a small
    truthy-token set (``true``/``1``/``yes``/``y``/``t``).
    """
    if isinstance(v, bool):
        return v
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return False
    s = str(v).strip().lower()
    return s in _TRUE_TOKENS


def to_float(v: object) -> float:
    """Scalar float coercion; ``NaN`` on anything that doesn't parse (never raises).

    Stringifies before parsing, so a stray ``bool`` (``str(True) ==
    "True"``) does not silently become ``1.0``/``0.0`` -- see module
    docstring.
    """
    try:
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return np.nan
        return float(str(v).strip())
    except (TypeError, ValueError):
        return np.nan


def as_bool(series: pd.Series) -> pd.Series:
    """Robust string/int/bool -> bool, independent of pandas dtype inference.

    See module docstring: guards against object-dtype columns where a bare
    ``series.astype(bool)`` would silently coerce the strings "True"/"False"
    both to ``True``.
    """
    return series.astype(str).str.strip().str.lower().isin(_TRUE_TOKENS)
