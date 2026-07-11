"""
Standalone generating script for a Perturbase CD4+ T-cell Perturb-seq platform chart.

chart_id:        R10
source image:    R10_dotmatrix.png
chart title:     Dot-plot matrix (scanpy)
language:        Python
env name:        python
packages:        matplotlib, pandas
input-artifact version_ids:
  - e168ccb9-6d5d-427c-a5cf-93f388492f2f
  - a58b4ba0-da04-46b9-9ad2-21a3e632615c
  - 11c6348b-f46d-48a3-8c22-7ae328f40c6c
  - 506b62e3-4ad0-42a0-ac4d-b779a31f8121
  - 024cefa5-3a8f-4e4e-b82a-51f356a03960
"""

import pandas as pd, numpy as np, matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 300,
    "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
    "xtick.labelsize": 6, "ytick.labelsize": 6, "legend.fontsize": 7,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.9, "axes.titlelocation": "left", "axes.titlepad": 8,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "font.family": ["DejaVu Sans"],
})

eff = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/34e69736-d190-40d4-853c-90e059c0d7b9/ve168ccb9_effect_matrix.csv", index_col=0)
demat = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/b6f9b507-3552-4d58-84f3-07354e0f53cb/va58b4ba0_de_matrix.csv", index_col=0)

COND = ["Rest","Stim8hr","Stim48hr"]
CLAB = {"Rest":"Rest","Stim8hr":"Stim 8 hr","Stim48hr":"Stim 48 hr"}

shortlist = ["CD3E","LAT","TADA2B","SENP5","PLCG1","VAV1","SGF29","UBXN1",
             "CD247","MED12","CCNC","SUPT20H","TADA1","DENR","PMVK"]
ital = lambda g: f"$\\it{{{g}}}$"

dm = demat.reindex(shortlist)[COND]
em = eff.reindex(shortlist)[COND]
order = dm.max(axis=1).sort_values().index.tolist()
dm = dm.reindex(order)
em = em.reindex(order)

fig, ax = plt.subplots(figsize=(5.6, 6.0))
ny = len(order); nx = len(COND)
smax = dm.values.max()
vlim = np.nanmax(np.abs(em.values))
norm = mpl.colors.TwoSlopeNorm(vmin=-vlim, vcenter=0, vmax=max(vlim*0.2, em.values.max()))
cmap = plt.cm.RdBu_r

for i, g in enumerate(order):
    for j, c in enumerate(COND):
        breadth = dm.loc[g, c]; effv = em.loc[g, c]
        size = 20 + (breadth / smax) * 520
        ax.scatter(j, i, s=size, color=cmap(norm(effv)), edgecolor="0.4", linewidth=0.4, zorder=3)

ax.set_xticks(range(nx)); ax.set_xticklabels([CLAB[c] for c in COND])
ax.set_yticks(range(ny)); ax.set_yticklabels([ital(g) for g in order])
ax.set_xlim(-0.5, nx-0.5); ax.set_ylim(-0.6, ny-0.4)
ax.set_title("Effect strength and breadth diverge across targets and time")
ax.set_axisbelow(True); ax.grid(color="0.93", lw=0.5)

sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap); sm.set_array([])
cb = fig.colorbar(sm, ax=ax, fraction=0.045, pad=0.02)
cb.set_label("On-target effect (signed; blue = silenced)", fontsize=6)
cb.ax.tick_params(labelsize=6)

for bk in [0.25, 0.5, 1.0]:
    ax.scatter([], [], s=20+bk*520, color="0.7", edgecolor="0.4", linewidth=0.4,
               label=f"{int(bk*smax/1000)}k" if bk*smax >= 1000 else f"{int(bk*smax)}")
ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.18, 1.0), fontsize=6,
          title="Breadth (genes)", labelspacing=1.4, borderpad=0.8,
          handles=[h for h in ax.collections[-3:]])

fig.tight_layout()
fig.savefig("R10_dotmatrix.png")