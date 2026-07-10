"""Frontend smoke tests for the persona-split dashboard (docs/frontend_design.md).

Every former ``st.tabs(...)`` body in ``target_card_dashboard.py`` is now its
own standalone page under ``pages/`` (01-10 researcher, 11-13 clinical-
evidence); ``target_card_dashboard.py`` itself is now a pure landing page
with a persona picker. Researcher pages need a live API to fully render past
their sidebar dataset picker, so we compile-check them (and the shared
modules) with ``ast.parse`` and additionally drive them far enough via
Streamlit's ``AppTest`` to confirm they degrade gracefully (an honest
``st.stop()``, never an exception) when no dataset/live API is available.
The target-dossier page and the clinical-evidence pages ship SAMPLE
fallbacks and are exercised further.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

DASH = Path(__file__).resolve().parent.parent / "frontend" / "dashboard"
PAGES = DASH / "pages"
if str(DASH) not in sys.path:
    sys.path.insert(0, str(DASH))

DOSSIER_PAGE = "08_研究者_標的檔案_target_dossier.py"

RESEARCHER_PAGES = [
    "01_研究者_總覽_overview.py",
    "02_研究者_整合Triage.py",
    "03_研究者_免疫優先.py",
    "04_研究者_標的探索_target_explorer.py",
    "05_研究者_疾病標的翻譯.py",
    "06_研究者_通路與模組.py",
    "07_研究者_校準與穩健性.py",
    DOSSIER_PAGE,
    "09_研究者_資料集上傳合併.py",
    "10_研究者_匯出.py",
]
CLINICAL_PAGES = [
    "11_臨床證據_個體概念剖面.py",
    "12_臨床證據_疾病藥物證據配對.py",
    "13_臨床證據_群體遺傳查詢.py",
]
ALL_PAGES = RESEARCHER_PAGES + CLINICAL_PAGES


def test_frontend_modules_compile():
    shared_modules = [
        "target_card_dashboard.py",
        "api_client.py",
        "dataset_context.py",
        "guardrails.py",
        "ui_chips.py",
        "nav.py",
        "concept_waterfall.py",
        "glossary.py",
    ]
    for f in shared_modules:
        ast.parse((DASH / f).read_text(encoding="utf-8"))
    for f in ALL_PAGES:
        ast.parse((PAGES / f).read_text(encoding="utf-8"))


def test_dossier_page_path_constant_matches_an_actual_file():
    """Regression lock: api_client.DOSSIER_PAGE_PATH is the single source of
    truth every deep-link (`_selectable_table_with_dossier_link`, Target
    Explorer's direct switch_page) points at. If the dossier page is ever
    renamed again without updating this constant, every deep-link silently
    breaks -- this catches that at test time instead of in a live app.
    """
    from api_client import DOSSIER_PAGE_PATH

    assert DOSSIER_PAGE_PATH == f"pages/{DOSSIER_PAGE}"
    assert (PAGES / DOSSIER_PAGE).exists()


def test_landing_page_offers_persona_picker():
    appt = pytest.importorskip("streamlit.testing.v1")
    at = appt.AppTest.from_file(str(DASH / "target_card_dashboard.py"), default_timeout=60)
    at.run()
    assert not at.exception, f"landing page raised: {at.exception}"
    assert any("GWT Target Evidence Browser" in t.value for t in at.title)
    button_labels = [b.label for b in at.button]
    assert any("研究者總覽" in label for label in button_labels), "researcher-workspace entry button missing"
    assert any("臨床證據首頁" in label for label in button_labels), "clinical-evidence entry button missing"


@pytest.mark.parametrize("page", RESEARCHER_PAGES)
def test_researcher_pages_render_offline_without_exception(page):
    """Every researcher page needs a dataset_id (fetched from a live API) to
    show real content, so offline all of them should stop cleanly at the
    shared `require_dataset_id()`/`load_summary()` gate -- never raise.
    (The dossier page is the one exception: it ships its own SAMPLE fallback
    and is exercised more deeply below, so an unconditional stop is not
    expected there.)
    """
    appt = pytest.importorskip("streamlit.testing.v1")
    at = appt.AppTest.from_file(str(PAGES / page), default_timeout=60)
    at.run()
    assert not at.exception, f"{page} raised offline: {at.exception}"


def test_empty_dataset_state_points_to_the_shipped_reference_dataset():
    """Wave 2 (docs/ux_trust_fix_plan.md, cold-start): a fresh clone already
    ships a built, git-tracked reference dataset
    (sources/target_tool_cache/e7ecd8d5-.../target_cards.csv) -- a first-time
    visitor should never have to run a build or wait on anything just to see
    real data. The empty-dataset message must say so by name, not just
    abstractly describe "run a build" / "paste a dataset_id"."""
    from dataset_context import SHIPPED_REFERENCE_DATASET_ID

    appt = pytest.importorskip("streamlit.testing.v1")
    at = appt.AppTest.from_file(str(PAGES / "01_研究者_總覽_overview.py"), default_timeout=60)
    at.run()
    assert not at.exception
    info_texts = " ".join(i.value for i in at.info)
    assert SHIPPED_REFERENCE_DATASET_ID in info_texts


@pytest.mark.parametrize("page", CLINICAL_PAGES)
def test_clinical_pages_render_offline_without_exception(page):
    appt = pytest.importorskip("streamlit.testing.v1")
    at = appt.AppTest.from_file(str(PAGES / page), default_timeout=60)
    at.run()
    assert not at.exception, f"{page} raised offline: {at.exception}"


@pytest.mark.parametrize("page", CLINICAL_PAGES)
def test_clinical_pages_show_a_forced_caveat(page):
    """Every clinical-evidence page must render an un-hideable safety banner
    on load, no toggle, no branch that suppresses it (docs/frontend_design.md
    §1.1/§6)."""
    appt = pytest.importorskip("streamlit.testing.v1")
    at = appt.AppTest.from_file(str(PAGES / page), default_timeout=60)
    at.run()
    error_texts = [e.value for e in at.error]
    assert error_texts, f"{page} did not render a forced caveat banner"


def test_disease_drug_evidence_page_shows_sample_on_demand():
    """C3: loading the verified example must not filter out the zero-trial
    row -- hiding it would be exactly the visual softening this feature
    exists to prevent (docs/frontend_design.md §5.2)."""
    appt = pytest.importorskip("streamlit.testing.v1")
    at = appt.AppTest.from_file(str(PAGES / "12_臨床證據_疾病藥物證據配對.py"), default_timeout=60)
    at.run()
    sample_button = next(b for b in at.button if "已驗證範例" in b.label)
    sample_button.click().run()
    assert not at.exception, f"disease-drug-evidence page raised: {at.exception}"

    dataframes = at.dataframe
    assert len(dataframes) >= 1, "no evidence table rendered from the sample"
    evidence_df = dataframes[0].value
    assert "BASILIXIMAB" in evidence_df["drug_name"].values
    zero_trial_rows = evidence_df[evidence_df["n_trials_for_this_disease"] == 0]
    assert not zero_trial_rows.empty, "the zero-trial drug row must still be shown, not filtered out"


def test_population_genetics_page_shows_sample_on_demand():
    appt = pytest.importorskip("streamlit.testing.v1")
    at = appt.AppTest.from_file(str(PAGES / "13_臨床證據_群體遺傳查詢.py"), default_timeout=60)
    at.run()
    sample_button = next(b for b in at.button if "已驗證範例" in b.label)
    sample_button.click().run()
    assert not at.exception, f"population-genetics page raised: {at.exception}"
    metric_labels = [m.label for m in at.metric]
    assert "CI excludes 0" in metric_labels, "CI-excludes/includes-zero metric did not render"


def test_researcher_page_source_does_not_use_dead_end_tables():
    """UX-flow fix (docs/ux_flow_stepwise_plan.md, Step 2/3), re-verified after
    the persona-split page move: Disease Translator's two tables and
    Pathway+Clinical's module-hit table must use the shared
    `_selectable_table_with_dossier_link` helper, never a plain
    `st.dataframe(...)` dead end.
    """
    disease_src = (PAGES / "05_研究者_疾病標的翻譯.py").read_text(encoding="utf-8")
    assert "_selectable_table_with_dossier_link(disease_df" in disease_src
    assert "_selectable_table_with_dossier_link(ds_df" in disease_src
    assert "st.dataframe(disease_df" not in disease_src
    assert "st.dataframe(ds_df" not in disease_src

    pathway_src = (PAGES / "06_研究者_通路與模組.py").read_text(encoding="utf-8")
    assert "_selectable_table_with_dossier_link(module_df" in pathway_src
    assert "st.dataframe(module_df" not in pathway_src


def test_target_explorer_deep_links_instead_of_duplicating_the_dossier():
    """UX-flow fix (docs/ux_flow_stepwise_plan.md, Step 3), re-verified after
    the persona-split page move: Target Explorer must deep-link to the
    dossier via the shared DOSSIER_PAGE_PATH constant, never re-render its
    own Readiness/External-evidence/Evidence-graph copy."""
    src = (PAGES / "04_研究者_標的探索_target_explorer.py").read_text(encoding="utf-8")
    assert "DOSSIER_PAGE_PATH" in src
    assert "st.switch_page(DOSSIER_PAGE_PATH)" in src
    assert "st.graphviz_chart(" not in src
    assert "External evidence" not in src
    assert "def _evidence(" not in src
    assert "def _evidence_graph(" not in src


def test_overview_page_has_persona_wayfinding_note():
    """UX-flow fix: the Overview page (the first researcher page) must point
    a clinician and a researcher at which page to open first."""
    src = (PAGES / "01_研究者_總覽_overview.py").read_text(encoding="utf-8")
    assert "臨床醫師" in src
    assert "研究者" in src
    assert "整合 Triage" in src


def test_overview_page_has_standard_limitations_text():
    src = (PAGES / "01_研究者_總覽_overview.py").read_text(encoding="utf-8")
    assert "primary human CD4⁺ T cell CRISPRi" in src
    assert "Rest/Stim8hr/Stim48hr" in src
    assert "hypothesis-generating interpretation only" in src
    assert "independent guides" in src
    assert "disease-context models" in src


def test_evidence_type_caveats_are_shared_not_page_copy_pasted():
    guide_src = (DASH / "evidence_type_guide.py").read_text(encoding="utf-8")
    assert "Perturb-seq screen evidence" in guide_src
    assert "Human genetic association" in guide_src
    assert "Population LoF evidence" in guide_src
    assert "Drug / tractability precedent" in guide_src
    assert "Heuristic readiness triage" in guide_src

    overview_src = (PAGES / "01_研究者_總覽_overview.py").read_text(encoding="utf-8")
    explorer_src = (PAGES / "04_研究者_標的探索_target_explorer.py").read_text(encoding="utf-8")
    dossier_src = (PAGES / DOSSIER_PAGE).read_text(encoding="utf-8")
    for src in [overview_src, explorer_src, dossier_src]:
        assert "render_evidence_type_guide" in src
    assert "evidence_type_caption(\"perturbseq\")" in explorer_src
    assert "evidence_type_caption(\"genetics\", \"tractability\")" in dossier_src
    assert "evidence_type_caption(\"readiness\")" in dossier_src


def test_dossier_page_renders_offline():
    appt = pytest.importorskip("streamlit.testing.v1")
    at = appt.AppTest.from_file(str(PAGES / DOSSIER_PAGE), default_timeout=60)
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
    at = appt.AppTest.from_file(str(PAGES / DOSSIER_PAGE), default_timeout=60)
    at.run()
    at.text_input(key="dossier_query").set_value("IL2RA").run()
    assert not at.exception, f"dossier page raised after selecting a gene: {at.exception}"

    expander_labels = [e.label for e in at.expander]
    assert any("名詞解釋" in label for label in expander_labels), "glossary expander did not render"

    caption_texts = [c.value for c in at.caption]
    assert any("CRISPRi screen" in t and "N≈3" in t for t in caption_texts), (
        "structural-limits banner did not render"
    )


def test_dossier_page_shows_preprint_disclosure_when_dataset_version_is_a_biorxiv_pin():
    """Wave 1d (docs/ux_trust_fix_plan.md): the reference dataset is pinned to a
    bioRxiv preprint (not yet peer-reviewed), a fact easy to lose track of once
    a user is looking at confident-looking chips. Sourced from the real
    per-dataset version string (never a hardcoded guess), so this is a source
    check for the logic + the exact string it looks for, not an offline AppTest
    render (the offline SAMPLE_DATASETS fixture carries no version field, so
    the disclosure only actually renders against a live dataset -- confirmed by
    manual verification against the running API during development)."""
    src = (PAGES / DOSSIER_PAGE).read_text(encoding="utf-8")
    assert "biorxiv" in src.lower()
    assert "peer-reviewed" in src.lower() or "同行評審" in src


def test_dossier_page_shows_quick_answer_headline_before_the_evidence_walkthrough():
    """UX-flow fix (/goal: optimize the sequence for a biomedical researcher and
    a clinician so the right information is found fast). Previously the
    readiness_call + next_validation_step only appeared at the very BOTTOM of
    the page, after 6 sections of raw statistics/concept/mechanism detail --
    a clinician had to scroll past all of that for the one-line answer, and a
    researcher had to scroll the same distance for the recommended next
    experiment. This asserts the headline (same values, no new computation)
    now renders right after the header, before the raw statistical evidence
    section appears in the underlying markdown order.
    """
    appt = pytest.importorskip("streamlit.testing.v1")
    at = appt.AppTest.from_file(str(PAGES / DOSSIER_PAGE), default_timeout=60)
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

    # Order check: the headline markdown must appear BEFORE section ⑥'s (the
    # raw GWT evidence section's) subheader in source order, so it isn't just
    # present but actually promoted above the evidence walkthrough.
    src = (PAGES / DOSSIER_PAGE).read_text(encoding="utf-8")
    headline_pos = src.index("快速結論")
    section_pos = src.index("GWT 篩選證據")
    assert headline_pos < section_pos, "quick-answer headline must be placed before the GWT evidence section"


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
    """
    src = (PAGES / DOSSIER_PAGE).read_text(encoding="utf-8")
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
    (now pages/11_臨床證據_個體概念剖面.py). This asserts the dossier page
    source never re-imports either symbol from `concept_waterfall`.
    """
    src = (PAGES / DOSSIER_PAGE).read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "concept_waterfall":
            imported_names.update(alias.name for alias in node.names)
    assert "SAMPLE_REPORT" not in imported_names
    assert "build_waterfall_figure" not in imported_names
