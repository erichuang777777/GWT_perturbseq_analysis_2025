"""Single source of truth for the UTC timestamp helper (architecture refactor Phase 1).

Before this module existed, the same one-line implementation --
``datetime.now(timezone.utc).isoformat()`` -- was defined independently three
times: ``utc_now()`` in ``import_manager.py`` (used for ``created_at``/
``approved_at``/``merged_at`` import metadata), ``_now()`` in
``external_evidence_cache.py`` (used for ``fetched_at`` on evidence
snapshots), and ``_now()`` in ``pathway_network_cache.py`` (used for
``fetched_at`` on pathway/network snapshots). All three were byte-identical.
Parallel-session development kept re-adding a new copy rather than importing
a shared one (see ``docs/next_phases_plan.md`` "Phase 1 -- 抽 common/").

Every original module still exposes its own name (``import_manager.utc_now``,
``external_evidence_cache._now``, ``pathway_network_cache._now``) as a
backward-compatible re-export of this implementation, so existing imports
and call sites are unaffected.
"""

from __future__ import annotations

from datetime import datetime, timezone

__all__ = ["utc_now"]


def utc_now() -> str:
    """Current UTC time as an ISO-8601 string (e.g. for ``fetched_at``/``created_at`` fields)."""
    return datetime.now(timezone.utc).isoformat()
