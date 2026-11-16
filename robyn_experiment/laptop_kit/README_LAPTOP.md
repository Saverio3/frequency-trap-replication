# Controlled Robyn experiment: laptop kit (Frequency Trap, Reviewer 1 point 2)

What this runs: the same 16 simulated 3-channel markets, through the REAL Robyn 3.12.1 code, in three arms. A = weekly Robyn. B = weekly KPI with media adstock and saturation applied to DAILY spend and then summed to weeks (the clean test of temporal aggregation; Meta's Robyn code with one switch in `run_transformations`, inactive unless an environment variable is set). C = daily Robyn (secondary). The design, written before any run, is in DESIGN_ROBYN_CONTROLLED.md. Do not change settings between markets.

I am already running markets 0-7 in the cloud. If you want to speed things up, run markets 8-15 (arms A and B) on your laptop with this kit. The two sets of result files can then be merged.

## 1. One-time setup (about 30 min)
1. Install R 4.3 or newer from r-project.org. On Windows also install Rtools (needed to build packages) if asked.
2. Open R and install the dependencies (copy-paste):
   `install.packages(c("glmnet","prophet","reticulate","doParallel","foreach","doRNG","dplyr","tidyr","stringr","lubridate","jsonlite","ggplot2","ggridges","patchwork","minpack.lm","data.table","Rcpp","rlang","magrittr","gridExtra","scales","nloptr","lares"))`
3. Install Python 3.9-3.11 if you do not have it, then Nevergrad for Robyn. In R: `reticulate::virtualenv_create("r-reticulate"); reticulate::virtualenv_install("r-reticulate", "nevergrad")` (If numpy 2.x gives errors, run `reticulate::virtualenv_install("r-reticulate", "numpy<2")`.)
4. Install the PATCHED Robyn into its own library folder so your normal Robyn is untouched. In a terminal in this kit folder:
   Mac/Linux: `mkdir -p rlibB && R CMD INSTALL --no-docs -l rlibB RobynPatched`
   Windows (cmd): `mkdir rlibB` then `R CMD INSTALL --no-docs -l rlibB RobynPatched`
5. Tell the script where things are (Mac/Linux shown; Windows: use `set NAME=value`, PowerShell: `$env:NAME="value"`):
   `export ROBYN_LIB_DIRS="$(pwd)/rlibB"`
   `export RETICULATE_PYTHON=""`   (empty = use the r-reticulate virtualenv you just made)
   Windows: separate several library folders with `;` instead of `:`.

## 2. Check it works (5 minutes)
`Rscript run_robyn_mc.R 0 B 100 1 results/test.csv 2` should end with `done market 0 arm B` and create results/test.csv. Delete that file afterwards (`results/test.csv`).

## 3. Run (long)
How long: at 2,000 iterations x 5 trials a run takes about 35 minutes on 2 cores; roughly 4x faster on 8 cores. Markets 8-15 with arms A and B = 16 runs: about 10 hours on 2 cores, about 3 hours on 8 cores. Keep the laptop awake and plugged in.
Command (use your core count minus 1 for the last number):
`Rscript run_mc_queue.R "8 9 10 11 12 13 14 15" results/RXM_laptop.csv 7`
You can stop it at any time and run the same command again: finished runs are skipped.

## 4. Send me the result
Send results/RXM_laptop.csv (a small file). I merge it with the cloud results and run the pre-declared analysis (`python an_rxm.py results/RXM_full.csv results/RXM_laptop.csv`).

## What the output means
Each run writes two rows (rule errscore = Robyn's own combined error score, the PRIMARY selection rule; rule nrmse = lowest validation error, secondary), the estimated media contribution per channel and in total, Robyn's convergence message, and timing. Truth is in robyn_mc/truth_mc.csv. Same-seed repeats of Robyn do not reproduce each other exactly (Nevergrad's search is not controlled by Robyn's seed), so small differences from my numbers are normal and are part of what the study measures.

## Troubleshooting
- `there is no package called X`: install it with install.packages("X").
- `nevergrad` / python errors: re-do step 3; `reticulate::py_config()` shows which Python is used.
- On Windows, if Rscript is not found, use the full path, e.g. `"C:\Program Files\R\R-4.3.3\bin\Rscript.exe"`.
- Untested on your machine: I built and tested this on Linux. If something fails, send me the error text.
