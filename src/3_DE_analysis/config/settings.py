"""Paths: the single source of truth for every file/directory this toolkit reads or writes.

Every path here is relative to ``REPO_ROOT``, resolved once, so a checkout in
a different location (or a different working directory at import time) still
resolves correctly -- unlike the previous per-module ``Path("metadata/...")``
literals, which were implicitly relative to the process's current working
directory.
"""

from __future__ import annotations

from pathlib import Path

# src/3_DE_analysis/config/settings.py -> parents[3] is the repo root.
REPO_ROOT = Path(__file__).resolve().parents[3]

# --- Real, in-repo primary data inputs (metadata/suppl_tables/*.csv) -------------
DE_STATS_PATH = REPO_ROOT / "metadata" / "suppl_tables" / "DE_stats.suppl_table.csv"
GUIDE_KD_PATH = REPO_ROOT / "metadata" / "suppl_tables" / "guide_kd_efficiency.suppl_table.csv"
LIBRARY_METADATA_PATH = REPO_ROOT / "metadata" / "suppl_tables" / "sgrna_library_metadata.suppl_table.csv"
SAMPLE_METADATA_PATH = REPO_ROOT / "metadata" / "suppl_tables" / "sample_metadata.suppl_table.csv"
BENCHMARK_CSV_PATH = REPO_ROOT / "sources" / "topic05_successful_drug_benchmarks.csv"

# --- Overlay / gene-list inputs ---------------------------------------------------
GENE_LISTS_DIR = REPO_ROOT / "metadata" / "gene_lists"
IMMUNE_EFFECTOR_CSV_PATH = REPO_ROOT / "metadata" / "immune_effector_genes.csv"
BROAD_EFFECT_GENES_PATH = REPO_ROOT / "sources" / "broad_effect_genes.txt"
CORE_ESSENTIALS_PATH = REPO_ROOT / "metadata" / "gene_lists" / "core_essentials_hart.tsv"
SEED_MODULES_PATH = REPO_ROOT / "sources" / "topic15_cd4_tcell_upstream_downstream_seed_modules.csv"
DISEASE_ASSOCIATIONS_PATH = (
    REPO_ROOT / "src" / "6_functional_interaction" / "results" / "disease_gene_associations_detailed.csv"
)

# --- CRE schema placeholders (B5) -- files do not exist in this repo; loaders
#     degrade to an honest "not loaded" result, see cre_schema.py ----------------
CRE_ELEMENTS_PATH = REPO_ROOT / "sources" / "cre_elements.csv"
VARIANT_CRE_LINKS_PATH = REPO_ROOT / "sources" / "variant_cre_links.csv"

# --- Runtime cache / output directories -------------------------------------------
CACHE_ROOT = REPO_ROOT / "sources" / "target_tool_cache"
EVIDENCE_CACHE_DIR = CACHE_ROOT / "_evidence"
