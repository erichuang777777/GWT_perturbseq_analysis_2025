"""Shared dependencies for the API layer (architecture refactor Phase 4, §4.1/§4.3④).

Path/version constants, cached resolvers/overlays, and generic per-dataset
I/O helpers used by more than one router live here, so splitting
``target_card_api.py`` into ``api/routers/*.py`` doesn't force each router
to duplicate them. This is DI in the "module as a namespace" sense used
throughout this repo's caching helpers (``_gene_resolver()``,
``_membrane_overlay()``, etc. below) -- not a class-based container,
consistent with the plan doc's "avoid over-engineering" guardrail (§6).

Routers reference this module's constants via ``deps.NAME`` (attribute
access on the imported module, e.g. ``from api import deps`` then
``deps.PATHWAY_CACHE_DIR`` inline in a handler body) rather than
``from api.deps import NAME`` at their own top level. This is not just
style: Python resolves ``from api.deps import NAME`` into a *copy* of the
binding in the importing module's own namespace, so a test that
monkeypatches ``deps.NAME`` would have no effect on a router that imported
it the other way -- see
``tests/test_mechanism_graph.py::test_mechanism_graph_api_endpoint_reads_real_cache_dir``,
which patches ``deps.PATHWAY_CACHE_DIR`` for exactly this reason.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from core.cards import load_gene_set
from core.readiness import load_overlays
from evidence.disease import load_disease_associations
from evidence.safety_overlay import (
    load_gnomad_constraint_overlay,
    load_gtex_safety_overlay,
    load_membrane_tractability_overlay,
)
from evidence.population import load_burden_estimates
from resolve.resolver import load_resolver
from upload.import_manager import utc_now

# --- Paths ---------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[3]
# SRC == src/3_DE_analysis (the package root one level up from this api/
# dir, not this file's own parent).
SRC = Path(__file__).resolve().parents[1]
DEFAULT_DE = ROOT / "metadata" / "suppl_tables" / "DE_stats.suppl_table.csv"
DEFAULT_GUIDE = ROOT / "metadata" / "suppl_tables" / "guide_kd_efficiency.suppl_table.csv"
DEFAULT_LIB = ROOT / "metadata" / "suppl_tables" / "sgrna_library_metadata.suppl_table.csv"
DEFAULT_BENCH = ROOT / "sources" / "topic05_successful_drug_benchmarks.csv"
SEED_MODULES = ROOT / "sources" / "topic15_cd4_tcell_upstream_downstream_seed_modules.csv"
CACHE_ROOT = ROOT / "sources" / "target_tool_cache"
# Deliberately still points at the flat build_target_cards.py shim, not
# core/cards.py directly: this is invoked as `python <script>` in a fresh
# subprocess (see api/routers/build.py's _run_script), which only
# auto-adds the *script's own* directory to sys.path. core/cards.py's
# package-relative imports (`from core.kd_status import ...`) require
# src/3_DE_analysis itself (not core/) on sys.path, so only the top-level
# shim -- which sits directly in src/3_DE_analysis -- is safely
# subprocess-invocable this way.
DEFAULT_BUILD_SCRIPT = SRC / "build_target_cards.py"
DEFAULT_SAMPLE_META = ROOT / "metadata" / "suppl_tables" / "sample_metadata.suppl_table.csv"
GENE_LISTS_DIR = ROOT / "metadata" / "gene_lists"
DEFAULT_ESSENTIALS = GENE_LISTS_DIR / "core_essentials_hart.tsv"
DEFAULT_BROAD_EFFECT = ROOT / "sources" / "broad_effect_genes.txt"
EVIDENCE_CACHE_DIR = CACHE_ROOT / "_evidence"
# A2: pathway_network_cache.py's snapshot directory -- mechanism_graph.py only
# ever reads what's already been batch-fetched here, same offline-batch,
# never-live-in-request-path pattern as EVIDENCE_CACHE_DIR above.
PATHWAY_CACHE_DIR = CACHE_ROOT / "_pathway"
DISEASE_ASSOCIATIONS_PATH = ROOT / "src" / "6_functional_interaction" / "results" / "disease_gene_associations_detailed.csv"

# B5 schema placeholders: no CRE dataset is present in this repo. These paths
# intentionally point at files that don't exist yet -- load_cre_elements /
# load_variant_cre_links report an explicit "not loaded" status rather than
# fabricating data. Point them at a real file (e.g. a processed Moonen CRE
# export) when one becomes available; no other code needs to change.
CRE_ELEMENTS_PATH = ROOT / "sources" / "cre_elements.csv"
VARIANT_CRE_LINKS_PATH = ROOT / "sources" / "variant_cre_links.csv"

# --- Versions --------------------------------------------------------------

# Bump whenever core/cards.py, core/readiness.py, core/calibration.py, or
# evidence/external_cache.py change scoring/engine behavior, so every
# dataset's provenance footer can say exactly which engine produced it.
ENGINE_VERSION = "1.3.0"  # wave 3: readiness engine + real batch flag + upload merge loop (1.0-1.2) + external evidence (1.3)

# Which upstream GWT dataset release this toolkit's local CSVs correspond to.
# Distinct from ENGINE_VERSION (this toolkit's own scoring logic) -- bump only
# when the underlying DE_stats/guide_kd/sgrna_library upstream release changes,
# per docs/de_and_baseline_spec.md and the manuscript DOI in README.md.
DATASET_VERSION = "gwt_marson2025/bioRxiv-10.64898-2025.12.23.696273v1"

# The target_cards.csv COLUMN CONTRACT itself, independent of engine scoring
# logic. Bump when out_cols in core/cards.py adds/removes/renames a column,
# so a consumer can tell whether its column-name assumptions still hold.
# v1 = the original 24-column spec (sources/topic14_target_card_specification.md);
# v2 = + druggable_class/tractability_modality/safety_note, kd_status/
# kd_threshold_version/target_baseline_expression, condition_specificity_zscore,
# effect_direction_flip_flag.
CARD_SCHEMA_VERSION = "card_schema/v2"

# Hard cap on how many genes one evidence-build request may schedule, so a
# single call can never fan out into an unbounded number of external HTTP
# fetches.
MAX_EVIDENCE_GENES = 50


# --- Cached resolvers/overlays ---------------------------------------------
# Each is a deterministic function of a static local file, so there is no
# correctness reason to reload per request -- only a performance one.


def _disease_associations():
    return load_disease_associations(DISEASE_ASSOCIATIONS_PATH)


_GENE_RESOLVER = None


def _gene_resolver():
    global _GENE_RESOLVER
    if _GENE_RESOLVER is None:
        _GENE_RESOLVER = load_resolver(DEFAULT_LIB, DEFAULT_GUIDE)
    return _GENE_RESOLVER


_BURDEN_ESTIMATES_CACHE: Dict[str, Any] = {}


def _burden_estimates(trait: str) -> Dict[str, Any]:
    if trait not in _BURDEN_ESTIMATES_CACHE:
        _BURDEN_ESTIMATES_CACHE[trait] = load_burden_estimates(trait)
    return _BURDEN_ESTIMATES_CACHE[trait]


def _overlays():
    return load_overlays(GENE_LISTS_DIR)


_MEMBRANE_OVERLAY_CACHE: Optional[Dict[str, Any]] = None
_GTEX_OVERLAY_CACHE: Optional[Dict[str, Any]] = None
_GNOMAD_OVERLAY_CACHE: Optional[Dict[str, Any]] = None


def _membrane_overlay() -> Dict[str, Any]:
    global _MEMBRANE_OVERLAY_CACHE
    if _MEMBRANE_OVERLAY_CACHE is None:
        _MEMBRANE_OVERLAY_CACHE = load_membrane_tractability_overlay()
    return _MEMBRANE_OVERLAY_CACHE


def _gtex_overlay() -> Dict[str, Any]:
    global _GTEX_OVERLAY_CACHE
    if _GTEX_OVERLAY_CACHE is None:
        _GTEX_OVERLAY_CACHE = load_gtex_safety_overlay()
    return _GTEX_OVERLAY_CACHE


def _gnomad_overlay() -> Dict[str, Any]:
    global _GNOMAD_OVERLAY_CACHE
    if _GNOMAD_OVERLAY_CACHE is None:
        _GNOMAD_OVERLAY_CACHE = load_gnomad_constraint_overlay()
    return _GNOMAD_OVERLAY_CACHE


def _essentials():
    return load_gene_set(DEFAULT_ESSENTIALS)


def _broad_effect_genes():
    return load_gene_set(DEFAULT_BROAD_EFFECT)


# --- Generic per-dataset helpers -------------------------------------------


def _dataset_path(dataset_id: str) -> Path:
    path = CACHE_ROOT / dataset_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _data_version_fingerprint(paths: List[Path]) -> str:
    """Deterministic fingerprint of input file identity: name + mtime + size, joined."""
    parts = []
    for path in paths:
        if path and Path(path).exists():
            stat = Path(path).stat()
            parts.append(f"{Path(path).name}@{int(stat.st_mtime)}:{stat.st_size}")
    return ";".join(parts) if parts else "unknown"


def _signature_set_version() -> str:
    """Fingerprint of the seed CD4 module list used for module scoring/mechanism graphs."""
    return _data_version_fingerprint([SEED_MODULES])


def _import_allowed_roots() -> List[Path]:
    import os

    raw = os.getenv("GWT_IMPORT_ALLOW_ROOTS", "")
    roots = [ROOT]
    for token in raw.split(";"):
        token = token.strip()
        if token:
            roots.append(Path(token))
    return roots


def _assert_allowed_input_path(path: Path) -> None:
    from fastapi import HTTPException

    resolved = path.resolve()
    for root in _import_allowed_roots():
        try:
            resolved.relative_to(root.resolve())
            return
        except ValueError:
            continue
    allowed = ", ".join(str(root.resolve()) for root in _import_allowed_roots())
    raise HTTPException(status_code=403, detail=f"input path must be under an allowed root: {allowed}")


def _load_cards(out_csv: Path) -> pd.DataFrame:
    if not out_csv.exists():
        raise FileNotFoundError(f"Target cards file not found: {out_csv}")
    return pd.read_csv(out_csv)


def _normalize_cell_values(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["ontarget_significant", "offtarget_flag", "replicate_pass_flag"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().isin({"true", "1", "yes", "y"})
    for col in [
        "n_cells_target",
        "n_guides",
        "n_total_de_genes",
        "n_up_genes",
        "n_down_genes",
        "crossdonor_correlation_mean",
        "crossdonor_correlation_min",
        "crossguide_correlation",
        "condition_specificity_score",
        "statistical_evidence_grade",
        "positive_control_similarity",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _load_modules() -> Dict[str, List[str]]:
    modules: Dict[str, List[str]] = {}
    if not SEED_MODULES.exists():
        return modules
    with open(SEED_MODULES, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            genes = row.get("seed_genes", "")
            gene_list = [g.strip() for g in genes.split(",") if g.strip()]
            modules[row.get("module_id", f"module_{row.get('module_name', '')}")] = gene_list
    return modules


def _module_scores(df: pd.DataFrame) -> pd.DataFrame:
    modules = _load_modules()
    if not modules:
        return pd.DataFrame(columns=["target", "condition", "module_id", "module_name", "overlap", "module_score"])

    module_records = []
    module_names = {}
    with open(SEED_MODULES, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            module_names[row["module_id"]] = row["module_name"]

    for _, row in df.iterrows():
        target = row["target"]
        target_gene = str(target).strip().upper()
        condition = row["condition"] if "condition" in df.columns else row.get("culture_condition", "")
        score_basis = float(row.get("condition_specificity_score", 0) or 0)
        for module_id, genes in modules.items():
            module_genes = {g.strip().upper() for g in genes if g.strip()}
            overlap = 1 if target_gene in module_genes else 0
            if overlap == 0:
                continue
            module_score = overlap * (1.0 + score_basis)
            module_records.append(
                {
                    "target": target,
                    "condition": condition,
                    "module_id": module_id,
                    "module_name": module_names.get(module_id, module_id),
                    "overlap": overlap,
                    "module_score": module_score,
                }
            )
    return pd.DataFrame(module_records)


def _persist_metadata(dataset_id: str, status: str, payload: Dict[str, Any]) -> None:
    path = _dataset_path(dataset_id) / "metadata.json"
    data = {
        "dataset_id": dataset_id,
        "status": status,
        "engine_version": ENGINE_VERSION,
        "schema_version": CARD_SCHEMA_VERSION,
        "signature_set_version": _signature_set_version(),
        "built_at": utc_now(),
    }
    data.update(payload)  # payload may override any of the above if the caller sets them explicitly
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _read_metadata(dataset_id: str) -> Dict[str, Any]:
    path = _dataset_path(dataset_id) / "metadata.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _provenance_block(dataset_id: str) -> Dict[str, Any]:
    """The four version layers (B4) for a dataset, pulled from its persisted metadata."""
    meta = _read_metadata(dataset_id)
    return {
        k: meta.get(k)
        for k in ["dataset_version", "engine_version", "schema_version", "signature_set_version", "built_at"]
        if meta.get(k) is not None
    }


def _safe_limit(df: pd.DataFrame, max_rows: Optional[int]) -> pd.DataFrame:
    if max_rows is None or max_rows <= 0:
        return df
    return df.head(max_rows).copy()


def _json_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    return json.loads(df.where(pd.notna(df), None).to_json(orient="records"))


def _json_object(payload: Dict[str, Any]) -> Dict[str, Any]:
    return json.loads(pd.Series(payload).to_json())


def _evidence_dir_mtime() -> float:
    if not EVIDENCE_CACHE_DIR.exists():
        return 0.0
    mtimes = [p.stat().st_mtime for p in EVIDENCE_CACHE_DIR.glob("*.json")]
    return max(mtimes, default=0.0)
