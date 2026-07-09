"""Shared evidence-chip primitives for the frontend dashboard + dossier pages.

Extracted verbatim (behaviour-preserving) from
``pages/2_標的檔案_target_dossier.py`` so BOTH the main dashboard and the target
dossier render fields with the same honest visual grammar:

    * ``unknown != 0`` — an unmeasured / unchecked field renders as a distinct
      grey 虛線「未檢查 (unknown)」 chip, NEVER as a measured 0 (which is a real
      verdict and renders as a normal value chip). See ``is_unknown`` /
      ``val_chip`` / ``flag_chip``.
    * ``flag_chip`` colours a liability by severity, but an *unchecked* flag is
      grey unknown — never a green "low / safe".
    * ``provenance_line`` stamps a section's source + version/fetched_at.
    * ``descriptive_note`` marks a block as descriptive (does NOT move the
      readiness call).

Isolation (frontend/README.md): this module talks to nothing but Streamlit and
pure Python — no backend import, no HTTP. It is the frontend's own presentation
layer.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import streamlit as st

# --------------------------------------------------------------------------- #
# `unknown != 0` primitives. A field is UNKNOWN (unchecked / not in an overlay)
# when it is None/NaN or one of these honest-degradation tokens the backend
# emits. A real numeric 0 or the string "none"/"no_*" is a MEASURED verdict and
# must NOT be greyed out — that is the whole point of the invariant.
# --------------------------------------------------------------------------- #
_UNKNOWN_TOKENS = {"unknown", "nan", "na", "n/a", "", "not_assessed", "not_measurable", "not measurable"}


def is_unknown(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.strip().lower() in _UNKNOWN_TOKENS:
        return True
    return False


def fmt(value: Any) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.3g}"
    return str(value)


def val_chip(value: Any, *, unknown_label: str = "未檢查 (unknown)") -> str:
    """Render one field as an HTML chip. UNKNOWN → distinct grey chip that reads
    as 'not checked', explicitly NOT a measured 0. Measured value (incl. real 0)
    → neutral chip."""
    if is_unknown(value):
        return f'<span class="gwt-chip gwt-chip--unknown" title="unmeasured / not in overlay — 非測得 0">{unknown_label}</span>'
    return f'<span class="gwt-chip gwt-chip--value">{fmt(value)}</span>'


_LIABILITY_CLASS = {
    "high": "gwt-chip--flag-high",
    "moderate": "gwt-chip--flag-mod",
    "low": "gwt-chip--flag-low",
    "loss_intolerant": "gwt-chip--flag-high",
    "none": "gwt-chip--flag-low",
    "strong_genetic_association": "gwt-chip--flag-info",
    "moderate_genetic_association": "gwt-chip--flag-info",
    "no_genetic_association": "gwt-chip--flag-low",
}


def flag_chip(value: Any, *, unknown_label: str = "未檢查 (unknown)") -> str:
    """Liability / flag chip with severity colour. Same unknown≠0 rule — an
    unchecked flag is grey 'unknown', never a green 'low/safe'."""
    if is_unknown(value):
        return f'<span class="gwt-chip gwt-chip--unknown" title="unmeasured / not in overlay — 非測得 0">{unknown_label}</span>'
    cls = _LIABILITY_CLASS.get(str(value).strip().lower(), "gwt-chip--value")
    return f'<span class="gwt-chip {cls}">{fmt(value)}</span>'


def labeled(label: str, chip_html: str, hint: str = "") -> str:
    hint_html = f'<span class="gwt-field-hint">{hint}</span>' if hint else ""
    return (
        '<div class="gwt-field">'
        f'<div class="gwt-field-label">{label}{hint_html}</div>'
        f"<div>{chip_html}</div>"
        "</div>"
    )


def fields_row(items: List[str]) -> None:
    st.markdown('<div class="gwt-fields">' + "".join(items) + "</div>", unsafe_allow_html=True)


def provenance_line(source: str, *, version: Any = None, fetched_at: Any = None, extra: Optional[Dict[str, Any]] = None) -> None:
    bits = [f"來源 source: {source}"]
    if version is not None and not is_unknown(version):
        bits.append(f"version: {version}")
    if fetched_at is not None and not is_unknown(fetched_at):
        bits.append(f"fetched_at: {fetched_at}")
    for k, v in (extra or {}).items():
        if not is_unknown(v):
            bits.append(f"{k}: {v}")
    st.markdown(
        '<div class="gwt-prov">🔖 ' + "  ·  ".join(str(b) for b in bits) + "</div>",
        unsafe_allow_html=True,
    )


def descriptive_note() -> None:
    st.caption(
        "🧭 **描述性區塊(descriptive)** — 僅供解讀,**不改變** readiness 判定"
        "(readiness_call / overall_readiness_stage)。"
    )


def not_available(what: str, reason: str = "") -> None:
    tail = f" — {reason}" if reason else ""
    st.info(f"未取得 (not available):{what}{tail}")


def format_concept_chips(value: Any) -> str:
    """Flatten a ``concept_modules`` cell to a readable ``module_id`` string.

    Accepts list-of-dicts (each with a ``module_id``), list-of-str, ``None`` or
    any non-list scalar — and NEVER raises. Non-list / empty inputs collapse to
    an empty string so a missing / unshaped concept column degrades quietly
    instead of blowing up a table render.
    """
    if not isinstance(value, list):
        return ""
    parts: List[str] = []
    for item in value:
        if isinstance(item, dict):
            module_id = item.get("module_id")
            if module_id is not None and str(module_id).strip():
                parts.append(str(module_id))
        elif item is not None:
            text = str(item).strip()
            if text:
                parts.append(text)
    return ", ".join(parts)


# --------------------------------------------------------------------------- #
# CSS (theme-neutral chips). Injected once per page via ``inject_chip_css()``.
# --------------------------------------------------------------------------- #
CHIP_CSS = """
<style>
.gwt-chip { display:inline-block; padding:2px 9px; margin:2px 4px 2px 0; border-radius:11px;
  font-size:0.82rem; font-weight:600; border:1px solid transparent; line-height:1.5; }
.gwt-chip--value      { background:#eef1f5; color:#243b53; border-color:#cfd8e3; }
.gwt-chip--unknown    { background:#e7e7e4; color:#6b6b66; border-color:#cbcbc4;
  border-style:dashed; font-weight:500; }
.gwt-chip--flag-high  { background:#fbe6e6; color:#8a1f1f; border-color:#e5a3a3; }
.gwt-chip--flag-mod   { background:#fff2dd; color:#8a5a12; border-color:#e8c98a; }
.gwt-chip--flag-low   { background:#e6f4ea; color:#1f6b37; border-color:#a8d5b7; }
.gwt-chip--flag-info  { background:#e6eefb; color:#1f3f8a; border-color:#a8bde8; }
.gwt-chip--grade      { background:#243b53; color:#fff; font-size:0.95rem; padding:3px 12px; }
.gwt-chip--call       { background:#0b5; color:#fff; font-size:0.95rem; padding:3px 12px; }
.gwt-fields { display:flex; flex-wrap:wrap; gap:6px 22px; margin:2px 0 6px 0; }
.gwt-field  { min-width:150px; }
.gwt-field-label { font-size:0.72rem; color:#7b8794; text-transform:uppercase;
  letter-spacing:0.02em; margin-bottom:2px; }
.gwt-field-hint  { text-transform:none; letter-spacing:0; color:#9aa5b1; margin-left:5px;
  font-size:0.68rem; }
.gwt-prov { font-size:0.74rem; color:#7b8794; background:#f6f8fa; border:1px solid #e1e4e8;
  border-radius:6px; padding:4px 10px; margin:2px 0 4px 0; display:inline-block; }
.gwt-red-flag { display:inline-block; background:#fbe6e6; color:#8a1f1f; border:1px solid #e5a3a3;
  border-radius:6px; padding:3px 10px; margin:3px 6px 3px 0; font-size:0.82rem; }
@media (prefers-color-scheme: dark) {
  .gwt-chip--value   { background:#22303c; color:#c7d3de; border-color:#33424f; }
  .gwt-chip--unknown { background:#2a2a27; color:#9a9a92; border-color:#44443c; }
  .gwt-prov  { background:#1c2530; color:#9aa5b1; border-color:#2c3a47; }
}
</style>
"""


def inject_chip_css() -> None:
    st.markdown(CHIP_CSS, unsafe_allow_html=True)
