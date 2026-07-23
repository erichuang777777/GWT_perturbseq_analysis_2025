"""Tests for the ported readiness faithfulness self-check (Predictability Audit #261).

Also guards that the ported cap table stays in sync with core/readiness.py.
"""

from __future__ import annotations

import readiness_selfcheck as rs


def test_cap_from_red_flags():
    assert rs.cap_from_red_flags([]) == "advance"
    assert rs.cap_from_red_flags(["kd_weak"]) == "validate"
    assert rs.cap_from_red_flags(["essential_gene"]) == "watchlist"
    # most restrictive wins
    assert rs.cap_from_red_flags(["kd_weak", "broad_effect"]) == "watchlist"


def test_selfcheck_flags_inconsistent_call():
    # advance while carrying an essential_gene flag is internally inconsistent
    bad = rs.selfcheck_call("advance", ["essential_gene"])
    assert bad["consistent"] is False and "essential_gene" in bad["violated_flags"]
    # validate with only a validate-cap flag is consistent
    ok = rs.selfcheck_call("validate", ["uncertain_direction"])
    assert ok["consistent"] is True
    # a more restrictive call than the cap is fine (deprioritize <= any cap)
    assert rs.selfcheck_call("deprioritize", ["kd_weak"])["consistent"] is True
    # unknown call -> not evaluable (unknown != 0)
    assert rs.selfcheck_call("bogus", [])["consistent"] is None


def test_audit_calls_batch():
    rows = [
        {"target": "A", "call": "advance", "red_flags": []},               # ok
        {"target": "B", "call": "advance", "red_flags": ["broad_effect"]},  # inconsistent
        {"target": "C", "call": "watchlist", "red_flags": ["broad_effect"]},# ok
    ]
    out = rs.audit_calls(rows)
    assert out["n_evaluated"] == 3 and out["n_inconsistent"] == 1
    assert out["all_consistent"] is False
    assert out["inconsistent"][0]["target"] == "B"


def test_caps_in_sync_with_readiness_engine():
    # The ported RED_FLAG_CAP must match core/readiness.py's _red_flags caps exactly.
    import inspect
    from core import readiness as core_readiness

    src = inspect.getsource(core_readiness._red_flags)
    for flag, cap in rs.RED_FLAG_CAP.items():
        assert f'"{flag}"' in src, f"{flag} not found in core _red_flags"
        # the cap call appears near the flag append
        assert f'CALL_ORDER.index("{cap}")' in src
