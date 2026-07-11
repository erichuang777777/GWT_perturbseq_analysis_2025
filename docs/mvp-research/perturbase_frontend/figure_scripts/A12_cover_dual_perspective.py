"""
chart_id:        A12
source image:    cover_dual_perspective.png
chart title:     One Dataset, Two Opposing First Impressions
language:        Python
env name:        python
input-artifact version_ids (1):
  - daeb84c7-c8df-4149-9464-191b1a6ba457  (target_master_table.csv)
packages referenced: matplotlib, numpy, pandas
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

# skill:figure-style kernel.py (auto-injected on skill load) - apply_figure_style and set_frame
def apply_figure_style(sizes=(9, 8, 7)):
    plt.rcParams.update({
        'font.size': sizes[1],
        'axes.titlesize': sizes[0],
        'axes.labelsize': sizes[1],
        'xtick.labelsize': sizes[2],
        'ytick.labelsize': sizes[2],
        'axes.spines.top': False,
        'axes.spines.right': False,
    })

def set_frame(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

apply_figure_style(sizes=(9, 8, 7))
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False

m = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/46a1c017-4a49-46dc-8098-512c17286263/vdaeb84c7_target_master_table.csv")
ctx = m[m["is_ctx_specific"]].copy()
ctx["x_appeal"] = np.log10(ctx["ctx_specific_de"].clip(lower=1) + 1)
ctx["y_risk"] = ctx["n_avoid_flags"].astype(float)
rng = np.random.default_rng(7)
ctx["y_jit"] = ctx["y_risk"] + rng.uniform(-0.28, 0.28, len(ctx))

fig, ax = plt.subplots(figsize=(11, 7.6))
ax.axhspan(1.5, 3.5, xmin=0.5, xmax=1.0, color="#d97757", alpha=0.08, zorder=0)
ax.text(2.52, 3.42, "Conflict zone: what the researcher wants most, the clinician fears most",
        ha="left", va="top", fontsize=9.5, color="#b5482c", fontweight="bold", style="italic")

RC = {0: "#788c5d", 1: "#e8a33d", 2: "#d97757", 3: "#c0504d"}
ax.scatter(ctx["x_appeal"], ctx["y_jit"], s=34,
           c=[RC[int(v)] for v in ctx["y_risk"]],
           alpha=0.55, edgecolor="white", lw=0.4, zorder=3)

picks = {"CD3E": (22, 15), "PLCG1": (30, -14), "VAV1": (-26, -20), "STAT3": (-34, -18), "BCL10": (-30, 18)}
pd_idx = ctx.set_index("gene")
for g, (dx, dy) in picks.items():
    r = pd_idx.loc[g]
    x, y = r["x_appeal"], r["y_jit"]
    ax.scatter([x], [y], s=115, facecolor=RC[int(r["n_avoid_flags"])], edgecolor="#222", lw=1.3, zorder=5)
    ax.annotate(g, (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=9.5, fontweight="bold",
                style="italic", ha="center", zorder=6,
                arrowprops=dict(arrowstyle="-", color="#888", lw=0.6))

ax.set_xlabel("Researcher's lens  →  context-specific effect (downstream DE breadth on activation, log)", fontsize=10)
ax.set_ylabel("Clinician's lens  →  number of risk flags\n(pleiotropy · genetic constraint · dosage sensitivity)", fontsize=10)
ax.set_yticks([0, 1, 2, 3])
ax.set_yticklabels(["clear\n0", "caution\n1", "high risk\n2", "avoid\n3"], fontsize=7.5)
ax.set_ylim(-0.6, 3.7)
ax.margins(x=0.07)
set_frame(ax)

fig.suptitle("One dataset, two opposing first impressions", x=0.5, y=0.99, ha="center", fontsize=16, fontweight="bold")
ax.set_title("CD4⁺ T-cell Perturb-seq target-discovery platform · researchers want novel mechanism, clinicians want safety — the most interesting targets are often the most dangerous",
             loc="center", fontsize=8.3, color="#555", pad=12)

leg = [Line2D([0], [0], marker="o", ls="", mfc=RC[k], mec="white", ms=9, label=v)
       for k, v in {0: "clear (safe to explore)", 1: "caution", 2: "high risk", 3: "avoid (clinically)"}.items()]
ax.legend(handles=leg, frameon=False, fontsize=8, loc="upper left", title="Clinical risk tier", title_fontsize=8.5)

fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig("cover_dual_perspective.png", dpi=300, bbox_inches="tight")
plt.close(fig)
