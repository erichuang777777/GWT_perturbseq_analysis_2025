"""Shared clinical-evidence page guardrails (docs/frontend_design.md §6).

The forced-caveat banner was previously reimplemented per module with its own
``CAVEAT_TEXT`` constant (``concept_waterfall.py``, and
``pages/11_臨床證據_個體概念剖面.py``'s own ``_forced_caveat_header``/
``_render_report_caveat``/``_render_provenance``). Adding more clinical-
evidence pages is the trigger to extract one shared implementation so the
guarantee is enforced by one function instead of copy-pasted per page. Pure
refactor of existing duplicated logic -- rendered text and behavior are
unchanged from what ``pages/11_臨床證據_個體概念剖面.py`` already did.

Isolation (frontend/README.md): pure Python + Streamlit only. No backend
import, no HTTP.
"""

from __future__ import annotations

from typing import Any, Dict

import streamlit as st


def forced_caveat_header(text: str) -> None:
    """Un-hideable safety banner -- no toggle, no branch that can suppress it.
    Call this first, every run, on every clinical-evidence page."""
    st.error(f"⚠️ {text}")


def render_response_caveat(payload: Dict[str, Any]) -> None:
    """Surface a live API response's OWN `caveat` field. A response contract
    that requires a non-empty caveat and doesn't have one is a compliance bug
    in the backend, not something to silently paper over -- so a missing
    caveat is a loud error, not a quiet no-op."""
    caveat = str((payload or {}).get("caveat", "") or "").strip()
    if caveat:
        st.warning(f"報告內建 caveat: {caveat}")
    else:
        st.error("報告缺少 caveat 欄位 — 此輸出不合規,不得使用。")


def provenance_footer(payload: Dict[str, Any], api_base: str) -> None:
    """Standard provenance line: concept_set_version / screen_data_version /
    computed_at / api_base. Every clinical-evidence page ends with this."""
    prov: Dict[str, Any] = (payload or {}).get("provenance", {}) or {}
    bits = [
        f"concept_set_version = {prov.get('concept_set_version', 'NA')}",
        f"screen_data_version = {prov.get('screen_data_version', 'NA')}",
        f"computed_at = {prov.get('computed_at', 'NA')}",
        f"api_base = {api_base}",
    ]
    st.divider()
    st.caption("Provenance · " + " · ".join(bits))
