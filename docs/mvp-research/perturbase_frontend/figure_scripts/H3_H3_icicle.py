"""
Standalone figure-generating script (Perturbase CD4+ T-cell Perturb-seq platform).

chart_id        : H3
source_image    : H3_icicle.png
chart_title     : Icicle
language        : Python
env_name        : python
packages        : matplotlib, numpy, pandas
input_artifacts : 506b62e3-4ad0-42a0-ac4d-b779a31f8121
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
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
    r,g,b=to_rgb(hexc); return (r+(1-r)*f,g+(1-g)*f,b+(1-b)*f)

COND=['Rest','Stim8hr','Stim48hr']
COND_COL={'Rest':'#4E79A7','Stim8hr':'#F28E2B','Stim48hr':'#59A14F'}
COND_LABEL={'Rest':'靜息 Rest','Stim8hr':'刺激 8hr','Stim48hr':'刺激 48hr'}
EFF_ORDER=['on-target KD','no on-target KD','putative off-target']
EFF_LABEL={'on-target KD':'有 on-target 敲低','no on-target KD':'無 on-target 敲低','putative off-target':'疑似 off-target'}

curated=pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/71b03570-3c70-4117-bd81-90917d27ab6b/v506b62e3_curated_targets.csv")
c=curated.copy()
c['gate_lab']=np.where(c.passes_gate,'通過門檻','未通過')

setup_style()
# ---------- H3 Icicle: 3 levels left->right: 全部 -> 條件 -> 效應類別 ----------
fig,ax=plt.subplots(figsize=(9.5,5.0))
grand=len(c)
# level x positions
xl={'root':(0.0,1.0),'cond':(1.15,2.15),'eff':(2.30,3.5)}
# root
ax.add_patch(mpl.patches.Rectangle((xl['root'][0],0),xl['root'][1]-xl['root'][0],grand,facecolor='#8a8f98',edgecolor='white',lw=1.5))
ax.text(np.mean(xl['root'])/1,grand/2,f"全部\nDE 統計\n{grand:,}",ha='center',va='center',fontsize=6.4,color='white',rotation=90 if False else 0)
# cond level (stacked)
y=grand
totals=c.culture_condition.value_counts().reindex(COND)
shade={'on-target KD':0.0,'no on-target KD':0.42,'putative off-target':0.72}
for cond in COND[::-1]:  # stack from bottom up; but keep order visually Rest top
    pass
# stack top->down in COND order
y0=grand
for cond in COND:
    h=totals[cond]; ytop=y0; ybot=y0-h
    ax.add_patch(mpl.patches.Rectangle((xl['cond'][0],ybot),xl['cond'][1]-xl['cond'][0],h,facecolor=COND_COL[cond],edgecolor='white',lw=1.5))
    ax.text(np.mean(xl['cond']),(ytop+ybot)/2,f"{COND_LABEL[cond]}\n{h:,}",ha='center',va='center',fontsize=6.0,color='white',fontweight='bold')
    # eff sublevel within this condition band
    sub=c[c.culture_condition==cond].ontarget_effect_category.value_counts().reindex(EFF_ORDER).fillna(0).astype(int)
    yy=ytop
    for eff in EFF_ORDER:
        hh=sub[eff]; a=yy; b=yy-hh
        sh=shade[eff]; col=lighten(COND_COL[cond],sh)
        ax.add_patch(mpl.patches.Rectangle((xl['eff'][0],b),xl['eff'][1]-xl['eff'][0],hh,facecolor=col,edgecolor='white',lw=1.0))
        if hh>grand*0.03:
            ax.text(np.mean(xl['eff']),(a+b)/2,f"{EFF_LABEL[eff]} · {hh:,}",ha='center',va='center',fontsize=5.2,color='white' if sh<0.45 else '#2b2b2b')
        yy=b
    y0=ybot
# level headers
for lab,key in [("第 1 層：全部",'root'),("第 2 層：培養條件",'cond'),("第 3 層：on-target 效應類別",'eff')]:
    ax.text(np.mean(xl[key]),grand*1.02,lab,ha='center',va='bottom',fontsize=6.4,color='#555')
ax.set_xlim(-0.05,3.6); ax.set_ylim(0,grand*1.08); ax.axis('off')
ax.set_title("階層冰柱圖：DE 統計列由全部 → 培養條件 → on-target 效應類別逐層拆分",fontsize=8,loc='left',pad=16)
fig.text(0.5,0.02,"矩形高度 ∝ DE 統計列數（n=33,983 列）；疑似 off-target 帶過小未標字",ha='center',fontsize=6)
fig.tight_layout(rect=[0,0.03,1,1])
fig.savefig("H3_icicle.png",dpi=300,bbox_inches='tight')