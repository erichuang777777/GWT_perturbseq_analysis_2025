"""
Standalone figure-generating script.

chart_id            : M5
source image        : M5_scatter_matrix.png
chart title         : Pairwise structure of DE metrics: effect size decouples from response breadth
language            : Python
conda env name      : python
input artifact vids : ['11c6348b-f46d-48a3-8c22-7ae328f40c6c', '506b62e3-4ad0-42a0-ac4d-b779a31f8121', '3d16f091-547f-4e36-861f-e1980da48a92']
referenced packages : matplotlib, os, scipy

Extracted verbatim from artifact lineage (host.lineage['4712945d-edaa-4e21-9afe-31a2286951f9']).
Edit this single file to tweak the figure, then re-run in the 'python' environment.
"""

import matplotlib as mpl, matplotlib.pyplot as plt, numpy as np, pandas as pd
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform, pdist

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
mpl.rcParams['font.family']='sans-serif'
mpl.rcParams['font.sans-serif']=['Helvetica Neue','Helvetica','Arial','DejaVu Sans','PingFang TC','Heiti TC']
mpl.rcParams['axes.unicode_minus']=False

raw=pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/eb4c9b7d-b197-47c5-824c-efbd6bc2b805/v11c6348b_DE_stats.suppl_table.csv")
curated=pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/71b03570-3c70-4117-bd81-90917d27ab6b/v506b62e3_curated_targets.csv")
COND=['Rest','Stim8hr','Stim48hr']
COND_COLORS={'Rest':'#4C78A8','Stim8hr':'#F58518','Stim48hr':'#B4432E'}
shortlist=['CD3E','LAT','TADA2B','SENP5','PLCG1','VAV1','SGF29','UBXN1','CD247','MED12','CCNC','SUPT20H','TADA1','DENR','PMVK']
inc=raw[~raw.offtarget_flag].copy()
feat_cols={'Cells assayed':'n_cells_target','Genes up':'n_up_genes','Genes down':'n_down_genes','Total DE genes':'n_total_de_genes','On-target effect':'ontarget_effect_size','Downstream genes':'n_downstream'}
FM=inc[list(feat_cols.values())].rename(columns={v:k for k,v in feat_cols.items()})
corrP=FM.corr(method='pearson')
ARR='\u2192'  # placeholder, avoid in labels

# M5 scatter matrix: 4 non-redundant features (drop one of DE/downstream since r=1; keep effect, cells, DE, up/down)
# Use: Cells assayed, On-target effect, Total DE genes(log1p), Genes up(log1p)
cols=['Cells assayed','On-target effect','Total DE genes','Genes up']
D=FM[cols].copy()
D['Cells assayed']=np.log10(D['Cells assayed'])
D['Total DE genes']=np.log10(D['Total DE genes']+1)
D['Genes up']=np.log10(D['Genes up']+1)
disp={'Cells assayed':'Cells\n(log10)','On-target effect':'On-target\neffect','Total DE genes':'DE genes\n(log10)','Genes up':'Genes up\n(log10)'}
n=len(cols)
fig,axes=plt.subplots(n,n,figsize=(7.2,7.2))
for i in range(n):
    for j in range(n):
        ax=axes[i,j]
        xi,yi=D[cols[j]].values,D[cols[i]].values
        if i==j:
            ax.hist(xi,bins=40,color='#4C78A8',alpha=0.85)
            ax.set_yticks([])
        else:
            ax.hexbin(xi,yi,gridsize=30,cmap='viridis',mincnt=1,bins='log',linewidths=0)
        if i<n-1: ax.set_xticklabels([])
        if j>0 and not(i==j): ax.set_yticklabels([])
        if j==0 and i!=0: ax.set_ylabel(disp[cols[i]],fontsize=7)
        if i==n-1: ax.set_xlabel(disp[cols[j]],fontsize=7)
        ax.tick_params(labelsize=6)
fig.suptitle('Pairwise structure of DE metrics: effect size decouples from response breadth',fontsize=9,y=0.995)
fig.tight_layout()
fig.savefig('M5_scatter_matrix.png',dpi=300,bbox_inches='tight')
print("M5 ok")
