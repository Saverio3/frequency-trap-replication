# Cross-platform queue (Windows / Mac / Linux). Usage from this folder:
#   Rscript run_mc_queue.R "8 9 10 11 12 13 14 15" results/RXM_laptop.csv 7
# args: markets (space separated), output csv, cores to give Robyn (use your cores minus 1), [iterations=2000] [trials=5]
# Arms A and B for every market, plus arm C for markets 0-7. Re-run the same command to resume: finished (market, arm) pairs are skipped.
args <- commandArgs(trailingOnly = TRUE)
markets <- as.integer(strsplit(args[1], " ")[[1]]); out <- args[2]; cores <- args[3]
iters <- if (length(args) >= 4) args[4] else "2000"; trials <- if (length(args) >= 5) args[5] else "5"
for (m in markets) for (a in c("A", "B", if (m <= 7) "C")) {
  if (file.exists(out)) { d <- read.csv(out); if (sum(d$market == m & d$arm == a) >= 2) next }
  cat(format(Sys.time()), "market", m, "arm", a, "\n")
  system2("Rscript", c("run_robyn_mc.R", m, a, iters, trials, out, cores), stdout = FALSE)
}
cat("QUEUE FINISHED\n")
