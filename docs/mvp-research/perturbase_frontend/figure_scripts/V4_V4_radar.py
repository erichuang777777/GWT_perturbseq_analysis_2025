"""
Standalone generating script for a Perturbase CD4+ T-cell Perturb-seq platform chart.

chart_id:        V4
source image:    V4_radar.png
chart title:     Curated targets differ in how knockdown magnitude shifts with stimulation
language:        Python
env name:        python
packages:        matplotlib, numpy, os, pandas
input-artifact version_ids:
  - e168ccb9-6d5d-427c-a5cf-93f388492f2f
  - a58b4ba0-da04-46b9-9ad2-21a3e632615c
"""

# skill:figure-style kernel.py (auto-injected on skill load)
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


import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

apply_figure_style()

eff = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/34e69736-d190-40d4-853c-90e059c0d7b9/ve168ccb9_effect_matrix.csv", index_col=0)

COND = ['Rest', 'Stim8hr', 'Stim48hr']
CCOL = {'Rest': '#4C6FB1', 'Stim8hr': '#E8A33D', 'Stim48hr': '#B5462E'}
CLAB = {'Rest': 'Rest', 'Stim8hr': 'Stim 8 hr', 'Stim48hr': 'Stim 48 hr'}
shortlist = ['CD3E', 'LAT', 'TADA2B', 'SENP5', 'PLCG1', 'VAV1', 'SGF29', 'UBXN1', 'CD247', 'MED12', 'CCNC', 'SUPT20H', 'TADA1', 'DENR', 'PMVK']

feat = eff.dropna(how='any').copy()
feat_genes = feat.index.tolist()
sl_present = [g for g in shortlist if g in feat.index]

sl_eff = eff.loc[sl_present]
vals = np.abs(sl_eff.values)  # rows=genes, cols=conditions
genes = sl_present
N = len(genes)
angles = np.linspace(0, 2*np.pi, N, endpoint=False)
ang_closed = np.concatenate([angles, angles[:1]])

fig_v4, ax = plt.subplots(figsize=(5.8, 6.0), subplot_kw=dict(polar=True))
ax.set_theta_offset(np.pi/2); ax.set_theta_direction(-1)
rmax = 45
for j, cond in enumerate(COND):
    v = np.concatenate([vals[:, j], vals[:1, j]])
    ax.plot(ang_closed, v, color=CCOL[cond], lw=1.7, label=CLAB[cond], zorder=4)
    ax.fill(ang_closed, v, color=CCOL[cond], alpha=0.09, zorder=2)
ax.set_xticks(angles); ax.set_xticklabels([])
for a, g in zip(angles, genes):
    ax.text(a, rmax*1.09, g, fontsize=6.2, fontstyle='italic', ha='center', va='center')
ax.set_ylim(0, rmax); ax.set_yticks([15, 30, 45])
ax.set_yticklabels(['15', '30', '45'], fontsize=6, color='0.45'); ax.set_rlabel_position(258)
ax.grid(color='0.85', lw=0.5); ax.spines['polar'].set_color('0.85')
ax.set_title("Curated targets differ in how knockdown magnitude shifts with stimulation", loc='center', pad=26)
ax.legend(loc='upper right', bbox_to_anchor=(1.20, 1.10), frameon=False, fontsize=6.5)
fig_v4.text(0.5, 0.055, "Radius = on-target |effect size|; each spoke a curated target", ha='center', fontsize=6.5, color='0.4')
fig_v4.savefig("V4_radar.png", dpi=300, bbox_inches='tight')