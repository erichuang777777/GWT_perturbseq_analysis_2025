"""Convergent regulatory core across CD4 polarization x aging x autoimmune risk.

Integrative re-analysis of the SOURCE paper's OWN three separate analyses
(Zhu & Dann et al. 2025): polarization regulators (Fig 4), aging regulators
(Fig 5), and autoimmune-GWAS cluster enrichment (Fig 7). The paper reports these
in isolation; this script asks whether a *convergent core* of regulators spans
all three, and — critically — whether that convergence survives technical-confound
control and the paper's own negative-control diseases.

Status: CANDIDATE hypothesis, internally robust but NOT independently validated
on the disease axis (see docs/convergent_core_analysis.md). Deterministic.

Honesty / anti-artifact discipline (this was rebuilt after an earlier attempt
turned out to be a sample-size artifact):
* Uses the paper's OWN regulator nominations + labels + negative controls — not
  any toolkit-internal construct.
* Every enrichment is tested against a COVARIATE-MATCHED permutation null
  (matched on trans-effect breadth), not just set sizes — so "well-powered /
  broad-effect genes score high everywhere" cannot manufacture the result.
* Reports the LIMITING results too: the held-out activation-signature test is
  null (the core is axis-specific, not general), and the only disease source
  available (Open Targets) is the paper's own Fig-7 source, so it CANNOT serve
  as independent validation. These are printed, not hidden.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[3]
_SUPPL = _ROOT / "metadata" / "suppl_tables"
POL_CSV = _SUPPL / "polarization_prediction_condition_comparison_regulator_coefficients.csv"
AGE_CSV = _SUPPL / "aging_prediction_condition_comparison_regulator_coefficients.csv"
AU_CSV = _SUPPL / "cluster_autoimmune_enrichment_results.suppl_table.csv"
DE_CSV = _SUPPL / "DE_stats.suppl_table.csv"

SEED = 0
N_PERM = 3000
STRONG_THRESHOLDS = (0.90, 0.95)


def tables_present() -> bool:
    return all(p.exists() for p in (POL_CSV, AGE_CSV, AU_CSV, DE_CSV))


def _autoimmune_driver_genes(au: pd.DataFrame, *, negative_control: bool = False) -> Set[str]:
    rows = au[(au["p_adj_fdr"] < 0.05) & (au["negative_control_disease"] == negative_control)]
    genes: Set[str] = set()
    for s in rows["intersecting_genes"].dropna():
        try:
            genes |= {g.upper() for g in ast.literal_eval(s)}
        except (ValueError, SyntaxError):
            continue
    return genes


def load_axes() -> Dict[str, Any]:
    """Load the four source tables into the axis quantities used throughout."""
    pol = pd.read_csv(POL_CSV)
    age = pd.read_csv(AGE_CSV)
    au = pd.read_csv(AU_CSV)
    de = pd.read_csv(DE_CSV)
    de["_g"] = de["target_contrast_gene_name"].astype(str).str.upper()
    breadth = {g: np.log1p(v) for g, v in de.groupby("_g")["n_total_de_genes"].max().items()}
    return {
        "ota": pol[pol["signature"] == "ota"].groupby("regulator")["coef_rank"].max(),
        "activation": pol[pol["signature"] == "activation"].groupby("regulator")["coef_rank"].max(),
        "aging": age.groupby("regulator")["coef_rank"].max(),
        "au_drivers": _autoimmune_driver_genes(au, negative_control=False),
        "au_negctrl": _autoimmune_driver_genes(au, negative_control=True),
        "breadth": breadth,
    }


def _universe(ax: Dict[str, Any]) -> List[str]:
    return [g for g in (set(ax["ota"].index) & set(ax["aging"].index) & set(ax["activation"].index))
            if g.upper() in ax["breadth"]]


def _matched_perm_p(uni: List[str], is_target: np.ndarray, is_hit: np.ndarray,
                    covariate: np.ndarray, *, nperm: int = N_PERM, nbins: int = 10, seed: int = SEED) -> Dict[str, float]:
    """Covariate-matched permutation: shuffle target membership within covariate
    bins, recompute overlap with the hit set. Controls for the covariate."""
    rng = np.random.default_rng(seed)
    bins = pd.qcut(covariate, nbins, labels=False, duplicates="drop")
    obs = int((is_target & is_hit).sum())
    null = np.empty(nperm)
    U = len(uni)
    for i in range(nperm):
        perm = np.zeros(U, bool)
        for b in np.unique(bins):
            idx = np.where(bins == b)[0]
            k = int(is_target[idx].sum())
            if k:
                perm[rng.choice(idx, k, replace=False)] = True
        null[i] = (perm & is_hit).sum()
    return {"obs": obs, "null_mean": float(null.mean()), "p": float((np.sum(null >= obs) + 1) / (nperm + 1))}


def core_genes(ax: Dict[str, Any], thr: float = 0.90) -> List[str]:
    uni = _universe(ax)
    P = {g for g in uni if ax["ota"].get(g, 0) >= thr}
    A = {g for g in uni if ax["aging"].get(g, 0) >= thr}
    return sorted({g for g in (P & A) if g.upper() in ax["au_drivers"]})


def run(ax: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Full analysis. Returns a structured report dict."""
    if ax is None:
        ax = load_axes()
    uni = _universe(ax)
    cov = np.array([ax["breadth"][g.upper()] for g in uni])
    out: Dict[str, Any] = {"universe": len(uni), "convergence": {}, "core": {}, "specificity": {}, "held_out_activation": {}}

    # 1) polarization ∩ aging overlap, breadth-matched
    for thr in STRONG_THRESHOLDS:
        P = np.array([ax["ota"].get(g, 0) >= thr for g in uni])
        A = np.array([ax["aging"].get(g, 0) >= thr for g in uni])
        out["convergence"][thr] = _matched_perm_p(uni, P, A, cov)

    # 2) the convergent core + its autoimmune-driver enrichment (breadth-matched)
    thr = 0.90
    P = np.array([ax["ota"].get(g, 0) >= thr for g in uni])
    A = np.array([ax["aging"].get(g, 0) >= thr for g in uni])
    PA = P & A
    isAU = np.array([g.upper() in ax["au_drivers"] for g in uni])
    core = core_genes(ax, thr)
    out["core"] = {"thr": thr, "n_pol_and_aging": int(PA.sum()), "genes": core,
                   "au_enrichment": _matched_perm_p(uni, PA, isAU, cov)}

    # 3) negative-control specificity (paper's own negative-control diseases)
    coreU = {g.upper() for g in core}
    out["specificity"] = {
        "core_in_real_disease": len(coreU & ax["au_drivers"]),
        "core_in_negative_control": len(coreU & ax["au_negctrl"]),
        "core_size": len(core),
    }

    # 4) held-out activation signature (NOT used to define the core) — a genuine
    #    non-circular generalization test. Expected result: NULL (core is axis-specific).
    isCore = np.array([g in coreU for g in uni])
    for hthr in STRONG_THRESHOLDS:
        isAct = np.array([ax["activation"].get(g, 0) >= hthr for g in uni])
        out["held_out_activation"][hthr] = _matched_perm_p(uni, isCore, isAct, cov)
    # correlation ota vs activation (calibrates whether the held-out test is informative)
    comm = sorted(set(ax["ota"].index) & set(ax["activation"].index))
    from scipy import stats
    out["ota_vs_activation_spearman"] = float(stats.spearmanr(ax["ota"][comm], ax["activation"][comm])[0])
    return out


def main() -> int:
    if not tables_present():
        print("source suppl tables not present in this checkout; nothing to run.")
        return 1
    r = run()
    print(f"universe (regulators in polarization ∩ aging ∩ activation, with covariate): {r['universe']}")
    print("\n[1] polarization ∩ aging overlap, breadth-matched permutation:")
    for thr, d in r["convergence"].items():
        print(f"    thr={thr}: obs={d['obs']}  matched-null={d['null_mean']:.1f}  p={d['p']:.4f}")
    c = r["core"]
    print(f"\n[2] convergent core (strong polarization ∩ strong aging ∩ autoimmune-driver) @thr={c['thr']}: {len(c['genes'])} genes")
    print(f"    {c['genes']}")
    print(f"    autoimmune-driver enrichment in pol∩aging: obs={c['au_enrichment']['obs']} "
          f"matched-null={c['au_enrichment']['null_mean']:.1f} p={c['au_enrichment']['p']:.4f}")
    s = r["specificity"]
    print(f"\n[3] negative-control specificity: {s['core_in_real_disease']}/{s['core_size']} core genes in REAL "
          f"autoimmune diseases vs {s['core_in_negative_control']}/{s['core_size']} in NEGATIVE-CONTROL diseases")
    print(f"\n[4] HELD-OUT activation signature (ota vs activation Spearman={r['ota_vs_activation_spearman']:.3f}; "
          f"low = independent axis):")
    for thr, d in r["held_out_activation"].items():
        print(f"    core enriched for strong activation@{thr}? obs={d['obs']} null={d['null_mean']:.1f} p={d['p']:.4f}  "
              f"(NULL expected — core is axis-specific, NOT a generic-strength artifact)")
    print("\nLIMITATION: the only disease source in-repo (Open Targets) is the paper's OWN Fig-7 source, "
          "so it cannot serve as independent disease validation. External GWAS needed (see docs).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
