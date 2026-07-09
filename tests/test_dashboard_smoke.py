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


def test_overview_tab_has_persona_wayfinding_note():
    """UX-flow fix: `render_overview()` (the very first thing anyone sees) must
    point a clinician and a researcher at which tab to open first, and explain
    how to reach the per-target dossier deep-link. `target_card_dashboard.py`
    needs a live API to fully render (see module docstring), so this is a
    source-text check rather than an AppTest render, consistent with
    `test_frontend_modules_compile` above.
    """
    src = (DASH / "target_card_dashboard.py").read_text(encoding="utf-8")
    overview_start = src.index("def render_overview()")
    overview_body = src[overview_start : overview_start + 1500]
    assert "臨床醫師" in overview_body
    assert "研究者" in overview_body
    assert "整合 Triage" in overview_body


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


def test_dossier_page_shows_quick_answer_headline_before_the_evidence_walkthrough():
    """UX-flow fix (/goal: optimize the sequence for a biomedical researcher and
    a clinician so the right information is found fast). Previously the
    readiness_call + next_validation_step only appeared at the very BOTTOM of
    the page (section 8), after 6 sections of raw statistics/concept/mechanism
    detail -- a clinician had to scroll past all of that for the one-line
    answer, and a researcher had to scroll the same distance for the
    recommended next experiment. This asserts the headline (same values, no
    new computation) now renders right after the header, before section 2's
    subheader appears in the underlying markdown order.
    """
    appt = pytest.importorskip("streamlit.testing.v1")
    at = appt.AppTest.from_file(str(DASH / "pages" / "2_標的檔案_target_dossier.py"), default_timeout=60)
    at.run()
    at.text_input(key="dossier_query").set_value("IL2RA").run()
    assert not at.exception, f"dossier page raised after selecting a gene: {at.exception}"

    markdown_texts = [m.value for m in at.markdown]
    assert any("快速結論" in t for t in markdown_texts), "quick-answer headline did not render"

    success_texts = [s.value for s in at.success]
    assert any("下一步驗證" in t for t in success_texts), "next_validation_step preview did not render in the headline"

    caption_texts = [c.value for c in at.caption]
    assert any("臨床醫師快速路徑" in t for t in caption_texts), "clinician routing pointer did not render"
    assert any("研究者快速路徑" in t for t in caption_texts), "researcher routing pointer did not render"

    # Order check: the headline markdown must appear BEFORE section ②'s
    # subheader in source order, so it isn't just present but actually promoted
    # above the evidence walkthrough (the whole point of this fix).
    src = (DASH / "pages" / "2_標的檔案_target_dossier.py").read_text(encoding="utf-8")
    headline_pos = src.index("快速結論")
    section2_pos = src.index("GWT 篩選證據")
    assert headline_pos < section2_pos, "quick-answer headline must be placed before the GWT evidence section"


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
