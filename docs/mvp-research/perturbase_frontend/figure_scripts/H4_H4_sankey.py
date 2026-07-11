"""
Standalone figure-generating script (Perturbase CD4+ T-cell Perturb-seq platform).

chart_id        : H4
source_image    : H4_sankey.png
chart_title     : Sequential QC-Filtering Funnel for CD4+ T-Cell Target Discovery
language        : Python
env_name        : python
packages        : matplotlib, numpy, pandas
input_artifacts : 506b62e3-4ad0-42a0-ac4d-b779a31f8121
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np
import os

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


paths = [
 "/System/Library/AssetsV2/com_apple_MobileAsset_Font7/3419f2a427639ad8c8e139149a287865a90fa17e.asset/AssetData/PingFang.ttc",
 "/System/Library/Fonts/STHeiti Medium.ttc",
 "/System/Library/Fonts/Hiragino Sans GB.ttc",
]
for p in paths:
    if os.path.exists(p):
        try: fm.fontManager.addfont(p)
        except Exception as e: print("err", p, e)


def setup_style():
    apply_figure_style()
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['PingFang TC', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False


curated = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/71b03570-3c70-4117-bd81-90917d27ab6b/v506b62e3_curated_targets.csv")
c = curated.copy()
c['gate_lab'] = np.where(c.passes_gate, '通過門檻', '未通過')

m1 = c.n_cells_target >= 200
m2 = m1 & c.ontarget_significant
m3 = m2 & (~c.offtarget_flag)
m4 = m3 & (c.n_total_de_genes >= 50)
stages = [("全部 DE 統計列", len(c)),
          ("細胞數 ≥200", int(m1.sum())),
          ("顯著 on-target", int(m2.sum())),
          ("無 off-target", int(m3.sum())),
          ("DE 基因 ≥50", int(m4.sum()))]
vals = [v for _, v in stages]
drops = [vals[i] - vals[i+1] for i in range(len(vals)-1)]
print(stages, drops)

setup_style()

fig, ax = plt.subplots(figsize=(9.5, 5.2))
N0 = vals[0]; x_gap = 1.0; band_w = 0.55
xs = [i * (band_w + x_gap) for i in range(len(vals))]
main_col = '#4E79A7'; drop_col = '#B0B7BF'
ytop = 1.0  # normalized to N0
def frac(v): return v / N0
# draw stage bars (kept)
for i, (x, (lab, v)) in enumerate(zip(xs, stages)):
    h = frac(v)
    ax.add_patch(mpl.patches.Rectangle((x, ytop - h), band_w, h, facecolor=main_col, edgecolor='white', lw=1))
    ax.text(x + band_w / 2, ytop + 0.03, f"{lab}", ha='center', va='bottom', fontsize=6.2, color='#333')
    ax.text(x + band_w / 2, ytop + 0.075, f"{v:,}", ha='center', va='bottom', fontsize=6.4, color=main_col, fontweight='bold')
# flow ribbons between kept portions + drop ribbons peeling down
def ribbon(x0, x1, yA0, yA1, yB0, yB1, color, alpha):
    verts = [(x0, yA0), ((x0+x1)/2, yA0), ((x0+x1)/2, yB0), (x1, yB0),
             (x1, yB1), ((x0+x1)/2, yB1), ((x0+x1)/2, yA1), (x0, yA1), (x0, yA0)]
    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]
    ax.add_patch(mpatches.PathPatch(Path(verts, codes), facecolor=color, edgecolor='none', alpha=alpha))
for i in range(len(vals) - 1):
    xA = xs[i] + band_w; xB = xs[i+1]
    keptB = frac(vals[i+1])
    # kept ribbon: aligns to top
    ribbon(xA, xB, ytop, ytop - keptB, ytop, ytop - keptB, main_col, 0.35)
    # drop ribbon peels off bottom of A down to a small sink
    d = frac(drops[i])
    ax.add_patch(mpatches.PathPatch(Path(
        [(xA, ytop - keptB), ((xA+xB)/2, ytop - keptB), ((xA+xB)/2, ytop - keptB - d), (xB, ytop - keptB - d),
         (xB, ytop - keptB - d - 0.0), ((xA+xB)/2, ytop - keptB - d), ((xA+xB)/2, ytop - frac(vals[i])), (xA, ytop - frac(vals[i])), (xA, ytop - keptB)],
        [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]),
        facecolor=drop_col, edgecolor='none', alpha=0.55))
    ax.text((xA+xB)/2, ytop - keptB - d/2 - 0.01, f"−{drops[i]:,}", ha='center', va='center', fontsize=5.2, color='#555')
ax.set_xlim(-0.1, xs[-1] + band_w + 0.1); ax.set_ylim(-0.02, ytop + 0.16); ax.axis('off')
ax.set_title("四道門檻把 33,983 列 DE 統計逐步篩到 2,131 列可用標的（保留 6.3%）", fontsize=8, loc='left', pad=10)
fig.text(0.5, 0.02, "藍色帶＝通過該關並延續的列；灰色帶＝該關淘汰的列。門檻：細胞數≥200 & 顯著 on-target & 無 off-target & DE 基因≥50", ha='center', fontsize=5.6)
fig.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig("H4_sankey.png", dpi=300, bbox_inches='tight')