# Equivalence tests T1/T2 (DESIGN_ROBYN_CONTROLLED.md). Usage: Rscript test_patch_equiv.R <lib: std|patched> <mode: std|b1|b7> <out.csv>
args <- commandArgs(trailingOnly = TRUE); lib <- args[1]; mode <- args[2]; out <- args[3]
.libPaths(c(if (lib == "patched") "/home/claude/rlibB", "/home/claude/rlib", .libPaths()))
suppressMessages({library(Robyn); library(dplyr)}); Sys.setenv(RETICULATE_PYTHON = "/home/claude/ngenv/bin/python")
if (mode == "b1") { Sys.setenv(ROBYN_DAILY_SPEND_FILE = "robyn_mc/market_00_weekly.csv", ROBYN_DAILY_BLOCK = "1") }
if (mode == "b7") { Sys.setenv(ROBYN_DAILY_SPEND_FILE = "robyn_mc/market_00_daily.csv", ROBYN_DAILY_BLOCK = "7") }
data("dt_prophet_holidays")
df <- read.csv("robyn_mc/market_00_weekly.csv"); df$DATE <- as.Date(df$DATE)
hyper <- list(ch1_alphas = c(0.5, 3), ch1_gammas = c(0.05, 1), ch1_thetas = c(0.01, 0.95), ch2_alphas = c(0.5, 3), ch2_gammas = c(0.05, 1), ch2_thetas = c(0.01, 0.95),
              ch3_alphas = c(0.5, 3), ch3_gammas = c(0.05, 1), ch3_thetas = c(0.01, 0.95), train_size = c(0.5, 0.9))
IC <- suppressWarnings(robyn_inputs(dt_input = df, dt_holidays = dt_prophet_holidays, date_var = "DATE", dep_var = "revenue", dep_var_type = "revenue",
        prophet_vars = c("trend", "season"), prophet_country = "GB", paid_media_spends = c("ch1", "ch2", "ch3"), paid_media_vars = c("ch1", "ch2", "ch3"),
        window_start = min(df$DATE), window_end = max(df$DATE), adstock = "geometric", hyperparameters = hyper))
draws <- read.csv("results/equiv_draws.csv"); res <- list()
for (d in seq_len(nrow(draws))) {
  hp <- draws[d, , drop = FALSE]
  tt <- run_transformations(all_media = IC$all_media, window_start_loc = IC$rollingWindowStartWhich, window_end_loc = IC$rollingWindowEndWhich,
                            dt_mod = IC$dt_mod, adstock = IC$adstock, dt_hyppar = hp)
  res[[d]] <- data.frame(draw = d, week = seq_len(nrow(tt$dt_modSaturated)),
    sat1 = tt$dt_modSaturated$ch1, sat2 = tt$dt_modSaturated$ch2, sat3 = tt$dt_modSaturated$ch3,
    imm1 = tt$dt_saturatedImmediate$ch1, imm2 = tt$dt_saturatedImmediate$ch2, imm3 = tt$dt_saturatedImmediate$ch3,
    car1 = tt$dt_saturatedCarryover$ch1, car2 = tt$dt_saturatedCarryover$ch2, car3 = tt$dt_saturatedCarryover$ch3,
    infl1 = tt$inflexions[1], infl2 = tt$inflexions[2], infl3 = tt$inflexions[3])
}
write.csv(do.call(rbind, res), out, row.names = FALSE)
cat("names in dt_modSaturated:", names(tt$dt_modSaturated), "\n")
