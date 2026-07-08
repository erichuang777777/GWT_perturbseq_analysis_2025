"""P2/P3: individual-sample concept projection (COMPASS-analog, honest half).

Per ``docs/compass_concept_integration_plan.md`` §3. This is the
**buildable-now, defensible half** of the COMPASS idea:

    one CD4 sample's gene-expression vector
        -> transparent projection onto this repo's 20 CD4 immune concept
           modules (M01-M20)  -> concept activation profile
        -> for each aberrant concept, the already-screened CRISPRi targets
           that sit inside that concept, as HYPOTHESIS-ONLY clues.

**What this deliberately does NOT do** (plan §6): it does not train, or
run, a response / non-response classifier. That needs patient-outcome
labels this repo does not have and must not fabricate. So there is no
black-box predictor anywhere here -- every concept score is the plain mean
of standardized expression over the seed genes actually present in the
input, hand-auditable from the numbers alone.

**Guardrails enforced in code** (plan §0/§3.3/§8), same mechanism as
``population_hypothesis.CAVEAT_TEXT`` / ``signature_explorer.CAVEAT_TEXT``:

- Every report carries a fixed, non-empty ``caveat``: exploratory research
  demo, NOT diagnosis / treatment / efficacy prediction.
- ``unknown != 0``: a concept whose seed genes are entirely absent from the
  input returns ``activation: None`` / ``direction: "unknown"`` -- never a
  fabricated ``0``. A missing concept is not a zero concept.
- Descriptive, not decision-making: nothing here writes back into
  ``readiness_call`` / ``overall_readiness_stage`` / ``statistical_evidence_grade``
  or ``core/readiness.py``. It only *reads* already-built cards/readiness to
  attach hypotheses. It is a standalone module (imports only stdlib + pandas
  + numpy).
- Request-only: this module never writes the input (or anything) to disk.
  It takes a ``sample_expression`` dict and returns a dict. Persistence
  (or the guarantee of none) is the API layer's concern; this module simply
  has no I/O side effects on the input.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

# --- Fixed guardrail text (plan §0) -- carried verbatim on every report. -------

CAVEAT_TEXT = (
    "Exploratory research demo -- NOT diagnosis, NOT treatment advice, NOT "
    "efficacy/response prediction, NOT clinical decision support. Output is a "
    "transparent concept projection (gene-expression vector -> concept "
    "activation profile) plus hypothesis-only target clues. Concept scores are "
    "the plain mean of standardized expression over present seed genes -- no "
    "black-box weights, no trained classifier, no patient-outcome labels. Per "
    "docs/compass_concept_integration_plan.md §0/§3.3: must not be used for any "
    "clinical or personal medical decision. The raw input expression vector is "
    "processed in request memory only and is never stored or transmitted."
)

HYPOTHESIS_CAVEAT = (
    "Hypothesis-only clue: this CRISPRi target sits inside an aberrant concept "
    "in this sample's transparent projection. This is NOT a claim that "
    "modulating it treats, diagnoses, or predicts response for this or any "
    "individual -- it is a research lead to inspect, nothing more."
)

# --- Concept-module loader (honest-fallback; reuses deps._load_modules logic) ---
#
# The seed CSV column contract (module_id, module_name, category, seed_genes,
# primary_question, notes) and the comma-split parse below are replicated from
# api/deps.py::_load_modules (which returns only module_id -> gene list). We do
# not modify deps; we replicate its parse and additionally keep module_name so a
# concept profile is human-readable. Kept independent of P1's concept_schema.py
# on purpose, so this module stands alone.

_DEFAULT_SEED_MODULES = (
    Path(__file__).resolve().parents[2]
    / "sources"
    / "topic15_cd4_tcell_upstream_downstream_seed_modules.csv"
)


def _seed_modules_path(path: Optional[Path] = None) -> Path:
    return Path(path) if path is not None else _DEFAULT_SEED_MODULES


def load_concept_modules(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load the 20 CD4 immune concept modules from the seed CSV.

    Honest-fallback: a missing file returns ``[]`` (never a fabricated
    module). Each entry is
    ``{"module_id", "module_name", "category", "seed_genes": [SYMBOL, ...]}``
    with seed symbols upper-cased for case-insensitive matching against an
    input expression vector.
    """
    seed_path = _seed_modules_path(path)
    modules: List[Dict[str, Any]] = []
    if not seed_path.exists():
        return modules
    with open(seed_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            raw_genes = row.get("seed_genes", "") or ""
            seed_genes = [g.strip().upper() for g in raw_genes.split(",") if g.strip()]
            module_id = row.get("module_id") or f"module_{row.get('module_name', '')}"
            modules.append(
                {
                    "module_id": module_id,
                    "module_name": row.get("module_name", module_id),
                    "category": row.get("category", ""),
                    "seed_genes": seed_genes,
                }
            )
    return modules


def concept_set_version(path: Optional[Path] = None) -> str:
    """Deterministic fingerprint (name@mtime:size) of the seed-module file.

    Mirrors deps._signature_set_version()'s scheme so provenance is
    comparable across the toolkit; honest ``"unknown"`` if the file is absent.
    """
    seed_path = _seed_modules_path(path)
    if not seed_path.exists():
        return "unknown"
    stat = seed_path.stat()
    return f"{seed_path.name}@{int(stat.st_mtime)}:{stat.st_size}"


# --- Transparent projection: sample expression -> concept activation profile ----

# A concept is flagged "aberrant" when |activation| (mean standardized
# expression over its present seed genes) exceeds this many standard deviations.
# Exposed as a parameter; this is only the default.
DEFAULT_ABERRANT_THRESHOLD = 1.0
# Sign epsilon: |activation| below this reads as "neutral", not up/down.
_DIRECTION_EPS = 1e-9

PROJECTION_METHOD = (
    "mean of within-sample standardized expression (z = (x - mean)/std over all "
    "finite input genes) across the seed genes present in the input"
)


def _standardize(sample_expression: Dict[str, float]) -> Dict[str, float]:
    """Within-sample z-score: (x - mean)/std over all finite input genes.

    Hand-auditable and scale-free (TPM vs normalized counts vs a signed
    z-score signature all collapse to the same standardized frame while
    preserving sign). If ``reference`` per-gene baselines are supplied by the
    caller, they are subtracted upstream before this is called. Returns an
    empty dict if there is no usable numeric spread (std == 0 or < 2 genes),
    so the caller degrades every concept to ``unknown`` rather than dividing
    by zero.
    """
    genes: List[str] = []
    values: List[float] = []
    for gene, value in sample_expression.items():
        try:
            fval = float(value)
        except (TypeError, ValueError):
            continue
        if np.isnan(fval) or np.isinf(fval):
            continue
        genes.append(str(gene).strip().upper())
        values.append(fval)
    if len(values) < 2:
        return {}
    arr = np.asarray(values, dtype=float)
    mean = float(arr.mean())
    std = float(arr.std())
    if std == 0.0:
        return {}
    return {gene: (val - mean) / std for gene, val in zip(genes, arr.tolist())}


def project_sample_onto_concepts(
    sample_expression: Dict[str, float],
    modules: List[Dict[str, Any]],
    reference: Optional[Dict[str, float]] = None,
    aberrant_threshold: float = DEFAULT_ABERRANT_THRESHOLD,
) -> List[Dict[str, Any]]:
    """Project one sample's expression vector onto the concept modules.

    For each module, aggregate the sample's standardized expression over the
    module's seed genes that are present in the input. Returns, per module::

        {module_id, module_name, category,
         activation,          # mean standardized expression, or None
         coverage,            # fraction of seed genes present in the input
         n_seed_genes, n_present_genes, present_genes,
         direction,           # "up" | "down" | "neutral" | "unknown"
         aberrant}            # bool: |activation| >= aberrant_threshold

    ``unknown != 0`` (plan §3.1/§8): a module with ZERO seed genes present in
    the input returns ``activation: None`` / ``direction: "unknown"`` /
    ``coverage: 0.0`` -- never a fabricated ``0``.

    ``reference`` (optional) is a ``{gene: baseline_value}`` map subtracted
    per gene before standardizing, to express activation relative to a
    reference distribution; ``None`` (default) standardizes within-sample.
    """
    if reference:
        ref_upper = {str(g).strip().upper(): float(v) for g, v in reference.items()}
        adjusted = {}
        for gene, value in sample_expression.items():
            key = str(gene).strip().upper()
            try:
                fval = float(value)
            except (TypeError, ValueError):
                continue
            adjusted[gene] = fval - ref_upper.get(key, 0.0)
        standardized = _standardize(adjusted)
    else:
        standardized = _standardize(sample_expression)

    profile: List[Dict[str, Any]] = []
    for module in modules:
        seed_genes = module.get("seed_genes", [])
        n_seed = len(seed_genes)
        present = [g for g in seed_genes if g in standardized]
        n_present = len(present)
        coverage = (n_present / n_seed) if n_seed else 0.0

        if n_present == 0:
            # Missing concept is not a zero concept.
            activation: Optional[float] = None
            direction = "unknown"
            aberrant = False
        else:
            activation = float(np.mean([standardized[g] for g in present]))
            if activation > _DIRECTION_EPS:
                direction = "up"
            elif activation < -_DIRECTION_EPS:
                direction = "down"
            else:
                direction = "neutral"
            aberrant = abs(activation) >= aberrant_threshold

        profile.append(
            {
                "module_id": module["module_id"],
                "module_name": module.get("module_name", module["module_id"]),
                "category": module.get("category", ""),
                "activation": activation,
                "coverage": coverage,
                "n_seed_genes": n_seed,
                "n_present_genes": n_present,
                "present_genes": present,
                "direction": direction,
                "aberrant": aberrant,
            }
        )
    return profile


# --- Connect aberrant concepts to already-screened CRISPRi targets --------------


def _screen_direction(effect: Optional[float]) -> Optional[str]:
    if effect is None:
        return None
    try:
        fval = float(effect)
    except (TypeError, ValueError):
        return None
    if np.isnan(fval):
        return None
    if fval < 0:
        return "down"
    if fval > 0:
        return "up"
    return "neutral"


def connect_concepts_to_screen_targets(
    profile: List[Dict[str, Any]],
    target_cards: Optional[pd.DataFrame],
    readiness: Optional[pd.DataFrame],
    modules: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """For each ABERRANT concept, list screened CRISPRi targets inside it.

    A target "sits inside" a concept iff its gene symbol is one of that
    concept's seed genes -- the SAME real target->module membership used by
    ``deps._module_scores`` (target gene in module seed set), not a new
    invented relationship. Each hypothesis carries the target's real screen
    direction (sign of ``ontarget_effect_size``) and its ``readiness_call``
    (read from an already-built readiness table -- never recomputed here), and
    ``HYPOTHESIS_CAVEAT``.

    Returns ``[]`` when there are no cards, no readiness, or no aberrant
    concept -- honestly empty, never fabricated.
    """
    if target_cards is None or target_cards.empty:
        return []
    if modules is None:
        modules = load_concept_modules()
    seed_by_module = {m["module_id"]: set(m.get("seed_genes", [])) for m in modules}

    # Index readiness by (target, condition) -> readiness_call, and a
    # target-only fallback for tables without a matching condition.
    readiness_by_key: Dict[tuple, Dict[str, Any]] = {}
    readiness_by_target: Dict[str, Dict[str, Any]] = {}
    if readiness is not None and not readiness.empty and "target" in readiness.columns:
        for _, r in readiness.iterrows():
            tgt = str(r.get("target", "")).strip().upper()
            cond = str(r.get("condition", "")).strip()
            info = {
                "readiness_call": r.get("readiness_call"),
                "overall_readiness_stage": r.get("overall_readiness_stage"),
            }
            readiness_by_key[(tgt, cond)] = info
            readiness_by_target.setdefault(tgt, info)

    hypotheses: List[Dict[str, Any]] = []
    has_condition = "condition" in target_cards.columns
    has_effect = "ontarget_effect_size" in target_cards.columns

    for concept in profile:
        if not concept.get("aberrant"):
            continue
        seed_set = seed_by_module.get(concept["module_id"], set())
        if not seed_set:
            continue
        for _, card in target_cards.iterrows():
            gene = str(card.get("target", "")).strip().upper()
            if gene not in seed_set:
                continue
            cond = str(card.get("condition", "")).strip() if has_condition else ""
            effect = card.get("ontarget_effect_size") if has_effect else None
            readiness_info = readiness_by_key.get((gene, cond)) or readiness_by_target.get(gene, {})
            hypotheses.append(
                {
                    "gene": card.get("target"),
                    "module_id": concept["module_id"],
                    "module_name": concept["module_name"],
                    "concept_direction": concept["direction"],
                    "concept_activation": concept["activation"],
                    "condition": cond or None,
                    "screen_direction": _screen_direction(effect),
                    "ontarget_effect_size": (float(effect) if _screen_direction(effect) is not None else None),
                    "readiness_call": readiness_info.get("readiness_call"),
                    "overall_readiness_stage": readiness_info.get("overall_readiness_stage"),
                    "caveat": HYPOTHESIS_CAVEAT,
                }
            )
    return hypotheses


# --- Assemble the full individual concept report --------------------------------


def build_individual_concept_report(
    sample_expression: Dict[str, float],
    modules: Optional[List[Dict[str, Any]]] = None,
    target_cards: Optional[pd.DataFrame] = None,
    readiness: Optional[pd.DataFrame] = None,
    reference: Optional[Dict[str, float]] = None,
    aberrant_threshold: float = DEFAULT_ABERRANT_THRESHOLD,
    computed_at: Optional[str] = None,
    screen_data_version: Optional[str] = None,
    seed_modules_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Assemble the individual concept report (plan §3.2 output contract).

    Returns::

        {concept_profile: [...],
         connected_target_hypotheses: [...],
         input_gene_count: int,
         caveat: CAVEAT_TEXT,                      # fixed, non-empty
         provenance: {concept_set_version, screen_data_version,
                      computed_at, projection_method, aberrant_threshold}}

    ``computed_at`` is PASSED IN (never ``datetime.now()`` inside -- the
    caller stamps it, matching this repo's provenance pattern). Descriptive
    only: nothing here touches ``readiness_call``/``_stage()``.
    """
    if modules is None:
        modules = load_concept_modules(seed_modules_path)

    profile = project_sample_onto_concepts(
        sample_expression, modules, reference=reference, aberrant_threshold=aberrant_threshold
    )
    hypotheses = connect_concepts_to_screen_targets(profile, target_cards, readiness, modules=modules)

    return {
        "concept_profile": profile,
        "connected_target_hypotheses": hypotheses,
        "input_gene_count": len(sample_expression),
        "caveat": CAVEAT_TEXT,
        "provenance": {
            "concept_set_version": concept_set_version(seed_modules_path),
            "screen_data_version": screen_data_version if screen_data_version is not None else "unavailable",
            "computed_at": computed_at,
            "projection_method": PROJECTION_METHOD,
            "aberrant_threshold": aberrant_threshold,
        },
    }
