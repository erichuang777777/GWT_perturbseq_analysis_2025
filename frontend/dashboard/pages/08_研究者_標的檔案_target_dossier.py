"""Streamlit page — 標的檔案 · Target Dossier(一個標的一頁).

Phase 2 of docs/server_northstar.md (§3 支柱一 UI friendly + §5 Phase 2): an
entity-centric target dossier — the way Open Targets / Pharos / cBioPortal give
each entity ONE rich profile page, with evidence split into titled, modular,
source-stamped widgets rendered top-to-bottom.

Isolation (frontend/README.md, NON-NEGOTIABLE):
    This file lives in the ISOLATED `frontend/` package. It talks to the FastAPI
    backend ONLY over HTTP/JSON via the `_api_get` helper (copied from
    target_card_dashboard.py — NOT imported from the backend). It never imports
    any `src/3_DE_analysis` module.

    Note: this page does NOT reuse `concept_waterfall`/`SAMPLE_REPORT` (the
    pasted-expression-table demo on pages/11_臨床證據_個體概念剖面.py). It
    previously rendered that IL2RA fixture unconditionally under the "CD4
    concept profile" heading, so every target's dossier showed an identical
    waterfall regardless of which gene was queried. Fixed: this page now shows
    only the real per-target module hits from GET /api/modules/{dataset_id}.

資料明確 (§3 支柱二, honored throughout):
    * `unknown != 0` — an unmeasured/unchecked field renders as a distinct grey
      「未檢查」chip via `_val_chip`, NEVER as a 0-value number/bar that reads as
      measured. A real measured 0 renders as a normal value chip. A missing whole
      section renders 「未取得 (not available)」, never an error/traceback.
    * Provenance chips — every section stamps its source + version/fetched_at
      where the API provides it (`_provenance`).
    * Descriptive-vs-decision — the concept / mechanism / safety-genetics /
      external sections are explicitly marked DESCRIPTIVE and do NOT move the
      readiness call (`_descriptive_note`).
    * Research-use disclaimer in the page header.

When the live API is unreachable, each fetcher falls back to a small inline
SAMPLE payload (shaped to match the real endpoint contract) that is LOUDLY
labeled as a fixture, not real data — mirroring pages/11_臨床證據_個體概念剖面.py.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
import streamlit as st

# Shared evidence-chip primitives (FE-3) — the `unknown != 0` visual grammar now
# lives in `ui_chips` so the main dashboard reuses the SAME helpers. Behaviour is
# preserved verbatim: the old `_name` aliases below keep the rest of this page
# byte-for-byte identical in behaviour to before the extraction.
from glossary import render_glossary_expander
from nav import seed_dossier_session
from ui_chips import format_concept_chips
from ui_chips import (
    descriptive_note as _descriptive_note,
    fields_row as _fields_row,
    flag_chip as _flag_chip,
    fmt as _fmt,
    inject_chip_css,
    is_unknown as _is_unknown,
    labeled as _labeled,
    not_available as _not_available,
    provenance_line as _provenance,
    val_chip as _val_chip,
)

API_BASE = os.getenv("GWT_API_BASE", "http://127.0.0.1:8000").rstrip("/")


# --------------------------------------------------------------------------- #
# HTTP client — copied small helper (frontend isolation: never import backend).
# --------------------------------------------------------------------------- #
def _api_get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    url = f"{API_BASE}{path}"
    r = requests.get(url, params=params, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code}: {r.text}")
    return r.json()


# NOTE: the `unknown != 0` chip primitives and `_CSS` string that used to live
# here now come from `ui_chips` (imported + aliased at the top of this file, FE-3).

# --------------------------------------------------------------------------- #
# Inline SAMPLE payloads — each matches the shape of the named live endpoint.
# Used ONLY when the live API is unreachable, and LOUDLY labeled as a fixture.
# Real data must come from the live HTTP call.
# --------------------------------------------------------------------------- #
_SAMPLE_DATASET_ID = "gwt_reference::SAMPLE"
_SAMPLE_TARGET = "IL2RA"

SAMPLE_DATASETS: List[Dict[str, Any]] = [
    {"dataset_id": _SAMPLE_DATASET_ID, "origin": "gwt_reference", "built_at": "SAMPLE"},
]

SAMPLE_RESOLVE: Dict[str, Any] = {
    "query": _SAMPLE_TARGET,
    "matched": True,
    "resolution_path": "exact_canonical_symbol",
    "ensembl_gene_id": "ENSG00000134460",
    "canonical_symbol": _SAMPLE_TARGET,
}

SAMPLE_SEARCH: Dict[str, Any] = {
    "query": "IL2",
    "results": [
        {"ensembl_gene_id": "ENSG00000134460", "canonical_symbol": "IL2RA", "match_type": "prefix", "score": 0.93},
        {"ensembl_gene_id": "ENSG00000102265", "canonical_symbol": "IL2RB", "match_type": "prefix", "score": 0.90},
        {"ensembl_gene_id": "ENSG00000109471", "canonical_symbol": "IL2", "match_type": "exact", "score": 1.0},
    ],
}

# /api/targets/{dataset_id}/{target_id}
SAMPLE_TARGET_DETAIL: Dict[str, Any] = {
    "target": _SAMPLE_TARGET,
    "summary": {
        "target": _SAMPLE_TARGET,
        "target_id": "ENSG00000134460",
        "condition": "Stim_8hr",
        "statistical_evidence_grade": 3,
        "kd_status": "confirmed",
        "kd_efficiency": 0.71,
        "ontarget_effect_size": -1.84,
        "ontarget_significant": True,
        "n_total_de_genes": 214,
        "n_up_genes": 96,
        "n_down_genes": 118,
        "n_cells_target": 812,
        "n_guides": 4,
        "n_donors": 3,
        "crossguide_correlation": 0.41,
        "crossdonor_correlation_mean": 0.33,
        "crossdonor_correlation_min": 0.19,
        "replicate_pass_flag": True,
        "offtarget_flag": False,
        "effect_direction_flip_flag": False,
        "batch_sensitivity_flag": False,
        "condition_specificity_score": 0.62,
        "score_cap_reason": "none",
        "pathway_axis": "IL2R_JAKSTAT",
        "clinical_axis": "immune_tolerance",
        "druggable_class": "cytokine_receptor",
        "tractability_modality": "antibody (surface)",
        "safety_note": "broadly expressed on Tregs; on-target Treg depletion risk",
        "genetic_support_confidence": "strong_genetic_association",
        "genetic_support_max_genetic_score": 0.74,
        "composite_safety_liability": "moderate",
        "safety_window_score": 18,
        "gnomad_constraint_flag": "none",
    },
    "rows": [],
}

# /api/readiness/{dataset_id} — one matching row for the sample target
SAMPLE_READINESS: Dict[str, Any] = {
    "dataset_id": _SAMPLE_DATASET_ID,
    "rows": 1,
    "counts": {"R2": 1},
    "call_counts": {"watchlist": 1},
    "overlays_missing": ["chembl", "open_targets_genetics", "depmap", "patient_scrna"],
    "readiness": [
        {
            "target": _SAMPLE_TARGET,
            "condition": "Stim_8hr",
            "overall_readiness_stage": "R2",
            "readiness_call": "watchlist",
            "red_flag_override": "none",
            "readiness_reasons": "strong on-target KD (confirmed); grade 3 statistics; "
            "cross-donor robustness moderate (0.33); genetic support strong; "
            "on-target Treg-depletion safety liability flagged (descriptive)",
            "next_validation_step": "orthogonal guide + protein-level KD confirmation, "
            "then Treg-specific functional readout",
            "biology_causality_score": 5,
            "translation_score": 3,
            "tractability_score": 3,
            "genetic_support_confidence": "strong_genetic_association",
            "composite_safety_liability": "moderate",
            "safety_window_score": 18,
            "gnomad_constraint_flag": "none",
            "has_external_evidence": True,
        }
    ],
}

# /api/mechanism-graph/{gene}
SAMPLE_MECHANISM: Dict[str, Any] = {
    "gene_query": _SAMPLE_TARGET,
    "resolution": SAMPLE_RESOLVE,
    "dataset_id": None,
    "gene": _SAMPLE_TARGET,
    "available": True,
    "reason": None,
    "fetched_at": "2025-11-02T00:00:00Z (SAMPLE)",
    "source_version": "reactome+string::SAMPLE",
    "reactome_status": "ok",
    "string_status": "ok",
    "nodes": [
        {"id": "IL2RA", "type": "gene", "role": "query", "evidence_available": True},
        {"id": "pathway:R-HSA-449147", "type": "pathway", "pathway_id": "R-HSA-449147",
         "pathway_name": "Signaling by Interleukins", "is_in_disease": False},
        {"id": "pathway:R-HSA-912694", "type": "pathway", "pathway_id": "R-HSA-912694",
         "pathway_name": "Interleukin-2 signaling", "is_in_disease": False},
        {"id": "IL2RB", "type": "gene", "role": "string_partner", "evidence_available": False},
        {"id": "JAK3", "type": "gene", "role": "string_partner", "evidence_available": False},
        {"id": "STAT5A", "type": "gene", "role": "string_partner", "evidence_available": False},
    ],
    "edges": [
        {"source": "IL2RA", "target": "pathway:R-HSA-912694", "relationship": "reactome_pathway_comembership"},
        {"source": "IL2RA", "target": "pathway:R-HSA-449147", "relationship": "reactome_pathway_comembership"},
        {"source": "IL2RA", "target": "IL2RB", "relationship": "string_interaction", "score": 0.999},
        {"source": "IL2RA", "target": "JAK3", "relationship": "string_interaction", "score": 0.94},
        {"source": "IL2RA", "target": "STAT5A", "relationship": "string_interaction", "score": 0.90},
    ],
}

# /api/population-hypothesis/{gene}
SAMPLE_POPULATION: Dict[str, Any] = {
    "available": True,
    "matched": True,
    "found_in_burden_table": True,
    "gene": _SAMPLE_TARGET,
    "trait": "lymphocyte_count",
    "disease_area": "immune",
    "direction": "LoF associated with lower lymphocyte count",
    "post_mean": -0.12,
    "ci_excludes_zero": True,
    "population_hypothesis": "Rare LoF carriers trend to lower lymphocyte count — "
    "consistent with IL2RA's role in lymphocyte homeostasis (hypothesis, not a patient prediction).",
    "caveat": "群體層級關聯的假設,非個人化預測、非診斷、非用藥建議。",
}

# /api/evidence/{gene}
SAMPLE_EVIDENCE: Dict[str, Any] = {
    "gene": _SAMPLE_TARGET,
    "fetched_at": "2025-10-20T00:00:00Z (SAMPLE)",
    "source_version": "external_cache::SAMPLE",
    "sources": {
        "clinical_trials": {
            "source_status": "ok",
            "items": [
                {"nct_id": "NCT00000000", "url": "https://clinicaltrials.gov/study/NCT00000000",
                 "title": "Anti-CD25 (IL2RA) mAb in autoimmune disease (SAMPLE)", "phase": "PHASE2", "status": "COMPLETED"},
            ],
        },
        "literature": {
            "source_status": "ok",
            "items": [
                {"pmid": "00000000", "url": "https://pubmed.ncbi.nlm.nih.gov/00000000",
                 "title": "IL2RA in regulatory T-cell biology (SAMPLE)", "year": 2023},
            ],
        },
        "open_targets": {
            "source_status": "ok",
            "items": ["EFO_0000685 rheumatoid arthritis"],
            "associated_diseases": [
                {"disease": "rheumatoid arthritis", "genetic_association_score": 0.74},
            ],
        },
    },
}


SAMPLE_BANNER = "⚠️ 目前顯示的是內建 **SAMPLE 示範資料**(API 無法連線),僅供介面展示,**非真實結果**。"


# --------------------------------------------------------------------------- #
# Cached fetchers with sample fallback. Each returns (payload, is_sample).
# --------------------------------------------------------------------------- #
@st.cache_data(ttl=30, show_spinner=False)
def _datasets() -> Tuple[List[Dict[str, Any]], bool]:
    try:
        return _api_get("/api/datasets"), False
    except Exception:
        return SAMPLE_DATASETS, True


@st.cache_data(ttl=30, show_spinner=False)
def _search(q: str, limit: int = 10) -> Tuple[Dict[str, Any], bool]:
    try:
        return _api_get("/api/search", params={"q": q, "limit": limit}), False
    except Exception:
        return SAMPLE_SEARCH, True


@st.cache_data(ttl=30, show_spinner=False)
def _resolve(q: str) -> Tuple[Dict[str, Any], bool]:
    try:
        return _api_get("/api/genes/resolve", params={"q": q}), False
    except Exception:
        return dict(SAMPLE_RESOLVE, query=q), True


@st.cache_data(ttl=30, show_spinner=False)
def _target_detail(dataset_id: str, target: str) -> Tuple[Optional[Dict[str, Any]], bool]:
    try:
        return _api_get(f"/api/targets/{dataset_id}/{target}"), False
    except Exception:
        # Offline we cannot tell "target genuinely absent" from "API down", so
        # we always fall back to the loudly-labeled sample.
        return SAMPLE_TARGET_DETAIL, True


@st.cache_data(ttl=30, show_spinner=False)
def _readiness(dataset_id: str) -> Tuple[Optional[Dict[str, Any]], bool]:
    try:
        return _api_get(f"/api/readiness/{dataset_id}"), False
    except Exception:
        return SAMPLE_READINESS, True


@st.cache_data(ttl=30, show_spinner=False)
def _mechanism(gene: str) -> Tuple[Dict[str, Any], bool]:
    try:
        return _api_get(f"/api/mechanism-graph/{gene}"), False
    except Exception:
        return SAMPLE_MECHANISM, True


@st.cache_data(ttl=30, show_spinner=False)
def _population(gene: str) -> Tuple[Dict[str, Any], bool]:
    try:
        return _api_get(f"/api/population-hypothesis/{gene}"), False
    except Exception:
        return SAMPLE_POPULATION, True


@st.cache_data(ttl=60, show_spinner=False)
def _evidence(gene: str) -> Tuple[Optional[Dict[str, Any]], bool]:
    try:
        return _api_get(f"/api/evidence/{gene}"), False
    except Exception:
        return SAMPLE_EVIDENCE, True


@st.cache_data(ttl=30, show_spinner=False)
def _modules(dataset_id: str) -> Tuple[List[Dict[str, Any]], bool]:
    try:
        return _api_get(f"/api/modules/{dataset_id}"), False
    except Exception:
        return [], True


@st.cache_data(ttl=30, show_spinner=False)
def _triage_target(dataset_id: str, target: str) -> Tuple[Optional[Dict[str, Any]], bool]:
    """Per-target composite descriptive axes (concept / switch / robustness /
    double-support / safety) from GET /api/triage/{dataset_id}/{target}."""
    try:
        return _api_get(f"/api/triage/{dataset_id}/{target}"), False
    except Exception:
        return None, True


@st.cache_data(ttl=300, show_spinner=False)
def _coverage(dataset_id: str) -> Tuple[Optional[Dict[str, Any]], bool]:
    """Real, computed coverage counts for the sparse safety/genetics overlays
    (Wave 1c, docs/ux_trust_fix_plan.md) from GET /api/meta/coverage/{dataset_id}.
    Never a hardcoded number -- the badge below reflects this dataset's actual
    overlap, not a value copied from a doc that could drift."""
    try:
        return _api_get(f"/api/meta/coverage/{dataset_id}"), False
    except Exception:
        return None, True


def _first(*values: Any) -> Any:
    """First non-unknown value — lets a field be pulled from card OR readiness row."""
    for v in values:
        if not _is_unknown(v):
            return v
    return values[0] if values else None


def _readiness_row(readiness: Optional[Dict[str, Any]], target: str) -> Optional[Dict[str, Any]]:
    if not readiness:
        return None
    rows = readiness.get("readiness", []) or []
    matches = [r for r in rows if str(r.get("target", "")).upper() == target.upper()]
    return matches[0] if matches else None


# =========================================================================== #
# PAGE BODY
# =========================================================================== #
st.set_page_config(page_title="標的檔案 · Target Dossier", layout="wide")
inject_chip_css()
# FE-1 deep-link: preselect the target/dataset a list view passed via query params.
seed_dossier_session(st.query_params, st.session_state)

st.title("標的檔案 · Target Dossier")
st.warning(
    "🔬 **研究用途(research use only)** — 本頁為 CD4 T-cell Perturb-seq 標的發現的"
    "探索性研究工具,**非臨床軟體**、非診斷、非治療或用藥建議。"
)
st.caption(
    "一個標的一頁(Open Targets / Pharos / cBioPortal 式的實體中心檔案)。"
    "每個區塊由上到下獨立呈現,並標註**來源 + 版本/擷取時間**。"
    "灰色虛線「未檢查 (unknown)」徽章代表**未測得,不是 0**。"
)

# ----- (①) Search / select affordance -------------------------------------- #
st.subheader("① 搜尋 / 選擇標的")
datasets, ds_sample = _datasets()
dataset_ids = [d.get("dataset_id") for d in datasets if d.get("dataset_id")]

sel_cols = st.columns([2, 2, 1.4])
with sel_cols[0]:
    query = st.text_input(
        "基因搜尋(symbol / alias / Ensembl ID;可容錯)",
        value=st.session_state.get("dossier_query", ""),
        placeholder="例如 IL2RA、CD25(alias)、ENSG00000134460",
        key="dossier_query",
    )
with sel_cols[1]:
    if dataset_ids:
        default_ds = st.session_state.get("dossier_dataset", dataset_ids[0])
        if default_ds not in dataset_ids:
            default_ds = dataset_ids[0]
        dataset_id = st.selectbox("資料集 dataset_id", dataset_ids, index=dataset_ids.index(default_ds))
    else:
        dataset_id = st.text_input("資料集 dataset_id", value=_SAMPLE_DATASET_ID)
    st.session_state["dossier_dataset"] = dataset_id
with sel_cols[2]:
    st.text_input("API base", value=API_BASE, disabled=True)

if ds_sample:
    st.warning(SAMPLE_BANNER)

# Typeahead: search + let user pick a resolved hit.
selected_symbol: Optional[str] = None
selected_ensembl: Optional[str] = None
if query.strip():
    search_payload, s_sample = _search(query.strip(), limit=10)
    hits = search_payload.get("results", []) or []
    if hits:
        labels = [
            f"{h.get('canonical_symbol')}  ·  {h.get('ensembl_gene_id')}  "
            f"({h.get('match_type')}, {h.get('score')})"
            for h in hits
        ]
        pick = st.selectbox("符合的基因(typeahead)", list(range(len(hits))), format_func=lambda i: labels[i])
        selected_symbol = hits[pick].get("canonical_symbol")
        selected_ensembl = hits[pick].get("ensembl_gene_id")
    else:
        st.info(f"找不到符合「{query}」的基因。")
else:
    st.info("在上面輸入一個基因以開啟它的標的檔案(例如 IL2RA)。")

if not selected_symbol:
    st.stop()

# Resolve (confirm canonical identity for the header + downstream gene endpoints).
resolve_payload, r_sample = _resolve(selected_symbol)
canonical = resolve_payload.get("canonical_symbol") or selected_symbol
ensembl = resolve_payload.get("ensembl_gene_id") or selected_ensembl

# Fetch the target's dataset-scoped card + readiness once.
detail, d_sample = _target_detail(dataset_id, canonical)
readiness_payload, rd_sample = _readiness(dataset_id)
summary: Dict[str, Any] = (detail or {}).get("summary", {}) or {}
rrow = _readiness_row(readiness_payload, canonical)

any_sample = any([ds_sample, r_sample, d_sample, rd_sample])
if any_sample:
    st.warning(SAMPLE_BANNER)

st.divider()

# ----- (Header) ------------------------------------------------------------ #
grade = summary.get("statistical_evidence_grade")
call = (rrow or {}).get("readiness_call")
condition = _first(summary.get("condition"), (rrow or {}).get("condition"))
origin = next((d.get("origin") for d in datasets if d.get("dataset_id") == dataset_id), None)

st.markdown(f"## 🎯 {canonical}")
header_bits = [
    _labeled("Ensembl ID", _val_chip(ensembl)),
    _labeled("Condition 條件", _val_chip(condition)),
    _labeled(
        "統計證據分級 grade",
        (f'<span class="gwt-chip gwt-chip--grade">Grade {grade}</span>' if not _is_unknown(grade) else _val_chip(grade)),
        hint="1–4",
    ),
    _labeled(
        "Readiness call",
        (f'<span class="gwt-chip gwt-chip--call">{call}</span>' if not _is_unknown(call) else _val_chip(call)),
    ),
    _labeled("資料集 origin", _val_chip(origin if origin else dataset_id)),
]
_fields_row(header_bits)
if not _is_unknown(resolve_payload.get("resolution_path")):
    st.caption(f"identity 解析路徑:`{resolve_payload.get('resolution_path')}`(query = `{selected_symbol}`)")
_provenance("GET /api/targets/{dataset_id}/{target} + /api/genes/resolve", extra={"dataset_id": dataset_id})
render_glossary_expander()
st.caption(
    "🧪 整個工具的證據基礎:**單一 CRISPRi screen**‧CD4⁺ T 細胞‧Rest/Stim8hr/Stim48hr 三種條件‧"
    "N≈3 位捐贈者。所有以下判定都建立在這一次篩選之上,屬於**假設生成 (hypothesis-generating)** "
    "用途,非臨床或個人醫療決策依據。詳見 REPRODUCIBILITY.md。"
)
# Wave 1d (docs/ux_trust_fix_plan.md): the underlying screen is a bioRxiv
# preprint pin, not yet peer-reviewed -- that fact is easy to lose track of
# once a user is looking at confident-looking chips. Shown from the real
# per-dataset version string when available, never a hardcoded guess.
_ds_meta_for_version = next((d for d in datasets if d.get("dataset_id") == dataset_id), {})
_data_version = _ds_meta_for_version.get("data_version") or _ds_meta_for_version.get("dataset_version")
if not _is_unknown(_data_version) and "biorxiv" in str(_data_version).lower():
    st.caption(f"📄 資料版本 `{_data_version}` 為 **preprint,尚未經同行評審(not peer-reviewed)**。")

# ----- (Quick-answer headline, persona fast-path) --------------------------- #
# UX-flow fix: the readiness call + next validation step were originally only
# shown at the very BOTTOM of the page, after every detail section. A clinician
# had to scroll past all of that to find the one-line "so what"; a researcher
# had to scroll the same distance to find the recommended next experiment even
# though it is derived entirely from evidence shown further down. This card
# promotes that same headline (computed once, in section ⑨ below -- no new
# computation, no new decision path) to right after the header, and points
# each persona at the section number they'll want to read next using the
# page's own existing ①–⑨ numbering as an informal table of contents. Step 4
# of docs/ux_flow_stepwise_plan.md additionally re-ordered ②–⑨ into a
# persona-oriented sequence (descriptive summary + clinically-relevant sections
# first, statistics/mechanism audit detail after) -- see that section's own
# comments below for the per-block rationale.
st.markdown("### 🧭 快速結論(quick answer)")
if not rrow:
    st.info("此標的尚無 readiness 記錄——請見下方 ⑥ 是否有統計證據。")
else:
    _qa_call = rrow.get("readiness_call")
    _qa_next = rrow.get("next_validation_step")
    _qa_flags = str(rrow.get("red_flag_override", "") or "")
    qa_cols = st.columns([1, 2])
    with qa_cols[0]:
        st.markdown(
            _labeled(
                "Readiness call",
                (f'<span class="gwt-chip gwt-chip--call">{_qa_call}</span>' if not _is_unknown(_qa_call) else _val_chip(_qa_call)),
            ),
            unsafe_allow_html=True,
        )
        if _qa_flags and _qa_flags.strip().lower() != "none":
            st.caption(f"⚑ 被紅旗下修:{_qa_flags}")
    with qa_cols[1]:
        if not _is_unknown(_qa_next):
            st.success(f"下一步驗證:{_qa_next}")
        else:
            st.caption("下一步驗證尚未定義(見下方 ⑨)。")
st.caption(
    "🩺 **臨床醫師快速路徑**:外部證據 trials/literature/genetics(見下方 ③)、"
    "安全性與遺傳學(見下方 ④)、完整判定理由(見下方 ⑨)。  \n"
    "🔬 **研究者快速路徑**:GWT 統計證據(見下方 ⑥)、多軸描述性摘要(見下方 ②)、"
    "CD4 概念剖面 + 機制圖(見下方 ⑦⑧)。"
)

# ----- (②) Descriptive multi-axis summary (triage) ------------------------- #
st.subheader("② 多軸描述性摘要(descriptive axes at a glance)")
_descriptive_note()
_triage_payload, _triage_sample = _triage_target(dataset_id, canonical)
if _triage_sample or not _triage_payload:
    _not_available("多軸摘要", "API 未連線或此標的無資料")
elif not _triage_payload.get("available", False):
    _not_available("多軸摘要", _triage_payload.get("reason", ""))
else:
    _axes = _triage_payload.get("axes", {})
    _concept_ids = format_concept_chips(_axes.get("concept_modules"))
    axis_row = [
        _labeled("免疫概念模組 concept modules", _val_chip(_concept_ids or None, unknown_label="無(none)")),
        _labeled("刺激門控 stimulation-gated", _flag_chip(_axes.get("stimulation_gated"))),
        _labeled("刺激開關 switch", _val_chip(_axes.get("switch_type"), unknown_label="無翻轉(none)")),
        _labeled("穩健度 tier", _flag_chip(_axes.get("robustness_tier"))),
    ]
    _fields_row(axis_row)
    axis_row2 = [
        _labeled("遺傳雙證據 double-support", _flag_chip(_axes.get("double_support"))),
        _labeled("疾病關聯數 n_diseases", _val_chip(_axes.get("n_diseases"))),
        _labeled("安全窗 composite liability", _flag_chip(_axes.get("composite_safety_liability")), hint="gnomAD+GTEx · 稀疏~15基因"),
        _labeled("成藥類別 druggable_class", _val_chip(_axes.get("druggable_class"))),
    ]
    _fields_row(axis_row2)
    prov = _triage_payload.get("provenance", {})
    _provenance(
        "GET /api/triage/{dataset_id}/{target}",
        version=prov.get("concept_set_version"),
        extra={"dataset_id": dataset_id, "descriptive_only": True},
    )

# ----- (③) External evidence ------------------------------------------------ #
st.subheader("③ 外部證據(trials / literature / genetics)")
_descriptive_note()
evidence, ev_sample = _evidence(canonical)
if evidence is None:
    _not_available(
        f"{canonical} 的外部證據快照",
        f"尚未建置;可用 API 建立:POST /api/evidence/build {{\"genes\": [\"{canonical}\"]}}",
    )
else:
    sources = evidence.get("sources", {}) or {}
    ecols = st.columns(3)
    with ecols[0]:
        st.markdown("**臨床試驗 clinical trials**")
        tr = sources.get("clinical_trials", {})
        if tr.get("source_status") == "ok":
            items = tr.get("items", []) or []
            for t in items[:5]:
                st.write(f"- [{t.get('nct_id', '')}]({t.get('url', '')}) {t.get('title', '')} "
                         f"({t.get('phase') or 'NA'}, {t.get('status', 'NA')})")
            if not items:
                st.caption("查無試驗(measured empty)。")
        else:
            st.markdown(_val_chip("unknown", unknown_label=f"未取得:{tr.get('reason', 'not fetched')}"), unsafe_allow_html=True)
    with ecols[1]:
        st.markdown("**文獻 literature**")
        lit = sources.get("literature", {})
        if lit.get("source_status") == "ok":
            items = lit.get("items", []) or []
            for it in items[:5]:
                st.write(f"- [{it.get('pmid', '')}]({it.get('url', '')}) {it.get('title', '')} ({it.get('year', 'NA')})")
            if not items:
                st.caption("查無文獻(measured empty)。")
        else:
            st.markdown(_val_chip("unknown", unknown_label=f"未取得:{lit.get('reason', 'not fetched')}"), unsafe_allow_html=True)
    with ecols[2]:
        st.markdown("**Open Targets(genetics/tractability)**")
        ot = sources.get("open_targets", {})
        if ot.get("source_status") == "ok":
            for d in (ot.get("associated_diseases", []) or [])[:5]:
                st.write(f"- {d.get('disease')} — genetic_association_score {d.get('genetic_association_score')}")
            if not ot.get("associated_diseases"):
                st.write(ot.get("items", []))
        else:
            st.markdown(_val_chip("unknown", unknown_label=f"未取得:{ot.get('reason', 'not fetched')}"), unsafe_allow_html=True)
_provenance(
    "GET /api/evidence/{gene}",
    version=(evidence or {}).get("source_version"),
    fetched_at=(evidence or {}).get("fetched_at"),
)

# ----- (④) Safety & genetics (descriptive liability framing) --------------- #
st.subheader("④ 安全性與遺傳學(liability / flag — 描述性)")
_descriptive_note()
st.caption(
    "⚠️ **框架很重要**:人類遺傳限制 + 廣泛表現 = **安全性負擔(liability)訊號**,"
    "**不是**「此標的安全」的背書。任一元件 unknown 時,合成負擔即 unknown(不當作無風險)。"
)
# Wave 1c (docs/ux_trust_fix_plan.md): the chips below can look equally
# confident regardless of how sparse their underlying overlay is (gnomAD
# constraint covers ~0.1% of targets, GTEx ~46%). This badge shows the REAL,
# computed-at-request-time coverage for this dataset, not a static hint.
_cov_payload, _cov_sample = _coverage(dataset_id)
if _cov_payload and not _cov_sample:
    _gnomad_cov = _cov_payload.get("domains", {}).get("gnomad_constraint", {})
    _gtex_cov = _cov_payload.get("domains", {}).get("gtex_tissue_breadth", {})
    if _gnomad_cov.get("available") and _gtex_cov.get("available"):
        st.caption(
            f"📊 此資料集的真實覆蓋率:gnomAD constraint {_gnomad_cov.get('covered')}/{_gnomad_cov.get('total')} "
            f"({_gnomad_cov.get('pct')}%) · GTEx tissue breadth {_gtex_cov.get('covered')}/{_gtex_cov.get('total')} "
            f"({_gtex_cov.get('pct')}%) —— 大多數標的落在**未覆蓋**的那一側,"
            f"下面的 chip 顯示 unknown 是正常情況,不是資料缺失。"
        )
sg = [
    _labeled(
        "composite_safety_liability",
        _flag_chip(_first(summary.get("composite_safety_liability"), (rrow or {}).get("composite_safety_liability"))),
        hint="high/moderate/low",
    ),
    _labeled(
        "safety_window_score",
        _val_chip(_first(summary.get("safety_window_score"), (rrow or {}).get("safety_window_score"))),
        hint="off-context GTEx 組織數",
    ),
    _labeled(
        "gnomad_constraint_flag",
        _flag_chip(_first(summary.get("gnomad_constraint_flag"), (rrow or {}).get("gnomad_constraint_flag"))),
        hint="LoF 限制",
    ),
    _labeled(
        "genetic_support_confidence",
        _flag_chip(_first(summary.get("genetic_support_confidence"), (rrow or {}).get("genetic_support_confidence"))),
        hint="Open Targets 遺傳關聯分級",
    ),
]
_fields_row(sg)
gmax = _first(summary.get("genetic_support_max_genetic_score"), (rrow or {}).get("genetic_support_max_genetic_score"))
if not _is_unknown(gmax):
    st.caption(f"最強 Open Targets genetic_association_score:{_fmt(gmax)}(passthrough,可稽核)")
safety_note = summary.get("safety_note")
if not _is_unknown(safety_note) and str(safety_note).strip():
    st.markdown("**安全性註記 safety_note:** " + str(safety_note).replace(";", "; "))

# Population LoF-burden hypothesis
st.markdown("**群體 LoF-burden 假設(UK Biobank)**")
pop, pop_sample = _population(canonical)
if not pop.get("available"):
    _not_available("群體遺傳假設", pop.get("reason") or "本地 burden 表無此資料")
elif pop.get("matched") is False or pop.get("found_in_burden_table") is False:
    _not_available("此基因的群體 LoF-burden 估計", pop.get("reason", ""))
else:
    pcols = [
        _labeled("trait", _val_chip(pop.get("trait"))),
        _labeled("disease_area", _val_chip(pop.get("disease_area"))),
        _labeled("方向 direction", _val_chip(pop.get("direction"))),
        _labeled("post_mean", _val_chip(pop.get("post_mean"))),
        _labeled("CI 排除 0", _val_chip(pop.get("ci_excludes_zero"))),
    ]
    _fields_row(pcols)
    if pop.get("population_hypothesis"):
        st.info("假設 hypothesis(非個人預測):" + str(pop.get("population_hypothesis")))
if pop.get("caveat"):
    st.caption("caveat:" + str(pop.get("caveat")))
_provenance(
    "GET /api/targets(safety cols) + GET /api/population-hypothesis/{gene}",
    extra={"trait": pop.get("trait")},
)

# ----- (⑤) Tractability ------------------------------------------------------ #
st.subheader("⑤ 成藥性(tractability)")
tcols = [
    _labeled("tractability_modality", _val_chip(summary.get("tractability_modality")), hint="推測 modality"),
    _labeled("druggable_class", _val_chip(summary.get("druggable_class"))),
]
_fields_row(tcols)
_provenance("GET /api/targets/{dataset_id}/{target}", extra={"dataset_id": dataset_id})

# ----- (⑥) GWT evidence -------------------------------------------------------#
st.subheader("⑥ GWT 篩選證據(statistical / robustness)")
_cell_state_cols = ["responder_fraction", "n_cells_classified", "n_donors_classified"]
_cell_state_values = {col: summary.get(col) for col in _cell_state_cols if col in summary}
if _cell_state_values:
    st.caption("Exploratory integrated-state evidence; not primary DE evidence.")
    st.caption(
        "Integrated cell-state summaries are descriptive aids for visualization, "
        "state matching, and hypothesis generation; they should not supersede "
        "pseudobulk/raw-count DE evidence."
    )
    _fields_row([
        _labeled(col, _val_chip(value), hint="exploratory/descriptive")
        for col, value in _cell_state_values.items()
    ])
if not summary:
    _not_available("此標的的 target card", "target 不在此資料集,或資料集未建置")
else:
    ev1 = [
        _labeled("DE 廣度 n_total_de_genes", _val_chip(summary.get("n_total_de_genes")), hint="上調/下調"),
        _labeled("上調 n_up", _val_chip(summary.get("n_up_genes"))),
        _labeled("下調 n_down", _val_chip(summary.get("n_down_genes"))),
        _labeled("On-target 效應量", _val_chip(summary.get("ontarget_effect_size")), hint="log2FC"),
        _labeled("On-target 顯著", _val_chip(summary.get("ontarget_significant"))),
    ]
    _fields_row(ev1)
    ev2 = [
        _labeled("KD 狀態 kd_status", _flag_chip(summary.get("kd_status"))),
        _labeled("KD 效率 kd_efficiency", _val_chip(summary.get("kd_efficiency"))),
        _labeled("Cross-guide 穩健度", _val_chip(summary.get("crossguide_correlation")), hint="gate 0.2/0.3"),
        _labeled("Cross-donor 穩健度(mean)", _val_chip(summary.get("crossdonor_correlation_mean"))),
        _labeled("Cross-donor(min)", _val_chip(summary.get("crossdonor_correlation_min"))),
    ]
    _fields_row(ev2)
    ev3 = [
        _labeled("Cells n_cells_target", _val_chip(summary.get("n_cells_target"))),
        _labeled("Guides n_guides", _val_chip(summary.get("n_guides"))),
        _labeled("Donors n_donors", _val_chip(summary.get("n_donors"))),
        _labeled("Replicate pass", _val_chip(summary.get("replicate_pass_flag"))),
        _labeled("條件特異性", _val_chip(summary.get("condition_specificity_score"))),
    ]
    _fields_row(ev3)

    # Red-flag chips: each explains why the statistical grade is capped.
    st.markdown("**紅旗 / 分數上限原因(red flags — 為何分級被 cap)**")
    flags_html: List[str] = []
    cap_reason = summary.get("score_cap_reason")
    if not _is_unknown(cap_reason) and str(cap_reason).strip().lower() != "none":
        for token in str(cap_reason).split(";"):
            token = token.strip()
            if token and token.lower() != "none":
                flags_html.append(f'<span class="gwt-red-flag">⚑ {token}</span>')
    flag_explanations = {
        "offtarget_flag": "偵測到潛在脫靶效應 → 下游 DE 可能非專一,分級受限",
        "effect_direction_flip_flag": "跨 guide/donor 效應方向翻轉 → 因果解讀不穩,分級受限",
        "batch_sensitivity_flag": "對批次敏感 → 效應可能被技術變異驅動,分級受限",
    }
    for col, why in flag_explanations.items():
        val = summary.get(col)
        if val is True:
            flags_html.append(f'<span class="gwt-red-flag" title="{why}">⚑ {col}:{why}</span>')
        elif _is_unknown(val):
            flags_html.append(_val_chip(val, unknown_label=f"{col}:未檢查"))
    if flags_html:
        st.markdown("<div>" + "".join(flags_html) + "</div>", unsafe_allow_html=True)
    else:
        st.markdown('<span class="gwt-chip gwt-chip--flag-low">無紅旗(no cap)· score_cap_reason = none</span>', unsafe_allow_html=True)

    with st.expander("完整 target card 欄位(可稽核)", expanded=False):
        audit_df = pd.DataFrame(
            [{"field": k, "value": "未檢查 (unknown)" if _is_unknown(v) else _fmt(v)} for k, v in summary.items()]
        )
        st.dataframe(audit_df, use_container_width=True, hide_index=True)
_provenance("GET /api/targets/{dataset_id}/{target}", extra={"dataset_id": dataset_id})

# ----- (⑦) CD4 concept profile (dataset-scoped module hits) ---------------- #
st.subheader("⑦ CD4 概念剖面(concept profile)")
_descriptive_note()
modules_payload, m_sample = _modules(dataset_id)
# NOTE: there is no live endpoint that returns a per-target SIGNED activation
# waterfall (the concept_waterfall component + its SAMPLE_REPORT fixture is
# the individual/COMPASS-layer demo on page 1, "探索demo" — driven by a
# pasted expression table, not by dataset/target). This page previously
# rendered that IL2RA fixture here UNCONDITIONALLY, so every target's dossier
# showed the identical waterfall regardless of which gene was queried — an
# honesty-invariant violation (a fixture presented as this target's data).
# Fixed: this section now shows ONLY the real per-target module hits from
# GET /api/modules/{dataset_id}, with an honest "not available" state when
# there is no signed per-gene waterfall to show.
st.caption(
    "此區塊顯示此資料集中,此標的命中的概念模組(descriptive,非活化強度波形)。"
    "目前的篩選 pipeline 未提供逐標的、有方向性的活化分數,因此不顯示瀑布圖——"
    "顯示假資料樣板會誤導使用者以為是這個基因的結果。"
)
target_modules = [r for r in (modules_payload or []) if str(r.get("target", "")).upper() == canonical.upper()]
if target_modules:
    st.markdown(f"**{canonical} 在此資料集命中的概念模組(live)**")
    st.dataframe(pd.DataFrame(target_modules), use_container_width=True, hide_index=True)
elif not m_sample:
    _not_available(f"{canonical} 的概念模組命中", "此標的無模組對應")
else:
    _not_available(f"{canonical} 的概念模組命中", "API 無法連線,無法取得 live 模組命中資料")
_provenance(
    "GET /api/modules/{dataset_id}",
    extra={"dataset_id": dataset_id, "descriptive_only": True},
)

# ----- (⑧) Mechanism graph ------------------------------------------------- #
st.subheader("⑧ 機制圖(Reactome pathways + STRING partners)")
_descriptive_note()
mech, mech_sample = _mechanism(canonical)
if not mech.get("available"):
    _not_available("機制圖", mech.get("reason") or "尚無快取的 pathway/network 快照")
else:
    nodes = mech.get("nodes", []) or []
    edges = mech.get("edges", []) or []
    pathways = [n for n in nodes if n.get("type") == "pathway"]
    partners = [n for n in nodes if n.get("type") == "gene" and n.get("role") == "string_partner"]
    mcols = st.columns(2)
    with mcols[0]:
        st.markdown(f"**Reactome pathways** ({len(pathways)})")
        if pathways:
            for p in pathways:
                disease = " · ⚠ disease pathway" if p.get("is_in_disease") else ""
                st.write(f"- {p.get('pathway_name')} (`{p.get('pathway_id')}`){disease}")
        else:
            st.caption(f"未取得 Reactome pathways(reactome_status = {mech.get('reactome_status')})")
    with mcols[1]:
        st.markdown(f"**STRING interaction partners** ({len(partners)})")
        if partners:
            edge_score = {e.get("target"): e.get("score") for e in edges if e.get("relationship") == "string_interaction"}
            for pn in sorted(partners, key=lambda n: -(edge_score.get(n.get("id")) or 0)):
                sc = edge_score.get(pn.get("id"))
                st.write(f"- {pn.get('id')} (score {sc if sc is not None else 'NA'})")
        else:
            st.caption(f"未取得 STRING partners(string_status = {mech.get('string_status')})")
    if mech.get("reason"):
        st.caption(f"部分未取得:{mech.get('reason')}")
_provenance(
    "GET /api/mechanism-graph/{gene}",
    version=mech.get("source_version"),
    fetched_at=mech.get("fetched_at"),
)

# ----- (⑨) Readiness call + next validation step ---------------------------- #
st.subheader("⑨ Readiness 判定 + 下一步驗證")
st.caption(
    "這是本工具的**決定性**輸出(decision);上面的描述性區塊不改變它。"
    "「advance / validate / watchlist / deprioritize」代表什麼、不代表什麼 → 見頁首「ℹ️ 名詞解釋」。"
)
if not rrow:
    _not_available("此標的的 readiness 記錄", "target 不在 readiness 表")
else:
    rcols = [
        _labeled("readiness_call", (f'<span class="gwt-chip gwt-chip--call">{rrow.get("readiness_call")}</span>'
                                    if not _is_unknown(rrow.get("readiness_call")) else _val_chip(rrow.get("readiness_call")))),
        _labeled("R-stage", _val_chip(rrow.get("overall_readiness_stage")), hint="R0→R3"),
        _labeled("red_flag_override", _flag_chip(rrow.get("red_flag_override"))),
        _labeled("biology_causality", _val_chip(rrow.get("biology_causality_score"))),
        _labeled("translation", _val_chip(rrow.get("translation_score"))),
        _labeled("tractability", _val_chip(rrow.get("tractability_score"))),
    ]
    _fields_row(rcols)
    # Wave 1b (docs/ux_trust_fix_plan.md): translation_score alone can't tell a
    # reader "we couldn't measure cross-donor robustness" from "we measured it
    # and it was weak" -- both cap the score identically. translation_capped_by
    # disambiguates the two without changing the score or the call.
    capped_by = rrow.get("translation_capped_by")
    if capped_by == "missing_crossdonor_data":
        st.caption("⚠️ translation 未達 5:**因缺少測量而下修**(cross-donor 未檢查,非測得偏低)。")
    elif capped_by == "measured_low_crossdonor":
        st.caption("translation 未達 5:cross-donor 穩健度**已測得**,但低於 0.3 門檻(測得偏低)。")
    elif capped_by == "replicate_not_passed":
        st.caption("translation 未達 5:replicate 未通過。")
    reasons = str(rrow.get("readiness_reasons", "") or "")
    if reasons.strip():
        st.markdown("**判定理由 readiness_reasons**")
        for part in reasons.split(";"):
            if part.strip():
                st.write(f"- {part.strip()}")
    nxt = rrow.get("next_validation_step")
    if not _is_unknown(nxt):
        st.success(f"下一步驗證 next_validation_step:{nxt}")
    missing = (readiness_payload or {}).get("overlays_missing", [])
    if missing:
        st.caption(f"尚未接線的外部 overlay(相關 domain 維持 unknown,非 0):{', '.join(missing)}")
_provenance("GET /api/readiness/{dataset_id}", extra={"dataset_id": dataset_id})

# ----- (Provenance footer) --------------------------------------------------#
st.divider()
st.markdown("### 🔖 Provenance(資料溯源)")
ds_meta = next((d for d in datasets if d.get("dataset_id") == dataset_id), {})
footer = {
    "dataset_id": dataset_id,
    "origin": ds_meta.get("origin"),
    "data_version": ds_meta.get("data_version") or ds_meta.get("dataset_version"),
    "engine_version": ds_meta.get("engine_version"),
    "schema_version": ds_meta.get("schema_version"),
    "built_at / fetched_at": ds_meta.get("built_at"),
    "resolved_ensembl": ensembl,
    "resolution_path": resolve_payload.get("resolution_path"),
    "api_base": API_BASE,
}
foot_items = [_labeled(k, _val_chip(v)) for k, v in footer.items()]
_fields_row(foot_items)
if any_sample:
    st.warning(SAMPLE_BANNER + " Provenance 欄位顯示為 SAMPLE 佔位,非真實版本號。")
st.caption(
    "資料明確 (支柱二):每個數字都能一鍵溯源到其**來源端點 + 版本/擷取時間**;"
    "「未檢查 (unknown)」徽章與測得 0 視覺上刻意區隔;描述性區塊(概念/機制/安全遺傳/外部)"
    "不改變 readiness 決定。"
)
