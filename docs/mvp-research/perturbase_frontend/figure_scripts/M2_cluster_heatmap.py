"""
Standalone figure-generating script.

chart_id            : M2
source image        : M2_cluster_heatmap.png
chart title         : Pearson Correlation Matrix of CD4+ T-Cell Target Features
language            : Python
conda env name      : python
input artifact vids : ['11c6348b-f46d-48a3-8c22-7ae328f40c6c']
referenced packages : matplotlib, os, scipy

Extracted verbatim from artifact lineage (host.lineage['cf645e23-b6db-40bd-b81a-84029f5e7751']).
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
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform

apply_figure_style(frame='open', sizes=(9,8,7))
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Helvetica Neue','Helvetica','Arial','DejaVu Sans','PingFang TC','Heiti TC']
mpl.rcParams['axes.unicode_minus'] = False

raw = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/eb4c9b7d-b197-47c5-824c-efbd6bc2b805/v11c6348b_DE_stats.suppl_table.csv")

inc = raw[~raw.offtarget_flag].copy()

feat_cols = {
    'Cells assayed': 'n_cells_target',
    'Genes up': 'n_up_genes',
    'Genes down': 'n_down_genes',
    'Total DE genes': 'n_total_de_genes',
    'On-target effect': 'ontarget_effect_size',
    'Downstream genes': 'n_downstream',
}
FM = inc[list(feat_cols.values())].rename(columns={v: k for k, v in feat_cols.items()})
corrP = FM.corr(method='pearson')

d = 1 - corrP.abs().values
np.fill_diagonal(d, 0)
Z = linkage(squareform(d, checks=False), method='average')

fig = plt.figure(figsize=(6.6, 6.2))
gs = GridSpec(2, 2, height_ratios=[1, 5], width_ratios=[20, 1], hspace=0.03, wspace=0.05)
axd = fig.add_subplot(gs[0, 0]); axh = fig.add_subplot(gs[1, 0]); axc = fig.add_subplot(gs[1, 1])
dd = dendrogram(Z, ax=axd, color_threshold=0, above_threshold_color='#555', no_labels=True)
order2 = dd['leaves']; labs = [corrP.index[i] for i in order2]; C = corrP.values[np.ix_(order2, order2)]
axd.set_axis_off()
n = len(labs)
im = axh.imshow(C, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
axh.set_xticks(range(n)); axh.set_yticks(range(n))
axh.set_xticklabels(labs, rotation=35, ha='right'); axh.set_yticklabels(labs)
for i in range(n):
    for j in range(n):
        v = C[i, j]; axh.text(j, i, f"{v:.2f}", ha='center', va='center', color='white' if abs(v) > 0.55 else '#222', fontsize=7)
axh.set_xticks(np.arange(-.5, n, 1), minor=True); axh.set_yticks(np.arange(-.5, n, 1), minor=True)
axh.grid(which='minor', color='w', lw=1.2); axh.tick_params(which='minor', length=0)
cb = fig.colorbar(im, cax=axc, ticks=[-1, -0.5, 0, 0.5, 1]); cb.set_label('Pearson correlation (0 = no linear relation)')
fig.suptitle('Clustering collapses the four DE-count metrics into one redundant block', fontsize=9, y=0.96, x=0.46)
fig.savefig('M2_cluster_heatmap.png', dpi=300, bbox_inches='tight')
