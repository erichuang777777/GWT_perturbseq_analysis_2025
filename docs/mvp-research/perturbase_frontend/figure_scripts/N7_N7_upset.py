"""
Standalone generating script for a Perturbase CD4+ T-cell Perturb-seq platform chart.

chart_id:        N7
source image:    N7_upset.png
chart title:     UpSet plot
language:        Python
env name:        python
packages:        collections, matplotlib, os, pandas
input-artifact version_ids:
  - 11c6348b-f46d-48a3-8c22-7ae328f40c6c
  - 506b62e3-4ad0-42a0-ac4d-b779a31f8121
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
from matplotlib.gridspec import GridSpec
from collections import Counter

apply_figure_style(sizes=(8,7,6))
os.makedirs('out', exist_ok=True)

raw = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/eb4c9b7d-b197-47c5-824c-efbd6bc2b805/v11c6348b_DE_stats.suppl_table.csv")
curated = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/71b03570-3c70-4117-bd81-90917d27ab6b/v506b62e3_curated_targets.csv")

g = raw.groupby('target_contrast_gene_name')
significant = set(g['ontarget_significant'].max()[lambda s: s>0].index)
has_offtarget = set(g['offtarget_flag'].max()[lambda s: s>0].index)
passes_gate = set(curated[curated['passes_gate']==1]['target_contrast_gene_name'].unique())
m = g['n_total_de_genes'].max().sort_values(ascending=False)
broad = set(m[m>=4870].index)

CCOL = {'Rest':'#4C72B0','Stim8hr':'#DD8452','Stim48hr':'#8172B3'}

def zh(size=None, weight=None):
    fp = FontProperties(family='DejaVu Sans')
    if size: fp.set_size(size)
    if weight: fp.set_weight(weight)
    return fp

sets = {'significant':significant, 'passes gate':passes_gate,
        'off-target':has_offtarget, 'broad effect':broad}
names = list(sets.keys())
universe = set().union(*sets.values())
memb = Counter(tuple(e in sets[n] for n in names) for e in universe)
combos = sorted([(k,v) for k,v in memb.items() if v>0], key=lambda x:-x[1])
setcol = {names[0]:CCOL['Rest'], names[1]:'#55A868', names[2]:CCOL['Stim8hr'], names[3]:CCOL['Stim48hr']}
set_totals = {n:len(s) for n,s in sets.items()}
row_order = names

fig = plt.figure(figsize=(8.4,5.6))
gs = GridSpec(2,2, height_ratios=[2.6,1.5], width_ratios=[1.0,3.6], hspace=0.05, wspace=0.04)
ax_bar = fig.add_subplot(gs[0,1]); ax_mat = fig.add_subplot(gs[1,1], sharex=ax_bar)
ax_tot = fig.add_subplot(gs[1,0], sharey=ax_mat)
x = np.arange(len(combos)); vals=[v for k,v in combos]
ax_bar.bar(x, vals, width=0.6, color='#555555', zorder=3)
for xi,vv in zip(x,vals):
    ax_bar.text(xi, vv+max(vals)*0.015, f"{vv:,}", ha='center', va='bottom', fontsize=6.5)
ax_bar.set_ylabel("Intersection size (genes)", fontproperties=zh(8))
ax_bar.spines[['top','right']].set_visible(False)
ax_bar.set_ylim(0, max(vals)*1.13); ax_bar.tick_params(labelbottom=False)
ax_bar.set_yticks([0,2000,4000]); ax_bar.set_yticklabels(['0','2k','4k'], fontsize=6)

ny=len(row_order)
for xi,(k,v) in enumerate(combos):
    active=[i for i in range(ny) if k[i]]
    for yi in range(ny):
        ax_mat.scatter(xi, ny-1-yi, s=70, color=setcol[row_order[yi]] if k[yi] else '#DDDDDD', zorder=3)
    if len(active)>1:
        ax_mat.plot([xi,xi],[ny-1-max(active),ny-1-min(active)], color='#444444', lw=1.4, zorder=2)
ax_mat.set_xlim(-0.6,len(combos)-0.4); ax_mat.set_ylim(-0.6,ny-0.4)
ax_mat.set_yticks(range(ny))
ax_mat.set_yticklabels([row_order[ny-1-i].replace(chr(10),' ') for i in range(ny)], fontproperties=zh(7.5))
ax_mat.set_xticks([])
for sp in ax_mat.spines.values(): sp.set_visible(False)
ax_mat.tick_params(length=0)

yt=np.arange(ny); tot_vals=[set_totals[row_order[ny-1-i]] for i in range(ny)]
ax_tot.barh(yt, tot_vals, color=[setcol[row_order[ny-1-i]] for i in range(ny)], height=0.55, zorder=3)
ax_tot.invert_xaxis(); ax_tot.set_yticks([])
ax_tot.spines[['top','left','right']].set_visible(False)
ax_tot.set_xlabel("Set size", fontproperties=zh(7.5))
ax_tot.set_xticks([0,4000,8000]); ax_tot.set_xticklabels(['0','4k','8k'], fontsize=6)
for yi,tv in zip(yt,tot_vals):
    ax_tot.text(tv+300, yi, f"{tv:,}", va='center', ha='right', fontsize=6, color='#333')

fig.suptitle("Most significant genes are significant-only; gate-passing and off-target are largely exclusive, broad-effect genes almost all pass the gate",
             fontproperties=zh(10.5), y=0.99, x=0.55)
fig.savefig('N7_upset.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)