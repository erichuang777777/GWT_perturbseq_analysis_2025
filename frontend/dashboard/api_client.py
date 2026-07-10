"""Shared HTTP client + cached fetchers for the frontend dashboard's pages.

Extracted (docs/frontend_design.md §6/§7 persona-split redesign) out of
``target_card_dashboard.py`` so the researcher pages (now one Streamlit
``pages/*.py`` file per former tab, plus the landing page) don't each
redefine the same ``_api_get``/``_api_post``/etc. helpers and per-endpoint
``@st.cache_data`` fetchers. Pure code motion -- no behavior change; every
function here is byte-for-byte the same body it had in
``target_card_dashboard.py`` before the split.

Isolation (frontend/README.md): this module talks to the backend ONLY over
HTTP/JSON via ``_api_get``/``_api_post``/etc. It never imports anything from
``src/3_DE_analysis``.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Iterable, Optional

import pandas as pd
import requests
import streamlit as st

API_BASE = os.getenv("GWT_API_BASE", "http://127.0.0.1:8000").rstrip("/")

# The researcher target-dossier page's filename. Centralized here so every
# page that deep-links to it (via `_selectable_table_with_dossier_link`)
# reads one constant instead of a hardcoded string repeated per page. Padded
# "08" (not "8") because Streamlit sorts multipage filenames as STRINGS --
# an unpadded "8" would sort after "10", "11", "12", "13" alphabetically.
DOSSIER_PAGE_PATH = "pages/08_研究者_標的檔案_target_dossier.py"


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


@st.cache_data(ttl=60)
def _gene_search(query: str, limit: int = 10) -> Dict[str, Any]:
    return _api_get("/api/search", params={"q": query, "limit": limit})


@st.cache_data(ttl=60)
def _gene_status(query: str, dataset_id: Optional[str] = None) -> Dict[str, Any]:
    params = {"q": query}
    if dataset_id:
        params["dataset_id"] = dataset_id
    return _api_get("/api/genes/status", params=params)


@st.cache_data(ttl=60)
def _immune_ranked(dataset_id: str, top_n: int = 100, stimulation_gated_only: bool = False) -> Dict[str, Any]:
    return _api_get(
        f"/api/immune_ranked/{dataset_id}",
        params={"top_n": top_n, "stimulation_gated_only": stimulation_gated_only},
    )


@st.cache_data(ttl=60)
def _switches(dataset_id: str, top_n: int = 100) -> Dict[str, Any]:
    return _api_get(f"/api/switches/{dataset_id}", params={"top_n": top_n})


@st.cache_data(ttl=60)
def _robust_ranked(dataset_id: str, strict: bool = False, lenient: bool = False, top_n: int = 100) -> Dict[str, Any]:
    return _api_get(
        f"/api/robust_ranked/{dataset_id}",
        params={"strict": strict, "lenient": lenient, "top_n": top_n},
    )


@st.cache_data(ttl=60)
def _genetic_double_support(dataset_id: str, min_grade: int = 2, trait: str = "lymphocyte_count") -> Dict[str, Any]:
    return _api_get(
        f"/api/genetic_double_support/{dataset_id}",
        params={"min_grade": min_grade, "trait": trait},
    )


@st.cache_data(ttl=60)
def _triage(dataset_id: str, top_n: int = 100) -> Dict[str, Any]:
    return _api_get(f"/api/triage/{dataset_id}", params={"top_n": top_n})


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


def _selectable_table_with_dossier_link(df: pd.DataFrame, table_key: str) -> None:
    """Render a single-row-selectable table (FE-1 sender). When a row is picked,
    offer a button that deep-links to the target dossier page for that target via
    query params + st.switch_page. Read-only; frontend stays isolated."""
    disp = df.reset_index(drop=True)
    event = st.dataframe(
        disp,
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun",
        key=table_key,
    )
    rows = []
    try:
        sel = getattr(event, "selection", None)
        rows = list(sel.rows) if sel is not None else []
    except Exception:
        rows = []
    if not rows:
        st.caption("↑ 選一列以開啟該標的的完整檔案(target dossier)。")
        return
    target = str(disp.iloc[rows[0]].get("target", "")).strip()
    if target and st.button(f"開啟標的檔案:{target} →", key=f"{table_key}_open"):
        st.query_params.update({"dataset_id": st.session_state.get("dataset_id", ""), "target": target})
        st.switch_page(DOSSIER_PAGE_PATH)
