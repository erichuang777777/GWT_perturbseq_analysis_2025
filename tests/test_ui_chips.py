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
