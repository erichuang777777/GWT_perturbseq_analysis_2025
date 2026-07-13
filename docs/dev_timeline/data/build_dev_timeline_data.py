#!/usr/bin/env python3
"""
Reproduce the raw data behind the GWT_perturbseq_analysis_2025 development
dot-flow chart, directly from git history.

Run from inside a clone of erichuang777777/GWT_perturbseq_analysis_2025:

    python3 build_dev_timeline_data.py [--repo /path/to/repo] [--out ./dev_timeline_data]

Requires: git (on PATH), Python 3.8+. No third-party packages.

Outputs (written to --out, default ./dev_timeline_data):
  commits_classified.csv   one row per non-merge commit: sha, timestamp, day,
                            8h-slot, work-type category, diff size (ins+del),
                            branch-lane, is_human_touch flag, subject
  grid_by_category.json    the exact [n, diff_lines, is_human] grid per
                            category x (day, 8h-slot) cell used to size/colour
                            every dot in the chart
  bug_events.json          the 11 known incident commits mapped to
                            category/day/slot, for the red dashed rings
  plan_docs.json           the 12 planning/decision-doc commits mapped to
                            category/day/slot, for the star markers
  README.txt               column definitions

Methodology (see chat writeup for full narrative):
  - A commit is attributed to the PR that introduced it via
    `git rev-list <merge>^1..<merge>^2` for every "Merge pull request #N"
    commit on origin/main. Commits not claimed by any PR (direct pushes) are
    the "manual" branch-lane.
  - "is_human_touch" is true if: the commit is on the manual branch-lane, OR
    its subject matches /^sync main/i or /^Merge main\\b/i (a human-run
    conflict-resolution merge embedded inside an AI branch), OR it matches
    /^Perturbase review:/i (a known hand-authored review commit).
  - The 5 work-type categories (data_processing / external_integration /
    stats_analysis / visualization / documentation) are assigned per commit
    by line-change-weighted majority vote over the file paths it touches
    (see classify_file() below) -- this is a heuristic, not a hand-checked
    label, and will misclassify a small fraction of mixed-purpose commits.
  - "diff size" = sum of (insertions + deletions) from `git log --numstat`,
    excluding the top-level "Merge pull request #N" commits themselves
    (which carry no diff of their own).
  - Bucketing is by author-date in UTC, cut into three 8-hour slots per day
    (00-08 / 08-16 / 16-24).
"""
import argparse, json, os, re, subprocess, sys
from collections import defaultdict
from datetime import datetime, timezone

def run(cmd, cwd):
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0 and r.stderr.strip():
        sys.stderr.write(r.stderr)
    return r.stdout

def classify_branch(branch):
    if branch is None:
        return "manual"
    if branch == "add-react-webserver-frontend":
        return "manual"
    if branch.startswith("codex"):
        return "codex"
    if branch == "claude/drug-discovery-tool-plan-258jof":
        return "main"
    if branch == "claude/pr10-executed-in-sandbox":
        return "sandbox"
    if branch in ("claude/wiki-init-docs-x5mj9m", "claude/frontend-persona-design-doc"):
        return "wiki"
    if branch in ("claude/module-alignment-doc", "claude/signed-de-application",
                  "claude/level4-external-validation", "claude/perturbase-review-deliverables",
                  "claude/perturbase-english-figures-bilingual", "claude/closure-audit-three-axis"):
        return "sandbox"
    return "main"

def classify_file(path):
    p = path.lower()
    base = p.rsplit("/", 1)[-1]
    if (p.startswith("frontend/") or "/dashboard/" in p or p.endswith((".tsx", ".jsx", ".css"))
            or "figure_scripts" in p or "/figures/" in p or p.endswith((".png", ".svg", ".jpeg", ".jpg"))
            or "plot" in base):
        return "visualization"
    if (p.endswith(".md") or p.startswith("wiki/") or p.startswith("sources/")
            or p in ("readme.md", "license", "data_license.md", "claude.md")):
        return "documentation"
    ext_kw = ["gnomad", "lincs", "string", "gwas", "clinicaltrial", "external_evidence", "mechanism_graph",
              "safety_overlay", "pathway_network", "disease_drug", "cell_integration", "level4", "overlay",
              "opentarget", "chembl", "depmap", "paper_regulators", "tractability"]
    if any(k in p for k in ext_kw):
        return "external_integration"
    dp_kw = ["1_preprocess", "2_embedding", "scripts/", "makefile", "environment.yaml", "make_pseudobulk",
             "freeze_pipeline", "target_tool_cache/imports", "de_config", "cellranger", "ingest", "qc_plots", "sgrna"]
    if any(k in p for k in dp_kw):
        return "data_processing"
    stats_kw = ["3_de_analysis", "10_ml_perturbation", "robust_ranking", "genetic_double_support",
                "perturbation_prediction", "triage_view", "concept_annotation", "population_hypothesis",
                "translation", "readiness", "calibration", "signed_module_effect", "signed_de",
                "t2_classifier", "core/readiness"]
    if any(k in p for k in stats_kw):
        return "stats_analysis"
    if p.startswith("tests/"):
        return "stats_analysis"
    return "data_processing"

HUMAN_SYNC_RE = re.compile(r"^sync main|^Merge main\b", re.I)
PERTURBASE_RE = re.compile(r"^Perturbase review:", re.I)

def bucket(at):
    dt = datetime.fromtimestamp(at, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d"), dt.hour // 8, dt

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--out", default="./dev_timeline_data")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    merges_raw = run("git log origin/main --merges --format='%H|%P|%at|%s'", args.repo)
    merges = []
    for line in merges_raw.splitlines():
        if not line.strip():
            continue
        h, parents, at, subj = line.split("|", 3)
        m = re.search(r"Merge pull request #(\d+) from erichuang777777/(\S+)", subj)
        merges.append(dict(h=h, parents=parents.split(" "), at=int(at), subj=subj,
                            branch=m.group(2) if m else None, prnum=int(m.group(1)) if m else None))
    pr_merges = [m for m in merges if m["prnum"] is not None]
    pr_merge_shas = {m["h"] for m in pr_merges}

    commit_lane = {}
    for m in sorted(pr_merges, key=lambda x: x["at"]):
        if len(m["parents"]) != 2:
            continue
        p1, p2 = m["parents"]
        lane = classify_branch(m["branch"])
        for sha in run(f"git rev-list {p1}..{p2}", args.repo).split():
            commit_lane[sha] = lane

    all_raw = run("git log origin/main --format='%H|%at|%ae|%an|%s'", args.repo)
    all_commits = []
    for line in all_raw.splitlines():
        if not line.strip():
            continue
        h, at, ae, an, subj = line.split("|", 4)
        all_commits.append(dict(h=h, at=int(at), ae=ae, an=an, subj=subj))
    for c in all_commits:
        if c["h"] in commit_lane or c["h"] in pr_merge_shas:
            continue
        commit_lane[c["h"]] = "manual"

    # git log --numstat shows no diff at all for merge commits by default, so
    # regular (non-merge) commits are read in bulk, and the handful of
    # non-PR "sync main" / "Merge main ..." merge commits (real human
    # conflict-resolution content, not GitHub's own "Merge pull request"
    # commits) are diffed individually against their first parent.
    numstat_raw = run("git log origin/main --no-merges --format='@@%H' --numstat", args.repo)
    files_by_sha = defaultdict(list)
    cur = None
    for line in numstat_raw.splitlines():
        if line.startswith("@@"):
            cur = line[2:]
        elif line.strip() and cur:
            parts = line.split("\t")
            if len(parts) >= 3:
                a = 0 if parts[0] == "-" else int(parts[0])
                d = 0 if parts[1] == "-" else int(parts[1])
                files_by_sha[cur].append((parts[2], a, d))

    parents_by_sha = {m["h"]: m["parents"] for m in merges}
    for m in merges:
        if m["h"] in pr_merge_shas or len(m["parents"]) != 2:
            continue
        p1 = m["parents"][0]
        out = run(f"git diff {p1} {m['h']} --numstat", args.repo)
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) >= 3:
                a = 0 if parts[0] == "-" else int(parts[0])
                d = 0 if parts[1] == "-" else int(parts[1])
                files_by_sha[m["h"]].append((parts[2], a, d))

    def is_human(c):
        lane = commit_lane.get(c["h"], "manual")
        if lane == "manual":
            return True
        if HUMAN_SYNC_RE.search(c["subj"]) or PERTURBASE_RE.search(c["subj"]):
            return True
        return False

    rows = []
    cells = defaultdict(lambda: {"n": 0, "diff": 0, "human": False})
    for c in all_commits:
        if c["h"] in pr_merge_shas:
            continue
        files = files_by_sha.get(c["h"], [])
        votes, total = defaultdict(int), 0
        for path, a, d in files:
            w = a + d
            votes[classify_file(path)] += w
            total += w
        if total == 0:
            votes = defaultdict(int)
            for path, a, d in files:
                votes[classify_file(path)] += 1
        category = max(votes.items(), key=lambda kv: kv[1])[0] if votes else "documentation"
        diff = sum(a + d for _, a, d in files)
        day, slot, dt = bucket(c["at"])
        human = is_human(c)
        rows.append(dict(sha=c["h"], iso=dt.isoformat(), day=day, slot=slot,
                          category=category, diff=diff, lane=commit_lane.get(c["h"], "manual"),
                          is_human=human, subject=c["subj"]))
        if day != "2026-07-05":  # exclude the pre-sprint founding snapshot from the category grid
            key = (category, day, slot)
            cells[key]["n"] += 1
            cells[key]["diff"] += diff
            if human:
                cells[key]["human"] = True

    rows.sort(key=lambda r: r["iso"])
    import csv
    with open(os.path.join(args.out, "commits_classified.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["sha", "iso", "day", "slot", "category", "diff", "lane", "is_human", "subject"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    grid = {k[0] + "|" + k[1] + "|" + str(k[2]): v for k, v in cells.items()}
    json.dump(grid, open(os.path.join(args.out, "grid_by_category.json"), "w"), indent=1, ensure_ascii=False)

    row_by_sha = {r["sha"]: r for r in rows}

    BUG_SHAS = {
        "e2399ff70d9344d418b8d83f2dcd7e565cd4ba24": "C3 automated test suite (defensive, pre-empts future regressions)",
        "33b36c67b323309b4fe22320e7f4841d5e128563": "readiness CLI cwd footgun: silent zero-overlay fallback",
        "89b5d853eeabbbe74b920de780d1c26ebab81484": "gnomAD bulk coverage 6% -> 97%",
        "32478f6700e8b5e2284139f28348575ae5d6e7f4": "IL2RA fixture rendered as every gene's real profile",
        "bcfde343ef8df7954cd31f9d6b3e607ee46f1174": "UX blindspot batch (human sync-merge commit)",
        "32c7d924042b6e9ce30d0d636e59627d0b2b8acd": "parity_03 shape-label bug",
        "046e7d496fb45f96b6a8f0f10c5a13958f5945e7": "reproducibility shape-column bug",
        "1e2a159515f04ab3beda4a55f02227a337f8a6a1": "external QA agent: 9 findings logged",
        "2217ca7afc0eee9404585ed6e427a9aca8246f99": "T2 classifier AUPRC reverses prior positive claim",
        "d9d7b1284593a71790b3e16a2552b9c4427b5b73": "researcher-guide calibration attribution fix",
        "68af47db9eaf73c08dc9de8264b5fd31979bf310": "release-freeze audit: 3 frontend build-wiring issues",
    }
    PLAN_SHAS = {
        "2e03622bd29a8b0f94e14eb87649a1a689b7a188": "architecture_refactor_plan.md",
        "54947490171da16ffca803f6c55b304a6124453e": "next_phases_plan.md",
        "e53ca08ce4f7a36e5d36306d2d01fe5ebf6e7bfc": "improvement_roadmap.md",
        "49bce0ee505bb782fe71fe1ddf6e87f4afa5927b": "server_northstar.md",
        "9eeaeb1e7df805fbb6f844cdd8c906879720d88e": "frontend_fix_plan.md",
        "01e1c53f09f1a763cf6b0a18ce683396a8f5bef3": "ux_trust_fix_plan.md",
        "083ae92df99d079b64b6da796557f1cfb2a4fd24": "def_followup_plan.md",
        "071d513944c1e811362b00cdf167c5f2e4386988": "compass_concept_integration_plan.md",
        "a65ae5b17a2cf9ddcb740b83670efcfe27165442": "frontend_design.md",
        "7d06639197f2cf06cb654d40e2a06c2e634583dd": "ux_flow_stepwise_plan.md",
        "1edae35fa84aac5ead80b2c547f977c54f0a3def": "server_modules.md",
        "b226f3e20424b99a157b9b67d96dc93e285371cf": "ROADMAP.md (release freeze)",
    }

    def lookup(shas_map, extra_lookup_needed):
        out = []
        for sha, label in shas_map.items():
            r = row_by_sha.get(sha)
            if r is None and extra_lookup_needed:
                # merge commit not in the non-merge `rows` list (e.g. the
                # blindspot sync commit) -- fetch its timestamp directly
                at_raw = run(f"git show -s --format=%at {sha}", args.repo).strip()
                if not at_raw:
                    out.append(dict(sha=sha, label=label, found=False))
                    continue
                day, slot, dt = bucket(int(at_raw))
                out.append(dict(sha=sha, label=label, found=True, day=day, slot=slot,
                                 category=None, diff=None, note="merge commit; not attributed to a category"))
            elif r is None:
                out.append(dict(sha=sha, label=label, found=False))
            else:
                out.append(dict(sha=sha, label=label, found=True, day=r["day"], slot=r["slot"],
                                 category=r["category"], diff=r["diff"]))
        return out

    json.dump(lookup(BUG_SHAS, True), open(os.path.join(args.out, "bug_events.json"), "w"), indent=1, ensure_ascii=False)
    json.dump(lookup(PLAN_SHAS, False), open(os.path.join(args.out, "plan_docs.json"), "w"), indent=1, ensure_ascii=False)

    # Real ML-modelling attempts under src/10_ml_perturbation_prediction/ and
    # the earlier src/3_DE_analysis/perturbation_prediction_ml.py T1 pass.
    # Found by request after the first pass of this script mis-labelled
    # roadmap Phase 5 "blocked" -- these commits exist under different file
    # names than the roadmap's target_condition_features.csv/weak_labels.csv,
    # which is why the naive filename search used for phases.json missed them.
    ML_SHAS = {
        "5f5d7b4218ff48ca8737a5707dbce6b31dec96f7": "T1: first supervised ML perturbation-prediction benchmark (honest, methodology-only)",
        "6727f2db166bb46865ca22936d5cad878f068953": "isolated ML exploration space added (src/10_ml_perturbation_prediction/)",
        "b56b3a8a2149620a65844c3d54b1ae4ee0c2a036": "GEARS GNN benchmark: honest negative result (pearson_de ~0, does not beat mean baseline)",
        "<multi_model_sha>": "T2: known-regulator classifier (5 models) + GenePT/real-features rework",
    }
    # the multi-model-comparison sha varies by checkout state during dev; resolve by subject instead
    ml_extra = []
    for r in rows:
        if r["subject"].startswith("ML vs linear multi-model comparison") or \
           r["subject"].startswith("T2 classifier") or r["subject"].startswith("T2 verification pass"):
            ml_extra.append(dict(sha=r["sha"], label=r["subject"], found=True, day=r["day"], slot=r["slot"],
                                  category=r["category"], diff=r["diff"]))
    ml_out = [lookup({k: v for k, v in ML_SHAS.items() if k != "<multi_model_sha>"}, True)[i]
              for i in range(len(ML_SHAS) - 1)]
    ml_out += ml_extra
    json.dump(ml_out, open(os.path.join(args.out, "ml_attempts.json"), "w"), indent=1, ensure_ascii=False)

    print(f"wrote {len(rows)} commit rows and {len(cells)} grid cells to {args.out}")

if __name__ == "__main__":
    main()
