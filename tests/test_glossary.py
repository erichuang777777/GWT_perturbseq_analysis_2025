"""Unit tests for the glossary module (Wave 1a, docs/ux_trust_fix_plan.md).

Pure-Python content checks: the glossary must cover every literal
``readiness_call`` value the engine can emit (``core.readiness.CALL_ORDER``)
plus ``grade``, and every entry must carry both a "what it means" and a
"what it does NOT mean" line -- an entry with only a definition and no
correction would defeat the whole point of this fix.
"""

from __future__ import annotations

import sys
from pathlib import Path

DASH = Path(__file__).resolve().parent.parent / "frontend" / "dashboard"
SRC = Path(__file__).resolve().parent.parent / "src" / "3_DE_analysis"
if str(DASH) not in sys.path:
    sys.path.insert(0, str(DASH))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from glossary import GLOSSARY, GLOSSARY_ORDER  # noqa: E402


def test_glossary_covers_every_readiness_call():
    from core.readiness import CALL_ORDER

    for call in CALL_ORDER:
        assert call in GLOSSARY, f"glossary is missing an entry for readiness_call={call!r}"


def test_glossary_covers_grade():
    assert "grade" in GLOSSARY


def test_every_entry_has_a_definition_and_a_correction():
    for key, entry in GLOSSARY.items():
        assert entry.get("means", "").strip(), f"{key} has no 'means' line"
        assert entry.get("not_mean", "").strip(), f"{key} has no 'not_mean' line -- glossary must say what it does NOT mean"
        assert entry.get("label", "").strip()


def test_glossary_order_matches_glossary_keys():
    assert set(GLOSSARY_ORDER) == set(GLOSSARY.keys())
