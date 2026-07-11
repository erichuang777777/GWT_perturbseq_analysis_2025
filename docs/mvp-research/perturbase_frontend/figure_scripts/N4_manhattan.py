"""
Standalone figure-generating script.

chart_id            : N4
source image        : N4_manhattan.png
chart title         : Downstream DE Gene Count by Target Gene and Stimulation Condition
language            : Python
conda env name      : python
input artifact vids : ['e168ccb9-6d5d-427c-a5cf-93f388492f2f', '11c6348b-f46d-48a3-8c22-7ae328f40c6c']
referenced packages : matplotlib, os, pandas

Extracted verbatim from artifact lineage (host.lineage['7ee3801b-289e-4b8d-a104-22c269b4e4b9']).
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

raw = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/eb4c9b7d-b197-47c5-824c-efbd6bc2b805/v11c6348b_DE_stats.suppl_table.csv")
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

d = raw[(raw['culture_condition'].isin(COND)) & (~raw['offtarget_flag'].astype(bool))].copy()
d = d[d['n_total_de_genes']>0]
genes_sorted = sorted(d['target_contrast_gene_name'].unique())
gidx = {gn:i for i,gn in enumerate(genes_sorted)}
d['x'] = d['target_contrast_gene_name'].map(gidx)

fig, ax = plt.subplots(figsize=(9.2,5.0))
for c in COND:
    dc = d[d['culture_condition']==c]
    ax.scatter(dc['x'], dc['n_total_de_genes'], s=5, color=CCOL[c], alpha=0.32,
               edgecolors='none', label=CLAB[c], rasterized=True)
ax.set_yscale('log')
ax.set_ylim(1, 40000)
ax.set_yticks([1,10,100,1000]); ax.set_yticklabels(['1','10','100','1,000'], fontsize=7)
ax.set_xlim(-100, len(genes_sorted)+100)
ax.set_xlabel("Target gene (alphabetical order)", fontproperties=zh(8.5))
ax.set_ylabel("Downstream DE gene count", fontproperties=zh(8.5))
ax.spines[['top','right']].set_visible(False)
ax.set_xticks([])

top_lab = d.groupby('target_contrast_gene_name')['n_total_de_genes'].max()
lab_genes = sorted([gn for gn in shortlist if top_lab.get(gn,0)>1000], key=lambda g:gidx[g])
band_y = 15000
n=len(lab_genes)
xspan=len(genes_sorted)
xt = np.linspace(xspan*0.03, xspan*0.97, n)
for (gn),xtar in zip(lab_genes,xt):
    xx=gidx[gn]; yy=top_lab[gn]
    ax.scatter([xx],[yy], s=24, facecolor='none', edgecolor='#222', lw=0.9, zorder=5)
    ax.annotate(ital(gn),(xx,yy),xytext=(xtar,band_y),textcoords='data',
                ha='center',va='bottom',fontsize=6.6,color='#222',
                arrowprops=dict(arrowstyle='-',color='#888',lw=0.4,
                                connectionstyle="arc3,rad=0"))
ax.set_title("A few core T-cell signaling targets drive most downstream transcriptional responses", fontproperties=zh(11), pad=8)
leg=ax.legend(loc='lower right', frameon=False, prop=zh(7.5), markerscale=2.2,
              handletextpad=0.3, ncol=3, columnspacing=1.0)
for lh in leg.legend_handles: lh.set_alpha(1)
fig.text(0.5,-0.02,"Off-target rows excluded; each point is one target\u00d7condition; labeled are shortlist genes with downstream DE >1000",
         ha='center', fontproperties=zh(6.8), color='#666')
fig.savefig('N4_manhattan.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
