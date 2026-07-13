"""Generate the unified funnel shown in Explorer and the root README.

The portal readiness set (302) and the publication delivery-decision set (39)
are parallel outputs from the same measured screen.  They are deliberately
drawn as separate lanes so neither can be mistaken for a filter of the other.
All counts are recomputed from committed source files where available.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


WEB_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = WEB_ROOT.parents[1]
PORTAL_DATA = WEB_ROOT / "public" / "real-dataset.json"
DELIVERY_DATA = REPO_ROOT / "docs" / "mvp-research" / "pipeline" / "delivery_decision" / "delivery_decision_shortlist.csv"

PUBLIC_OUT = WEB_ROOT / "public" / "flagship"
README_OUT = REPO_ROOT / "docs" / "readme_assets"

SCREEN_COUNT = 11_526
PUBLICATION_GATE_COUNT = 1_235

INK = "#1A1D24"
MUTED = "#5F6672"
LINE = "#C9CED6"
PORTAL = "#1A5FB4"
PORTAL_LIGHT = "#EDF4FC"
PUBLICATION = "#D55E00"
PUBLICATION_LIGHT = "#FFF3EA"
CORE = "#6B40B8"
CORE_LIGHT = "#F3EEFB"
GREEN = "#009E73"
AMBER = "#E69F00"
GREY = "#A7ADB6"
RED = "#B44B52"


def read_sources() -> tuple[list[dict], list[dict]]:
    with PORTAL_DATA.open(encoding="utf-8") as handle:
        portal_targets = json.load(handle)["targets"]
    with DELIVERY_DATA.open(encoding="utf-8-sig", newline="") as handle:
        delivery_rows = list(csv.DictReader(handle))
    return portal_targets, delivery_rows


def publication_modality(value: str) -> str:
    if value.startswith("CAR-T"):
        return "CAR-T / ADC / antibody"
    if value.startswith("抗體"):
        return "Antibody"
    if value.startswith("小分子"):
        return "Small molecule"
    return "Awaiting modality"


def node(ax, x: float, y: float, w: float, h: float, label: str, count: int, color: str) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.008,rounding_size=0.012",
            facecolor="white",
            edgecolor=color,
            linewidth=2.0,
            zorder=3,
        )
    )
    ax.text(x + w / 2, y + h * 0.65, label, ha="center", va="center", fontsize=10.2, color=MUTED, fontweight="bold", zorder=4)
    ax.text(x + w / 2, y + h * 0.29, f"{count:,}", ha="center", va="center", fontsize=20, color=color, fontweight="bold", zorder=4)


def arrow(
    ax,
    start: tuple[float, float],
    end: tuple[float, float],
    label: str,
    color: str,
    label_offset: float = 0.022,
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=13,
            linewidth=1.8,
            color=color,
            shrinkA=2,
            shrinkB=2,
            zorder=2,
        )
    )
    ax.text((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + label_offset, label, ha="center", va="center", fontsize=9.0, color=MUTED, fontweight="bold")


def stack_bar(ax, x: float, y: float, w: float, h: float, values: list[int], colors: list[str]) -> None:
    total = sum(values)
    cursor = x
    for value, color in zip(values, colors):
        width = w * value / total
        ax.add_patch(Rectangle((cursor, y), width, h, facecolor=color, edgecolor="white", linewidth=0.8, zorder=3))
        cursor += width


def composition_card(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    first_values: list[int],
    first_colors: list[str],
    first_text: str,
    second_values: list[int],
    second_colors: list[str],
    second_text: str,
    border: str,
) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.008,rounding_size=0.012",
            facecolor="white",
            edgecolor=border,
            linewidth=1.4,
            zorder=2,
        )
    )
    ax.text(x + 0.012, y + h - 0.026, title, fontsize=10.5, color=INK, fontweight="bold", va="top")

    ax.text(x + 0.012, y + h - 0.067, first_text, fontsize=8.5, color=MUTED, va="top", fontweight="bold")
    stack_bar(ax, x + 0.012, y + h - 0.097, w - 0.024, 0.014, first_values, first_colors)

    ax.text(x + 0.012, y + 0.061, second_text, fontsize=8.5, color=MUTED, va="top", fontweight="bold")
    stack_bar(ax, x + 0.012, y + 0.027, w - 0.024, 0.014, second_values, second_colors)


def build_figure(portal_targets: list[dict], delivery_rows: list[dict]) -> tuple[plt.Figure, dict]:
    portal_count = len(portal_targets)
    calls = Counter((target.get("readiness") or {}).get("call", "unknown") for target in portal_targets)
    portal_gate = calls["validate"] + calls["advance"]
    portal_advance = calls["advance"]

    advance_rows = [target for target in portal_targets if (target.get("readiness") or {}).get("call") == "advance"]
    portal_modalities = Counter((target.get("readiness") or {}).get("tractabilityModality", "none") for target in advance_rows)
    portal_directions = Counter(
        "up" if (target.get("nUpGenes") or 0) > (target.get("nDownGenes") or 0) else "down" for target in advance_rows
    )

    publication_context = len(delivery_rows)
    known_delivery = [row for row in delivery_rows if publication_modality(row["delivery_modality"]) != "Awaiting modality"]
    publication_modalities = Counter(publication_modality(row["delivery_modality"]) for row in known_delivery)
    publication_polarity = Counter(row["polarity"] for row in known_delivery)

    primary = {target["gene"] for target in portal_targets if target.get("primaryOutcome")}
    deliverable = {row["gene"] for row in known_delivery}
    core = sorted(primary & deliverable)

    assert portal_count == 7_249
    assert portal_gate == 621
    assert portal_advance == 302
    assert publication_context == 96
    assert len(known_delivery) == 39
    assert len(primary) == 15
    assert core == ["CD247", "CD3E", "LAT", "PLCG1", "VAV1"]

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial"],
            "text.color": INK,
        }
    )
    fig, ax = plt.subplots(figsize=(16, 9), facecolor="white")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.035, 0.955, "One screen, two parallel funnels, one Core-5 intersection", fontsize=23, fontweight="bold", va="top")
    ax.text(
        0.035,
        0.912,
        "PORTAL   11,526 measured  ->  7,249 portal-included  ->  621 validate / advance  ->  302 advance-ready",
        fontsize=10.8,
        color=PORTAL,
        fontweight="bold",
        va="top",
    )
    ax.text(
        0.035,
        0.881,
        "PUBLICATION   11,526 measured  ->  1,235 QC-pass  ->  96 context-specific  ->  39 with a known modality",
        fontsize=10.8,
        color=PUBLICATION,
        fontweight="bold",
        va="top",
    )

    # Shared measured-screen start.
    node(ax, 0.035, 0.405, 0.145, 0.205, "Measured targets", SCREEN_COUNT, GREY)
    ax.text(0.1075, 0.435, "shared denominator", ha="center", fontsize=8.3, color=MUTED)

    # Parallel lane backgrounds and labels.
    ax.add_patch(FancyBboxPatch((0.205, 0.57), 0.76, 0.27, boxstyle="round,pad=0.008,rounding_size=0.014", facecolor=PORTAL_LIGHT, edgecolor="#CDDEF3", linewidth=1.2))
    ax.add_patch(FancyBboxPatch((0.205, 0.255), 0.76, 0.27, boxstyle="round,pad=0.008,rounding_size=0.014", facecolor=PUBLICATION_LIGHT, edgecolor="#F2D5C3", linewidth=1.2))
    ax.text(0.22, 0.815, "A · Portal readiness — current web-app decision set", fontsize=12.5, color=PORTAL, fontweight="bold", va="top")
    ax.text(0.22, 0.500, "B · Publication delivery-decision — separate analysis", fontsize=12.5, color=PUBLICATION, fontweight="bold", va="top")

    # Portal readiness lane.
    portal_y, node_w, node_h = 0.635, 0.125, 0.115
    portal_x = [0.23, 0.395, 0.56]
    node(ax, portal_x[0], portal_y, node_w, node_h, "Portal-included", portal_count, PORTAL)
    node(ax, portal_x[1], portal_y, node_w, node_h, "Validate + advance", portal_gate, PORTAL)
    node(ax, portal_x[2], portal_y, node_w, node_h, "Advance-ready", portal_advance, PORTAL)
    arrow(ax, (0.18, 0.54), (portal_x[0], portal_y + node_h / 2), "", PORTAL)
    arrow(ax, (portal_x[0] + node_w, portal_y + node_h / 2), (portal_x[1], portal_y + node_h / 2), f"validate/advance · {portal_gate / portal_count:.1%}", PORTAL, 0.09)
    arrow(ax, (portal_x[1] + node_w, portal_y + node_h / 2), (portal_x[2], portal_y + node_h / 2), f"advance call · {portal_advance / portal_gate:.1%}", PORTAL, 0.09)

    composition_card(
        ax,
        0.725,
        0.615,
        0.22,
        0.175,
        "302 advance-ready endpoint",
        [portal_modalities["small molecule"], portal_modalities["small molecule / biologic"], portal_modalities["none"]],
        [PORTAL, "#56A0D8", "#D5D8DD"],
        f"Tractability: {portal_modalities['small molecule']} SM · {portal_modalities['small molecule / biologic']} hybrid · {portal_modalities['none']} none",
        [portal_directions["up"], portal_directions["down"]],
        [GREEN, AMBER],
        f"Direction: {portal_directions['up']} up-dominant · {portal_directions['down']} down-dominant",
        PORTAL,
    )

    # Publication delivery-decision lane.
    publication_y = 0.32
    publication_x = [0.23, 0.395, 0.56]
    node(ax, publication_x[0], publication_y, node_w, node_h, "Publication QC-pass", PUBLICATION_GATE_COUNT, PUBLICATION)
    node(ax, publication_x[1], publication_y, node_w, node_h, "Context-specific", publication_context, PUBLICATION)
    node(ax, publication_x[2], publication_y, node_w, node_h, "Known modality", len(known_delivery), PUBLICATION)
    arrow(ax, (0.18, 0.475), (publication_x[0], publication_y + node_h / 2), "", PUBLICATION)
    arrow(ax, (publication_x[0] + node_w, publication_y + node_h / 2), (publication_x[1], publication_y + node_h / 2), f"context-specific · {publication_context / PUBLICATION_GATE_COUNT:.1%}", PUBLICATION, 0.09)
    arrow(ax, (publication_x[1] + node_w, publication_y + node_h / 2), (publication_x[2], publication_y + node_h / 2), f"known modality · {len(known_delivery) / publication_context:.1%}", PUBLICATION, 0.09)

    composition_card(
        ax,
        0.725,
        0.300,
        0.22,
        0.175,
        "39 known-modality endpoint",
        [publication_modalities["CAR-T / ADC / antibody"], publication_modalities["Antibody"], publication_modalities["Small molecule"]],
        [GREEN, "#65B89B", PORTAL],
        f"Modality: {publication_modalities['CAR-T / ADC / antibody']} CAR-T/ADC/Ab · {publication_modalities['Antibody']} Ab · {publication_modalities['Small molecule']} SM",
        [publication_polarity["mixed"], publication_polarity["repressor"], publication_polarity["activator"]],
        [GREY, RED, PORTAL],
        f"Polarity: {publication_polarity['mixed']} mixed · {publication_polarity['repressor']} repressor · {publication_polarity['activator']} activator",
        PUBLICATION,
    )

    # Explicit non-sequential cue between lanes.
    ax.text(
        0.49,
        0.548,
        "PARALLEL ENDPOINTS · 302 ≠ 39",
        ha="center",
        va="center",
        fontsize=9.5,
        color=INK,
        fontweight="bold",
        bbox={"boxstyle": "round,pad=0.38", "facecolor": "white", "edgecolor": LINE},
        zorder=5,
    )

    # Core-5 set equation.
    ax.text(0.22, 0.205, "Final intersection", fontsize=12.5, color=CORE, fontweight="bold", va="top")
    ax.text(0.22, 0.178, "Set A: breadth-ranked primary outcome. Set B: publication known-modality endpoint.", fontsize=9.5, color=MUTED, va="top")
    node(ax, 0.27, 0.055, 0.18, 0.095, "Set A · primary outcome", len(primary), CORE)
    ax.text(0.485, 0.102, "∩", fontsize=27, fontweight="bold", color=INK, ha="center", va="center")
    node(ax, 0.52, 0.055, 0.18, 0.095, "Set B · known modality", len(known_delivery), PUBLICATION)
    ax.text(0.73, 0.102, "=", fontsize=24, fontweight="bold", color=INK, ha="center", va="center")
    ax.add_patch(FancyBboxPatch((0.765, 0.045), 0.20, 0.115, boxstyle="round,pad=0.008,rounding_size=0.015", facecolor=CORE_LIGHT, edgecolor=CORE, linewidth=2.0))
    ax.text(0.865, 0.128, "Core-5", ha="center", va="center", fontsize=12.5, color=CORE, fontweight="bold")
    ax.text(0.865, 0.095, "CD3E · CD247 · LAT", ha="center", va="center", fontsize=9.7, color=INK, fontweight="bold")
    ax.text(0.865, 0.067, "PLCG1 · VAV1", ha="center", va="center", fontsize=9.7, color=INK, fontweight="bold")

    counts = {
        "portal": [portal_count, portal_gate, portal_advance],
        "publication": [PUBLICATION_GATE_COUNT, publication_context, len(known_delivery)],
        "primary": len(primary),
        "core": core,
    }
    return fig, counts


def main() -> None:
    portal_targets, delivery_rows = read_sources()
    figure, counts = build_figure(portal_targets, delivery_rows)
    PUBLIC_OUT.mkdir(parents=True, exist_ok=True)
    README_OUT.mkdir(parents=True, exist_ok=True)

    figure.savefig(PUBLIC_OUT / "fig_funnel.png", dpi=160, facecolor="white")
    figure.savefig(PUBLIC_OUT / "fig_funnel.svg", facecolor="white")
    figure.savefig(README_OUT / "druggability_funnel.png", dpi=160, facecolor="white")
    plt.close(figure)
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
