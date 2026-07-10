"""Unit tests for the shared frontend chip primitives (FE-3).

These lock the `unknown != 0` invariant at the pure-function level: an unknown /
unchecked field must render as the grey 「未檢查」chip, while a MEASURED value
(including a real 0 or the string "none") must NOT be greyed out. Also covers
`format_concept_chips`, which must never raise on odd inputs.

The chip module lives in the isolated frontend package (`frontend/dashboard`),
which is not on the default import path, so we add it here.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dashboard"
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

import ui_chips  # noqa: E402


def test_is_unknown_none_and_token():
    assert ui_chips.is_unknown(None) is True
    assert ui_chips.is_unknown("unknown") is True
    assert ui_chips.is_unknown("UNKNOWN") is True
    assert ui_chips.is_unknown(float("nan")) is True


def test_is_unknown_measured_values_are_not_unknown():
    # A real measured 0 is a verdict, not "unchecked".
    assert ui_chips.is_unknown(0) is False
    # "none" / "no_*" are measured negatives, not unknown.
    assert ui_chips.is_unknown("none") is False
    assert ui_chips.is_unknown("no_genetic_association") is False


def test_val_chip_unknown_shows_not_checked_label():
    html = ui_chips.val_chip(None)
    assert "未檢查" in html
    assert "gwt-chip--unknown" in html


def test_val_chip_measured_zero_is_not_unknown():
    html = ui_chips.val_chip(0)
    assert "未檢查" not in html
    assert "gwt-chip--value" in html
    assert ">0<" in html


def test_format_concept_chips_list_of_dicts():
    assert ui_chips.format_concept_chips([{"module_id": "M02"}]) == "M02"
    assert (
        ui_chips.format_concept_chips([{"module_id": "M02"}, {"module_id": "M07"}])
        == "M02, M07"
    )


def test_format_concept_chips_list_of_str():
    assert ui_chips.format_concept_chips(["M01", "M02"]) == "M01, M02"


def test_format_concept_chips_none_is_empty():
    assert ui_chips.format_concept_chips(None) == ""


def test_format_concept_chips_non_list_does_not_raise():
    assert ui_chips.format_concept_chips("x") == ""
    assert ui_chips.format_concept_chips(42) == ""
    assert ui_chips.format_concept_chips({"module_id": "M02"}) == ""


def test_age_label_fresh_timestamp_no_staleness_warning():
    fresh = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    label = ui_chips.age_label(fresh)
    assert label is not None
    assert "⚠" not in label
    assert "1 天前" in label or "0 天前" in label


def test_age_label_stale_timestamp_past_ttl_shows_warning():
    """Wave 1d (docs/ux_trust_fix_plan.md): evidence older than the external-
    cache's own re-fetch TTL must be flagged, not shown identically to fresh
    data with only a raw timestamp."""
    stale = (datetime.now(timezone.utc) - timedelta(days=ui_chips.STALE_TTL_DAYS + 10)).isoformat().replace("+00:00", "Z")
    label = ui_chips.age_label(stale)
    assert label is not None
    assert "⚠" in label
    assert "過期" in label


def test_age_label_non_timestamp_placeholder_is_unparseable():
    assert ui_chips.age_label("SAMPLE — not computed from live data") is None


def test_age_label_dated_sample_fixture_is_still_correctly_flagged_stale():
    """A sample fixture that DOES carry a real (if old) ISO timestamp with a
    ' (SAMPLE)' suffix -- e.g. 'concept_waterfall.py's SAMPLE_REPORT dates --
    must still be parsed and flagged, not silently ignored just because it's
    a fixture. Old-and-unflagged is exactly the blind spot this fix closes."""
    label = ui_chips.age_label("2025-10-20T00:00:00Z (SAMPLE)")
    assert label is not None
    assert "⚠" in label


def test_age_label_none_and_unknown_do_not_raise():
    assert ui_chips.age_label(None) is None
    assert ui_chips.age_label("unknown") is None
    assert ui_chips.age_label(42) is None
