"""Backward-compatibility shim (architecture refactor Phase 2).

The real implementation moved to ``upload/import_manager.py`` (see
``docs/architecture_refactor_plan.md`` §3/§5). This module re-exports it
under the original flat import path (``from import_manager import X``) so
existing callers -- notably ``tests/test_empty_states.py`` and
``target_card_api.py`` -- keep working unchanged. Prefer importing from
``upload.import_manager`` directly in new code.
"""

from __future__ import annotations

from upload.import_manager import *  # noqa: F401,F403
from upload.import_manager import (  # noqa: F401
    ImportPayload,
    apply_and_validate_mapping,
    approve_import,
    build_mapped_view,
    canonical_fields,
    context_match_score,
    duplicate_normalized_columns,
    ensure_valid_declared_type,
    infer_source_type,
    is_within_allowed_roots,
    list_imports,
    mark_merged,
    normalize_columns,
    read_import,
    read_preview,
    read_table_preview,
    register_import,
    safe_name,
    suggested_mapping,
    utc_now,
    validate_schema,
    value_text,
    write_payload_file,
)
