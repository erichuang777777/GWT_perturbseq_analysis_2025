"""Streamlit page — 研究者 · Program overview.

R1 (docs/frontend_design.md §3a): "As a researcher, I want a single view of
where every screened target stands, so I can spot where the program's
attention should go next."

Extracted verbatim (behavior-preserving) from target_card_dashboard.py's
former "Overview" tab, MINUS the Calibration / QC-funnel / cross-guide vs
cross-donor robustness sections -- those moved to their own page
(pages/7_研究者_校準與穩健性.py, R4 in the design doc) so each page answers
one question rather than several.

Isolation (frontend/README.md): talks to the backend ONLY via api_client's
HTTP helpers. Never imports `src/3_DE_analysis`.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from api_client import _count_chart, _metric_value, _readiness
from dataset_context import configure_page, load_summary, render_sidebar, require_dataset_id
from glossary import render_glossary_expander

configure_page("GWT Target Evidence Browser — Overview")
render_sidebar()
dataset_id = require_dataset_id()
opts, summary_payload, summary = load_summary(dataset_id)

st.title("研究者 · Program overview")

# UX-flow fix: wayfinding starts here, before any page or gene is chosen.
# Both personas used to have to discover the right tab by trial and error;
# this is a one-line map from "who you are" to "where to click first".
st.caption(
    "🧭 **快速導覽**——"
    "🩺 臨床醫師:先看「整合 Triage」(整體排序)或「Disease Translator」(依疾病找標的);"
    "🔬 研究者:先看「Target Explorer」(逐標的統計證據)或「Pathway + Clinical」。"
    "在任一表格選取一列後按「開啟標的檔案:… →」可進入該標的的完整 dossier(含快速結論)。"
)
cols = st.columns(6)
for col, key, label in zip(
    cols,
    ["n_rows", "n_targets", "n_conditions", "n_grade_3_or_4", "n_replicate_pass", "n_watchlist"],
    ["Rows", "Targets", "Conditions", "Grade 3-4", "Replicate pass", "Watchlist"],
):
    col.metric(label, _metric_value(summary, key))

chart_cols = st.columns(3)
with chart_cols[0]:
    st.subheader("Evidence grade")
    grade_chart = _count_chart(summary_payload.get("grade_counts", []), "statistical_evidence_grade")
    if not grade_chart.empty:
        st.bar_chart(grade_chart)
with chart_cols[1]:
    st.subheader("Condition")
    condition_chart = _count_chart(summary_payload.get("condition_counts", []), "condition")
    if not condition_chart.empty:
        st.bar_chart(condition_chart)
with chart_cols[2]:
    st.subheader("Pathway axis")
    pathway_chart = _count_chart(summary_payload.get("pathway_counts", []), "pathway_axis")
    if not pathway_chart.empty:
        st.bar_chart(pathway_chart)

st.subheader("Top candidates")
st.markdown(
    "**Evidence type: Perturb-seq screen evidence.** Shows target-condition knockdown-associated transcriptomic effects, robustness, and QC support; "
    "it cannot by itself prove disease efficacy, clinical safety, or pharmacologic equivalence."
)
st.markdown(
    "**Evidence type: Drug/tractability precedent.** Indicates known modality, druggability, or clinical precedent for the target class; "
    "it cannot prove that this target, direction, indication, or dose is feasible."
)
st.markdown(
    "**Evidence type: Heuristic readiness triage.** Combines available evidence into a transparent prioritization call; "
    "it is not regulatory, clinical, or nomination-ready proof."
)
top_df = pd.DataFrame(summary_payload.get("top_candidates", []))
st.dataframe(top_df, use_container_width=True, hide_index=True)

st.subheader("Watchlist")
watch_df = pd.DataFrame(summary_payload.get("watchlist", []))
st.dataframe(watch_df, use_container_width=True, hide_index=True)

st.subheader("Readiness")
st.markdown(
    "**Evidence type: Heuristic readiness triage.** Combines available evidence into a transparent prioritization call; "
    "it is not regulatory, clinical, or nomination-ready proof."
)
render_glossary_expander(keys=["advance", "validate", "watchlist", "deprioritize", "grade"])
try:
    readiness_payload = _readiness(dataset_id)
    stage_counts = readiness_payload.get("counts", {})
    call_counts = readiness_payload.get("call_counts", {})
    rcols = st.columns(2)
    with rcols[0]:
        st.caption("R-stage (R0 deprioritize → R3 advance)")
        if stage_counts:
            st.bar_chart(pd.Series(stage_counts).sort_index().rename("n"))
    with rcols[1]:
        st.caption("Readiness call")
        if call_counts:
            st.bar_chart(pd.Series(call_counts).rename("n"))
    missing = readiness_payload.get("overlays_missing", [])
    if missing:
        st.caption(f"External overlays not yet wired (domains stay 'unknown'): {', '.join(missing)}")
except Exception as e:
    st.info(f"Readiness not available: {e}")
