#!/usr/bin/env Rscript
# recompute_crosscheck.R -- INDEPENDENT R re-computation of the subset of portal
# display numbers that are reproducible from the in-repo CSV / JSON sources,
# used to cross-check the Python recompute (scripts/recompute_display_numbers.py).
#
# R deliberately re-derives each quantity with a different toolchain (readr /
# dplyr / jsonlite instead of pandas) so that agreement is genuine cross-engine
# corroboration, not a shared-code artifact. R covers:
#   - DE row count + genome-total target count (DE_stats.suppl_table.csv)
#   - per-condition DE summaries (rows, mean n_total_de_genes, significant frac)
#   - cross-donor / cross-guide robustness aggregates (DE_stats columns)
#   - risk-flag tier distribution (real-dataset.json, exprCompare.ts rule)
#   - negative-control grade-1 percentage (target_cards.csv)
#   - readiness call distribution (real-dataset.json)
#
# Numbers that need the S3-only h5ad (measured_downstream_genes) or an offline
# benchmark engine (AUROC) are NOT recomputed here -- see the Python script /
# REPRODUCIBILITY_REPORT.md for the honest NOT-REPRODUCIBLE-IN-REPO verdict.
#
# Repo root: env GWT_REPO_ROOT, else two levels up from this file (scripts/->repo).
# Output:    $GWT_OUT_DIR/recomputed_numbers_R.csv (else scripts/).
#
# Run (env gwt-web has no R; use the `r` conda env):
#   Rscript scripts/recompute_crosscheck.R

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(jsonlite)
})

find_repo <- function() {
  env <- Sys.getenv("GWT_REPO_ROOT", unset = "")
  if (nzchar(env)) return(normalizePath(env))
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- sub("^--file=", "", args[grep("^--file=", args)])
  here <- if (length(file_arg)) normalizePath(dirname(file_arg)) else getwd()
  cand <- normalizePath(file.path(here, ".."))
  if (file.exists(file.path(cand, "frontend/webserver/public/disclosure.json"))) return(cand)
  cand
}

REPO <- find_repo()
SUPPL <- file.path(REPO, "metadata", "suppl_tables")
L4 <- file.path(REPO, "docs", "mvp-research", "level4_external_validation")
TARGET_CARDS <- file.path(REPO, "sources", "target_tool_cache",
                          "a792d68c-7adc-46a6-964a-35770e5adbde", "target_cards.csv")
GNOMAD_SEED <- file.path(REPO, "sources", "target_tool_cache", "_overlays",
                         "gnomad_constraint_seed.csv")
REAL_DATASET <- file.path(REPO, "frontend", "webserver", "public", "real-dataset.json")

OUT_DIR <- Sys.getenv("GWT_OUT_DIR", unset = file.path(REPO, "scripts"))
dir.create(OUT_DIR, showWarnings = FALSE, recursive = TRUE)
OUT <- file.path(OUT_DIR, "recomputed_numbers_R.csv")

rows <- list()
add <- function(key, value, how, source) {
  rows[[length(rows) + 1]] <<- data.frame(
    key = key, value = as.character(value), how_derived = how,
    source_file = source, stringsAsFactors = FALSE)
}

# ---------------------------------------------------------------------------
# DE stats table
# ---------------------------------------------------------------------------
de <- read_csv(file.path(SUPPL, "DE_stats.suppl_table.csv"),
               show_col_types = FALSE, progress = FALSE)

add("de_rows_total", nrow(de),
    "nrow(DE_stats.suppl_table.csv)", "metadata/suppl_tables/DE_stats.suppl_table.csv")
add("genome_total_targets", n_distinct(de$target_contrast),
    "n_distinct(target_contrast) in DE_stats", "metadata/suppl_tables/DE_stats.suppl_table.csv")
add("genome_total_target_names", n_distinct(de$target_contrast_gene_name),
    "n_distinct(target_contrast_gene_name) in DE_stats", "metadata/suppl_tables/DE_stats.suppl_table.csv")

# per-condition DE summaries
pc <- de %>%
  group_by(culture_condition) %>%
  summarise(n_rows = n(),
            mean_n_total_de_genes = round(mean(n_total_de_genes, na.rm = TRUE), 4),
            frac_ontarget_significant = round(mean(ontarget_significant, na.rm = TRUE), 4),
            frac_offtarget_flag = round(mean(offtarget_flag, na.rm = TRUE), 4),
            .groups = "drop")
for (i in seq_len(nrow(pc))) {
  cond <- pc$culture_condition[i]
  add(paste0("de_per_condition.", cond, ".n_rows"), pc$n_rows[i],
      "rows in DE_stats with culture_condition==cond", "metadata/suppl_tables/DE_stats.suppl_table.csv")
  add(paste0("de_per_condition.", cond, ".mean_n_total_de_genes"), pc$mean_n_total_de_genes[i],
      "mean(n_total_de_genes) per condition", "metadata/suppl_tables/DE_stats.suppl_table.csv")
  add(paste0("de_per_condition.", cond, ".frac_ontarget_significant"), pc$frac_ontarget_significant[i],
      "mean(ontarget_significant) per condition", "metadata/suppl_tables/DE_stats.suppl_table.csv")
}

# overall significant / offtarget counts
add("de_ontarget_significant_true", sum(de$ontarget_significant, na.rm = TRUE),
    "sum(ontarget_significant) over DE_stats", "metadata/suppl_tables/DE_stats.suppl_table.csv")
add("de_offtarget_flag_true", sum(de$offtarget_flag, na.rm = TRUE),
    "sum(offtarget_flag) over DE_stats", "metadata/suppl_tables/DE_stats.suppl_table.csv")

# ---------------------------------------------------------------------------
# cross-donor / cross-guide robustness aggregates
# ---------------------------------------------------------------------------
add("crossdonor_correlation_mean.mean",
    round(mean(de$crossdonor_correlation_mean, na.rm = TRUE), 4),
    "mean of crossdonor_correlation_mean over non-NA rows", "metadata/suppl_tables/DE_stats.suppl_table.csv")
add("crossdonor_correlation_mean.n_nonNA", sum(!is.na(de$crossdonor_correlation_mean)),
    "count of rows with non-NA crossdonor_correlation_mean", "metadata/suppl_tables/DE_stats.suppl_table.csv")
add("crossguide_correlation.mean",
    round(mean(de$crossguide_correlation, na.rm = TRUE), 4),
    "mean of crossguide_correlation over non-NA rows", "metadata/suppl_tables/DE_stats.suppl_table.csv")
add("crossguide_correlation.n_nonNA", sum(!is.na(de$crossguide_correlation)),
    "count of rows with non-NA crossguide_correlation", "metadata/suppl_tables/DE_stats.suppl_table.csv")

# ---------------------------------------------------------------------------
# gnomAD constraint coverage (DE ensembl ∩ gnomad seed ensembl)
# ---------------------------------------------------------------------------
gseed <- read_csv(GNOMAD_SEED, show_col_types = FALSE, progress = FALSE)
gnomad_covered <- length(intersect(unique(na.omit(de$target_contrast)),
                                    unique(na.omit(gseed$ensembl_id))))
add("gnomad_constraint_genes", gnomad_covered,
    "|DE target_contrast ensembl ∩ gnomad_constraint_seed ensembl_id|",
    "DE_stats.suppl_table.csv + gnomad_constraint_seed.csv")

# ---------------------------------------------------------------------------
# negative-control grade-1 percentage (target_cards.csv)
# ---------------------------------------------------------------------------
tc <- read_csv(TARGET_CARDS, show_col_types = FALSE, progress = FALSE,
               guess_max = 100000)
nm <- tc %>% filter(kd_status == "not_measurable")
add("neg_control_not_measurable_rows", nrow(nm),
    "rows with kd_status=='not_measurable' in target_cards", "sources/.../target_cards.csv")
add("neg_control_grade1_pct",
    round(mean(nm$statistical_evidence_grade == 1, na.rm = TRUE) * 100, 2),
    "pct of not_measurable rows with statistical_evidence_grade==1", "sources/.../target_cards.csv")

# ---------------------------------------------------------------------------
# real-dataset.json: readiness calls + risk-flag tier distribution
# ---------------------------------------------------------------------------
real <- fromJSON(REAL_DATASET, simplifyVector = FALSE)
targets <- real$targets
add("targets_in_portal", length(targets),
    "length(real-dataset.json targets[])", "frontend/webserver/public/real-dataset.json")
add("modules", length(real$modules),
    "length(real-dataset.json modules[])", "frontend/webserver/public/real-dataset.json")

# readiness call distribution
calls <- vapply(targets, function(t) {
  rc <- t$readiness$call
  if (is.null(rc)) NA_character_ else rc
}, character(1))
for (cc in c("watchlist", "validate", "advance")) {
  add(paste0("readiness.", cc), sum(calls == cc, na.rm = TRUE),
      paste0("count of targets with readiness.call=='", cc, "'"),
      "frontend/webserver/public/real-dataset.json")
}

# risk-flag tier distribution -- exprCompare.ts deriveRiskTier rule:
# f = nRedFlags + nSafetyLiabilities + (gnomad.constraintTier=='high' ? 1 : 0)
# f>=3 avoid ; f==2 high ; f==1 caution ; f==0 clear
tier_of <- function(t) {
  n_red <- length(t$readiness$redFlags)
  n_liab <- length(t$safetyLiabilities)
  hi <- if (!is.null(t$gnomad$constraintTier) && t$gnomad$constraintTier == "high") 1L else 0L
  f <- n_red + n_liab + hi
  if (f >= 3) "avoid" else if (f == 2) "high" else if (f == 1) "caution" else "clear"
}
tiers <- vapply(targets, tier_of, character(1))
for (tt in c("clear", "caution", "high", "avoid")) {
  add(paste0("risk_tier.", tt), sum(tiers == tt),
      paste0("deriveRiskTier count for tier '", tt, "' (exprCompare.ts rule)"),
      "frontend/webserver/public/real-dataset.json")
}

# red-flag / safety-liability raw counts (robustness aggregate)
add("targets_with_redflags", sum(vapply(targets, function(t) length(t$readiness$redFlags) > 0, logical(1))),
    "count of targets with >=1 readiness.redFlags", "frontend/webserver/public/real-dataset.json")
add("targets_with_safety_liabilities", sum(vapply(targets, function(t) length(t$safetyLiabilities) > 0, logical(1))),
    "count of targets with >=1 safetyLiabilities", "frontend/webserver/public/real-dataset.json")
add("targets_gnomad_constraint_high", sum(vapply(targets, function(t) {
      !is.null(t$gnomad$constraintTier) && t$gnomad$constraintTier == "high"}, logical(1))),
    "count of targets with gnomad.constraintTier=='high'", "frontend/webserver/public/real-dataset.json")

# ---------------------------------------------------------------------------
# write + cross-check against the Python output if present
# ---------------------------------------------------------------------------
out <- do.call(rbind, rows)
write_csv(out, OUT)
cat(sprintf("wrote %s: %d rows\n", OUT, nrow(out)))
for (i in seq_len(nrow(out))) cat(sprintf("  %-45s %s\n", out$key[i], out$value[i]))

py_json <- file.path(OUT_DIR, "recomputed_numbers.json")
if (file.exists(py_json)) {
  py <- fromJSON(py_json, simplifyVector = FALSE)$numbers
  # keys shared between R and Python (map R key -> Python key)
  bridge <- c(
    de_rows_total = "coverage.de_rows_total",
    genome_total_targets = "coverage.genome_total_targets",
    gnomad_constraint_genes = "coverage.gnomad_constraint_genes",
    targets_in_portal = "coverage.targets_in_portal",
    modules = "real_dataset.modules",
    readiness.watchlist = "readiness.watchlist",
    readiness.validate = "readiness.validate",
    readiness.advance = "readiness.advance",
    risk_tier.clear = "risk_tier.clear",
    risk_tier.caution = "risk_tier.caution",
    risk_tier.high = "risk_tier.high",
    risk_tier.avoid = "risk_tier.avoid",
    neg_control_grade1_pct = "validation.calibration.neg_control_grade1_pct"
  )
  cat("\n=== R vs Python cross-check ===\n")
  rmap <- setNames(out$value, out$key)
  divergence <- 0
  for (rk in names(bridge)) {
    pk <- bridge[[rk]]
    rv <- rmap[[rk]]
    pv <- if (!is.null(py[[pk]])) as.character(py[[pk]]$value) else NA
    # numeric-tolerant compare
    agree <- isTRUE(rv == pv) ||
             (suppressWarnings(!is.na(as.numeric(rv)) && !is.na(as.numeric(pv))) &&
              isTRUE(all.equal(as.numeric(rv), as.numeric(pv))))
    status <- if (agree) "AGREE" else { divergence <- divergence + 1; "DIVERGE" }
    cat(sprintf("  %-40s R=%-10s Py=%-10s %s\n", rk, rv, pv, status))
  }
  cat(sprintf("\ncross-check: %d shared keys, %d divergence(s)\n", length(bridge), divergence))
} else {
  cat("\n[note] Python output not found; run recompute_display_numbers.py first for cross-check.\n")
}
