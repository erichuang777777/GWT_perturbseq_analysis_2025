#!/usr/bin/env python3
"""
phenotype_matched_crosscheck.py
================================
WP1 (perturbation_validation_plan.md §5b) — Track D: phenotype-MATCHED external
CRISPR-screen cross-check for the signed target ranking.

Track C (`track_c_gse318876_target_evidence.csv`) is a genome-wide CD4+ CRISPR
screen, but it measures HIV infection, not T-cell activation — a phenotype
mismatch documented in `LEVEL4_EXTERNAL_VALIDATION.md`. This script strengthens
L4 by cross-checking the signed ranking against an external screen whose
phenotype IS T-cell activation / proliferation (e.g. Shifrut et al. 2018,
GSE119450; Schmidt et al. 2022, GSE190604; Freimer et al. 2022) — see
`perturbation_validation_plan.md` §5b P1 for the rationale.

Input contract for --external (NOT shipped in this repo; supply your own)
---------------------------------------------------------------------------
A CSV with (at minimum):
    gene          : str   HGNC gene symbol
    effect_score  : float magnitude of the activation/proliferation effect
                    (larger = bigger perturbation phenotype; sign is NOT
                    assumed to encode direction — direction is optional, see
                    `hit_direction` below)
    fdr           : float multiple-testing-corrected significance for the hit
                    call in the external screen
Optional:
    hit_direction : +1 / -1  (perturbing the gene INCREASES / DECREASES
                    activation). Used only for the flagship direction-agreement
                    check; genes lacking it are excluded from that one stat.

Honest assert-or-SKIP pattern (mirrors reproduce_signed_tracks.py)
--------------------------------------------------------------------
If --external is not given, or the path does not exist / cannot be read, the
script prints an explicit SKIP report describing the input contract above and
exits 0. It NEVER fabricates a Spearman rho, an AUROC, or a direction-agreement
fraction from absent data. When the external file IS present, every statistic
is computed only from the merged rows actually shared between the two tables;
no imputation.

Usage
-----
    python phenotype_matched_crosscheck.py --external <path/to/external_hits.csv>
    python phenotype_matched_crosscheck.py                       # -> SKIP report, exit 0

Outputs (written next to this script, only when --external is usable)
-----------------------------------------------------------------------
    track_d_phenotype_matched_crosscheck.csv  — per-gene merged rows
    track_d_phenotype_matched_crosscheck.md   — short honest summary
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr

HERE = Path(__file__).resolve().parent
DEFAULT_RANKING = HERE.parent / "signed_de_application" / "signed_ranking_v2.csv"
OUT_CSV = HERE / "track_d_phenotype_matched_crosscheck.csv"
OUT_MD = HERE / "track_d_phenotype_matched_crosscheck.md"

FLAGSHIPS = ["VAV1", "CD3E", "PLCG1", "LCK", "ZAP70"]
FDR_HIT_THRESHOLD = 0.1

REQUIRED_EXTERNAL_COLS = {"gene", "effect_score", "fdr"}

INPUT_CONTRACT = """\
Track D input contract (external activation-phenotype CRISPR screen hit table)
--------------------------------------------------------------------------------
A CSV with columns:
    gene          (str)   HGNC gene symbol
    effect_score  (float) magnitude of the activation/proliferation effect
    fdr           (float) multiple-testing-corrected significance
Optional:
    hit_direction (+1/-1) perturbation increases (+1) / decreases (-1) activation

Suggested public sources (see perturbation_validation_plan.md §5b P1):
    - Shifrut et al. 2018   GEO GSE119450  (primary human T-cell CRISPR-KO x
      TCR-stimulation proliferation/cytokine screen)
    - Schmidt et al. 2022   GEO GSE190604  (CRISPRa/i x IL-2/IFN-gamma
      regulators, primary CD4/CD8)
    - Freimer et al. 2022   (trans-regulatory network, primary CD4)

Pass the path via --external. This repo does NOT ship the external table —
it must be downloaded / prepared by the user from one of the sources above.
"""


# --------------------------------------------------------------------------- #
# Core, importable functions
# --------------------------------------------------------------------------- #
def load_external(path: str | Path) -> pd.DataFrame | None:
    """Load and lightly validate the external hit table. Returns None (never
    raises) if the file is missing or unreadable, so callers can SKIP honestly."""
    p = Path(path)
    if not p.exists() or not p.is_file():
        return None
    try:
        df = pd.read_csv(p)
    except Exception:
        return None
    missing = REQUIRED_EXTERNAL_COLS - set(df.columns)
    if missing:
        return None
    return df


def crosscheck(ranking_df: pd.DataFrame, external_df: pd.DataFrame) -> dict:
    """Compute the three Track D statistics from an inner merge of the signed
    ranking and the external activation-phenotype hit table on gene symbol.

    Returns a dict with:
        merged            : per-gene merged DataFrame (incl. is_hit, agrees_direction)
        n_merged          : number of genes present in BOTH tables
        spearman_rho, spearman_p, spearman_n   : rank-rank Spearman
        auroc, auroc_n_pos, auroc_n_neg, mannwhitney_p : top-N enrichment AUROC
        direction_n_agree, direction_n_total, direction_frac : flagship agreement
        direction_detail  : list of (gene, our_sign, hit_direction, agree) tuples
    """
    r = ranking_df.copy()
    e = external_df.copy()
    e = e.rename(columns={"gene": "target_gene"})

    merged = r.merge(e, on="target_gene", how="inner")
    n_merged = len(merged)

    result: dict = {"merged": merged, "n_merged": n_merged}

    # ---- (a) rank-rank Spearman: our primary_rank vs external effect magnitude
    # primary_rank is 1 = top (most polarised); effect_score magnitude, larger = bigger hit.
    # A "good" ranking would show top primary_rank (small integer) paired with
    # LARGE effect_score -> negative Spearman rho between primary_rank and effect_score,
    # equivalently POSITIVE rho between (-primary_rank) and effect_score. We report rho
    # for primary_rank vs effect_score directly and note the expected sign in the summary.
    sub = merged.dropna(subset=["primary_rank", "effect_score"])
    if len(sub) >= 2:
        rho, pval = spearmanr(sub["primary_rank"], sub["effect_score"])
    else:
        rho, pval = float("nan"), float("nan")
    result["spearman_rho"] = float(rho)
    result["spearman_p"] = float(pval)
    result["spearman_n"] = int(len(sub))

    # ---- (b) top-N enrichment AUROC via Mann-Whitney U identity
    # label = external is_hit (fdr < threshold); score = inverted rank (top rank = high score)
    # so that hits are expected to have HIGHER inverted-rank score if the ranking is good.
    merged["is_hit"] = merged["fdr"] < FDR_HIT_THRESHOLD
    scored = merged.dropna(subset=["primary_rank"]).copy()
    scored["inv_rank_score"] = -scored["primary_rank"]  # higher = more top-ranked
    pos = scored.loc[scored["is_hit"], "inv_rank_score"]
    neg = scored.loc[~scored["is_hit"], "inv_rank_score"]
    if len(pos) > 0 and len(neg) > 0:
        u_stat, mw_p = mannwhitneyu(pos, neg, alternative="two-sided")
        auroc = float(u_stat / (len(pos) * len(neg)))
    else:
        u_stat, mw_p, auroc = float("nan"), float("nan"), float("nan")
    result["auroc"] = auroc
    result["auroc_n_pos"] = int(len(pos))
    result["auroc_n_neg"] = int(len(neg))
    result["mannwhitney_u"] = float(u_stat) if not np.isnan(u_stat) else float("nan")
    result["mannwhitney_p"] = float(mw_p)

    # ---- (c) direction agreement for flagship hubs
    direction_detail = []
    n_agree = 0
    n_total = 0
    if "hit_direction" in merged.columns:
        flank = merged[merged["target_gene"].isin(FLAGSHIPS)].dropna(
            subset=["signed_net", "hit_direction"]
        )
        for _, row in flank.iterrows():
            our_sign = int(np.sign(row["signed_net"])) if row["signed_net"] != 0 else 0
            hit_dir = int(np.sign(row["hit_direction"])) if row["hit_direction"] != 0 else 0
            agree = bool(our_sign != 0 and our_sign == hit_dir)
            direction_detail.append((row["target_gene"], our_sign, hit_dir, agree))
            n_total += 1
            n_agree += int(agree)
    result["direction_n_agree"] = n_agree
    result["direction_n_total"] = n_total
    result["direction_frac"] = (n_agree / n_total) if n_total > 0 else float("nan")
    result["direction_detail"] = direction_detail

    merged["agrees_direction"] = merged["target_gene"].map(
        {g: a for g, _, _, a in direction_detail}
    ) if direction_detail else np.nan

    return result


def write_outputs(result: dict, out_csv: Path = OUT_CSV, out_md: Path = OUT_MD) -> None:
    merged = result["merged"]
    merged.to_csv(out_csv, index=False)

    lines = []
    lines.append("# Track D — Phenotype-matched external CRISPR-screen cross-check")
    lines.append("")
    lines.append(
        "Cross-check of `signed_ranking_v2.csv` against a user-supplied external "
        "**activation-phenotype** CRISPR screen hit table (e.g. Shifrut 2018 "
        "GSE119450 / Schmidt 2022 GSE190604 / Freimer 2022). This strengthens L4 "
        "by matching the phenotype axis (T-cell activation/proliferation), unlike "
        "Track C (GSE318876, HIV infection)."
    )
    lines.append("")
    lines.append(f"- Genes present in both tables (inner merge): **{result['n_merged']}**")
    lines.append("")
    lines.append("## (a) Rank-rank Spearman (primary_rank vs external effect_score)")
    lines.append(
        f"- rho = **{result['spearman_rho']:.4f}**, p = {result['spearman_p']:.4g}, "
        f"n = {result['spearman_n']}"
    )
    lines.append(
        "  - Note: primary_rank is 1=top; a ranking that agrees with the external "
        "screen is expected to show a **negative** rho (small rank paired with large "
        "effect magnitude)."
    )
    lines.append("")
    lines.append("## (b) Top-N enrichment AUROC (external hit, fdr < %.2f, vs inverted primary_rank)"
                  % FDR_HIT_THRESHOLD)
    lines.append(
        f"- AUROC = **{result['auroc']:.4f}** (Mann-Whitney U identity), "
        f"n_pos = {result['auroc_n_pos']}, n_neg = {result['auroc_n_neg']}, "
        f"Mann-Whitney p = {result['mannwhitney_p']:.4g}"
    )
    lines.append("")
    lines.append("## (c) Flagship-hub direction agreement (VAV1, CD3E, PLCG1, LCK, ZAP70)")
    if result["direction_n_total"] > 0:
        lines.append(
            f"- {result['direction_n_agree']}/{result['direction_n_total']} "
            f"({100 * result['direction_frac']:.1f}%) flagship hubs agree in sign "
            f"between `signed_net` and external `hit_direction`."
        )
        for g, our, hit, agree in result["direction_detail"]:
            lines.append(f"  - {g}: our_sign={our:+d}, external_hit_direction={hit:+d}, agree={agree}")
    else:
        lines.append(
            "- No flagship hubs had both a merged row and a `hit_direction` value "
            "(either not present in the external table, or `hit_direction` column "
            "was not supplied) — reported honestly as 0/0, not fabricated."
        )
    lines.append("")
    lines.append("## Honest framing")
    lines.append(
        "**Corroborative, not confirmatory.** As with Tracks A-C in "
        "`LEVEL4_EXTERNAL_VALIDATION.md`, agreement here is consistent with, but "
        "does not prove, that the signed ranking captures causal drivers of T-cell "
        "activation. Any null or weak result above is reported as-is — it is "
        "**not** smoothed over, re-run with different thresholds, or omitted. "
        "See `perturbation_validation_plan.md` §5b (P1) for the acceptance "
        "criterion this track was designed against (AUROC >= 0.65 with permutation "
        "p < 0.05, plus flagship direction agreement)."
    )
    out_md.write_text("\n".join(lines) + "\n")


def print_skip_report(external_arg: str | None) -> None:
    print("=" * 78)
    print("Track D phenotype-matched cross-check: SKIP")
    print("=" * 78)
    if external_arg is None:
        print("No --external path supplied.")
    else:
        print(f"--external {external_arg!r} was not usable (missing, unreadable, or "
              f"missing required columns {sorted(REQUIRED_EXTERNAL_COLS)}).")
    print()
    print(INPUT_CONTRACT)
    print("No CSV/MD output was written. No Spearman/AUROC/direction numbers were")
    print("fabricated. This is the honest assert-or-SKIP pattern (see")
    print("docs/mvp-research/perturbase_review/reproducibility/reproduce_signed_tracks.py).")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    ap.add_argument("--ranking", default=str(DEFAULT_RANKING),
                     help="path to signed_ranking_v2.csv")
    ap.add_argument("--external", default=None,
                     help="path to external activation-phenotype CRISPR screen hit table "
                          "(gene, effect_score, fdr[, hit_direction]); if omitted or "
                          "unreadable, prints a SKIP report and exits 0")
    args = ap.parse_args(argv)

    external_df = load_external(args.external) if args.external else None
    if external_df is None:
        print_skip_report(args.external)
        return 0

    ranking_path = Path(args.ranking)
    if not ranking_path.exists():
        print(f"ERROR: --ranking file not found: {ranking_path}", file=sys.stderr)
        return 1
    ranking_df = pd.read_csv(ranking_path, comment="#")

    result = crosscheck(ranking_df, external_df)
    # NOTE: pass the module-level output paths explicitly (looked up at call
    # time) rather than relying on write_outputs()'s default parameters, so
    # that tests can monkeypatch OUT_CSV/OUT_MD and have main() honour it.
    write_outputs(result, out_csv=OUT_CSV, out_md=OUT_MD)

    print("Track D phenotype-matched cross-check: COMPUTED")
    print(f"  merged genes           : {result['n_merged']}")
    print(f"  spearman rho (n={result['spearman_n']})   : {result['spearman_rho']:.4f} "
          f"(p={result['spearman_p']:.4g})")
    print(f"  AUROC (n_pos={result['auroc_n_pos']}, n_neg={result['auroc_n_neg']}) : "
          f"{result['auroc']:.4f} (Mann-Whitney p={result['mannwhitney_p']:.4g})")
    print(f"  flagship direction agreement : {result['direction_n_agree']}/"
          f"{result['direction_n_total']}")
    print(f"  wrote {OUT_CSV}")
    print(f"  wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
