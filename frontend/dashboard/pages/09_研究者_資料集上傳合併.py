"""Streamlit page — 研究者 · Dataset upload & merge.

R6 (docs/frontend_design.md §3a): "As a researcher, I want to bring my own DE
results through the same scoring engine, so I can compare my screen on equal
footing with the reference dataset."

Extracted verbatim (behavior-preserving) from target_card_dashboard.py's
former "Imports" tab (`_render_imports_tab`), including the upload/local-path
registration helpers that were only ever used by that tab.

Isolation (frontend/README.md): talks to the backend ONLY via api_client's
HTTP helpers. Never imports `src/3_DE_analysis`.
"""

from __future__ import annotations

import base64
import os
from typing import Any, Dict

import streamlit as st

from api_client import _api_post, _api_post_timeout, _import_preview, _imports, _mapping_suggestion
from dataset_context import configure_page, render_sidebar

MAX_UPLOAD_BYTES = 25 * 1024 * 1024

configure_page("GWT Target Evidence Browser — Upload / Import")
render_sidebar()

st.title("Dataset upload & merge")


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
    import_df = None

if import_df is not None:
    st.subheader("Staged sources")
    if import_df.empty:
        st.info("No staged imports yet.")
    else:
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
