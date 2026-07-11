"""
chart_id:        A10
source image:    evidence_coverage_fix.png
chart title:     Evidence Coverage Improvement: gnomAD Integration for CD4+ T-cell Targets
language:        Python
env name:        python
input-artifact version_ids (1):
  - daeb84c7-c8df-4149-9464-191b1a6ba457  (target_master_table.csv)
packages referenced: matplotlib, numpy, pandas, warnings
"""

import warnings; warnings.filterwarnings("ignore")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd

# CJK-free font
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False

m = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/46a1c017-4a49-46dc-8098-512c17286263/vdaeb84c7_target_master_table.csv")
n = len(m)

fig, (axL, axR) = plt.subplots(1, 2, figsize=(12.5, 5), gridspec_kw={"width_ratios": [1, 1.05], "wspace": 0.3})

axes_names = ["gnomAD\nLOEUF", "gnomAD\npLI", "Delivery modality\n(ADC)", "Polarity\n(endogenous)", "Kinetics type\n(endogenous)"]
before = [71, 71, 345, 1235, 1225]
after = [int(m['loeuf'].notna().sum()), int(m['pli'].notna().sum()),
         int((m['delivery_modality'] != '待新模態 (無已知遞送方式)').sum()), 1235, 1225]
x = np.arange(len(axes_names))
w = 0.38
axL.bar(x - w/2, [b/n*100 for b in before], w, label="Before integration", color="#c9c9c9", zorder=3)
axL.bar(x + w/2, [a/n*100 for a in after], w, label="After integration", color="#788c5d", zorder=3)
for xi, (b, a) in enumerate(zip(before, after)):
    axL.text(xi - w/2, b/n*100 + 1.5, f"{b/n*100:.0f}%", ha="center", fontsize=7, color="#666")
    axL.text(xi + w/2, a/n*100 + 1.5, f"{a/n*100:.0f}%", ha="center", fontsize=7, fontweight="bold")
axL.set_xticks(x)
axL.set_xticklabels(axes_names, fontsize=8)
axL.set_ylabel("Coverage of 1,235 targets (%)")
axL.set_ylim(0, 108)
axL.set_title("Evidence coverage completion: gnomAD 6% \u2192 97% (bulk download)", loc="left", fontsize=10.5)
axL.legend(frameon=False, fontsize=8, loc="center right")
axL.axhline(100, color="#ccc", lw=0.6, ls="--", zorder=1)

tiers = ["clear", "caution", "high_risk", "avoid"]
b_avoid = {"clear": 1111, "caution": 97, "high_risk": 12, "avoid": 15}
a_avoid = m["avoid_tier"].value_counts().to_dict()
TC = {"clear": "#788c5d", "caution": "#e8a33d", "high_risk": "#d97757", "avoid": "#c0504d"}
xa = np.arange(len(tiers))
axR.bar(xa - w/2, [b_avoid[t] for t in tiers], w, label="Before (6%)", color="#c9c9c9", zorder=3)
axR.bar(xa + w/2, [a_avoid.get(t, 0) for t in tiers], w, label="After (97%)", color=[TC[t] for t in tiers], zorder=3)
for xi, t in enumerate(tiers):
    axR.text(xi - w/2, b_avoid[t] + 8, str(b_avoid[t]), ha="center", fontsize=7, color="#666")
    axR.text(xi + w/2, a_avoid.get(t, 0) + 8, str(a_avoid.get(t, 0)), ha="center", fontsize=7, fontweight="bold")
axR.set_xticks(xa)
axR.set_xticklabels(["clear\n(0 flags)", "caution\n(1 flag)", "high_risk\n(2 flags)", "avoid\n(3 flags)"], fontsize=8)
axR.set_ylabel("Number of targets")
axR.set_title("Coverage gain reveals hidden risk: avoid tier 27 \u2192 387", loc="left", fontsize=10.5)
axR.legend(frameon=False, fontsize=8)
fig.suptitle("External evidence coverage completion \u2014 one bulk gnomAD download resolves the per-gene crawl ceiling", x=0.02, ha="left", fontsize=12, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig("evidence_coverage_fix.png", dpi=300, bbox_inches="tight")
plt.close(fig)
