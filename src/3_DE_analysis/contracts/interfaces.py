"""Protocol interfaces at the "safe swap" seams (architecture refactor Phase 3, §4.2②).

These are structural (``typing.Protocol``) interfaces, not a class
hierarchy -- any object with matching methods satisfies them, including the
existing plain-function/plain-class implementations already in this repo
(``core.readiness.compute_readiness``, ``evidence.external_cache``'s module
functions, ``resolve.resolver.GeneResolver``). Nothing in this repo is
required to subclass these; they exist so a call site can declare "I need
something shaped like X" without importing the concrete module that
happens to implement X today, and so a future alternate implementation
(a different scorer, a mocked evidence source for tests, a swapped-in
resolver) can be typed-checked as a drop-in without touching callers.

Only defined at the three seams that actually need to be swappable per the
plan doc (evidence, scoring/readiness, gene resolution) -- not on every
function, per §6's explicit "avoid over-engineering" guardrail.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class EvidenceProvider(Protocol):
    """Something that can look up a pre-fetched external-evidence snapshot for a gene.

    Matches ``evidence.external_cache.load_snapshot`` bound to a fixed cache
    directory (e.g. ``functools.partial(load_snapshot, EVIDENCE_CACHE_DIR)``),
    and is exactly the shape ``core.readiness.compute_readiness``'s
    ``evidence_lookup`` parameter expects. Must never raise on a missing
    snapshot -- return ``None`` instead (honest-fallback contract, see
    ``docs/data_governance_checklist.md``).
    """

    def __call__(self, gene: str) -> Optional[Dict[str, Any]]: ...


@runtime_checkable
class ReadinessEngine(Protocol):
    """Something that turns target cards (+ optional evidence/overlays) into
    readiness calls -- the shape of ``core.readiness.compute_readiness``.

    Any alternate scoring/readiness implementation that returns a DataFrame
    satisfying ``contracts.readiness_schema`` (a real scorer swap, or a
    fixture-backed mock for tests) is a drop-in for
    ``core.readiness.compute_readiness`` from every caller's point of view,
    without importing ``core.readiness`` directly to type-check against it.
    """

    def __call__(
        self,
        cards: pd.DataFrame,
        overlays: Optional[Dict[str, Any]] = None,
        essentials: Optional[Any] = None,
        broad_effect_genes: Optional[Any] = None,
        evidence_lookup: Optional[EvidenceProvider] = None,
        membrane_overlay: Optional[Dict[str, Any]] = None,
        gtex_overlay: Optional[Dict[str, Any]] = None,
        gnomad_overlay: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame: ...


@runtime_checkable
class GeneResolver(Protocol):
    """Something that resolves a gene query (symbol/alias/Ensembl id) to a
    canonical identity -- the public surface of
    ``resolve.resolver.GeneResolver``.

    Declared so ``resolve.search``/the API's gene endpoints can depend on
    "a resolver shaped like this" rather than importing the concrete
    ``resolve.resolver.GeneResolver`` class purely for typing.
    """

    def resolve(self, query: str) -> Dict[str, Any]: ...

    def resolve_many(self, queries: List[str]) -> List[Dict[str, Any]]: ...

    def canonical_symbols(self) -> Dict[str, str]: ...

    def alias_symbols(self) -> Dict[str, str]: ...

    def canonical_symbol_for(self, gene_id: str) -> Optional[str]: ...
