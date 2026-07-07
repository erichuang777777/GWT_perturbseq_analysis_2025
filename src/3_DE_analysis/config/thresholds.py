"""Numeric gates: the single source of truth for every scoring/QC threshold.

Before this module existed, the cross-donor/cross-guide correlation gates
(0.2 and 0.3) were independently hardcoded in THREE files --
``build_target_cards.py`` (``_make_score``, ``_score_cap_reasons``,
``replicate_pass_flag``, ``batch_sensitivity_flag``), ``calibration.py``
(``rank_stability``, ``qc_funnel``), and ``readiness_engine.py``
(``_translation``) -- a real risk flagged in code review: tuning one copy
and missing another silently desynchronizes the card grade, the calibration
report, and the readiness score. They now all read from here.

Values are unchanged from what was already in use; this is a pure
consolidation, not a recalibration.
"""

from __future__ import annotations

# --- Card-building gates (build_target_cards.py) ----------------------------------
MIN_CELLS_DEFAULT = 200
MIN_DE_GENES_DEFAULT = 50

# Minimum acceptable cross-donor / cross-guide correlation for a row to count
# as "replicated" at all (grade >=2 / replicate_pass_flag).
CROSSDONOR_MIN = 0.2
CROSSGUIDE_MIN = 0.2

# Stricter bar for the highest grade (4) and for "confounded_but_robust"
# batch-sensitivity classification.
CROSSDONOR_ROBUST = 0.3
CROSSGUIDE_ROBUST = 0.3

# Guide-level knockdown-confirmation gate (grade 3/4, kd_status="confirmed").
GUIDE_SIGNIF_RATIO_MIN = 0.5
GUIDE_FDR_MAX_CONFIRMED = 0.05
GUIDE_FDR_MAX_GRADE3 = 0.1

# Minimum guides for grade 3/4.
N_GUIDES_MIN_HIGH_GRADE = 2

# --- kd_status (three measured states + not_assessed) -----------------------------
# Per metadata/data_sharing_readme.md's documented definition of
# high_confidence_no_effect_guides: "target expression in NTCs > 0.001" is the
# repo's own stated floor for whether knockdown is assessable at all.
# (The version tag for this threshold logic, KD_THRESHOLD_VERSION, lives in
# config/versions.py alongside the other version strings, not here.)
KD_NOT_MEASURABLE_EXPRESSION_FLOOR = 0.001

# --- Evidence cache TTL (external_evidence_cache.py) -------------------------------
EVIDENCE_TTL_SECONDS_DEFAULT = 30 * 24 * 3600  # 30 days; external evidence changes slowly

# --- Upload API limits (target_card_api.py) ----------------------------------------
MAX_EVIDENCE_GENES_PER_BUILD = 50
