"""Streamlit page — 臨床證據 · 群體遺傳查詢 (population genetics lookup).

C4 (docs/frontend_design.md §3a/§5.3): "As a clinical reviewer, I want
independent population-level genetic evidence for a gene, so I have a
second, checkable line of support beyond the screen itself."

Wraps the existing GET /api/population-hypothesis/{gene} -- already
implemented and already surfaced inside the researcher target-dossier page
(pages/08_研究者_標的檔案_target_dossier.py, UK Biobank LoF-burden hypothesis
section). Per docs/frontend_design.md §5.3, the clinical-evidence persona gets
its own standalone gene+trait lookup here rather than only a cross-link to
that dossier section -- a smaller ask than "open the full researcher
dossier to find one section". Both surfaces call the same read-only
endpoint; neither writes anything.

The result must show a CI-includes-zero row exactly as plainly as a
CI-excludes-zero one -- a non-significant gene is reported, not hidden. This
page renders whichever real result comes back with equal visual weight; it
does not filter, re-rank, or de-emphasize a null (CI-includes-zero) finding.

Isolation (frontend/README.md): talks to the backend ONLY over HTTP/JSON. It
never imports `src/3_DE_analysis`.
"""

from __future__ import annotations

import os
from typing import Any, Dict

import requests
import streamlit as st

from guardrails import forced_caveat_header

API_BASE = os.getenv("GWT_API_BASE", "http://127.0.0.1:8000").rstrip("/")

CAVEAT_TEXT = "群體層級關聯的假設,非個人化預測、非診斷、非用藥建議。"

# Real, previously-verified example (matches the SAMPLE_POPULATION fixture
# already used as the offline fallback on pages/08_研究者_標的檔案_target_dossier.py)
# -- not a fabricated value, the same fact already relied on elsewhere in this repo.
SAMPLE_RESPONSE: Dict[str, Any] = {
    "gene": "IL2RA",
    "trait": "lymphocyte_count",
    "available": True,
    "matched": True,
    "found_in_burden_table": True,
    "disease_area": "immune",
    "direction": "LoF associated with lower lymphocyte count",
    "post_mean": -0.12,
    "ci_excludes_zero": True,
    "population_hypothesis": (
        "Rare LoF carriers trend to lower lymphocyte count — "
        "consistent with IL2RA's role in lymphocyte homeostasis (hypothesis, not a patient prediction)."
    ),
    "caveat": CAVEAT_TEXT,
}


def _get_population_hypothesis(gene: str, trait: str) -> Dict[str, Any]:
    r = requests.get(f"{API_BASE}/api/population-hypothesis/{gene}", params={"trait": trait}, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code}: {r.text}")
    return r.json()


st.set_page_config(page_title="臨床證據 · 群體遺傳查詢", layout="wide")
st.title("臨床證據 · 群體遺傳查詢")

forced_caveat_header(CAVEAT_TEXT)

st.markdown(
    "輸入一個基因與一個性狀(trait),查詢 UK Biobank 的稀有 LoF(loss-of-function)"
    "負擔估計。這是**群體層級**的關聯假設,不是個人化預測——"
    "CI 涵蓋 0(不顯著)的結果會跟 CI 不涵蓋 0(顯著)的結果**以相同的視覺權重**呈現,"
    "不隱藏、不淡化空結果。"
)

in_cols = st.columns([2, 2, 1])
with in_cols[0]:
    gene_query = st.text_input("基因 symbol", value="", placeholder="例如 IL2RA", key="pg_gene")
with in_cols[1]:
    trait_query = st.text_input("性狀 trait", value="lymphocyte_count", key="pg_trait")

run_cols = st.columns([1, 1, 4])
query_live = run_cols[0].button("查詢(呼叫 API)", type="primary")
load_sample = run_cols[1].button("載入已驗證範例(IL2RA)")

result: Dict[str, Any] = {}
source_note = ""

if query_live:
    if not gene_query.strip():
        st.warning("請輸入基因 symbol。")
    else:
        try:
            result = _get_population_hypothesis(gene_query.strip(), trait_query.strip() or "lymphocyte_count")
            source_note = "live: GET /api/population-hypothesis/{gene}"
        except Exception as e:  # noqa: BLE001
            st.error(f"呼叫 API 失敗:{e}")
            st.info("以下改用內建已驗證範例(SAMPLE),僅供介面展示,**非即時查詢結果**。")
            result = SAMPLE_RESPONSE
            source_note = "SAMPLE fallback (endpoint unreachable)"
elif load_sample:
    result = SAMPLE_RESPONSE
    source_note = "SAMPLE (已驗證範例,非即時查詢結果)"

if result:
    if source_note:
        if source_note.startswith("live"):
            st.success(f"資料來源:{source_note}")
        else:
            st.warning(f"資料來源:{source_note}")

    if not result.get("available", False):
        st.info(f"查無群體遺傳資料(honest fallback):{result.get('reason', 'unknown')}")
    elif result.get("matched") is False or result.get("found_in_burden_table") is False:
        st.info(f"此基因無群體 LoF-burden 估計:{result.get('reason', '')}")
    else:
        st.subheader(f"{result.get('gene')} — {result.get('trait')}")
        cols = st.columns(5)
        cols[0].metric("Disease area", str(result.get("disease_area", "NA")))
        cols[1].metric("Direction", str(result.get("direction", "NA")))
        cols[2].metric("Post mean", str(result.get("post_mean", "NA")))
        # CI-includes-zero and CI-excludes-zero are rendered with the SAME
        # st.metric — no color/size difference that would de-emphasize a null.
        cols[3].metric("CI excludes 0", str(result.get("ci_excludes_zero", "NA")))
        cols[4].metric("Trait", str(result.get("trait", "NA")))
        hyp = result.get("population_hypothesis")
        if hyp:
            st.info(f"假設 hypothesis(非個人預測):{hyp}")
        else:
            st.caption("此性狀無群體假設敘述(可能是 CI 涵蓋 0 的非顯著結果)。")

    caveat = str(result.get("caveat", "") or "").strip()
    if caveat:
        st.warning(f"報告內建 caveat: {caveat}")

    st.divider()
    st.caption(f"Provenance · api_base = {API_BASE}")
else:
    st.info("輸入基因後按『查詢』,或按『載入已驗證範例』預覽這個頁面。")
