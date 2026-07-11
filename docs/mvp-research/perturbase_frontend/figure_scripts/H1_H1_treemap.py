"""
Standalone figure-generating script (Perturbase CD4+ T-cell Perturb-seq platform).

chart_id        : H1
source_image    : H1_treemap.png
chart_title     : Marimekko Mosaic Treemap of DE-Stat Rows by Culture Condition and On-Target Effect
language        : Python
env_name        : python
packages        : matplotlib, numpy, pandas, squarify
input_artifacts : 506b62e3-4ad0-42a0-ac4d-b779a31f8121
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import squarify
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
        except Exception as e: print("err",p,e)

def setup_style():
    apply_figure_style()
    plt.rcParams['font.family']='sans-serif'
    plt.rcParams['font.sans-serif']=['PingFang TC','DejaVu Sans']
    plt.rcParams['axes.unicode_minus']=False

def lighten(hexc,f):
    from matplotlib.colors import to_rgb
    r,g,b=to_rgb(hexc); return (r+(1-r)*f,g+(1-g)*f,b+(1-b)*f)

COND=['Rest','Stim8hr','Stim48hr']
COND_COL={'Rest':'#4E79A7','Stim8hr':'#F28E2B','Stim48hr':'#59A14F'}
COND_LABEL={'Rest':'靜息 Rest','Stim8hr':'刺激 8hr','Stim48hr':'刺激 48hr'}
EFF_ORDER=['on-target KD','no on-target KD','putative off-target']
EFF_LABEL={'on-target KD':'有 on-target 敲低','no on-target KD':'無 on-target 敲低','putative off-target':'疑似 off-target'}

curated = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/71b03570-3c70-4117-bd81-90917d27ab6b/v506b62e3_curated_targets.csv")
c = curated.copy()
c['gate_lab'] = np.where(c.passes_gate,'通過門檻','未通過')

hier=(c.groupby(['culture_condition','ontarget_effect_category']).size().rename('n').reset_index())
hier['culture_condition']=pd.Categorical(hier.culture_condition,COND,ordered=True)
hier['ontarget_effect_category']=pd.Categorical(hier.ontarget_effect_category,EFF_ORDER,ordered=True)
hier=hier.sort_values(['culture_condition','ontarget_effect_category']).reset_index(drop=True)

setup_style()
fig,ax=plt.subplots(figsize=(9,5.6))
x0=0.0; W=100.0; H=100.0
totals=hier.groupby('culture_condition',observed=True).n.sum()
shade={'on-target KD':0.0,'no on-target KD':0.4,'putative off-target':0.72}
off_rects={}
for cond in COND:
    w=W*totals[cond]/totals.sum()
    sub=hier[hier.culture_condition==cond]
    r=squarify.normalize_sizes(sub.n.values,w,H); rr=squarify.squarify(r,x0,0,w,H)
    for rec,(_,row) in zip(rr,sub.iterrows()):
        eff=row.ontarget_effect_category; sh=shade[eff]; col=lighten(COND_COL[cond],sh)
        is_off=eff=='putative off-target'
        ax.add_patch(mpl.patches.Rectangle((rec['x'],rec['y']),rec['dx'],rec['dy'],facecolor=col,
                     edgecolor=('#C0392B' if is_off else 'white'),lw=(1.4 if is_off else 1.8),hatch=('////' if is_off else None)))
        if is_off: off_rects[cond]=rec
        if rec['dx']*rec['dy']>W*H*0.010:
            ax.text(rec['x']+rec['dx']/2,rec['y']+rec['dy']/2,f"{EFF_LABEL[eff]}\n{row.n:,} 列",
                    ha='center',va='center',fontsize=6.4,color='white' if sh<0.45 else '#2b2b2b')
    ax.text(x0+w/2,H+7.0,f"{COND_LABEL[cond]}",ha='center',va='bottom',fontsize=8,fontweight='bold',color=COND_COL[cond])
    ax.text(x0+w/2,H+2.0,f"{totals[cond]:,} 列",ha='center',va='bottom',fontsize=6.4,color=COND_COL[cond])
    x0+=w
rc=off_rects['Stim48hr']
off_total=int(hier[hier.ontarget_effect_category=='putative off-target'].n.sum())
lx,ly=rc['x']+rc['dx']*0.5, rc['y']+rc['dy']/2
tx,ty=W+2, H*0.30
ax.plot([lx,tx-0.5],[ly,ty],color='#C0392B',lw=0.8,zorder=6,clip_on=False)
ax.text(tx,ty,f"疑似 off-target\n（全體 {off_total} 列，約 1%）",fontsize=5.8,color='#C0392B',ha='left',va='center')
ax.set_xlim(0,W+30); ax.set_ylim(0,H+16)
ax.set_xticks([]); ax.set_yticks([]); ax.axis('off')
ax.set_title("on-target 敲低是三條件下最主要的效應類別（約 62% 的 DE 統計列）",fontsize=8,loc='left',pad=36)
fig.text(0.5,0.02,f"全圖 n=33,983 列 DE 統計；矩形面積 ∝ 列數，外層依培養條件分欄、內層依 on-target 效應類別；頂端紅框斜線帶為疑似 off-target（全體 {off_total} 列，約 1%）",ha='center',fontsize=5.4)
fig.tight_layout(rect=[0,0.04,1,1])
fig.savefig("H1_treemap.png",dpi=300,bbox_inches='tight')