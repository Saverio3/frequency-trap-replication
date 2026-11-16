# Stability experiment (DESIGN_ROBYN_STABILITY.md). Same model configuration as run_robyn_mc.R; adds full output saving.
# Usage: Rscript run_robyn_stab.R <market> <arm A|B> <iterations> <trials> <tag> <outfile> <cores> [seed]
args <- commandArgs(trailingOnly = TRUE)
mk <- as.integer(args[1]); arm <- args[2]; iters <- as.integer(args[3]); trials <- as.integer(args[4]); tag <- args[5]; outfile <- args[6]; cores <- as.integer(args[7])
seed <- if (length(args) >= 8) as.integer(args[8]) else 1L
stopifnot(arm %in% c("A", "B"))
LIBS <- Sys.getenv("ROBYN_LIB_DIRS", "")
if (nzchar(LIBS)) .libPaths(c(strsplit(LIBS, .Platform$path.sep)[[1]], .libPaths()))
suppressMessages({library(Robyn); library(dplyr)})
RP <- Sys.getenv("RETICULATE_PYTHON", ""); if (nzchar(RP) && file.exists(RP)) Sys.setenv(RETICULATE_PYTHON = RP)
source("stab_extract.R")
Sys.unsetenv("ROBYN_DAILY_SPEND_FILE")
truth <- read.csv("robyn_mc/truth_mc.csv"); tr <- truth[truth$market == mk, ]
dailyf <- sprintf("robyn_mc/market_%02d_daily.csv", mk); weeklyf <- sprintf("robyn_mc/market_%02d_weekly.csv", mk)
if (arm == "B") {
  if (!exists("run_transformations_daily_then_weekly", envir = asNamespace("Robyn"))) stop("Robyn loaded from ", find.package("Robyn"), " is NOT the patched version (arm B would silently run as arm A).")
  Sys.setenv(ROBYN_DAILY_SPEND_FILE = normalizePath(dailyf), ROBYN_DAILY_BLOCK = "7")
  if (.Platform$OS.type == "windows") {   # parallel workers on Windows are fresh R sessions: check that they also see the patched Robyn
    cl <- parallel::makeCluster(1)
    ok <- tryCatch(parallel::clusterEvalQ(cl, { suppressMessages(library(Robyn)); exists("run_transformations_daily_then_weekly", envir = asNamespace("Robyn")) })[[1]], error = function(e) FALSE)
    parallel::stopCluster(cl)
    if (!isTRUE(ok)) stop("Parallel workers do not see the patched Robyn (set R_LIBS to the rlibB folder before starting R).")
  }
}
df <- read.csv(weeklyf); df$DATE <- as.Date(df$DATE)
data("dt_prophet_holidays")
hyper <- list(ch1_alphas = c(0.5, 3), ch1_gammas = c(0.05, 1), ch1_thetas = c(0.01, 0.95), ch2_alphas = c(0.5, 3), ch2_gammas = c(0.05, 1), ch2_thetas = c(0.01, 0.95),
              ch3_alphas = c(0.5, 3), ch3_gammas = c(0.05, 1), ch3_thetas = c(0.01, 0.95), train_size = c(0.5, 0.9))
hyper_txt <- "alphas 0.5-3; gammas 0.05-1; thetas 0.01-0.95 (all 3 channels); train_size 0.5-0.9"
pv <- c("trend", "season")
t0 <- Sys.time()
IC <- suppressWarnings(robyn_inputs(dt_input = df, dt_holidays = dt_prophet_holidays, date_var = "DATE", dep_var = "revenue", dep_var_type = "revenue",
        prophet_vars = pv, prophet_country = "GB", paid_media_spends = c("ch1", "ch2", "ch3"), paid_media_vars = c("ch1", "ch2", "ch3"),
        window_start = min(df$DATE), window_end = max(df$DATE), adstock = "geometric", hyperparameters = hyper))
OM <- suppressWarnings(robyn_run(InputCollect = IC, iterations = iters, trials = trials, ts_validation = TRUE, cores = cores, seed = seed, outputs = FALSE))
OC <- suppressWarnings(robyn_outputs(IC, OM, pareto_fronts = "auto", clusters = FALSE, csv_out = NULL, plot_pareto = FALSE, plot_folder = tempdir(), export = FALSE, quiet = TRUE))
secs <- round(as.numeric(difftime(Sys.time(), t0, units = "secs")))
outdir <- file.path(dirname(outfile), "stab_pareto")
out <- extract_stab(OC, OM, mk, arm, iters, trials, seed, cores, secs, tag, outdir)
out$timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
write_manifest(file.path(dirname(outfile), "stab_manifest.csv"), mk, arm, tag, iters, trials, seed, cores, hyper_txt, if (arm == "B") dailyf else NA_character_)
writeLines(capture.output(sessionInfo()), file.path(outdir, sprintf("m%02d_%s_%s_session.txt", mk, arm, tag)))
first <- !file.exists(outfile)
write.table(out, outfile, sep = ",", row.names = FALSE, col.names = first, append = !first, qmethod = "double")
cat("done market", mk, "arm", arm, "tag", tag, "secs", secs, "\n", file = stderr())
