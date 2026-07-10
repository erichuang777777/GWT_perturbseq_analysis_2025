"""Shared evidence-type caveats for the isolated dashboard frontend.

Frontend pages cannot import backend report modules (see ``frontend/README.md``),
so this module keeps the UI copy in one local place instead of repeating long
captions across Overview, Target Explorer, and Target Dossier.
"""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

import streamlit as st


EVIDENCE_TYPES: Tuple[Dict[str, str], ...] = (
    {
        "key": "perturbseq",
        "label": "Perturb-seq screen evidence",
        "short": "CD4 CRISPRi 轉錄體假說;不是治療有效性證明。",
        "caveat": (
            "CD4 CRISPRi transcriptomic target-condition evidence. Use it for "
            "discovery hypotheses; reserve stronger biology claims for rows with "
            "replicate-pass and guide/donor/off-target robustness support."
        ),
    },
    {
        "key": "genetics",
        "label": "Human genetic association",
        "short": "疾病關聯支持;不是直接 perturbation 驗證。",
        "caveat": (
            "External disease-association support. It can increase biological "
            "plausibility, but it is not direct validation of the screen effect "
            "and not proof of causal drug response."
        ),
    },
    {
        "key": "lof",
        "label": "Population LoF evidence",
        "short": "群體層級 loss-of-function 訊號;不是個人預測。",
        "caveat": (
            "Population-level loss-of-function burden evidence. It is not "
            "patient-level prediction and cannot replace disease-context "
            "functional validation."
        ),
    },
    {
        "key": "tractability",
        "label": "Drug / tractability precedent",
        "short": "成藥或 target-class 先例;不是此情境安全/有效證明。",
        "caveat": (
            "A target class, modality, or nearby mechanism may be druggable. This "
            "does not mean modulating the target is safe or efficacious for this "
            "condition."
        ),
    },
    {
        "key": "readiness",
        "label": "Heuristic readiness triage",
        "short": "內部後續優先序 heuristic;不是臨床建議。",
        "caveat": (
            "Internal prioritization for follow-up planning. It is not clinical "
            "guidance and not a wet-lab validation endpoint."
        ),
    },
)

_BY_KEY = {item["key"]: item for item in EVIDENCE_TYPES}


def _format_items(items: Iterable[Dict[str, str]], field: str) -> str:
    return " · ".join(f"**{item['label']}** = {item[field]}" for item in items)


def render_evidence_type_guide(*, compact: bool = True) -> None:
    """Render the shared evidence-type guide as one compact UI element."""
    if compact:
        st.caption("證據類型分層: " + _format_items(EVIDENCE_TYPES, "short"))
        return

    with st.expander("證據類型分層 Evidence type guide", expanded=False):
        for item in EVIDENCE_TYPES:
            st.markdown(f"- **{item['label']}** — {item['caveat']}")


def evidence_type_caption(*keys: str) -> str:
    """Return a concise block-specific caveat for one or more evidence types."""
    items = [_BY_KEY[key] for key in keys if key in _BY_KEY]
    return _format_items(items, "caveat")
