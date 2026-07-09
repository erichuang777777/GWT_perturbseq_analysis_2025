"""Shared glossary for the readiness-call vocabulary and the statistical grade.

Blind-spot fix (Wave 1a, docs/ux_trust_fix_plan.md): ``advance / validate /
watchlist / deprioritize`` and ``grade`` are rendered throughout the dashboard
and dossier as confident, decision-shaped chips, but the product ships with
**no in-product definition** of what any of them mean -- or, just as
important, what they do NOT mean. "advance" reads to a domain expert as "move
into a program"; it only means the target cleared the engine's R3 statistical
gate on a single CRISPRi screen. "grade" reads as "how good/important this
target is"; it is purely a measurement-quality score (cell count, DE breadth,
significance, cross-donor/cross-guide reproducibility) and carries no
information about biological importance.

The copy below is a plain restatement of the exact thresholds implemented in
``core/readiness.py`` (``_stage`` / ``_red_flags`` / ``STAGE_TO_CALL``) and
``core/scoring.py`` (``make_score``) -- verified against that source before
writing, per the "never fabricate" invariant. If those thresholds change, this
copy must be re-verified against the new source, not guessed.

Isolation (frontend/README.md): pure Python + Streamlit only. No backend
import, no HTTP -- this module explains behaviour, it never computes it.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import streamlit as st

# --------------------------------------------------------------------------- #
# Glossary content. Keys match the literal `readiness_call` values plus
# "grade". Each entry is intentionally short -- a definition and a single most
# important "does NOT mean" correction, not a re-derivation of the engine.
# --------------------------------------------------------------------------- #
GLOSSARY: Dict[str, Dict[str, str]] = {
    "advance": {
        "label": "advance",
        "means": (
            "此標的在單一 CRISPRi screen 上,清過本引擎最高的統計門檻(R3):"
            "biology_causality ≥3、translation_score = 5(replicate 通過且 "
            "cross-donor ≥0.3),且成藥性或人類遺傳學支持至少一項成立,"
            "並且沒有被任何紅旗封頂。"
        ),
        "not_mean": (
            "**不代表**已臨床驗證、已成藥、或已準備好進入藥物開發 program——"
            "全部證據來自同一個篩選實驗。"
        ),
    },
    "validate": {
        "label": "validate",
        "means": (
            "biology_causality ≥3 且 translation_score ≥3(replicate 通過,"
            "但未必達到 cross-donor ≥0.3 的門檻),**或**一個原本可達 advance 的"
            "標的因紅旗(方向不確定 / batch 干擾 / knockdown 偏弱)被封頂於此。"
        ),
        "not_mean": "**不代表**「中等有效」——也可能是「證據強但有待排除干擾」。",
    },
    "watchlist": {
        "label": "watchlist",
        "means": (
            "biology_causality ≥3 但 translation_score <3(通常代表 replicate "
            "未通過),**或**因必需基因 / 廣效性基因 / 高度 off-target / knockdown "
            "無法量測而被封頂於此。"
        ),
        "not_mean": "**不代表**「弱標的」——常常只是「還沒有足夠的穩健性資料」。",
    },
    "deprioritize": {
        "label": "deprioritize",
        "means": (
            "biology_causality = 0(統計分級低且不在已知路徑中),**或**是必需"
            "基因且統計分級 ≤1。"
        ),
        "not_mean": "**不代表**「證明無關」——多數情況是統計證據本身就薄弱,而非被積極排除。",
    },
    "grade": {
        "label": "統計證據分級 grade (1–4)",
        "means": (
            "純粹衡量**這次測量的統計檢定力與再現性**:細胞數、DE 基因數、"
            "on-target 顯著性、off-target 旗標、cross-donor / cross-guide "
            "相關性、guide FDR。"
        ),
        "not_mean": (
            "**不代表**生物重要性——一個高表現量、細胞數多的基因,即使生物意義"
            "普通,也能因為檢定力高而拿到 Grade 4;反之亦然。"
        ),
    },
}

GLOSSARY_ORDER: List[str] = ["advance", "validate", "watchlist", "deprioritize", "grade"]


def render_glossary_expander(*, keys: Optional[List[str]] = None, expanded: bool = False) -> None:
    """Render an always-available glossary expander.

    ``keys`` restricts which entries show (default: all, in ``GLOSSARY_ORDER``).
    Pure presentation -- reads no live data, feeds no decision.
    """
    show_keys = keys if keys is not None else GLOSSARY_ORDER
    with st.expander("ℹ️ 名詞解釋:這些字代表什麼、不代表什麼 (glossary)", expanded=expanded):
        for key in show_keys:
            entry = GLOSSARY.get(key)
            if not entry:
                continue
            st.markdown(f"**{entry['label']}**")
            st.markdown(f"= {entry['means']}")
            st.markdown(f"≠ {entry['not_mean']}")
            st.markdown("")
