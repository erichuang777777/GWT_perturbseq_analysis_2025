"""Version strings: the single source of truth for the four-layer versioning contract (B4).

See ``docs/cache_and_versioning_policy.md`` for what each layer means and
when to bump it. Previously ``ENGINE_VERSION``/``DATASET_VERSION``/
``CARD_SCHEMA_VERSION`` lived in ``target_card_api.py`` and
``KD_THRESHOLD_VERSION`` lived in ``build_target_cards.py``; both still
re-export from here.
"""

from __future__ import annotations

# Bump whenever build_target_cards.py, readiness_engine.py, calibration.py, or
# external_evidence_cache.py change scoring/engine behavior, so every dataset's
# provenance footer can say exactly which engine produced it.
ENGINE_VERSION = "1.3.0"

# Which upstream GWT dataset release this toolkit's local CSVs correspond to.
# Distinct from ENGINE_VERSION (this toolkit's own scoring logic) -- bump only
# when the underlying DE_stats/guide_kd/sgrna_library upstream release changes.
DATASET_VERSION = "gwt_marson2025/bioRxiv-10.64898-2025.12.23.696273v1"

# The target_cards.csv COLUMN CONTRACT itself, independent of engine scoring
# logic. Bump when contracts/card_schema.py's CARD_COLUMNS adds/removes/renames
# a column, so a consumer can tell whether its column-name assumptions still
# hold. v1 = the original 24-column spec; v2 = + druggable_class/
# tractability_modality/safety_note, kd_status/kd_threshold_version/
# target_baseline_expression, condition_specificity_zscore,
# effect_direction_flip_flag.
CARD_SCHEMA_VERSION = "card_schema/v2"

# kd_status threshold-logic version (config/thresholds.py). v2 split the
# never-measured NaN-baseline case into "not_assessed", distinct from the
# measured-below-floor "not_measurable" (see docs/de_and_baseline_spec.md).
KD_THRESHOLD_VERSION = "kd_status/v2"
