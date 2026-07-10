"""Streamlit page — 研究者 · 整合多軸 Triage.

Extracted verbatim (behavior-preserving) from target_card_dashboard.py's
former "整合 Triage" tab (composite descriptive shortlist + robustness-first
filter-then-rank).

Isolation (frontend/README.md): talks to the backend ONLY via api_client's
HTTP helpers. Never imports `src/3_DE_analysis`.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from api_client import _robust_ranked, _selectable_table_with_dossier_link, _triage
from dataset_context import configure_page, load_summary, render_sidebar, require_dataset_id
from ui_chips import format_concept_chips

configure_page("GWT Target Evidence Browser — 整合 Triage")
render_sidebar()
dataset_id = require_dataset_id()
opts, summary_payload, summary = load_summary(dataset_id)

st.title("整合多軸 Triage — composite descriptive shortlist")
st.markdown(
    "**Evidence type: Heuristic readiness triage.** Combines available evidence into a transparent prioritization call; "
    "it is not regulatory, clinical, or nomination-ready proof."
)
st.caption(
    "One row per target, scored across independent descriptive axes: immune "
    "concept membership, stimulation-gating, direction switches, safety window "
    "(gnomAD/GTeX — only ~15 genes covered), druggability, robustness tier, and "
    "genetic double-support. **Every axis is descriptive — none feeds the "
    "readiness call.** Sparse axes (safety) never credit `unknown` as safe."
)
tri_top_n = st.slider("Top N targets", 10, 500, 100, 10, key="triage_top_n")
try:
    tri_payload = _triage(dataset_id, top_n=tri_top_n)
    if not tri_payload.get("available", False):
        st.info(f"Triage not available: {tri_payload.get('reason', 'unknown')}")
    else:
        prov = tri_payload.get("provenance", {})
        st.caption(
            f"{tri_payload.get('returned', 0)} of {tri_payload.get('n_total', 0)} targets · "
            f"concept_set: `{prov.get('concept_set_version', '?')}` · "
            f"safety coverage: {prov.get('gnomad_source', 'gnomAD')} / {prov.get('gtex_source', 'GTEx')}"
        )
        tri_rows = tri_payload.get("targets", [])
        if tri_rows:
            tri_df = pd.DataFrame(tri_rows)
            if "concept_modules" in tri_df.columns:
                tri_df["concept_modules"] = tri_df["concept_modules"].map(format_concept_chips)
            _selectable_table_with_dossier_link(tri_df, "triage_table")
except Exception as e:
    st.info(f"Triage view not available: {e}")

st.divider()
st.subheader("穩健優先排序 — Robustness-first (filter-then-rank)")
st.markdown(
    "**Evidence type: Perturb-seq screen evidence.** Shows target-condition knockdown-associated transcriptomic effects, robustness, and QC support; "
    "it cannot by itself prove disease efficacy, clinical safety, or pharmacologic equivalence."
)
st.caption(
    "Keeps only `high_confidence` rows (all measurable robustness checks pass) "
    "THEN ranks — addressing the calibration finding that the raw-DE shortlist "
    "churns 74–85% under strict filtering. `unresolved` rows (a robustness field "
    "is unmeasured) are counted separately, never treated as pass or fail."
)
rr_cols = st.columns(3)
with rr_cols[0]:
    rr_strict = st.checkbox("Strict (cross ≥0.5)", value=False)
with rr_cols[1]:
    rr_lenient = st.checkbox("Lenient (accept confounded-but-robust)", value=False)
with rr_cols[2]:
    rr_top_n = st.slider("Top N", 10, 500, 100, 10, key="robust_top_n")
try:
    rr_payload = _robust_ranked(dataset_id, strict=rr_strict, lenient=rr_lenient, top_n=rr_top_n)
    if not rr_payload.get("available", False):
        st.info(f"Robust ranking not available: {rr_payload.get('reason', 'unknown')}")
    else:
        st.caption(
            f"high_confidence: {rr_payload.get('n_high_confidence', 0)} · "
            f"unresolved: {rr_payload.get('n_unresolved', 0)} · "
            f"total: {rr_payload.get('n_total', 0)} · thresholds: {rr_payload.get('thresholds', {})}"
        )
        rr_rows = rr_payload.get("targets", [])
        if rr_rows:
            st.dataframe(pd.DataFrame(rr_rows), use_container_width=True, hide_index=True)
except Exception as e:
    st.info(f"Robust ranking view not available: {e}")
