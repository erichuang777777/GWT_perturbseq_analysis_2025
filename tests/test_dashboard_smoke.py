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
    for f in ["target_card_dashboard.py", "ui_chips.py", "nav.py", "concept_waterfall.py", "glossary.py"]:
        ast.parse((DASH / f).read_text(encoding="utf-8"))


def test_dossier_page_renders_offline():
    appt = pytest.importorskip("streamlit.testing.v1")
    at = appt.AppTest.from_file(str(DASH / "pages" / "2_標的檔案_target_dossier.py"), default_timeout=60)
    at.run()
    assert not at.exception, f"dossier page raised: {at.exception}"
    # the entity-centric title renders (sample-data offline path)
    assert any("Target Dossier" in t.value for t in at.title)


def test_dossier_page_shows_glossary_and_structural_limits_banner():
    """Wave 1a/1e (docs/ux_trust_fix_plan.md): once a gene is selected, the
    dossier must show (1) the glossary expander explaining what
    advance/validate/watchlist/deprioritize/grade do and do NOT mean, and (2)
    an un-hideable structural-limits banner (single screen / CD4+ / N≈3
    donors) -- both surfaced at the point where the user first sees the
    grade/call chips, not buried in docs they'll never read.
    """
    appt = pytest.importorskip("streamlit.testing.v1")
    at = appt.AppTest.from_file(str(DASH / "pages" / "2_標的檔案_target_dossier.py"), default_timeout=60)
    at.run()
    at.text_input(key="dossier_query").set_value("IL2RA").run()
    assert not at.exception, f"dossier page raised after selecting a gene: {at.exception}"

    expander_labels = [e.label for e in at.expander]
    assert any("名詞解釋" in label for label in expander_labels), "glossary expander did not render"

    caption_texts = [c.value for c in at.caption]
    assert any("CRISPRi screen" in t and "N≈3" in t for t in caption_texts), (
        "structural-limits banner did not render"
    )


def test_dossier_page_does_not_import_the_il2ra_fixture_waterfall():
    """Regression lock (blind-spot fix, Wave 0): the per-target dossier used to
    render `build_waterfall_figure(SAMPLE_REPORT.get("concept_profile", []))`
    UNCONDITIONALLY, so every gene's dossier showed the identical hardcoded
    IL2RA fixture "concept profile" -- a fixture presented as this target's
    data regardless of which gene was actually queried. `SAMPLE_REPORT`/
    `build_waterfall_figure` belong only to the explicit demo page
    (pages/1_個體概念剖面_探索demo.py). This asserts the dossier page source
    never re-imports either symbol from `concept_waterfall`.
    """
    src = (DASH / "pages" / "2_標的檔案_target_dossier.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "concept_waterfall":
            imported_names.update(alias.name for alias in node.names)
    assert "SAMPLE_REPORT" not in imported_names
    assert "build_waterfall_figure" not in imported_names
