"""
chart_id:        A4
source image:    kinetics_and_avoid.png
chart title:     Kinetic archetypes and clinical avoid-list for CD4+ T-cell targets
language:        Python
env name:        python
input-artifact version_ids (1):
  - daeb84c7-c8df-4149-9464-191b1a6ba457  (target_master_table.csv)
packages referenced: matplotlib, numpy, pandas
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

m = pd.read_csv('/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/46a1c017-4a49-46dc-8098-512c17286263/vdaeb84c7_target_master_table.csv')

fig, (axL, axR) = plt.subplots(1, 2, figsize=(13, 5.6), gridspec_kw={"width_ratios": [1.15, 1], "wspace": 0.32})
kin_order = ["early_transient", "late_sustained", "stim_switch", "other"]
KCOL = {"early_transient": "#d97757", "late_sustained": "#788c5d", "stim_switch": "#6a9bcc", "other": "#bdbdbd"}
KLAB = {"early_transient": "early transient", "late_sustained": "late sustained", "stim_switch": "stim switch", "other": "other"}
xk = [0, 1, 2]
for k in kin_order:
    sub = m[m["kinetic_archetype"] == k]
    if len(sub) == 0:
        continue
    norm = sub[["de_Rest", "de_Stim8hr", "de_Stim48hr"]].div(sub[["de_Rest", "de_Stim8hr", "de_Stim48hr"]].max(axis=1), axis=0)
    axL.plot(xk, norm.median().values, "-o", color=KCOL[k], lw=2.2, ms=7, label=f"{KLAB[k]} (n={len(sub)})")
axL.set_xticks(xk)
axL.set_xticklabels(["Rest", "Stim 8hr", "Stim 48hr"])
axL.set_ylabel("Normalised DE breadth (to each target's peak)")
axL.set_title("Kinetic archetypes: at which activation stage a target acts", loc="left", fontsize=11)
axL.legend(frameon=False, fontsize=7.5, loc="lower center")

avoid = m[m["n_avoid_flags"] >= 2].copy().sort_values("n_avoid_flags", ascending=True).tail(15)
ypos = np.arange(len(avoid))
hb = avoid["avoid_flags"].str.contains("Pleiotropy").astype(int)
hl = avoid["avoid_flags"].str.contains("constraint").astype(int)
hp = avoid["avoid_flags"].str.contains("Dosage").astype(int)
axR.barh(ypos, hb, color="#c0504d", label="Pleiotropy (breadth top 10%)", zorder=3)
axR.barh(ypos, hl, left=hb, color="#e8a33d", label="High constraint (LOEUF<0.35)", zorder=3)
axR.barh(ypos, hp, left=hb + hl, color="#8064a2", label="Dosage-sensitive (pLI≥0.9)", zorder=3)
axR.set_yticks(ypos)
axR.set_yticklabels(avoid["gene"], fontsize=8, style="italic")
axR.set_xlabel("Number of risk flags")
axR.set_xticks([0, 1, 2, 3])
axR.set_title("Clinical avoid-list: high pleiotropy × essentiality risk", loc="left", fontsize=11)
axR.legend(frameon=False, fontsize=7.5, loc="lower right")
fig.suptitle("Kinetic archetypes (idea 3) + clinical avoid-list (idea 4) — both GB10-free", x=0.02, ha="left", fontsize=12.5, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig("kinetics_and_avoid.png", dpi=300, bbox_inches="tight")
plt.close(fig)
