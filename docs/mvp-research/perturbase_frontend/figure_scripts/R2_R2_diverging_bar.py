"""
Standalone generating script for a Perturbase CD4+ T-cell Perturb-seq platform chart.

chart_id:        R2
source image:    R2_diverging_bar.png
chart title:     Diverging bar
language:        Python
env name:        python
packages:        matplotlib, numpy, pandas
input-artifact version_ids:
  - 11c6348b-f46d-48a3-8c22-7ae328f40c6c
  - 506b62e3-4ad0-42a0-ac4d-b779a31f8121
  - e168ccb9-6d5d-427c-a5cf-93f388492f2f
  - a58b4ba0-da04-46b9-9ad2-21a3e632615c
  - 024cefa5-3a8f-4e4e-b82a-51f356a03960
"""

import pandas as pd
import numpy as np
import matplotlib as mpl
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

COND = ["Rest", "Stim8hr", "Stim48hr"]
CCOL = {"Rest": "#4C72B0", "Stim8hr": "#DD8452", "Stim48hr": "#8172B3"}

inc = de[de['ontarget_significant'] & (~de['offtarget_flag'])].copy()

shortlist = ["CD3E", "LAT", "TADA2B", "SENP5", "PLCG1", "VAV1", "SGF29", "UBXN1",
             "CD247", "MED12", "CCNC", "SUPT20H", "TADA1", "DENR", "PMVK"]
ital = lambda g: f"$\\it{{{g}}}$"

def kfmt(v, _=None):
    a = abs(v)
    return (f"{a/1000:.0f}k" if a >= 1000 else f"{a:.0f}")

sub = inc[(inc['culture_condition'] == "Stim8hr") & (inc['target_contrast_gene_name'].isin(shortlist))]
sub = sub.groupby('target_contrast_gene_name')[['n_up_genes', 'n_down_genes']].max().reindex(shortlist).dropna()
sub['net'] = sub['n_up_genes'] - sub['n_down_genes']
sub = sub.sort_values('net')
genes = sub.index.tolist()
y = np.arange(len(genes))
xmax = max(sub['n_up_genes'].max(), sub['n_down_genes'].max())

fig, ax = plt.subplots(figsize=(6.2, 5.4))
ax.barh(y, -sub['n_down_genes'], color=CCOL["Rest"], height=0.72, edgecolor="white", lw=0.5, label="Down-regulated")
ax.barh(y, sub['n_up_genes'], color=CCOL["Stim8hr"], height=0.72, edgecolor="white", lw=0.5, label="Up-regulated")
ax.axvline(0, color="0.35", lw=1.0)
ax.set_yticks(y)
ax.set_yticklabels([ital(g) for g in genes])
ax.set_xlabel("Downstream genes   \u2190 down-regulated      up-regulated \u2192")
ax.set_title("Knockdown up-regulates more genes than it silences (12 of 13, Stim 8 hr)")
ax.set_xlim(-xmax * 1.12, xmax * 1.12)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(kfmt))
ax.margins(y=0.03)
ax.legend(frameon=False, loc="lower left", fontsize=6)
fig.tight_layout()
fig.savefig("R2_diverging_bar.png")