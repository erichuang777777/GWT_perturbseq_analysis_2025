"""Shared dataset-selection sidebar + summary loading for researcher pages.

Not explicitly named in docs/frontend_design.md (that design doc was written
without full visibility of target_card_dashboard.py's module-level setup --
the gene-lookup expander, dataset picker, and build form used to run ONCE at
module scope and every tab's render_*() function closed over the resulting
`dataset_id`/`opts`/`summary_payload`/`summary` variables as free variables).
Splitting each tab into its own standalone Streamlit page means each page is
now its own script run with no shared module scope, so this setup has to
live somewhere every researcher page can call it from -- this module is that
one place, extracted verbatim (behavior-preserving) from
target_card_dashboard.py.

Isolation (frontend/README.md): talks to the backend ONLY via api_client's
HTTP helpers. Never imports `src/3_DE_analysis`.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

import streamlit as st

from api_client import (
    API_BASE,
    _api_post,
    _compatibility_banner,
    _datasets,
    _gene_search,
    _gene_status,
    _options,
    _summary,
)

DEFAULT_DE = "metadata/suppl_tables/DE_stats.suppl_table.csv"
DEFAULT_GUIDE = "metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv"
DEFAULT_LIBRARY = "metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv"
DEFAULT_BENCHMARK = "sources/topic05_successful_drug_benchmarks.csv"

_PAGE_STYLE = """
    <style>
    .stMetric { border: 1px solid #d8dee8; border-radius: 6px; padding: 10px 12px; background: #fbfcfd; }
    div[data-testid="stDataFrame"] { border: 1px solid #d8dee8; border-radius: 6px; }
    </style>
    """


def configure_page(title: str) -> None:
    """Shared page chrome every researcher page starts with: page config +
    the metric/dataframe border styling that used to be injected once at
    target_card_dashboard.py's module scope, now needed per-page since each
    split-out page is its own script run."""
    st.set_page_config(page_title=title, layout="wide")
    st.markdown(_PAGE_STYLE, unsafe_allow_html=True)


def _run_job() -> None:
    payload = {
        "de_stats": st.session_state.get("de_stats", DEFAULT_DE),
        "guide_kd": st.session_state.get("guide_kd", DEFAULT_GUIDE),
        "library_metadata": st.session_state.get("library_metadata", DEFAULT_LIBRARY),
        "clinical_benchmark": None if st.session_state.get("skip_benchmark") else st.session_state.get("clinical_benchmark", DEFAULT_BENCHMARK),
        "min_cells": int(st.session_state.get("min_cells", 200)),
        "min_de_genes": int(st.session_state.get("min_de", 50)),
        "skip_benchmark": bool(st.session_state.get("skip_benchmark", False)),
        "max_rows": int(st.session_state.get("preview_rows", 50)),
        "include_module_scores": True,
    }
    result = _api_post("/api/run/target-card", payload)
    st.session_state["dataset_id"] = result.get("dataset_id", "")
    st.cache_data.clear()


def render_sidebar() -> None:
    """Gene-lookup expander + dataset picker + build-target-cards form.
    Verbatim (behavior-preserving) move from target_card_dashboard.py."""
    with st.sidebar:
        with st.expander("Gene lookup", expanded=False):
            st.caption("Alias-tolerant search (typos/partial/old symbols OK) + three-state result status. Works without a loaded dataset.")
            lookup_query = st.text_input("gene symbol, alias, or Ensembl ID", key="gene_lookup_query")
            if lookup_query:
                try:
                    search_result = _gene_search(lookup_query, limit=5)
                    for hit in search_result.get("results", []):
                        st.write(f"- **{hit['canonical_symbol']}** ({hit['match_type']}, score {hit['score']}) — `{hit['ensembl_gene_id']}`")
                    if not search_result.get("results"):
                        st.caption("No matches.")
                    status_dataset = st.session_state.get("dataset_id", "").strip() or None
                    status_result = _gene_status(lookup_query, dataset_id=status_dataset)
                    st.info(f"result_status: **{status_result.get('result_status')}** (source: {status_result.get('source', 'reference DE table')})")
                except Exception as e:
                    st.error(f"Lookup failed: {e}")

        st.subheader("Dataset")
        st.text_input("API base", value=API_BASE, disabled=True)
        try:
            dataset_df = _datasets()
        except Exception:
            import pandas as pd

            dataset_df = pd.DataFrame()

        dataset_choices = dataset_df["dataset_id"].tolist() if not dataset_df.empty and "dataset_id" in dataset_df.columns else []
        if dataset_choices:
            current = st.session_state.get("dataset_id", dataset_choices[0])
            if current not in dataset_choices:
                current = dataset_choices[0]
            selected_dataset = st.selectbox("recent dataset", dataset_choices, index=dataset_choices.index(current))
            st.session_state["dataset_id"] = selected_dataset

        st.text_input("dataset_id", key="dataset_id")

        with st.expander("Build target cards", expanded=not bool(st.session_state.get("dataset_id"))):
            st.text_input("DE stats", key="de_stats", value=DEFAULT_DE)
            st.text_input("guide_kd_efficiency", key="guide_kd", value=DEFAULT_GUIDE)
            st.text_input("library metadata", key="library_metadata", value=DEFAULT_LIBRARY)
            st.text_input("clinical benchmark", key="clinical_benchmark", value=DEFAULT_BENCHMARK)
            st.slider("min_cells", min_value=1, max_value=1000, value=200, key="min_cells")
            st.slider("min_de_genes", min_value=1, max_value=300, value=50, key="min_de")
            st.number_input("preview rows", min_value=1, max_value=5000, value=50, key="preview_rows")
            st.checkbox("skip benchmark mapping", value=False, key="skip_benchmark")
            if st.button("Run build", type="primary"):
                try:
                    with st.spinner("Building target cards..."):
                        _run_job()
                    st.success(f"dataset_id={st.session_state['dataset_id']}")
                except Exception as e:
                    st.error(f"Run failed: {e}")


# The git-tracked reference dataset shipped in this repo (sources/target_tool_cache/
# e7ecd8d5-.../target_cards.csv) -- a fresh clone already has this built and
# committed, so a first-time visitor never has to run a build or wait on
# anything just to see real data. docs/ux_trust_fix_plan.md Wave 2 (cold-start).
SHIPPED_REFERENCE_DATASET_ID = "e7ecd8d5-5463-43e3-9bf1-6e8a15d3e137"


def require_dataset_id() -> str:
    """Return the active dataset_id, or st.stop() with guidance if none is
    selected. Previously this fell back to an inline Imports-only tab; in the
    split-page world the sidebar's own page nav already lists the upload page,
    so this just points there instead of duplicating that tab inline."""
    dataset_id = st.session_state.get("dataset_id", "").strip()
    if not dataset_id:
        st.info(
            f"還沒有選擇資料集。**最快的方式**:在左側側邊欄的「dataset_id」欄位貼上 "
            f"`{SHIPPED_REFERENCE_DATASET_ID}`(這是本 repo 已經內建、可直接使用的參考資料集,"
            "不需要重新建置)。也可以自行 Run a build,或用「研究者_資料集上傳合併」頁面上傳自己的資料。"
        )
        st.stop()
    return dataset_id


def load_summary(dataset_id: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Fetch (opts, summary_payload, summary) for the active dataset, showing
    the compatibility banner as a side effect (verbatim prior behavior).
    st.stop()s with an error if the dataset isn't available."""
    try:
        opts = _options(dataset_id)
        summary_payload = _summary(dataset_id, top_n=50)
    except Exception as e:
        st.error(f"Dataset not available: {e}")
        st.stop()
        raise  # unreachable, satisfies type-checkers that opts/summary_payload are bound

    summary = summary_payload.get("summary", {})
    _compatibility_banner(dataset_id)
    return opts, summary_payload, summary
