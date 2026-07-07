"""Single source of truth for the "typed unavailable" degradation wrapper (architecture refactor Phase 1).

Every optional/fragile data source in this codebase follows the same
honest-fallback contract: on a missing file, a malformed file, a missing
network dependency, or a request failure, return an explicit typed result
that says "this source is unavailable, here's why, and here's an
empty-but-correctly-shaped placeholder" -- never raise, and never silently
fabricate a value. Before this module existed, four files each hand-built
that same shape independently, in two slightly different flavors:

- **"available" + a named data key** -- ``cre_schema.py``'s
  ``load_cre_elements``/``load_variant_cre_links`` (lines 57/61/67/71:
  ``{"available": False, "reason": ..., "elements"|"links": empty_table}``)
  and ``safety_overlay.py``'s ``load_membrane_tractability_overlay``/
  ``load_gtex_safety_overlay`` (lines 84-88/92-96/114-118/122-126:
  ``{"available": False, "reason": ..., "table": empty_table}``).
- **"source_status" + "items"** -- ``external_evidence_cache.py``'s
  module-local ``_unavailable`` (line 53: ``{"source_status":
  "unavailable", "reason": ..., "items": []}``) and
  ``pathway_network_cache.py``'s module-local ``_unavailable`` (line 48,
  identical shape).

The two flavors differ in key names (``available``/``reason``/<data key> vs.
``source_status``/``reason``/``items``) and are both real, load-bearing
contracts that downstream code (``cre_for_gene``,
``tractability_from_membrane_overlay``, ``safety_window_from_gtex``, the
evidence/pathway cache readers) already pattern-matches against -- so this
module provides one small helper per flavor rather than forcing a single
rigid shape onto both.

``external_evidence_cache._unavailable`` and ``pathway_network_cache._unavailable``
remain as backward-compatible re-exports (thin wrappers around
``unavailable_source``) so existing call sites are unaffected.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

__all__ = ["unavailable_available", "unavailable_source"]


def unavailable_available(reason: str, *, data_key: str, empty: Any) -> Dict[str, Any]:
    """The ``{"available": False, "reason": ..., <data_key>: <empty>}`` shape
    used by ``cre_schema.py`` (``data_key`` = ``"elements"``/``"links"``) and
    ``safety_overlay.py`` (``data_key`` = ``"table"``).
    """
    return {"available": False, "reason": reason, data_key: empty}


def unavailable_source(reason: str, *, items: Optional[List[Any]] = None) -> Dict[str, Any]:
    """The ``{"source_status": "unavailable", "reason": ..., "items": [...]}``
    shape used by ``external_evidence_cache.py`` and ``pathway_network_cache.py``.
    """
    return {"source_status": "unavailable", "reason": reason, "items": items if items is not None else []}
