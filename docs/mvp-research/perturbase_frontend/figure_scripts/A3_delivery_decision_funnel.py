"""
chart_id:        A3
source image:    delivery_decision_funnel.png
chart title:     Immune drug-delivery decision layer: turning 'important' into 'which drug can we make today'
language:        Python
env name:        python
input-artifact version_ids (1):
  - daeb84c7-c8df-4149-9464-191b1a6ba457  (target_master_table.csv)
packages referenced: matplotlib
"""

import matplotlib.pyplot as plt, numpy as np, pandas as pd

plt.rcParams["font.family"]="DejaVu Sans"; plt.rcParams["axes.unicode_minus"]=False
m=pd.read_csv('/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/46a1c017-4a49-46dc-8098-512c17286263/vdaeb84c7_target_master_table.csv')

full=m[m["is_ctx_specific"]].copy()

fig=plt.figure(figsize=(12,6.2)); gs=fig.add_gridspec(1,2,width_ratios=[1,1.15],wspace=0.28)
ax0=fig.add_subplot(gs[0])
stages=["Genome-wide\n11,526","Quality gate\n1,235","Context-specific\n96","Deliverable\n39"]; vals=[11526,1235,96,39]
cols=["#c9c9c9","#6a9bcc","#d97757","#788c5d"]; y=np.arange(4)[::-1]
for yi,v,c,lab in zip(y,vals,cols,stages):
    w=np.log10(v); ax0.barh(yi,w,color=c,height=0.62,zorder=3)
    ax0.text(w+0.05,yi,f"{v:,}",va="center",fontsize=10,fontweight="bold")
    ax0.text(0.05,yi,lab,va="center",ha="left",fontsize=8.5,color="white",fontweight="bold",zorder=4)
ax0.set_xlim(0,4.6); ax0.set_yticks([]); ax0.set_xticks([])
for sp in ax0.spines.values(): sp.set_visible(False)
ax0.set_title("Filter funnel: important → context-specific → deliverable",loc="left",fontsize=11)
ax1=fig.add_subplot(gs[1])
act=full[full["delivery_modality"]!="Awaiting modality (no known delivery route)"].copy()
act["mod_short"]=act["delivery_modality"].str.split(r" \(").str[0]
order=["CAR-T / ADC / antibody","Antibody","Small molecule"]
act["mod_short"]=pd.Categorical(act["mod_short"],categories=order,ordered=True)
act=act.sort_values(["mod_short","ctx_specific_de"],ascending=[True,False]).reset_index(drop=True)
POL={"repressor":"#c0504d","activator":"#4f81bd","mixed":"#9e9e9e"}
ypos=np.arange(len(act))[::-1]
ax1.barh(ypos,act["ctx_specific_de"].fillna(1).clip(lower=1),color=[POL.get(p,"#ccc") for p in act["polarity"]],height=0.7,zorder=3)
ax1.set_yticks(ypos); ax1.set_yticklabels(act["gene"],fontsize=6.8,style="italic")
ax1.set_xscale("log"); ax1.set_xlabel("Context-specific DE (Stim − Rest, log)")
bounds=act.groupby("mod_short",observed=True).size().cumsum().tolist()
for b in bounds[:-1]: ax1.axhline(len(act)-b-0.5,color="#888",lw=0.7,ls="--",zorder=1)
for mod,cnt,prev in zip(order,act.groupby("mod_short",observed=True).size(),[0]+bounds):
    ax1.text(ax1.get_xlim()[1]*1.05,len(act)-(prev+cnt/2),mod.split(" /")[0],rotation=90,va="center",ha="left",fontsize=7,fontweight="bold")
from matplotlib.patches import Patch
ax1.legend(handles=[Patch(color=POL[k],label=v) for k,v in [("repressor","repressor (KD → immune up)"),("activator","activator (KD → immune down)"),("mixed","mixed")]],frameon=False,fontsize=7,loc="lower right")
ax1.set_title("39 deliverable targets: modality (grouped) × polarity (colour)",loc="left",fontsize=11)
fig.suptitle("Immune drug-delivery decision layer: turning \"important\" into \"which drug can we make today\"",x=0.02,ha="left",fontsize=13,fontweight="bold")
fig.tight_layout(rect=[0,0,1,0.96])
fig.savefig("delivery_decision_funnel.png",dpi=300,bbox_inches="tight"); plt.close(fig)
