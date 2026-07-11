"""
chart_id:        A6
source image:    figure_target_validation.png
chart title:     How we know a CD4+ T-cell Perturb-seq target is real
language:        Python
env name:        python
input-artifact version_ids (4):
  - b5899e1f-e6ae-4de8-8438-7be8def535dd  (benchmark_results.csv)
  - a76505a5-a3d7-4d2b-b6c7-0d6d2689b88f  (dropout_diagnosis.csv)
  - 26f49368-549f-4923-bf86-f02ca670180f  (context_specific_corrected.csv)
  - 6d81fd84-7016-4255-b730-0bb4a144cfcd  (delivery_modality_all_1235.csv)
packages referenced: matplotlib, numpy, os, pandas, sklearn
"""

import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from sklearn.metrics import roc_curve, roc_auc_score

# Global state
META_GREY = "#888888"


def apply_figure_style(*, frame="open", font=None, sizes=(8, 7, 6), grid=False):
    import matplotlib as mpl
    if frame not in ("open", "boxed", "none"):
        raise ValueError(f"frame must be 'open'|'boxed'|'none', got {frame!r}")
    try:
        import os, sys, glob, matplotlib.font_manager as fm
        fdir = os.path.join(os.environ.get("CONDA_PREFIX") or sys.prefix, "fonts")
        if os.path.isdir(fdir):
            known = {f.fname for f in fm.fontManager.ttflist}
            for f in glob.glob(os.path.join(fdir, "*.ttf")):
                if f not in known:
                    fm.fontManager.addfont(f)
    except Exception:
        pass
    base, secondary, tick = sizes
    boxed = (frame == "boxed")
    rc = {
        "font.family": "sans-serif",
        "font.size": base,
        "axes.labelsize": base,
        "axes.titlesize": base,
        "legend.fontsize": secondary,
        "xtick.labelsize": tick,
        "ytick.labelsize": tick,
        "axes.linewidth": 0.6,
        "xtick.direction": "out", "ytick.direction": "out",
        "xtick.major.size": 3, "ytick.major.size": 3,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "axes.spines.top": boxed, "axes.spines.right": boxed,
        "axes.spines.left": frame != "none", "axes.spines.bottom": frame != "none",
        "axes.grid": bool(grid),
        "legend.frameon": False,
        "figure.dpi": 200,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.titleweight": "normal",
        "axes.titlelocation": "left",
        "axes.labelweight": "normal",
        "lines.linewidth": 1.2,
        "patch.linewidth": 0.6,
        "pdf.fonttype": 42, "ps.fonttype": 42,
    }
    if font:
        rc["font.sans-serif"] = [font, "DejaVu Sans"]
    mpl.rcParams.update(rc)


def panel_letter(ax, letter, dx=-0.18, dy=1.02, case="lower", fontsize=None):
    import matplotlib.pyplot as plt
    if fontsize is None:
        fontsize = plt.rcParams.get("font.size", 8) + 1
    s = letter.lower() if case == "lower" else letter.upper()
    ax.text(dx, dy, s, transform=ax.transAxes,
            fontweight="bold", fontsize=fontsize, va="bottom", ha="left")


# Load data
b = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/ab6f9574-6ba6-46f5-85b6-84ba51d47dc9/vb5899e1f_benchmark_results.csv")
d = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/159093dd-3f0f-498e-aabc-f90d33097d03/va76505a5_dropout_diagnosis.csv")
c = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/b8771640-0103-4ed9-b2f0-9081d96735fe/v26f49368_context_specific_corrected.csv")
de = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/b9b601db-dc0e-4520-8ab9-3b25a0424645/v6d81fd84_delivery_modality_all_1235.csv")

# English mapping for delivery modality
modmap = {
    "待新模態 (無已知遞送方式)": "No known modality (awaiting new delivery)",
    "小分子 (胞內可成藥口袋)": "Small molecule (intracellular druggable pocket)",
    "抗體 (表面但胞外域有限)": "Antibody (surface, limited ectodomain)",
    "CAR-T / ADC / 抗體 (細胞表面+胞外域)": "CAR-T / ADC / antibody (surface + ectodomain)",
}
de["mod_en"] = de.delivery_modality.map(modmap)

apply_figure_style(sizes=(8, 7, 6))

pos = b[b.truth_class == "positive"]
rest = b[b.truth_class == "rest"]
neg = b[b.truth_class == "negative"]

# Panel A data: ROC curves
y_full = np.r_[np.ones(len(pos)), np.zeros(len(rest))]
s_full = np.r_[pos.ctx_specific_de.values, rest.ctx_specific_de.values]
fpr_f, tpr_f, _ = roc_curve(y_full, s_full)
auc_f = roc_auc_score(y_full, s_full)

y_sr = np.r_[np.ones(len(pos)), np.zeros(len(neg))]
s_sr = np.r_[pos.ctx_specific_de.values, neg.ctx_specific_de.values]
fpr_s, tpr_s, _ = roc_curve(y_sr, s_sr)
auc_s = roc_auc_score(y_sr, s_sr)

# Palettes
C_FOCAL = "#1f5fa8"
C_MUTE = "#b8b8b8"
C_ALARM = "#c0392b"
C_TRUE = "#2a8f5f"
C_ART = "#c0392b"

# Dropout tiers
sus = d[d.essentiality_tier == "likely_essential_dropout"]
wm = d[d.essentiality_tier == "well_measured"]

# Context classes
tr = c[c.ctx_class == "true_regulator"]
ar = c[c.ctx_class == "expression_artifact"]

# Deliverability
tr_genes = set(tr.gene)
dv = de[de.gene.isin(tr_genes)]
n_deliverable_nested = (dv.mod_en != "No known modality (awaiting new delivery)").sum()

plt.close("all")
fig = plt.figure(figsize=(7.4, 7.0))
gs = GridSpec(2, 2, figure=fig, hspace=0.55, wspace=0.34,
              left=0.095, right=0.975, top=0.895, bottom=0.085)

# ===== A : ROC =====
axA = fig.add_subplot(gs[0, 0])
axA.plot(fpr_f, tpr_f, color=C_FOCAL, lw=2.4, zorder=3, label=f"vs. all other genes  (AUROC {auc_f:.3f})")
axA.plot(fpr_s, tpr_s, color=C_MUTE, lw=1.6, ls="--", zorder=2, label=f"vs. 1 curated negative  (AUROC {auc_s:.3f})")
axA.plot([0, 1], [0, 1], color="#9a9a9a", lw=0.8, ls=":", zorder=1)
axA.set_xlim(-0.02, 1.02)
axA.set_ylim(-0.02, 1.02)
axA.set_aspect("equal")
axA.set_xlabel("False positive rate")
axA.set_ylabel("True positive rate")
axA.set_title("Context-specific DE ranks known\nCD4 regulators above the transcriptome", loc="left", fontsize=8)
axA.legend(frameon=False, fontsize=5.6, loc="lower right", handlelength=1.6, borderpad=0.2, labelspacing=0.3)
axA.text(0.03, 0.965, f"n = {len(pos)} positives", transform=axA.transAxes, fontsize=5.7, va="top", color="#555")

# ===== B : dropout survivorship =====
axB = fig.add_subplot(gs[0, 1])
axB.scatter(wm.n_cells_percentile, wm.loeuf, s=3, c=C_MUTE, alpha=0.28, edgecolors="none",
            zorder=1, rasterized=True, label=f"well-measured (n={len(wm):,})")
axB.scatter(sus.n_cells_percentile, sus.loeuf, s=9, c=C_ALARM, alpha=0.8, edgecolors="none",
            zorder=3, label=f"essential-dropout suspect (n={len(sus)})")
axB.set_xlim(-2, 102)
axB.set_ylim(-0.03, 2.0)
axB.set_xlabel("Cells recovered (percentile of screen)")
axB.set_ylabel("LOEUF  (lower = more constrained)")
axB.set_title("237 top targets are constraint artifacts:\nlost cells, not lost function", loc="left", fontsize=8)
axB.axhline(0.35, color="#777", lw=0.7, ls="--", zorder=2)
axB.text(101, 0.30, "constraint\nthreshold 0.35", fontsize=5.3, ha="right", va="top", color="#555")
axB.legend(frameon=False, fontsize=5.6, loc="upper right", handlelength=1.0, borderpad=0.2, labelspacing=0.3, markerscale=1.3)
axB.text(0.42, 0.30, "94% of suspects\nLOEUF < 0.35", transform=axB.transAxes, fontsize=5.9, color=C_ALARM, va="center", ha="left")

# ===== C : baseline correction =====
axC = fig.add_subplot(gs[1, 0])
axC.scatter(tr.rest_baseMean, tr.de_Stim_max, s=11, c=C_TRUE, alpha=0.8, edgecolors="none",
            zorder=3, label=f"true regulator (n={len(tr)})")
axC.scatter(ar.rest_baseMean, ar.de_Stim_max, s=24, c=C_ART, alpha=0.9, edgecolors="none",
            zorder=4, marker="D", label=f"expression artifact (n={len(ar)})")
axC.set_xscale("log")
axC.set_xlim(0.1, 400)
axC.axvspan(0.1, 10, color=C_ART, alpha=0.07, zorder=0)
axC.axvline(10, color="#777", lw=0.7, ls="--", zorder=2)
axC.set_xlabel("Resting baseline expression (baseMean)")
axC.set_ylabel("Peak stimulated DE signal")
axC.set_title("Baseline correction flags 11 hits with\nnear-zero resting expression", loc="left", fontsize=8)
axC.legend(frameon=False, fontsize=5.6, loc="upper right", handlelength=1.0, borderpad=0.2, labelspacing=0.3, markerscale=1.2)
axC.text(0.28, 0.55, "all 11 artifacts\nbaseMean < 10", transform=axC.transAxes, fontsize=5.9, color=C_ART, ha="center", va="center")

# ===== D : funnel lollipop =====
axD = fig.add_subplot(gs[1, 1])
stages = ["Candidates\nscreened", "Context-specific\nhits", "Baseline-confirmed\nregulators", "Deliverable\n(known modality)"]
vals = [len(de), len(c), len(tr), int(n_deliverable_nested)]
cols = [C_MUTE, "#7ba7cf", C_FOCAL, C_TRUE]
ypos = np.arange(len(stages))[::-1]
for yi, v, col in zip(ypos, vals, cols):
    axD.plot([20, v], [yi, yi], color=col, lw=1.4, zorder=2)
    axD.scatter([v], [yi], s=70, color=col, zorder=3)
    axD.text(v * 1.18, yi, f"{v:,}", va="center", ha="left", fontsize=6.8, fontweight="bold")
axD.set_yticks(ypos)
axD.set_yticklabels(stages, fontsize=6.2)
axD.set_xscale("log")
axD.set_xlim(20, 2600)
axD.set_ylim(-0.6, 3.6)
axD.set_xlabel("Targets remaining (log scale)")
axD.set_title("Discovery funnel: 1,235 candidates\nnarrow to 34 deliverable targets", loc="left", fontsize=8)

for L, ax in zip("abcd", [axA, axB, axC, axD]):
    panel_letter(ax, L, case="lower")

fig.suptitle("How we know a CD4$^+$ T-cell Perturb-seq target is real",
             x=0.02, y=0.975, ha="left", fontsize=10, fontweight="bold")

fig.savefig("figure_target_validation.png", dpi=300, bbox_inches="tight", facecolor="white")
