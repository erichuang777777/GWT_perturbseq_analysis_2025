"""
Standalone figure-generating script.

chart_id            : M6
source image        : M6_condition_metric_heatmap.png
chart title         : ×
language            : Python
conda env name      : python
input artifact vids : ['11c6348b-f46d-48a3-8c22-7ae328f40c6c', '506b62e3-4ad0-42a0-ac4d-b779a31f8121']
referenced packages : matplotlib, os

Extracted verbatim from artifact lineage (host.lineage['57843977-5cae-44f3-bd16-125e11194fb9']).
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
from matplotlib.gridspec import GridSpec

raw = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/eb4c9b7d-b197-47c5-824c-efbd6bc2b805/v11c6348b_DE_stats.suppl_table.csv")
curated = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/71b03570-3c70-4117-bd81-90917d27ab6b/v506b62e3_curated_targets.csv")

apply_figure_style(frame='open', sizes=(9,8,7))
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Helvetica Neue','Helvetica','Arial','DejaVu Sans','PingFang TC','Heiti TC']
mpl.rcParams['axes.unicode_minus'] = False

COND = ['Rest','Stim8hr','Stim48hr']
COND_COLORS = {'Rest':'#4C78A8','Stim8hr':'#F58518','Stim48hr':'#B4432E'}

raw = raw.merge(curated[['index','passes_gate','logDE']], on='index', how='left')
inc = raw[~raw.offtarget_flag].copy()

metrics={'Mean DE genes':('n_total_de_genes','mean','{:.0f}'),
         'Mean genes up':('n_up_genes','mean','{:.0f}'),
         'Mean genes down':('n_down_genes','mean','{:.0f}'),
         'Mean on-target effect':('ontarget_effect_size','mean','{:.2f}'),
         '% on-target significant':(None,'sig','{:.1f}%'),
         '% passes gate':(None,'gate','{:.1f}%'),
         'Median cells assayed':('n_cells_target','median','{:.0f}')}
rows=list(metrics); M=np.zeros((len(rows),3))
for ci,c in enumerate(COND):
    g=inc[inc.culture_condition==c]
    for ri,r in enumerate(rows):
        col,how,_=metrics[r]
        if how=='sig': M[ri,ci]=100*g.ontarget_significant.mean()
        elif how=='gate': M[ri,ci]=100*g.passes_gate.fillna(False).mean()
        elif how=='mean': M[ri,ci]=g[col].mean()
        else: M[ri,ci]=g[col].median()
Z=(M-M.mean(1,keepdims=True))/(M.std(1,keepdims=True)+1e-9)
fig,ax=plt.subplots(figsize=(5.4,4.8))
im=ax.imshow(Z,cmap='RdBu_r',vmin=-1.5,vmax=1.5,aspect='auto')
ax.set_xticks(range(3)); ax.set_xticklabels(COND)
ax.set_yticks(range(len(rows))); ax.set_yticklabels(rows)
for ri in range(len(rows)):
    for ci in range(3):
        ax.text(ci,ri,metrics[rows[ri]][2].format(M[ri,ci]),ha='center',va='center',fontsize=7,
                color='white' if abs(Z[ri,ci])>0.9 else '#222')
cb=fig.colorbar(im,ax=ax,fraction=0.046,pad=0.04,ticks=[-1.5,0,1.5])
cb.set_label('Relative to 3-condition mean (row z-score)')
ax.set_title('Hit rate and knockdown strength rise with stimulation;\nDE breadth peaks at 8 h',fontsize=9)
for lbl,c in zip(ax.get_xticklabels(),COND): lbl.set_color(COND_COLORS[c]); lbl.set_fontweight('bold')
ax.set_xticks(np.arange(-.5,3,1),minor=True); ax.set_yticks(np.arange(-.5,len(rows),1),minor=True)
ax.grid(which='minor',color='w',lw=1.2); ax.tick_params(which='minor',length=0)
fig.tight_layout(); fig.savefig('M6_condition_metric_heatmap.png',dpi=300,bbox_inches='tight')
