# ONE COMMAND for the stability experiment. From the kit folder (the one with run_robyn_mc.R, robyn_mc/ and rlibB/):
#     Rscript run_stability.R
# 24 runs (markets 0 2 4 7 11 13 x arms A, B x {2000 repeat, 4000}); about 9 hours. Safe to stop (Ctrl+C) and re-run: finished runs are skipped.
# Your first-experiment results (results/RXM_laptop.csv) are never touched. New results: results/RXM_stability.csv and results/stab_pareto/.
args <- commandArgs(trailingOnly = TRUE)
msg <- function(...) cat("\n>>>", ..., "\n")
for (f in c("run_robyn_mc.R", "run_robyn_stab.R", "stab_extract.R", "robyn_mc/truth_mc.csv")) if (!file.exists(f)) stop("File not found: ", f, ". Run this from the kit folder after copying the stability files into it.")
if (!dir.exists(file.path("rlibB", "Robyn"))) stop("Folder rlibB/Robyn not found. Run this from the kit folder where run_everything.R was run.")
rlib <- normalizePath("rlibB")
Sys.setenv(ROBYN_LIB_DIRS = rlib, R_LIBS = rlib)            # R_LIBS is inherited by Robyn's parallel workers on Windows
py <- Sys.getenv("RETICULATE_PYTHON")
if (!nzchar(py) || !file.exists(py)) { library(reticulate); py <- virtualenv_python("r-reticulate") }
Sys.setenv(RETICULATE_PYTHON = py)
chk <- tryCatch(system2(py, c("-c", shQuote("import nevergrad; print('nevergrad', nevergrad.__version__)")), stdout = TRUE, stderr = FALSE), error = function(e) character(0))
if (!length(chk) || !is.null(attr(chk, "status"))) stop("Python at ", py, " cannot import nevergrad. Run: Rscript run_everything.R once, or set RETICULATE_PYTHON to the Python that has nevergrad.")
msg("Python:", py, "|", chk)
rscript <- file.path(R.home("bin"), "Rscript"); cores <- max(1, parallel::detectCores() - 1); msg("cores:", cores)
dir.create("results", showWarnings = FALSE); dir.create("logs_mc", showWarnings = FALSE)
if (file.exists(file.path("results", "RXM_laptop.csv"))) msg("first-experiment file found and left untouched: results/RXM_laptop.csv") else msg("NOTE: results/RXM_laptop.csv not in this folder (fine for running; keep your copy for the analysis)")

# ---- smoke tests (about 4 minutes): both arms, small run, check that every expected output exists ----
msg("Smoke test (400 iterations x 1 trial, market 0, arms A and B)")
td <- file.path("results", "smoke"); unlink(td, recursive = TRUE); dir.create(td, recursive = TRUE)
tout <- file.path(td, "smoke.csv")
for (a in c("A", "B")) {
  system2(rscript, c("run_robyn_stab.R", "0", a, "400", "1", paste0("smoke_", a), tout, cores), stdout = FALSE, stderr = file.path("logs_mc", sprintf("smoke_%s.log", a)))
}
need <- c("m00_A_smoke_A_models.csv", "m00_B_smoke_B_models.csv")
ok <- file.exists(tout) && all(file.exists(file.path(td, "stab_pareto", need)))
if (ok) { s <- read.csv(tout); ok <- nrow(s) == 4 && all(c("rssd_converged", "nrmse_converged", "sel_rank_errscore", "p1_total_med") %in% names(s)) && !anyNA(s$est_total) }
if (!ok) stop("Smoke test FAILED. Open logs_mc/smoke_A.log and logs_mc/smoke_B.log and send me the last 30 lines of each.")
msg("smoke test OK"); unlink(td, recursive = TRUE)

# ---- the experiment ----
out <- file.path("results", "RXM_stability.csv")
jobs <- list()
for (m in c(0, 2, 4, 7, 11, 13)) for (spec in list(c("rep2000", 2000), c("inc4000", 4000))) for (a in c("A", "B")) jobs[[length(jobs) + 1]] <- list(m = m, a = a, tag = spec[1], it = spec[2])
msg("24 runs planned. Output:", out)
k <- 0
for (j in jobs) {
  k <- k + 1
  if (file.exists(out)) { d <- read.csv(out); if (sum(d$market == j$m & d$arm == j$a & d$tag == j$tag) >= 2) next }
  msg(format(Sys.time(), "%d %b %H:%M"), sprintf("run %d of 24: market %d arm %s tag %s (%s iterations x 5 trials)", k, j$m, j$a, j$tag, j$it))
  system2(rscript, c("run_robyn_stab.R", j$m, j$a, j$it, "5", j$tag, out, cores, "1"), stdout = FALSE, stderr = file.path("logs_mc", sprintf("stab_m%d_%s_%s.log", j$m, j$a, j$tag)))
}
done <- if (file.exists(out)) nrow(read.csv(out)) / 2 else 0
msg("FINISHED.", done, "of 24 runs recorded. Send me: results/RXM_stability.csv, results/stab_manifest.csv and the folder results/stab_pareto (zip it).")
