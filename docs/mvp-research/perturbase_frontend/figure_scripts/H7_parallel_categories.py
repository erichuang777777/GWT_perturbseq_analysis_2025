"""
Standalone figure-generating script.

chart_id            : H7
source image        : H7_parallel_categories.png
chart title         : CD4+ T-Cell Target Perturbations: Four-Dimensional Classification by Culture, On-Target Effect, DE-Gene Grade, and Filter Status
language            : Python
conda env name      : python
input artifact vids : ['506b62e3-4ad0-42a0-ac4d-b779a31f8121']
referenced packages : matplotlib, numpy, os, pandas

Extracted verbatim from artifact lineage (host.lineage['d6306673-86f7-4afb-9758-0ad22cb656a0']).
Edit this single file to tweak the figure, then re-run in the 'python' environment.
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
c['gate_lab'] = np.where(c.passes_gate,'通過門檻','未通過')

d = c.copy()
d['cond'] = pd.Categorical(d.culture_condition, COND, ordered=True)
d['eff'] = pd.Categorical(d.ontarget_effect_category, EFF_ORDER, ordered=True)
DEG_ORDER = ['no effect','1 DE gene','2-10 DE genes','>10 DE genes']
d['deg'] = pd.Categorical(d.n_total_genes_category, DEG_ORDER, ordered=True)
d['gate'] = pd.Categorical(d.gate_lab, ['通過門檻','未通過'], ordered=True)
d['cond_c'] = d['cond']

dims = [('cond', COND, {k:COND_LABEL[k] for k in COND}),
        ('eff', EFF_ORDER, {k:EFF_LABEL[k] for k in EFF_ORDER}),
        ('deg', DEG_ORDER, {'no effect':'無效應','1 DE gene':'1 個 DE','2-10 DE genes':'2–10 DE','>10 DE genes':'>10 DE'}),
        ('gate', ['通過門檻','未通過'], {'通過門檻':'通過門檻','未通過':'未通過'})]
Ntot = len(d)

setup_style()
d['cond_c'] = d['cond']
fig, ax = plt.subplots(figsize=(9.5, 5.6))
xw = [i*3.0 for i in range(len(dims))]; barw = 0.5; gap = 0.012
cat_pos = {}
for di, (col, order, lab) in enumerate(dims):
    counts = d[col].value_counts().reindex(order).fillna(0).astype(int)
    y = 1.0
    for ci, cat in enumerate(order):
        h = counts[cat]/Ntot; y0 = y-h; y1 = y
        if col == 'cond': col_c = COND_COL[cat]
        elif col == 'gate': col_c = '#59A14F' if cat == '通過門檻' else '#BBBBBB'
        else: col_c = lighten('#666666', 0.15+0.2*ci)
        ax.add_patch(mpl.patches.Rectangle((xw[di]-barw/2, y0), barw, h-gap, facecolor=col_c, edgecolor='none'))
        cat_pos[(di, cat)] = [y0, y1, col_c]
        whitetxt = (col == 'cond') or (col == 'gate' and cat == '通過門檻')
        if h > 0.015:
            ax.text(xw[di], (y0+y1)/2, f"{lab[cat]}\n{counts[cat]:,}", ha='center', va='center', fontsize=5.4,
                    color='white' if whitetxt else '#2b2b2b')
        y = y0
    ax.text(xw[di], 1.03, {'cond':'培養條件','eff':'on-target 效應','deg':'DE 基因數分級','gate':'篩選門檻'}[col],
            ha='center', va='bottom', fontsize=6.6, color='#333', fontweight='bold')
cursor = {k: cat_pos[k][1] for k in cat_pos}
for di in range(len(dims)-1):
    colA, orderA, _ = dims[di]; colB, orderB, _ = dims[di+1]
    grp = d.groupby([colA, colB, 'cond_c'], observed=True).size().reset_index(name='n')
    grp[colA] = pd.Categorical(grp[colA], orderA, ordered=True); grp[colB] = pd.Categorical(grp[colB], orderB, ordered=True)
    grp['cond_c'] = pd.Categorical(grp['cond_c'], COND, ordered=True); grp = grp.sort_values([colA, colB, 'cond_c'])
    xA = xw[di]+barw/2; xB = xw[di+1]-barw/2
    for _, rr in grp.iterrows():
        if rr.n == 0: continue
        h = rr.n/Ntot
        yA1 = cursor[(di, rr[colA])]; yA0 = yA1-h; cursor[(di, rr[colA])] = yA0
        yB1 = cursor[(di+1, rr[colB])]; yB0 = yB1-h; cursor[(di+1, rr[colB])] = yB0
        verts = [(xA,yA1),((xA+xB)/2,yA1),((xA+xB)/2,yB1),(xB,yB1),(xB,yB0),((xA+xB)/2,yB0),((xA+xB)/2,yA0),(xA,yA0),(xA,yA1)]
        codes = [Path.MOVETO,Path.CURVE4,Path.CURVE4,Path.CURVE4,Path.LINETO,Path.CURVE4,Path.CURVE4,Path.CURVE4,Path.CLOSEPOLY]
        ax.add_patch(mpatches.PathPatch(Path(verts, codes), facecolor=COND_COL[rr['cond_c']], edgecolor='none', alpha=0.28))
ax.set_xlim(-1.0, xw[-1]+1.0); ax.set_ylim(-0.02, 1.09)
ax.set_xticks([]); ax.set_yticks([]); ax.axis('off')
ax.set_title("多數 DE 統計列僅 1–10 個 DE 基因；通過門檻的 2,131 列全為有 on-target 敲低且 >10 DE 基因", fontsize=7.2, loc='left', pad=14)
fig.text(0.5, 0.02, "每條帶＝一組類別組合的 DE 統計列，寬度 ∝ 列數，依培養條件著色（Rest/Stim8hr/Stim48hr）（n=33,983 列）", ha='center', fontsize=6)
fig.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig("H7_parallel_categories.png", dpi=300, bbox_inches='tight')
