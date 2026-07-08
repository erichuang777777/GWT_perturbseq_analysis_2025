"""Pure grading of already-fetched per-gene evidence snapshots (roadmap Phase 1).

Companion to ``common/overlay_lookup.py``: where that module interprets an
already-loaded *overlay table* (gnomAD/GTEx/membrane), this module interprets
an already-fetched *evidence snapshot* dict -- the JSON that
``evidence.external_cache.load_snapshot`` returns and that the caller injects
into ``core.readiness.compute_readiness`` via ``evidence_lookup``. These
functions perform no I/O, no network call, and cannot raise on a missing/odd
field -- an absent field degrades to ``"unknown"`` (never a fabricated value or
a silent ``0``; ``unknown != 0`` is this repo's headline invariant).

Living here (under ``common/``, not ``evidence/``) is what lets
``core/readiness.py`` grade an injected snapshot without importing the evidence
layer at all -- the same decoupling that moved the overlay-interpretation
functions into ``common/overlay_lookup.py`` (architecture refactor Phase 3).

All fields produced here are **descriptive only**. None is read by
``core/readiness._stage()`` or ``_red_flags()``; none feeds
``readiness_call``/``overall_readiness_stage``/``statistical_evidence_grade``.
They carry the same causal-independence property already enforced for
``safety_window_score`` and ``gnomad_constraint_flag``.

Rationale / citations
---------------------
* Minikel et al., *Nature* 2024 (https://www.nature.com/articles/s41586-024-07316-0):
  human genetic support raises clinical success ~2.6x, and the boost rises with
  the confidence of the causal-gene assignment (OMIM/Mendelian relative success
  ~3.7). This motivates GRADING genetic support into tiers rather than a flat
  yes/no.
* Open Targets L2G / eQTL-colocalisation benchmark, medRxiv 2025
  (https://www.medrxiv.org/content/10.1101/2025.09.23.25336370v1.full): across
  445 diseases, L2G (OR 3.14) does NOT statistically beat nearest-gene (OR
  3.08) and eQTL coloc is worse. So a causal-gene / genetic-support call is
  presented as GRADED and provisional, never authoritative.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

UNKNOWN = "unknown"

# An Open Targets ``genetic_association_score`` at or above this bar is treated
# as a "strong" germline genetic association; a positive value below it is
# "moderate". This is a coarse, disclosed cut on Open Targets' own 0-1
# association-datatype score, NOT a biological absolute -- per the 2025
# benchmark above the assignment is graded, not authoritative.
STRONG_GENETIC_THRESHOLD = 0.5

# Genetic-support confidence tiers, ordered least -> most supported. Grounded in
# what the committed Open Targets snapshots actually contain
# (``sources.open_targets.associated_diseases[].genetic_association_score``);
# the snapshot carries no OMIM/Mendelian-vs-eQTL datatype breakdown, so no such
# tier is emitted here (emitting one would fabricate a distinction the data does
# not support).
GENETIC_TIER_STRONG = "strong_genetic_association"
GENETIC_TIER_MODERATE = "moderate_genetic_association"
GENETIC_TIER_NONE = "no_genetic_association"
GENETIC_TIER_UNKNOWN = UNKNOWN


def genetic_support_confidence_from_evidence(
    evidence: Optional[Dict[str, Any]],
) -> Tuple[str, Any]:
    """Grade an injected evidence snapshot's genetic support into an honest tier.

    Returns ``(tier, max_genetic_association_score)`` where ``tier`` is one of
    ``strong_genetic_association`` / ``moderate_genetic_association`` /
    ``no_genetic_association`` / ``"unknown"``, and the second element is the
    strongest Open Targets ``genetic_association_score`` seen across the target's
    associated diseases (a real passthrough for auditability), or ``"unknown"``
    when nothing was measured.

    Grading is driven ONLY by ``genetic_association_score`` -- deliberately not
    by ``overall_score``, because a high overall association can be entirely
    literature / somatic / expression evidence with zero germline genetic
    support (e.g. VAV1, whose cancer literature drives a high overall score but
    whose genetic_association_score is null/0 throughout). Collapsing those into
    "genetic support" would overstate the strongest single clinical-success
    predictor this repo tracks.

    Honest-degradation contract (``unknown != 0``):
      * no snapshot, or Open Targets not successfully fetched
        (``source_status != "ok"``), or the gene was not resolved in Open
        Targets (empty ``items``) -> ``("unknown", "unknown")`` (unmeasured,
        NOT "no association").
      * Open Targets fetched and the gene resolved, but no associated disease
        carries a positive ``genetic_association_score`` -> a real
        ``("no_genetic_association", 0.0)`` verdict (checked, none found).
    """
    if not evidence:
        return GENETIC_TIER_UNKNOWN, UNKNOWN
    ot = evidence.get("sources", {}).get("open_targets", {})
    if ot.get("source_status") != "ok":
        return GENETIC_TIER_UNKNOWN, UNKNOWN
    if not ot.get("items"):
        # Open Targets answered but did not resolve this gene -- we cannot
        # distinguish "no genetic association" from "gene not in the response",
        # so it stays honestly unknown rather than a fabricated "none".
        return GENETIC_TIER_UNKNOWN, UNKNOWN
    diseases = ot.get("associated_diseases") or []
    positive = [
        float(d.get("genetic_association_score"))
        for d in diseases
        if isinstance(d.get("genetic_association_score"), (int, float))
        and not isinstance(d.get("genetic_association_score"), bool)
        and float(d.get("genetic_association_score")) > 0
    ]
    if not positive:
        return GENETIC_TIER_NONE, 0.0
    max_score = max(positive)
    tier = GENETIC_TIER_STRONG if max_score >= STRONG_GENETIC_THRESHOLD else GENETIC_TIER_MODERATE
    return tier, max_score


def trait_liability_similarity(
    evidence: Optional[Dict[str, Any]],
    adverse_vocab: Optional[Any] = None,
) -> Tuple[str, str]:
    """On-target trait-similarity liability signal -- honest-fallback stub.

    LIABILITY framing (get this right): human genetic support predicts
    **on-target safety liabilities**, not de-risking -- a target whose
    genetically-associated traits resemble known adverse-event terms is a
    HIGHER on-target concern, never a "this is safe" signal (Duffy et al., *Sci
    Adv* 2020, https://www.science.org/doi/10.1126/sciadv.abb6242 -- joint
    genetic features -> ~2.6x side-effect risk; Nat Rev Genet 2025,
    https://www.nature.com/articles/s41576-025-00904-4 -- associated-similar-
    trait targets carry ~2x adverse events).

    Computing this needs a curated adverse-event reference vocabulary (e.g.
    SIDER / MedDRA preferred terms) to match the target's associated
    diseases/traits against. **This repo commits no such vocabulary**, so the
    default path returns ``("unknown", <reason>)`` -- it does NOT fabricate a
    similarity score. This mirrors the repo's established seed + honest-fallback
    pattern (a real reference dropped in later flips this on with no caller
    change).

    ``adverse_vocab`` (optional): if a caller ever supplies a set/collection of
    lower-cased adverse-event trait terms, the target's associated-disease names
    are matched against it and a real ``("match"/"no_match", <detail>)`` verdict
    is returned. Absent that reference (the current state), the result is
    honestly ``"unknown"``.
    """
    if adverse_vocab is None:
        return (
            UNKNOWN,
            "no adverse-event reference vocabulary (e.g. SIDER/MedDRA) is committed in "
            "this repo; on-target trait-similarity liability is not computable without "
            "one, so it is reported unknown rather than fabricated (unknown != 0)",
        )
    ot = evidence.get("sources", {}).get("open_targets", {}) if evidence else {}
    traits = [str(d.get("disease", "")).strip().lower() for d in (ot.get("associated_diseases") or [])]
    matched = sorted({t for t in traits if t and t in adverse_vocab})
    if not matched:
        return ("no_match", "no associated trait overlaps the supplied adverse-event vocabulary")
    return ("match", "associated traits overlapping adverse-event vocabulary: " + ", ".join(matched))
