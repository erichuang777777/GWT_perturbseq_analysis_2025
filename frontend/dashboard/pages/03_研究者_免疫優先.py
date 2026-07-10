"""Streamlit page — 研究者 · 免疫優先排序 (Immune-concept priority).

Extracted verbatim (behavior-preserving) from target_card_dashboard.py's
former "免疫優先 Immune Priority" tab (concept-membership ranking + the
stimulation-dependent switches view).

Isolation (frontend/README.md): talks to the backend ONLY via api_client's
HTTP helpers. Never imports `src/3_DE_analysis`.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from api_client import _immune_ranked, _selectable_table_with_dossier_link, _switches
from dataset_context import configure_page, load_summary, render_sidebar, require_dataset_id
from ui_chips import format_concept_chips

configure_page("GWT Target Evidence Browser — 免疫優先")
render_sidebar()
dataset_id = require_dataset_id()
opts, summary_payload, summary = load_summary(dataset_id)

st.title("免疫優先排序 — Immune-concept priority")
st.caption(
    "Re-orders targets by CD4 immune-concept interest (membership in the 20 "
    "COMPASS-analog modules, then on-target effect) instead of raw DE breadth, "
    "so the immunologically meaningful hits (TCR signalosome, checkpoint / "
    "exhaustion, cytokine axes) surface first. **Descriptive only — this view "
    "never changes any readiness call.**"
)
ip_cols = st.columns([1, 1, 2])
with ip_cols[0]:
    ip_top_n = st.slider("Top N targets", min_value=10, max_value=500, value=100, step=10)
with ip_cols[1]:
    ip_gated = st.checkbox("Stimulation-gated only", value=False, help="Quiet at Rest, active on Stim (e.g. the TCR-proximal signalosome).")
try:
    ip_payload = _immune_ranked(dataset_id, top_n=ip_top_n, stimulation_gated_only=ip_gated)
    prov = ip_payload.get("provenance", {})
    st.caption(
        f"concept_set_version: `{prov.get('concept_set_version', 'unknown')}` · "
        f"{prov.get('n_modules', '?')} modules / {prov.get('n_seed_genes', '?')} seed genes · "
        f"join key: {prov.get('join_key', 'target (symbol)')} · "
        f"{ip_payload.get('returned', 0)} of {ip_payload.get('n_targets', 0)} targets shown"
    )
    rows = ip_payload.get("targets", [])
    if not rows:
        st.info("No targets matched (try turning off the stimulation-gated filter).")
    else:
        ip_df = pd.DataFrame(rows)
        if "concept_modules" in ip_df.columns:
            ip_df["concept_modules"] = ip_df["concept_modules"].map(format_concept_chips)
        display_cols = [
            c
            for c in [
                "target",
                "condition",
                "n_concept_modules",
                "concept_modules",
                "stimulation_gated",
                "ontarget_effect_size",
                "n_total_de_genes",
                "statistical_evidence_grade",
                "druggable_class",
            ]
            if c in ip_df.columns
        ]
        _selectable_table_with_dossier_link(ip_df[display_cols], "immune_table")
except Exception as e:
    st.info(f"Immune-priority view not available: {e}")

st.divider()
st.subheader("刺激依賴開關 — Stimulation-dependent switches")
st.caption(
    "Targets whose knockdown effect **changes direction with activation "
    "state** (true sign flips like IKZF1 / NFATC2 / RHOH / SMAD3) or switch "
    "on/off across Rest → Stim8hr → Stim48hr. Reads the existing "
    "`effect_direction_flip_flag`; descriptive only, never a readiness input."
)
try:
    sw_payload = _switches(dataset_id, top_n=ip_top_n)
    if not sw_payload.get("available", False):
        st.info(f"Switches not available: {sw_payload.get('reason', 'unknown')}")
    else:
        st.caption(
            f"true sign flips: {sw_payload.get('n_true_sign_flip', 0)} · "
            f"on/off switches: {sw_payload.get('n_on_off_switch', 0)} · "
            f"sign-flip |logFC| threshold: {sw_payload.get('sign_flip_threshold_abs_logfc', 1.0)} · "
            f"concept_set_version: `{sw_payload.get('concept_set_version', 'unknown')}`"
        )
        sw_rows = sw_payload.get("switches", [])
        if not sw_rows:
            st.info("No stimulation-dependent switches in this dataset.")
        else:
            sw_df = pd.DataFrame(sw_rows)
            if "concept_modules" in sw_df.columns:
                sw_df["concept_modules"] = sw_df["concept_modules"].map(format_concept_chips)
            st.dataframe(sw_df, use_container_width=True, hide_index=True)
except Exception as e:
    st.info(f"Switches view not available: {e}")
