"""
Standalone figure-generating script (Perturbase CD4+ T-cell Perturb-seq platform).

chart_id        : C2
source_image    : C2_pseudovolcano.png
chart_title     : Pseudo-volcano: CD4+ T-cell targets by on-target effect size and DE-gene count
language        : Python
env_name        : python
packages        : matplotlib, pandas
input_artifacts : 506b62e3-4ad0-42a0-ac4d-b779a31f8121
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


import pandas as pd, numpy as np, matplotlib as mpl, matplotlib.pyplot as plt
figs = apply_figure_style()

curated = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/71b03570-3c70-4117-bd81-90917d27ab6b/v506b62e3_curated_targets.csv")

COND = ['Rest', 'Stim8hr', 'Stim48hr']
CCOL = {'Rest': '#4C6FB1', 'Stim8hr': '#E8A33D', 'Stim48hr': '#B5462E'}
CLAB = {'Rest': 'Rest', 'Stim8hr': 'Stim 8 hr', 'Stim48hr': 'Stim 48 hr'}

from adjustText import adjust_text
import math

d = curated.copy()
inc = d[~d['offtarget_flag']].copy()
exc = d[d['offtarget_flag']].copy()

fig_c2, ax = plt.subplots(figsize=(6.2, 4.8))
for cond in COND:
    sub = inc[inc['culture_condition'] == cond]
    ax.scatter(sub['ontarget_effect_size'], sub['logDE'], s=5, c=CCOL[cond], alpha=0.33,
               linewidths=0, label=CLAB[cond], rasterized=True, zorder=2)
ax.scatter(exc['ontarget_effect_size'], exc['logDE'], s=7, facecolors='none', edgecolors='0.55',
           linewidths=0.4, alpha=0.45, label='Off-target flagged (excluded)', rasterized=True, zorder=1)
inc['score'] = inc['ontarget_effect_size'].abs() * inc['logDE']
top = inc.sort_values('score', ascending=False).drop_duplicates('target_contrast_gene_name').head(8)
ax.scatter(top['ontarget_effect_size'], top['logDE'], s=22, facecolors='none', edgecolors='#222', linewidths=0.9, zorder=5)
texts = [ax.text(r['ontarget_effect_size'], r['logDE'], r['target_contrast_gene_name'],
        fontsize=6, fontstyle='italic', zorder=6) for _, r in top.iterrows()]
adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='-', color='0.5', lw=0.5), expand=(1.4, 1.7),
            force_text=(0.5, 0.8))
ax.axhline(math.log10(50), color='0.4', ls='--', lw=0.7, zorder=3)
ax.text(-58, math.log10(50) + 0.06, 'gate: ≥50 DE genes', fontsize=6, color='0.4', ha='left', va='bottom')
ax.set_xlabel("On-target effect size (signed; negative = knockdown)")
ax.set_ylabel("DE-gene count  (log$_{10}$)")
ax.set_yticks([0, 1, 2, 3]); ax.set_yticklabels(['1', '10', '100', '1k'])
ax.margins(0.03)
ax.set_title("Pseudo-volcano: data has no p-value, so y is DE-gene count, not significance", loc='left', fontsize=7.5)
ax.legend(loc='lower left', frameon=False, fontsize=6, markerscale=2, handletextpad=0.3, bbox_to_anchor=(0.005, 0.005))
fig_c2.tight_layout()
fig_c2.savefig("C2_pseudovolcano.png", dpi=300, bbox_inches='tight')