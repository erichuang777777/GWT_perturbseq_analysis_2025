"""Frontend smoke tests (FE-2/FE-4).

The main dashboard needs a live API to fully render, so we compile-check it (and
the shared frontend modules) with ``ast.parse``. The target-dossier page ships
sample fallbacks, so we run it headless with Streamlit's ``AppTest`` and assert it
renders without raising -- this exercises the FE-3 chip extraction and the FE-1
deep-link seeding on a real Streamlit runtime.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

DASH = Path(__file__).resolve().parent.parent / "frontend" / "dashboard"
if str(DASH) not in sys.path:
    sys.path.insert(0, str(DASH))


def test_frontend_modules_compile():
    for f in ["target_card_dashboard.py", "ui_chips.py", "nav.py", "concept_waterfall.py"]:
        ast.parse((DASH / f).read_text(encoding="utf-8"))


def test_dossier_page_renders_offline():
    appt = pytest.importorskip("streamlit.testing.v1")
    at = appt.AppTest.from_file(str(DASH / "pages" / "2_標的檔案_target_dossier.py"), default_timeout=60)
    at.run()
    assert not at.exception, f"dossier page raised: {at.exception}"
    # the entity-centric title renders (sample-data offline path)
    assert any("Target Dossier" in t.value for t in at.title)
