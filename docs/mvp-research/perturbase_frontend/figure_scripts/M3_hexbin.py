"""
Standalone figure-generating script.

chart_id            : M3
source image        : M3_hexbin.png
chart title         : Hexbin Density: Cells Assayed vs. DE Gene Breadth Across CD4+ Targets
language            : Python
conda env name      : python
input artifact vids : ['11c6348b-f46d-48a3-8c22-7ae328f40c6c']
referenced packages : matplotlib, os

Extracted verbatim from artifact lineage (host.lineage['5f540aee-2e7b-4712-8d8b-37cf4d1a8bfb']).
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

x = inc.n_cells_target.values
y = inc.n_total_de_genes.values + 1

fig, ax = plt.subplots(figsize=(5.6, 4.8))
hb = ax.hexbin(x, y, gridsize=45, xscale='log', yscale='log', cmap='viridis', mincnt=1, norm=LogNorm())
ax.set_xlabel('Cells assayed per target')
ax.set_ylabel('Total DE genes (+1)')
cb = fig.colorbar(hb, ax=ax, fraction=0.046, pad=0.04)
cb.set_label('Targets per bin')
cb.set_ticks([1, 10, 100])
cb.set_ticklabels(['1', '10', '100'])
ax.set_xticks([100, 1000, 10000])
ax.set_xticklabels(['100', '1k', '10k'])
ax.set_yticks([1, 10, 100, 1000])
ax.set_yticklabels(['0', '10', '100', '1k'])
med = np.median(inc.n_total_de_genes) + 1
ax.axhline(med, color='#B4432E', lw=1.2, ls='--')
ax.text(ax.get_xlim()[0] * 1.4, med * 1.4, f'median = {int(med-1)} DE genes', color='#B4432E', fontsize=7, ha='left')
ax.set_title('Most perturbations move few genes, regardless of cells assayed', fontsize=9)
fig.tight_layout()
fig.savefig('M3_hexbin.png', dpi=300, bbox_inches='tight')
