"""Streamlit page — 研究者 · Pathway + clinical axis + module hits.

Extracted verbatim (behavior-preserving) from target_card_dashboard.py's
former "Pathway + Clinical" tab.

Isolation (frontend/README.md): talks to the backend ONLY via api_client's
HTTP helpers. Never imports `src/3_DE_analysis`.
"""

from __future__ import annotations

import streamlit as st

from api_client import _count_chart, _modules, _selectable_table_with_dossier_link
from dataset_context import configure_page, load_summary, render_sidebar, require_dataset_id

configure_page("GWT Target Evidence Browser — Pathway + Clinical")
render_sidebar()
dataset_id = require_dataset_id()
opts, summary_payload, summary = load_summary(dataset_id)

st.title("Pathway + Clinical")

module_df = _modules(dataset_id)
clinical_chart = _count_chart(summary_payload.get("clinical_counts", []), "clinical_axis")
panel_cols = st.columns(2)
with panel_cols[0]:
    st.subheader("Clinical axis")
    if not clinical_chart.empty:
        st.bar_chart(clinical_chart)
with panel_cols[1]:
    st.subheader("Module hits")
    if module_df.empty:
        st.info("No module mapping available.")
    else:
        module_counts = module_df["module_name"].value_counts().rename_axis("module_name").reset_index(name="n")
        st.bar_chart(module_counts.set_index("module_name"))

st.subheader("Module hit table")
_selectable_table_with_dossier_link(module_df, "module_table")
