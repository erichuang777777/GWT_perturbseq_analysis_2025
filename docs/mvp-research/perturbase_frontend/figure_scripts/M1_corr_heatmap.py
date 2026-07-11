"""
Standalone figure-generating script.

chart_id            : M1
source image        : M1_corr_heatmap.png
chart title         : Pearson Correlation Heatmap of CD4+ T-Cell Target Discovery Metrics
language            : Python
conda env name      : python
input artifact vids : ['11c6348b-f46d-48a3-8c22-7ae328f40c6c']
referenced packages : matplotlib, numpy, os, pandas

Extracted verbatim from artifact lineage (host.lineage['83641d05-e1bd-459a-b083-44b64f349424']).
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


import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

raw = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/eb4c9b7d-b197-47c5-824c-efbd6bc2b805/v11c6348b_DE_stats.suppl_table.csv")

apply_figure_style(frame='open', sizes=(9,8,7))
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Helvetica Neue','Helvetica','Arial','DejaVu Sans','PingFang TC','Heiti TC']
mpl.rcParams['axes.unicode_minus'] = False

inc = raw[~raw.offtarget_flag].copy()

feat_cols = {
 'Cells assayed':'n_cells_target',
 'Genes up':'n_up_genes',
 'Genes down':'n_down_genes',
 'Total DE genes':'n_total_de_genes',
 'On-target effect':'ontarget_effect_size',
 'Downstream genes':'n_downstream',
}
FM = inc[list(feat_cols.values())].rename(columns={v:k for k,v in feat_cols.items()})

corrP = FM.corr(method='pearson')

fig, ax = plt.subplots(figsize=(6.2,5.4))
n = corrP.shape[0]
im = ax.imshow(corrP.values, cmap='RdBu_r', vmin=-1, vmax=1, aspect='equal')
ax.set_xticks(range(n)); ax.set_yticks(range(n))
ax.set_xticklabels(corrP.columns, rotation=35, ha='right')
ax.set_yticklabels(corrP.index)
for i in range(n):
    for j in range(n):
        v = corrP.values[i,j]
        ax.text(j,i,f"{v:.2f}",ha='center',va='center',
                color='white' if abs(v)>0.55 else '#222', fontsize=7)
i_de = list(corrP.index).index('Total DE genes'); i_ds=list(corrP.index).index('Downstream genes')
import matplotlib.patches as mpatches
ax.add_patch(mpatches.Rectangle((i_ds-0.5,i_de-0.5),1,1,fill=False,ec='k',lw=2))
ax.add_patch(mpatches.Rectangle((i_de-0.5,i_ds-0.5),1,1,fill=False,ec='k',lw=2))
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, ticks=[-1,-0.5,0,0.5,1])
cb.set_label('Pearson correlation (0 = no linear relation)')
ax.set_title('"Total DE genes" and "downstream genes" are the same signal (r≈1.00)', fontsize=9)
ax.set_xticks(np.arange(-.5,n,1),minor=True); ax.set_yticks(np.arange(-.5,n,1),minor=True)
ax.grid(which='minor',color='w',lw=1.2); ax.tick_params(which='minor',length=0)
fig.tight_layout()
fig.savefig('M1_corr_heatmap.png', dpi=300, bbox_inches='tight')
