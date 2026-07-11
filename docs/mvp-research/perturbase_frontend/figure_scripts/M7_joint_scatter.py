"""
Standalone figure-generating script.

chart_id            : M7
source image        : M7_joint_scatter.png
chart title         : Target Cell Assay Coverage vs. Differential Expression: Joint Distribution
language            : Python
conda env name      : python
input artifact vids : ['11c6348b-f46d-48a3-8c22-7ae328f40c6c', '506b62e3-4ad0-42a0-ac4d-b779a31f8121', '3d16f091-547f-4e36-861f-e1980da48a92']
referenced packages : matplotlib, os

Extracted verbatim from artifact lineage (host.lineage['3761f44a-31ce-4d93-b5bb-bd02fd800ac9']).
Edit this single file to tweak the figure, then re-run in the 'python' environment.
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


import matplotlib as mpl, matplotlib.pyplot as plt, numpy as np, pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.colors import LogNorm

raw = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/eb4c9b7d-b197-47c5-824c-efbd6bc2b805/v11c6348b_DE_stats.suppl_table.csv")
curated = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/71b03570-3c70-4117-bd81-90917d27ab6b/v506b62e3_curated_targets.csv")

apply_figure_style(frame='open', sizes=(9,8,7))
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Helvetica Neue','Helvetica','Arial','DejaVu Sans','PingFang TC','Heiti TC']
mpl.rcParams['axes.unicode_minus'] = False

raw = raw.merge(curated[['index','passes_gate','logDE']], on='index', how='left')
inc = raw[~raw.offtarget_flag].copy()

sub = inc.copy()
x = np.log10(sub.n_cells_target.values); y = np.log10(sub.n_total_de_genes.values+1)
passg = sub.passes_gate.fillna(False).values.astype(bool)
fig = plt.figure(figsize=(6.0,6.0))
gs = GridSpec(2,2,width_ratios=[5,1.1],height_ratios=[1.1,5],hspace=0.04,wspace=0.04)
axj = fig.add_subplot(gs[1,0]); axx = fig.add_subplot(gs[0,0],sharex=axj); axy = fig.add_subplot(gs[1,1],sharey=axj)
axj.hexbin(x,y,gridsize=45,cmap='Greys',mincnt=1,norm=LogNorm(),linewidths=0)
axj.scatter(x[passg],y[passg],s=6,color='#B4432E',edgecolors='none',alpha=0.55,label='Passes target gate (n=2,131)')
axj.set_xlabel('Cells assayed per target (log10)'); axj.set_ylabel('Total DE genes (log10, +1)')
axj.set_yticks([0,1,2,3]); axj.set_yticklabels(['0','10','100','1k'])
axj.set_xticks([2,3,4]); axj.set_xticklabels(['100','1k','10k'])
axj.axvline(np.log10(200),color='#333',lw=0.8,ls='--')
axj.axhline(np.log10(51),color='#333',lw=0.8,ls='--')
axj.text(np.log10(210),0.05,'>=200 cells',color='#333',fontsize=6,rotation=90,va='bottom')
axj.text(3.9,np.log10(53),'>=50 DE genes',color='#333',fontsize=6,ha='right',va='bottom')
axj.legend(loc='upper left',frameon=False,fontsize=7)
axx.hist(x,bins=60,color='#bbb'); axx.hist(x[passg],bins=60,color='#B4432E',alpha=0.8)
axy.hist(y,bins=60,orientation='horizontal',color='#bbb'); axy.hist(y[passg],bins=60,orientation='horizontal',color='#B4432E',alpha=0.8)
for a in (axx,axy): a.set_axis_off()
fig.suptitle('Gate-passing targets need both ample cells and many DE genes',fontsize=9,x=0.45,y=0.965)
fig.savefig('M7_joint_scatter.png',dpi=300,bbox_inches='tight')
print("M7 v2 ok")
