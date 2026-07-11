"""
Standalone figure-generating script (Perturbase CD4+ T-cell Perturb-seq platform).

chart_id        : D7
source_image    : D7_swarm.png
chart_title     : On-Target Effect Size Distribution Across Conditions
language        : Python
env_name        : figures
packages        : matplotlib, numpy, pandas
input_artifacts : 506b62e3-4ad0-42a0-ac4d-b779a31f8121
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl, matplotlib.pyplot as plt
import pandas as pd, numpy as np
from matplotlib.font_manager import FontProperties

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

apply_figure_style(frame='open', sizes=(9,8,7))
mpl.rcParams['font.sans-serif'] = ['Helvetica Neue','Arial','DejaVu Sans','PingFang TC','Heiti TC']
mpl.rcParams['axes.unicode_minus'] = False
CJK = FontProperties(family='DejaVu Sans')

df = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/71b03570-3c70-4117-bd81-90917d27ab6b/v506b62e3_curated_targets.csv")
df['logDE'] = np.log10(df['n_total_de_genes'] + 1)

COND_ORDER = ['Rest','Stim8hr','Stim48hr']
COND_EN = {'Rest':'Rest','Stim8hr':'Stim 8 hr','Stim48hr':'Stim 48 hr'}
PAL = {'Rest':'#4C72B0','Stim8hr':'#DD8452','Stim48hr':'#C44E52'}

incl = df[~df['offtarget_flag']].copy()

SHORTLIST = ['CD3E','LAT','TADA2B','SENP5','PLCG1','VAV1','SGF29','UBXN1','CD247','MED12','CCNC','SUPT20H','TADA1','DENR','PMVK']
sl = incl[incl['target_contrast_gene_name'].isin(SHORTLIST)].copy()

YL = 'Downstream DE genes + 1 (log scale)'
EFF_YL_EN = 'on-target effect size (negative = knockdown)'

def beeswarm_offsets(y, width=0.32, ptsize=0.9):
    order=np.argsort(y); yb=np.array(y)[order]; xs=np.zeros(len(yb))
    placed=[]
    for i,yi in enumerate(yb):
        for off in np.concatenate([[0], np.repeat(np.arange(ptsize, width+ptsize, ptsize),2)*np.array([1,-1]*20)[:len(np.repeat(np.arange(ptsize,width+ptsize,ptsize),2))]]):
            if all(not (abs(yi-py)<ptsize and abs(off-px)<ptsize) for px,py in placed):
                xs[i]=off; placed.append((off,yi)); break
        else:
            xs[i]=0; placed.append((0,yi))
    out=np.zeros(len(y)); out[order]=xs; return out

fig,ax=plt.subplots(figsize=(6.2,4.4))
ymin=sl['ontarget_effect_size'].min()
for i,c in enumerate(COND_ORDER):
    v=sl[sl.culture_condition==c]['ontarget_effect_size'].values
    off=beeswarm_offsets(v, width=0.30, ptsize=1.5)
    ax.scatter(i+off*0.11, v, s=40, color=PAL[c], alpha=0.88, edgecolor='white', lw=0.6, zorder=3)
    med=np.median(v); ax.plot([i-0.24,i+0.24],[med,med],color='0.15',lw=2.4,zorder=4)
    ax.text(i,ymin-3.5,f'n={len(v)}',ha='center',fontsize=7,color='0.35')
ax.axhline(0,color='0.6',lw=0.9,ls=(0,(4,3)),zorder=0)
ax.set_xticks([0,1,2]); ax.set_xticklabels([COND_EN[c] for c in COND_ORDER])
ax.set_ylabel(EFF_YL_EN, fontproperties=CJK, labelpad=8)
ax.set_title('Beeswarm layout spreads each prioritized target effect size; density reflects knockdown-strength distribution', fontproperties=CJK, loc='left')
ax.set_xlim(-0.5,2.5); ax.set_ylim(ymin-5,3.5)
fig.tight_layout(); fig.savefig('D7_swarm.png',dpi=300,bbox_inches='tight')

ax.set_title('Beeswarm layout spreads each prioritized target\'s effect size; density reflects knockdown-strength distribution', fontproperties=CJK, loc='left')
fig.savefig('D7_swarm.png',dpi=300,bbox_inches='tight')