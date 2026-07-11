"""
Standalone figure-generating script.

chart_id            : M4
source image        : M4_density_scatter.png
chart title         : 2D density
language            : Python
conda env name      : python
input artifact vids : ['11c6348b-f46d-48a3-8c22-7ae328f40c6c']
referenced packages : matplotlib, os

Extracted verbatim from artifact lineage (host.lineage['23035b79-eb5c-4707-9d2b-581428425047']).
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
from matplotlib.colors import LogNorm

raw = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/eb4c9b7d-b197-47c5-824c-efbd6bc2b805/v11c6348b_DE_stats.suppl_table.csv")

apply_figure_style(frame='open', sizes=(9,8,7))
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Helvetica Neue','Helvetica','Arial','DejaVu Sans','PingFang TC','Heiti TC']
mpl.rcParams['axes.unicode_minus'] = False

inc = raw[~raw.offtarget_flag].copy()

sub = inc[inc.n_total_de_genes>0].copy()
x = sub.ontarget_effect_size.values
y = np.log10(sub.n_total_de_genes.values)

nb=80
H,xe,ye=np.histogram2d(x,y,bins=nb)
ix=np.clip(np.digitize(x,xe)-1,0,nb-1); iy=np.clip(np.digitize(y,ye)-1,0,nb-1)
dens=H[ix,iy]
o=np.argsort(dens)
fig,ax=plt.subplots(figsize=(5.6,4.8))
sc=ax.scatter(x[o],y[o],c=dens[o],s=5,cmap='mako' if False else 'viridis',norm=LogNorm(vmin=1),edgecolors='none',rasterized=True)
ax.set_xlabel('On-target effect size (log2 fold-change of the perturbed gene)')
ax.set_ylabel('Total DE genes')
ax.set_yticks([0,1,2,3]); ax.set_yticklabels(['1','10','100','1k'])
cb=fig.colorbar(sc,ax=ax,fraction=0.046,pad=0.04); cb.set_label('Targets at this density')
ax.axvline(0,color='#888',lw=0.8,ls=':')
me=np.median(x)
ax.set_title('Stronger knockdown coincides with broader transcriptional response', fontsize=9)
ax.margins(0.03)
fig.tight_layout(); fig.savefig('M4_density_scatter.png',dpi=300,bbox_inches='tight')
print("M4 ok n=",len(x),"median eff",round(me,2))
