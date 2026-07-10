"""Streamlit landing page — persona picker (docs/frontend_design.md).

This used to be a single monolithic dashboard: one script, eight
``st.tabs(...)``, every tab's body a ``render_*()`` function closing over
module-level dataset-selection state. Per the persona-split redesign, each
former tab is now its own standalone page under ``pages/`` (numbered 01-10
for the researcher workspace, 11-13 for the clinical-evidence workspace);
this script's only remaining job is to greet a first-time visitor and point
them at the workspace matching their question -- "who you are" -> "where to
click first" -- before they've picked a dataset or a gene.

Both personas hit the same unauthenticated FastAPI app; there is no backend
permission boundary between them (docs/frontend_design.md §2) -- this page
is a navigation aid, not a gate. Every page remains reachable from the
sidebar regardless of which card a visitor clicks here.

Isolation (frontend/README.md): this file lives in the ISOLATED `frontend/`
package. It talks to the FastAPI backend ONLY over HTTP/JSON. It never
imports any `src/3_DE_analysis` module.
"""

from __future__ import annotations

import os

import streamlit as st

API_BASE = os.getenv("GWT_API_BASE", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="GWT Target Evidence Browser", layout="wide")
st.title("GWT Target Evidence Browser")

st.warning(
    "🔬 **研究用途(research use only)** — 本工具為 CD4 T-cell Perturb-seq 標的發現的"
    "探索性研究工具,**非臨床軟體**、非診斷、非治療或用藥建議。"
)

st.markdown(
    """
**CD4 T-cell Perturb-seq 標的發現工具** — turns a CRISPRi knockdown screen in primary human
CD4⁺ T cells into decision-ready, evidence-integrated **target cards**. Research /
hypothesis-generating use only — **not** clinical software.

選擇下面其中一個工作區開始(兩者都呼叫同一個公開、無驗證的 API;彼此隨時互相可達,
這裡只是導覽,不是權限邊界)。
    """
)

col_researcher, col_clinical = st.columns(2)

with col_researcher:
    st.subheader("🔬 研究者工作區 · Researcher workspace")
    st.caption(
        "篩選 / 排序 / 比對標的,檢視 readiness + calibration,建置或合併資料集,匯出報告。"
        "從左側側邊欄的「01_研究者_總覽」開始。"
    )
    if st.button("開啟研究者總覽 →", key="goto_researcher", type="primary"):
        st.switch_page("pages/01_研究者_總覽_overview.py")

with col_clinical:
    st.subheader("🩺 臨床證據工作區 · Clinical-evidence lookup")
    st.caption(
        "貼上一個樣本的表現量、或查詢一個疾病+藥物配對,取得透明、可稽核的證據——"
        "不需要熟悉整個篩選實驗的細節。從左側側邊欄的「11_臨床證據_個體概念剖面」開始。"
    )
    if st.button("開啟臨床證據首頁 →", key="goto_clinical", type="primary"):
        st.switch_page("pages/11_臨床證據_個體概念剖面.py")

st.divider()

with st.expander("ℹ️ 開始使用 · What is this & how to start", expanded=False):
    st.markdown(
        f"""
**How to start:** pick a workspace above (or use the sidebar directly) →
researcher pages need a dataset selected in their own sidebar; clinical-evidence
pages work standalone (paste a sample, or query a gene/disease pair).

**Query the data yourself:** a documented REST API lives at
[`{API_BASE}/docs`]({API_BASE}/docs) (Swagger UI) and [`{API_BASE}/redoc`]({API_BASE}/redoc);
see `docs/API.md` for a curl/Python quickstart. `{API_BASE}/api/health` reports engine/schema
versions.

**Reading the data:** every value is source- & version-stamped; **`unknown` is shown as
unknown, never as `0`** (a gene not yet checked is not a measured zero); descriptive evidence
is kept separate from the final advance/validate/watchlist/deprioritize call. See the
glossary (ℹ️ 名詞解釋) on the researcher pages for what each readiness call does and does
NOT mean.

**Design doc:** docs/frontend_design.md records the full persona-split rationale and the
constraints every clinical-evidence page must respect (no auth/persistence, population-level
≠ patient-level, descriptive/decision separation).
        """
    )
