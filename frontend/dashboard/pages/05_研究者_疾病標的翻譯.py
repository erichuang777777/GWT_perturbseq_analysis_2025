"""Streamlit page — 研究者 · Disease → target translator.

R5 (docs/frontend_design.md §3a): "As a researcher, I want to start from a
disease name instead of a gene, so I can find which screened targets are
already implicated in it."

Extracted verbatim (behavior-preserving) from target_card_dashboard.py's
former "Disease Translator" tab (disease→target ranking + 遺傳雙證據
genetic double-support).

Isolation (frontend/README.md): talks to the backend ONLY via api_client's
HTTP helpers. Never imports `src/3_DE_analysis`.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from api_client import _disease_targets, _diseases, _genetic_double_support, _selectable_table_with_dossier_link
from dataset_context import configure_page, load_summary, render_sidebar, require_dataset_id

configure_page("GWT Target Evidence Browser — Disease Translator")
render_sidebar()
dataset_id = require_dataset_id()
opts, summary_payload, summary = load_summary(dataset_id)

st.title("Disease Translator")
st.caption(
    "Ranks target cards by real Open Targets genetic-association evidence for a chosen indication. "
    "Coverage is restricted to diseases already present in the local association table -- "
    "no free-text disease is guessed or fabricated."
)
try:
    disease_payload = _diseases()
    disease_options = [d["disease_name"] for d in disease_payload.get("diseases", [])]
except Exception as e:
    disease_options = []
    st.error(f"Could not load disease list: {e}")

if not disease_options:
    st.info("No local disease-association table available.")
else:
    disease_cols = st.columns([2, 1, 1])
    with disease_cols[0]:
        selected_disease = st.selectbox("Indication", disease_options)
    with disease_cols[1]:
        disease_min_grade = st.slider("min grade", min_value=1, max_value=4, value=2, key="disease_min_grade")
    with disease_cols[2]:
        disease_top_n = st.number_input("top N", min_value=5, max_value=200, value=30, step=5, key="disease_top_n")

    try:
        result = _disease_targets(selected_disease, dataset_id, int(disease_min_grade), int(disease_top_n))
    except Exception as e:
        result = {"matched": False, "reason": str(e), "targets": []}

    if not result.get("matched"):
        st.warning(result.get("reason", "No match."))
    elif not result.get("targets"):
        st.info(result.get("reason") or "No target-condition rows matched this indication at the current filters.")
    else:
        disease_df = pd.DataFrame(result["targets"])
        _selectable_table_with_dossier_link(disease_df, "disease_table")
        if "disease_association_score" in disease_df.columns and "target" in disease_df.columns:
            chart_df = disease_df.drop_duplicates("target").set_index("target")[["disease_association_score"]]
            st.bar_chart(chart_df)

st.divider()
st.subheader("遺傳雙證據 — Genetic double-support (disease × population)")
st.caption(
    "Targets that are BOTH a genetic-association top target for ≥1 immune "
    "indication AND carry a UK Biobank rare-LoF-burden signal whose 95% CI "
    "excludes zero. Descriptive hypothesis prioritisation — GWAS-style "
    "genetic association (not experimental causal proof) crossed with a "
    "**population-level** burden estimate (not a patient-level prediction)."
)
ds_cols = st.columns([1, 3])
with ds_cols[0]:
    ds_min_grade = st.slider("Min statistical grade", 1, 4, 2)
try:
    ds_payload = _genetic_double_support(dataset_id, min_grade=ds_min_grade)
    if not ds_payload.get("available", False):
        st.info(f"Double-support not available: {ds_payload.get('reason', 'unknown')}")
    else:
        st.caption(
            f"trait: `{ds_payload.get('trait', '')}` · "
            f"{ds_payload.get('n_double_support', 0)} double-support targets · "
            f"⚠️ {ds_payload.get('caveat', '')}"
        )
        ds_rows = ds_payload.get("targets", [])
        if not ds_rows:
            st.info("No double-support targets at this grade threshold.")
        else:
            ds_df = pd.DataFrame(ds_rows)
            if "diseases" in ds_df.columns:
                ds_df["diseases"] = ds_df["diseases"].map(lambda v: ", ".join(v) if isinstance(v, list) else v)
            _selectable_table_with_dossier_link(ds_df, "double_support_table")
except Exception as e:
    st.info(f"Double-support view not available: {e}")
