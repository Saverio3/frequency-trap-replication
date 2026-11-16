# Runs the REAL Robyn code (3.12.1, Meta's source) on simulated single-channel markets, daily data vs weekly data.
# Design: DESIGN_ROBYN_REAL.md.  Usage: Rscript run_robyn_real.R <iterations> <outfile> [market ids comma-separated]
.libPaths(c("/home/claude/rlib", .libPaths())); suppressMessages({library(Robyn); library(dplyr)})
Sys.setenv(RETICULATE_PYTHON = "/home/claude/ngenv/bin/python")
args <- commandArgs(trailingOnly = TRUE); iters <- as.integer(args[1]); outfile <- args[2]
truth <- read.csv("robyn_markets/truth.csv")
ids <- if (length(args) >= 3) as.integer(strsplit(args[3], ",")[[1]]) else truth$market[truth$rep == 0]
data("dt_prophet_holidays")
run_one <- function(file, interval) {
  df <- read.csv(file); df$DATE <- as.Date(df$DATE)
  hyper <- list(spend_ch_alphas = c(0.5, 3), spend_ch_gammas = c(0.05, 1), spend_ch_thetas = c(0.01, 0.95), train_size = c(0.5, 0.9))
  pv <- if (interval == "day") c("trend", "season", "weekday") else c("trend", "season")
  IC <- suppressWarnings(robyn_inputs(dt_input = df, dt_holidays = dt_prophet_holidays, date_var = "DATE", dep_var = "revenue", dep_var_type = "revenue",
                     prophet_vars = pv, prophet_country = "GB", paid_media_spends = "spend_ch", paid_media_vars = "spend_ch",
                     window_start = min(df$DATE), window_end = max(df$DATE), adstock = "geometric", hyperparameters = hyper))
  OM <- suppressWarnings(robyn_run(InputCollect = IC, iterations = iters, trials = 1, ts_validation = TRUE, cores = 2, seed = 1, outputs = FALSE))
  OC <- suppressWarnings(robyn_outputs(IC, OM, pareto_fronts = "auto", clusters = FALSE, csv_out = NULL, plot_pareto = FALSE, plot_folder = tempdir(), export = FALSE, quiet = TRUE))
  rp <- OC$resultHypParam %>% filter(robynPareto == 1)
  ag <- OC$xDecompAgg %>% filter(rn == "spend_ch")
  pick <- function(sol) ag$xDecompAgg[ag$solID == sol][1]
  s_nrmse <- rp$solID[which.min(rp$nrmse_val)]; s_err <- rp$solID[which.min(rp$error_score)]
  data.frame(est_nrmse = pick(s_nrmse), est_errscore = pick(s_err), nrmse_val_best = min(rp$nrmse_val), n_pareto1 = nrow(rp),
             theta = rp$spend_ch_thetas[which.min(rp$nrmse_val)], gamma = rp$spend_ch_gammas[which.min(rp$nrmse_val)], alpha = rp$spend_ch_alphas[which.min(rp$nrmse_val)])
}
first <- !file.exists(outfile)
for (i in ids) for (iv in c("week", "day")) {
  f <- sprintf("robyn_markets/market_%02d_%s.csv", i, ifelse(iv == "day", "daily", "weekly")); t0 <- Sys.time()
  r <- tryCatch(run_one(f, iv), error = function(e) { message("ERR market ", i, " ", iv, ": ", conditionMessage(e)); NULL })
  if (is.null(r)) r <- data.frame(est_nrmse = NA, est_errscore = NA, nrmse_val_best = NA, n_pareto1 = NA, theta = NA, gamma = NA, alpha = NA)
  row <- cbind(market = i, interval = iv, iterations = iters, secs = round(as.numeric(difftime(Sys.time(), t0, units = "secs"))), r)
  write.table(row, outfile, sep = ",", row.names = FALSE, col.names = first, append = !first); first <- FALSE
  cat("done market", i, iv, "\n", file = stderr())
}
