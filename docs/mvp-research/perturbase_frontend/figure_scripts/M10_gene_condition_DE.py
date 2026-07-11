"""
Standalone figure-generating script.

chart_id            : M10
source image        : M10_gene_condition_DE.png
chart title         : Top DE Gene Targets across TCR Stimulation Conditions
language            : Python
conda env name      : python
input artifact vids : ['11c6348b-f46d-48a3-8c22-7ae328f40c6c', 'e168ccb9-6d5d-427c-a5cf-93f388492f2f', 'a58b4ba0-da04-46b9-9ad2-21a3e632615c', '3d16f091-547f-4e36-861f-e1980da48a92']
referenced packages : matplotlib, os, scipy

Extracted verbatim from artifact lineage (host.lineage['b40d9294-52b5-4710-81c5-6950191913b0']).
Edit this single file to tweak the figure, then re-run in the 'python' environment.
"""

import matplotlib as mpl, matplotlib.pyplot as plt, numpy as np, pandas as pd
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from scipy.cluster.hierarchy import linkage, dendrogram

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

apply_figure_style(frame='open', sizes=(9,8,7))
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Helvetica Neue','Helvetica','Arial','DejaVu Sans','PingFang TC','Heiti TC']
mpl.rcParams['axes.unicode_minus'] = False

raw = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/eb4c9b7d-b197-47c5-824c-efbd6bc2b805/v11c6348b_DE_stats.suppl_table.csv")
demat = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/b6f9b507-3552-4d58-84f3-07354e0f53cb/va58b4ba0_de_matrix.csv", index_col=0)

COND = ['Rest','Stim8hr','Stim48hr']
COND_COLORS = {'Rest':'#4C78A8','Stim8hr':'#F58518','Stim48hr':'#B4432E'}
shortlist = ['CD3E','LAT','TADA2B','SENP5','PLCG1','VAV1','SGF29','UBXN1','CD247','MED12','CCNC','SUPT20H','TADA1','DENR','PMVK']

from matplotlib.colors import LogNorm

sl = [g for g in shortlist if g in demat.index]
D = demat.loc[sl, COND].copy()
Zr = linkage(np.log1p(D.values), method='ward')
order = dendrogram(Zr, no_plot=True)['leaves']
D = D.iloc[order]
fig = plt.figure(figsize=(5.8, 5.6))
gs = GridSpec(1, 3, width_ratios=[1.4, 7, 0.4], wspace=0.04)
axd = fig.add_subplot(gs[0]); axh = fig.add_subplot(gs[1]); axc = fig.add_subplot(gs[2])
dendrogram(Zr, ax=axd, orientation='left', color_threshold=0, above_threshold_color='#555', no_labels=True)
axd.invert_yaxis(); axd.set_axis_off()
V = D.values
im = axh.imshow(V, cmap='magma', norm=LogNorm(vmin=1, vmax=V.max()), aspect='auto')
axh.set_xticks(range(3)); axh.set_xticklabels(COND)
axh.set_yticks(range(len(D))); axh.set_yticklabels(D.index, fontstyle='italic')
for i in range(len(D)):
    for j in range(3):
        v = V[i, j]
        axh.text(j, i, f"{v/1000:.1f}k" if v >= 1000 else f"{v:.0f}", ha='center', va='center', fontsize=6.5,
                 color='white' if v < V.max() * 0.3 else 'black')
for lbl, c in zip(axh.get_xticklabels(), COND): lbl.set_color(COND_COLORS[c]); lbl.set_fontweight('bold')
cb = fig.colorbar(im, cax=axc); cb.set_label('DE genes (log scale)')
tcr = ['VAV1','CD247','LAT','CD3E','PLCG1']; idx = [list(D.index).index(g) for g in tcr]
axh.add_patch(mpatches.Rectangle((-0.5, min(idx)-0.5), 3, len(idx), fill=False, ec='#2CA02C', lw=2))
for lbl in axh.get_yticklabels():
    if lbl.get_text() in tcr: lbl.set_color('#2CA02C'); lbl.set_fontweight('bold')
axh.set_title('A TCR-signaling cluster (green) responds far more strongly\nafter stimulation than at rest', fontsize=9)
axh.set_xticks(np.arange(-.5, 3, 1), minor=True); axh.set_yticks(np.arange(-.5, len(D), 1), minor=True)
axh.grid(which='minor', color='w', lw=0.8); axh.tick_params(which='minor', length=0)
fig.savefig('M10_gene_condition_DE.png', dpi=300, bbox_inches='tight')
print("M10 v4 ok")
