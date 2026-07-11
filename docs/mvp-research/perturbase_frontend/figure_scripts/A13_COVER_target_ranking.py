"""
chart_id:        A13
source image:    COVER_target_ranking.png
chart title:     Top CD4+ T-cell Perturbation Targets by DE Gene Count
language:        Python
env name:        python
input-artifact version_ids (0):
  (none)
packages referenced: matplotlib, numpy, pandas
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

# CJK-free font
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

de = pd.read_csv("/tmp/data/DE_stats.suppl_table.csv")

def to_bool(s):
    return s.astype(str).str.lower().isin(["true", "1", "yes"])

de["_sig"] = to_bool(de["ontarget_significant"])
de["_off"] = to_bool(de["offtarget_flag"])
de["_pass"] = (de["n_cells_target"] >= 200) & de["_sig"] & ~de["_off"] & (de["n_total_de_genes"] >= 50)
de["logDE"] = np.log10(de["n_total_de_genes"] + 1)

broad_effect = {"TADA2B", "SGF29", "MED12", "CCNC", "SUPT20H", "TADA1", "DENR", "SENP5", "UBXN1", "PMVK"}

top_dedup = (de[de["_pass"]].groupby("target_contrast_gene_name")["n_total_de_genes"].max().nlargest(12).iloc[::-1])

fig, ax = plt.subplots(figsize=(10, 7.2))
t = top_dedup
cols = ["#d62728" if g in broad_effect else "#08519c" for g in t.index]
ax.hlines(range(len(t)), 0, t.values, color="#d0d0d0", lw=1.5, zorder=1)
ax.scatter(t.values, range(len(t)), c=cols, s=180, zorder=3, edgecolors="white", linewidths=1.5)
for i, (g, v) in enumerate(zip(t.index, t.values)):
    ax.text(v + 80, i, f"{int(v):,}", va="center", fontsize=8, color="#333")
ax.set_yticks(range(len(t)))
ax.set_yticklabels(t.index, fontsize=10)
ax.set_xlabel("Downstream DE gene count (effect breadth, max across conditions)", fontsize=11)
fig.suptitle("CD4 T-cell Perturb-seq target ranking", fontsize=15, fontweight=600, x=0.09, ha="left", y=0.98)
ax.set_title("Top 12 targets \u00b7 blue = immune candidate, red = broad-effect (pan-effect, needs isolation)",
             fontsize=9, color="#666", loc="left", pad=10)
ax.legend(handles=[Patch(color="#08519c", label="Immune candidate (TCR signalling)"), Patch(color="#d62728", label="Broad-effect (transcription/chromatin machinery)")],
          loc="lower right", frameon=False, fontsize=9)
ax.set_xlim(0, t.values.max() * 1.15)
fig.subplots_adjust(top=0.90)
fig.savefig("COVER_target_ranking.png", dpi=300, bbox_inches="tight")
plt.close(fig)
