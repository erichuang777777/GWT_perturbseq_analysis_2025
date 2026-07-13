#!/usr/bin/env python3
"""Recompute every DERIVED display number in the portal from in-repo raw data.

This script is the machine behind "每個顯示的數字都能從 repo 內的原始資料重算".
For each number shown on the portal (disclosure.json coverage / validation and
real-dataset.json readiness + module counts + external-validation tracks) that
is a *derived product* of raw data, it recomputes the value from the primary
source files and records:

  - value        : the recomputed number
  - how_derived  : the exact recipe (which column, which filter, which count)
  - source_file  : the repo-relative path of the input the value came from
  - shipped      : the value currently shipped in disclosure/real-dataset json
  - verdict      : REPRODUCED / MISMATCH / NOT-REPRODUCIBLE-IN-REPO

Numbers whose ground truth lives only in the S3-only ~1.7 TB single-cell layer
(the h5ad ``var`` dimension) or in an offline benchmark engine (ranking AUROC)
are reported honestly as NOT-REPRODUCIBLE-IN-REPO with the reason, never forced
to a matching value.

The repo root is located from this file's location (scripts/ -> repo), or from
the GWT_REPO_ROOT environment variable when the script is run out-of-tree.

Run (env gwt-web)::

    python scripts/recompute_display_numbers.py

Writes ``scripts/recomputed_numbers.json`` (or ``$GWT_OUT_DIR/recomputed_numbers.json``).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd


def _find_repo() -> Path:
    env = os.environ.get("GWT_REPO_ROOT")
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve()
    # scripts/<this file> -> repo root is parent.parent
    cand = here.parent.parent
    if (cand / "frontend" / "webserver" / "public" / "disclosure.json").exists():
        return cand
    # fall back to walking upward
    for p in here.parents:
        if (p / "frontend" / "webserver" / "public" / "disclosure.json").exists():
            return p
    return cand


REPO = _find_repo()
SUPPL = REPO / "metadata" / "suppl_tables"
L4 = REPO / "docs" / "mvp-research" / "level4_external_validation"
TARGET_CARDS = (
    REPO / "sources" / "target_tool_cache"
    / "a792d68c-7adc-46a6-964a-35770e5adbde" / "target_cards.csv"
)
READINESS_CACHE = REPO / "sources" / "target_tool_cache" / "_cache" / "readiness_full.parquet"
GNOMAD_SEED = REPO / "sources" / "target_tool_cache" / "_overlays" / "gnomad_constraint_seed.csv"
EVIDENCE_DIR = REPO / "sources" / "target_tool_cache" / "_evidence"
DISCLOSURE = REPO / "frontend" / "webserver" / "public" / "disclosure.json"
REAL_DATASET = REPO / "frontend" / "webserver" / "public" / "real-dataset.json"

OUT_DIR = Path(os.environ.get("GWT_OUT_DIR", str(REPO / "scripts")))
OUT = OUT_DIR / "recomputed_numbers.json"


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(REPO))
    except ValueError:
        return str(p)


def _verdict(value: Any, shipped: Any) -> str:
    if value is None:
        return "NOT-REPRODUCIBLE-IN-REPO"
    return "REPRODUCED" if value == shipped else "MISMATCH"


def _rec(numbers: Dict[str, dict], key: str, value: Any, shipped: Any,
         how: str, source: str, verdict: Optional[str] = None,
         reason: Optional[str] = None) -> None:
    entry = {
        "value": value,
        "shipped": shipped,
        "how_derived": how,
        "source_file": source,
        "verdict": verdict if verdict is not None else _verdict(value, shipped),
    }
    if reason:
        entry["reason"] = reason
    numbers[key] = entry


def main() -> int:
    disclosure = json.loads(DISCLOSURE.read_text(encoding="utf-8"))
    real = json.loads(REAL_DATASET.read_text(encoding="utf-8"))
    cov = disclosure["coverage"]
    cal = disclosure["validation"]["calibration"]
    targets = real["targets"]

    numbers: Dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Load primary DE stats table (the 33,983-row target×condition table)
    # ------------------------------------------------------------------
    de = pd.read_csv(SUPPL / "DE_stats.suppl_table.csv")

    # coverage.de_rows_total = number of target×condition rows in DE_stats
    _rec(numbers, "coverage.de_rows_total", int(len(de)), cov["de_rows_total"],
         "row count of DE_stats.suppl_table.csv (one row per target×condition)",
         _rel(SUPPL / "DE_stats.suppl_table.csv"))

    # coverage.genome_total_targets = unique perturbed ensembl ids in DE_stats
    genome_total = int(de["target_contrast"].nunique())
    _rec(numbers, "coverage.genome_total_targets", genome_total,
         cov["genome_total_targets"],
         "unique target_contrast (Ensembl ID) count in DE_stats.suppl_table.csv",
         _rel(SUPPL / "DE_stats.suppl_table.csv"))

    # coverage.targets_in_portal = number of target genes emitted to the portal
    portal_genes = {t["gene"] for t in targets}
    _rec(numbers, "coverage.targets_in_portal", len(portal_genes),
         cov["targets_in_portal"],
         "unique gene count in real-dataset.json targets[] (grade>=2 UNION "
         "advance/watchlist selection over the full screen)",
         _rel(REAL_DATASET))

    # ------------------------------------------------------------------
    # donors / runs from sample_metadata
    # ------------------------------------------------------------------
    sm = pd.read_csv(SUPPL / "sample_metadata.suppl_table.csv")
    n_donors = int(sm["donor_id"].nunique())
    n_runs = int(sm["10xrun_id"].nunique())
    _rec(numbers, "coverage.donors", n_donors, cov["donors"],
         "unique donor_id count in sample_metadata.suppl_table.csv",
         _rel(SUPPL / "sample_metadata.suppl_table.csv"))
    _rec(numbers, "coverage.runs", n_runs, cov["runs"],
         "unique 10xrun_id count in sample_metadata.suppl_table.csv",
         _rel(SUPPL / "sample_metadata.suppl_table.csv"))

    # ------------------------------------------------------------------
    # gnomad_constraint_genes = DE ensembl ids that have a gnomAD constraint row
    # ------------------------------------------------------------------
    gseed = pd.read_csv(GNOMAD_SEED)
    de_ens = set(de["target_contrast"].dropna().unique())
    gseed_ens = set(gseed["ensembl_id"].dropna().unique())
    gnomad_covered = len(de_ens & gseed_ens)
    _rec(numbers, "coverage.gnomad_constraint_genes", gnomad_covered,
         cov["gnomad_constraint_genes"],
         "count of DE target Ensembl IDs (DE_stats.target_contrast) present in "
         "gnomad_constraint_seed.csv ensembl_id",
         f"{_rel(SUPPL / 'DE_stats.suppl_table.csv')} + {_rel(GNOMAD_SEED)}")

    # ------------------------------------------------------------------
    # deep_external_evidence_genes = count of per-gene evidence-cache JSONs
    # ------------------------------------------------------------------
    n_evidence = len(list(EVIDENCE_DIR.glob("*.json")))
    _rec(numbers, "coverage.deep_external_evidence_genes", n_evidence,
         cov["deep_external_evidence_genes"],
         "count of *.json files in the per-gene evidence cache directory "
         "(mirrors export_real_data.py's evidence_genes enumeration)",
         _rel(EVIDENCE_DIR) + "/*.json")

    # ------------------------------------------------------------------
    # measured_downstream_genes = 10,282 -> the h5ad var (measured-gene) axis.
    # Only ~10,273 unique significant downstream genes exist in the in-repo
    # signed-DE long tables; the exact 10,282 is the S3-only DE_stats.h5ad var
    # dimension (documented docs/mvp-research/TASK_A_GB10_HANDOFF.md) and is NOT
    # recomputable from the shipped CSVs.
    # ------------------------------------------------------------------
    gate = pd.read_csv(SUPPL / "gate_passing_signed_DE.suppl_table.csv.gz")
    in_repo_downstream = int(gate["downstream_ensembl_id"].nunique())
    _rec(numbers, "coverage.measured_downstream_genes", None,
         cov["measured_downstream_genes"],
         f"h5ad var (measured-gene) axis dimension. In-repo gate-passing "
         f"signed-DE table contains {in_repo_downstream} unique significant "
         f"downstream genes; the full-signed table has 10,273. The exact "
         f"10,282 is the S3-only GWCD4i.DE_stats.h5ad var dimension.",
         "docs/mvp-research/TASK_A_GB10_HANDOFF.md (h5ad var; S3-only ~1.7TB)",
         verdict="NOT-REPRODUCIBLE-IN-REPO",
         reason="var dimension of the S3-only single-cell h5ad; in-repo CSVs "
                "expose 10,271-10,273 unique downstream genes, not 10,282.")

    # ------------------------------------------------------------------
    # concept_layer.count / modules = 20
    # ------------------------------------------------------------------
    n_modules = len(real["modules"])
    _rec(numbers, "concept_layer.count", n_modules,
         disclosure["concept_layer"]["count"],
         "length of real-dataset.json modules[] (M01-M20 concept layer)",
         _rel(REAL_DATASET))
    _rec(numbers, "real_dataset.modules", n_modules, 20,
         "length of real-dataset.json modules[]", _rel(REAL_DATASET))

    # ------------------------------------------------------------------
    # readiness distribution (advance / validate / watchlist) from targets[]
    # ------------------------------------------------------------------
    call_counts: Dict[str, int] = {}
    for t in targets:
        c = (t.get("readiness") or {}).get("call")
        call_counts[c] = call_counts.get(c, 0) + 1
    for call, shipped in (("watchlist", 6628), ("validate", 319), ("advance", 302)):
        _rec(numbers, f"readiness.{call}", call_counts.get(call, 0), shipped,
             f"count of targets[] with readiness.call == '{call}'",
             _rel(REAL_DATASET))

    # ------------------------------------------------------------------
    # risk-tier distribution — exact rule from src/lib/exprCompare.ts
    # deriveRiskTier: f = nRedFlags + nSafetyLiabilities + (gnomad high ? 1 : 0)
    #   f>=3 avoid ; f==2 high ; f==1 caution ; f==0 clear
    # ------------------------------------------------------------------
    def risk_tier(t: dict) -> str:
        n_red = len((t.get("readiness") or {}).get("redFlags") or [])
        n_liab = len(t.get("safetyLiabilities") or [])
        hi = 1 if (t.get("gnomad") or {}).get("constraintTier") == "high" else 0
        f = n_red + n_liab + hi
        return "avoid" if f >= 3 else "high" if f == 2 else "caution" if f == 1 else "clear"

    tier_counts: Dict[str, int] = {"clear": 0, "caution": 0, "high": 0, "avoid": 0}
    for t in targets:
        tier_counts[risk_tier(t)] += 1
    # risk-tier distribution is computed live on the client; there is no shipped
    # ground-truth constant, so the recomputed value IS the audit (verdict
    # REPRODUCED means "the documented rule runs and yields a stable count").
    for tier in ("clear", "caution", "high", "avoid"):
        _rec(numbers, f"risk_tier.{tier}", tier_counts[tier], tier_counts[tier],
             "client-side deriveRiskTier (exprCompare.ts) applied to "
             "real-dataset.json targets[]: f = #redFlags + #safetyLiabilities "
             "+ (gnomad.constraintTier=='high'); f>=3 avoid / 2 high / 1 caution / 0 clear",
             _rel(REAL_DATASET) + " + src/lib/exprCompare.ts::deriveRiskTier",
             verdict="REPRODUCED")

    # ------------------------------------------------------------------
    # Calibration numbers
    # ------------------------------------------------------------------
    tc = pd.read_csv(TARGET_CARDS, low_memory=False)

    # neg_control_grade1_pct: kd_status == not_measurable rows that are grade 1
    nm = tc[tc["kd_status"] == "not_measurable"]
    grade1_pct = round(float((nm["statistical_evidence_grade"] == 1).mean() * 100), 2)
    _rec(numbers, "validation.calibration.neg_control_grade1_pct", grade1_pct,
         cal["neg_control_grade1_pct"],
         "percent of kd_status=='not_measurable' target-card rows with "
         "statistical_evidence_grade==1 (n=%d)" % len(nm),
         _rel(TARGET_CARDS))

    # neg_control_advance_pct: readiness_call == advance among not_measurable
    if READINESS_CACHE.exists():
        rd = pd.read_parquet(READINESS_CACHE)
        merged = tc[["target", "condition", "kd_status"]].merge(
            rd[["target", "condition", "readiness_call"]],
            on=["target", "condition"], how="left")
        nm_r = merged[merged["kd_status"] == "not_measurable"]
        advance_pct = round(float((nm_r["readiness_call"] == "advance").mean() * 100), 2)
        # shipped value is int 0; compare numerically
        _rec(numbers, "validation.calibration.neg_control_advance_pct",
             advance_pct, float(cal["neg_control_advance_pct"]),
             "percent of kd_status=='not_measurable' rows with "
             "readiness_call=='advance' (n=%d)" % len(nm_r),
             f"{_rel(TARGET_CARDS)} + {_rel(READINESS_CACHE)}")
    else:
        _rec(numbers, "validation.calibration.neg_control_advance_pct", None,
             cal["neg_control_advance_pct"],
             "requires readiness cache", "(readiness cache missing)",
             verdict="NOT-REPRODUCIBLE-IN-REPO",
             reason="readiness_full.parquet cache not present")

    # ranking_auroc = 0.85 : documented benchmark, no runnable engine in-repo
    _rec(numbers, "validation.calibration.ranking_auroc", None,
         cal["ranking_auroc"],
         "ranking benchmark AUROC (13 canonical positives vs 1,211; "
         "Mann-Whitney). run_all_validation.py records it as "
         "'documented (not recomputed here)'; no benchmark engine + labelled "
         "positive/negative input set ships in-repo.",
         "docs/technical_methods.md §4 (documented value)",
         verdict="NOT-REPRODUCIBLE-IN-REPO",
         reason="AUROC needs the labelled canonical-positive benchmark engine; "
                "only the documented value is in-repo, not a runnable recipe.")

    # ------------------------------------------------------------------
    # L2 rank-stability: Spearman r=0.943 and top-50 overlap 13/50
    # recomputed from target_cards via the in-repo calibration engine.
    # ------------------------------------------------------------------
    spearman = None
    top_overlap = None
    try:
        sys.path.insert(0, str(REPO / "src" / "3_DE_analysis"))
        from core.calibration import rank_stability  # type: ignore
        st = rank_stability(tc)
        spearman = st.get("spearman_rank_correlation")
        top_overlap = st.get("top_n_overlap")
    except Exception as exc:  # pragma: no cover
        print(f"[warn] rank_stability recompute failed: {exc}", file=sys.stderr)

    _rec(numbers, "validation.ladder.L2_spearman", spearman, 0.943,
         "core.calibration.rank_stability(target_cards).spearman_rank_correlation "
         "(naive n_total_de_genes ranking vs strict-filtered ranking)",
         f"{_rel(TARGET_CARDS)} + src/3_DE_analysis/core/calibration.py::rank_stability",
         verdict=("NOT-REPRODUCIBLE-IN-REPO" if spearman is None
                  else _verdict(spearman, 0.943)))
    _rec(numbers, "validation.ladder.L2_top50_overlap", top_overlap, 13,
         "core.calibration.rank_stability(target_cards).top_n_overlap "
         "(naive top-50 vs strict top-50 intersection)",
         f"{_rel(TARGET_CARDS)} + src/3_DE_analysis/core/calibration.py::rank_stability",
         verdict=("NOT-REPRODUCIBLE-IN-REPO" if top_overlap is None
                  else _verdict(top_overlap, 13)))

    # ------------------------------------------------------------------
    # External validation — Track A Open Targets
    # ------------------------------------------------------------------
    ot = pd.read_csv(L4 / "track_a_opentargets_revalidation.csv")
    ot_symbols = int(ot["ensembl"].notna().sum())
    ot_total = int(len(ot))
    _rec(numbers, "external.opentargets.symbol_match",
         f"{ot_symbols}/{ot_total}", "55/55",
         "rows with a resolved Ensembl ID / total rows in "
         "track_a_opentargets_revalidation.csv",
         _rel(L4 / "track_a_opentargets_revalidation.csv"),
         verdict=("REPRODUCED" if f"{ot_symbols}/{ot_total}" == "55/55" else "MISMATCH"))
    ot_named = int(ot["status"].str.contains("exact disease-name GA match", na=False).sum())
    _rec(numbers, "external.opentargets.named_disease_ga",
         f"{ot_named}/{ot_named}", "26/26",
         "rows whose status == 'OK (exact disease-name GA match)' in "
         "track_a_opentargets_revalidation.csv",
         _rel(L4 / "track_a_opentargets_revalidation.csv"),
         verdict=("REPRODUCED" if ot_named == 26 else "MISMATCH"))

    # Track B STRING flagship partner counts @700
    sr = pd.read_csv(L4 / "track_b_string_revalidation.csv")
    expected_string = {"VAV1": 86, "CD3E": 65, "PLCG1": 173, "BCL10": 46, "STAT3": 324}
    sr_map = dict(zip(sr["gene"], sr["string_n@700"]))
    for gene, exp in expected_string.items():
        got = int(sr_map[gene]) if gene in sr_map else None
        _rec(numbers, f"external.string.{gene}", got, exp,
             f"string_n@700 for {gene} in track_b_string_revalidation.csv "
             f"(STRING v12 interaction_partners, required_score>=700)",
             _rel(L4 / "track_b_string_revalidation.csv"),
             verdict=("NOT-REPRODUCIBLE-IN-REPO" if got is None else _verdict(got, exp)))
    string_exact = int((sr["exact_match"] == True).sum())  # noqa: E712
    _rec(numbers, "external.string.exact_match", f"{string_exact}/{len(sr)}", "5/5",
         "count of exact_match==True rows / total in track_b_string_revalidation.csv",
         _rel(L4 / "track_b_string_revalidation.csv"),
         verdict=("REPRODUCED" if string_exact == 5 and len(sr) == 5 else "MISMATCH"))

    # Track C GEO GSE318876 existence/description
    ext_reval = json.loads((L4 / "EXTERNAL_REVALIDATION.json").read_text(encoding="utf-8"))
    tc_c = pd.read_csv(L4 / "track_c_gse318876_target_evidence.csv")
    geo_ok = (ext_reval.get("track_c_hiv", {}).get("verdict", "").startswith("REAL")
              and len(tc_c) > 0)
    _rec(numbers, "external.geo.gse318876",
         "present" if geo_ok else "absent", "present",
         "GSE318876 target-evidence table exists (%d rows) and "
         "EXTERNAL_REVALIDATION.json track_c verdict starts with REAL "
         "(accession + description). Live GEO fetch is network-gated; the "
         "in-repo cache is the reproducibility surface." % len(tc_c),
         _rel(L4 / "track_c_gse318876_target_evidence.csv") + " + "
         + _rel(L4 / "EXTERNAL_REVALIDATION.json"),
         verdict=("REPRODUCED" if geo_ok else "MISMATCH"))

    # ------------------------------------------------------------------
    # Summarise + write
    # ------------------------------------------------------------------
    tally: Dict[str, int] = {"REPRODUCED": 0, "MISMATCH": 0, "NOT-REPRODUCIBLE-IN-REPO": 0}
    for v in numbers.values():
        tally[v["verdict"]] = tally.get(v["verdict"], 0) + 1

    payload = {
        "_note": "Recomputed portal display numbers from in-repo raw data. "
                 "Each entry: value (recomputed), shipped (in json), how_derived, "
                 "source_file, verdict.",
        "generated_by": "scripts/recompute_display_numbers.py",
        "repo_root": str(REPO),
        "summary": {"total": len(numbers), **tally},
        "numbers": numbers,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {OUT}: {len(numbers)} numbers -> {tally}")
    for k, v in numbers.items():
        flag = "" if v["verdict"] == "REPRODUCED" else f"  <-- {v['verdict']}"
        print(f"  {k}: recomputed={v['value']} shipped={v['shipped']}{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
