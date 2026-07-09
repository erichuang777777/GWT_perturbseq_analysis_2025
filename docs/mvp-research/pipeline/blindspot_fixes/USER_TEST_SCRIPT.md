# Real-User Test Script — 10-minute moderated usability test

**Platform:** CD4+ T-cell Perturb-seq target-discovery platform
**Why this test:** the whole build is "developer's imagined user." The deepest blindspot
is that no real immunologist or clinician has used it. This script surfaces the
unknown-unknowns only real users produce — how they search, what they expect, where they stall.

---

## Setup (before the session)

- **What you need:** the two prototype HTML files open in a browser
  (`entry_a_rank_board.html`, `entry_b_risk_evidence.html`), a way to record screen +
  audio (or a second person taking notes), and this script.
- **Time:** 10 minutes of tasks + 3 minutes debrief per participant.
- **Recruit 2 people, one per persona.** Do NOT recruit a bioinformatician who
  already knows the dataset — you want a naive domain expert.
- **Golden rule — do not teach.** When they get stuck, ask "what would you try next?"
  and wait. A stall IS the finding. Never point at the button.
- **Think-aloud:** ask them to narrate ("I'm looking for…", "I expected…", "I don't
  know what this means…"). The narration is the data.

---

## Persona 1 — Immunologist (Entry A · Rank Board) · 5 min

*Frame to them:* "You study CD4 T-cell biology. This tool ranks perturbation targets
from a genome-scale screen. Show me how you'd explore it — think aloud."

### Task 1.1 — First 30 seconds (unprompted) · tests blindspot 1 & 2
- **Do:** hand them the open Rank Board, say nothing, watch the first 30 seconds.
- **Observe:** What do they do FIRST? (Hypothesis: they search their own favourite gene,
  not read your ranking.) Do they trust the top of the list, or react to CD3E/LAT being
  "old news"?
- **Success:** they find the search box and/or the novelty badge unaided.
- **Struggle signal:** they scroll the ranked list confused, or say "these are all
  known targets, is that all?"

### Task 1.2 — "Look up your gene" · tests blindspot 1 (the big one)
- **Say:** "Search for a gene you care about that you suspect might NOT be a top hit —
  e.g. IL2RA, or your own."
- **Observe:** When it's a filtered gene, do they understand the funnel diagnosis
  ("in the raw data but didn't pass: too few downstream DE genes")? Or do they read
  "not found" and conclude the tool is incomplete?
- **Success:** they say something like "ah, so it's not missing, it just didn't pass
  the DE threshold."
- **Struggle signal:** they think the gene is absent / the tool is broken.

### Task 1.3 — "Find something new" · tests blindspot 2
- **Say:** "Show me only targets that are NOT already drug-targeted."
- **Observe:** Do they find the novel-only toggle? Once filtered, do they understand
  the distinction between validation hits and discoveries?
- **Success:** toggle found, list changes, they grasp "novel = the tool's value."

### Task 1.4 — "Take it with you" · tests blindspot 5 (action loop)
- **Say:** "You want to bring 5 of these to your lab meeting. What would you do?"
- **Observe:** Do they find CSV export? Is that enough, or do they want more
  (guide RNAs, links, next-step guidance)? **Their answer to "what's missing" here is gold.**

---

## Persona 2 — Clinical researcher (Entry B · Risk & Evidence) · 5 min

*Frame to them:* "You're a clinician-researcher considering an immune target. This tool
gives target-level safety evidence. Explore it — think aloud."

### Task 2.1 — First impression · tests blindspot 3 (positioning)
- **Do:** hand them the open Entry B, watch unprompted.
- **Observe:** Do they land on Tab 1 (Target Safety Lookup) and read it as a
  *research* tool — or do they go straight to the Patient Upload tab expecting a
  *patient* tool? Do they notice the "NOT patient-level clinical advice" line and the
  DEMO label? **Critical safety check:** does anyone treat the demo as a real clinical output?
- **Success:** they correctly read Tab 1 as target-level evidence, recognise Tab 2 as a demo.
- **Struggle / RED FLAG:** they expect patient-specific guidance, or treat the upload
  demo as clinical. If this happens, the positioning still over-promises — note it.

### Task 2.2 — "Check a target's safety" · tests blindspot 6 (jargon)
- **Say:** "Look up VAV1 (or MED12). Is it safe to consider?"
- **Observe:** Do they understand LOEUF / pLI / avoid-tier without help? Do the
  plain-language tooltips get used, and do they help? Do they grasp *why* a
  high-context-specific gene can also be high-risk?
- **Success:** they reach a defensible read ("high constraint → risky to inhibit systemically").
- **Struggle signal:** they read the numbers aloud but can't say what they mean for a decision.

### Task 2.3 — "How much do you trust this?" · tests blindspot 4 (fragility)
- **Say:** "Would you act on this? What would you want to know first?"
- **Observe:** Do they notice the context-boundary banner (CD4 T only, one dataset)?
  Do they over-trust the polished UI, or do they ask about validation / other cell types?
- **Success:** they spontaneously raise the single-dataset / context limitation.
- **Struggle signal:** they'd act on it without questioning the evidence base — meaning
  the caveat isn't prominent enough.

---

## Debrief (3 min, both personas)

Ask verbatim, don't lead:
1. "In one sentence, what does this tool do?" *(tests whether positioning landed)*
2. "What did you expect to be here that wasn't?" *(surfaces unknown-unknowns)*
3. "Was there a moment you felt lost or unsure?" *(pinpoints the stall)*
4. "Would you use this in your actual work? What would have to be true first?"
5. "Anything you didn't trust?"

---

## Capture sheet (fill per participant)

| Task | Found feature unaided? (Y/N) | Understood it? (Y/N) | Time to complete | Quote / stall |
|------|:---:|:---:|:---:|-------|
| 1.1 first 30s | | | | |
| 1.2 gene lookup + funnel | | | | |
| 1.3 novel-only | | | | |
| 1.4 export / next step | | | | |
| 2.1 positioning | | | | |
| 2.2 jargon / tooltips | | | | |
| 2.3 trust / context | | | | |

**Severity rubric for each finding:**
- **Critical** — user reaches a wrong/unsafe conclusion (esp. Task 2.1 treating demo as clinical)
- **Major** — user cannot complete the task / abandons
- **Minor** — user completes but with friction or a wrong first guess

---

## How to read the results

- If **Task 1.2** trips people ("gene is missing") → the funnel diagnosis isn't visible
  enough; make absence-explanation the default first screen.
- If **Task 2.1** trips people (expect patient tool) → the dual-mode reposition didn't
  fully land; strengthen Tab 1's framing further.
- If **Task 2.3** never surfaces the context limit → the banner is being ignored;
  make it a blocking acknowledgement, not passive text.
- **Two participants is enough to find the biggest problems.** Nielsen's rule: ~5 users
  find ~85% of usability issues; 2 domain experts find the show-stoppers. Run this,
  fix the criticals, run 2 more.
