"""
Standalone generating script for a Perturbase CD4+ T-cell Perturb-seq platform chart.

chart_id:        R9
source image:    R9_MA.png
chart title:     MA plot
language:        Python
env name:        python
packages:        matplotlib, pandas
input-artifact version_ids:
  - 11c6348b-f46d-48a3-8c22-7ae328f40c6c
  - 506b62e3-4ad0-42a0-ac4d-b779a31f8121
  - e168ccb9-6d5d-427c-a5cf-93f388492f2f
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

CCOL = {"Rest":"#4C72B0", "Stim8hr":"#DD8452", "Stim48hr":"#8172B3"}
ALARM = "#C44E52"

ma=de[(de['culture_condition']=="Stim8hr") & (de['target_baseMean']>0)].copy()
sig=ma['ontarget_significant'] & (~ma['offtarget_flag'])
off=ma['offtarget_flag']
fig,ax=plt.subplots(figsize=(6.4,4.6))
ax.scatter(ma.loc[~sig & ~off,'target_baseMean'], ma.loc[~sig & ~off,'ontarget_effect_size'],
           s=6,color="0.75",alpha=0.5,linewidth=0,label="Not significant")
ax.scatter(ma.loc[sig,'target_baseMean'], ma.loc[sig,'ontarget_effect_size'],
           s=7,color=CCOL["Stim8hr"],alpha=0.6,linewidth=0,label="On-target KD")
ax.scatter(ma.loc[off,'target_baseMean'], ma.loc[off,'ontarget_effect_size'],
           s=14,facecolor="none",edgecolor=ALARM,linewidth=0.6,label="Off-target flagged")
ax.axhline(0,color="0.35",lw=0.9)
ax.set_xscale("log")
ax.set_xlabel("Target baseline expression (mean normalized counts)")
ax.set_ylabel("On-target effect size (signed)")
ax.set_title("Knockdown is detectable across the full expression range (Stim 8 hr)")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"{v/1000:.0f}k" if v>=1000 else (f"{v:.0f}" if v>=1 else f"{v:g}")))
ax.legend(frameon=False,loc="lower right",fontsize=6,markerscale=1.6); ax.margins(x=0.03,y=0.05)
fig.tight_layout(); fig.savefig("R9_MA.png")