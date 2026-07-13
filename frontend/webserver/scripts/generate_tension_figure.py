"""Generate the Home-page researcher-value / clinical-risk figure.

The source of truth is public/real-dataset.json.  Flagship labels are kept out
of the dense scatter cloud: the plot uses numbered highlights, while the right
panel provides an aligned, fixed-row key.  This makes the figure readable at
the final browser display size instead of only at its export resolution.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


WEB_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = WEB_ROOT / "public" / "real-dataset.json"
OUTPUT_DIR = WEB_ROOT / "public" / "flagship"

FLAGSHIPS = ["CD3E", "VAV1", "STAT3", "PLCG1", "BCL10"]

RISK = {
    "clear": {"label": "Clear", "color": "#0D7D5A"},
    "caution": {"label": "Caution", "color": "#B7791F"},
    "high": {"label": "High risk", "color": "#C85A11"},
    "avoid": {"label": "Avoid", "color": "#A4262C"},
}


def risk_for(target: dict) -> tuple[str, int]:
    readiness = target.get("readiness") or {}
    red_flags = len(readiness.get("redFlags") or [])
    liabilities = len(target.get("safetyLiabilities") or [])
    high_constraint = int((target.get("gnomad") or {}).get("constraintTier") == "high")
    flags = red_flags + liabilities + high_constraint
    tier = "avoid" if flags >= 3 else "high" if flags == 2 else "caution" if flags == 1 else "clear"
    return tier, flags


def percentile(values: np.ndarray, value: float) -> float:
    return float(np.count_nonzero(values <= value) / values.size * 100)


def build_figure(targets: list[dict]) -> plt.Figure:
    usable = [
        target
        for target in targets
        if isinstance(target.get("effect"), (int, float))
        and isinstance(target.get("nTotalDeGenes"), (int, float))
        and target["nTotalDeGenes"] > 0
    ]
    effect = np.asarray([target["effect"] for target in usable], dtype=float)
    breadth = np.asarray([target["nTotalDeGenes"] for target in usable], dtype=float)
    tiers = [risk_for(target)[0] for target in usable]
    tier_counts = {tier: tiers.count(tier) for tier in RISK}

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial"],
            "axes.edgecolor": "#1A1D24",
            "axes.labelcolor": "#1A1D24",
            "xtick.color": "#4A515E",
            "ytick.color": "#4A515E",
            "text.color": "#1A1D24",
        }
    )

    fig = plt.figure(figsize=(15.2, 8.6), facecolor="white")
    grid = fig.add_gridspec(1, 2, width_ratios=[1.72, 0.9], wspace=0.22)
    ax = fig.add_subplot(grid[0, 0])
    ranked = fig.add_subplot(grid[0, 1])

    # Draw low-risk points first and severe tiers last so the encoding remains
    # visible without enlarging or obscuring the cloud.
    for tier in RISK:
        mask = np.asarray([item == tier for item in tiers])
        ax.scatter(
            effect[mask],
            breadth[mask],
            s=14 if tier in {"high", "avoid"} else 11,
            c=RISK[tier]["color"],
            alpha=0.62 if tier in {"high", "avoid"} else 0.36,
            linewidths=0,
            rasterized=True,
            zorder=1,
        )

    by_gene = {target["gene"]: target for target in usable}
    effect_values = np.asarray([target["effect"] for target in usable], dtype=float)
    breadth_values = np.asarray([target["nTotalDeGenes"] for target in usable], dtype=float)
    flagship_rows: list[dict] = []

    for number, gene in enumerate(FLAGSHIPS, start=1):
        target = by_gene[gene]
        tier, flags = risk_for(target)
        score = (
            percentile(effect_values, float(target["effect"]))
            + percentile(breadth_values, float(target["nTotalDeGenes"]))
        ) / 2
        flagship_rows.append(
            {"number": number, "gene": gene, "target": target, "tier": tier, "flags": flags, "score": score}
        )
        ax.scatter(
            [target["effect"]],
            [target["nTotalDeGenes"]],
            s=140,
            c=RISK[tier]["color"],
            edgecolors="#111820",
            linewidths=2.0,
            zorder=5,
        )
        ax.text(
            target["effect"],
            target["nTotalDeGenes"],
            str(number),
            ha="center",
            va="center",
            color="white",
            fontsize=7.5,
            fontweight="bold",
            zorder=6,
        )

    ax.set_yscale("log")
    ax.set_xlim(-1.5, max(58, float(np.nanmax(effect)) + 1))
    ax.set_ylim(0.8, 8200)
    ax.set_xlabel(r"Perturbation effect size (max |log$_2$FC|)", fontsize=13, labelpad=10)
    ax.set_ylabel("Downstream breadth (DE genes, log scale)", fontsize=13, labelpad=10)
    ax.tick_params(labelsize=10, length=4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", which="major", color="#E8EBEF", linewidth=0.8, zorder=0)

    ax.set_title(
        "Researcher value: effect strength × downstream breadth",
        loc="left",
        fontsize=18,
        fontweight="bold",
        pad=54,
    )
    ax.text(
        0,
        1.055,
        f"{len(targets):,} CD4 perturbations · numbered flagships map to the aligned rows at right",
        transform=ax.transAxes,
        fontsize=10.5,
        color="#5F6672",
        va="bottom",
    )

    legend_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            markerfacecolor=RISK[tier]["color"],
            markeredgecolor="none",
            markersize=7,
            label=f"{RISK[tier]['label']} ({tier_counts[tier]:,})",
        )
        for tier in RISK
    ]
    ax.legend(
        handles=legend_handles,
        title="Clinical risk tier",
        loc="upper left",
        bbox_to_anchor=(0, 1.045),
        ncol=4,
        frameon=False,
        fontsize=9.5,
        title_fontsize=9.5,
        handletextpad=0.45,
        columnspacing=1.1,
        borderaxespad=0,
    )

    # A clean row layout replaces five free-floating labels and crossing leader
    # lines. Rows are sorted by researcher value and use identical baselines.
    flagship_rows.sort(key=lambda row: row["score"], reverse=True)
    y_positions = np.arange(len(flagship_rows) - 1, -1, -1, dtype=float) * 1.22
    ranked.set_xlim(77.5, 96.0)
    ranked.set_ylim(-0.72, y_positions[0] + 0.82)

    for row, y in zip(flagship_rows, y_positions):
        tier = row["tier"]
        score = row["score"]
        ranked.text(78.0, y + 0.17, f"{row['number']}  {row['gene']}", fontsize=13, fontweight="bold", va="center")
        suffix = "flag" if row["flags"] == 1 else "flags"
        ranked.text(
            78.0,
            y - 0.19,
            f"{RISK[tier]['label']} · {row['flags']} {suffix}",
            fontsize=9.5,
            color=RISK[tier]["color"],
            va="center",
        )
        ranked.hlines(y, 82.2, score, color="#CBD0D6", linewidth=2.2, zorder=1)
        ranked.scatter(
            [score],
            [y],
            s=188,
            c=RISK[tier]["color"],
            edgecolors="#111820",
            linewidths=1.8,
            zorder=3,
        )
        ranked.text(95.4, y, f"{score:.1f}", ha="right", va="center", fontsize=11.5, fontweight="bold")

    ranked.set_title("Conflict-zone flagships", loc="left", fontsize=18, fontweight="bold", pad=20)
    ranked.text(
        0,
        1.015,
        "Aligned labels · no text over data",
        transform=ranked.transAxes,
        fontsize=10.5,
        color="#5F6672",
        va="bottom",
    )
    ranked.set_xlabel("Researcher value (0–100)\nmean percentile of effect + breadth", fontsize=12, labelpad=10)
    ranked.set_yticks([])
    ranked.set_xticks([80, 85, 90, 95])
    ranked.tick_params(axis="x", labelsize=10, length=4)
    ranked.spines["top"].set_visible(False)
    ranked.spines["right"].set_visible(False)
    ranked.spines["left"].set_visible(False)
    ranked.spines["bottom"].set_color("#1A1D24")
    ranked.grid(False)

    fig.subplots_adjust(left=0.07, right=0.985, top=0.82, bottom=0.13)
    return fig


def main() -> None:
    with DATA_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    targets = payload["targets"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    figure = build_figure(targets)
    figure.savefig(OUTPUT_DIR / "fig_tension.png", dpi=160, facecolor="white")
    figure.savefig(OUTPUT_DIR / "fig_tension.svg", facecolor="white")
    plt.close(figure)


if __name__ == "__main__":
    main()
