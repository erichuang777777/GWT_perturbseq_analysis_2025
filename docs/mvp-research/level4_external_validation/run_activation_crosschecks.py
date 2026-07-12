#!/usr/bin/env python3
"""
run_activation_crosschecks.py
=============================
Track D (perturbation_validation_plan.md §5b P1) — ACTUAL RUN of the
phenotype-matched external cross-check against real, in-repo activation-phenotype
CRISPR screens.

Unlike `phenotype_matched_crosscheck.py` (the generic harness, which SKIPs when
no external table is supplied), this runner adapts the activation-phenotype
screens that ARE cached in this repo under `metadata/` into the harness input
contract, then runs `crosscheck()` on each and adds a **confound control**
(Hart core-essential genes) plus a label-permutation p-value.

Screens run (all measure T-cell ACTIVATION, unlike Track C's HIV screen):
    - Schmidt & Steinhart 2022  CD4+ IL2   (CRISPRi — same modality as our screen)
    - Schmidt & Steinhart 2022  CD8+ IFNG  (CRISPRi)
    - Freimer et al. 2022       IL2/IL2RA/CTLA4 regulator screens (aggregated)

Shifrut et al. 2018 (GSE119450) is NOT cached in this repo and NCBI/Cell are
blocked by the sandbox network policy, so it cannot be run here; the generic
harness stays turn-key for it (drop its casTLE gene table in via --external).

MAGeCK gene-summary -> harness contract mapping
-----------------------------------------------
Each screen file is MAGeCK `gene_summary` output (sorted marker-high vs -low):
    gene          = id
    fdr           = min(neg|fdr, pos|fdr)          # best hit significance
    effect_score  = abs(lfc)                        # gene-level activation effect magnitude
    hit_direction = -1 if neg|fdr <= pos|fdr else +1
                    (neg selection = knockdown DEPLETES marker-high pool =
                     knockdown DECREASES activation = -1; pos selection = +1)

Honesty
-------
Any null/weak result is reported as-is. If a cached file is missing, that screen
is skipped with a printed reason — never fabricated. Deterministic (fixed RNG
seed for the permutation null).

Usage
-----
    python run_activation_crosschecks.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# import the merged harness (same directory)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phenotype_matched_crosscheck import (  # noqa: E402
    FDR_HIT_THRESHOLD,
    crosscheck,
    write_outputs,
    OUT_CSV,
    OUT_MD,
)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]  # docs/mvp-research/level4_external_validation -> repo root
RANKING = HERE.parent / "signed_de_application" / "signed_ranking_v2.csv"
META = REPO / "metadata"
SCHMIDT = META / "SchmidtSteinhart2022_CRISPRi_screen_gene_phenotypes.csv"
FREIMER = META / "Freimer2022_Screen.csv"
HART = META / "gene_lists" / "core_essentials_hart.tsv"

COMBINED_MD = HERE / "track_d_activation_crosschecks_combined.md"
COMBINED_CSV = HERE / "track_d_activation_crosschecks_summary.csv"

PERM_N = 5000
PERM_SEED = 0


# --------------------------------------------------------------------------- #
# Adapters: cached MAGeCK screen -> harness input contract
# --------------------------------------------------------------------------- #
def _mageck_to_contract(df: pd.DataFrame) -> pd.DataFrame:
    """Map one MAGeCK gene_summary frame to {gene, effect_score, fdr, hit_direction}."""
    out = pd.DataFrame()
    out["gene"] = df["id"].astype(str)
    neg_fdr = pd.to_numeric(df["neg|fdr"], errors="coerce")
    pos_fdr = pd.to_numeric(df["pos|fdr"], errors="coerce")
    lfc = pd.to_numeric(df["neg|lfc"], errors="coerce")  # neg|lfc == pos|lfc in these files
    out["fdr"] = np.minimum(neg_fdr, pos_fdr)
    out["effect_score"] = lfc.abs()
    # neg selection wins -> knockdown depletes marker-high pool -> decreases activation -> -1
    out["hit_direction"] = np.where(neg_fdr <= pos_fdr, -1, 1)
    return out.dropna(subset=["fdr", "effect_score"])


def load_schmidt(phenotype: str) -> pd.DataFrame | None:
    if not SCHMIDT.exists():
        return None
    d = pd.read_csv(SCHMIDT)
    d = d[d["phenotype"] == phenotype]
    if d.empty:
        return None
    return _mageck_to_contract(d)


def load_freimer() -> pd.DataFrame | None:
    if not FREIMER.exists():
        return None
    d = pd.read_csv(FREIMER)
    c = _mageck_to_contract(d)
    c = c[c["gene"].str.upper() != "NON-TARGETING"]
    # aggregate across the 3 Freimer screens: keep each gene's most-significant hit
    c = c.sort_values("fdr").drop_duplicates(subset="gene", keep="first")
    return c


def load_essentials() -> set[str]:
    if not HART.exists():
        return set()
    return {g.strip().upper() for g in HART.read_text().splitlines() if g.strip()}


# --------------------------------------------------------------------------- #
# Confound control + permutation significance
# --------------------------------------------------------------------------- #
def _auroc(pos: np.ndarray, neg: np.ndarray) -> float:
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    from scipy.stats import mannwhitneyu

    u, _ = mannwhitneyu(pos, neg, alternative="two-sided")
    return float(u / (len(pos) * len(neg)))


def auroc_excluding_essentials(merged: pd.DataFrame, essentials: set[str]) -> dict:
    """Recompute the top-N enrichment AUROC after dropping Hart core-essential genes,
    to check the signal is not just driven by generically essential/proliferation genes."""
    m = merged.dropna(subset=["primary_rank"]).copy()
    m["is_hit"] = m["fdr"] < FDR_HIT_THRESHOLD
    m["is_essential"] = m["target_gene"].str.upper().isin(essentials)
    m["score"] = -m["primary_rank"]

    kept = m[~m["is_essential"]]
    pos = kept.loc[kept["is_hit"], "score"].to_numpy()
    neg = kept.loc[~kept["is_hit"], "score"].to_numpy()
    n_hits = int(m["is_hit"].sum())
    n_hits_essential = int((m["is_hit"] & m["is_essential"]).sum())
    return {
        "auroc_no_essential": _auroc(pos, neg),
        "n_pos_no_essential": int(len(pos)),
        "n_neg_no_essential": int(len(neg)),
        "n_hits_total": n_hits,
        "n_hits_essential": n_hits_essential,
        "frac_hits_essential": (n_hits_essential / n_hits) if n_hits else float("nan"),
    }


def permutation_p(merged: pd.DataFrame, observed_auroc: float,
                  n_perm: int = PERM_N, seed: int = PERM_SEED) -> float:
    """Two-sided permutation p for the AUROC: shuffle the is_hit labels over the
    fixed set of ranks, recompute AUROC, count how often |AUROC-0.5| >= observed."""
    m = merged.dropna(subset=["primary_rank"]).copy()
    if np.isnan(observed_auroc):
        return float("nan")
    is_hit = (m["fdr"] < FDR_HIT_THRESHOLD).to_numpy()
    score = (-m["primary_rank"]).to_numpy()
    n_pos = int(is_hit.sum())
    if n_pos == 0 or n_pos == len(is_hit):
        return float("nan")
    rng = np.random.default_rng(seed)
    obs_dev = abs(observed_auroc - 0.5)
    idx = np.arange(len(score))
    count = 0
    for _ in range(n_perm):
        perm = rng.permutation(idx)[:n_pos]
        mask = np.zeros(len(score), dtype=bool)
        mask[perm] = True
        a = _auroc(score[mask], score[~mask])
        if abs(a - 0.5) >= obs_dev:
            count += 1
    return (count + 1) / (n_perm + 1)


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
def magnitude_concordance(ranking: pd.DataFrame, contract: pd.DataFrame) -> dict:
    """Exploratory (POST-HOC, not the pre-registered test): correlate our transcriptional
    footprint MAGNITUDE (n_hits, the axis the AUROC-0.85 calibration was built on) with
    the screen's hit significance. `primary_rank` ranks DIRECTIONALITY, a different axis;
    this asks whether footprint breadth tracks activation-screen significance at all."""
    from scipy.stats import spearmanr

    c = contract.rename(columns={"gene": "target_gene"}).copy()
    c["neglog_fdr"] = -np.log10(pd.to_numeric(c["fdr"], errors="coerce").clip(lower=1e-320))
    m = ranking.merge(c[["target_gene", "neglog_fdr"]], on="target_gene", how="inner")
    m = m.dropna(subset=["n_hits", "neglog_fdr"])
    if len(m) < 3:
        return {"rho": float("nan"), "p": float("nan"), "n": int(len(m))}
    rho, p = spearmanr(m["n_hits"], m["neglog_fdr"])
    return {"rho": float(rho), "p": float(p), "n": int(len(m))}


def essential_dropout_among_top_hits(ranking: pd.DataFrame, contract: pd.DataFrame,
                                     essentials: set[str], top_n: int = 50) -> dict:
    """Of the screen's TOP-N most-significant hits, how many are (a) Hart core-essential
    and (b) absent from our ranking entirely (i.e. lost to viability dropout in our
    Perturb-seq screen)? Explains why phenotype-matched enrichment can be null."""
    c = contract.copy()
    top = c.sort_values("fdr").head(top_n)
    ranked = set(ranking["target_gene"])
    genes = top["gene"].astype(str)
    n_ess = int(genes.str.upper().isin(essentials).sum())
    n_absent = int((~genes.isin(ranked)).sum())
    return {"top_n": int(len(top)), "n_essential": n_ess, "n_absent_from_ranking": n_absent}


def run_one(name: str, contract: pd.DataFrame, ranking: pd.DataFrame,
            essentials: set[str]) -> dict:
    res = crosscheck(ranking, contract)
    conf = auroc_excluding_essentials(res["merged"], essentials)
    perm_p = permutation_p(res["merged"], res["auroc"])
    mag = magnitude_concordance(ranking, contract)
    drop = essential_dropout_among_top_hits(ranking, contract, essentials)
    return {"name": name, "res": res, "conf": conf, "perm_p": perm_p,
            "mag": mag, "drop": drop}


def format_report(runs: list[dict]) -> str:
    L = []
    L.append("# Track D — Phenotype-matched activation-screen cross-checks (ACTUAL RUN)")
    L.append("")
    L.append("Real run of the phenotype-matched external cross-check "
             "(`perturbation_validation_plan.md` §5b P1) against activation-phenotype "
             "CRISPR screens cached in `metadata/`. Generated by "
             "`run_activation_crosschecks.py`. Every number below is computed live; "
             "nulls are reported as-is.")
    L.append("")
    L.append("**Acceptance criterion (from the plan):** AUROC ≥ 0.65 with permutation "
             "p < 0.05, plus flagship direction agreement. A gene is an external 'hit' at "
             f"fdr < {FDR_HIT_THRESHOLD}. AUROC score = inverted `primary_rank` (top-ranked "
             "= high), so AUROC > 0.5 means our top-ranked genes are enriched among the "
             "screen's activation hits.")
    L.append("")
    L.append("**Confound control:** each AUROC is recomputed after dropping Hart "
             "core-essential genes, to check the signal is not merely generic "
             "essential/proliferation biology.")
    L.append("")
    L.append("| Screen | modality | n merged | AUROC | perm p | AUROC (no essentials) | hits that are essential | flagship dir. |")
    L.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for r in runs:
        res, conf = r["res"], r["conf"]
        fe = f"{conf['n_hits_essential']}/{conf['n_hits_total']}" if conf["n_hits_total"] else "0/0"
        dir_s = (f"{res['direction_n_agree']}/{res['direction_n_total']}"
                 if res["direction_n_total"] else "n/a")
        L.append(
            f"| {r['name']} | {r['modality']} | {res['n_merged']} | "
            f"{res['auroc']:.3f} | {r['perm_p']:.2g} | "
            f"{conf['auroc_no_essential']:.3f} | {fe} | {dir_s} |"
        )
    L.append("")
    for r in runs:
        res, conf = r["res"], r["conf"]
        L.append(f"## {r['name']} ({r['modality']})")
        L.append(f"- genes present in both tables: **{res['n_merged']}**")
        L.append(f"- rank–rank Spearman (primary_rank vs |lfc|): rho = {res['spearman_rho']:.4f}, "
                 f"p = {res['spearman_p']:.3g}, n = {res['spearman_n']} "
                 f"(a good ranking → **negative** rho)")
        L.append(f"- top-N enrichment **AUROC = {res['auroc']:.4f}** "
                 f"(n_pos={res['auroc_n_pos']} hits, n_neg={res['auroc_n_neg']}), "
                 f"Mann-Whitney p = {res['mannwhitney_p']:.3g}, permutation p = {r['perm_p']:.3g}")
        L.append(f"- confound control — AUROC excluding {conf['n_hits_essential']} "
                 f"essential hits: **{conf['auroc_no_essential']:.4f}** "
                 f"(n_pos={conf['n_pos_no_essential']}, n_neg={conf['n_neg_no_essential']}); "
                 f"{conf['n_hits_essential']}/{conf['n_hits_total']} of the screen hits are "
                 f"Hart core-essential")
        mag, drop = r["mag"], r["drop"]
        L.append(f"- **post-hoc** magnitude concordance (our footprint breadth `n_hits` vs "
                 f"screen −log10 fdr): Spearman rho = {mag['rho']:.4f}, p = {mag['p']:.3g}, "
                 f"n = {mag['n']} — a *different, exploratory* axis from the pre-registered "
                 f"directionality AUROC above")
        L.append(f"- essential dropout among the screen's top-{drop['top_n']} hits: "
                 f"{drop['n_essential']} are Hart core-essential and "
                 f"{drop['n_absent_from_ranking']} are absent from our ranking entirely "
                 f"(lost to viability dropout in our Perturb-seq screen)")
        if res["direction_n_total"]:
            L.append(f"- flagship direction agreement: {res['direction_n_agree']}/"
                     f"{res['direction_n_total']}")
            for g, our, hit, agree in res["direction_detail"]:
                L.append(f"  - {g}: our signed_net sign={our:+d}, screen hit_direction={hit:+d}, agree={agree}")
        L.append("")
    L.append("## Honest framing")
    L.append("**Corroborative, not confirmatory** (same tier as Tracks A–C in "
             "`LEVEL4_EXTERNAL_VALIDATION.md`). These are two independently-generated "
             "activation screens using a *different method* (arrayed/pooled CRISPRi) than "
             "our Perturb-seq; agreement is consistent with — but does not prove — that "
             "the signed ranking captures causal drivers of T-cell activation (that is L5). "
             "Direction semantics differ between `signed_net` (transcriptional derepression "
             "on KO) and the screen's marker `hit_direction` (activation change on "
             "knockdown), so the flagship direction column is a coarse diagnostic, not a "
             "strict test. Shifrut 2018 could not be run here (not cached; NCBI/Cell blocked "
             "by the sandbox network policy) — the generic harness stays turn-key for it.")
    return "\n".join(L) + "\n"


def main() -> int:
    if not RANKING.exists():
        print(f"ERROR: ranking not found: {RANKING}", file=sys.stderr)
        return 1
    ranking = pd.read_csv(RANKING, comment="#")
    essentials = load_essentials()

    specs = [
        ("Schmidt2022 CD4+ IL2", "CRISPRi", lambda: load_schmidt("CD4+ IL2")),
        ("Schmidt2022 CD8+ IFNG", "CRISPRi", lambda: load_schmidt("CD8+ IFNG")),
        ("Freimer2022 (IL2/IL2RA/CTLA4)", "CRISPR-KO", load_freimer),
    ]

    runs = []
    for name, modality, loader in specs:
        contract = loader()
        if contract is None or contract.empty:
            print(f"SKIP {name}: cached screen file missing/empty — not fabricated.")
            continue
        r = run_one(name, contract, ranking, essentials)
        r["modality"] = modality
        runs.append(r)
        res = r["res"]
        print(f"[{name}] merged={res['n_merged']} AUROC={res['auroc']:.4f} "
              f"perm_p={r['perm_p']:.3g} AUROC_noEss={r['conf']['auroc_no_essential']:.4f} "
              f"dir={res['direction_n_agree']}/{res['direction_n_total']}")

    if not runs:
        print("No activation screens available — nothing run (honest SKIP).")
        return 0

    # canonical single-screen harness output = the cleanest modality match (Schmidt CD4 IL2)
    primary = next((r for r in runs if r["name"].startswith("Schmidt2022 CD4")), runs[0])
    write_outputs(primary["res"], out_csv=OUT_CSV, out_md=OUT_MD)

    COMBINED_MD.write_text(format_report(runs))
    # tidy machine-readable summary
    rows = []
    for r in runs:
        res, conf = r["res"], r["conf"]
        rows.append({
            "screen": r["name"], "modality": r["modality"], "n_merged": res["n_merged"],
            "spearman_rho": res["spearman_rho"], "spearman_p": res["spearman_p"],
            "auroc": res["auroc"], "mannwhitney_p": res["mannwhitney_p"], "perm_p": r["perm_p"],
            "auroc_no_essential": conf["auroc_no_essential"],
            "n_hits_total": conf["n_hits_total"], "n_hits_essential": conf["n_hits_essential"],
            "magnitude_rho": r["mag"]["rho"], "magnitude_p": r["mag"]["p"],
            "top50_essential": r["drop"]["n_essential"],
            "top50_absent_from_ranking": r["drop"]["n_absent_from_ranking"],
            "direction_agree": res["direction_n_agree"], "direction_total": res["direction_n_total"],
        })
    pd.DataFrame(rows).to_csv(COMBINED_CSV, index=False)
    print(f"wrote {COMBINED_MD}")
    print(f"wrote {COMBINED_CSV}")
    print(f"wrote {OUT_CSV} / {OUT_MD} (canonical single-screen = {primary['name']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
