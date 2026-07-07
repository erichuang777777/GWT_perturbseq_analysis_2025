"""Name-keyed registry for evidence/overlay providers (architecture refactor
Phase 3, §4.2③ / §4.3③).

Deliberately minimal, per the plan doc's explicit "avoid over-engineering"
guardrail (§6): a dict of name -> zero-argument factory callable, with
``register``/``get``/``names``. Nothing here changes what a provider does or
how it degrades on failure -- each provider is still the existing honest-
fallback loader from this package; the registry only adds "swap by name"
indirection so ``config`` (or a test) can select an implementation without
every call site importing the concrete module.

Providers are registered as zero-argument factories (not the loaded value
itself) so ``get(name)()`` always re-runs the real loader -- consistent with
every existing loader's own contract of re-reading its file/table on each
call, and so a caller can override just the underlying file path (e.g. for
tests) before triggering the load.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List

_REGISTRY: Dict[str, Callable[[], Any]] = {}


def register(name: str, factory: Callable[[], Any]) -> None:
    """Register (or replace) a provider factory under ``name``."""
    _REGISTRY[name] = factory


def get(name: str) -> Callable[[], Any]:
    """Return the factory registered under ``name``.

    Raises ``KeyError`` with the list of known names if ``name`` was never
    registered -- a programming-time error (wrong config value), not a
    runtime data-availability question (that's what each provider's own
    ``available``/``source_status`` honest-fallback field is for).
    """
    if name not in _REGISTRY:
        raise KeyError(f"no evidence/overlay provider registered as {name!r}; known: {sorted(_REGISTRY)}")
    return _REGISTRY[name]


def names() -> List[str]:
    return sorted(_REGISTRY)


def _register_defaults() -> None:
    """Register this package's own providers under their default names.

    Called once at import time (idempotent -- re-registering just replaces
    the entry with the same factory). Kept as a separate function so tests
    can call it again after mutating the registry to restore defaults.
    """
    from evidence.external_cache import build_evidence_for_gene  # noqa: F401 (documents intended factory shape)
    from evidence.population import load_burden_estimates
    from evidence.safety_overlay import (
        load_gnomad_constraint_overlay,
        load_gtex_safety_overlay,
        load_membrane_tractability_overlay,
    )

    register("membrane_tractability", load_membrane_tractability_overlay)
    register("gtex_safety_window", load_gtex_safety_overlay)
    register("gnomad_constraint", load_gnomad_constraint_overlay)
    register("population_burden_lymphocyte_count", load_burden_estimates)


_register_defaults()
