"""
chart_id:        A9
source image:    lincs_concordance.png
chart title:     GB10 Signed Matrix vs LINCS - Directional Agreement and Rank Correlation (4 Targets, Non-T-Cell Lines)
language:        Python
env name:        python
input-artifact version_ids (3):
  - ca1ccabf-a849-4eac-9225-be930d12a3a8  (part-000.parquet)
  - 3df56bd0-dcae-437c-8137-68c8e0308a40  (part-001.parquet)
  - db18632b-f68a-4025-9f03-4688c343e939  (lincs_demo_signatures_4genes.csv)
packages referenced: matplotlib, os, pandas, scipy
"""

import pandas as pd, numpy as np
import matplotlib as mpl, matplotlib.pyplot as plt
from scipy.stats import spearmanr

PART0 = '/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/ed0fef52-6322-4297-9044-fd821bd683f9/vca1ccabf_part-000.parquet'
PART1 = '/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/d3754585-a77d-4289-b4dd-7fc62ca84277/v3df56bd0_part-001.parquet'
LINCS = '/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/9feeba23-71e2-445a-8788-fbfc440eb4a1/vdb18632b_lincs_demo_signatures_4genes.csv'

full = pd.concat([pd.read_parquet(PART0), pd.read_parquet(PART1)], ignore_index=True)
lincs = pd.read_csv(LINCS)

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


targets = ["SENP5","PLCG1","CCNC","PMVK"]
landmarks = set(lincs["landmark_gene"])

def target_profile(tg):
    sub = full[full.target_gene == tg]
    if sub.empty: return None
    idx = sub.groupby("downstream_gene")["log_fc"].apply(lambda s: s.abs().idxmax())
    prof = sub.loc[idx.values, ["downstream_gene","log_fc"]].set_index("downstream_gene")["log_fc"]
    return prof

rows=[]
per_target={}
caveat="DEMO-level directional sanity check: LINCS from non-T-cell lines, only 4 overlapping targets; NOT full external validation."
for tg in targets:
    prof = target_profile(tg)
    lref = lincs.set_index("landmark_gene")[tg]
    if prof is None:
        rows.append([tg,0,np.nan,np.nan,np.nan,caveat]); continue
    shared = sorted(set(prof.index) & landmarks)
    gb = prof.loc[shared].values
    lc = lref.loc[shared].values
    n=len(shared)
    sign_agree = float(np.mean(np.sign(gb)==np.sign(lc))) if n else np.nan
    rho,p = spearmanr(gb,lc) if n>=3 else (np.nan,np.nan)
    rows.append([tg,n,sign_agree,rho,p,caveat])
    per_target[tg]={"n_shared":int(n),"sign_agreement":round(float(sign_agree),4),"spearman":round(float(rho),4)}

conc = pd.DataFrame(rows, columns=["target","n_shared_landmark","sign_agreement_frac","spearman_rho","p_value","caveat"])

apply_figure_style()

d = conc.dropna(subset=["sign_agreement_frac"]).copy()
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))

# Panel a: sign agreement
ax=axes[0]
colors=["#4C72B0" if p>=0.05 else "#C44E52" for p in d["p_value"]]
bars=ax.bar(d["target"], d["sign_agreement_frac"], color="#4C72B0", width=0.6)
ax.axhline(0.5, color=META_GREY, ls="--", lw=1)
ax.text(3.35,0.505,"chance",color=META_GREY,fontsize=6,va="bottom",ha="right")
ax.set_ylim(0,0.7); ax.set_ylabel("Sign-agreement fraction")
for x,v,n in zip(range(len(d)),d["sign_agreement_frac"],d["n_shared_landmark"]):
    ax.text(x,v+0.01,f"{v:.2f}\n(n={n})",ha="center",va="bottom",fontsize=6)
ax.set_title("Directional agreement vs LINCS")
panel_letter(ax,'a')

# Panel b: spearman rho
ax=axes[1]
cols=["#C44E52" if p<0.05 else "#8C8C8C" for p in d["p_value"]]
ax.bar(d["target"], d["spearman_rho"], color=cols, width=0.6)
ax.axhline(0,color="k",lw=0.8)
ax.set_ylabel("Spearman "+r"$\rho$")
ax.set_ylim(-0.1,0.25)
for x,r,p in zip(range(len(d)),d["spearman_rho"],d["p_value"]):
    star="*" if p<0.05 else ""
    ax.text(x, r+(0.008 if r>=0 else -0.02), f"{r:+.2f}{star}",ha="center",va="bottom" if r>=0 else "top",fontsize=6)
ax.set_title("Rank correlation (overlap subspace)")
panel_letter(ax,'b')

fig.suptitle("GB10 signed matrix vs LINCS — DEMO directional check (4 targets, non-T-cell lines)", fontsize=8, y=1.02)
fig.tight_layout()
fig.savefig("lincs_concordance.png", dpi=300, bbox_inches="tight")
