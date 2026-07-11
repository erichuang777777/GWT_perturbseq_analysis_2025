"""
Standalone figure-generating script (Perturbase CD4+ T-cell Perturb-seq platform).

chart_id        : D10
source_image    : D10_qq.png
chart_title     : Q-Q Plot: On-Target Effect Size Distribution Across CD4+ T-Cell Conditions
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
import scipy.stats as ss
from scipy import stats

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
eff = incl[incl['ontarget_significant'] & (incl['ontarget_effect_size']!=0)].copy()

fig,axes=plt.subplots(1,3,figsize=(9.2,3.6),sharey=True)
for ax,c in zip(axes,COND_ORDER):
    v=eff[eff.culture_condition==c]['ontarget_effect_size'].values
    (osm,osr),(slope,inter,r)=stats.probplot(v, dist='norm')
    ax.scatter(osm,osr,s=5,color=PAL[c],alpha=0.35,edgecolor='none',zorder=2)
    xr=np.array([osm.min(),osm.max()])
    ax.plot(xr,slope*xr+inter,color='0.15',lw=1.4,zorder=3)
    ax.set_title(f'{COND_EN[c]}\nn={len(v):,}  R\u00b2={r**2:.3f}', fontproperties=CJK, fontsize=9, loc='center')
    ax.set_xlabel('Normal theoretical quantiles', fontproperties=CJK, fontsize=8)
axes[0].set_ylabel('on-target effect size', fontproperties=CJK, labelpad=6)
fig.suptitle('Effect size deviates from normality: left-skewed heavy tail; Q-Q tails clearly depart from the reference line', fontproperties=CJK, x=0.02, ha='left', fontsize=11)
fig.tight_layout(rect=[0,0,1,0.94])

for ax in axes: ax.set_xlabel('Normal theoretical quantiles', fontproperties=CJK, fontsize=8, labelpad=6)
fig.tight_layout(rect=[0,0,1,0.94]); fig.savefig('D10_qq.png',dpi=300,bbox_inches='tight')