"""Streamlit page — 個體概念剖面(探索 demo).

COMPASS-style personalized concept waterfall (plan P4 / §2B). This page talks to
the backend ONLY over HTTP/JSON (POST /api/individual-concept-profile) — it never
imports backend modules. When the live endpoint is unreachable it renders an
inline SAMPLE payload (clearly labeled) so the tab stays demonstrable, but real
data is gated strictly behind the live HTTP call.

Hard requirements honored here:
  * forced §0 caveat header — rendered un-hideable at the top, no toggle;
  * the report's own `caveat` field is surfaced;
  * `unknown != 0` is honored visually (see concept_waterfall.build_waterfall_figure);
  * hypotheses are labeled HYPOTHESES, never recommendations;
  * the pasted / uploaded expression input is request-only and NEVER persisted.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import pandas as pd
import requests
import streamlit as st

from concept_waterfall import (
    CAVEAT_TEXT,
    SAMPLE_REPORT,
    build_waterfall_figure,
    parse_expression_table,
)

API_BASE = os.getenv("GWT_API_BASE", "http://127.0.0.1:8000").rstrip("/")
PROFILE_ENDPOINT = "/api/individual-concept-profile"


def _post_profile(sample_expression: Dict[str, float]) -> Dict[str, Any]:
    """Request-only call. The expression vector is sent to the API and NOT stored
    anywhere on the frontend (no cache decorator, no disk write, no session_state
    of the raw vector)."""
    url = f"{API_BASE}{PROFILE_ENDPOINT}"
    r = requests.post(url, json={"sample_expression": sample_expression}, timeout=120)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code}: {r.text}")
    return r.json()


def _forced_caveat_header() -> None:
    """Plan §0 boundary. Written into the code, rendered every run, un-hideable —
    there is no branch or toggle that can suppress it."""
    st.error(f"⚠️ {CAVEAT_TEXT}")


def _render_waterfall(report: Dict[str, Any]) -> None:
    profile: List[Dict[str, Any]] = report.get("concept_profile", []) or []
    if not profile:
        st.info("報告未包含 concept_profile。")
        return

    st.plotly_chart(
        build_waterfall_figure(profile),
        use_container_width=True,
        config={"displayModeBar": False},
    )
    st.caption(
        "顏色 = 方向(藍 上調 / 紅 下調);長度 = 活化強度;透明度 = 覆蓋率"
        "(越淡 = seed 基因覆蓋越低 = 越不可信);灰色斜線填滿的 placeholder = "
        "**unknown(無 seed 覆蓋),非測得 0**。"
    )

    # Table view (dataviz: a table view always exists alongside the chart).
    with st.expander("概念剖面資料表(可稽核)", expanded=False):
        df = pd.DataFrame(profile)
        preferred = [c for c in ["module_id", "module_name", "activation", "coverage", "direction"] if c in df.columns]
        st.dataframe(df[preferred] if preferred else df, use_container_width=True, hide_index=True)


def _render_hypotheses(report: Dict[str, Any]) -> None:
    st.subheader("連結的標的假設 — HYPOTHESES(非建議、非用藥)")
    st.caption(
        "以下是「篩過的 CRISPRi 標的中,哪些會調節某個異常概念」的**假設性線索**,"
        "不是診斷、不是治療建議、不是用藥。"
    )
    hyps: List[Dict[str, Any]] = report.get("connected_target_hypotheses", []) or []
    if not hyps:
        st.info("此報告沒有連結到任何標的假設。")
        return
    df = pd.DataFrame(hyps)
    cols = [c for c in ["gene", "module_id", "screen_direction", "readiness_call", "caveat"] if c in df.columns]
    rename = {
        "gene": "基因 (HYPOTHESIS)",
        "module_id": "概念",
        "screen_direction": "篩選方向",
        "readiness_call": "readiness_call",
        "caveat": "caveat",
    }
    show = df[cols].rename(columns=rename) if cols else df
    st.dataframe(show, use_container_width=True, hide_index=True)


def _render_report_caveat(report: Dict[str, Any]) -> None:
    caveat = str(report.get("caveat", "") or "").strip()
    if caveat:
        st.warning(f"報告內建 caveat: {caveat}")
    else:
        # Contract requires a non-empty caveat; make its absence loud rather than silent.
        st.error("報告缺少 caveat 欄位 — 此輸出不合規,不得使用。")


def _render_provenance(report: Dict[str, Any]) -> None:
    prov: Dict[str, Any] = report.get("provenance", {}) or {}
    bits = [
        f"concept_set_version = {prov.get('concept_set_version', 'NA')}",
        f"screen_data_version = {prov.get('screen_data_version', 'NA')}",
        f"computed_at = {prov.get('computed_at', 'NA')}",
        f"api_base = {API_BASE}",
    ]
    st.divider()
    st.caption("Provenance · " + " · ".join(bits))


# --------------------------------------------------------------------------- #
# Page body
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="個體概念剖面(探索 demo)", layout="wide")
st.title("個體概念剖面(探索 demo)")

# (1) FORCED, non-hideable safety header — first thing on the page, every run.
_forced_caveat_header()

st.markdown(
    "把單一 CD4 樣本的基因表現向量,透明地投影到 20 個免疫概念模組,"
    "畫成 COMPASS 式的個人化概念活化 waterfall,並列出**假設性**標的線索。"
    "這是可手算稽核的概念投影,**不是**黑箱預測。"
)

# (5) Input affordance — no identifier fields, request-only, not persisted.
st.subheader("輸入樣本表現向量")
st.caption(
    "只吃一張「基因 → 表現值」表(bulk 或 pseudobulk CD4;TPM/normalized 皆可)。"
    "**不要、也不會接受任何識別欄位**(姓名/病歷號/日期)。"
    "輸入只在本次請求記憶體內運算,**不儲存、不快取、不外傳**。"
)

in_cols = st.columns([3, 2])
with in_cols[0]:
    pasted = st.text_area(
        "貼上表現表(每行:GENE,value / GENE\\tvalue / GENE value)",
        height=180,
        placeholder="GATA3,2.4\nIL4R,1.9\nSTAT6,1.5\nTBX21,0.2",
        key="cw_pasted",
    )
with in_cols[1]:
    uploaded = st.file_uploader(
        "或上傳兩欄 CSV/TSV(gene, value)",
        type=["csv", "tsv", "txt"],
        key="cw_upload",
    )
    st.caption("表頭若含 gene/value 會自動忽略;多餘欄位不讀取。")

run_cols = st.columns([1, 1, 4])
compute_live = run_cols[0].button("投影(呼叫 API)", type="primary")
load_sample = run_cols[1].button("載入示範資料")


def _collect_expression() -> Dict[str, float]:
    expr: Dict[str, float] = {}
    if uploaded is not None:
        try:
            sep = "\t" if uploaded.name.endswith((".tsv", ".txt")) else ","
            up_df = pd.read_csv(uploaded, sep=sep)
            if up_df.shape[1] >= 2:
                gene_col, val_col = up_df.columns[0], up_df.columns[1]
                for g, v in zip(up_df[gene_col], up_df[val_col]):
                    try:
                        expr[str(g).strip()] = float(v)
                    except (TypeError, ValueError):
                        continue
        except Exception as e:  # noqa: BLE001
            st.error(f"無法解析上傳檔:{e}")
    expr.update(parse_expression_table(pasted or ""))
    expr.pop("", None)
    return expr


report: Dict[str, Any] = {}
source_note = ""

if compute_live:
    expr = _collect_expression()
    if not expr:
        st.warning("沒有可用的表現值 — 請貼上或上傳一張基因→值表,或點『載入示範資料』。")
    else:
        st.caption(f"送出 {len(expr)} 個基因至 API(不落地)。")
        try:
            report = _post_profile(expr)
            source_note = "live: POST " + PROFILE_ENDPOINT
        except Exception as e:  # noqa: BLE001
            st.error(f"呼叫 {PROFILE_ENDPOINT} 失敗:{e}")
            st.info("以下改用內建示範資料(SAMPLE),僅供介面展示,**非真實結果**。")
            report = SAMPLE_REPORT
            source_note = "SAMPLE fallback (endpoint unreachable)"
elif load_sample:
    report = SAMPLE_REPORT
    source_note = "SAMPLE (示範資料,非真實結果)"

if report:
    if source_note:
        if source_note.startswith("live"):
            st.success(f"資料來源:{source_note}")
        else:
            st.warning(f"資料來源:{source_note} — 僅供介面展示,非真實個體結果。")

    # (2b) surface the report's OWN caveat field.
    _render_report_caveat(report)
    # (1) waterfall: activation / direction / coverage / unknown-not-zero.
    _render_waterfall(report)
    # (3) hypotheses, explicitly labeled.
    _render_hypotheses(report)
    # (4) provenance footer.
    _render_provenance(report)
else:
    st.info("貼上或上傳一張表現表後按『投影』,或按『載入示範資料』預覽這個 demo。")
