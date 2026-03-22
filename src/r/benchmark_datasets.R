#!/usr/bin/env Rscript
# benchmark_datasets.R -- LogosSort per-dataset benchmark (R)
#
# Kaggle dataset categories (one number per line, .txt files):
#   uniform          Uniform random floats
#   gaussian         Gaussian random floats
#   ordered          Pre-sorted ascending
#   reverse_ordered  Pre-sorted descending
#   repeated_values  Few distinct values (heavy duplicates)
#   same_value       All elements identical
#   Combinations_*   Mixed ascending/descending integer runs
#
# Algorithms compared:
#   logos_sort   -- pure R LogosSort (logos_sort.R)
#   sort()       -- R built-in (C-backed, the natural R baseline)
#
# Each (file, algorithm) pair is run RUNS=2 times; wall-clock results averaged.
#
# Usage:
#   Rscript benchmark_datasets.R --kaggle /path/to/archive
#   Rscript benchmark_datasets.R --kaggle /path/to/archive --sizes 10000 100000

suppressPackageStartupMessages({
  if (!requireNamespace("optparse", quietly = TRUE)) {
    message("Installing optparse...")
    install.packages("optparse", repos = "https://cloud.r-project.org", quiet = TRUE)
  }
  library(optparse)
})

# ── Source logos_sort ──────────────────────────────────────────────────────────
script_dir <- tryCatch(
  dirname(sys.frame(1)$ofile),
  error = function(e) getwd()
)
source(file.path(script_dir, "logos_sort.R"))

# ── Config ─────────────────────────────────────────────────────────────────────
RUNS          <- 2L
DEFAULT_SIZES <- c(1000L, 10000L, 100000L, 1000000L)

CATEGORIES <- c(
  "uniform",
  "gaussian",
  "ordered",
  "reverse_ordered",
  "repeated_values",
  "same_value",
  "Combinations_of_ascending_and_descending_two_sub_arrays"
)

CATEGORY_META <- list(
  uniform         = c("Uniform random",       "dual-pivot introsort"),
  gaussian        = c("Gaussian random",       "dual-pivot introsort"),
  ordered         = c("Pre-sorted ascending",  "monotone detect -> O(n)"),
  reverse_ordered = c("Pre-sorted descending", "reverse detect -> O(n)"),
  repeated_values = c("Repeated values",       "dual-pivot (floats skip counting sort)"),
  same_value      = c("All same value",        "monotone detect -> O(n)"),
  Combinations_of_ascending_and_descending_two_sub_arrays =
                    c("Asc/desc runs (int)",   "counting sort or dual-pivot")
)

# ── File discovery ─────────────────────────────────────────────────────────────
extract_size <- function(fname) {
  m <- regmatches(fname, regexpr("-([0-9]{3,})", fname))
  if (length(m) == 0L) return(NA_integer_)
  as.integer(sub("-", "", m))
}

find_files <- function(kaggle_root, target_sizes) {
  result <- list()
  for (cat in CATEGORIES) {
    inner <- file.path(kaggle_root, cat, cat)
    if (!dir.exists(inner)) inner <- file.path(kaggle_root, cat)
    if (!dir.exists(inner)) next

    files    <- list.files(inner, pattern = "\\.txt$", full.names = TRUE)
    by_size  <- list()
    for (fp in sort(files)) {
      sz <- extract_size(basename(fp))
      if (!is.na(sz) && sz %in% target_sizes && is.null(by_size[[as.character(sz)]])) {
        by_size[[as.character(sz)]] <- fp
      }
    }
    if (length(by_size) > 0L) result[[cat]] <- by_size
  }
  result
}

# ── Data loading ───────────────────────────────────────────────────────────────
load_file <- function(path) {
  lines <- readLines(path, warn = FALSE)
  lines <- trimws(lines[nchar(trimws(lines)) > 0L])
  vals  <- suppressWarnings(as.numeric(lines))
  vals  <- vals[!is.na(vals)]
  # Use integer storage if all values are whole numbers (enables counting sort)
  if (all(vals == floor(vals))) as.integer(vals) else vals
}

# ── Timing harness ─────────────────────────────────────────────────────────────
bench <- function(fn, data) {
  total <- 0.0
  for (i in seq_len(RUNS)) {
    arr <- data               # R copy semantics: this is a fresh copy
    t0  <- proc.time()[["elapsed"]]
    fn(arr)
    total <- total + (proc.time()[["elapsed"]] - t0)
  }
  total / RUNS
}

# ── Formatting ──────────────────────────────────────────────────────────────────
fmt_t <- function(s) {
  if      (s >= 10)   sprintf("%7.2fs", s)
  else if (s >= 1)    sprintf("%7.3fs", s)
  else if (s >= 0.01) sprintf("%7.1fms", s * 1000)
  else                sprintf("%7.2fms", s * 1000)
}

SEP  <- strrep("-", 78)
DSEP <- strrep("=", 78)

# ── Main ───────────────────────────────────────────────────────────────────────
run_benchmark <- function(kaggle_root, target_sizes) {
  cat(DSEP, "\n")
  cat("  LogosSort (pure R) vs sort() -- Kaggle Dataset Benchmark\n")
  cat(sprintf("  Runs per measurement: %d  (averaged)\n", RUNS))
  cat(sprintf("  Target sizes: %s\n", paste(format(sort(target_sizes), big.mark=","), collapse=", ")))
  cat(sprintf("  Dataset root: %s\n", kaggle_root))
  cat(sprintf("  logos_sort = pure R  |  sort() = R built-in C-backed baseline\n"))
  cat(DSEP, "\n")

  file_map <- find_files(kaggle_root, target_sizes)
  if (length(file_map) == 0L) {
    cat("  No matching files found. Check --kaggle path.\n")
    return(invisible(NULL))
  }

  for (cat_key in CATEGORIES) {
    if (is.null(file_map[[cat_key]])) next

    meta  <- CATEGORY_META[[cat_key]]
    label <- if (!is.null(meta)) meta[1] else cat_key
    note  <- if (!is.null(meta)) meta[2] else ""

    cat(sprintf("\n  [%s]  (%s)\n", label, note))
    cat(SEP, "\n")
    cat(sprintf("  %10s   %10s   %10s   %7s   %s\n",
                "Size", "logos_sort", "sort()", "ratio", "Winner"))
    cat(SEP, "\n")

    by_size <- file_map[[cat_key]]
    for (sz_key in as.character(sort(as.integer(names(by_size))))) {
      fp   <- by_size[[sz_key]]
      data <- load_file(fp)
      n    <- length(data)
      if (n == 0L) { cat(sprintf("  %10s   (empty file, skipped)\n", sz_key)); next }

      logos_t  <- bench(logos_sort,  data)
      builtin_t <- bench(sort,       data)

      ratio  <- if (builtin_t > 0) logos_t / builtin_t else Inf
      winner <- if (ratio < 0.99) "logos" else if (ratio > 1.01) "sort()" else "tied"

      cat(sprintf("  %10s   %10s   %10s   %6.2fx   %s\n",
                  format(n, big.mark=","),
                  fmt_t(logos_t),
                  fmt_t(builtin_t),
                  ratio,
                  winner))
    }
    cat(SEP, "\n")
  }
  cat("\n")
  cat("  Note: sort() is C-backed (not a fair pure-R peer; shown as scale reference).\n")
  cat(SEP, "\n")
}

# ── Argument parsing ───────────────────────────────────────────────────────────
option_list <- list(
  make_option("--kaggle", type = "character", default = NULL,
              help = "Root directory of the Kaggle sort-benchmark archive [required]"),
  make_option("--sizes",  type = "character",
              default = paste(DEFAULT_SIZES, collapse = ","),
              help = sprintf("Comma-separated array sizes [default: %s]",
                             paste(DEFAULT_SIZES, collapse = ",")))
)

opt <- parse_args(OptionParser(option_list = option_list))

if (is.null(opt$kaggle)) {
  cat("Usage: Rscript benchmark_datasets.R --kaggle /path/to/archive\n")
  cat("       Rscript benchmark_datasets.R --kaggle /path/to/archive --sizes 10000,100000\n")
  quit(status = 1L)
}

if (!dir.exists(opt$kaggle)) {
  cat(sprintf("Error: --kaggle path not found: %s\n", opt$kaggle))
  quit(status = 1L)
}

target_sizes <- as.integer(strsplit(opt$sizes, "[, ]+")[[1L]])
run_benchmark(opt$kaggle, target_sizes)
