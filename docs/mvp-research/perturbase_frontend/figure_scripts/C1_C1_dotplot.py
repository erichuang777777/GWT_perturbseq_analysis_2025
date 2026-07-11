"""
Standalone figure-generating script (Perturbase CD4+ T-cell Perturb-seq platform).

chart_id        : C1
source_image    : C1_dotplot.png
chart_title     : Knockdown effect and breadth across stimulation states
language        : Python
env_name        : python
packages        : matplotlib, numpy, pandas
input_artifacts : 506b62e3-4ad0-42a0-ac4d-b779a31f8121, e168ccb9-6d5d-427c-a5cf-93f388492f2f, a58b4ba0-da04-46b9-9ad2-21a3e632615c
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


import pandas as pd, numpy as np, matplotlib as mpl, matplotlib.pyplot as plt
figs = apply_figure_style()

eff = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/34e69736-d190-40d4-853c-90e059c0d7b9/ve168ccb9_effect_matrix.csv", index_col=0)
dem = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/b6f9b507-3552-4d58-84f3-07354e0f53cb/va58b4ba0_de_matrix.csv", index_col=0)

COND = ['Rest', 'Stim8hr', 'Stim48hr']
CCOL = {'Rest': '#4C6FB1', 'Stim8hr': '#E8A33D', 'Stim48hr': '#B5462E'}
CLAB = {'Rest': 'Rest', 'Stim8hr': 'Stim 8 hr', 'Stim48hr': 'Stim 48 hr'}
shortlist = ['CD3E', 'LAT', 'TADA2B', 'SENP5', 'PLCG1', 'VAV1', 'SGF29', 'UBXN1', 'CD247', 'MED12', 'CCNC', 'SUPT20H', 'TADA1', 'DENR', 'PMVK']

sl_present = [g for g in shortlist if g in eff.index]

sl_de = dem.loc[sl_present]  # n_DE
sl_ef = eff.loc[sl_present]  # signed effect
# order rows by mean |effect| descending (same as V5)
row_order = sl_ef.abs().mean(1).sort_values(ascending=True).index.tolist()  # ascending so top row = strongest at top
genes_c1 = row_order
from matplotlib.colors import TwoSlopeNorm
import matplotlib.cm as cm
vmin, vmax = sl_ef.values.min(), sl_ef.values.max()
# semantic zero centered diverging
tn = TwoSlopeNorm(vmin=min(vmin,-1), vcenter=0, vmax=max(vmax,1))
cmap = plt.get_cmap('RdBu_r')  # note: this is diverging; but avoid red/green -> RdBu is fine (blue/red not red/green)
# size scale from n_DE
de_all = sl_de.values.flatten()
smin, smax = 20, 320
def sz(n): 
    n=np.clip(n,0,None)
    return smin + (smax-smin)*(np.sqrt(n)/np.sqrt(max(de_all)))

fig_c1, ax = plt.subplots(figsize=(4.8,5.6))
ny=len(genes_c1)
for xi,cond in enumerate(COND):
    for yi,g in enumerate(genes_c1):
        e=sl_ef.loc[g,cond]; n=sl_de.loc[g,cond]
        ax.scatter(xi, yi, s=sz(n), c=[cmap(tn(e))], edgecolors='0.3', linewidths=0.4, zorder=3)
ax.set_xticks(range(3)); ax.set_xticklabels([CLAB[c] for c in COND], fontsize=7)
ax.set_yticks(range(ny)); ax.set_yticklabels(genes_c1, fontsize=7, fontstyle='italic')
ax.set_xlim(-0.5,2.5); ax.set_ylim(-0.7, ny-0.3)
ax.set_axisbelow(True); ax.grid(True, color='0.92', lw=0.5)
for s in ['top','right']: ax.spines[s].set_visible(False)
ax.set_title("Knockdown effect and breadth\nacross stimulation states", loc='left', fontsize=8)
# colorbar for effect
sm=cm.ScalarMappable(norm=tn,cmap=cmap); sm.set_array([])
cb=fig_c1.colorbar(sm, ax=ax, fraction=0.045, pad=0.03)
cb.set_label('On-target effect size (signed)', fontsize=6.5); cb.ax.tick_params(labelsize=6)
# size legend
for n,lab in [(10,'10'),(100,'100'),(1000,'1k')]:
    ax.scatter([],[],s=sz(n),c='0.7',edgecolors='0.3',linewidths=0.4,label=lab)
leg=ax.legend(title='DE genes', loc='upper left', bbox_to_anchor=(1.02,1.0), frameon=False,
              fontsize=6, title_fontsize=6.5, labelspacing=1.1, borderpad=0.8)
fig_c1.tight_layout()
fig_c1.savefig("C1_dotplot.png", dpi=300, bbox_inches='tight')