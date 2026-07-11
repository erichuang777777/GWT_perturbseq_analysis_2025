"""
Standalone figure-generating script (Perturbase CD4+ T-cell Perturb-seq platform).

chart_id        : C3
source_image    : C3_funnel.png
chart_title     : QC funnel
language        : Python
env_name        : python
packages        : matplotlib, numpy, pandas
input_artifacts : 506b62e3-4ad0-42a0-ac4d-b779a31f8121
"""

# skill:figure-style kernel.py (auto-injected on skill load)
META_GREY = "#888888"


def apply_figure_style(*, frame="open", font=None, sizes=(8, 7, 6), grid=False):
    import matplotlib as mpl
    if frame not in ("open", "boxed", "none"):
        raise ValueError(f"frame must be 'open'|'boxed'|'none', got {frame!r}")
    try:
        import os, sys, glob, matplotlib.font_manager as fm
        fdir = os.path.join(os.environ.get("CONDA_PREFIX") or sys.prefix, "fonts")
        if os.path.isdir(fdir):
            known = {f.fname for f in fm.fontManager.ttflist}
            for f in glob.glob(os.path.join(fdir, "*.ttf")):
                if f not in known:
                    fm.fontManager.addfont(f)
    except Exception:
        pass
    base, secondary, tick = sizes
    boxed = (frame == "boxed")
    rc = {
        "font.family": "sans-serif",
        "font.size": base,
        "axes.labelsize": base,
        "axes.titlesize": base,
        "legend.fontsize": secondary,
        "xtick.labelsize": tick,
        "ytick.labelsize": tick,
        "axes.linewidth": 0.6,
        "xtick.direction": "out", "ytick.direction": "out",
        "xtick.major.size": 3, "ytick.major.size": 3,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "axes.spines.top": boxed, "axes.spines.right": boxed,
        "axes.spines.left": frame != "none", "axes.spines.bottom": frame != "none",
        "axes.grid": bool(grid),
        "legend.frameon": False,
        "figure.dpi": 200,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.titleweight": "normal",
        "axes.titlelocation": "left",
        "axes.labelweight": "normal",
        "lines.linewidth": 1.2,
        "patch.linewidth": 0.6,
        "pdf.fonttype": 42, "ps.fonttype": 42,
    }
    if font:
        rc["font.sans-serif"] = [font, "DejaVu Sans"]
    mpl.rcParams.update(rc)


import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

figs = apply_figure_style()

curated = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/71b03570-3c70-4117-bd81-90917d27ab6b/v506b62e3_curated_targets.csv")

d = curated
s0 = len(d)
s1 = (d['n_cells_target'] >= 200).sum()
m1 = d['n_cells_target'] >= 200
s2 = (m1 & d['ontarget_significant']).sum()
m2 = m1 & d['ontarget_significant']
s3 = (m2 & ~d['offtarget_flag']).sum()
m3 = m2 & ~d['offtarget_flag']
s4 = (m3 & (d['n_total_de_genes'] >= 50)).sum()
print("funnel:", s0, s1, s2, s3, s4, "| passes_gate:", d['passes_gate'].sum())
stages = [('All target×condition rows', s0),
          ('≥200 cells per target', s1),
          ('On-target significant', s2),
          ('No off-target flag', s3),
          ('≥50 DE genes → gate pass', s4)]
labels = [s[0] for s in stages]
vals3 = [s[1] for s in stages]

from matplotlib.patches import Polygon
fig_c3, ax = plt.subplots(figsize=(6.0, 4.2))
n = len(vals3)
ys = np.arange(n)[::-1]  # top stage at top
maxv = vals3[0]
# color: single-hue sequential deepening toward the pass; last stage = focal (brick)
seq = plt.get_cmap('Blues')
bar_cols = [seq(0.35 + 0.13 * i) for i in range(n - 1)] + ['#B5462E']
for i, (y, v) in enumerate(zip(ys, vals3)):
    w = v / maxv
    ax.barh(y, w, height=0.62, left=(1 - w) / 2, color=bar_cols[i], zorder=3)
    # stage label above-left, count inside/right
    ax.text(0.5, y + 0.42, labels[i], ha='center', va='bottom', fontsize=7)
    ax.text(0.5, y, f"{v:,}", ha='center', va='center', fontsize=7.5,
            color='white' if i >= 1 else '0.15', fontweight='bold')
    # pct retained from previous
    if i > 0:
        pct = v / vals3[i - 1] * 100
        ax.text((1 - w) / 2 - 0.015, y, f"{pct:.0f}%", ha='right', va='center', fontsize=6, color='0.45')
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.6, n - 0.35)
ax.axis('off')
ax.set_title("Curation gate: 33,983 rows → 2,131 (6.3%) high-confidence target hits", loc='left', fontsize=8)
fig_c3.text(0.5, 0.02, "% = fraction retained from the stage above", ha='center', fontsize=6, color='0.45')
fig_c3.tight_layout()
fig_c3.savefig("C3_funnel.png", dpi=300, bbox_inches='tight')