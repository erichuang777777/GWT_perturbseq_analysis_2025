"""
Standalone generating script for a Perturbase CD4+ T-cell Perturb-seq platform chart.

chart_id:        R7
source image:    R7_errorbar.png
chart title:     Mean On-Target Effect Size by Stimulation Condition
language:        Python
env name:        python
packages:        matplotlib, pandas, scipy
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

COND = ["Rest","Stim8hr","Stim48hr"]
CCOL = {"Rest":"#4C72B0", "Stim8hr":"#DD8452", "Stim48hr":"#8172B3"}
CLAB = {"Rest":"Rest","Stim8hr":"Stim 8 hr","Stim48hr":"Stim 48 hr"}

inc = de[de['ontarget_significant'] & (~de['offtarget_flag'])].copy()

means={}; cis={}; ns={}
for c in COND:
    v=inc[inc['culture_condition']==c]['ontarget_effect_size'].dropna()
    from scipy import stats
    m=v.mean(); se=v.std(ddof=1)/np.sqrt(len(v)); tcrit=stats.t.ppf(0.975,len(v)-1)
    means[c]=m; cis[c]=tcrit*se; ns[c]=len(v)
fig,ax=plt.subplots(figsize=(4.8,4.4))
xpos=np.arange(len(COND))
ax.bar(xpos,[means[c] for c in COND],yerr=[cis[c] for c in COND],width=0.55,
       color=[CCOL[c] for c in COND],edgecolor="white",lw=0.6,
       error_kw=dict(ecolor="0.3",elinewidth=1.1,capsize=4))
ax.axhline(0,color="0.35",lw=0.9)
ax.set_xticks(xpos); ax.set_xticklabels([f"{CLAB[c]}\n(n={ns[c]:,})" for c in COND])
ax.set_ylabel("Mean on-target effect size (signed)")
ax.set_title("Silencing strength is stable across conditions (mean \u00b1 95% CI)")
for i,c in enumerate(COND):
    ax.text(i,means[c]-cis[c]-0.35,f"{means[c]:.1f}",ha="center",va="top",fontsize=6,color="0.25")
ax.margins(y=0.12)
fig.tight_layout(); fig.savefig("R7_errorbar.png")