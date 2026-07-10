"""Streamlit page — 研究者 · Calibration & robustness.

R4 (docs/frontend_design.md §3a): "As a researcher, I want to see whether
this ranking actually recovers known successful drug targets, so I can
trust the score before acting on it."

Extracted verbatim (behavior-preserving) out of target_card_dashboard.py's
former "Overview" tab's Calibration / QC-funnel / cross-guide vs cross-donor
robustness sections -- split into its own page so Overview (pages/1) answers
one question ("where does the program stand") and this page answers a
different one ("can I trust the ranking").

Isolation (frontend/README.md): talks to the backend ONLY via api_client's
HTTP helpers. Never imports `src/3_DE_analysis`.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from api_client import _calibration, _targets
from dataset_context import configure_page, load_summary, render_sidebar, require_dataset_id

configure_page("GWT Target Evidence Browser — Calibration & Robustness")
render_sidebar()
dataset_id = require_dataset_id()
opts, summary_payload, summary = load_summary(dataset_id)

st.title("Calibration & robustness")

st.subheader("Calibration — does this ranking recover known biology?")
st.caption("Deterministic, reproducible checks: positive-control recovery, known drug-axis enrichment, and rank stability under strict robustness filtering.")
try:
    calibration_payload = _calibration(dataset_id)
    for line in calibration_payload.get("narrative", []):
        st.write(f"- {line}")
    with st.expander("Calibration details", expanded=False):
        pc = calibration_payload.get("positive_control_recovery", {})
        st.write(f"Positive-control gene set size: {pc.get('gene_set_size', 'NA')} | fraction in top-2 deciles: {pc.get('fraction_in_top_2_deciles', 'NA')}")
        axis = calibration_payload.get("known_drug_axis_enrichment", {})
        if axis.get("available"):
            st.write(f"Known drug axes recovered: {axis.get('known_axes_recovered', [])}")
            st.write(f"Known drug axes missing: {axis.get('known_axes_missing', [])}")
        stability = calibration_payload.get("rank_stability", {})
        st.write(
            f"Top-{stability.get('top_n', 'NA')} overlap after strict filtering: "
            f"{stability.get('top_n_overlap', 'NA')}/{stability.get('top_n', 'NA')} "
            f"(Spearman r={stability.get('spearman_rank_correlation', 'NA')})"
        )

    st.subheader("QC funnel")
    st.caption("Row count surviving each successive robustness gate (the EDA's strict actionable filter).")
    funnel = calibration_payload.get("qc_funnel", {})
    stages = funnel.get("stages", [])
    if stages:
        funnel_df = pd.DataFrame(stages).set_index("stage")[["n"]]
        st.bar_chart(funnel_df)
        st.caption(f"High-confidence rows after all gates: {funnel.get('high_confidence_rows', 'NA')}")
except Exception as e:
    st.info(f"Calibration not available: {e}")

st.subheader("Cross-guide vs cross-donor robustness")
st.caption("Every target-condition row in this dataset (up to 2,000 sampled). Robustness gates used elsewhere in this tool sit at 0.2 (candidate) and 0.3 (strong).")
try:
    robustness_df = _targets(dataset_id, {"max_rows": 2000})
    scatter_cols = [c for c in ["crossguide_correlation", "crossdonor_correlation_mean"] if c in robustness_df.columns]
    if len(scatter_cols) == 2 and not robustness_df.empty:
        try:
            st.scatter_chart(robustness_df, x="crossguide_correlation", y="crossdonor_correlation_mean")
        except Exception:
            st.dataframe(robustness_df[["target", "condition"] + scatter_cols], use_container_width=True, hide_index=True)
    else:
        st.info("Robustness columns not available in this dataset.")
except Exception as e:
    st.info(f"Robustness scatter not available: {e}")
