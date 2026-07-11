"""
Standalone generating script for a Perturbase CD4+ T-cell Perturb-seq platform chart.

chart_id:        A1
source image:    benchmark_pr_roc.png
chart title:     CD4+ Perturb-seq Context-Specific DE Benchmark: PR Curve, ROC Curve, and Regulator Ranking
language:        Python
env name:        python
packages:        matplotlib, numpy, os, pandas, scipy, sklearn
input-artifact version_ids:
  - 39559648-2551-44f3-9d14-80c861dac4af
"""

import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_curve, roc_curve
from scipy.stats import mannwhitneyu, hypergeom

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


def panel_letter(ax, letter, dx=-0.18, dy=1.02, case="lower", fontsize=None):
    import matplotlib.pyplot as plt
    if fontsize is None:
        fontsize = plt.rcParams.get("font.size", 8) + 1
    s = letter.lower() if case == "lower" else letter.upper()
    ax.text(dx, dy, s, transform=ax.transAxes,
            fontweight="bold", fontsize=fontsize, va="bottom", ha="left")


df = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/46a1c017-4a49-46dc-8098-512c17286263/v39559648_target_master_table.csv")

POSITIVE = ["CD3E","CD3D","CD3G","CD247","LAT","ZAP70","LCK","PLCG1","VAV1","ITK","LCP2","FYN",
            "TBX21","GATA3","STAT6","STAT4","RORC","FOXP3","BCL6","STAT3",
            "CD28","ICOS","IL2RA","CTLA4","IL2RB","JAK3","STAT5B"]
NEGATIVE = ["ACTB","GAPDH","TUBB","B2M","RPL13A","PPIA","HPRT1","YWHAZ","SDHA","TBP","GUSB"]

d = df.dropna(subset=['ctx_specific_de']).copy()
d = d.sort_values('ctx_specific_de', ascending=False).reset_index(drop=True)
d['ctx_rank'] = np.arange(1, len(d)+1)

def cls(g):
    if g in POSITIVE: return 'positive'
    if g in NEGATIVE: return 'negative'
    return 'rest'
d['truth_class'] = d['gene'].apply(cls)

pos_present = d[d.truth_class=='positive']['gene'].tolist()
neg_present = d[d.truth_class=='negative']['gene'].tolist()
n_pos, n_neg = len(pos_present), len(neg_present)

score = d['ctx_specific_de'].values
y_pos = (d.truth_class=='positive').astype(int).values

auroc_full = roc_auc_score(y_pos, score)
avg_prec = average_precision_score(y_pos, score)

strict = d[d.truth_class.isin(['positive','negative'])]
auroc_strict = roc_auc_score((strict.truth_class=='positive').astype(int), strict['ctx_specific_de'])

pos_scores = d[d.truth_class=='positive']['ctx_specific_de']
rest_scores = d[d.truth_class!='positive']['ctx_specific_de']
U, mw_p = mannwhitneyu(pos_scores, rest_scores, alternative='greater')

N = len(d); K = n_pos; nn = 50
k = (d.head(50).truth_class=='positive').sum()
top50_p = hypergeom.sf(k-1, N, K, nn)

pos_med = float(d[d.truth_class=='positive']['ctx_rank'].median())
neg_med = float(d[d.truth_class=='negative']['ctx_rank'].median())

prec, rec, _ = precision_recall_curve(y_pos, score)
fpr, tpr, _ = roc_curve(y_pos, score)
baseline = n_pos/len(d)

apply_figure_style()

fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))

ax = axes[0]
ax.plot(rec, prec, color='#1b4079', lw=2)
ax.axhline(baseline, ls='--', color=META_GREY, lw=1)
ax.text(0.02, baseline+0.03, f'random ({baseline:.3f})', color=META_GREY, fontsize=6, ha='left')
ax.set_xlabel('Recall'); ax.set_ylabel('Precision')
ax.set_title(f'Positives concentrate at top\nAP = {avg_prec:.2f} ({avg_prec/baseline:.0f}× random)')
ax.set_ylim(-0.03, 1.03); ax.margins(x=0.04)
panel_letter(ax, 'a')

ax = axes[1]
ax.plot(fpr, tpr, color='#1b4079', lw=2)
ax.plot([0,1],[0,1], ls='--', color=META_GREY, lw=1)
ax.set_xlabel('False positive rate'); ax.set_ylabel('True positive rate')
ax.set_title(f'Known regulators rank high\nAUROC = {auroc_full:.2f} (pos vs rest)')
ax.set_xlim(-0.03,1.03); ax.set_ylim(-0.03,1.03)
panel_letter(ax, 'b')

ax = axes[2]
order = ['positive','negative','rest']
labs = {'positive':f'canonical\nregulators\n(n={n_pos})','negative':f'housekeeping\n(n={n_neg})','rest':f'other\n(n={len(d)-n_pos-n_neg})'}
cols = {'positive':'#1b4079','negative':'#b3122e','rest':META_GREY}
rng = np.random.default_rng(0)
for i,c in enumerate(order):
    r = d[d.truth_class==c]['ctx_rank'].values
    x = i + rng.uniform(-0.18,0.18,len(r))
    ax.scatter(x, r, s=(14 if c!='rest' else 5), color=cols[c], alpha=(0.85 if c!='rest' else 0.25),
               edgecolor='none', zorder=(3 if c!='rest' else 1))
    med = np.median(r)
    ax.plot([i-0.25,i+0.25],[med,med], color='k', lw=1.8, zorder=4)
ax.set_xticks(range(3)); ax.set_xticklabels([labs[c] for c in order], fontsize=6)
ax.set_ylabel('Context-specific rank (1 = top)')
ax.invert_yaxis()
ax.set_title(f'Median rank: {int(pos_med)} vs {int(neg_med)}\nMann-Whitney p = {mw_p:.1e}')
panel_letter(ax, 'c')

fig.suptitle('Ranking benchmark against canonical CD4 T-cell regulators (ground truth independent of concept modules)',
             fontsize=8, y=1.02)
fig.tight_layout()
fig.savefig('benchmark_pr_roc.png', dpi=300, bbox_inches='tight')
print("saved")