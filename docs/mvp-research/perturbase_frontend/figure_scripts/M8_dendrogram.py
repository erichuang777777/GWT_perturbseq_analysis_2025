"""
Standalone figure-generating script.

chart_id            : M8
source image        : M8_dendrogram.png
chart title         : Shortlist genes group by their three-condition knockdown profile
language            : Python
conda env name      : python
input artifact vids : ['e168ccb9-6d5d-427c-a5cf-93f388492f2f', '3d16f091-547f-4e36-861f-e1980da48a92']
referenced packages : matplotlib, os, scipy

Extracted verbatim from artifact lineage (host.lineage['f5b11d6d-ebc1-47d7-98fa-a7acbf6e9f49']).
Edit this single file to tweak the figure, then re-run in the 'python' environment.
"""

# skill:figure-style kernel.py (auto-injected on skill load)
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


import matplotlib as mpl, matplotlib.pyplot as plt, numpy as np, pandas as pd
from scipy.cluster.hierarchy import linkage, dendrogram, set_link_color_palette

effect = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/34e69736-d190-40d4-853c-90e059c0d7b9/ve168ccb9_effect_matrix.csv", index_col=0)

apply_figure_style(frame='open', sizes=(9,8,7))
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Helvetica Neue','Helvetica','Arial','DejaVu Sans','PingFang TC','Heiti TC']
mpl.rcParams['axes.unicode_minus'] = False

COND = ['Rest','Stim8hr','Stim48hr']
COND_COLORS = {'Rest':'#4C78A8','Stim8hr':'#F58518','Stim48hr':'#B4432E'}
shortlist = ['CD3E','LAT','TADA2B','SENP5','PLCG1','VAV1','SGF29','UBXN1','CD247','MED12','CCNC','SUPT20H','TADA1','DENR','PMVK']

sl = [g for g in shortlist if g in effect.index]
E = effect.loc[sl, COND]
Z = linkage(E.values, method='ward')
# CVD-safe qualitative palette (blue/orange/purple) instead of red/green
set_link_color_palette(['#4C78A8','#F58518','#7B4FA3','#54A24B'])
fig, ax = plt.subplots(figsize=(7.0, 4.4))
dn = dendrogram(Z, labels=E.index.tolist(), ax=ax, color_threshold=0.5*Z[:,2].max(),
                above_threshold_color='#999', leaf_rotation=45)
ax.set_ylabel('Cluster distance (Ward, on effect-size profile)')
for lbl in ax.get_xticklabels(): lbl.set_fontstyle('italic'); lbl.set_fontsize(7.5); lbl.set_ha('right')
ax.set_title('Shortlist genes group by their three-condition knockdown profile', fontsize=9)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout()
fig.savefig('M8_dendrogram.png', dpi=300, bbox_inches='tight')
set_link_color_palette(None)
print("M8 v2 ok")
