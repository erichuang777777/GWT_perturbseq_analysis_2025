"""
Standalone figure-generating script.

chart_id            : N6
source image        : N6_stacked_area.png
chart title         : CD4+ T-cell targets by differentially expressed gene count
language            : Python
conda env name      : python
input artifact vids : ['a58b4ba0-da04-46b9-9ad2-21a3e632615c']
referenced packages : matplotlib, numpy, os, pandas

Extracted verbatim from artifact lineage (host.lineage['f4a4ed8d-023f-48d8-841e-f44ca5f6945a']).
Edit this single file to tweak the figure, then re-run in the 'python' environment.
"""

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
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.font_manager import FontProperties

apply_figure_style(sizes=(8,7,6))
os.makedirs('out', exist_ok=True)

de = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/b6f9b507-3552-4d58-84f3-07354e0f53cb/va58b4ba0_de_matrix.csv", index_col=0)

COND = ['Rest','Stim8hr','Stim48hr']
CLAB = {'Rest':'Rest','Stim8hr':'Stim 8hr','Stim48hr':'Stim 48hr'}

def zh(size=None, weight=None):
    fp = FontProperties(family='DejaVu Sans')
    if size: fp.set_size(size)
    if weight: fp.set_weight(weight)
    return fp

tiers = [(0,10,'1–9'),(10,50,'10–49'),(50,200,'50–199'),(200,1000,'200–999'),(1000,10**9,'≥1000')]
tier_labels = [t[2] for t in tiers]
comp = {}
for c in COND:
    col = de[c].dropna()
    col = col[col>0]
    counts=[]
    for lo,hi,lab in tiers:
        counts.append(((col>=lo)&(col<hi)).sum())
    comp[c]=counts
compdf = pd.DataFrame(comp, index=[t[2] for t in tiers])

plotted_tot = compdf.sum(axis=0)
fig, ax = plt.subplots(figsize=(7.2,5.2))
x=np.arange(3)
ramp = plt.cm.viridis(np.linspace(0.15,0.9,len(tiers)))
ax.stackplot(x, compdf.values, labels=tier_labels, colors=ramp, alpha=0.92, edgecolor='white', lw=0.6)
ax.set_xticks(x); ax.set_xticklabels([CLAB[c] for c in COND], fontsize=8.5)
ax.set_ylabel("Number of affected targets", fontproperties=zh(8.5))
ax.set_title("Targets with large downstream responses (\u22651000 DE genes) increase slightly after stimulation; overall composition stable",
             fontproperties=zh(10.5), pad=10)
ax.spines[['top','right']].set_visible(False)
ax.set_yticks([0,2000,4000,6000,8000,10000])
ax.set_yticklabels(['0','2k','4k','6k','8k','10k'], fontsize=7)
cum=np.cumsum(compdf['Stim48hr'].values); prev=0
for i,lab in enumerate(tier_labels):
    ymid=(prev+cum[i])/2; prev=cum[i]
    ax.annotate(lab, (2, ymid), xytext=(6,0), textcoords='offset points',
                va='center', fontsize=6.8, color='#333',
                path_effects=[pe.withStroke(linewidth=1.5, foreground='white')])
ax.set_xlim(0,2.3)
pt = plotted_tot
fig.text(0.5,-0.02,
    f"Targets with \u22651 DE gene only: n = {int(pt['Rest']):,} / {int(pt['Stim8hr']):,} / {int(pt['Stim48hr']):,}"
    " (Rest / Stim 8hr / Stim 48hr); bands are DE-gene-count tiers, light to dark = small to large downstream response",
    ha='center', fontproperties=zh(7), color='#555')
fig.savefig('out/N6_stacked_area.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
