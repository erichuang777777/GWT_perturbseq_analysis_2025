"""
Standalone generating script for a Perturbase CD4+ T-cell Perturb-seq platform chart.

chart_id:        R4
source image:    R4_waterfall.png
chart title:     Waterfall
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

COND = ["Rest","Stim8hr","Stim48hr"]
CCOL = {"Rest":"#4C72B0", "Stim8hr":"#DD8452", "Stim48hr":"#8172B3"}

inc = de[de['ontarget_significant'] & (~de['offtarget_flag'])].copy()
shortlist = ["CD3E","LAT","TADA2B","SENP5","PLCG1","VAV1","SGF29","UBXN1",
             "CD247","MED12","CCNC","SUPT20H","TADA1","DENR","PMVK"]
ital = lambda g: f"$\\it{{{g}}}$"

# ================= R4: Waterfall (ranked effect size, Stim8hr, all included) =================
w=inc[inc['culture_condition']=="Stim8hr"].copy().sort_values('ontarget_effect_size').reset_index(drop=True)
vals=w['ontarget_effect_size'].values; x=np.arange(len(vals))
fig,ax=plt.subplots(figsize=(6.6,4.2))
ax.bar(x,vals,width=1.0,color=CCOL["Stim8hr"],linewidth=0)
ax.axhline(0,color="0.35",lw=0.9)
# annotate shortlist positions with leaders
lut={g:i for i,g in enumerate(w['target_contrast_gene_name'])}
ann=[(g,lut[g]) for g in shortlist if g in lut]
ann=sorted(ann,key=lambda t:vals[t[1]])[:4]  # 4 strongest to keep <ceiling
# stagger label y-positions to avoid collisions
ylabs=[-46,-36,-26,-16]
for (g,i),yl in zip(ann,ylabs):
    ax.annotate(ital(g),(i,vals[i]),xytext=(i+len(vals)*0.05,yl),
                fontsize=6,ha="left",va="center",
                arrowprops=dict(arrowstyle="-",lw=0.5,color="0.5"))
pct_neg=(vals<0).mean()*100
ax.set_xlabel(f"Knockdowns ranked by on-target effect (n = {len(vals):,})")
ax.set_ylabel("On-target effect size")
_r4t = ("Nearly all on-target knockdowns reduce expression, with a deep tail"
        if pct_neg>=99 else "Most on-target knockdowns reduce expression, with a deep tail")
ax.set_title(_r4t)
ax.set_xlim(-len(vals)*0.01,len(vals)*1.01); ax.margins(y=0.05)
fig.tight_layout()
fig.savefig("R4_waterfall.png")