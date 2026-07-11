"""
Standalone generating script for a Perturbase CD4+ T-cell Perturb-seq platform chart.

chart_id:        R5
source image:    R5_bubble.png
chart title:     CD4+ T-Cell Target Discovery: Downstream Gene Breadth vs. On-Target Effect Size
language:        Python
env name:        python
packages:        matplotlib, pandas
input-artifact version_ids:
  - 11c6348b-f46d-48a3-8c22-7ae328f40c6c
  - e168ccb9-6d5d-427c-a5cf-93f388492f2f
  - 506b62e3-4ad0-42a0-ac4d-b779a31f8121
  - a58b4ba0-da04-46b9-9ad2-21a3e632615c
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

de = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/eb4c9b7d-b197-47c5-824c-efbd6bc2b805/v11c6348b_DE_stats.suppl_table.csv")

COND = ["Rest","Stim8hr","Stim48hr"]
CCOL = {"Rest":"#4C72B0", "Stim8hr":"#DD8452", "Stim48hr":"#8172B3"}
CLAB = {"Rest":"Rest","Stim8hr":"Stim 8 hr","Stim48hr":"Stim 48 hr"}

inc = de[de['ontarget_significant'] & (~de['offtarget_flag'])].copy()

shortlist = ["CD3E","LAT","TADA2B","SENP5","PLCG1","VAV1","SGF29","UBXN1",
             "CD247","MED12","CCNC","SUPT20H","TADA1","DENR","PMVK"]

b = inc[inc['target_contrast_gene_name'].isin(shortlist)].copy()
b = b[b['n_total_de_genes']>0]

fig, ax = plt.subplots(figsize=(6.4,4.8))
for c in COND:
    s = b[b['culture_condition']==c]
    ax.scatter(s['n_total_de_genes'], s['ontarget_effect_size'],
               s=np.clip(s['n_cells_target']/6,10,300), color=CCOL[c], alpha=0.72,
               edgecolor="white", linewidth=0.5, label=CLAB[c])
ax.set_xscale("log")
ax.set_xlabel("Downstream genes differentially expressed (breadth)")
ax.set_ylabel("On-target effect size (signed)")
ax.set_title("Silencing strength and response breadth vary independently across targets")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"{v/1000:.0f}k" if v>=1000 else f"{v:.0f}"))
ax.margins(0.06)
leg1 = ax.legend(frameon=False, loc="lower right", fontsize=6, title="Condition")
ax.add_artist(leg1)
for ncell in [200,1000,3000]:
    ax.scatter([],[],s=np.clip(ncell/6,10,300),color="0.6",alpha=0.6,edgecolor="white",
               label=f"{ncell:,} cells")
ax.legend(frameon=False, loc="upper left", fontsize=6, title="Cells per target",
          handletextpad=1.0, labelspacing=1.2, borderpad=0.8,
          handles=[h for h in ax.collections[-3:]])
fig.tight_layout()
fig.savefig("R5_bubble.png")