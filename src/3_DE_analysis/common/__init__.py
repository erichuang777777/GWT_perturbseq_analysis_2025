"""Shared, dependency-free helpers used across module boundaries (architecture refactor Phase 1).

Before this package existed, several small helpers -- a UTC timestamp
function, scalar/Series bool and float coercion, and an "unavailable"
degradation wrapper -- were each reimplemented independently in multiple
modules (three copies of the timestamp helper alone; see
``docs/next_phases_plan.md`` "Phase 1 -- 抽 common/" and
``docs/architecture_refactor_plan.md`` §3). Every original module still
exposes its own name for backward compatibility, but now re-exports the
single implementation here instead of defining it independently, so there is
exactly one place to fix a bug or extend the behavior.

This package is additive only: importing it does not change any computed
value or behavior. It has no dependency on any other package in
``src/3_DE_analysis`` (only ``numpy``/``pandas``/stdlib), consistent with
being the innermost layer in the "dependency always points inward"
principle (``docs/architecture_refactor_plan.md`` §2) -- ``core``, ``data``,
``resolve``, ``evidence``, ``report``, and ``api`` may all depend on
``common``, but ``common`` depends on none of them.

Submodules:
- ``coerce``: scalar/Series bool and float coercion (``to_bool``, ``to_float``, ``as_bool``).
- ``timeutil``: UTC timestamp helper (``utc_now``).
- ``degrade``: typed "unavailable" degradation wrapper(s) (``unavailable_available``, ``unavailable_source``).
"""

from __future__ import annotations

from . import coerce, degrade, timeutil

__all__ = ["coerce", "degrade", "timeutil"]
