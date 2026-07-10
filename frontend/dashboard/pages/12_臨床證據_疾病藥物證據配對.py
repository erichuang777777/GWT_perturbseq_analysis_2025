"""Streamlit page — 臨床證據 · 疾病 × 藥物證據配對 (disease x drug evidence match).

C3 (docs/frontend_design.md §3a/§5.2): "As a clinical reviewer, I want to
check whether a candidate drug has real trial evidence for this specific
disease, so I don't assume a drug works just because it hits the right
gene."

Wraps GET /api/disease-drug-evidence, a thin route (api/routers/disease_drug.py)
over the already-implemented match_disease_drug_evidence() -- answers two
separate, checkable facts and keeps them separate rather than collapsing them
into one score: (1) does this gene have a known drug, (2) has that drug
actually been trialled for THIS disease. A drug can legitimately target the
right gene and still carry zero trials for the disease asked about (e.g.
IL2RA's approved antibody basiliximab is trialled for kidney-transplant
rejection, not rheumatoid arthritis) -- that row is shown, never filtered out
(§5.2: hiding "no trials for this indication" rows is exactly the kind of
visual softening this feature exists to prevent).

Isolation (frontend/README.md): talks to the backend ONLY over HTTP/JSON. It
never imports `src/3_DE_analysis`.
"""

from __future__ import annotations

import os
from typing import Any, Dict

import pandas as pd
import requests
import streamlit as st

from guardrails import forced_caveat_header, render_response_caveat

API_BASE = os.getenv("GWT_API_BASE", "http://127.0.0.1:8000").rstrip("/")

CAVEAT_TEXT = (
    "evidence-matching only -- not a treatment recommendation or efficacy "
    "prediction; a nonzero drug count for this gene does not mean the drug "
    "has been trialled for the disease queried (see trials_for_this_disease "
    "per drug); verified drug-indication pairings must be confirmed against "
    "the drug label and a qualified physician"
)

# Real, previously-verified example (Module 3 doc §6 / tests/test_disease_drug_evidence.py):
# IL2RA has a known approved antibody, basiliximab, whose real indication is
# kidney-transplant rejection -- it carries ZERO trials for rheumatoid
# arthritis despite IL2RA being genetically associated with RA. This is not a
# fabricated demo value; it is the documented, tested real-world fact this
# feature exists to surface.
SAMPLE_RESPONSE: Dict[str, Any] = {
    "available": True,
    "gene": "IL2RA",
    "disease_queried": "rheumatoid arthritis",
    "ensembl_id": "ENSG00000134460",
    "n_known_drugs_for_gene": 2,
    "drugs": [
        {
            "drug_name": "BASILIXIMAB",
            "drug_type": "Antibody",
            "drug_class": "antibody (surface)",
            "max_clinical_stage": 4,
            "trials_for_this_disease": {"source_status": "ok", "n_trials": 0},
        },
        {
            "drug_name": "DACLIZUMAB",
            "drug_type": "Antibody",
            "drug_class": "antibody (surface)",
            "max_clinical_stage": 4,
            "trials_for_this_disease": {"source_status": "ok", "n_trials": 0},
        },
    ],
    "caveat": CAVEAT_TEXT,
    "fetched_at": "SAMPLE — not fetched live",
    "source_version": "SAMPLE",
}


def _get_evidence(gene: str, disease: str, max_drugs: int) -> Dict[str, Any]:
    r = requests.get(
        f"{API_BASE}/api/disease-drug-evidence",
        params={"gene": gene, "disease": disease, "max_drugs": max_drugs},
        timeout=60,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code}: {r.text}")
    return r.json()


st.set_page_config(page_title="臨床證據 · 疾病藥物證據配對", layout="wide")
st.title("臨床證據 · 疾病 × 藥物證據配對")

# (1) FORCED, non-hideable safety header — first thing on the page, every run.
forced_caveat_header(CAVEAT_TEXT)

st.markdown(
    "輸入一個基因與一個疾病名稱,檢查兩件分開、可查核的事實:"
    "(1) 這個基因是否有已知藥物;(2) 這個藥物是否**真的**在這個疾病上做過臨床試驗——"
    "而不是把兩者混成單一分數。一個藥物可以正中基因,卻對你查詢的疾病完全沒有試驗"
    "(例如 IL2RA 的 basiliximab 核准用於腎臟移植排斥,而非類風濕性關節炎)。"
)

in_cols = st.columns([2, 2, 1])
with in_cols[0]:
    gene_query = st.text_input("基因 symbol", value="", placeholder="例如 IL2RA", key="ddm_gene")
with in_cols[1]:
    disease_query = st.text_input("疾病名稱", value="", placeholder="例如 rheumatoid arthritis", key="ddm_disease")
with in_cols[2]:
    max_drugs = st.number_input("最多顯示幾種藥物", min_value=1, max_value=50, value=10, key="ddm_max_drugs")

run_cols = st.columns([1, 1, 4])
query_live = run_cols[0].button("查詢(呼叫 API)", type="primary")
load_sample = run_cols[1].button("載入已驗證範例(IL2RA + RA)")

result: Dict[str, Any] = {}
source_note = ""

if query_live:
    if not gene_query.strip() or not disease_query.strip():
        st.warning("請同時輸入基因與疾病名稱。")
    else:
        try:
            result = _get_evidence(gene_query.strip(), disease_query.strip(), int(max_drugs))
            source_note = "live: GET /api/disease-drug-evidence"
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
        st.info(f"查無證據(honest fallback):{result.get('reason', 'unknown')}")
    else:
        render_response_caveat(result)
        st.subheader(f"{result.get('gene')} 已知藥物 x {result.get('disease_queried')} 試驗證據")
        st.caption(f"共 {result.get('n_known_drugs_for_gene', 0)} 種已知藥物(Open Targets)。")

        drugs = result.get("drugs", []) or []
        if not drugs:
            st.info("此基因在 Open Targets 沒有已知藥物(measured empty,非未檢查)。")
        else:
            rows = []
            for d in drugs:
                trial_info = d.get("trials_for_this_disease") or {}
                rows.append(
                    {
                        "drug_name": d.get("drug_name"),
                        "drug_type": d.get("drug_type"),
                        "drug_class": d.get("drug_class"),
                        "max_clinical_stage": d.get("max_clinical_stage"),
                        "n_trials_for_this_disease": trial_info.get("n_trials"),
                        "trial_lookup_status": trial_info.get("source_status"),
                    }
                )
            df = pd.DataFrame(rows)
            # Every drug is shown, including zero-trial rows -- filtering those
            # out would hide exactly the mismatch this page exists to surface.
            st.dataframe(df, use_container_width=True, hide_index=True)
            zero_trial = df[df["n_trials_for_this_disease"] == 0]
            if not zero_trial.empty:
                st.caption(
                    f"⚠️ {len(zero_trial)} 種藥物對此疾病的試驗數為 0——"
                    "有已知藥物不代表這個藥物治療過這個疾病。"
                )

    st.divider()
    st.caption(
        f"Provenance · fetched_at = {result.get('fetched_at', 'NA')} · "
        f"source_version = {result.get('source_version', 'NA')} · api_base = {API_BASE}"
    )
else:
    st.info("輸入基因與疾病後按『查詢』,或按『載入已驗證範例』預覽這個頁面。")
