#!/usr/bin/env python3
"""Export a real, non-mock dataset for the CD4 Target Discovery Portal frontend.

Reads directly from this repo's already-computed / already-fetched artifacts —
never invents a statistic, disease association, drug, or gene-name profile
value that isn't backed by one of these files:

  - sources/target_tool_cache/<run-id>/target_cards.csv
      Real per-target-per-condition statistics from the genome-scale CD4
      Perturb-seq screen (effect size, FDR, DE gene counts, grade, ...) —
      11,526 genes, 33,983 gene x condition rows.
  - src/3_DE_analysis/core/readiness.py (compute_readiness)
      The repo's own deterministic readiness engine — run as-is, not
      reimplemented, on the FULL card set. Produces readiness_call / stage /
      reasons / next step for every gene x condition row.
  - src/3_DE_analysis/individual_concept_profile.py (load_concept_modules)
      The real M01-M20 immune concept module definitions (seed gene lists).
  - src/3_DE_analysis/concept_annotation.py (annotate_targets)
      Real "stimulation_gated" descriptive tagging.
  - sources/target_tool_cache/_evidence/<GENE>.json
      Real, already-fetched Open Targets / ClinicalTrials.gov / PubMed
      snapshots (disease associations, Open-Targets-vocabulary tractability,
      Open-Targets-curated safety liabilities, clinical trials, literature)
      — only fetched for 21 genes. Every target in the portal gets real
      statistics + a real readiness call regardless; this deeper external
      evidence is populated only for the genes this cache actually covers,
      and left empty (not fabricated) for the rest.
  - sources/target_tool_cache/_overlays/gnomad_v4.1_constraint_full.csv
      Real gnomAD v4.1 LOEUF / pLI constraint metrics, genome-wide (17,473
      genes; MANE Select protein-coding transcripts only) — downloaded
      directly from gnomAD's public release bucket and filtered, superseding
      the earlier 16-gene gnomad_constraint_seed.csv (kept only because a
      backend test pins its exact values; this export no longer reads it).
  - src/3_DE_analysis/evidence/safety_overlay.py's
      load_membrane_tractability_overlay() / load_gtex_safety_overlay()
      Real ADC-derived membrane/surface-protein/druggability overlay
      (docs/mvp-research/adc_overlay_gwt_overlap_full.csv, 5,588 genes) and
      real GTEx per-tissue expression-breadth overlay
      (sources/target_tool_cache/_overlays/gtex_per_tissue.parquet, 9,718
      genes). Both are passed into compute_readiness() (it already accepted
      these parameters; this export previously never supplied them), which
      upgrades tractability_score/tractability_modality and adds a real
      safety_window_score wherever the gene's Ensembl id is covered. The raw
      membrane-overlay flags are additionally surfaced as their own
      `membraneOverlay` field — a different vocabulary than Open Targets'
      tractability buckets, so the two are never merged into one field.
  - src/6_functional_interaction/results/disease_gene_associations_detailed.csv
      A real Open Targets genetic-association export already produced by
      prior repo research (evidence/disease.py) -- 7,528 rows across 13
      autoimmune/inflammatory indications (Crohn's, RA, SLE, IBD, psoriasis,
      T1D, asthma, ...), no live fetch needed. Merged into the same
      `diseases` field as the live 21-gene Open Targets evidence cache above
      (same semantic meaning -- association_score is the same 0-1 scale as
      that cache's overallScore), deduplicated by disease name, each entry
      tagged with which of the two sources it came from. Covers 1,256 of the
      7,249 selected genes.
  - src/3_DE_analysis/evidence/population.py (load_burden_estimates,
      build_population_hypothesis_card) + src/8_lymphocyte_counts_LoF/input/
      Backman_LymphocyteCount_fullFeatures.per_gene_estimates.tsv
      Real UK Biobank exome-wide rare-LoF-variant lymphocyte-count burden
      estimates (Backman et al. 2021) -- a population-level statistical
      association ("if a population carries a LoF variant in this gene, does
      lymphocyte count shift on average"), entirely local (zero network
      calls), registered in evidence/registry.py but never previously wired
      into this export. Covers 7,140 of the 7,249 selected genes (98.5%) --
      independent of and complementary to gnomAD's constraint signal above
      (gnomAD: population tolerance for loss of the gene; this: the actual
      measured phenotypic consequence for one CD4-relevant trait).
  - docs/mvp-research/signed_de_application/signed_ranking_v2.csv
      This repo's own signed/directional re-analysis of the same GB10 CD4+
      T-cell KO Perturb-seq screen -- for each target, whether knockout nets
      MORE up- or down-regulated downstream genes (directionality_index,
      footprint_class), a real axis target_cards.csv itself doesn't carry.
      The file's own header explicitly cautions that footprint_class is a
      net transcriptional FOOTPRINT direction, NOT a molecular
      activator/repressor role assignment -- that caveat is carried verbatim
      into the frontend copy, not paraphrased away. Covers 7,173 of the
      7,249 selected genes (99.0%).
  - metadata/SchmidtSteinhart2022_CRISPRi_screen_gene_phenotypes.csv,
      Arce2025_Screen.csv, Freimer2022_Screen.csv, Umhoefer2025_FOXP3_Teff.csv
      Four independent, already-published external CRISPR screens (real
      MAGeCK-style neg/pos enrichment statistics per gene per
      phenotype/condition) -- Arce/Freimer/Umhoefer share the identical
      1,351-gene druggable-genome panel; SchmidtSteinhart is genome-wide
      (18,939 genes, CD4+ IL2 / CD8+ IFNG phenotypes). Surfaced as
      "independent screen replication" -- does an external, separately
      published study also see a hit at this gene. Combined coverage: 6,921
      of the 7,249 selected genes (95.5%) have at least one entry.
  - docs/mvp-research/pipeline/kinetics_avoid/target_master_table.csv
      This repo's own PRIOR CURATED editorial judgment layer (avoid_tier,
      avoid_flags with reasons, delivery_modality, kinetic_archetype) --
      explicitly NOT a new independent measurement, so the frontend labels
      it as this repo's own assessment rather than presenting it alongside
      raw evidence sources as if it were on the same footing. Covers 1,228
      of the 7,249 selected genes (16.9%) -- the 1,235-gene "gate shortlist"
      this repo's prior research curated most deeply.
  - metadata/suppl_tables/clustering_results_and_annotations.csv
      Real CORUM/STRINGdb/KEGG/Reactome functional-complex overlap analysis
      over this screen's own co-regulation clusters (112 clusters). Only the
      50 clusters with a resolved (non-"unknown") manual_annotation are
      surfaced -- covers 611 of the 7,249 selected genes (8.4%), a
      complement to the M01-M20 concept modules above, not a replacement.

Target selection: every gene whose best-condition statistical_evidence_grade
is >= MIN_GRADE (2 = C or better), UNION every gene (any grade) whose
primary-condition readiness_call is "advance" or "watchlist" — not an
arbitrary curation, a disclosed statistical threshold applied to the full
real screen. Below MIN_GRADE, "deprioritize" calls (the overwhelming
majority of the remaining low-grade genes) are intentionally excluded.

Anything not present in these sources is emitted as JSON `null` (never a
fabricated 0 or placeholder), matching this project's own "unknown != 0"
discipline (see docs/architecture_refactor_plan.md, core/readiness.py). Gene
full names are standard HGNC nomenclature for the 21 evidence-cache genes
(verified by hand); every other gene displays its symbol as its name rather
than a guessed/fabricated full name.

The readiness engine and concept annotation run once over all 33,983 rows
(~15s) and are then CACHED to sources/target_tool_cache/_cache/*.parquet so
re-running this export (e.g. after only touching GENE_FULL_NAMES or the JSON
shape) does not repeat that computation. Pass --force to recompute after
readiness.py / concept_annotation.py / target_cards.csv itself changes — the
cache is otherwise trusted whenever it's newer than target_cards.csv.

Usage (from repo root):
    pip install pandas numpy pyyaml pyarrow
    python3 frontend/webserver/scripts/export_real_data.py [--force]

Writes frontend/webserver/public/real-dataset.json (fetched at runtime, not
bundled into the JS -- see src/data/dataset.ts).
"""
from __future__ import annotations

import argparse
import ast
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
# Genome-wide gnomAD v4.1 constraint (17,473 genes) -- see module docstring.
# NOT the same file as evidence/safety_overlay.py's default 16-gene seed
# (gnomad_constraint_seed.csv); this export always uses the wider file.
GNOMAD_CSV = REPO_ROOT / "sources" / "target_tool_cache" / "_overlays" / "gnomad_v4.1_constraint_full.csv"
GENE_LISTS_DIR = REPO_ROOT / "metadata" / "gene_lists"
ESSENTIALS_TSV = GENE_LISTS_DIR / "core_essentials_hart.tsv"
BROAD_EFFECT_TXT = REPO_ROOT / "sources" / "broad_effect_genes.txt"
# Local (zero-network) Open Targets genetic-association export, 13 real
# autoimmune/inflammatory indications -- see module docstring.
DISEASE_ASSOC_CSV = REPO_ROOT / "src" / "6_functional_interaction" / "results" / "disease_gene_associations_detailed.csv"
# Local (zero-network) UK Biobank LoF-burden estimates -- see module docstring.
LYMPHOCYTE_BURDEN_TSV = (
    REPO_ROOT / "src" / "8_lymphocyte_counts_LoF" / "input" / "Backman_LymphocyteCount_fullFeatures.per_gene_estimates.tsv"
)
# This repo's own signed/directional re-analysis of the same GB10 screen --
# see module docstring.
SIGNED_RANKING_CSV = REPO_ROOT / "docs" / "mvp-research" / "signed_de_application" / "signed_ranking_v2.csv"
# Independent published external screens (all real, all gene-symbol keyed) --
# see module docstring.
SCHMIDT_STEINHART_CSV = REPO_ROOT / "metadata" / "SchmidtSteinhart2022_CRISPRi_screen_gene_phenotypes.csv"
ARCE2025_CSV = REPO_ROOT / "metadata" / "Arce2025_Screen.csv"
FREIMER2022_CSV = REPO_ROOT / "metadata" / "Freimer2022_Screen.csv"
UMHOEFER2025_CSV = REPO_ROOT / "metadata" / "Umhoefer2025_FOXP3_Teff.csv"
# This repo's own prior curated avoid/delivery assessment (an editorial
# judgment layer, not a new independent measurement) -- see module docstring.
KINETICS_AVOID_CSV = REPO_ROOT / "docs" / "mvp-research" / "pipeline" / "kinetics_avoid" / "target_master_table.csv"
# Real CORUM/STRINGdb/KEGG/Reactome functional-complex clustering -- see
# module docstring.
CLUSTERING_CSV = REPO_ROOT / "metadata" / "suppl_tables" / "clustering_results_and_annotations.csv"

# Cached full-screen compute_readiness / annotate_targets output (see module
# docstring). Committed to the repo so nobody has to pay the ~15s recompute
# just to regenerate the frontend JSON.
CACHE_DIR = REPO_ROOT / "sources" / "target_tool_cache" / "_cache"
READINESS_CACHE = CACHE_DIR / "readiness_full.parquet"
ANNOTATED_CACHE = CACHE_DIR / "concept_annotated_full.parquet"

# Minimum best-condition statistical_evidence_grade for a gene to be included,
# UNION any gene (any grade) whose primary-condition readiness_call is
# "advance" or "watchlist" — see README's Data section.
MIN_GRADE = 2

# public/ (not src/) -- at ~7,200 genes this is fetched at runtime, not
# bundled into the JS (see src/data/dataset.ts's loadDataset()).
OUT_PATH = Path(__file__).resolve().parents[1] / "public" / "real-dataset.json"

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


def parse_score(v):
    """Undo the str() coercion applied to disease_relevance_score before caching."""
    if v is None or v == "unknown":
        return "unknown"
    try:
        return int(v)
    except (TypeError, ValueError):
        return v


def _cache_is_fresh() -> bool:
    if not (READINESS_CACHE.exists() and ANNOTATED_CACHE.exists()):
        return False
    cards_mtime = CARDS_CSV.stat().st_mtime
    return READINESS_CACHE.stat().st_mtime >= cards_mtime and ANNOTATED_CACHE.stat().st_mtime >= cards_mtime


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Recompute readiness/annotation even if a fresh cache exists.")
    args = parser.parse_args()

    from concept_annotation import annotate_targets
    from core.readiness import compute_readiness, load_overlays
    from data.loaders import load_gene_set
    from evidence.disease import load_disease_associations
    from evidence.population import build_population_hypothesis_card, load_burden_estimates
    from evidence.safety_overlay import (
        load_gnomad_constraint_overlay,
        load_gtex_safety_overlay,
        load_membrane_tractability_overlay,
    )
    from individual_concept_profile import load_concept_modules

    print(f"Loading real target cards from {CARDS_CSV}", file=sys.stderr)
    cards = pd.read_csv(CARDS_CSV)
    print(f"Full screen: {len(cards)} gene x condition rows, {cards['target'].nunique()} unique genes", file=sys.stderr)

    evidence_genes = sorted(p.stem for p in EVIDENCE_DIR.glob("*.json"))
    print(f"Evidence-cache genes ({len(evidence_genes)}) — deep external evidence only for these: {evidence_genes}", file=sys.stderr)

    # Local (zero-network) disease-association export -- see module docstring.
    disease_assoc = load_disease_associations(DISEASE_ASSOC_CSV)
    disease_assoc_by_gene: dict[str, list] = {}
    for _, r in disease_assoc.iterrows():
        disease_assoc_by_gene.setdefault(r["gene_symbol"], []).append(r)
    print(f"Local disease-association export: {len(disease_assoc_by_gene)} genes across {disease_assoc['disease_name'].nunique() if not disease_assoc.empty else 0} indications", file=sys.stderr)

    # Local (zero-network) UK Biobank lymphocyte-count LoF-burden -- see module docstring.
    burden = load_burden_estimates("lymphocyte_count", path=LYMPHOCYTE_BURDEN_TSV)
    pop_burden_by_gene: dict[str, "pd.Series"] = {}
    if burden["available"]:
        pop_cards = build_population_hypothesis_card(cards, burden["estimates"], trait="lymphocyte_count")
        pop_burden_by_gene = {r["target"]: r for _, r in pop_cards.iterrows()}
    print(f"Population LoF-burden (lymphocyte count): {'unavailable — ' + burden['reason'] if not burden['available'] else str(len(pop_burden_by_gene)) + ' genes'}", file=sys.stderr)

    # Local (zero-network) signed/directional re-analysis of this repo's own
    # screen -- see module docstring.
    signed_ranking = pd.read_csv(SIGNED_RANKING_CSV, comment="#")
    footprint_by_gene = {r["target_gene"]: r for _, r in signed_ranking.iterrows()}
    print(f"Signed footprint re-analysis: {len(footprint_by_gene)} genes", file=sys.stderr)

    # Local (zero-network) independent published external screens -- see
    # module docstring. Normalized into one gene -> list-of-hits lookup;
    # "Non-Targeting" rows are screen negative controls, not genes.
    external_screens_by_gene: dict[str, list] = {}

    def _add_external_hit(gene: str, study: str, phenotype: str, row) -> None:
        if gene == "Non-Targeting" or pd.isna(gene):
            return
        external_screens_by_gene.setdefault(gene, []).append({
            "study": study,
            "phenotype": phenotype,
            "negScore": nan_to_none(row.get("neg|score")),
            "negFdr": nan_to_none(row.get("neg|fdr")),
            "negRank": nan_to_none(row.get("neg|rank")),
            "posScore": nan_to_none(row.get("pos|score")),
            "posFdr": nan_to_none(row.get("pos|fdr")),
            "posRank": nan_to_none(row.get("pos|rank")),
        })

    schmidt = pd.read_csv(SCHMIDT_STEINHART_CSV)
    for _, r in schmidt.iterrows():
        _add_external_hit(r["id"], "SchmidtSteinhart2022", r["phenotype"], r)

    freimer = pd.read_csv(FREIMER2022_CSV)
    for _, r in freimer.iterrows():
        _add_external_hit(r["id"], "Freimer2022", r["screen"], r)

    umhoefer = pd.read_csv(UMHOEFER2025_CSV)
    for _, r in umhoefer.iterrows():
        _add_external_hit(r["id"], "Umhoefer2025", "FOXP3_Teff", r)

    arce = pd.read_csv(ARCE2025_CSV)
    arce_conditions = sorted({c.split(".", 1)[1] for c in arce.columns if "." in c})
    for _, r in arce.iterrows():
        for cond in arce_conditions:
            sub = {
                "neg|score": r.get(f"neg|score.{cond}"),
                "neg|fdr": r.get(f"neg|fdr.{cond}"),
                "neg|rank": r.get(f"neg|rank.{cond}"),
                "pos|score": r.get(f"pos|score.{cond}"),
                "pos|fdr": r.get(f"pos|fdr.{cond}"),
                "pos|rank": r.get(f"pos|rank.{cond}"),
            }
            _add_external_hit(r["id"], "Arce2025", cond, sub)

    n_screen_genes = len({g for g in external_screens_by_gene})
    print(f"External screen replication: {n_screen_genes} genes across 4 published studies", file=sys.stderr)

    # Local (zero-network) prior curated avoid/delivery assessment -- an
    # editorial judgment layer, not a new independent measurement (see
    # module docstring).
    kinetics_avoid = pd.read_csv(KINETICS_AVOID_CSV)
    avoid_by_gene = {r["gene"]: r for _, r in kinetics_avoid.iterrows()}
    print(f"Prior curated avoid/delivery assessment: {len(avoid_by_gene)} genes (gate shortlist)", file=sys.stderr)

    # Local (zero-network) real CORUM/STRINGdb/KEGG/Reactome functional-
    # complex clustering -- see module docstring. Only non-"unknown" clusters
    # are surfaced; a gene can belong to more than one cluster.
    clustering = pd.read_csv(CLUSTERING_CSV)
    clustering = clustering[clustering["manual_annotation"] != "unknown"]
    complexes_by_gene: dict[str, list] = {}
    for _, r in clustering.iterrows():
        members = ast.literal_eval(r["cluster_member"])
        for g in members:
            complexes_by_gene.setdefault(g, []).append({
                "clusterAnnotation": r["manual_annotation"],
                "bestDescribedBy": r["best_described_by"],
            })
    print(f"Functional-complex clustering: {len(complexes_by_gene)} genes across {len(clustering)} resolved clusters", file=sys.stderr)

    if not args.force and _cache_is_fresh():
        print(f"Reading cached readiness/annotation from {CACHE_DIR} (pass --force to recompute)...", file=sys.stderr)
        readiness = pd.read_parquet(READINESS_CACHE)
        annotated = pd.read_parquet(ANNOTATED_CACHE)
    else:
        overlays = load_overlays(GENE_LISTS_DIR)
        essentials = load_gene_set(ESSENTIALS_TSV) if ESSENTIALS_TSV.exists() else set()
        broad_effect = load_gene_set(BROAD_EFFECT_TXT) if BROAD_EFFECT_TXT.exists() else set()

        def evidence_lookup(gene: str):
            return load_evidence(gene)

        membrane = load_membrane_tractability_overlay()
        gtex = load_gtex_safety_overlay()
        gnomad_readiness_overlay = load_gnomad_constraint_overlay(path=GNOMAD_CSV)
        print(
            f"Overlays for compute_readiness(): membrane={membrane['available']}, "
            f"gtex={gtex['available']}, gnomad={gnomad_readiness_overlay['available']}",
            file=sys.stderr,
        )

        print("Running the repo's real readiness engine (core.readiness.compute_readiness) on the full screen (~15s, cached after)...", file=sys.stderr)
        readiness = compute_readiness(
            cards,
            overlays=overlays,
            essentials=essentials,
            broad_effect_genes=broad_effect,
            evidence_lookup=evidence_lookup,
            membrane_overlay=membrane if membrane["available"] else None,
            gtex_overlay=gtex if gtex["available"] else None,
            gnomad_overlay=gnomad_readiness_overlay if gnomad_readiness_overlay["available"] else None,
        )
        # disease_relevance_score and safety_window_score are int-or-"unknown"
        # (readiness.py's UNKNOWN sentinel) -- genuinely mixed-type columns
        # parquet can't store. Stringify uniformly here so the cached and
        # freshly-computed frames have identical dtypes; parse_score() below
        # undoes this on read (safety_window_score reuses the same helper --
        # both are int-or-"unknown", nothing score-specific about it).
        readiness["disease_relevance_score"] = readiness["disease_relevance_score"].apply(str)
        readiness["safety_window_score"] = readiness["safety_window_score"].apply(str)
        # Keep only the columns this export actually reads -- shrinks the
        # cache and drops other mixed-type/unused columns (e.g.
        # genetic_support_max_genetic_score) we'd otherwise have to placate
        # parquet about for no benefit.
        readiness = readiness[[
            "target", "condition", "red_flag_override", "readiness_call",
            "overall_readiness_stage", "readiness_reasons", "next_validation_step",
            "biology_causality_score", "translation_score", "translation_capped_by",
            "tractability_score", "tractability_modality", "human_genetic_support",
            "disease_relevance_score", "clinical_feasibility_score",
            "composite_safety_liability", "genetic_support_confidence",
            "has_external_evidence", "safety_window_score",
        ]].copy()

        print("Running real concept-module annotation (concept_annotation.annotate_targets) on the full screen...", file=sys.stderr)
        modules_for_cache = load_concept_modules()
        annotated_full = annotate_targets(cards, modules=modules_for_cache)
        # This export only ever reads target/condition/stimulation_gated back
        # off the annotated frame (module membership itself comes from
        # load_concept_modules() directly) -- drop the nested
        # concept_modules list-of-dicts column, which parquet can't round
        # -trip as cleanly, rather than fight with its serialization.
        annotated = annotated_full[["target", "condition", "stimulation_gated"]].copy()

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        readiness.to_parquet(READINESS_CACHE, index=False)
        annotated.to_parquet(ANNOTATED_CACHE, index=False)
        print(f"Cached readiness -> {READINESS_CACHE.relative_to(REPO_ROOT)}, annotation -> {ANNOTATED_CACHE.relative_to(REPO_ROOT)}", file=sys.stderr)

    modules = load_concept_modules()

    gnomad = pd.read_csv(GNOMAD_CSV) if GNOMAD_CSV.exists() else pd.DataFrame(columns=["ensembl_id", "gene_symbol", "loeuf", "pli"])
    gnomad_by_gene = {r["gene_symbol"]: r for _, r in gnomad.iterrows()}

    # Raw ADC membrane/tractability overlay flags, keyed by Ensembl id -- a
    # different vocabulary than Open Targets' SM/AB/PR/OC tractability
    # buckets (see module docstring), so surfaced as its own field rather
    # than merged into tractabilityFlags. compute_readiness() above already
    # used this same overlay to upgrade readiness.tractabilityScore/Modality;
    # this is the raw signal underneath that upgrade.
    membrane_overlay_result = load_membrane_tractability_overlay()
    membrane_by_ensembl: dict[str, pd.Series] = {}
    if membrane_overlay_result["available"]:
        for _, r in membrane_overlay_result["table"].iterrows():
            membrane_by_ensembl[r["ensembl_id"]] = r
    print(
        f"Membrane overlay: {'available, ' + str(len(membrane_by_ensembl)) + ' genes' if membrane_overlay_result['available'] else membrane_overlay_result['reason']}",
        file=sys.stderr,
    )

    module_by_gene: dict[str, list[dict]] = {}
    for m in modules:
        for g in m["seed_genes"]:
            module_by_gene.setdefault(g, []).append(m)

    # Primary condition per gene = highest statistical_evidence_grade, tie-broken by lowest fdr_min.
    cards = cards.assign(
        _grade=pd.to_numeric(cards["statistical_evidence_grade"], errors="coerce").fillna(0),
        _fdr=pd.to_numeric(cards["fdr_min"], errors="coerce").fillna(1.0),
    )
    primary_rows = cards.sort_values(["_grade", "_fdr"], ascending=[False, True]).groupby("target", as_index=False).head(1)
    primary_by_gene = {r["target"]: r for _, r in primary_rows.iterrows()}

    readiness_indexed = readiness.set_index(["target", "condition"])
    grade_max_by_gene = cards.groupby("target")["_grade"].max()

    def primary_call(gene: str, primary_row: pd.Series):
        key = (gene, primary_row["condition"])
        if key not in readiness_indexed.index:
            return None
        return readiness_indexed.loc[key]

    # Selection: grade>=MIN_GRADE anywhere for that gene, UNION primary-condition
    # readiness_call in (advance, watchlist) — deprioritize calls below MIN_GRADE
    # are intentionally excluded.
    selected_genes = set()
    for gene, prow in primary_by_gene.items():
        if grade_max_by_gene.get(gene, 0) >= MIN_GRADE:
            selected_genes.add(gene)
            continue
        r = primary_call(gene, prow)
        if r is not None and r["readiness_call"] in ("advance", "watchlist"):
            selected_genes.add(gene)
    selected_genes = sorted(selected_genes)
    print(f"Selected {len(selected_genes)} genes (grade>={MIN_GRADE} OR primary-condition readiness_call in advance/watchlist)", file=sys.stderr)

    targets_out = []
    for gene in selected_genes:
        g_cards = cards[cards["target"] == gene]
        g_readiness = readiness[readiness["target"] == gene]
        g_annot = annotated[annotated["target"] == gene]

        primary_row = primary_by_gene[gene]
        primary_condition = primary_row["condition"]
        r_row = primary_call(gene, primary_row)

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
        diseases_merged = [
            {
                "name": d.get("disease"),
                "id": d.get("disease_id"),
                "overallScore": nan_to_none(d.get("overall_score")),
                "geneticAssociationScore": nan_to_none(d.get("genetic_association_score")),
                "source": "Open Targets (cached fetch)",
            }
            for d in diseases
        ]
        seen_disease_names = {(d["name"] or "").strip().lower() for d in diseases_merged}
        for row in disease_assoc_by_gene.get(gene, []):
            name = str(row.get("disease_name") or "").strip()
            if name.lower() in seen_disease_names:
                continue
            seen_disease_names.add(name.lower())
            diseases_merged.append({
                "name": name,
                "id": row.get("disease_efo"),
                "overallScore": nan_to_none(row.get("association_score")),
                "geneticAssociationScore": nan_to_none(row.get("genetic_evidence_score")),
                "source": "Open Targets (local autoimmune-disease export)",
            })
        diseases_out = sorted(diseases_merged, key=lambda d: d["overallScore"] or 0, reverse=True)[:8]

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

        pb = pop_burden_by_gene.get(gene)
        pop_burden_out = None
        if pb is not None:
            pop_burden_out = {
                "trait": pb["trait"],
                "effectEstimate": nan_to_none(pb["population_effect_estimate"]),
                "ci95Lower": nan_to_none(pb["ci_95_lower"]),
                "ci95Upper": nan_to_none(pb["ci_95_upper"]),
                "ciExcludesZero": bool(pb["ci_excludes_zero"]),
                "direction": pb["direction"],
                "hypothesis": pb["population_hypothesis"],
                "caveat": pb["caveat"],
            }

        mb = membrane_by_ensembl.get(primary_row.get("target_id"))
        membrane_overlay_out = None
        if mb is not None:
            membrane_overlay_out = {
                "isSurfaceProtein": bool(mb["is_surface_protein"]),
                "hasTransmembraneDomain": bool(mb["has_transmembrane_domain"]),
                "hasExtracellularDomain": bool(mb["has_extracellular_domain"]),
                "isDruggable": bool(mb["is_druggable"]),
                "druggablePathway": nan_to_none(mb.get("druggable_pathway")),
            }

        fp = footprint_by_gene.get(gene)
        downstream_footprint_out = None
        if fp is not None:
            downstream_footprint_out = {
                "directionalityIndex": nan_to_none(fp["directionality_index"]),
                "footprintClass": fp["footprint_class"],
                "binomFdr": nan_to_none(fp["binom_fdr"]),
                "nUp": nan_to_none(fp["n_up"]),
                "nDown": nan_to_none(fp["n_down"]),
                "netLogfc": nan_to_none(fp["net_logfc"]),
                "inGateShortlist": bool(fp["in_gate_shortlist"]),
            }

        external_screens_out = sorted(
            external_screens_by_gene.get(gene, []),
            key=lambda h: min(h["negFdr"] if h["negFdr"] is not None else 1.0, h["posFdr"] if h["posFdr"] is not None else 1.0),
        )[:6]

        av = avoid_by_gene.get(gene)
        avoid_assessment_out = None
        if av is not None:
            flags_raw = av.get("avoid_flags")
            avoid_assessment_out = {
                "avoidTier": av["avoid_tier"],
                "avoidFlags": [f.strip() for f in str(flags_raw).split(";") if f.strip()] if isinstance(flags_raw, str) else [],
                "deliveryModality": av["delivery_modality"],
                "kineticArchetype": av["kinetic_archetype"],
                "isContextSpecific": bool(av["is_ctx_specific"]),
            }

        # A gene can genuinely belong to more than one real cluster (e.g. a
        # tight core cluster and a larger looser one) that happen to share
        # the same manual annotation text -- dedupe by the displayed label
        # pair so the UI doesn't show an apparently-identical row twice.
        seen_complex_labels = set()
        functional_complexes_out = []
        for c in complexes_by_gene.get(gene, []):
            key = (c["clusterAnnotation"], c["bestDescribedBy"])
            if key in seen_complex_labels:
                continue
            seen_complex_labels.add(key)
            functional_complexes_out.append(c)

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
                "diseaseRelevanceScore": parse_score(r_row.get("disease_relevance_score")),
                "clinicalFeasibilityScore": nan_to_none(r_row.get("clinical_feasibility_score")),
                "compositeSafetyLiability": r_row.get("composite_safety_liability"),
                "geneticSupportConfidence": r_row.get("genetic_support_confidence"),
                "hasExternalEvidence": bool(r_row.get("has_external_evidence")),
                "safetyWindowScore": parse_score(r_row.get("safety_window_score")),
            },
            "diseases": diseases_out,
            "tractabilityFlags": modality_summary,
            "membraneOverlay": membrane_overlay_out,
            "safetyLiabilities": safety_liabilities,
            "clinicalTrials": trials_out,
            "literature": literature_out,
            "gnomad": {"loeuf": loeuf, "pli": pli, "constraintTier": constraint_tier},
            "populationBurden": pop_burden_out,
            "downstreamFootprint": downstream_footprint_out,
            "externalScreens": external_screens_out,
            "avoidAssessment": avoid_assessment_out,
            "functionalComplexes": functional_complexes_out,
        })

    call_counts = pd.Series([t["readiness"]["call"] for t in targets_out if t["readiness"]]).value_counts().to_dict()
    print(f"Final target count: {len(targets_out)}; readiness call distribution: {call_counts}", file=sys.stderr)

    out = {
        "generatedAt": None,  # stamped by the caller/build step if needed; kept out of the deterministic export
        "sourceVersion": "GWT_perturbseq_analysis_2025 · target_cards.csv (marson2025_data DE) + readiness_engine + Open Targets/ClinicalTrials.gov/PubMed evidence cache (fetched 2026-07-08, 21 genes) + local Open Targets disease-association export (13 indications) + gnomAD v4.1 genome-wide constraint + ADC membrane overlay + GTEx safety-window overlay + UK Biobank lymphocyte-count LoF burden + signed footprint re-analysis + 4 external screens (SchmidtSteinhart2022/Arce2025/Freimer2022/Umhoefer2025) + prior curated avoid/delivery assessment + CORUM/STRINGdb/KEGG/Reactome clustering",
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
