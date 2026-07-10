"""Deterministic readiness engine for CD4 Perturb-seq target cards.

Turns statistical target cards (grades 1-4) into stage-gated readiness calls
following the 12-domain schema in ``sources/topic04_drug_readiness_checklist.csv``:

    12 domain scores  ->  R0-R5 stage  ->  advance / validate / watchlist / deprioritize

Design invariants
-----------------
* Every domain that depends on an external overlay we have NOT built returns the
  literal string ``"unknown"`` -- never a silent 0.
* Red-flag overrides (essential gene, off-target, uncertain direction, batch
  confound) CAP the final call regardless of how strong the statistics look.
* The engine is pure and deterministic: same input -> same output, no randomness,
  and no LIVE network calls at compute time. It may read pre-fetched external
  evidence snapshots -- but only ones already loaded and handed to it by the
  caller (see ``evidence_lookup`` on ``compute_readiness`` below), never by
  importing the evidence layer itself.

Dependency boundary (architecture refactor Phase 3, §4.3⑤)
------------------------------------------------------------
This module imports nothing from ``evidence/``, ``api/``, or any
network-touching package -- every piece of external/fragile data
(druggable-class overlays aside, which are local static gene-list files via
``data.loaders``) is received as an already-loaded value or an injected
lookup callable:

* ``membrane_overlay``/``gtex_overlay``/``gnomad_overlay`` -- already-loaded
  overlay dicts (the caller calls ``evidence.safety_overlay.load_*``  and
  passes the result in); this module only *interprets* them, via the pure
  functions in ``common.overlay_lookup`` (also used natively by
  ``evidence/safety_overlay.py``, so there is exactly one implementation).
* ``evidence_lookup`` -- an optional ``gene -> snapshot|None`` callable the
  caller builds by closing over ``evidence.external_cache.load_snapshot``
  and a cache directory. Before this refactor, ``compute_readiness`` took an
  ``evidence_dir: Path`` and imported ``evidence.external_cache`` itself to
  do the lookup -- exactly the "core imports a fragile edge" anti-pattern
  flagged in ``docs/architecture_refactor_plan.md`` §1 ("危險的依賴方向").
  The caller (``api/app.py``) is unaffected by this change other than
  passing a small lambda instead of a path.

This means disabling/breaking the evidence layer entirely (missing file,
network outage, provider removed) cannot break ``build``/``readiness``/
``calibration`` -- the worst case is every evidence-dependent domain reads
``"unknown"``, never an exception.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Optional, Set

import numpy as np
import pandas as pd

from core.cards import (
    CLINICAL_BENCHMARK_KEYWORDS,
    DRUGGABLE_CLASS_MODALITY,
    PATHWAY_AXIS_HINTS,
    POSITIVE_CONTROLS,
    load_gene_set,
)
from common import coerce
from common.evidence_grading import (
    genetic_support_confidence_from_evidence,
    trait_liability_similarity,
)
from common.overlay_lookup import (
    composite_safety_liability,
    gnomad_flag_from_constraint,
    safety_window_from_gtex,
    tractability_from_membrane_overlay,
)

UNKNOWN = "unknown"

# Repo root, anchored to this file's location (core -> 3_DE_analysis -> src ->
# repo root), NOT to the process cwd. The CLI __main__ block below anchors its
# default overlay paths here so that `python -m core.readiness cards.csv` loads
# the druggability/essentials/broad-effect gene sets regardless of which
# directory it is invoked from. Matches ``api/deps.py``'s ``ROOT`` (same
# parents[3]) so the CLI and the API resolve the same files. Previously these
# defaults were cwd-relative (``Path("metadata/gene_lists")``), so running from
# anywhere but the repo root silently loaded ZERO overlays and collapsed the
# advance tier -- with no error, since missing overlay files degrade to
# "unknown" by design. Anchoring removes the silent-misconfiguration footgun
# without changing the honest-degradation contract for genuinely-absent files.
_REPO_ROOT = Path(__file__).resolve().parents[3]

# Ordered from least to most advanced; used for red-flag capping via min().
CALL_ORDER = ["deprioritize", "watchlist", "validate", "advance"]
STAGE_TO_CALL = {"R0": "deprioritize", "R1": "watchlist", "R2": "validate", "R3": "advance"}


def load_overlays(gene_lists_dir: Path) -> Dict[str, Set[str]]:
    """Load druggable-class + genetics gene sets from ``metadata/gene_lists``.

    Returns a dict mapping overlay name -> upper-cased gene set. Missing files
    are simply absent from the dict (their domains stay ``"unknown"``).

    Thin wrapper around ``data.loaders.load_druggable_class_overlays`` (the
    single implementation, architecture refactor Phase 2) -- this function
    used to be a byte-for-byte duplicate of ``build_target_cards.py``'s
    ``load_druggable_overlays`` (code review had flagged this drift risk).
    """
    from data.loaders import load_druggable_class_overlays

    return load_druggable_class_overlays(gene_lists_dir, DRUGGABLE_CLASS_MODALITY)


def _gene(row: pd.Series) -> str:
    return str(row.get("target", "") or "").strip().upper()


# Re-export for backward compatibility -- canonical implementation now lives
# in common/coerce.py (architecture refactor Phase 1). Note this now follows
# common.coerce.to_float's stringify-then-parse behavior rather than calling
# float(value) directly; see common/coerce.py's module docstring for why
# that's the safer canonical choice, and confirmation that no call site here
# ever passes a literal bool (the only case where the two differ).
_num = coerce.to_float


def _known_pathway(row: pd.Series) -> bool:
    axis = str(row.get("pathway_axis", "") or "")
    if axis and axis != "unassigned":
        return True
    return _gene(row) in {g for genes in PATHWAY_AXIS_HINTS.values() for g in genes}


def _biology_causality(row: pd.Series) -> int:
    grade = _num(row.get("statistical_evidence_grade"))
    known = _known_pathway(row)
    if grade >= 3 and known:
        return 5
    if grade >= 2 or known:
        return 3
    return 0


def _translation(row: pd.Series) -> int:
    replicate = bool(row.get("replicate_pass_flag"))
    cd = _num(row.get("crossdonor_correlation_mean"))
    if replicate and cd >= 0.3:
        return 5
    if replicate:
        return 3
    return 0


def _translation_capped_by(row: pd.Series, translation_score: int) -> str:
    """Purely descriptive explanation for why ``translation_score`` fell short
    of 5, when it did. NEVER read by ``_stage()``/``_red_flags()`` -- this
    cannot change ``readiness_call``/``overall_readiness_stage``, it only
    disambiguates a real blind spot in the raw score: a NaN
    ``crossdonor_correlation_mean`` (the field is unmeasured for ~86% of rows,
    see REPRODUCIBILITY.md) caps translation at 3 the exact same way a
    measured-but-low value does, and the bare integer can't tell a reader
    which one happened. "we couldn't measure this" and "we measured it and it
    was weak" are different findings; conflating them under-calls the vast
    majority of targets for a reason that looks identical to genuine weakness.
    """
    if translation_score >= 5:
        return "not_capped"
    if not bool(row.get("replicate_pass_flag")):
        return "replicate_not_passed"
    cd = row.get("crossdonor_correlation_mean")
    if pd.isna(cd):
        return "missing_crossdonor_data"
    return "measured_low_crossdonor"


def _biomarker(row: pd.Series) -> int:
    return 3 if _num(row.get("n_total_de_genes")) >= 50 else 0


def _disease_relevance(row: pd.Series):
    clinical = str(row.get("clinical_axis", "") or "")
    if (clinical and clinical != "unassigned") or bool(row.get("positive_control_similarity")):
        return 3
    return UNKNOWN


def _clinical_feasibility(row: pd.Series, evidence: Optional[Dict[str, Any]] = None):
    """Prefer real trial evidence (if fetched) over the local benchmark-drug fallback."""
    if evidence:
        trials = evidence.get("sources", {}).get("clinical_trials", {})
        if trials.get("source_status") == "ok" and trials.get("items"):
            phases = {str(t.get("phase") or "").upper() for t in trials["items"]}
            return 5 if phases & {"PHASE3", "PHASE4"} else 3
    drug = str(row.get("nearest_success_drug", "") or "").strip()
    return 3 if drug else UNKNOWN


def _human_genetic_from_evidence(evidence: Optional[Dict[str, Any]]):
    """Return 'yes'/'no' if an Open Targets snapshot was actually fetched, else None."""
    if not evidence:
        return None
    ot = evidence.get("sources", {}).get("open_targets", {})
    if ot.get("source_status") != "ok":
        return None
    return "yes" if ot.get("items") else "no"


def _tractability(gene: str, overlays: Optional[Dict[str, Set[str]]]):
    """Return (modality, score) from local druggable-class overlays, else unknown."""
    if not overlays:
        return UNKNOWN, UNKNOWN
    for name, modality in DRUGGABLE_CLASS_MODALITY.items():
        genes = overlays.get(name)
        if genes and gene in genes:
            return modality, 3
    # Overlays supplied but gene not in any druggable class.
    if any(name in overlays for name in DRUGGABLE_CLASS_MODALITY):
        return "none", 0
    return UNKNOWN, UNKNOWN


def _human_genetic(gene: str, overlays: Optional[Dict[str, Set[str]]]):
    if not overlays:
        return UNKNOWN
    sources = [overlays.get("gwascatalog"), overlays.get("clinvar_path_likelypath")]
    if not any(s for s in sources):
        return UNKNOWN
    return "yes" if any(gene in s for s in sources if s) else "no"


def _red_flags(
    row: pd.Series,
    gene: str,
    essentials: Optional[Set[str]],
    broad_effect_genes: Optional[Set[str]] = None,
):
    """Return (list of override tokens, capped_call)."""
    overrides = []
    cap_idx = len(CALL_ORDER) - 1  # advance
    if essentials and gene in essentials:
        overrides.append("essential_gene")
        cap_idx = min(cap_idx, CALL_ORDER.index("watchlist"))
    # Broad/pleiotropic chromatin-transcription-machinery genes (Mediator, SAGA,
    # HAT/HDAC, SWI/SNF, etc.) can dominate high-DE rankings without being a
    # narrow immune-pathway hit. Distinct from core essentiality (Hart screen).
    if broad_effect_genes and gene in broad_effect_genes and "essential_gene" not in overrides:
        overrides.append("broad_effect")
        cap_idx = min(cap_idx, CALL_ORDER.index("watchlist"))
    if bool(row.get("offtarget_flag")):
        overrides.append("high_offtarget")
        cap_idx = min(cap_idx, CALL_ORDER.index("watchlist"))
    reason = str(row.get("score_cap_reason", "") or "")
    if (not bool(row.get("ontarget_significant"))) or "direction_unclear" in reason:
        overrides.append("uncertain_direction")
        cap_idx = min(cap_idx, CALL_ORDER.index("validate"))
    if str(row.get("batch_sensitivity_flag", "")) == "sensitive":
        overrides.append("batch_confounded")
        cap_idx = min(cap_idx, CALL_ORDER.index("validate"))
    # CRISPRi's causal chain is target-suppressed -> downstream transcription
    # changes. If the target itself was never confirmed knocked down, the
    # downstream DE is not causally interpretable, regardless of how strong
    # the DE signal looks. "not_measurable" (baseline expression MEASURED and
    # too low to ever assess) is worse than "weak" (some signal, just not
    # confirmed), so it caps more strictly.
    #
    # "not_assessed" (no knockdown data at all, e.g. a guide-less upload) is
    # deliberately NOT a red flag: it is genuinely unknown, not a measured
    # failure (unknown != 0). Penalizing it would fabricate an "NTC expression
    # too low" claim about an upload that never had NTC cells and wrongly cap
    # the whole dataset. Such uploads are still bounded by the real robustness
    # gates (no guide data -> grade caps at 2, no cross-donor/guide support ->
    # translation score 0), so they do not advance on the strength of an
    # unassessable knockdown.
    kd_status = str(row.get("kd_status", "") or "")
    if kd_status == "not_measurable":
        overrides.append("kd_not_measurable")
        cap_idx = min(cap_idx, CALL_ORDER.index("watchlist"))
    elif kd_status == "weak":
        overrides.append("kd_weak")
        cap_idx = min(cap_idx, CALL_ORDER.index("validate"))
    return overrides, cap_idx


def _gnomad_loeuf_pli(gene_ensembl: str, overlay: Optional[Dict[str, Any]]):
    """Raw (loeuf, pli) passthrough values from the gnomAD overlay, else (unknown, unknown).

    Purely descriptive passthrough alongside ``gnomad_flag_from_constraint`` --
    never read by ``_stage()``/``_red_flags()``.
    """
    if not overlay or not overlay.get("available") or not gene_ensembl:
        return UNKNOWN, UNKNOWN
    table = overlay["table"]
    row = table[table["ensembl_id"] == gene_ensembl]
    if row.empty:
        return UNKNOWN, UNKNOWN
    r = row.iloc[0]
    loeuf = r["loeuf"]
    pli = r["pli"]
    loeuf_out = UNKNOWN if pd.isna(loeuf) else float(loeuf)
    pli_out = UNKNOWN if pd.isna(pli) else float(pli)
    return loeuf_out, pli_out


def _stage(biology: int, translation: int, tractability, human_genetic, essential: bool, grade: float) -> str:
    trac = tractability if isinstance(tractability, (int, float)) else 0
    if biology == 0 or (essential and grade <= 1):
        return "R0"
    if biology >= 3 and translation == 5 and (trac >= 3 or human_genetic == "yes"):
        return "R3"
    if biology >= 3 and translation >= 3:
        return "R2"
    if biology >= 3:
        return "R1"
    return "R0"


def _next_step(overrides, tractability, human_genetic, translation: int) -> str:
    if "kd_not_measurable" in overrides:
        return "target expression too low in NTC cells to assess knockdown; downstream DE is not causally interpretable as-is"
    if "kd_weak" in overrides:
        return "confirm on-target knockdown (independent guide or protein-level assay) before trusting downstream DE"
    if "essential_gene" in overrides:
        return "orthogonal viability/essentiality control to separate a specific effect from general fitness"
    if "broad_effect" in overrides:
        return "check essentiality/viability and pathway specificity before treating this as a narrow immune hit"
    if "high_offtarget" in overrides:
        return "independent non-overlapping sgRNA / CRISPRi validation to rule out off-target"
    if "batch_confounded" in overrides:
        return "replicate Stim48hr in an independent run to break the condition-batch confound"
    if "uncertain_direction" in overrides:
        return "confirm knockdown and on-target effect direction"
    if tractability == UNKNOWN:
        return "annotate druggability (ChEMBL / Open Targets tractability)"
    if human_genetic == UNKNOWN:
        return "check human genetic support (Open Targets Genetics / GWAS)"
    if translation < 5:
        return "replicate across additional donors/guides to strengthen robustness"
    return "advance to functional / protein-level validation assay"


def _reasons(row: pd.Series, domains: Dict[str, Any], overrides, stage: str, call: str) -> str:
    grade = _num(row.get("statistical_evidence_grade"))
    parts = [
        f"biology {domains['biology_causality_score']} (grade {int(grade) if grade == grade else 'NA'}, pathway {row.get('pathway_axis', 'NA')})",
        f"translation {domains['translation_score']} (replicate_pass={bool(row.get('replicate_pass_flag'))}, crossdonor {row.get('crossdonor_correlation_mean')})",
        f"tractability {domains['tractability_score']} ({domains['tractability_modality']})",
        f"genetics {domains['human_genetic_support']}",
        f"biomarker {domains['biomarker_score']}",
    ]
    if overrides:
        parts.append("RED FLAGS " + ",".join(overrides) + f" -> capped {call}")
    parts.append(f"stage {stage}")
    return "; ".join(parts)


def compute_readiness(
    cards: pd.DataFrame,
    overlays: Optional[Dict[str, Set[str]]] = None,
    essentials: Optional[Set[str]] = None,
    broad_effect_genes: Optional[Set[str]] = None,
    evidence_lookup: Optional[Callable[[str], Optional[Dict[str, Any]]]] = None,
    membrane_overlay: Optional[Dict[str, Any]] = None,
    gtex_overlay: Optional[Dict[str, Any]] = None,
    gnomad_overlay: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Compute readiness domains, R-stage, call, reasons and next step per card.

    ``evidence_lookup``, if given, is a ``gene_symbol -> snapshot|None``
    callable (see ``contracts.interfaces.EvidenceProvider`` for the Protocol
    shape) -- typically a small closure the caller builds over
    ``evidence.external_cache.load_snapshot`` and a fixed cache directory,
    e.g. ``lambda gene: load_snapshot(EVIDENCE_CACHE_DIR, gene)``. This
    module never imports the evidence layer itself (architecture refactor
    Phase 3, §4.3⑤) -- the caller is responsible for supplying pre-fetched
    snapshots. When a snapshot exists and a source was actually fetched
    (``source_status == "ok"``), it upgrades ``clinical_feasibility`` and
    ``human_genetic_support`` beyond the local-overlay fallback. Genes with
    no snapshot (or no ``evidence_lookup`` at all) are unaffected -- this
    never fabricates evidence.

    ``membrane_overlay``/``gtex_overlay``, if given (the dict returned by
    ``evidence.safety_overlay.load_membrane_tractability_overlay`` /
    ``load_gtex_safety_overlay``), upgrade ``tractability_modality`` and
    ``safety_window_score`` respectively beyond the local gene-list fallback,
    same upgrade-not-replace pattern as the evidence snapshot above. Omitted
    or unavailable overlays leave existing behavior (local overlays /
    ``unknown``) completely unchanged.

    ``gnomad_overlay``, if given (the dict returned by
    ``evidence.safety_overlay.load_gnomad_constraint_overlay``), adds three
    new, purely additive output columns -- ``gnomad_constraint_flag``,
    ``gnomad_loeuf``, ``gnomad_pli`` -- a second, independent safety signal
    alongside ``safety_window_score`` (§C of ``docs/next_phases_plan.md``).
    It is never read by ``_stage()`` or ``_red_flags()`` and therefore can
    never change ``readiness_call``/``overall_readiness_stage``; omitting it
    leaves every existing column completely unchanged.

    Five further purely additive, DESCRIPTIVE columns are always emitted
    (roadmap Phase 1):

    * ``genetic_support_confidence`` + ``genetic_support_max_genetic_score``
      (P1.1/P1.2) -- an honest tier for the target's germline genetic support,
      graded from the injected Open Targets snapshot's
      ``associated_diseases[].genetic_association_score``
      (``strong``/``moderate``/``no``-genetic-association, or ``"unknown"`` when
      no snapshot was fetched). Graded, not authoritative (see
      ``common/evidence_grading.py``).
    * ``composite_safety_liability`` (P1.3) -- a disclosed on-target safety
      LIABILITY tier (``high``/``moderate``/``low``/``"unknown"``) composing the
      gnomAD constraint flag + GTEx off-context breadth; higher constraint +
      broader expression = MORE concern, never de-risking (see
      ``common/overlay_lookup.composite_safety_liability``).
    * ``trait_liability_similarity`` + ``trait_liability_similarity_reason``
      (P1.3) -- an honest-fallback stub that returns ``"unknown"`` + a reason,
      because this repo commits no adverse-event reference vocabulary to match
      associated traits against.

    A sixth additive, DESCRIPTIVE column (docs/ux_trust_fix_plan.md Wave 1b):

    * ``translation_capped_by`` -- disambiguates WHY ``translation_score`` is
      below 5, when it is: ``"missing_crossdonor_data"`` (a NaN
      ``crossdonor_correlation_mean`` -- unmeasured for ~86% of rows, see
      REPRODUCIBILITY.md) vs. ``"measured_low_crossdonor"`` (a real value that
      just didn't clear the 0.3 gate) vs. ``"replicate_not_passed"`` vs.
      ``"not_capped"``. The raw integer alone cannot tell a reader "we
      couldn't measure this" from "we measured it and it was weak" -- both
      cap translation at 3 identically. Computed from ``translation_score``
      and the row's own fields; never read by ``_stage()``/``_red_flags()``,
      so it cannot change ``readiness_call``/``overall_readiness_stage``.

    Like the gnomAD columns, none of these five is read by ``_stage()`` /
    ``_red_flags()``, so none can change ``readiness_call`` /
    ``overall_readiness_stage``.
    """
    if cards.empty:
        return cards.copy()

    evidence_cache: Dict[str, Any] = {}

    def _evidence_for(gene: str) -> Optional[Dict[str, Any]]:
        if evidence_lookup is None:
            return None
        if gene not in evidence_cache:
            evidence_cache[gene] = evidence_lookup(gene)
        return evidence_cache[gene]

    records = []
    for _, row in cards.iterrows():
        gene = _gene(row)
        grade = _num(row.get("statistical_evidence_grade"))
        essential = bool(essentials and gene in essentials)
        broad_effect = bool(broad_effect_genes and gene in broad_effect_genes)
        evidence = _evidence_for(gene)

        biology = _biology_causality(row)
        translation = _translation(row)
        translation_capped_by = _translation_capped_by(row, translation)
        biomarker = _biomarker(row)
        disease = _disease_relevance(row)
        clinical = _clinical_feasibility(row, evidence)
        gene_ensembl = str(row.get("target_id", "") or "")
        trac_modality, trac_score = (
            tractability_from_membrane_overlay(gene_ensembl, membrane_overlay) if membrane_overlay else (UNKNOWN, UNKNOWN)
        )
        if trac_modality == UNKNOWN:
            trac_modality, trac_score = _tractability(gene, overlays)
        genetics = _human_genetic_from_evidence(evidence) or _human_genetic(gene, overlays)
        # Essentiality is already fully captured by the separate "essential_gene"
        # red-flag override and _stage()'s grade cap below -- safety_window_score
        # must not also special-case it, or real GTEx off-context-expression data
        # gets silently discarded and replaced by a fabricated 0, which reads as
        # the *safest* possible value on this metric's own documented scale
        # (higher = broader off-context expression = narrower safety window) for
        # exactly the gene class that most needs honest reporting here.
        safety = safety_window_from_gtex(gene_ensembl, gtex_overlay) if gtex_overlay else UNKNOWN
        gnomad_flag = gnomad_flag_from_constraint(gene_ensembl, gnomad_overlay) if gnomad_overlay else UNKNOWN
        gnomad_loeuf, gnomad_pli = _gnomad_loeuf_pli(gene_ensembl, gnomad_overlay)
        # Descriptive genetic-support tiering (roadmap P1.1/P1.2) and the
        # composite safety-LIABILITY view + trait-similarity liability stub
        # (P1.3). All three are graded/disclosed annotations only: they are NOT
        # passed to _stage()/_red_flags() and therefore cannot move
        # readiness_call/overall_readiness_stage -- the exact causal-independence
        # property already enforced for safety_window_score and gnomad_*.
        genetic_support_confidence, genetic_support_max_score = genetic_support_confidence_from_evidence(evidence)
        composite_liability = composite_safety_liability(gnomad_flag, safety)
        trait_similarity, trait_similarity_reason = trait_liability_similarity(evidence)
        immune_flags = []
        if bool(row.get("offtarget_flag")):
            immune_flags.append("offtarget")
        if str(row.get("batch_sensitivity_flag", "")) == "sensitive":
            immune_flags.append("batch_sensitive")
        if broad_effect:
            immune_flags.append("broad_effect")

        overrides, cap_idx = _red_flags(row, gene, essentials, broad_effect_genes)
        stage = _stage(biology, translation, trac_score, genetics, essential, grade)
        stage_call_idx = CALL_ORDER.index(STAGE_TO_CALL[stage])
        call = CALL_ORDER[min(stage_call_idx, cap_idx)]

        domains = {
            "biology_causality_score": biology,
            "disease_relevance_score": disease,
            "human_genetic_support": genetics,
            "tractability_modality": trac_modality,
            "tractability_score": trac_score,
            "safety_window_score": safety,
            "gnomad_constraint_flag": gnomad_flag,
            "gnomad_loeuf": gnomad_loeuf,
            "gnomad_pli": gnomad_pli,
            "genetic_support_confidence": genetic_support_confidence,
            "genetic_support_max_genetic_score": genetic_support_max_score,
            "composite_safety_liability": composite_liability,
            "trait_liability_similarity": trait_similarity,
            "trait_liability_similarity_reason": trait_similarity_reason,
            "cd4_immune_red_flags": ",".join(immune_flags) if immune_flags else "none",
            "biomarker_score": biomarker,
            "translation_score": translation,
            "translation_capped_by": translation_capped_by,
            "clinical_feasibility_score": clinical,
        }
        records.append(
            {
                "target": row.get("target"),
                "condition": row.get("condition"),
                **domains,
                "red_flag_override": ";".join(overrides) if overrides else "none",
                "overall_readiness_stage": stage,
                "readiness_call": call,
                "readiness_reasons": _reasons(row, domains, overrides, stage, call),
                "next_validation_step": _next_step(overrides, trac_score, genetics, translation),
                "has_external_evidence": bool(evidence),
            }
        )
    return pd.DataFrame.from_records(records)


def readiness_summary(readiness: pd.DataFrame, overlays: Optional[Dict[str, Set[str]]] = None) -> Dict[str, Any]:
    """Aggregate counts for the API/dashboard."""
    if readiness.empty:
        # Keep the same key set as the populated branch so clients never hit a
        # KeyError on empty datasets.
        return {
            "rows": 0,
            "counts": {},
            "call_counts": {},
            "overlays_used": [],
            "overlays_missing": ["chembl", "open_targets_genetics", "depmap", "patient_scrna"],
            "unique_targets_with_external_evidence": 0,
        }
    overlays_used = []
    if overlays:
        if any(name in overlays for name in DRUGGABLE_CLASS_MODALITY):
            overlays_used.append("druggable_class")
        if overlays.get("gwascatalog") or overlays.get("clinvar_path_likelypath"):
            overlays_used.append("genetics")
    overlays_missing = ["chembl", "open_targets_genetics", "depmap", "patient_scrna"]
    n_with_evidence = int(readiness["has_external_evidence"].sum()) if "has_external_evidence" in readiness.columns else 0
    if n_with_evidence:
        overlays_used.append("external_evidence(clinical_trials,literature)")
    return {
        "rows": int(len(readiness)),
        "counts": readiness["overall_readiness_stage"].value_counts().to_dict(),
        "call_counts": readiness["readiness_call"].value_counts().to_dict(),
        "overlays_used": overlays_used,
        "overlays_missing": overlays_missing,
        "unique_targets_with_external_evidence": int(readiness.loc[readiness["has_external_evidence"], "target"].nunique()) if n_with_evidence else 0,
    }


if __name__ == "__main__":
    import argparse

    # Composition-root import: this is the CLI script entrypoint, not
    # importable library code (it only runs under `if __name__ ==
    # "__main__"`), so it plays the same role as api/app.py -- loading the
    # evidence layer and injecting it into compute_readiness -- without
    # making core/readiness.py itself import evidence/ at module scope (see
    # this module's "Dependency boundary" docstring section above; `grep -n
    # "^import\|^from" core/*.py` finds no evidence import because this line
    # is indented, i.e. not reachable by simply importing this module).
    from evidence.external_cache import load_snapshot as _load_evidence_snapshot

    parser = argparse.ArgumentParser(description="Compute readiness calls from a target-cards CSV.")
    parser.add_argument("cards", type=Path)
    # Defaults are anchored to _REPO_ROOT (this file's location), NOT the cwd,
    # so the CLI loads the overlay/essentials/broad-effect files from any
    # working directory. An explicit --gene-lists (etc.) still wins.
    parser.add_argument("--gene-lists", type=Path, default=_REPO_ROOT / "metadata" / "gene_lists")
    parser.add_argument("--essentials", type=Path, default=_REPO_ROOT / "metadata" / "gene_lists" / "core_essentials_hart.tsv")
    parser.add_argument("--broad-effect", type=Path, default=_REPO_ROOT / "sources" / "broad_effect_genes.txt")
    parser.add_argument("--evidence-dir", type=Path, default=_REPO_ROOT / "sources" / "target_tool_cache" / "_evidence")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    cards_df = pd.read_csv(args.cards)
    ov = load_overlays(args.gene_lists)
    ess = load_gene_set(args.essentials)
    broad = load_gene_set(args.broad_effect)
    # Loud (but non-fatal) guard, scoped to the CLI call site ONLY -- never
    # inside the shared load_overlays(), which the API also calls and which must
    # stay quiet under its honest-degradation contract. Keyed on "loaded zero
    # overlays" regardless of whether the directory exists, so it also catches a
    # wrong-but-present cwd directory. Zero overlays means every druggability /
    # genetics domain reads "unknown" and the advance tier is under-called; this
    # turns that previously-silent misconfiguration into a visible warning.
    if not ov:
        import warnings

        warnings.warn(
            f"load_overlays returned 0 gene sets from {args.gene_lists!s} -- "
            "druggability/genetics domains will all read 'unknown' and the "
            "advance tier will be under-called. Pass --gene-lists pointing at "
            "the repo's metadata/gene_lists directory.",
            RuntimeWarning,
            stacklevel=2,
        )
    evidence_dir = args.evidence_dir
    result = compute_readiness(
        cards_df,
        overlays=ov,
        essentials=ess,
        broad_effect_genes=broad,
        evidence_lookup=lambda gene: _load_evidence_snapshot(evidence_dir, gene),
    )
    if args.output:
        result.to_csv(args.output, index=False)
    print(readiness_summary(result, overlays=ov))
