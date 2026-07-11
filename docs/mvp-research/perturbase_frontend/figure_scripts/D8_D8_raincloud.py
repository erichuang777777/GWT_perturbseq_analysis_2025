"""
Standalone figure-generating script (Perturbase CD4+ T-cell Perturb-seq platform).

chart_id        : D8
source_image    : D8_raincloud.png
chart_title     : Raincloud
language        : Python
env_name        : figures
packages        : matplotlib, numpy, pandas, scipy
input_artifacts : 506b62e3-4ad0-42a0-ac4d-b779a31f8121
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl, matplotlib.pyplot as plt
import pandas as pd, numpy as np
from matplotlib.font_manager import FontProperties
from scipy.stats import gaussian_kde

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
grp = {c: incl.loc[incl['culture_condition']==c] for c in COND_ORDER}

YL = 'Downstream DE genes + 1 (log scale)'

# D8 Raincloud — horizontal: half-violin (cloud) + box + jittered rain, per condition
rng=np.random.default_rng(3)
fig,ax=plt.subplots(figsize=(6.6,4.6))
for i,c in enumerate(COND_ORDER):
    v=grp[c]['logDE'].values
    # half violin (cloud) above the row baseline
    kde=gaussian_kde(v); xs=np.linspace(0,3.9,200); d=kde(xs); d=d/d.max()*0.34
    base=i
    ax.fill_between(xs, base+0.06, base+0.06+d, color=PAL[c], alpha=0.7, edgecolor='white', lw=0.6, zorder=3)
    # rain: jittered points below baseline (subsample for legibility)
    sub=rng.choice(v, size=min(400,len(v)), replace=False)
    ax.scatter(sub, base-0.12-rng.uniform(0,0.18,len(sub)), s=3, color=PAL[c], alpha=0.25, edgecolor='none', zorder=2)
    # slim box at baseline
    q1,med,q3=np.quantile(v,[.25,.5,.75]); wlo,whi=np.quantile(v,[.05,.95])
    ax.plot([wlo,whi],[base,base],color='0.3',lw=1,zorder=4)
    ax.add_patch(plt.Rectangle((q1,base-0.045),q3-q1,0.09,facecolor='white',edgecolor='0.25',lw=1,zorder=5))
    ax.plot([med,med],[base-0.045,base+0.045],color='black',lw=2,zorder=6)
    ax.text(-0.12, base, f'{COND_EN[c]}\n(n={len(v):,})', ha='right', va='center', fontsize=8, color=PAL[c], fontweight='bold')
ax.set_yticks([]); ax.spines['left'].set_visible(False)
ax.set_xticks([0,1,2,3]); ax.set_xticklabels(['1','10','100','1,000'])
ax.set_xlabel(YL, fontproperties=CJK, labelpad=6)
ax.set_title('Raincloud: cloud, box, and rain layers of the downstream DE distribution are consistent across conditions', fontproperties=CJK, loc='left')
ax.set_xlim(-0.7,3.95); ax.set_ylim(-0.5,2.6)
fig.tight_layout(); fig.savefig('D8_raincloud.png',dpi=300,bbox_inches='tight')