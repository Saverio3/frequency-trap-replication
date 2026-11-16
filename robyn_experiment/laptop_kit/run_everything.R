# ONE-COMMAND RUNNER. From a terminal in this folder:   Rscript run_everything.R
# (or in the R console, after setwd() to this folder:   source("run_everything.R"))
# Optional arguments: Rscript run_everything.R "<markets>" <iterations> <trials>     defaults: all 16 markets, 2000, 5
# It (1) installs missing R packages, (2) sets up Python + nevergrad, (3) installs the patched Robyn into ./rlibB,
# (4) runs a 100-iteration test, (5) runs the full experiment and can be stopped and re-run: finished runs are skipped.
args <- commandArgs(trailingOnly = TRUE)
markets <- if (length(args) >= 1) args[1] else paste(0:15, collapse = " ")
iters <- if (length(args) >= 2) args[2] else "2000"; trials <- if (length(args) >= 3) args[3] else "5"
if (!file.exists("run_robyn_mc.R")) stop("Run this from the kit folder (the one containing run_robyn_mc.R). In R: setwd('path/to/robyn_controlled_kit')")
msg <- function(...) cat("\n>>>", ..., "\n")
repos <- "https://cloud.r-project.org"

msg("Step 1/5: R packages")
pkgs <- c("glmnet", "prophet", "reticulate", "doParallel", "foreach", "doRNG", "dplyr", "tidyr", "stringr", "lubridate", "jsonlite", "ggplot2", "ggridges",
          "patchwork", "minpack.lm", "data.table", "Rcpp", "rlang", "magrittr", "gridExtra", "scales", "nloptr", "lares")
need <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]
if (length(need)) { msg("installing:", paste(need, collapse = ", ")); install.packages(need, repos = repos) }
still <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]
if (length(still)) stop("Could not install: ", paste(still, collapse = ", "), ". Install them by hand with install.packages(), then re-run.")

msg("Step 2/5: Python and nevergrad (Robyn's optimiser)")
library(reticulate)
if (Sys.getenv("RETICULATE_PYTHON") != "" && file.exists(Sys.getenv("RETICULATE_PYTHON"))) {
  py <- Sys.getenv("RETICULATE_PYTHON")      # you already pointed to a Python that has nevergrad
} else {
  if (!virtualenv_exists("r-reticulate")) {
    ok <- tryCatch({ virtualenv_create("r-reticulate"); TRUE }, error = function(e) FALSE)
    if (!ok) { msg("No usable Python found: installing one (a few minutes)"); install_python(); virtualenv_create("r-reticulate", python = install_python()) }
  }
  py <- virtualenv_python("r-reticulate")
  Sys.setenv(RETICULATE_PYTHON = py)
  chk <- system2(py, c("-c", shQuote("import nevergrad, numpy; print(numpy.__version__)")), stdout = TRUE, stderr = FALSE)
  if (!length(chk) || !is.null(attr(chk, "status"))) virtualenv_install("r-reticulate", c("numpy<2", "nevergrad"))
}
Sys.setenv(RETICULATE_PYTHON = py)
chk <- system2(py, c("-c", shQuote("import nevergrad; print('nevergrad', nevergrad.__version__)")), stdout = TRUE)
msg("Python:", py, "|", chk)

msg("Step 3/5: patched Robyn (installed into ./rlibB, your normal Robyn is untouched)")
dir.create("rlibB", showWarnings = FALSE)
if (!dir.exists(file.path("rlibB", "Robyn"))) install.packages("RobynPatched", repos = NULL, type = "source", lib = "rlibB", INSTALL_opts = "--no-docs")
if (!dir.exists(file.path("rlibB", "Robyn"))) stop("Patched Robyn did not install. Send me the red error text above.")
Sys.setenv(ROBYN_LIB_DIRS = normalizePath("rlibB"))
rscript <- file.path(R.home("bin"), "Rscript")
cores <- max(1, parallel::detectCores() - 1); msg("cores given to Robyn:", cores)

msg("Step 4/5: 100-iteration test run (arm B, market 0)")
dir.create("results", showWarnings = FALSE); dir.create("logs_mc", showWarnings = FALSE)
tst <- file.path("results", "test.csv"); if (file.exists(tst)) file.remove(tst)
system2(rscript, c("run_robyn_mc.R", "0", "B", "100", "1", tst, cores), stdout = FALSE, stderr = file.path("logs_mc", "test.log"))
if (!file.exists(tst)) stop("Test run failed. Open logs_mc/test.log and send me the last 30 lines.")
file.remove(tst); msg("test OK")

msg("Step 5/5: full experiment. Output: results/RXM_laptop.csv (safe to stop with Ctrl+C and re-run later)")
out <- file.path("results", "RXM_laptop.csv")
for (m in as.integer(strsplit(markets, " ")[[1]])) for (a in c("A", "B", if (m <= 7) "C")) {
  if (file.exists(out)) { d <- read.csv(out); if (sum(d$market == m & d$arm == a) >= 2) next }
  msg(format(Sys.time(), "%H:%M"), "market", m, "arm", a, "(about 35 min at 2000 x 5 on 2 cores, less with more cores)")
  system2(rscript, c("run_robyn_mc.R", m, a, iters, trials, out, cores), stdout = FALSE, stderr = file.path("logs_mc", sprintf("m%d_%s.log", m, a)))
}
msg("ALL DONE. Send me the file results/RXM_laptop.csv")
