"""Backward-compatibility shim (architecture refactor Phase 2).

The real implementation was split into ``core/cards.py`` (card assembly),
``core/kd_status.py`` (knockdown-status classification), and
``core/scoring.py`` (statistical-evidence-grade scoring) -- see
``docs/architecture_refactor_plan.md`` §3/§5. This module re-exports all
three under the original flat import path (``from build_target_cards import
X``) so existing callers -- notably ``tests/`` (``build_cards_frame``,
``KD_NOT_MEASURABLE_EXPRESSION_FLOOR``, ``adapt_generic_de``, ...),
``calibration.py`` (``POSITIVE_CONTROLS``), and ``target_card_api.py`` --
keep working unchanged. Prefer importing from ``core.cards``/
``core.kd_status``/``core.scoring`` directly in new code.
"""

from __future__ import annotations

from core.cards import *  # noqa: F401,F403
from core.cards import (  # noqa: F401
    BENCHMARK_CSV_DEFAULT,
    CLINICAL_BENCHMARK_KEYWORDS,
    DRUGGABLE_CLASS_MODALITY,
    GENE_LISTS_DIR_DEFAULT,
    GENERIC_TARGET_FIELDS,
    IMMUNE_EFFECTOR_CSV_DEFAULT,
    PATHWAY_AXIS_HINTS,
    POSITIVE_CONTROLS,
    _build_cards,
    _build_guide_summary,
    _clinical_axis,
    _druggable_class_for,
    _first_match_in_benchmark,
    _kd_status,
    _load_benchmark,
    _make_score,
    _normalize_cols,
    _pathway_axis,
    _safe_split_tokens,
    _score_cap_reasons,
    _to_bool,
    _to_float,
    adapt_generic_de,
    annotate_local_overlays,
    build_cards_frame,
    build_parser,
    confounded_conditions,
    load_druggable_overlays,
    load_gene_set,
    load_immune_effector_map,
    main,
)
from core.kd_status import KD_NOT_MEASURABLE_EXPRESSION_FLOOR, KD_THRESHOLD_VERSION  # noqa: F401

# api/app.py's _run_script() invokes this shim as `python build_target_cards.py
# --de-stats ... --output ...` in a fresh subprocess (never core/cards.py
# directly -- see DEFAULT_BUILD_SCRIPT's comment in api/app.py for why). This
# guard preserves that CLI entrypoint exactly as it worked before the Phase 2
# split.
if __name__ == "__main__":
    main()
