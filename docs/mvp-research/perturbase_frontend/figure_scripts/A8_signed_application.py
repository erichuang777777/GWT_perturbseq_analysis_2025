"""
chart_id:        A8
source image:    signed_application.png
chart title:     Phenotype-signed ranking and pathway validation of CD4+ T-cell perturbation targets
language:        Python
env name:        python
input-artifact version_ids (7):
  - be0150d9-d316-4f49-bfd7-b2fe82d0f999  (lincs_concordance.csv)
  - 4348ff01-932f-4b2f-9488-a82a8a3cbd2a  (signed_ranking_v2.csv)
  - 128441e4-9459-40b9-8fd9-7b8ebbae04cb  (downstream_enrichment_v2.csv)
  - 33e15964-b453-4950-b624-14ea5a9a545c  (panel_a.png)
  - d2da1659-248b-4e64-8362-f99b3821c8a4  (panel_b.png)
  - 2b989956-52d4-4bf6-8ef0-c81a9b19230a  (panel_c.png)
  - 25172ec2-eac3-41d1-9026-f7d6acb9a4a2  (outline.json)
packages referenced: json, matplotlib, numpy, pandas
"""

import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

apply_figure_style()

ORANGE = "#d97757"
BLUE = "#6a9bcc"
GREEN = "#788c5d"

sp = json.load(open("handoff/signed_phase1.json"))
cnt = [x for x in sp if x["name"] == "下游模組解析"][0]["out"]["per_flagship_downstream_counts"]
rk2 = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/87c1a765-07f4-47c8-a21c-09ee75c4e88c/v4348ff01_signed_ranking_v2.csv", comment="#")
lc = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/04636fa0-0fc8-4b36-861d-78c82bd84245/vbe0150d9_lincs_concordance.csv")
dicol = [c for c in rk2.columns if 'directionality_index' in c][0]
s = rk2[rk2.in_gate_shortlist == True].sort_values(dicol).reset_index(drop=True)
FL = ["CD3E", "PLCG1", "VAV1", "STAT3", "BCL10"]

fig = plt.figure(figsize=(15, 5.2))
gs = GridSpec(1, 3, figure=fig, wspace=0.34)

axA = fig.add_subplot(gs[0, 0])
axA.scatter(range(len(s)), s[dicol], s=6, c=[ORANGE if v > 0 else BLUE for v in s[dicol]], alpha=.6)
axA.axhline(0, color="#888", lw=.8)
offs = {"CD3E": (45, .17), "PLCG1": (-100, .15), "VAV1": (40, -.04), "STAT3": (-150, -.20), "BCL10": (90, -.30)}
for g in FL:
    idx = s.index[s.target_gene == g]
    if len(idx):
        i = int(idx[0])
        yv = s[dicol].iloc[i]
        dx, dy = offs[g]
        axA.annotate(g, (i, yv), (i + dx, yv + dy), fontsize=8, fontweight="bold",
                     arrowprops=dict(arrowstyle="-", lw=.5, color="#555"))
axA.set_title("A. Phenotype-signed axis (1,235 shortlist)\nprimary = directionality index (scale-free)", fontsize=10.5, loc="left")
axA.set_xlabel("targets (ranked by directionality index)")
axA.set_ylabel("(n_up − n_down)/(n_up + n_down)")

axB = fig.add_subplot(gs[0, 1])
y = np.arange(len(FL))
axB.barh(y, [cnt[g]["up"] for g in FL], color=ORANGE, label="up")
axB.barh(y, [-cnt[g]["down"] for g in FL], color=BLUE, label="down")
axB.set_yticks(y)
axB.set_yticklabels(FL)
axB.axvline(0, color="#888", lw=.8)
axB.set_title("B. Flagship downstream genes (gene-level)\nVAV1→T-cell diff.; STAT3→interleukin (bg-corrected)", fontsize=10.5, loc="left")
axB.set_xlabel("downstream genes (unique)")
axB.legend(fontsize=8, frameon=False, loc="lower right")

axC = fig.add_subplot(gs[0, 2])
tcol = [c for c in lc.columns if 'target' in c.lower()][0]
acol = [c for c in lc.columns if 'agree' in c.lower()][0]
axC.bar(lc[tcol], lc[acol], color=GREEN)
axC.axhline(0.5, color=ORANGE, ls="--", lw=1.2, label="0.5 = chance")
axC.set_ylim(0, 1)
axC.set_ylabel("sign-agreement fraction")
axC.set_title("C. LINCS concordance (demo: non-T-cell, n=4)\nPMVK* weak-but-signif. (ρ=0.22, p=3e-5)", fontsize=10.5, loc="left")
for i, (g, v) in enumerate(zip(lc[tcol], lc[acol])):
    axC.text(i, v + .02, f"{v:.2f}" + ("*" if g == "PMVK" else ""), ha="center", fontsize=8)
axC.legend(fontsize=8, frameon=False)

fig.suptitle("GB10 signed DE — phenotype-signed ranking (scale-free), downstream mechanism (bg-corrected), external concordance", fontsize=12, fontweight="bold", y=1.02)
fig.savefig("signed_application.png", dpi=300, bbox_inches="tight")
plt.close(fig)
