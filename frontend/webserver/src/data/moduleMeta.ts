// Editorial framing (not evidence) for the real M01-M20 concept modules —
// a clinical-question gloss to help a reader orient. The module id/name/
// category/seed-gene membership itself comes from the real
// individual_concept_profile.load_concept_modules() output (see
// data/dataset.ts); this file only adds explanatory prose alongside it.
export const MODULE_META: Record<string, { desc: string; question: string }> = {
  M01: { desc: "The TCR core receptor complex (CD3 chains + TRBC) — the most upstream initiation point of the CD4 activation signal.", question: "Can CD4 TCR initiation signalling reshape the activation threshold?" },
  M02: { desc: "The proximal TCR signalling chain — a node-dense stretch of kinases and adaptors immediately downstream of receptor engagement, rich in druggable checkpoints.", question: "Which early TCR-downstream nodes behave as druggable regulatory points?" },
  M03: { desc: "The costimulatory axis (CD28/ICOS and ligands) that sets how activation and proliferation programs are re-wired after receptor engagement.", question: "Does costimulation drive reconfiguration of the proliferation/activation program?" },
  M04: { desc: "Inhibitory checkpoint receptors balancing immune suppression against activation.", question: "Does the inhibitory axis show reversible / enhanceable signal?" },
  M05: { desc: "The IL-2 receptor / JAK-STAT survival and proliferation loop — a key branch point between Treg and effector fates.", question: "Is the IL-2 survival & proliferation loop reset by perturbation?" },
  M06: { desc: "Interferon response axis (type I/II receptors + STAT1/IRF) capturing inflammatory-stimulus sensitivity.", question: "Is inflammatory-stimulus sensitivity amplified or dampened?" },
  M07: { desc: "The master transcriptional program for Th1 differentiation.", question: "Does perturbation drive a Th1-like transcriptomic shift?" },
  M08: { desc: "The Th2 differentiation program (GATA3/STAT6 axis + IL4/IL13 effectors).", question: "Does perturbation drive a Th2-like skew?" },
  M09: { desc: "The Th17 inflammatory differentiation program (RORC/STAT3 axis + IL17 effectors) — common in chronic autoimmune inflammation.", question: "Does perturbation drive a Th17-like inflammatory program?" },
  M10: { desc: "The regulatory-T tolerance / suppression program.", question: "Is the tolerance/suppression axis altered?" },
  M11: { desc: "The NF-κB inflammatory signal-amplification axis.", question: "Is innate/inflammatory signal amplification altered?" },
  M12: { desc: "AP-1 / NFAT immediate-early activation response — a directionality sanity check for perturbations.", question: "Do immediate-early activation responses shift in concert?" },
  M13: { desc: "The PI3K-AKT-mTOR metabolic / proliferation signalling axis.", question: "Are metabolic and proliferation signals rewritten?" },
  M14: { desc: "The activation-coupled metabolic reprogramming (MYC/HIF1A/glycolysis).", question: "Does metabolic reprogramming track with activation?" },
  M15: { desc: "Naive/memory homing and lymphoid-tissue positioning program.", question: "Is the naive/memory homing profile preserved?" },
  M16: { desc: "Chemotaxis and tissue-infiltration program.", question: "Are migration / tissue-positioning programs altered?" },
  M17: { desc: "Atypical CD4 cytotoxic / effector-like program.", question: "Does perturbation bias toward effector-like cytotoxic programs?" },
  M18: { desc: "T-cell exhaustion / escape program — used in safety and therapeutic-window assessment.", question: "Does prolonged stimulation induce exhaustion or reversible suppression?" },
  M19: { desc: "Memory-fate / plasticity transcriptional and chromatin program.", question: "Are fate plasticity and stability changed?" },
  M20: { desc: "Cell-cycle / proliferation marker program — a non-specific-proliferation sanity check.", question: "Does perturbation mainly drive proliferation rather than a specific immune pathway?" },
};
