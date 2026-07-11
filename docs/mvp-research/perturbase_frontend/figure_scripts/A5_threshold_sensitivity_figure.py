"""
chart_id:        A5
source image:    threshold_sensitivity_figure.png
chart title:     Threshold Sensitivity Analysis for CD4+ T-cell Perturbation Target Discovery
language:        Python
env name:        python
input-artifact version_ids (1):
  - 11c6348b-f46d-48a3-8c22-7ae328f40c6c  (DE_stats.suppl_table.csv)
packages referenced: matplotlib, numpy, os, pandas, scipy
"""

import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

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


# Load data
df = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/eb4c9b7d-b197-47c5-824c-efbd6bc2b805/v11c6348b_DE_stats.suppl_table.csv")

# Per-target rank score: max n_total_de_genes across conditions
rank_score = df.groupby('target_contrast_gene_name')['n_total_de_genes'].max()

# Precompute per-row boolean components
sig = df['ontarget_significant'].values
noff = (~df['offtarget_flag']).values
ncells = df['n_cells_target'].values
nde = df['n_total_de_genes'].values
tgt = df['target_contrast_gene_name'].values

all_targets = np.array(sorted(df['target_contrast_gene_name'].unique()))
tgt_idx = {t:i for i,t in enumerate(all_targets)}
row_tidx = np.array([tgt_idx[t] for t in tgt])
N = len(all_targets)

def passing_set(C, D):
    row_pass = (ncells >= C) & sig & noff & (nde >= D)
    passed = np.zeros(N, dtype=bool)
    np.logical_or.at(passed, row_tidx, row_pass)
    return passed

bp = passing_set(200, 50)
baseline_bool = bp.copy()
baseline_idx_set = set(np.where(baseline_bool)[0])
rank_arr = rank_score.reindex(all_targets).values

Cs = [100,150,200,250,300,400]
Ds = [30,40,50,75,100]

pass_matrix = np.zeros((30, N), dtype=bool)
k = 0
for C in Cs:
    for D in Ds:
        pb = passing_set(C, D)
        pass_matrix[k] = pb
        k += 1

from scipy.stats import spearmanr

grid_rows = []
k = 0
for C in Cs:
    for D in Ds:
        pb = pass_matrix[k]
        idx = np.where(pb)[0]
        idx_set = set(idx.tolist())
        inter = np.array(sorted(idx_set & baseline_idx_set))
        union = idx_set | baseline_idx_set
        jac = len(idx_set & baseline_idx_set)/len(union) if union else np.nan
        if len(inter) >= 3:
            s_base = rank_arr[inter]
            s_comb = rank_arr[inter]
            rho = spearmanr(s_base, s_comb).correlation
        else:
            rho = np.nan
        grid_rows.append(dict(C=C, D=D, n_targets=int(pb.sum()),
                              delta_vs_baseline=int(pb.sum()-1235),
                              jaccard_vs_baseline=round(float(jac),4),
                              intersect_count=len(inter),
                              spearman_rho_vs_baseline=round(float(rho),4)))
        k += 1
grid = pd.DataFrame(grid_rows)

pass_fraction = pass_matrix.mean(axis=0)
in_baseline = baseline_bool

stab = pd.DataFrame({
    'target': all_targets,
    'pass_fraction': np.round(pass_fraction,4),
    'in_baseline': in_baseline,
})

def sclass(pf):
    if pf >= 0.9: return 'CORE'
    elif pf >= 0.1: return 'BOUNDARY'
    elif pf > 0: return 'FRAGILE'
    else: return 'NEVER'
stab['stability_class'] = stab['pass_fraction'].map(sclass)

unstable_inclusions = int(((stab['in_baseline']) & (stab['pass_fraction'] < 0.9)).sum())
unstable_exclusions_ge50 = int(((~stab['in_baseline']) & (stab['pass_fraction'] >= 0.5)).sum())
median_rho = float(np.nanmedian(grid['spearman_rho_vs_baseline']))

apply_figure_style()

fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))

# --- Panel A: heatmap n_targets over C x D ---
axA = axes[0]
piv = grid.pivot(index='D', columns='C', values='n_targets').sort_index(ascending=False)
im = axA.imshow(piv.values, cmap='viridis', aspect='auto')
axA.set_xticks(range(len(piv.columns))); axA.set_xticklabels(piv.columns)
axA.set_yticks(range(len(piv.index))); axA.set_yticklabels(piv.index)
axA.set_xlabel('C  (min cells per target)')
axA.set_ylabel('D  (min DE genes)')
axA.set_title('Shortlist size across thresholds', loc='left')
for i in range(piv.shape[0]):
    for j in range(piv.shape[1]):
        v = piv.values[i,j]
        axA.text(j, i, f'{v}', ha='center', va='center',
                 color='white' if v < piv.values.max()*0.6 else 'black', fontsize=6)
bj = list(piv.columns).index(200); bi = list(piv.index).index(50)
axA.add_patch(plt.Rectangle((bj-0.5,bi-0.5),1,1, fill=False, edgecolor='crimson', lw=2))
cb = fig.colorbar(im, ax=axA, fraction=0.046, pad=0.04); cb.set_label('n targets')

# --- Panel B: pass_fraction histogram with bands ---
axB = axes[1]
pf_all = stab['pass_fraction'].values
bins = np.linspace(0,1,21)
axB.hist(pf_all, bins=bins, color=META_GREY, edgecolor='white', lw=0.4)
axB.axvspan(0.9,1.001, color='#2c7fb8', alpha=0.15)
axB.axvspan(0.1,0.9, color='#fdae61', alpha=0.12)
axB.axvspan(0.001,0.1, color='#d7191c', alpha=0.12)
axB.set_yscale('log')
axB.set_xlabel('pass_fraction (over 30 combos)')
axB.set_ylabel('n targets (log)')
axB.set_title('Stability over full universe (11,526)', loc='left')
axB.text(0.95,0.5,'CORE', transform=axB.get_xaxis_transform(), ha='center', color='#2c7fb8', fontsize=6, rotation=90, va='bottom')
axB.text(0.5,0.5,'BOUNDARY', transform=axB.get_xaxis_transform(), ha='center', color='#b8860b', fontsize=6, va='bottom')
axB.text(0.05,0.5,'FRAGILE', transform=axB.get_xaxis_transform(), ha='center', color='#d7191c', fontsize=6, rotation=90, va='bottom')

# --- Panel C: Spearman rho distribution across combos ---
axC = axes[2]
rhos = grid['spearman_rho_vs_baseline'].values
axC.hist(rhos, bins=np.linspace(0.90,1.001,22), color='#2c7fb8', edgecolor='white', lw=0.4)
axC.set_xlabel('Spearman rho vs baseline ordering')
axC.set_ylabel('n combos')
axC.set_xlim(0.9,1.005)
axC.set_title('Rank stability of shared targets', loc='left')
axC.text(0.5,0.92,'all 30 combos rho = 1.00\n(intrinsic rank score)', transform=axC.transAxes,
         ha='center', va='top', fontsize=6.5)

for ax,l in zip(axes, ['a','b','c']):
    panel_letter(ax, l)
fig.tight_layout()
fig.savefig('threshold_sensitivity_figure.png', dpi=300, bbox_inches='tight')

# Fix panel B labels
for t in list(axB.texts):
    t.remove()
axB.text(0.96,0.97,'CORE', transform=axB.transAxes, ha='right', va='top', color='#2c7fb8', fontsize=6.5, fontweight='bold')
axB.text(0.5,0.97,'BOUNDARY', transform=axB.transAxes, ha='center', va='top', color='#b8860b', fontsize=6.5, fontweight='bold')
axB.text(0.055,0.55,'FRAGILE', transform=axB.transAxes, ha='center', va='center', color='#d7191c', fontsize=6, rotation=90)
for ax in axes:
    ax.xaxis.labelpad = 7
axA.yaxis.labelpad = 8
fig.tight_layout(pad=1.4, w_pad=2.2)

# Fix panel C annotation
for t in list(axC.texts):
    t.remove()
axC.text(0.5,0.92,'rho = 1.00 by construction\n(intrinsic rank score:\nself-comparison, not a test)',
         transform=axC.transAxes, ha='center', va='top', fontsize=6.2)
axC.set_title('Rank score is threshold-invariant', loc='left')

fig.savefig('threshold_sensitivity_figure.png', dpi=300, bbox_inches='tight')
