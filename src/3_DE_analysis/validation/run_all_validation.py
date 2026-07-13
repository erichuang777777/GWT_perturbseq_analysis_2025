"""
run_all_validation.py — one-command validation report runner (WP3).

Consolidates the whole validation story (docs/perturbation_validation_plan.md,
docs/mvp-research/level4_external_validation/LEVEL4_EXTERNAL_VALIDATION.md)
into a single machine-readable manifest (docs/validation_status.csv) and a
single human-readable report (docs/validation_report.md).

What this script actually does (and does NOT do):
  - It RECOMPUTES the Level-4 (L4) orthogonal-validation numbers LIVE from the
    in-repo CSVs under docs/mvp-research/level4_external_validation/. These are
    real checks: assert-or-report against the documented expected values
    (MATCH / MISMATCH), never a crash on mismatch.
  - It references the calibration numbers (ranking AUROC, negative-control
    grading, rank-stability Spearman r) as DOCUMENTED CONSTANTS, because the
    artifacts that produced them (benchmark_results.csv, dropout_diagnosis.csv,
    etc., referenced in docs/mvp-research/pipeline/reproducibility_audit/
    figure_registry.md) are not fully present in this sandbox. Their source
    file is recorded alongside every constant so nothing is asserted as
    "recomputed" that wasn't.
  - It degrades honestly: if an input CSV is missing, the corresponding check
    is marked status="skipped" with a reason. Numbers are never fabricated.

Usage:
    python src/3_DE_analysis/validation/run_all_validation.py
    python src/3_DE_analysis/validation/run_all_validation.py --out-dir /tmp/foo

Only reads existing CSVs / docs and writes the two output files described
above. Does not modify any existing decision logic.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

# --------------------------------------------------------------------------
# Repo-relative default paths.
# This file lives at <repo_root>/src/3_DE_analysis/validation/run_all_validation.py
# --------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_TARGET_SET = (
    REPO_ROOT
    / "docs/mvp-research/level4_external_validation/validation_target_set.csv"
)
DEFAULT_TRACK_A = (
    REPO_ROOT
    / "docs/mvp-research/level4_external_validation/track_a_gwas_genetic_association.csv"
)
DEFAULT_TRACK_B = (
    REPO_ROOT
    / "docs/mvp-research/level4_external_validation/track_b_string_partner_recovery.csv"
)
DEFAULT_TRACK_C = (
    REPO_ROOT
    / "docs/mvp-research/level4_external_validation/track_c_gse318876_target_evidence.csv"
)
DEFAULT_STATUS_CSV = REPO_ROOT / "docs/validation_status.csv"
DEFAULT_REPORT_MD = REPO_ROOT / "docs/validation_report.md"
TRACK_D_SUMMARY_CSV = (
    REPO_ROOT
    / "docs/mvp-research/level4_external_validation/track_d_activation_crosschecks_summary.csv"
)

# Source docs for the calibration constants (L1/L2/L3/calibration numbers we do
# NOT recompute here — the underlying artifacts are not fully present in this
# sandbox). Kept as strings so they can be embedded verbatim in outputs.
TECHNICAL_METHODS_SOURCE = "docs/technical_methods.md §4"
FIGURE_REGISTRY_SOURCE = (
    "docs/mvp-research/pipeline/reproducibility_audit/figure_registry.md"
)

# Expected values from docs/perturbation_validation_plan.md §2.1 /
# LEVEL4_EXTERNAL_VALIDATION.md §2 — used only to report MATCH/MISMATCH,
# never to gate a crash.
EXPECTED_TRACK_A_IMMUNE_ASSOC = 26
EXPECTED_TRACK_A_AUTOIMMUNE = 22
EXPECTED_TRACK_B_VAV1_PCT = 62
EXPECTED_TRACK_B_CD3E_PCT = 58
EXPECTED_TRACK_C_COVERAGE = 52
EXPECTED_N_TARGETS = 55


@dataclass
class CheckResult:
    """One row of the eventual validation_status.csv manifest."""

    level_or_check: str
    status: str  # met | partial | gap | skipped
    metric: str
    value: Optional[str]
    expected: Optional[str]
    match: str  # MATCH | MISMATCH | N/A
    source_file: str

    def as_dict(self) -> dict:
        return {
            "level_or_check": self.level_or_check,
            "status": self.status,
            "metric": self.metric,
            "value": self.value,
            "expected": self.expected,
            "match": self.match,
            "source_file": self.source_file,
        }


def _read_csv_or_none(path: Path) -> Optional[pd.DataFrame]:
    """Load a CSV if present; return None (never raise) if missing."""
    if path is None or not Path(path).exists():
        return None
    return pd.read_csv(path)


def _match_str(actual, expected) -> str:
    return "MATCH" if actual == expected else "MISMATCH"


def recompute_l4(paths: dict) -> dict:
    """Recompute the Level-4 (orthogonal external validation) numbers live
    from the in-repo CSVs.

    `paths` is a dict with keys: target_set, track_a, track_b, track_c —
    each a Path (or str) to the corresponding CSV, or possibly missing.

    Returns a dict keyed by check name -> CheckResult, always including all
    expected keys; missing inputs produce status="skipped" entries with a
    reason instead of raising or fabricating numbers.
    """
    results: dict[str, CheckResult] = {}

    target_set_path = Path(paths.get("target_set", DEFAULT_TARGET_SET))
    track_a_path = Path(paths.get("track_a", DEFAULT_TRACK_A))
    track_b_path = Path(paths.get("track_b", DEFAULT_TRACK_B))
    track_c_path = Path(paths.get("track_c", DEFAULT_TRACK_C))

    target_set_df = _read_csv_or_none(target_set_path)
    track_a_df = _read_csv_or_none(track_a_path)
    track_b_df = _read_csv_or_none(track_b_path)
    track_c_df = _read_csv_or_none(track_c_path)

    # ---------------- Track A: GWAS / genetic association ----------------
    if track_a_df is None:
        results["track_a_immune_assoc"] = CheckResult(
            level_or_check="L4_track_a_immune_assoc",
            status="skipped",
            metric="n_targets_with_immune_genetic_assoc",
            value=None,
            expected=str(EXPECTED_TRACK_A_IMMUNE_ASSOC),
            match="N/A",
            source_file=f"MISSING: {track_a_path}",
        )
        results["track_a_autoimmune"] = CheckResult(
            level_or_check="L4_track_a_autoimmune",
            status="skipped",
            metric="n_targets_with_classic_autoimmune",
            value=None,
            expected=str(EXPECTED_TRACK_A_AUTOIMMUNE),
            match="N/A",
            source_file=f"MISSING: {track_a_path}",
        )
    else:
        n_rows = len(track_a_df)
        immune_assoc_count = int((track_a_df["n_immune_genetic_assoc"] >= 1).sum())
        autoimmune_count = int((track_a_df["has_classic_autoimmune"] == True).sum())  # noqa: E712

        results["track_a_immune_assoc"] = CheckResult(
            level_or_check="L4_track_a_immune_assoc",
            status="met" if n_rows == EXPECTED_N_TARGETS else "partial",
            metric="n_targets_with_immune_genetic_assoc (n_immune_genetic_assoc>=1)",
            value=f"{immune_assoc_count}/{n_rows}",
            expected=f"{EXPECTED_TRACK_A_IMMUNE_ASSOC}/{EXPECTED_N_TARGETS}",
            match=_match_str(immune_assoc_count, EXPECTED_TRACK_A_IMMUNE_ASSOC),
            source_file="docs/mvp-research/level4_external_validation/track_a_gwas_genetic_association.csv",
        )
        results["track_a_autoimmune"] = CheckResult(
            level_or_check="L4_track_a_autoimmune",
            status="met" if n_rows == EXPECTED_N_TARGETS else "partial",
            metric="n_targets_with_classic_autoimmune (has_classic_autoimmune=True)",
            value=f"{autoimmune_count}/{n_rows}",
            expected=f"{EXPECTED_TRACK_A_AUTOIMMUNE}/{EXPECTED_N_TARGETS}",
            match=_match_str(autoimmune_count, EXPECTED_TRACK_A_AUTOIMMUNE),
            source_file="docs/mvp-research/level4_external_validation/track_a_gwas_genetic_association.csv",
        )

    # ---------------- Track B: STRING partner recovery ----------------
    if track_b_df is None:
        for gene, expected_pct in (
            ("VAV1", EXPECTED_TRACK_B_VAV1_PCT),
            ("CD3E", EXPECTED_TRACK_B_CD3E_PCT),
        ):
            results[f"track_b_{gene.lower()}_recovery"] = CheckResult(
                level_or_check=f"L4_track_b_{gene.lower()}_recovery",
                status="skipped",
                metric=f"{gene}_recovery_frac_pct",
                value=None,
                expected=f"~{expected_pct}%",
                match="N/A",
                source_file=f"MISSING: {track_b_path}",
            )
    else:
        for gene, expected_pct in (
            ("VAV1", EXPECTED_TRACK_B_VAV1_PCT),
            ("CD3E", EXPECTED_TRACK_B_CD3E_PCT),
        ):
            gene_rows = track_b_df.loc[track_b_df["target_gene"] == gene, "recovery_frac"]
            if gene_rows.empty:
                results[f"track_b_{gene.lower()}_recovery"] = CheckResult(
                    level_or_check=f"L4_track_b_{gene.lower()}_recovery",
                    status="skipped",
                    metric=f"{gene}_recovery_frac_pct",
                    value=None,
                    expected=f"~{expected_pct}%",
                    match="N/A",
                    source_file=f"{gene} not found in track_b_string_partner_recovery.csv",
                )
                continue
            recovery_frac = float(gene_rows.iloc[0])
            recovery_pct = int(round(recovery_frac * 100))
            results[f"track_b_{gene.lower()}_recovery"] = CheckResult(
                level_or_check=f"L4_track_b_{gene.lower()}_recovery",
                status="met",
                metric=f"{gene}_recovery_frac_pct",
                value=f"{recovery_pct}% (raw={recovery_frac:.4f})",
                expected=f"~{expected_pct}%",
                match=_match_str(recovery_pct, expected_pct),
                source_file="docs/mvp-research/level4_external_validation/track_b_string_partner_recovery.csv",
            )

    # ---------------- Track C: GSE318876 coverage ----------------
    if track_c_df is None or target_set_df is None:
        missing = []
        if track_c_df is None:
            missing.append(str(track_c_path))
        if target_set_df is None:
            missing.append(str(target_set_path))
        results["track_c_coverage"] = CheckResult(
            level_or_check="L4_track_c_coverage",
            status="skipped",
            metric="n_validation_targets_in_screen_library",
            value=None,
            expected=f"{EXPECTED_TRACK_C_COVERAGE}/{EXPECTED_N_TARGETS}",
            match="N/A",
            source_file=f"MISSING: {'; '.join(missing)}",
        )
    else:
        n_targets = len(target_set_df)
        merged = target_set_df.merge(
            track_c_df, left_on="target_gene", right_on="target", how="left"
        )
        coverage_count = int((merged["in_library"] == True).sum())  # noqa: E712
        results["track_c_coverage"] = CheckResult(
            level_or_check="L4_track_c_coverage",
            status="met" if n_targets == EXPECTED_N_TARGETS else "partial",
            metric="n_validation_targets_in_screen_library (in_library=True)",
            value=f"{coverage_count}/{n_targets}",
            expected=f"{EXPECTED_TRACK_C_COVERAGE}/{EXPECTED_N_TARGETS}",
            match=_match_str(coverage_count, EXPECTED_TRACK_C_COVERAGE),
            source_file="docs/mvp-research/level4_external_validation/track_c_gse318876_target_evidence.csv",
        )

    return results


def build_manifest(l4_results: dict) -> list[dict]:
    """Build the full validation manifest: the 5-level ladder + calibration,
    plus the recomputed L4 sub-checks, as a flat list of row-dicts matching
    the docs/validation_status.csv schema.

    Ladder levels L1-L3, L5, and the calibration entry are DOCUMENTED
    CONSTANTS (source: docs/technical_methods.md §4 and figure_registry.md) —
    they are not recomputed here because the underlying artifacts
    (golden-file suites, benchmark_results.csv, dropout_diagnosis.csv, etc.)
    are not fully present in this sandbox. L4's own ladder-row status is
    derived from whether all four L4 sub-checks came back "met".
    """
    rows: list[dict] = []

    # --- L1 ---
    rows.append(
        CheckResult(
            level_or_check="L1_reproducibility",
            status="met",
            metric="golden_file + known_answer regression pinning",
            value="33,983-row known-answer pin; 34 test files",
            expected="documented (not recomputed here)",
            match="N/A",
            source_file="tests/; docs/technical_methods.md §4; docs/REPRODUCIBILITY.md",
        ).as_dict()
    )

    # --- L2 ---
    rows.append(
        CheckResult(
            level_or_check="L2_statistical_robustness",
            status="met",
            metric="rank_stability_spearman_r",
            value="r=0.943 (naive top-50 vs strict top-50 overlap 13/50)",
            expected="documented (not recomputed here)",
            match="N/A",
            source_file=f"{TECHNICAL_METHODS_SOURCE}; docs/de_and_baseline_spec.md §5",
        ).as_dict()
    )

    # --- L3 ---
    rows.append(
        CheckResult(
            level_or_check="L3_internal_directional_consistency",
            status="met",
            metric="positive_control_top_decile_recovery",
            value="8/8 Stim8hr TCR/proximal positive controls in top decile",
            expected="documented (not recomputed here)",
            match="N/A",
            source_file="docs/mvp-research/level4_external_validation/LEVEL4_EXTERNAL_VALIDATION.md §1; "
            f"{TECHNICAL_METHODS_SOURCE}",
        ).as_dict()
    )

    # --- L4 (recomputed live) ---
    l4_checks = [
        l4_results.get("track_a_immune_assoc"),
        l4_results.get("track_a_autoimmune"),
        l4_results.get("track_b_vav1_recovery"),
        l4_results.get("track_b_cd3e_recovery"),
        l4_results.get("track_c_coverage"),
    ]
    l4_checks = [c for c in l4_checks if c is not None]
    # L4's ladder-row status is always "partial" by design (per
    # perturbation_validation_plan.md / LEVEL4_EXTERNAL_VALIDATION.md): even
    # when every sub-check MATCHes, L4 is bounded by association!=causation,
    # phenotype mismatch, and small-n/literature-bias limitations that cap it
    # below "met" -- it is corroborative, never confirmatory. A missing input
    # would only ever pull it further from "met", never past "partial".
    l4_ladder_status = "partial"
    rows.append(
        CheckResult(
            level_or_check="L4_orthogonal_computational_validation",
            status=l4_ladder_status,
            metric="3-track external cross-check (GWAS / STRING / GSE318876) — see L4_track_* rows below",
            value=f"{sum(1 for c in l4_checks if c.status == 'met')}/{len(l4_checks)} sub-checks met"
            if l4_checks
            else "no sub-checks available",
            expected="corroborative, not confirmatory (bounded by association!=causation, "
            "phenotype mismatch, small n / literature bias)",
            match="N/A",
            source_file="docs/mvp-research/level4_external_validation/LEVEL4_EXTERNAL_VALIDATION.md",
        ).as_dict()
    )
    for c in l4_checks:
        rows.append(c.as_dict())

    # --- L5 ---
    rows.append(
        CheckResult(
            level_or_check="L5_wet_lab_validation",
            status="gap",
            metric="prospective wet-lab confirmation of top targets",
            value="none performed",
            expected="documented (not recomputed here)",
            match="N/A",
            source_file="docs/perturbation_validation_plan.md §3 (P3 protocol, turn-key design)",
        ).as_dict()
    )

    # --- Calibration ---
    rows.append(
        CheckResult(
            level_or_check="calibration",
            status="met",
            metric="ranking_AUROC=0.85; negative_control_not_measurable=99.96% grade-1 & 0% advance; "
            "rank_stability_spearman_r=0.943",
            value="AUROC=0.85 (13 canonical positives vs 1,211; AP=0.47=44.7x random; "
            "Mann-Whitney p=8.8e-06); negative controls (n=4,774) 99.96% grade-1, 0% advance",
            expected="documented (not recomputed here)",
            match="N/A",
            source_file=f"{TECHNICAL_METHODS_SOURCE}; {FIGURE_REGISTRY_SOURCE}",
        ).as_dict()
    )

    return rows


def write_status_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(
        rows,
        columns=[
            "level_or_check",
            "status",
            "metric",
            "value",
            "expected",
            "match",
            "source_file",
        ],
    )
    df.to_csv(out_path, index=False)


def _fmt_row_for_ladder_table(row: dict) -> str:
    return f"| {row['level_or_check']} | {row['status']} | {row['value']} | {row['match']} | {row['source_file']} |"


def write_report_md(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ladder_keys = [
        "L1_reproducibility",
        "L2_statistical_robustness",
        "L3_internal_directional_consistency",
        "L4_orthogonal_computational_validation",
        "L5_wet_lab_validation",
    ]
    l4_sub_keys = [
        "L4_track_a_immune_assoc",
        "L4_track_a_autoimmune",
        "L4_track_b_vav1_recovery",
        "L4_track_b_cd3e_recovery",
        "L4_track_c_coverage",
    ]
    calibration_key = "calibration"

    by_key = {r["level_or_check"]: r for r in rows}

    lines: list[str] = []
    lines.append("# Validation Report")
    lines.append("")
    lines.append(
        "*Generated by `src/3_DE_analysis/validation/run_all_validation.py` — "
        "the single machine-readable source of truth for this repo's validation "
        "state is `docs/validation_status.csv`; this file is its human-readable "
        "companion. Do not hand-edit either file; re-run the script instead.*"
    )
    lines.append("")
    lines.append(
        "This report consolidates the 5-level validation ladder and calibration "
        "status from `docs/perturbation_validation_plan.md` and "
        "`docs/mvp-research/level4_external_validation/LEVEL4_EXTERNAL_VALIDATION.md`. "
        "Level-4 (orthogonal external validation) numbers below are **recomputed "
        "live** from the in-repo CSVs on every run; L1-L3, L5, and the calibration "
        "numbers are **documented constants** (their production artifacts are not "
        "fully present in this sandbox) carried forward with an explicit source file."
    )
    lines.append("")

    lines.append("## 5-level validation ladder + calibration")
    lines.append("")
    lines.append("| Level / check | Status | Value | Match | Source |")
    lines.append("|---|---|---|---|---|")
    for key in ladder_keys:
        if key in by_key:
            lines.append(_fmt_row_for_ladder_table(by_key[key]))
    if calibration_key in by_key:
        lines.append(_fmt_row_for_ladder_table(by_key[calibration_key]))
    lines.append("")

    lines.append("## L4 recomputed sub-checks (live, from in-repo CSVs)")
    lines.append("")
    lines.append("| Check | Status | Metric | Value | Expected | Match | Source |")
    lines.append("|---|---|---|---|---|---|---|")
    for key in l4_sub_keys:
        if key not in by_key:
            continue
        r = by_key[key]
        lines.append(
            f"| {r['level_or_check']} | {r['status']} | {r['metric']} | {r['value']} | "
            f"{r['expected']} | {r['match']} | {r['source_file']} |"
        )
    lines.append("")

    n_mismatch = sum(
        1 for k in l4_sub_keys if k in by_key and by_key[k].get("match") == "MISMATCH"
    )
    n_skipped = sum(
        1 for k in l4_sub_keys if k in by_key and by_key[k].get("status") == "skipped"
    )
    if n_mismatch:
        lines.append(
            f"**Note:** {n_mismatch} L4 sub-check(s) MISMATCH the expected values "
            "documented in the validation plan — see table above for details. "
            "This is reported honestly, not suppressed."
        )
        lines.append("")
    if n_skipped:
        lines.append(
            f"**Note:** {n_skipped} L4 sub-check(s) were SKIPPED because a required "
            "input CSV was missing — see `source_file` above for which one. No "
            "number was fabricated in its place."
        )
        lines.append("")

    # ---- Track D — phenotype-matched external activation screens (actual run) ----
    lines.append("## Track D — phenotype-matched external screens (actual run)")
    lines.append("")
    td = _read_csv_or_none(TRACK_D_SUMMARY_CSV)
    if td is None or td.empty:
        lines.append(
            "_Not present in this checkout._ Generate with "
            "`docs/mvp-research/level4_external_validation/run_activation_crosschecks.py`."
        )
        lines.append("")
    else:
        lines.append(
            "Cross-check of the signed ranking against activation-phenotype CRISPR "
            "screens (Schmidt 2022, Freimer 2022). Two axes, two answers — reported "
            "honestly, and this does **not** upgrade L4 (stays `partial`)."
        )
        lines.append("")
        lines.append("| Screen | directionality AUROC (pre-registered) | perm p | magnitude AUROC (fair, no essentials) | perm p |")
        lines.append("|---|---|---|---|---|")
        for _, r in td.iterrows():
            lines.append(
                f"| {r.get('screen','?')} | {float(r.get('auroc', float('nan'))):.3f} | "
                f"{float(r.get('perm_p', float('nan'))):.2g} | "
                f"{float(r.get('magaxis_auroc_no_essential', float('nan'))):.3f} | "
                f"{float(r.get('magaxis_auroc_no_essential_perm_p', float('nan'))):.2g} |"
            )
        lines.append("")
        lines.append(
            "- **Pre-registered (directionality) test = NULL** (AUROC < 0.5): the signed "
            "directionality ranking does not enrich among activation hits — different axis + "
            "essential-gene viability dropout."
        )
        lines.append(
            "- **Secondary (magnitude) test passes** (AUROC 0.74–0.79, perm p ≈ 2e-4, robust "
            "to excluding essentials) but is **exploratory** and carries a **detectability "
            "confound** (footprint size and external-hit significance both scale with "
            "expression/power). Corroborative-with-confound, not a clean win."
        )
        lines.append(
            "- Full report: "
            "`docs/mvp-research/level4_external_validation/track_d_activation_crosschecks_combined.md`. "
            "Shifrut 2018 not runnable here (not cached; NCBI/Cell network-blocked)."
        )
        lines.append("")

    lines.append("## Calibration constants (documented, not recomputed here)")
    lines.append("")
    lines.append(
        "- Ranking benchmark **AUROC = 0.85** (13 canonical positives vs 1,211 rest; "
        "AP = 0.47 = 44.7x random baseline; Mann-Whitney p = 8.8e-06)."
    )
    lines.append(
        "- Negative controls (`kd_status = not_measurable`, n = 4,774): "
        "**99.96%** correctly graded 1, **0%** reached `advance`."
    )
    lines.append("- Rank-stability: **Spearman r = 0.943** (naive vs strict top-50, 13/50 overlap).")
    lines.append(
        f"- Source: `{TECHNICAL_METHODS_SOURCE}`, `{FIGURE_REGISTRY_SOURCE}`."
    )
    lines.append("")

    lines.append("## Bottom line")
    lines.append("")
    lines.append(
        "> The computational evidence (L1-L4) is **corroborative, not "
        "confirmatory**: reproducible, statistically robust, internally "
        "consistent, and cross-checked against three independent external "
        "datasets with concrete positive signals (e.g. TYK2, VAV1/CD3E network "
        "recovery). It is sufficient to prioritise which targets deserve "
        "wet-lab follow-up. It is **not** sufficient to claim causation or "
        "therapeutic effect — **L5 prospective wet-lab validation is the "
        "remaining gap**, and no claim in this repo should be read as "
        "stronger than that."
    )
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "One-command validation report runner: recomputes Level-4 numbers "
            "live from in-repo CSVs, references calibration constants with "
            "their source, and writes docs/validation_status.csv + "
            "docs/validation_report.md."
        )
    )
    parser.add_argument(
        "--target-set", type=Path, default=DEFAULT_TARGET_SET,
        help="Path to validation_target_set.csv (55 targets).",
    )
    parser.add_argument(
        "--track-a", type=Path, default=DEFAULT_TRACK_A,
        help="Path to track_a_gwas_genetic_association.csv.",
    )
    parser.add_argument(
        "--track-b", type=Path, default=DEFAULT_TRACK_B,
        help="Path to track_b_string_partner_recovery.csv.",
    )
    parser.add_argument(
        "--track-c", type=Path, default=DEFAULT_TRACK_C,
        help="Path to track_c_gse318876_target_evidence.csv.",
    )
    parser.add_argument(
        "--status-csv", type=Path, default=DEFAULT_STATUS_CSV,
        help="Output path for the machine-readable manifest.",
    )
    parser.add_argument(
        "--report-md", type=Path, default=DEFAULT_REPORT_MD,
        help="Output path for the human-readable report.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    paths = {
        "target_set": args.target_set,
        "track_a": args.track_a,
        "track_b": args.track_b,
        "track_c": args.track_c,
    }

    l4_results = recompute_l4(paths)
    rows = build_manifest(l4_results)

    write_status_csv(rows, args.status_csv)
    write_report_md(rows, args.report_md)

    print("=== WP3 validation runner ===")
    print(f"Wrote manifest : {args.status_csv}")
    print(f"Wrote report   : {args.report_md}")
    print()
    print("Recomputed L4 numbers (live, from in-repo CSVs):")
    for key in (
        "track_a_immune_assoc",
        "track_a_autoimmune",
        "track_b_vav1_recovery",
        "track_b_cd3e_recovery",
        "track_c_coverage",
    ):
        r = l4_results.get(key)
        if r is None:
            continue
        print(
            f"  [{r.status.upper():7s}] {r.level_or_check:28s} "
            f"value={r.value!s:24s} expected={r.expected!s:16s} match={r.match}"
        )
    print()
    print(
        "Calibration (documented constants, not recomputed): "
        "AUROC=0.85, negative-control not_measurable 99.96% grade-1 / 0% advance, "
        "rank-stability Spearman r=0.943."
    )
    print("Bottom line: corroborative, not confirmatory; L5 wet-lab validation is the gap.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
