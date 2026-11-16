# Controlled real-Robyn experiment (DESIGN_ROBYN_CONTROLLED.md).
# Usage: Rscript run_robyn_mc.R <market> <arm A|B|C> <iterations> <trials> <outfile> <cores> [seed]
# Arm A: weekly Robyn. Arm B: weekly KPI, media transformed at DAILY frequency then summed to weeks (patched Robyn, library rlibB). Arm C: daily Robyn.
args <- commandArgs(trailingOnly = TRUE)
mk <- as.integer(args[1]); arm <- args[2]; iters <- as.integer(args[3]); trials <- as.integer(args[4]); outfile <- args[5]; cores <- as.integer(args[6])
seed <- if (length(args) >= 7) as.integer(args[7]) else 1L
LIBS <- Sys.getenv("ROBYN_LIB_DIRS", "/home/claude/rlibB:/home/claude/rlib")   # rlibB = patched Robyn (identical to Meta's code unless ROBYN_DAILY_SPEND_FILE is set)
if (nzchar(LIBS)) .libPaths(c(strsplit(LIBS, .Platform$path.sep)[[1]], .libPaths()))
suppressMessages({library(Robyn); library(dplyr)})
RP <- Sys.getenv("RETICULATE_PYTHON", "/home/claude/ngenv/bin/python"); if (nzchar(RP) && file.exists(RP)) Sys.setenv(RETICULATE_PYTHON = RP)   # laptop: set RETICULATE_PYTHON="" to use reticulate default
Sys.unsetenv("ROBYN_DAILY_SPEND_FILE")
truth <- read.csv("robyn_mc/truth_mc.csv"); tr <- truth[truth$market == mk, ]
dailyf <- sprintf("robyn_mc/market_%02d_daily.csv", mk); weeklyf <- sprintf("robyn_mc/market_%02d_weekly.csv", mk)
if (arm == "B") Sys.setenv(ROBYN_DAILY_SPEND_FILE = normalizePath(dailyf), ROBYN_DAILY_BLOCK = "7")
df <- read.csv(if (arm == "C") dailyf else weeklyf); df$DATE <- as.Date(df$DATE)
data("dt_prophet_holidays")
hyper <- list(ch1_alphas = c(0.5, 3), ch1_gammas = c(0.05, 1), ch1_thetas = c(0.01, 0.95), ch2_alphas = c(0.5, 3), ch2_gammas = c(0.05, 1), ch2_thetas = c(0.01, 0.95),
              ch3_alphas = c(0.5, 3), ch3_gammas = c(0.05, 1), ch3_thetas = c(0.01, 0.95), train_size = c(0.5, 0.9))
pv <- if (arm == "C") c("trend", "season", "weekday") else c("trend", "season")
t0 <- Sys.time()
IC <- suppressWarnings(robyn_inputs(dt_input = df, dt_holidays = dt_prophet_holidays, date_var = "DATE", dep_var = "revenue", dep_var_type = "revenue",
        prophet_vars = pv, prophet_country = "GB", paid_media_spends = c("ch1", "ch2", "ch3"), paid_media_vars = c("ch1", "ch2", "ch3"),
        window_start = min(df$DATE), window_end = max(df$DATE), adstock = "geometric", hyperparameters = hyper))
OM <- suppressWarnings(robyn_run(InputCollect = IC, iterations = iters, trials = trials, ts_validation = TRUE, cores = cores, seed = seed, outputs = FALSE))
conv <- tryCatch(paste(unlist(OM$convergence$conv_msg), collapse = " | "), error = function(e) NA_character_)
OC <- suppressWarnings(robyn_outputs(IC, OM, pareto_fronts = "auto", clusters = FALSE, csv_out = NULL, plot_pareto = FALSE, plot_folder = tempdir(), export = FALSE, quiet = TRUE))
rp <- OC$resultHypParam %>% filter(robynPareto == 1)
ag <- OC$xDecompAgg %>% filter(rn %in% c("ch1", "ch2", "ch3"))
est <- function(sol) sapply(c("ch1", "ch2", "ch3"), function(ch) ag$xDecompAgg[ag$solID == sol & ag$rn == ch][1])
rules <- list(errscore = rp$solID[which.min(rp$error_score)], nrmse = rp$solID[which.min(rp$nrmse_val)])
secs <- round(as.numeric(difftime(Sys.time(), t0, units = "secs")))
rows <- list()
for (nm in names(rules)) {
  sol <- rules[[nm]]; e <- est(sol); r1 <- rp[rp$solID == sol, ][1, ]
  rows[[nm]] <- data.frame(market = mk, arm = arm, rule = nm, iterations = iters, trials = trials, seed = seed, cores = cores, secs = secs,
     est_ch1 = e[1], est_ch2 = e[2], est_ch3 = e[3], est_total = sum(e), nrmse_val = r1$nrmse_val, decomp_rssd = r1$decomp.rssd, error_score = r1$error_score,
     n_pareto1 = nrow(rp), n_models = nrow(OC$resultHypParam), converged_msg = conv)
}
out <- do.call(rbind, rows); first <- !file.exists(outfile)
write.table(out, outfile, sep = ",", row.names = FALSE, col.names = first, append = !first, qmethod = "double")
cat("done market", mk, "arm", arm, "secs", secs, "\n", file = stderr())
