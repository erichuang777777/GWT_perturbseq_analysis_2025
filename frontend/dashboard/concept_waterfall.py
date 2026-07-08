"""Shared, backend-free rendering helpers for the COMPASS-style concept waterfall.

This module is part of the ISOLATED `frontend/` package. It NEVER imports from
`src/3_DE_analysis/` — it only knows the documented HTTP/JSON report contract
(see `docs/compass_concept_integration_plan.md` §3.2). It deliberately does not
import `streamlit`, so the pure logic (payload parsing, figure construction) can
be compiled/tested without a Streamlit runtime; the Streamlit page imports it.

Both the target layer and the new individual layer are meant to share this one
waterfall component (plan §2B).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import plotly.graph_objects as go


# --------------------------------------------------------------------------- #
# Forced safety boundary (plan §0). Written into the code, not optional.
# The Streamlit page renders this at the top of the tab, un-hideable, with no
# toggle. Matches the repo's forced-caveat mechanism
# (population_hypothesis.py::CAVEAT_TEXT / signature_explorer.py::CAVEAT_TEXT).
# --------------------------------------------------------------------------- #
CAVEAT_TEXT = (
    "探索性研究 demo — 非診斷、非治療建議、非療效預測。"
    "輸出為「透明的概念投影 + 假設性標的線索」,不可用於任何臨床或個人醫療決策。"
)

# --------------------------------------------------------------------------- #
# Colors. Sourced from metadata/figure_palettes.yaml (DE_effects_regulator_class
# for signed direction; matched_targets:False for the "no data" gray). blue↔red
# is also the dataviz skill's diverging pair, so up/down read as opposite poles.
# --------------------------------------------------------------------------- #
COLOR_UP = "#2D6CBC"       # figure_palettes.yaml DE_effects_regulator_class.Positive
COLOR_DOWN = "#A8373A"     # figure_palettes.yaml DE_effects_regulator_class.Negative
COLOR_UNKNOWN = "#969696"  # figure_palettes.yaml matched_targets.False (no-data gray)

# text / chrome tokens (dataviz palette chrome)
_INK_PRIMARY = "#0b0b0b"
_INK_MUTED = "#898781"
_GRID = "#e1e0d9"
_BASELINE = "#c3c2b7"
_SURFACE = "#fcfcfb"

_UP_TOKENS = {"up", "positive", "high", "elevated", "+", "over", "overactive"}
_DOWN_TOKENS = {"down", "negative", "low", "reduced", "-", "under", "suppressed"}


def _hex_to_rgb(h: str) -> Tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgba(hex_color: str, alpha: float) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    return f"rgba({r},{g},{b},{alpha:.3f})"


def _coverage_alpha(coverage: Optional[float]) -> float:
    """Map coverage in [0,1] to fill opacity. Low coverage = low confidence =
    faint bar, but never fully invisible so a low-coverage result is still read."""
    try:
        cov = float(coverage)
    except (TypeError, ValueError):
        cov = 0.0
    cov = max(0.0, min(1.0, cov))
    return round(0.35 + 0.60 * cov, 3)


def _is_unknown(entry: Dict[str, Any]) -> bool:
    """A concept is 'unknown' when it has no measured activation (honest fallback,
    plan §3.1: no seed-gene overlap -> unknown, NEVER imputed to 0)."""
    act = entry.get("activation")
    if act is None:
        return True
    if isinstance(act, str) and act.strip().lower() in {"unknown", "nan", "na", ""}:
        return True
    direction = str(entry.get("direction", "")).strip().lower()
    if direction == "unknown":
        return True
    return False


def _activation_value(entry: Dict[str, Any]) -> Optional[float]:
    try:
        return float(entry.get("activation"))
    except (TypeError, ValueError):
        return None


def _direction_color(entry: Dict[str, Any], activation: Optional[float]) -> str:
    direction = str(entry.get("direction", "")).strip().lower()
    if direction in _UP_TOKENS:
        return COLOR_UP
    if direction in _DOWN_TOKENS:
        return COLOR_DOWN
    if activation is not None:
        return COLOR_UP if activation >= 0 else COLOR_DOWN
    return COLOR_UNKNOWN


def _label(entry: Dict[str, Any]) -> str:
    mid = str(entry.get("module_id", "")).strip()
    name = str(entry.get("module_name", "")).strip()
    if mid and name:
        return f"{mid} · {name}"
    return mid or name or "?"


def split_profile(
    concept_profile: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Return (known, unknown) partition. Known sorted by activation descending."""
    known: List[Dict[str, Any]] = []
    unknown: List[Dict[str, Any]] = []
    for entry in concept_profile or []:
        if _is_unknown(entry):
            unknown.append(entry)
        else:
            known.append(entry)
    known.sort(
        key=lambda e: (_activation_value(e) if _activation_value(e) is not None else 0.0),
        reverse=True,
    )
    unknown.sort(key=lambda e: _label(e))
    return known, unknown


def build_waterfall_figure(
    concept_profile: List[Dict[str, Any]],
    *,
    title: str = "個體概念活化剖面 · concept-activation waterfall",
    height: Optional[int] = None,
) -> go.Figure:
    """COMPASS-style ordered/waterfall bar chart of a concept-activation profile.

    Encodings:
      * ordering  -> concepts sorted by activation (waterfall), highest at top;
      * length    -> activation magnitude;
      * color     -> direction (blue = up/positive, red = down/negative);
      * opacity   -> coverage / confidence (faint = low seed-gene coverage);
      * hatched   -> 'unknown' concepts (no coverage), drawn as a distinct gray
        hatched placeholder band that is emphatically NOT a zero-height bar, so
        `unknown != 0` is honored visually (plan §7/§8).
    """
    known, unknown = split_profile(concept_profile)

    order_top_to_bottom = [_label(e) for e in known] + [_label(e) for e in unknown]

    fig = go.Figure()

    # --- known concepts: signed, coverage-weighted diverging bars ------------- #
    if known:
        k_labels = [_label(e) for e in known]
        k_vals = [_activation_value(e) for e in known]
        k_colors = [
            _rgba(_direction_color(e, v), _coverage_alpha(e.get("coverage")))
            for e, v in zip(known, k_vals)
        ]
        k_line = [_direction_color(e, v) for e, v in zip(known, k_vals)]
        k_text = [
            f"{v:+.2f} · 覆蓋 {float(e.get('coverage', 0)):.0%}"
            for e, v in zip(known, k_vals)
        ]
        k_hover = [
            (
                f"<b>{_label(e)}</b><br>"
                f"activation: {v:+.3f}<br>"
                f"direction: {e.get('direction', 'NA')}<br>"
                f"coverage: {float(e.get('coverage', 0)):.0%}"
                "<extra></extra>"
            )
            for e, v in zip(known, k_vals)
        ]
        fig.add_bar(
            x=k_vals,
            y=k_labels,
            orientation="h",
            marker=dict(color=k_colors, line=dict(color=k_line, width=1)),
            text=k_text,
            textposition="outside",
            textfont=dict(color=_INK_MUTED, size=11),
            cliponaxis=False,
            hovertemplate=k_hover,
            name="measured concept",
            showlegend=False,
        )

    # --- unknown concepts: hatched gray placeholder band (NOT zero) ----------- #
    if unknown:
        abs_max = max(
            (abs(v) for v in (_activation_value(e) for e in known) if v is not None),
            default=1.0,
        )
        span = abs_max if abs_max > 0 else 1.0
        u_labels = [_label(e) for e in unknown]
        # A full-width faint hatched track reads as a greyed-out empty slot,
        # never as a measured value of 0.
        fig.add_bar(
            x=[span] * len(unknown),
            y=u_labels,
            orientation="h",
            marker=dict(
                color=_rgba(COLOR_UNKNOWN, 0.18),
                line=dict(color=COLOR_UNKNOWN, width=1),
                pattern=dict(shape="x", fgcolor=COLOR_UNKNOWN, size=6, solidity=0.25),
            ),
            text=["unknown · 無 seed 覆蓋(非測得 0)"] * len(unknown),
            textposition="inside",
            insidetextanchor="start",
            textfont=dict(color=_INK_MUTED, size=11),
            cliponaxis=False,
            hovertemplate=[
                f"<b>{_label(e)}</b><br>activation: unknown（無 seed 基因覆蓋，非 0）"
                f"<br>coverage: {float(e.get('coverage', 0) or 0):.0%}<extra></extra>"
                for e in unknown
            ],
            name="unknown (no coverage ≠ 0)",
            showlegend=False,
        )

    n = max(len(order_top_to_bottom), 1)
    fig.update_layout(
        title=dict(text=title, font=dict(color=_INK_PRIMARY, size=16)),
        barmode="overlay",
        height=height or (140 + 26 * n),
        paper_bgcolor=_SURFACE,
        plot_bgcolor=_SURFACE,
        margin=dict(l=10, r=90, t=54, b=40),
        bargap=0.35,
    )
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=list(reversed(order_top_to_bottom)),  # first entry -> top
        tickfont=dict(color=_INK_PRIMARY, size=11),
        showgrid=False,
        zeroline=False,
    )
    fig.update_xaxes(
        title=dict(
            text="concept activation（標準化;藍=上調 紅=下調;越淡=覆蓋越低越不確定)",
            font=dict(color=_INK_MUTED, size=11),
        ),
        tickfont=dict(color=_INK_MUTED, size=11),
        gridcolor=_GRID,
        zeroline=True,
        zerolinecolor=_BASELINE,
        zerolinewidth=1,
    )
    return fig


# --------------------------------------------------------------------------- #
# Input parsing (frontend-side, request-only; the caller must NOT persist it).
# --------------------------------------------------------------------------- #
def parse_expression_table(text: str) -> Dict[str, float]:
    """Parse a pasted gene->value table into {gene_symbol: value}.

    Accepts comma / tab / whitespace separated 2-column rows. Ignores blank lines
    and an optional header row. Only a gene symbol and a numeric value are read —
    any extra columns are ignored, and NO identifier columns are wanted (plan
    §3.1: the interface eats an expression table, not an identity).
    """
    out: Dict[str, float] = {}
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "," in line:
            parts = [p.strip() for p in line.split(",")]
        elif "\t" in line:
            parts = [p.strip() for p in line.split("\t")]
        else:
            parts = line.split()
        if len(parts) < 2:
            continue
        gene = parts[0]
        try:
            value = float(parts[1])
        except ValueError:
            # header row or non-numeric -> skip silently
            continue
        if gene:
            out[gene] = value
    return out


# --------------------------------------------------------------------------- #
# Inline SAMPLE payload — matches the plan §3.2 report contract EXACTLY. Used
# only to make the tab demonstrable when the live endpoint is unreachable; real
# data must come from the live HTTP call. Clearly labeled as demo in the UI.
# --------------------------------------------------------------------------- #
SAMPLE_REPORT: Dict[str, Any] = {
    "concept_profile": [
        {"module_id": "M08", "module_name": "Th2_Polarization", "activation": 2.14, "coverage": 0.92, "direction": "up"},
        {"module_id": "M05", "module_name": "IL2R_JAKSTAT", "activation": 1.63, "coverage": 0.81, "direction": "up"},
        {"module_id": "M12", "module_name": "AP1_NFAT_Activation", "activation": 1.10, "coverage": 0.74, "direction": "up"},
        {"module_id": "M03", "module_name": "Costimulation", "activation": 0.86, "coverage": 0.40, "direction": "up"},
        {"module_id": "M06", "module_name": "IFN_Response", "activation": 0.52, "coverage": 0.88, "direction": "up"},
        {"module_id": "M20", "module_name": "Cell_Cycle_Proliferation", "activation": 0.34, "coverage": 0.66, "direction": "up"},
        {"module_id": "M11", "module_name": "NFkB_Axis", "activation": 0.12, "coverage": 0.71, "direction": "up"},
        {"module_id": "M01", "module_name": "TCR_Core_Receptor", "activation": -0.08, "coverage": 0.95, "direction": "down"},
        {"module_id": "M14", "module_name": "Metabolic_Switch", "activation": -0.41, "coverage": 0.58, "direction": "down"},
        {"module_id": "M13", "module_name": "PI3K_AKT_mTOR", "activation": -0.63, "coverage": 0.77, "direction": "down"},
        {"module_id": "M02", "module_name": "TCR_Proximal_Signaling", "activation": -0.79, "coverage": 0.83, "direction": "down"},
        {"module_id": "M04", "module_name": "Checkpoint_Module", "activation": -1.02, "coverage": 0.45, "direction": "down"},
        {"module_id": "M07", "module_name": "Th1_Polarization", "activation": -1.44, "coverage": 0.90, "direction": "down"},
        {"module_id": "M10", "module_name": "Treg_Modulation", "activation": -1.71, "coverage": 0.69, "direction": "down"},
        {"module_id": "M18", "module_name": "Exhaustion_Escape", "activation": -2.05, "coverage": 0.34, "direction": "down"},
        {"module_id": "M09", "module_name": "Th17_Polarization", "activation": None, "coverage": 0.0, "direction": "unknown"},
        {"module_id": "M15", "module_name": "Maturation_Memory_Trafficking", "activation": None, "coverage": 0.0, "direction": "unknown"},
        {"module_id": "M16", "module_name": "Chemotaxis_Tissue_Infiltration", "activation": None, "coverage": 0.0, "direction": "unknown"},
        {"module_id": "M17", "module_name": "Cytotoxic_Like_Differentiation", "activation": None, "coverage": 0.0, "direction": "unknown"},
        {"module_id": "M19", "module_name": "Memory_Fate_Program", "activation": None, "coverage": 0.0, "direction": "unknown"},
    ],
    "connected_target_hypotheses": [
        {"gene": "IL4R", "module_id": "M08", "screen_direction": "knockdown lowers Th2 program", "readiness_call": "watchlist", "caveat": "假設性線索,非用藥建議"},
        {"gene": "STAT5A", "module_id": "M05", "screen_direction": "knockdown lowers IL2R/JAK-STAT", "readiness_call": "candidate", "caveat": "假設性線索,非用藥建議"},
        {"gene": "TBX21", "module_id": "M07", "screen_direction": "knockdown lowers Th1 program", "readiness_call": "deprioritize", "caveat": "假設性線索,非用藥建議"},
        {"gene": "PDCD1", "module_id": "M04", "screen_direction": "knockdown lowers checkpoint program", "readiness_call": "watchlist", "caveat": "假設性線索,非用藥建議"},
    ],
    "caveat": (
        "探索性研究 demo — 非診斷、非治療建議、非療效預測。概念分數為 seed-gene 表現彙總"
        "(可手算稽核),unknown 概念代表無 seed 基因覆蓋、非測得 0。輸入僅在記憶體內運算,不落地。"
    ),
    "provenance": {
        "concept_set_version": "topic15_cd4_tcell_seed_modules::v0 (SAMPLE)",
        "screen_data_version": "gwt_reference::SAMPLE",
        "computed_at": "SAMPLE — not computed from live data",
    },
}
