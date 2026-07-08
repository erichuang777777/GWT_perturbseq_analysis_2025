"""Backward-compatibility shim (architecture refactor Phase 2).

The real implementation moved to ``evidence/disease.py`` (see
``docs/architecture_refactor_plan.md`` §3/§5). This module re-exports it
under the original flat import path (``from disease_translator import X``)
so existing callers -- notably ``target_card_api.py`` -- keep working
unchanged. Prefer importing from ``evidence.disease`` directly in new code.
"""

from __future__ import annotations

from evidence.disease import *  # noqa: F401,F403
from evidence.disease import (  # noqa: F401
    DEFAULT_ASSOCIATIONS_PATH,
    list_diseases,
    load_disease_associations,
    translate_disease,
)
