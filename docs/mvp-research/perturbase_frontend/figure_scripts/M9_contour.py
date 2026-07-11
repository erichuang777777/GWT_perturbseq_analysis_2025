"""
Standalone figure-generating script.

chart_id            : M9
source image        : M9_contour.png
chart title         : Contour
language            : Python
conda env name      : python
input artifact vids : ['11c6348b-f46d-48a3-8c22-7ae328f40c6c', '3d16f091-547f-4e36-861f-e1980da48a92']
referenced packages : matplotlib, os, scipy

Extracted verbatim from artifact lineage (host.lineage['854699e6-999d-4ff4-a170-9a1fa06cb57a']).
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
from scipy.stats import gaussian_kde

raw = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/eb4c9b7d-b197-47c5-824c-efbd6bc2b805/v11c6348b_DE_stats.suppl_table.csv")

apply_figure_style(frame='open', sizes=(9,8,7))
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Helvetica Neue','Helvetica','Arial','DejaVu Sans','PingFang TC','Heiti TC']
mpl.rcParams['axes.unicode_minus'] = False

inc = raw[~raw.offtarget_flag].copy()

sub = inc[inc.n_total_de_genes>0].copy()
x = sub.ontarget_effect_size.values
y = np.log10(sub.n_total_de_genes.values)
kde = gaussian_kde(np.vstack([x,y]))
xg = np.linspace(-32,4,180); yg = np.linspace(y.min(),y.max(),180)
XX,YY = np.meshgrid(xg,yg)
ZZ = kde(np.vstack([XX.ravel(),YY.ravel()])).reshape(XX.shape)
fig,ax = plt.subplots(figsize=(5.6,4.8))
cf = ax.contourf(XX,YY,ZZ,levels=10,cmap='viridis')
ax.contour(XX,YY,ZZ,levels=10,colors='white',linewidths=0.4,alpha=0.5)
ax.set_xlim(-32,4)
ax.set_xlabel('On-target effect size (log2 fold-change of the perturbed gene)')
ax.set_ylabel('Total DE genes')
ax.set_yticks([0,1,2,3]); ax.set_yticklabels(['1','10','100','1k'])
cb = fig.colorbar(cf,ax=ax,fraction=0.046,pad=0.04); cb.set_label('Density of targets (low to high)')
cb.set_ticks([])
ax.axvline(0,color='w',lw=0.8,ls=':')
ax.set_title('The response mass sits at weak knockdown and few DE genes', fontsize=9)
fig.tight_layout(); fig.savefig('M9_contour.png',dpi=300,bbox_inches='tight')
print("M9 v3 ok")
