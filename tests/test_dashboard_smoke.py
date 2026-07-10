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


def test_discovery_tables_link_to_the_target_dossier_not_dead_ends():
    """UX-flow fix (docs/ux_flow_stepwise_plan.md, Step 2/3): Disease Translator's
    two tables and Pathway+Clinical's module-hit table used to render with plain
    `st.dataframe(...)` -- a dead end, since selecting a row did not offer any
    path to that target's full dossier. `整合 Triage` and `免疫優先` already used
    the shared `_selectable_table_with_dossier_link` helper; this locks the other
    three tables onto the same helper so a clinician using Disease Translator (a
    likely first entry point) is never stuck re-typing the gene symbol elsewhere.
    """
    src = (DASH / "target_card_dashboard.py").read_text(encoding="utf-8")

    disease_start = src.index("def render_disease()")
    disease_end = src.index("def render_immune_priority()")
    disease_body = src[disease_start:disease_end]
    assert '_selectable_table_with_dossier_link(disease_df' in disease_body
    assert '_selectable_table_with_dossier_link(ds_df' in disease_body
    assert "st.dataframe(disease_df" not in disease_body
    assert "st.dataframe(ds_df" not in disease_body

    pathway_start = src.index("def render_pathway_clinical()")
    pathway_end = src.index("def render_imports()")
    pathway_body = src[pathway_start:pathway_end]
    assert "_selectable_table_with_dossier_link(module_df" in pathway_body
    assert "st.dataframe(module_df" not in pathway_body


def test_target_explorer_deep_links_instead_of_duplicating_the_dossier():
    """UX-flow fix (docs/ux_flow_stepwise_plan.md, Step 3): Target Explorer used
    to carry its own inline Readiness / External-evidence / Evidence-graph
    section -- a second, independently-maintained "single target" view that had
    already drifted from the real Target Dossier page (raw `st.metric(...,
    "NA")` instead of `unknown != 0` chip treatment, no glossary, no
    quick-answer headline). This locks in its removal: `render_target_explorer`
    must deep-link to the dossier instead of rendering its own copy, and the
    now-dead `_evidence`/`_evidence_graph` helpers it alone used must not
    reappear.
    """
    src = (DASH / "target_card_dashboard.py").read_text(encoding="utf-8")

    explorer_start = src.index("def render_target_explorer()")
    explorer_end = src.index("def render_pathway_clinical()")
    explorer_body = src[explorer_start:explorer_end]
    assert "st.switch_page(\"pages/2_標的檔案_target_dossier.py\")" in explorer_body
    assert "st.graphviz_chart(" not in explorer_body
    assert "External evidence" not in explorer_body

    assert "def _evidence(" not in src
    assert "def _evidence_graph(" not in src


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

    # Order check: the headline markdown must appear BEFORE the raw statistical
    # evidence section (now ⑥, see test_dossier_sections_ordered_for_both_personas_below
    # for the full post-Step-4 order) in source order, so it isn't just present
    # but actually promoted above the evidence walkthrough (the whole point of
    # this fix).
    src = (DASH / "pages" / "2_標的檔案_target_dossier.py").read_text(encoding="utf-8")
    headline_pos = src.index("快速結論")
    section2_pos = src.index("GWT 篩選證據")
    assert headline_pos < section2_pos, "quick-answer headline must be placed before the GWT evidence section"


def test_dossier_sections_ordered_for_both_personas():
    """UX-flow fix (docs/ux_flow_stepwise_plan.md, Step 4): the per-target
    dossier's detail sections used to run in IMPLEMENTATION order (raw stats
    first, decision-relevant content like external evidence/safety last) --
    a clinician had to scroll past statistics/concept-profile/mechanism-graph
    detail to reach the content they actually needed. This locks in the
    re-ordered, persona-oriented sequence: quick-glance descriptive summary,
    then the clinically-relevant sections (external evidence, safety,
    tractability), THEN the statistics/mechanism detail a researcher audits,
    with the full readiness-call breakdown last before the provenance footer.
    Every section is independently fetched (verified when reordering: none
    reads a variable computed by another section), so this is a pure
    presentation-order change with no behavioural risk.
    """
    src = (DASH / "pages" / "2_標的檔案_target_dossier.py").read_text(encoding="utf-8")
    expected_order = [
        "① 搜尋 / 選擇標的",
        "② 多軸描述性摘要",
        "③ 外部證據",
        "④ 安全性與遺傳學",
        "⑤ 成藥性",
        "⑥ GWT 篩選證據",
        "⑦ CD4 概念剖面",
        "⑧ 機制圖",
        "⑨ Readiness 判定",
    ]
    positions = [src.index(label) for label in expected_order]
    assert positions == sorted(positions), (
        f"dossier sections are out of the expected persona-oriented order: {expected_order}"
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
