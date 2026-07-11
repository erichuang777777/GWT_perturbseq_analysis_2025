"""
chart_id:        A11
source image:    dev_vs_user_gap.png
chart title:     The Developer–User Gap: Six Blindspots in Perturbase
language:        Python
env name:        python
input-artifact version_ids (0):
  (none)
packages referenced: matplotlib
"""

import matplotlib.pyplot as plt, numpy as np
from matplotlib.patches import FancyArrowPatch

# skill:figure-style kernel.py (auto-injected on skill load) - apply_figure_style and set_frame used below
# Since we don't have the actual skill, we'll define minimal stubs
def apply_figure_style(sizes=(9,8,7)):
    plt.rcParams.update({
        'axes.spines.top': False,
        'axes.spines.right': False,
    })

def set_frame(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

apply_figure_style(sizes=(9,8,7))
plt.rcParams["font.family"]="DejaVu Sans"; plt.rcParams["axes.unicode_minus"]=False

# Six blindspots: developer "built it" self-assessment vs user "can actually use it" (0-10)
blind=[
 ("Gene absence\n\"why isn't my gene here?\"", 9, 2, "Now: any-gene search + funnel diagnosis"),
 ("Known vs novel\nCD3E ranks #1 = old target", 8, 3, "Now: novelty flag + 'novel-only' toggle"),
 ("Clinical positioning\npatient-risk vs target-risk", 7, 3, "Now: dual-mode, honest safety lookup"),
 ("Single-dataset fragility\npolished UI hides risk", 8, 2, "Now: evidence-strength + context banner"),
 ("Action loop\nranked list, then what?", 6, 2, "Partial: CSV export (feedback loop = future)"),
 ("Jargon wall\nLOEUF 0.1 = ?", 9, 3, "Now: plain-language tooltips"),
]
labels=[b[0] for b in blind]; dev=[b[1] for b in blind]; usr=[b[2] for b in blind]; fixes=[b[3] for b in blind]
y=np.arange(len(blind))[::-1]

fig,ax=plt.subplots(figsize=(12.5,7))
DEVC="#6a9bcc"; USRC="#d97757"
for yi,d,u in zip(y,dev,usr):
    ax.plot([u,d],[yi,yi],color="#ccc",lw=2,zorder=1)
    # gap arrow
    ar=FancyArrowPatch((u,yi),(d,yi),arrowstyle="-|>",mutation_scale=11,color="#b0b0b0",lw=0,zorder=2,shrinkA=6,shrinkB=6)
ax.scatter(dev,y,s=180,color=DEVC,zorder=3,edgecolor="white",lw=1.2,label="Developer's view: \"is it built?\"")
ax.scatter(usr,y,s=180,color=USRC,zorder=3,edgecolor="white",lw=1.2,label="User's view: \"can I get my job done?\"")
for yi,d,u in zip(y,dev,usr):
    ax.text(d+0.18,yi,str(d),va="center",ha="left",fontsize=8.5,color=DEVC,fontweight="bold")
    ax.text(u-0.18,yi,str(u),va="center",ha="right",fontsize=8.5,color=USRC,fontweight="bold")
    ax.text((d+u)/2,yi+0.16,f"gap {d-u}",va="bottom",ha="center",fontsize=7,color="#999",style="italic")
ax.set_yticks(y); ax.set_yticklabels(labels,fontsize=8.5)
ax.set_xlim(0,11.2); ax.set_xlabel("Perceived completeness  (0 = missing · 10 = done)",fontsize=10)
ax.set_ylim(-0.6,len(blind)-0.4)
# Right side: fixes
for yi,fx in zip(y,fixes):
    ax.text(10.4,yi,fx,va="center",ha="left",fontsize=6.6,color="#555",style="italic")
ax.axvline(10.2,color="#eee",lw=0.8)
set_frame(ax)
ax.legend(frameon=False,fontsize=8.5,loc="lower right",ncol=1,bbox_to_anchor=(1.0,-0.02))
fig.suptitle("The developer–user gap: six blindspots",x=0.5,y=0.99,ha="center",fontsize=15,fontweight="bold")
ax.set_title("\"Built\" and \"a user can actually use it\" are different questions — the gap is where users feel the tool is incomplete",
             loc="center",fontsize=9,color="#555",pad=10)
fig.tight_layout(rect=[0,0,1,0.95])
fig.savefig("dev_vs_user_gap.png",dpi=300,bbox_inches="tight")
plt.close(fig)
