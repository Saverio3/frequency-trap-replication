# Robyn stability and convergence check (design fixed BEFORE any run; 4 Nov 2026)

## Why
The controlled experiment (DESIGN_ROBYN_CONTROLLED.md, results in results/RXM_laptop.csv) gave one run per market, arm and selection rule at 2,000 iterations x 5 trials. Robyn's search (Nevergrad TwoPointsDE) is NOT reproducible under the same seed, and Robyn's own convergence check failed on at least one of its two criteria in 30 of 40 runs (both converged 10; NRMSE converged but DECOMP.RSSD not 18; DECOMP.RSSD converged but NRMSE not 6; neither 6). The two criteria are different things and are recorded separately here. Before interpreting the A-versus-B difference, we need to know (1) how much a selected estimate moves when the SAME run is repeated, and (2) whether doubling the optimisation budget moves it by more than that.
This is a STABILITY experiment, not a new test of whether A or B is better in general.

## What is run (24 runs, nothing else)
Markets 0, 2, 4, 7, 11, 13 (chosen BEFORE this run, from the first experiment: 0 and 7 large A-B differences, 2 correlated with B better, 4 and 11 very large bias, 13 substantial bias in both arms). Arms A and B only. The underlying simulated data are the existing files robyn_mc/market_XX_*.csv (unchanged).
- tag `rep2000`: 2,000 iterations x 5 trials, identical configuration to the first run (12 runs).
- tag `inc4000`: 4,000 iterations x 5 trials, everything else identical (12 runs).
- The first-experiment run is called `orig2000` and is read from results/RXM_laptop.csv, which is never modified by this experiment.
Seed argument 1 in all runs (as in the first experiment; it does not control Nevergrad, so repeats differ anyway). Same Robyn version, same patched package, same hyperparameter bounds, same Prophet settings, same selection rules (PRIMARY error_score, SECONDARY validation NRMSE), clustering off.
Selection of the six markets was by outcome (extreme or interesting cells), so the result describes stability in those markets and is not a representative sample of the 16.

## What is saved for every run (results/stab_pareto/)
- the full table of ALL models Robyn evaluated that reach the output step (`..._models.csv`): hyperparameters, nrmse_val, decomp.rssd, error_score, Pareto front number, and the estimated contribution of each channel and in total for every Pareto-front model;
- the two convergence messages separately, with a TRUE/FALSE flag for NRMSE and for DECOMP.RSSD, and Robyn's convergence error table where available (`..._convergence.csv`);
- the selected model for each rule, its rank inside the Pareto-1 set on error_score, NRMSE and DECOMP.RSSD, its percentile on NRMSE and DECOMP.RSSD, and the minimum, quartiles and maximum of the total contribution across Pareto-1 models;
- a run manifest (results/stab_manifest.csv): date, market, arm, tag, iterations, trials, seed, cores, R version, Robyn, glmnet, prophet, reticulate, nevergrad and numpy versions, the folder Robyn was loaded from, the hyperparameter bounds, the daily spend file used by arm B.
Summary rows (2 per run, one per selection rule) go to results/RXM_stability.csv.

## Pre-declared analysis (an_stab.py)
Bias = 100 (estimated total - true total) / true total, as before.
- Noise unit N: for each market x arm x rule cell (12 cells per rule) N = |bias(orig2000) - bias(rep2000)|.
- Budget shift S: S = bias(inc4000) - mean(bias(orig2000), bias(rep2000)) (signed).
- Reading rule, fixed now. With no budget effect, the expected |S| is about 0.87 times the expected N (algebra: the SD of S is 1.22 sigma, the SD of the difference of two runs is 1.41 sigma). Therefore: median|S| <= median N means NO MATERIAL BUDGET EFFECT; median|S| > 1.5 x median N AND |mean S| > 2 SE means an OPTIMISATION-STABILITY PROBLEM (the 2,000-iteration results are not settled); anything in between is INCONCLUSIVE and is reported as such. With 12 cells per rule this is descriptive, not a formal test, and the paper will say so.
- Also reported: the paired A minus B difference of |bias| in these six markets under orig2000, rep2000 and inc4000 (does the sign survive?); the number of markets in which the sign of A minus B changes between runs; the share of runs with each convergence outcome (both, NRMSE only, RSSD only, neither) at 2,000 and at 4,000; the change in the number of Pareto-1 models; the spread of total contribution across Pareto-1 models compared with N.
- Not done: no new markets, no claim about A versus B in general, no change to the first experiment's results, no re-selection of markets or rules after seeing results.

## How A and B must be described in the paper (stated now)
A and B are two complete frequency-specific transformation workflows inside Robyn, not a pure change of the aggregation point with the absolute response function held fixed. Same weekly KPI, same weekly model rows, same ridge, validation split, objectives, search and scoring; but (1) theta is a per-week decay in A and a per-day decay in B, with the same numeric bounds 0.01-0.95; (2) Robyn's saturation inflexion is gamma times the maximum of the adstocked series, a weekly maximum in A and a daily maximum (within the rolling window) in B, with the same gamma bounds 0.05-1; (3) in B the Hill curve is applied to each day and the seven values are summed. The A-versus-B contrast therefore measures the frequency-specific workflow, and must not be described as isolating aggregation alone.

## Compute (estimate, to be replaced by the measured times)
About 15 minutes per 2,000 x 5 run (15 cores), about 30 minutes for 4,000 x 5: 12 x 15 + 12 x 30 = about 9 hours, plus about 4 minutes of smoke tests. The laptop must stay awake and plugged in (the first experiment had one run whose timer includes a sleep period).
