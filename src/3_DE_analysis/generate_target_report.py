"""Backward-compatibility shim (architecture refactor Phase 2).

The real implementation moved to ``report/generate.py`` (see
``docs/architecture_refactor_plan.md`` §3/§5). This module re-exports it
under the original flat import path (``from generate_target_report import
X``) so existing callers -- notably ``target_card_api.py`` -- keep working
unchanged. Prefer importing from ``report.generate`` directly in new code.
"""

from __future__ import annotations

from report.generate import *  # noqa: F401,F403
from report.generate import (  # noqa: F401
    CORE_COLUMNS,
    build_report_payload,
    build_target_report_payload,
    normalize_cards,
    render_html,
    render_markdown,
    render_target_html,
    write_report,
)
