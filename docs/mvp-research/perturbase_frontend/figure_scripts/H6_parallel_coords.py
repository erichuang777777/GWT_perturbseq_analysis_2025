"""
Standalone figure-generating script.

chart_id            : H6
source image        : H6_parallel_coords.png
chart title         : Parallel-coordinates plot of CD4+ T-cell activation metrics across stimulation conditions
language            : Python
conda env name      : python
input artifact vids : ['506b62e3-4ad0-42a0-ac4d-b779a31f8121']
referenced packages : matplotlib, numpy, os, pandas

Extracted verbatim from artifact lineage (host.lineage['5255eaf2-450a-4732-a34b-3db1c3d9ab6c']).
Edit this single file to tweak the figure, then re-run in the 'python' environment.
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
    plt.rcParams['font.family']='sans-serif'
    plt.rcParams['font.sans-serif']=['PingFang TC','DejaVu Sans']
    plt.rcParams['axes.unicode_minus']=False

def lighten(hexc, f):
    from matplotlib.colors import to_rgb
    r,g,b=to_rgb(hexc); return (r+(1-r)*f, g+(1-g)*f, b+(1-b)*f)

COND = ['Rest','Stim8hr','Stim48hr']
COND_COL = {'Rest':'#4E79A7','Stim8hr':'#F28E2B','Stim48hr':'#59A14F'}
COND_LABEL = {'Rest':'靜息 Rest','Stim8hr':'刺激 8hr','Stim48hr':'刺激 48hr'}
EFF_ORDER = ['on-target KD','no on-target KD','putative off-target']
EFF_LABEL = {'on-target KD':'有 on-target 敲低','no on-target KD':'無 on-target 敲低','putative off-target':'疑似 off-target'}

curated = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/71b03570-3c70-4117-bd81-90917d27ab6b/v506b62e3_curated_targets.csv")
c = curated.copy()
c['gate_lab'] = np.where(c.passes_gate, '通過門檻', '未通過')

setup_style()
axes_feat = [('n_cells_target', '細胞數'), ('abs_eff', '|on-target 效應量|'), ('n_total_de_genes', 'DE 基因數')]
df6 = c.copy()
df6['abs_eff'] = df6.ontarget_effect_size.abs()
P = {f: df6[f].rank(pct=True).values for f, _ in axes_feat}
Pdf = pd.DataFrame(P)
Pdf['cond'] = df6.culture_condition.values
K = len(axes_feat)
xpos = np.arange(K)
fig, ax = plt.subplots(figsize=(8.2, 5.2))
rng = np.random.default_rng(7)
for cond in COND:
    idx = np.where(Pdf.cond.values == cond)[0]
    samp = rng.choice(idx, size=min(500, len(idx)), replace=False)
    Y = Pdf.iloc[samp][[f for f, _ in axes_feat]].values
    for row in Y:
        ax.plot(xpos, row, color=COND_COL[cond], alpha=0.025, lw=0.5)
for cond in COND:
    med = [np.median(Pdf[Pdf.cond == cond][f]) for f, _ in axes_feat]
    ax.plot(xpos, med, color=COND_COL[cond], lw=2.8, marker='o', ms=6, zorder=5, markeredgecolor='white', markeredgewidth=0.9)
for j, (f, lab) in enumerate(axes_feat):
    ax.axvline(j, color='#ccc', lw=0.8, zorder=0)
    for q in [0.05, 0.5, 0.95]:
        rv = df6[f].quantile(q)
        txt = f"{rv:,.0f}" if rv >= 10 else f"{rv:.1f}"
        ax.text(j - 0.03, q, txt, ha='right', va='center', fontsize=5.0, color='#999')
    ax.text(j, 1.045, lab, ha='center', va='bottom', fontsize=7, color='#333')
for k, cond in enumerate(COND):
    yy = 0.22 - k * 0.06
    ax.plot([1.55, 1.72], [yy, yy], color=COND_COL[cond], lw=2.8)
    ax.text(1.76, yy, COND_LABEL[cond] + " 中位軌跡", color=COND_COL[cond], fontsize=6.4, va='center')
ax.set_xlim(-0.5, K - 1 + 0.05)
ax.set_ylim(-0.03, 1.08)
ax.set_yticks([0, .25, .5, .75, 1])
ax.set_yticklabels(['0', '25', '50', '75', '100'], fontsize=5.5)
ax.set_ylabel('特徵百分位 (percentile)', fontsize=6.6)
for s in ['top', 'right', 'bottom']:
    ax.spines[s].set_visible(False)
ax.set_xticks([])
ax.set_title("三條件下標的特徵分布幾乎重疊：培養條件不改變效應量與 DE 廣度", fontsize=8, loc='left', pad=18)
fig.text(0.5, 0.02, "每條細線＝一列 DE 統計（每條件抽樣 500 列，α=0.025）；粗線＝該條件中位軌跡；軸為各特徵百分位，旁註 5/50/95 百分位真值（三軸皆 n=33,983 列，無缺失）", ha='center', fontsize=5.2)
fig.tight_layout(rect=[0, 0.035, 1, 1])
fig.savefig("H6_parallel_coords.png", dpi=300, bbox_inches='tight')
