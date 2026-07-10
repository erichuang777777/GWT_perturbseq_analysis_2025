"""Streamlit page — 研究者 · Exports.

R7 (docs/frontend_design.md §3a): "As a researcher, I want a versioned,
provenance-stamped export, so results stay reproducible outside this tool."

Extracted verbatim (behavior-preserving) from target_card_dashboard.py's
former "Export" tab.

Isolation (frontend/README.md): talks to the backend ONLY via api_client's
HTTP helpers. Never imports `src/3_DE_analysis`.
"""

from __future__ import annotations

import streamlit as st

from api_client import _api_download, _summary
from dataset_context import configure_page, load_summary, render_sidebar, require_dataset_id

configure_page("GWT Target Evidence Browser — Export")
render_sidebar()
dataset_id = require_dataset_id()
opts, summary_payload, summary = load_summary(dataset_id)

st.title("Exports")

report_top_n = st.slider("report top_n", min_value=10, max_value=500, value=50, step=10)
report = _summary(dataset_id, top_n=int(report_top_n))
st.write(report.get("summary", {}))

col_csv, col_json, col_html, col_md = st.columns(4)
with col_csv:
    st.download_button(
        "CSV",
        data=_api_download(f"/api/exports/{dataset_id}", params={"fmt": "csv"}),
        file_name="target_cards.csv",
        mime="text/csv",
    )
with col_json:
    st.download_button(
        "JSON report",
        data=_api_download(f"/api/reports/{dataset_id}", params={"fmt": "json", "top_n": int(report_top_n)}),
        file_name="target_report.json",
        mime="application/json",
    )
with col_html:
    st.download_button(
        "HTML report",
        data=_api_download(f"/api/reports/{dataset_id}", params={"fmt": "html", "top_n": int(report_top_n)}),
        file_name="target_report.html",
        mime="text/html",
    )
with col_md:
    st.download_button(
        "Markdown report",
        data=_api_download(f"/api/reports/{dataset_id}", params={"fmt": "md", "top_n": int(report_top_n)}),
        file_name="target_report.md",
        mime="text/markdown",
    )
