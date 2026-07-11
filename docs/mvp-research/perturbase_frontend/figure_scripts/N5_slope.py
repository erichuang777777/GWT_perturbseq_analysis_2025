"""
Standalone figure-generating script.

chart_id            : N5
source image        : N5_slope.png
chart title         : CD4+ T-cell knockdown effect trajectories across stimulation time course
language            : Python
conda env name      : python
input artifact vids : ['e168ccb9-6d5d-427c-a5cf-93f388492f2f']
referenced packages : matplotlib, os, pandas

Extracted verbatim from artifact lineage (host.lineage['b7d68ed3-0431-47d1-90ba-4a00e6735ac1']).
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


import pandas as pd, numpy as np, os
import matplotlib as mpl, matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D

apply_figure_style(sizes=(8,7,6))
os.makedirs('out', exist_ok=True)

effect = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/34e69736-d190-40d4-853c-90e059c0d7b9/ve168ccb9_effect_matrix.csv", index_col=0)

COND = ['Rest','Stim8hr','Stim48hr']
CLAB = {'Rest':'Rest','Stim8hr':'Stim 8hr','Stim48hr':'Stim 48hr'}
CCOL = {'Rest':'#4C72B0','Stim8hr':'#DD8452','Stim48hr':'#8172B3'}
shortlist = ['CD3E','LAT','TADA2B','SENP5','PLCG1','VAV1','SGF29','UBXN1','CD247','MED12','CCNC','SUPT20H','TADA1','DENR','PMVK']

def zh(size=None, weight=None):
    fp = FontProperties(family='DejaVu Sans')
    if size: fp.set_size(size)
    if weight: fp.set_weight(weight)
    return fp

def ital(s): return f"$\\it{{{s}}}$"

sl = [gn for gn in shortlist if gn in effect.index]
sub = effect.loc[sl, COND]

def spread_labels(ax, items, x, dx, fontsize, min_gap):
    items = sorted(items, key=lambda t: t[1])
    ys = [it[1] for it in items]
    placed = list(ys)
    for i in range(1,len(placed)):
        if placed[i]-placed[i-1] < min_gap:
            placed[i] = placed[i-1]+min_gap
    for lab,(y0),c,py in zip([it[0] for it in items],[it[1] for it in items],[it[2] for it in items],placed):
        ax.annotate(lab,(x,y0),xytext=(x+dx,py),textcoords='data',va='center',
                    fontsize=fontsize,color=c,
                    arrowprops=dict(arrowstyle='-',color=c,lw=0.5,alpha=0.6,
                                    connectionstyle="arc3,rad=0"))

fig, ax = plt.subplots(figsize=(7.2,6.2))
xpos=[0,1,2]
delta=(sub['Stim48hr']-sub['Rest'])
right_items=[]
for gn in sub.index:
    y=sub.loc[gn].values
    weaken=delta[gn]>0
    col=CCOL['Stim48hr'] if weaken else CCOL['Rest']
    ax.plot(xpos,y,'-',color=col,lw=1.3,alpha=0.75,zorder=2,marker='o',ms=3.5)
    right_items.append((ital(gn), sub.loc[gn,'Stim48hr'], col))
spread_labels(ax, right_items, x=2, dx=0.12, fontsize=6.8, min_gap=1.35)
ax.set_xticks(xpos); ax.set_xticklabels([CLAB[c] for c in COND], fontsize=8)
ax.set_xlim(-0.15,2.75)
ax.set_ylabel("On-target effect size (more negative = stronger knockdown)", fontproperties=zh(8.5))
ax.set_title("Most core T-cell target effects weaken\ntoward zero after 48 h stimulation",
             fontproperties=zh(11), pad=10, loc='left', y=1.01)
ax.spines[['top','right']].set_visible(False)
leg=[Line2D([0],[0],color=CCOL['Stim48hr'],lw=1.5,label='Effect weakens with stimulation (12/15)'),
     Line2D([0],[0],color=CCOL['Rest'],lw=1.5,label='Effect strengthens with stimulation (3/15)')]
ax.legend(handles=leg, loc='lower left', frameon=False, prop=zh(7.5))
fig.savefig('N5_slope.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
