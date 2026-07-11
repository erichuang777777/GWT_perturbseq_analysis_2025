"""
Standalone generating script for a Perturbase CD4+ T-cell Perturb-seq platform chart.

chart_id:        R6
source image:    R6_grouped_bar.png
chart title:     Grouped bar
language:        Python
env name:        python
packages:        matplotlib, numpy, pandas
input-artifact version_ids:
  - a58b4ba0-da04-46b9-9ad2-21a3e632615c
  - 11c6348b-f46d-48a3-8c22-7ae328f40c6c
  - 506b62e3-4ad0-42a0-ac4d-b779a31f8121
  - e168ccb9-6d5d-427c-a5cf-93f388492f2f
  - 024cefa5-3a8f-4e4e-b82a-51f356a03960
"""

import pandas as pd
import numpy as np
import matplotlib as mpl
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
demat = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/b6f9b507-3552-4d58-84f3-07354e0f53cb/va58b4ba0_de_matrix.csv", index_col=0)

COND = ["Rest", "Stim8hr", "Stim48hr"]
CCOL = {"Rest": "#4C72B0", "Stim8hr": "#DD8452", "Stim48hr": "#8172B3"}
CLAB = {"Rest": "Rest", "Stim8hr": "Stim 8 hr", "Stim48hr": "Stim 48 hr"}

shortlist = ["CD3E", "LAT", "TADA2B", "SENP5", "PLCG1", "VAV1", "SGF29", "UBXN1",
             "CD247", "MED12", "CCNC", "SUPT20H", "TADA1", "DENR", "PMVK"]
ital = lambda g: f"$\\it{{{g}}}$"

def kfmt(v, _=None):
    a = abs(v)
    return (f"{a/1000:.0f}k" if a >= 1000 else f"{a:.0f}")

top6 = demat.reindex(shortlist)[COND].max(axis=1).sort_values(ascending=False).head(6).index.tolist()
g6 = demat.reindex(top6)[COND]
fig, ax = plt.subplots(figsize=(6.4, 4.2))
xpos = np.arange(len(top6))
bw = 0.26
for j, c in enumerate(COND):
    ax.bar(xpos + (j - 1) * bw, g6[c].values, width=bw, color=CCOL[c], edgecolor="white", lw=0.5, label=CLAB[c])
ax.set_xticks(xpos)
ax.set_xticklabels([ital(g) for g in top6])
ax.set_ylabel("Downstream genes differentially expressed")
ax.set_title("Peak response lands at 8 hr for most top targets, not 48 hr")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(kfmt))
ax.legend(frameon=False, loc="upper right", fontsize=6)
ax.margins(y=0.08)
fig.tight_layout()
fig.savefig("R6_grouped_bar.png")