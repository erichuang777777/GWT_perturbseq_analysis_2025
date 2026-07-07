"""Streamlit dashboard for target-condition evidence exploration."""

from __future__ import annotations

import base64
import os
from typing import Any, Dict, Iterable, Optional

import pandas as pd
import requests
import streamlit as st


API_BASE = os.getenv("GWT_API_BASE", "http://127.0.0.1:8000").rstrip("/")
DEFAULT_DE = "metadata/suppl_tables/DE_stats.suppl_table.csv"
DEFAULT_GUIDE = "metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv"
DEFAULT_LIBRARY = "metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv"
DEFAULT_BENCHMARK = "sources/topic05_successful_drug_benchmarks.csv"
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def _api_get(path: str, params: Dict[str, Any] | None = None) -> Any:
    url = f"{API_BASE}{path}"
    r = requests.get(url, params=params, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code}: {r.text}")
    return r.json()


def _api_post(path: str, payload: Dict[str, Any]) -> Any:
    url = f"{API_BASE}{path}"
    r = requests.post(url, json=payload, timeout=180)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code}: {r.text}")
    return r.json()


def _api_post_timeout(path: str, payload: Dict[str, Any], timeout: int) -> Any:
    url = f"{API_BASE}{path}"
    r = requests.post(url, json=payload, timeout=timeout)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code}: {r.text}")
    return r.json()


def _api_download(path: str, params: Dict[str, Any] | None = None) -> bytes:
    url = f"{API_BASE}{path}"
    r = requests.get(url, params=params, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code}: {r.text}")
    return r.content


@st.cache_data(ttl=20)
def _summary(dataset_id: str, top_n: int) -> Dict[str, Any]:
    return _api_get(f"/api/summary/{dataset_id}", params={"top_n": top_n})


@st.cache_data(ttl=20)
def _datasets() -> pd.DataFrame:
    return pd.DataFrame(_api_get("/api/datasets"))


@st.cache_data(ttl=60)
def _options(dataset_id: str) -> Dict[str, Any]:
    return _api_get(f"/api/options/{dataset_id}")


@st.cache_data(ttl=20)
def _targets(dataset_id: str, params: Dict[str, Any]) -> pd.DataFrame:
    rows = _api_get(f"/api/targets/{dataset_id}", params=params)
    return pd.DataFrame(rows)


@st.cache_data(ttl=20)
def _target_detail(dataset_id: str, target: str) -> Dict[str, Any]:
    return _api_get(f"/api/targets/{dataset_id}/{target}")


@st.cache_data(ttl=30)
def _modules(dataset_id: str) -> pd.DataFrame:
    return pd.DataFrame(_api_get(f"/api/modules/{dataset_id}"))


@st.cache_data(ttl=20)
def _imports() -> pd.DataFrame:
    return pd.DataFrame(_api_get("/api/imports"))


@st.cache_data(ttl=20)
def _import_preview(import_id: str) -> pd.DataFrame:
    return pd.DataFrame(_api_get(f"/api/imports/{import_id}/preview"))


@st.cache_data(ttl=20)
def _mapping_suggestion(import_id: str) -> Dict[str, Any]:
    return _api_get(f"/api/imports/{import_id}/mapping/suggestion")


@st.cache_data(ttl=20)
def _readiness(dataset_id: str) -> Dict[str, Any]:
    return _api_get(f"/api/readiness/{dataset_id}")


@st.cache_data(ttl=60)
def _calibration(dataset_id: str) -> Dict[str, Any]:
    return _api_get(f"/api/calibration/{dataset_id}")


@st.cache_data(ttl=300)
def _evidence(gene: str) -> Optional[Dict[str, Any]]:
    try:
        return _api_get(f"/api/evidence/{gene}")
    except Exception:
        return None


@st.cache_data(ttl=30)
def _dataset_status(dataset_id: str) -> Dict[str, Any]:
    try:
        return _api_get(f"/api/status/{dataset_id}")
    except Exception:
        return {}


@st.cache_data(ttl=300)
def _diseases() -> Dict[str, Any]:
    return _api_get("/api/disease")


@st.cache_data(ttl=60)
def _disease_targets(disease_name: str, dataset_id: str, min_grade: int, top_n: int) -> Dict[str, Any]:
    return _api_get(f"/api/disease/{disease_name}/targets/{dataset_id}", params={"min_grade": min_grade, "top_n": top_n})


def _compatibility_banner(dataset_id: str) -> None:
    """Warn when the active dataset is a user upload, keyed on its context tier."""
    status = _dataset_status(dataset_id)
    lineage = status.get("lineage") or {}
    if status.get("origin") != "user_upload" and lineage.get("kind") != "user_merge":
        return
    tier = lineage.get("context_tier", "unknown")
    name = lineage.get("source_name", dataset_id)
    if tier == "high_direct_context":
        st.success(f"User dataset '{name}' — CD4 direct context. Pathway/clinical axes apply.")
    elif tier == "compatible_context":
        st.info(f"User dataset '{name}' — compatible context. Pathway/clinical axes are advisory.")
    elif tier == "indirect_context":
        st.warning(f"User dataset '{name}' — indirect context. Interpret cross-context results with caution.")
    else:
        st.error(f"User dataset '{name}' — context unverified. Grades reflect statistics only; axes are advisory.")


def _metric_value(summary: Dict[str, Any], key: str) -> str:
    value = summary.get(key, 0)
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def _count_chart(records: Iterable[Dict[str, Any]], label_col: str) -> pd.DataFrame:
    df = pd.DataFrame(records)
    if df.empty or label_col not in df.columns or "n" not in df.columns:
        return pd.DataFrame()
    return df.set_index(label_col)[["n"]]


def _evidence_graph(target: str, row: Dict[str, Any]) -> str:
    pathway = str(row.get("pathway_axis") or "unassigned")
    clinical = str(row.get("clinical_axis") or "unassigned")
    grade = str(row.get("statistical_evidence_grade") or "NA")
    cap = str(row.get("score_cap_reason") or "none")
    return f"""
digraph evidence {{
  graph [rankdir=LR, bgcolor="transparent"];
  node [shape=box, style="rounded,filled", color="#9fb3c8", fillcolor="#f5f7fa", fontname="Arial"];
  edge [color="#6b7c93"];
  "{target}" -> "{pathway}";
  "{target}" -> "grade {grade}";
  "{pathway}" -> "{clinical}";
  "{clinical}" -> "{cap}";
}}
"""


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


def _register_upload() -> Dict[str, Any]:
    uploaded = st.session_state.get("import_file")
    if uploaded is None:
        raise RuntimeError("Choose a file to upload.")
    if getattr(uploaded, "size", 0) and uploaded.size > MAX_UPLOAD_BYTES:
        raise RuntimeError(f"Uploaded files must be <= {MAX_UPLOAD_BYTES // (1024 * 1024)} MB. Use local path registration for large raw-cell files.")
    content = uploaded.getvalue()
    if len(content) > MAX_UPLOAD_BYTES:
        raise RuntimeError(f"Uploaded files must be <= {MAX_UPLOAD_BYTES // (1024 * 1024)} MB. Use local path registration for large raw-cell files.")
    payload = {
        "source_name": st.session_state.get("import_source_name") or uploaded.name,
        "filename": uploaded.name,
        "content_base64": base64.b64encode(content).decode("ascii"),
        "declared_source_type": st.session_state.get("import_declared_type", "auto"),
        "mode": st.session_state.get("import_mode", "strict"),
        "notes": st.session_state.get("import_notes", ""),
    }
    return _api_post_timeout("/api/imports", payload, timeout=240)


def _register_local_path() -> Dict[str, Any]:
    file_path = st.session_state.get("import_file_path", "").strip()
    if not file_path:
        raise RuntimeError("Enter a local file path.")
    payload = {
        "source_name": st.session_state.get("path_source_name") or os.path.basename(file_path),
        "file_path": file_path,
        "declared_source_type": st.session_state.get("path_declared_type", "auto"),
        "mode": st.session_state.get("path_import_mode", "strict"),
        "notes": st.session_state.get("path_import_notes", ""),
    }
    return _api_post_timeout("/api/imports", payload, timeout=240)


def _render_imports_tab() -> None:
    st.subheader("Upload / Import Staging")
    st.caption("Imports are staged first. Approval marks a source as ready for downstream use, but does not merge it into target cards automatically.")

    source_types = ["auto", "target_evidence", "guide_evidence", "external_evidence", "metadata_manifest", "raw_cell_data"]
    import_cols = st.columns(2)
    with import_cols[0]:
        st.markdown("**Upload small table/source**")
        st.file_uploader("file", key="import_file", type=["csv", "tsv", "txt", "json", "jsonl"])
        st.text_input("source name", key="import_source_name", placeholder="e.g. external_pubmed_hits")
        st.selectbox("source type", source_types, key="import_declared_type")
        st.selectbox("mode", ["strict", "exploratory"], key="import_mode")
        st.text_area("notes", key="import_notes", height=80)
        if st.button("Stage uploaded file"):
            try:
                result = _register_upload()
                st.cache_data.clear()
                st.success(f"staged import_id={result['import_id']}")
            except Exception as e:
                st.error(f"Import failed: {e}")

    with import_cols[1]:
        st.markdown("**Register local large file**")
        st.caption("Local paths must be under the project root unless GWT_IMPORT_ALLOW_ROOTS is configured on the API server.")
        st.text_input("local file path", key="import_file_path", placeholder="D:\\data\\sample.assigned_guide.h5ad")
        st.text_input("source name", key="path_source_name", placeholder="e.g. GWT donor 1 Stim8hr")
        st.selectbox("source type", source_types, key="path_declared_type")
        st.selectbox("mode", ["strict", "exploratory"], key="path_import_mode")
        st.text_area("notes", key="path_import_notes", height=80)
        if st.button("Stage local path"):
            try:
                result = _register_local_path()
                st.cache_data.clear()
                st.success(f"staged import_id={result['import_id']}")
            except Exception as e:
                st.error(f"Import failed: {e}")

    try:
        import_df = _imports()
    except Exception as e:
        st.error(f"Could not load imports: {e}")
        return

    st.subheader("Staged sources")
    if import_df.empty:
        st.info("No staged imports yet.")
        return

    display_cols = [
        "import_id",
        "created_at",
        "source_name",
        "source_type",
        "route",
        "merge_status",
        "mode",
        "filename",
    ]
    display_cols = [c for c in display_cols if c in import_df.columns]
    st.dataframe(import_df[display_cols], use_container_width=True, hide_index=True)

    selected_import = st.selectbox("Inspect import", import_df["import_id"].tolist())
    selected_row = import_df[import_df["import_id"] == selected_import].iloc[0].to_dict()
    schema = selected_row.get("schema_validation", {}) or {}
    context = selected_row.get("context_match", {}) or {}

    metric_cols = st.columns(4)
    metric_cols[0].metric("Schema", schema.get("status", "unknown"))
    metric_cols[1].metric("Context score", context.get("score", "NA"))
    metric_cols[2].metric("Context tier", context.get("tier", "NA"))
    metric_cols[3].metric("Route", selected_row.get("route", "NA"))

    detail_cols = st.columns(2)
    with detail_cols[0]:
        st.markdown("**Warnings**")
        warnings = schema.get("warnings", [])
        if warnings:
            for warning in warnings:
                st.write(f"- {warning}")
        else:
            st.write("No schema warnings.")
    with detail_cols[1]:
        st.markdown("**Context reasons**")
        reasons = context.get("reasons", [])
        if reasons:
            for reason in reasons:
                st.write(f"- {reason}")
        else:
            st.write("No context evidence detected.")

    with st.expander("Import metadata", expanded=False):
        st.json(selected_row)

    preview_df = _import_preview(selected_import)
    if not preview_df.empty:
        st.subheader("Preview")
        st.dataframe(preview_df, use_container_width=True, hide_index=True)

    merge_status = str(selected_row.get("merge_status", ""))

    # Column-mapping wizard: available whenever mapping could unblock/relabel the import.
    if merge_status in {"blocked_needs_column_mapping", "staged_needs_classification"} or selected_row.get("source_type") in {"unknown_table", "target_evidence", "guide_evidence"}:
        with st.expander("Map columns", expanded=merge_status == "blocked_needs_column_mapping"):
            try:
                suggestion = _mapping_suggestion(selected_import)
            except Exception as e:
                suggestion = None
                st.error(f"Could not load mapping suggestion: {e}")
            if suggestion:
                uploaded_cols = suggestion.get("uploaded_columns", [])
                fields = suggestion.get("canonical_fields", {})
                suggested = suggestion.get("suggested", {})
                required = set(fields.get("required", []))
                st.caption("Map each canonical field to one of your uploaded columns (required fields marked *).")
                chosen: Dict[str, Any] = {}
                map_source_type = st.selectbox(
                    "source type", ["target_evidence", "guide_evidence"],
                    index=0 if suggestion.get("source_type") != "guide_evidence" else 1,
                    key=f"map_type_{selected_import}",
                )
                for canonical in fields.get("required", []) + fields.get("recommended", []):
                    label = f"{canonical} *" if canonical in required else canonical
                    options = ["<none>"] + uploaded_cols
                    default = suggested.get(canonical)
                    idx = options.index(default) if default in options else 0
                    pick = st.selectbox(label, options, index=idx, key=f"map_{selected_import}_{canonical}")
                    chosen[canonical] = None if pick == "<none>" else pick
                if st.button("Validate mapping", key=f"validate_map_{selected_import}"):
                    try:
                        result = _api_post(f"/api/imports/{selected_import}/mapping", {"map": chosen, "source_type": map_source_type})
                        st.cache_data.clear()
                        schema = result.get("schema_validation", {})
                        st.success(f"Mapping applied — schema {schema.get('status')}, status {result.get('merge_status')}")
                        for issue in schema.get("blocking_issues", []):
                            st.error(issue)
                    except Exception as e:
                        st.error(f"Mapping failed: {e}")

    if merge_status == "staged":
        if st.button("Approve staged table for downstream use"):
            try:
                _api_post(f"/api/imports/{selected_import}/approve", {"approved_by": "dashboard_user"})
                st.cache_data.clear()
                st.success("Import approved for downstream use.")
            except Exception as e:
                st.error(f"Approval failed: {e}")
    elif merge_status.startswith("approved"):
        st.success("This import is approved for downstream use.")
        if st.button("Merge into target cards", type="primary", key=f"merge_{selected_import}"):
            try:
                with st.spinner("Building cards from your dataset..."):
                    result = _api_post_timeout(f"/api/imports/{selected_import}/merge", {}, timeout=240)
                st.session_state["dataset_id"] = result["dataset_id"]
                st.cache_data.clear()
                st.success(f"Merged — dataset_id={result['dataset_id']} ({result['rows']} rows). Select it in the sidebar.")
            except Exception as e:
                st.error(f"Merge failed: {e}")
    elif merge_status == "merged_into_cards":
        st.success(f"Already merged into dataset {selected_row.get('merged_dataset_id', '')}.")
    else:
        st.warning(f"Approval blocked until review is resolved: {merge_status}")


st.set_page_config(page_title="GWT Target Evidence Browser", layout="wide")
st.markdown(
    """
    <style>
    .stMetric { border: 1px solid #d8dee8; border-radius: 6px; padding: 10px 12px; background: #fbfcfd; }
    div[data-testid="stDataFrame"] { border: 1px solid #d8dee8; border-radius: 6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("GWT Target Evidence Browser")

with st.sidebar:
    st.subheader("Dataset")
    st.text_input("API base", value=API_BASE, disabled=True)
    try:
        dataset_df = _datasets()
    except Exception:
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

dataset_id = st.session_state.get("dataset_id", "").strip()
if not dataset_id:
    st.info("Run a build, paste an existing dataset_id in the sidebar, or stage external sources in Imports.")
    import_only_tab = st.tabs(["Imports"])[0]
    with import_only_tab:
        _render_imports_tab()
    st.stop()

try:
    opts = _options(dataset_id)
    summary_payload = _summary(dataset_id, top_n=50)
except Exception as e:
    st.error(f"Dataset not available: {e}")
    st.stop()

summary = summary_payload.get("summary", {})
_compatibility_banner(dataset_id)
tabs = st.tabs(["Overview", "Target Explorer", "Pathway + Clinical", "Imports", "Export", "Disease Translator"])

with tabs[0]:
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
    top_df = pd.DataFrame(summary_payload.get("top_candidates", []))
    st.dataframe(top_df, use_container_width=True, hide_index=True)

    st.subheader("Watchlist")
    watch_df = pd.DataFrame(summary_payload.get("watchlist", []))
    st.dataframe(watch_df, use_container_width=True, hide_index=True)

    st.subheader("Readiness")
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

with tabs[1]:
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

        st.subheader("Readiness")
        try:
            readiness_rows = pd.DataFrame(_readiness(dataset_id).get("readiness", []))
            target_readiness = readiness_rows[readiness_rows["target"] == selected] if not readiness_rows.empty else pd.DataFrame()
            if not target_readiness.empty:
                rr = target_readiness.iloc[0].to_dict()
                rcols = st.columns(3)
                rcols[0].metric("R-stage", rr.get("overall_readiness_stage", "NA"))
                rcols[1].metric("Call", str(rr.get("readiness_call", "NA")))
                rcols[2].metric("Red flags", str(rr.get("red_flag_override", "none")))
                with st.expander("Readiness reasons", expanded=True):
                    for part in str(rr.get("readiness_reasons", "")).split(";"):
                        if part.strip():
                            st.write(f"- {part.strip()}")
                    st.info(f"Next validation step: {rr.get('next_validation_step', '')}")
                st.dataframe(
                    target_readiness[[c for c in ["condition", "overall_readiness_stage", "readiness_call", "biology_causality_score", "translation_score", "tractability_score", "red_flag_override"] if c in target_readiness.columns]],
                    use_container_width=True,
                    hide_index=True,
                )

                st.caption("Evidence components for this condition (not a summed total -- domains combine via rules, not addition).")
                domain_cols = [
                    "biology_causality_score",
                    "translation_score",
                    "tractability_score",
                    "biomarker_score",
                    "disease_relevance_score",
                    "clinical_feasibility_score",
                ]
                domain_values = {}
                for col in domain_cols:
                    val = rr.get(col)
                    domain_values[col] = pd.to_numeric(pd.Series([val]), errors="coerce").iloc[0]
                waterfall_series = pd.Series(domain_values, name="score").dropna()
                if not waterfall_series.empty:
                    st.bar_chart(waterfall_series)
                unknown_domains = [c for c in domain_cols if pd.isna(domain_values.get(c))]
                if unknown_domains:
                    st.caption(f"Not chartable (unknown -- no overlay/evidence yet): {', '.join(unknown_domains)}")
            else:
                st.info("No readiness record for this target.")
        except Exception as e:
            st.info(f"Readiness not available: {e}")

        st.subheader("External evidence")
        snapshot = _evidence(selected)
        if snapshot is None:
            st.info(f"No external evidence fetched yet for {selected}. Use the API to build it: POST /api/evidence/build {{\"genes\": [\"{selected}\"]}}")
        else:
            st.caption(f"Fetched {snapshot.get('fetched_at', 'NA')} · source_version {snapshot.get('source_version', 'NA')}")
            ev_cols = st.columns(3)
            sources = snapshot.get("sources", {})
            with ev_cols[0]:
                st.markdown("**Clinical trials**")
                trials = sources.get("clinical_trials", {})
                if trials.get("source_status") == "ok":
                    for t in trials.get("items", [])[:5]:
                        st.write(f"- [{t.get('nct_id', '')}]({t.get('url', '')}) {t.get('title', '')} ({t.get('phase') or 'NA'}, {t.get('status', 'NA')})")
                    if not trials.get("items"):
                        st.caption("No trials found.")
                else:
                    st.caption(f"unavailable: {trials.get('reason', 'not fetched')}")
            with ev_cols[1]:
                st.markdown("**Literature**")
                lit = sources.get("literature", {})
                if lit.get("source_status") == "ok":
                    for item in lit.get("items", [])[:5]:
                        st.write(f"- [{item.get('pmid', '')}]({item.get('url', '')}) {item.get('title', '')} ({item.get('year', 'NA')})")
                    if not lit.get("items"):
                        st.caption("No literature found.")
                else:
                    st.caption(f"unavailable: {lit.get('reason', 'not fetched')}")
            with ev_cols[2]:
                st.markdown("**Open Targets (tractability/genetics)**")
                ot = sources.get("open_targets", {})
                if ot.get("source_status") == "ok":
                    st.write(ot.get("items", []))
                else:
                    st.caption(f"unavailable: {ot.get('reason', 'not fetched')}")

        st.subheader("Evidence graph")
        st.graphviz_chart(_evidence_graph(selected, summary_row))

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

with tabs[2]:
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
    st.dataframe(module_df, use_container_width=True, hide_index=True)

with tabs[3]:
    _render_imports_tab()

with tabs[4]:
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

with tabs[5]:
    st.subheader("Disease Translator")
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
            st.dataframe(disease_df, use_container_width=True, hide_index=True)
            if "disease_association_score" in disease_df.columns and "target" in disease_df.columns:
                chart_df = disease_df.drop_duplicates("target").set_index("target")[["disease_association_score"]]
                st.bar_chart(chart_df)
