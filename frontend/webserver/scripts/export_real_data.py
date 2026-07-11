#!/usr/bin/env python3
"""Export a real, non-mock dataset for the CD4 Target Discovery Portal frontend.

Reads directly from this repo's already-computed / already-fetched artifacts —
never invents a statistic, disease association, drug, or gene-name profile
value that isn't backed by one of these files:

  - sources/target_tool_cache/<run-id>/target_cards.csv
      Real per-target-per-condition statistics from the genome-scale CD4
      Perturb-seq screen (effect size, FDR, DE gene counts, grade, ...).
  - src/3_DE_analysis/core/readiness.py (compute_readiness)
      The repo's own deterministic readiness engine — run as-is, not
      reimplemented. Produces readiness_call / stage / reasons / next step.
  - src/3_DE_analysis/individual_concept_profile.py (load_concept_modules)
      The real M01-M20 immune concept module definitions (seed gene lists).
  - src/3_DE_analysis/concept_annotation.py (annotate_targets)
      Real "stimulation_gated" descriptive tagging.
  - sources/target_tool_cache/_evidence/<GENE>.json
      Real, already-fetched Open Targets / ClinicalTrials.gov / PubMed
      snapshots (tractability, disease associations, safety liabilities,
      clinical trials, literature) — the *only* genes this export selects
      are the ones this cache actually covers (21 genes), so the target
      list itself is not an arbitrary curation.
  - sources/target_tool_cache/_overlays/gnomad_constraint_seed.csv
      Real gnomAD v4 LOEUF / pLI constraint metrics.

Anything not present in these sources is emitted as JSON `null` (never a
fabricated 0 or placeholder), matching this project's own "unknown != 0"
discipline (see docs/architecture_refactor_plan.md, core/readiness.py).

Usage (from repo root):
    pip install pandas numpy pyyaml
    python3 frontend/webserver/scripts/export_real_data.py

Writes frontend/webserver/src/data/generated/real-dataset.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_3DE = REPO_ROOT / "src" / "3_DE_analysis"
sys.path.insert(0, str(SRC_3DE))

CARDS_CSV = REPO_ROOT / "sources" / "target_tool_cache" / "e7ecd8d5-5463-43e3-9bf1-6e8a15d3e137" / "target_cards.csv"
EVIDENCE_DIR = REPO_ROOT / "sources" / "target_tool_cache" / "_evidence"
GNOMAD_CSV = REPO_ROOT / "sources" / "target_tool_cache" / "_overlays" / "gnomad_constraint_seed.csv"
GENE_LISTS_DIR = REPO_ROOT / "metadata" / "gene_lists"
ESSENTIALS_TSV = GENE_LISTS_DIR / "core_essentials_hart.tsv"
BROAD_EFFECT_TXT = REPO_ROOT / "sources" / "broad_effect_genes.txt"

OUT_PATH = Path(__file__).resolve().parents[1] / "src" / "data" / "generated" / "real-dataset.json"

# Standard HGNC full names for the 21 genes this export covers. Public
# nomenclature, not evidence -- kept separate from every statistic/score
# below, all of which come from the files listed in the module docstring.
GENE_FULL_NAMES = {
    "CCNC": "Cyclin C",
    "CD247": "CD247 molecule (TCR zeta chain)",
    "CD28": "CD28 molecule",
    "CD3E": "CD3 epsilon subunit of T-cell receptor complex",
    "CTLA4": "Cytotoxic T-lymphocyte-associated protein 4",
    "DENR": "Density regulated re-initiation and release factor",
    "IL2RA": "Interleukin-2 receptor alpha (CD25)",
    "ITK": "IL2-inducible T-cell kinase",
    "JAK3": "Janus kinase 3",
    "LAT": "Linker for activation of T cells",
    "MED12": "Mediator complex subunit 12",
    "PLCG1": "Phospholipase C gamma 1",
    "PMVK": "Phosphomevalonate kinase",
    "SENP5": "SUMO-specific peptidase 5",
    "SGF29": "SAGA complex associated factor 29",
    "SUPT20H": "SPT20 homolog, SAGA complex component",
    "TADA1": "Transcriptional adaptor 1",
    "TADA2B": "Transcriptional adaptor 2B",
    "UBXN1": "UBX domain protein 1",
    "VAV1": "Vav guanine nucleotide exchange factor 1",
    "ZAP70": "Zeta-chain-associated protein kinase 70",
}

GRADE_LETTER = {4: "A", 3: "B", 2: "C", 1: "D"}


def nan_to_none(x):
    """NaN/NaT -> None, and numpy scalar -> native Python scalar (so json
    serializes real numbers instead of falling back to `default=str`)."""
    if x is None:
        return None
    try:
        if isinstance(x, float) and np.isnan(x):
            return None
        if pd.isna(x):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(x, np.generic):
        return x.item()
    return x


def load_evidence(gene: str) -> dict | None:
    p = EVIDENCE_DIR / f"{gene}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def main() -> None:
    from concept_annotation import annotate_targets
    from core.readiness import compute_readiness, load_overlays
    from data.loaders import load_gene_set
    from individual_concept_profile import load_concept_modules

    print(f"Loading real target cards from {CARDS_CSV}", file=sys.stderr)
    cards = pd.read_csv(CARDS_CSV)

    evidence_genes = sorted(p.stem for p in EVIDENCE_DIR.glob("*.json"))
    print(f"Evidence-cache genes ({len(evidence_genes)}): {evidence_genes}", file=sys.stderr)

    gene_cards = cards[cards["target"].isin(evidence_genes)].copy()
    print(f"target_cards rows for these genes: {len(gene_cards)}", file=sys.stderr)

    overlays = load_overlays(GENE_LISTS_DIR)
    essentials = load_gene_set(ESSENTIALS_TSV) if ESSENTIALS_TSV.exists() else set()
    broad_effect = load_gene_set(BROAD_EFFECT_TXT) if BROAD_EFFECT_TXT.exists() else set()

    def evidence_lookup(gene: str):
        return load_evidence(gene)

    print("Running the repo's real readiness engine (core.readiness.compute_readiness)...", file=sys.stderr)
    readiness = compute_readiness(
        gene_cards,
        overlays=overlays,
        essentials=essentials,
        broad_effect_genes=broad_effect,
        evidence_lookup=evidence_lookup,
    )

    print("Running real concept-module annotation (concept_annotation.annotate_targets)...", file=sys.stderr)
    modules = load_concept_modules()
    annotated = annotate_targets(gene_cards, modules=modules)

    gnomad = pd.read_csv(GNOMAD_CSV) if GNOMAD_CSV.exists() else pd.DataFrame(columns=["ensembl_id", "gene_symbol", "loeuf", "pli"])
    gnomad_by_gene = {r["gene_symbol"]: r for _, r in gnomad.iterrows()}

    module_by_gene: dict[str, list[dict]] = {}
    for m in modules:
        for g in m["seed_genes"]:
            module_by_gene.setdefault(g, []).append(m)

    targets_out = []
    for gene in evidence_genes:
        g_cards = gene_cards[gene_cards["target"] == gene]
        if g_cards.empty:
            print(f"  SKIP {gene}: no target_cards rows", file=sys.stderr)
            continue
        g_readiness = readiness[readiness["target"] == gene]
        g_annot = annotated[annotated["target"] == gene]

        # Primary condition = highest statistical_evidence_grade, tie-broken by lowest fdr_min.
        g_cards_sorted = g_cards.assign(
            _grade=pd.to_numeric(g_cards["statistical_evidence_grade"], errors="coerce").fillna(0),
            _fdr=pd.to_numeric(g_cards["fdr_min"], errors="coerce").fillna(1.0),
        ).sort_values(["_grade", "_fdr"], ascending=[False, True])
        primary_row = g_cards_sorted.iloc[0]
        primary_condition = primary_row["condition"]

        r_row_df = g_readiness[g_readiness["condition"] == primary_condition]
        r_row = r_row_df.iloc[0] if not r_row_df.empty else None

        conditions_out = []
        for _, crow in g_cards.iterrows():
            conditions_out.append({
                "condition": crow["condition"],
                "nTotalDeGenes": nan_to_none(crow.get("n_total_de_genes")),
                "nUpGenes": nan_to_none(crow.get("n_up_genes")),
                "nDownGenes": nan_to_none(crow.get("n_down_genes")),
                "maxAbsLogFC": nan_to_none(crow.get("max_abs_logFC")),
                "fdrMin": nan_to_none(crow.get("fdr_min")),
                "ontargetSignificant": bool(crow.get("ontarget_significant")) if not pd.isna(crow.get("ontarget_significant")) else None,
                "grade": nan_to_none(crow.get("statistical_evidence_grade")),
            })
        conditions_out.sort(key=lambda c: {"Rest": 0, "Stim8hr": 1, "Stim48hr": 2}.get(c["condition"], 9))

        annot_row_df = g_annot[g_annot["condition"] == primary_condition]
        stim_gated = None
        if not annot_row_df.empty and "stimulation_gated" in annot_row_df.columns:
            v = annot_row_df.iloc[0]["stimulation_gated"]
            stim_gated = bool(v) if not pd.isna(v) else None

        mods = module_by_gene.get(gene, [])
        primary_module = mods[0] if mods else None

        ev = load_evidence(gene) or {}
        ot = ev.get("sources", {}).get("open_targets", {})
        diseases = ot.get("associated_diseases", []) or []
        diseases_out = [
            {
                "name": d.get("disease"),
                "id": d.get("disease_id"),
                "overallScore": nan_to_none(d.get("overall_score")),
                "geneticAssociationScore": nan_to_none(d.get("genetic_association_score")),
            }
            for d in sorted(diseases, key=lambda d: d.get("overall_score") or 0, reverse=True)[:6]
        ]

        tract_flags = ot.get("tractability", []) or []
        modality_summary: dict[str, dict[str, bool]] = {}
        for t in tract_flags:
            mod = t.get("modality", "?")
            modality_summary.setdefault(mod, {})[t.get("label", "?")] = bool(t.get("value"))

        safety_liabilities = [
            {"event": s.get("event"), "tissues": s.get("tissues", [])}
            for s in (ot.get("safety_liabilities") or [])
        ]

        ct = ev.get("sources", {}).get("clinical_trials", {})
        trials_out = [
            {
                "nctId": t.get("nct_id"),
                "title": t.get("title"),
                "phase": t.get("phase"),
                "status": t.get("status"),
                "conditions": t.get("conditions", []),
                "url": t.get("url"),
            }
            for t in (ct.get("items") or [])
        ]

        lit = ev.get("sources", {}).get("literature", {})
        literature_out = [
            {"pmid": l.get("pmid"), "title": l.get("title"), "year": l.get("year"), "journal": l.get("journal"), "url": l.get("url")}
            for l in (lit.get("items") or [])[:5]
        ]

        gn = gnomad_by_gene.get(gene)
        loeuf = nan_to_none(gn["loeuf"]) if gn is not None else None
        pli = nan_to_none(gn["pli"]) if gn is not None else None
        constraint_tier = None
        if loeuf is not None:
            constraint_tier = "high" if loeuf < 0.35 else ("moderate" if loeuf < 0.6 else "low")

        grade_num = int(primary_row["_grade"]) if primary_row["_grade"] else None
        red_flags = []
        if r_row is not None and r_row.get("red_flag_override") not in (None, "none"):
            red_flags = str(r_row["red_flag_override"]).split(";")

        targets_out.append({
            "gene": gene,
            "name": GENE_FULL_NAMES.get(gene, gene),
            "ensembl": primary_row.get("target_id"),
            "module": {
                "id": primary_module["module_id"],
                "name": primary_module["module_name"],
                "category": primary_module["category"],
            } if primary_module else None,
            "allModules": [{"id": m["module_id"], "name": m["module_name"]} for m in mods],
            "primaryCondition": primary_condition,
            "grade": GRADE_LETTER.get(grade_num),
            "gradeNum": grade_num,
            "effect": nan_to_none(primary_row.get("max_abs_logFC")),
            "medianLogFC": nan_to_none(primary_row.get("median_logFC")),
            "fdr": nan_to_none(primary_row.get("fdr_min")),
            "nCells": nan_to_none(primary_row.get("n_cells_target")),
            "nGuides": nan_to_none(primary_row.get("n_guides")),
            "nDonors": nan_to_none(primary_row.get("n_donors")),
            "nTotalDeGenes": nan_to_none(primary_row.get("n_total_de_genes")),
            "nUpGenes": nan_to_none(primary_row.get("n_up_genes")),
            "nDownGenes": nan_to_none(primary_row.get("n_down_genes")),
            "crossDonorCorrelationMean": nan_to_none(primary_row.get("crossdonor_correlation_mean")),
            "crossDonorCorrelationMin": nan_to_none(primary_row.get("crossdonor_correlation_min")),
            "replicatePassFlag": bool(primary_row.get("replicate_pass_flag")) if not pd.isna(primary_row.get("replicate_pass_flag")) else None,
            "offtargetFlag": bool(primary_row.get("offtarget_flag")) if not pd.isna(primary_row.get("offtarget_flag")) else None,
            "conditions": conditions_out,
            "stimulationGated": stim_gated,
            "readiness": None if r_row is None else {
                "call": r_row["readiness_call"],
                "stage": r_row["overall_readiness_stage"],
                "reasons": r_row["readiness_reasons"],
                "nextValidationStep": r_row["next_validation_step"],
                "redFlags": red_flags,
                "biologyScore": nan_to_none(r_row.get("biology_causality_score")),
                "translationScore": nan_to_none(r_row.get("translation_score")),
                "translationCappedBy": r_row.get("translation_capped_by"),
                "tractabilityScore": nan_to_none(r_row.get("tractability_score")),
                "tractabilityModality": r_row.get("tractability_modality"),
                "humanGeneticSupport": r_row.get("human_genetic_support"),
                "diseaseRelevanceScore": nan_to_none(r_row.get("disease_relevance_score")),
                "clinicalFeasibilityScore": nan_to_none(r_row.get("clinical_feasibility_score")),
                "compositeSafetyLiability": r_row.get("composite_safety_liability"),
                "geneticSupportConfidence": r_row.get("genetic_support_confidence"),
                "hasExternalEvidence": bool(r_row.get("has_external_evidence")),
            },
            "diseases": diseases_out,
            "tractabilityFlags": modality_summary,
            "safetyLiabilities": safety_liabilities,
            "clinicalTrials": trials_out,
            "literature": literature_out,
            "gnomad": {"loeuf": loeuf, "pli": pli, "constraintTier": constraint_tier},
        })

    call_counts = pd.Series([t["readiness"]["call"] for t in targets_out if t["readiness"]]).value_counts().to_dict()
    print(f"Final target count: {len(targets_out)}; readiness call distribution: {call_counts}", file=sys.stderr)

    out = {
        "generatedAt": None,  # stamped by the caller/build step if needed; kept out of the deterministic export
        "sourceVersion": "GWT_perturbseq_analysis_2025 · target_cards.csv (marson2025_data DE) + readiness_engine + Open Targets/ClinicalTrials.gov/PubMed evidence cache (fetched 2026-07-08) + gnomAD v4 constraint",
        "modules": [
            {"id": m["module_id"], "name": m["module_name"], "category": m["category"], "seedGenes": m["seed_genes"]}
            for m in modules
        ],
        "targets": targets_out,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2, default=str))
    print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size / 1024:.1f} KB)", file=sys.stderr)


if __name__ == "__main__":
    main()
