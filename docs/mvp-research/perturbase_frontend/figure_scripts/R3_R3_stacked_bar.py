"""
Standalone generating script for a Perturbase CD4+ T-cell Perturb-seq platform chart.

chart_id:        R3
source image:    R3_stacked_bar.png
chart title:     Distribution of knockdown response magnitudes across REST, 8-hour, and 48-hour stimulation conditions
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
curated = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/71b03570-3c70-4117-bd81-90917d27ab6b/v506b62e3_curated_targets.csv")

COND = ["Rest","Stim8hr","Stim48hr"]
CCOL = {"Rest":"#4C72B0", "Stim8hr":"#DD8452", "Stim48hr":"#8172B3"}
CLAB = {"Rest":"Rest","Stim8hr":"Stim 8 hr","Stim48hr":"Stim 48 hr"}

inc = de[de['ontarget_significant'] & (~de['offtarget_flag'])].copy()
gate_df = curated[curated['passes_gate']].copy()

def bbox_check(fig, tol=1.0):
    r=fig.canvas.get_renderer(); seen=[]; texts=[]
    for t in fig.findobj(mpl.text.Text):
        if not (t.get_text().strip() and t.get_visible()): continue
        e=t.get_window_extent(r)
        if any(abs(e.x0-s.x0)<tol and abs(e.y0-s.y0)<tol and abs(e.x1-s.x1)<tol for s in seen): continue
        seen.append(e); texts.append((t,e))
    ov=[(a.get_text(),b.get_text()) for i,(a,ba) in enumerate(texts) for b,bb in texts[i+1:]
        if ba.overlaps(bb) and a.get_text()!=b.get_text()]
    return len(ov)

cat_order=["no effect","1 DE gene","2-10 DE genes",">10 DE genes"]
# Composition across ALL tested knockdowns per condition (every category present here).
comp=(de.groupby(['culture_condition','n_total_genes_category']).size()
        .unstack(fill_value=0).reindex(COND))
cat_order=[c for c in cat_order if c in comp.columns]
comp=comp[cat_order]
compf=comp.div(comp.sum(axis=1),axis=0)*100
cat_cols=["#D9D9D9","#BFD3E6","#7BA7CF","#3A6EA5"]  # sequential single-hue ramp for ordinal magnitude
fig,ax=plt.subplots(figsize=(5.6,4.4))
xpos=np.arange(len(COND)); bottom=np.zeros(len(COND))
for cat,col in zip(cat_order,cat_cols):
    vals=compf[cat].values
    ax.bar(xpos,vals,bottom=bottom,color=col,width=0.62,edgecolor="white",lw=0.6,label=cat)
    for xi,(v,b) in enumerate(zip(vals,bottom)):
        if v>=4: ax.text(xi,b+v/2,f"{v:.0f}%",ha="center",va="center",fontsize=6,
                         color="white" if col in ("#3A6EA5","#7BA7CF") else "0.25")
    bottom+=vals
ax.set_xticks(xpos); ax.set_xticklabels([CLAB[c] for c in COND])
ax.set_ylabel("Share of tested knockdowns (%)"); ax.set_ylim(0,100)
# data-driven claim: is the >10 DE share monotically rising Rest->8hr->48hr?
share_big=compf[">10 DE genes"].values
mono_up = share_big[0] < share_big[1] and share_big[1] < share_big[2]
_t="Response-size composition is nearly constant across conditions"
ax.set_title(_t)
ax.legend(frameon=False,loc="center left",bbox_to_anchor=(1.01,0.5),fontsize=6,title="Downstream DE genes")
fig.tight_layout(); fig.savefig("R3_stacked_bar.png")