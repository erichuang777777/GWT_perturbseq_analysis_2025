"""Streamlit page — 研究者 · Target explorer.

R2 (docs/frontend_design.md §3a): "As a researcher, I want to filter and rank
targets by condition, stage, and evidence grade, so I can shortlist
candidates worth a closer look."

Extracted verbatim (behavior-preserving) from target_card_dashboard.py's
former "Target Explorer" tab. Already deep-links to the real Target Dossier
page instead of duplicating it inline (docs/ux_flow_stepwise_plan.md Step 3)
-- this move only updates the deep-link's target filename to match the
dossier page's new number in the split.

Isolation (frontend/README.md): talks to the backend ONLY via api_client's
HTTP helpers. Never imports `src/3_DE_analysis`.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd
import streamlit as st

from api_client import DOSSIER_PAGE_PATH, _dataset_status, _target_detail, _targets
from dataset_context import configure_page, load_summary, render_sidebar, require_dataset_id

configure_page("GWT Target Evidence Browser — Target Explorer")
render_sidebar()
dataset_id = require_dataset_id()
opts, summary_payload, summary = load_summary(dataset_id)

st.title("Target explorer")

filter_cols = st.columns([1, 1, 1, 1])
condition_options = [""] + opts.get("conditions", [])
pathway_options = [""] + opts.get("pathway_axis", [])
clinical_options = [""] + opts.get("clinical_axis", [])
cap_options = [""] + opts.get("score_cap_reason", [])

with filter_cols[0]:
    grade = st.slider("minimum grade", min_value=1, max_value=4, value=2)
    condition = st.selectbox("condition", condition_options)
with filter_cols[1]:
    pathway = st.selectbox("pathway axis", pathway_options)
    clinical = st.selectbox("clinical axis", clinical_options)
with filter_cols[2]:
    cap_reason = st.selectbox("score cap reason", cap_options)
    target_search = st.text_input("target contains", "")
with filter_cols[3]:
    replicate_pass = st.checkbox("replicate pass only", value=False)
    exclude_offtarget = st.checkbox("exclude off-target", value=True)
    min_de = st.number_input("min DE genes", min_value=0, max_value=1000, value=50)
    show_rows = st.number_input("rows", min_value=10, max_value=2000, value=200, step=10)

params: Dict[str, Any] = {
    "grade": int(grade),
    "max_rows": int(show_rows),
    "min_de_genes": int(min_de),
}
if condition:
    params["condition"] = condition
if pathway:
    params["pathway_axis"] = pathway
if clinical:
    params["clinical_axis"] = clinical
if cap_reason:
    params["cap_reason"] = cap_reason
if target_search:
    params["target_search"] = target_search
if replicate_pass:
    params["replicate_pass"] = True
if exclude_offtarget:
    params["off_target"] = False

df = _targets(dataset_id, params)
st.dataframe(df, use_container_width=True, hide_index=True)

if not df.empty and "target" in df.columns:
    selected = st.selectbox("Target detail", sorted(df["target"].dropna().unique().tolist()))
    detail = _target_detail(dataset_id, selected)
    rows = pd.DataFrame(detail.get("rows", []))
    summary_row = detail.get("summary", {})

    detail_cols = st.columns(5)
    detail_cols[0].metric("Best grade", summary_row.get("statistical_evidence_grade", "NA"))
    detail_cols[1].metric("Cells", summary_row.get("n_cells_target", "NA"))
    detail_cols[2].metric("DE genes", summary_row.get("n_total_de_genes", "NA"))
    detail_cols[3].metric("Guides", summary_row.get("n_guides", "NA"))
    detail_cols[4].metric("Replicate pass", str(summary_row.get("replicate_pass_flag", "NA")))

    modality_cols = st.columns(3)
    modality_cols[0].metric("Druggable class", str(summary_row.get("druggable_class") or "none"))
    modality_cols[1].metric("Likely modality", str(summary_row.get("tractability_modality") or "unknown"))
    safety_note = str(summary_row.get("safety_note") or "")
    modality_cols[2].metric("Safety notes", safety_note.replace(";", ", ") if safety_note else "none")

    st.subheader(f"{selected} across conditions")
    st.dataframe(rows, use_container_width=True, hide_index=True)

    numeric_view = rows[[c for c in ["condition", "n_total_de_genes", "n_cells_target", "condition_specificity_score"] if c in rows.columns]].copy()
    if not numeric_view.empty and "condition" in numeric_view.columns:
        st.bar_chart(numeric_view.set_index("condition"))

    st.divider()
    st.info(
        "完整的 Readiness 判定、外部證據(trials/literature/genetics)與機制圖,"
        "請至該標的的完整檔案查看(含 unknown≠0 標示、名詞解釋、下一步驗證)。"
    )
    if st.button(f"開啟標的檔案:{selected} →", key="target_explorer_open_dossier"):
        st.query_params.update({"dataset_id": dataset_id, "target": selected})
        st.switch_page(DOSSIER_PAGE_PATH)

    status = _dataset_status(dataset_id)
    lineage = status.get("lineage") or {}
    footer_bits = [
        f"dataset_id={dataset_id}",
        f"origin={status.get('origin', 'gwt_reference')}",
        f"engine_version={status.get('engine_version', 'NA')}",
        f"built_at={status.get('built_at', 'NA')}",
        f"data_version={status.get('data_version', 'NA')}",
    ]
    if lineage:
        footer_bits.append(f"import_id={lineage.get('import_id', 'NA')}")
        footer_bits.append(f"source_name={lineage.get('source_name', 'NA')}")
    st.caption(" · ".join(footer_bits))
