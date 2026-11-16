# Helper functions for the stability experiment: pull everything we want to keep out of Robyn's output objects.
conv_flags <- function(OM) {
  msgs <- tryCatch(as.character(unlist(OM$convergence$conv_msg)), error = function(e) character(0))
  pick <- function(key) { m <- msgs[grepl(key, msgs, fixed = TRUE)]; if (length(m)) m[1] else NA_character_ }
  rssd <- pick("DECOMP.RSSD"); nr <- pick("NRMSE")
  list(rssd_msg = rssd, nrmse_msg = nr,
       rssd_conv = if (is.na(rssd)) NA else !grepl("NOT converged", rssd, fixed = TRUE),
       nrmse_conv = if (is.na(nr)) NA else !grepl("NOT converged", nr, fixed = TRUE))
}

est_by_sol <- function(OC, chs) {
  ag <- OC$xDecompAgg[OC$xDecompAgg$rn %in% chs, , drop = FALSE]
  sols <- unique(ag$solID)
  out <- data.frame(solID = sols, stringsAsFactors = FALSE)
  for (ch in chs) { v <- ag[ag$rn == ch, , drop = FALSE]; out[[paste0("est_", ch)]] <- v$xDecompAgg[match(sols, v$solID)] }
  out$est_total <- rowSums(out[paste0("est_", chs)])
  out
}

pkgv <- function(p) tryCatch(as.character(utils::packageVersion(p)), error = function(e) NA_character_)

write_manifest <- function(file, mk, arm, tag, iters, trials, seed, cores, hyper_txt, dailyf) {
  nv <- tryCatch(as.character(reticulate::import("nevergrad")$`__version__`), error = function(e) NA_character_)
  npv <- tryCatch(as.character(reticulate::import("numpy")$`__version__`), error = function(e) NA_character_)
  m <- data.frame(time = format(Sys.time(), "%Y-%m-%d %H:%M:%S"), market = mk, arm = arm, tag = tag, iterations = iters, trials = trials, seed = seed, cores = cores,
                  r_version = R.version.string, platform = R.version$platform, robyn = pkgv("Robyn"), robyn_path = tryCatch(find.package("Robyn"), error = function(e) NA_character_),
                  glmnet = pkgv("glmnet"), prophet = pkgv("prophet"), reticulate = pkgv("reticulate"), nevergrad = nv, numpy = npv,
                  python = Sys.getenv("RETICULATE_PYTHON"), hyperparameters = hyper_txt, daily_spend_file = dailyf, host = Sys.info()[["nodename"]], stringsAsFactors = FALSE)
  write.table(m, file, sep = ",", row.names = FALSE, col.names = !file.exists(file), append = file.exists(file), qmethod = "double")
}

# Writes the full model table, convergence table, and returns the 2 summary rows (one per selection rule).
extract_stab <- function(OC, OM, mk, arm, iters, trials, seed, cores, secs, tag, outdir) {
  chs <- c("ch1", "ch2", "ch3")
  dir.create(outdir, showWarnings = FALSE, recursive = TRUE)
  hp <- OC$resultHypParam; est <- est_by_sol(OC, chs)
  allm <- merge(hp, est, by = "solID", all.x = TRUE, sort = FALSE)
  allm <- cbind(market = mk, arm = arm, tag = tag, allm)
  stem <- file.path(outdir, sprintf("m%02d_%s_%s", mk, arm, tag))
  write.csv(allm, paste0(stem, "_models.csv"), row.names = FALSE)
  tryCatch(write.csv(as.data.frame(OM$convergence$errors), paste0(stem, "_convergence.csv"), row.names = FALSE), error = function(e) NULL)
  cf <- conv_flags(OM)
  p1 <- allm[which(allm$robynPareto == 1 & !is.na(allm$est_total)), , drop = FALSE]
  if (nrow(p1) == 0) stop("no Pareto-1 models with estimates")
  qs <- stats::quantile(p1$est_total, c(0, 0.25, 0.5, 0.75, 1), names = FALSE)
  rules <- list(errscore = which.min(p1$error_score), nrmse = which.min(p1$nrmse_val))
  rk_err <- rank(p1$error_score, ties.method = "min"); rk_nr <- rank(p1$nrmse_val, ties.method = "min"); rk_rs <- rank(p1$decomp.rssd, ties.method = "min")
  rows <- lapply(names(rules), function(nm) {
    i <- rules[[nm]]; s <- p1[i, , drop = FALSE]
    data.frame(market = mk, arm = arm, tag = tag, rule = nm, iterations = iters, trials = trials, seed = seed, cores = cores, secs = secs,
               est_ch1 = s$est_ch1, est_ch2 = s$est_ch2, est_ch3 = s$est_ch3, est_total = s$est_total,
               nrmse_val = s$nrmse_val, decomp_rssd = s$decomp.rssd, error_score = s$error_score, solID = s$solID,
               n_pareto1 = nrow(p1), n_models = nrow(hp),
               sel_rank_errscore = rk_err[i], sel_rank_nrmse = rk_nr[i], sel_rank_rssd = rk_rs[i],
               sel_pct_nrmse = mean(p1$nrmse_val <= s$nrmse_val), sel_pct_rssd = mean(p1$decomp.rssd <= s$decomp.rssd),
               p1_total_min = qs[1], p1_total_q25 = qs[2], p1_total_med = qs[3], p1_total_q75 = qs[4], p1_total_max = qs[5],
               nrmse_converged = cf$nrmse_conv, rssd_converged = cf$rssd_conv, conv_msg_nrmse = cf$nrmse_msg, conv_msg_rssd = cf$rssd_msg,
               stringsAsFactors = FALSE)
  })
  do.call(rbind, rows)
}
