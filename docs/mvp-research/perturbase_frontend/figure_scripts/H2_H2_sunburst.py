"""
Standalone figure-generating script (Perturbase CD4+ T-cell Perturb-seq platform).

chart_id        : H2
source_image    : H2_sunburst.png
chart_title     : Sunburst
language        : Python
env_name        : python
packages        : matplotlib, numpy, pandas
input_artifacts : 506b62e3-4ad0-42a0-ac4d-b779a31f8121
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
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

COND=['Rest','Stim8hr','Stim48hr']
COND_COL={'Rest':'#4E79A7','Stim8hr':'#F28E2B','Stim48hr':'#59A14F'}
COND_LABEL={'Rest':'靜息 Rest','Stim8hr':'刺激 8hr','Stim48hr':'刺激 48hr'}
EFF_ORDER=['on-target KD','no on-target KD','putative off-target']
EFF_LABEL={'on-target KD':'有 on-target 敲低','no on-target KD':'無 on-target 敲低','putative off-target':'疑似 off-target'}

curated=pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/71b03570-3c70-4117-bd81-90917d27ab6b/v506b62e3_curated_targets.csv")
c=curated.copy()
c['gate_lab']=np.where(c.passes_gate,'通過門檻','未通過')

setup_style()
# ---------- H2 Sunburst: condition (inner ring) -> effect category (outer ring) ----------
from matplotlib.patches import Wedge
hier_full=(c.groupby(['culture_condition','ontarget_effect_category']).size().rename('n').reset_index())
hier_full['culture_condition']=pd.Categorical(hier_full.culture_condition,COND,ordered=True)
hier_full['ontarget_effect_category']=pd.Categorical(hier_full.ontarget_effect_category,EFF_ORDER,ordered=True)
hier_full=hier_full.sort_values(['culture_condition','ontarget_effect_category']).reset_index(drop=True)
totals=hier_full.groupby('culture_condition',observed=True).n.sum()
grand=totals.sum()

fig,ax=plt.subplots(figsize=(7.2,7.6)); ax.set_aspect('equal')
r_in0,r_in1,r_out1=0.0,1.0,1.9
shade={'on-target KD':0.0,'no on-target KD':0.42,'putative off-target':0.72}
theta=90.0  # start top
for cond in COND:
    span=360.0*totals[cond]/grand
    t0=theta; t1=theta-span  # clockwise
    ax.add_patch(Wedge((0,0),r_in1,t1,t0,width=r_in1-r_in0,facecolor=COND_COL[cond],edgecolor='white',lw=2))
    mid=np.deg2rad((t0+t1)/2); rr=0.55
    ax.text(rr*np.cos(mid),rr*np.sin(mid),f"{COND_LABEL[cond]}\n{totals[cond]:,}",ha='center',va='center',
            fontsize=6.6,color='white',fontweight='bold')
    sub=hier_full[hier_full.culture_condition==cond]
    tt=t0
    for _,row in sub.iterrows():
        sp=span*row.n/totals[cond]; a0=tt; a1=tt-sp
        sh=shade[row.ontarget_effect_category]; col=lighten(COND_COL[cond],sh)
        ax.add_patch(Wedge((0,0),r_out1,a1,a0,width=r_out1-r_in1,facecolor=col,edgecolor='white',lw=1.5))
        if sp>18:
            m=np.deg2rad((a0+a1)/2); rr2=(r_in1+r_out1)/2
            ax.text(rr2*np.cos(m),rr2*np.sin(m),f"{EFF_LABEL[row.ontarget_effect_category]}\n{row.n:,}",
                    ha='center',va='center',fontsize=5.6,color='white' if sh<0.45 else '#2b2b2b')
        tt=a1
    theta=t1
ax.set_xlim(-2,2); ax.set_ylim(-2,2.05); ax.axis('off')
ax.set_title("內環＝培養條件、外環＝on-target 效應類別；三條件結構高度一致",fontsize=8,loc='center',pad=8)
fig.text(0.5,0.045,"扇形角度 ∝ DE 統計列數（n=33,983 列）；最外細扇為疑似 off-target（約 1%）",ha='center',fontsize=6)
fig.tight_layout(rect=[0,0.05,1,1])
fig.savefig("H2_sunburst.png",dpi=300,bbox_inches='tight')