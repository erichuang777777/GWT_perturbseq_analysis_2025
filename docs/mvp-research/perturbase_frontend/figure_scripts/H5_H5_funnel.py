"""
Standalone figure-generating script (Perturbase CD4+ T-cell Perturb-seq platform).

chart_id        : H5
source_image    : H5_funnel.png
chart_title     : Funnel
language        : Python
env_name        : python
packages        : matplotlib, numpy, pandas
input_artifacts : 506b62e3-4ad0-42a0-ac4d-b779a31f8121
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.font_manager as fm
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

def lighten(hexc, f):
    from matplotlib.colors import to_rgb
    r, g, b = to_rgb(hexc)
    return (r+(1-r)*f, g+(1-g)*f, b+(1-b)*f)

COND = ['Rest', 'Stim8hr', 'Stim48hr']

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

setup_style()
labels = [s[0] for s in stages]; vals = [s[1] for s in stages]
N0 = vals[0]
fig, ax = plt.subplots(figsize=(8.4, 5.2))
yh = 0.82
grad = [lighten('#4E79A7', t) for t in np.linspace(0, 0.5, len(vals))]
for i, (lab, v) in enumerate(zip(labels, vals)):
    y = len(vals)-1-i
    w = v/N0
    ax.add_patch(mpl.patches.Rectangle((0.5-w/2, y-yh/2), w, yh, facecolor=grad[i], edgecolor='white', lw=1.2))
    ax.text(-0.02, y, lab, ha='right', va='center', fontsize=6.8, color='#333')
    pct = v/N0*100
    ax.text(0.5, y, f"{v:,}", ha='center', va='center', fontsize=7, color='white' if i < 3 else '#2b2b2b', fontweight='bold')
    ax.text(1.02, y, f"{pct:.1f}%", ha='left', va='center', fontsize=6.4, color='#666')
    if i > 0:
        step = vals[i]/vals[i-1]*100
        ax.text(1.02, y+0.5, f"↓ 保留 {step:.0f}%", ha='left', va='center', fontsize=5.4, color='#999')
ax.set_xlim(-0.42, 1.28); ax.set_ylim(-0.7, len(vals)-1+0.9); ax.axis('off')
ax.text(0.5, len(vals)-1+0.78, "每一格中央數字＝通過該關的列數；右側為佔全體 %", ha='center', va='bottom', fontsize=5.8, color='#777')
ax.set_title("篩選漏斗：DE 基因≥50 是最嚴苛的一關（16,998→2,131，僅保留 13%）", fontsize=8, loc='left', pad=20)
fig.text(0.5, 0.02, "門檻依序套用：細胞數≥200 → 顯著 on-target → 無 off-target → DE 基因≥50（n=33,983 起始列）", ha='center', fontsize=6)
fig.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig("H5_funnel.png", dpi=300, bbox_inches='tight')