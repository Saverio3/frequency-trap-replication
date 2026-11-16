# Controlled Robyn-type comparison (Reviewer 1, point 2, second round). Design fixed BEFORE the full run (24 Oct 2026)

## What can and cannot be done
The R package Robyn cannot be installed in the cloud workspace used for these simulations (R and its package servers are not reachable). Meta also ships an alpha Python port (robynpy 0.3.6); it depends on R through rpy2 for its ridge step, so it cannot run here either. What was done instead:
1. Read Meta's published code (robynpy) and the R package's documented behaviour, and built an EQUIVALENT of the modelling loop: geometric adstock; Hill saturation with gamma as a fraction of the min-max range of the adstocked series (inflexion = gamma max + (1 - gamma) min, exactly as in Meta's `saturation_hill`); ridge on standardised inputs with lambda = lambda_min + (lambda_max - lambda_min) x lambda_hp, lambda_max = 0.1 max|X_s'y|/(0.001 n), lambda_min = 1e-4 lambda_max (Meta's `ridge_metrics_calculator`); media coefficients constrained non-negative; NRMSE on a time-series validation split (60% train, 20% validation, 20% test; coefficients from the training fit, as in Robyn); DECOMP.RSSD = sqrt(sum (effect share - spend share)^2) over paid media with the zero-effect penalty (Meta's `ridge_evaluate_model`); Nevergrad TwoPointsDE; every evaluated model kept and a Pareto set computed over (NRMSE, RSSD).
2. Verify the building blocks numerically against Meta's own code (adstock, Hill) in `rb_equivalence.py`.
3. Prepare an R script that runs the real Robyn package on exported data, for the author to run if desired (untested here, flagged as such).

## Held constant between the weekly arm and the daily arm
Same simulated markets (multichannel DGP of DESIGN_MULTI.md, new seeds, prefix RB), same controls (trend, annual sine and cosine, price), same hyperparameter bounds (theta 0.01-0.95, alpha 0.5-3, gamma 0.05-1, lambda_hp 0-1; wider than Robyn's default gamma 0.3-1 on purpose, so that neither arm is cut off), same search algorithm, same budget (2,000 evaluations, one trial), same random seed for the optimiser across the two arms of a market, same ridge and validation scheme, same sign constraints.
## Not held constant, by construction (must be stated in the paper)
- In the real package, a daily model uses a daily KPI; here the KPI stays weekly and the daily arm transforms daily spend then sums to weeks (the paper's arm). Robyn cannot do this natively.
- Robyn's Prophet decomposition (trend, season, weekday) and its automatic model clustering are replaced by fixed controls and three explicit selection rules.
- theta has a different meaning at the two frequencies (weekly theta is roughly daily theta to the 7th); the same numeric bounds are used.
- One trial of 2,000 iterations, not Robyn's default of 5 trials.
- Equivalence to the real package is checked at the level of formulas, not of end-to-end output.

## Searches and arms (all for weekly-transform "W" and daily-transform "D", applied to every channel)
- SO: single-objective search on validation NRMSE; best model by NRMSE.
- MO: multi-objective search (NRMSE, RSSD); three selection rules from the Pareto set: nrmse (lowest NRMSE), rssd (lowest RSSD), bal (closest to the ideal point after min-max scaling).
- Reference arms on the same markets: gridW, gridD (the paper's grid + backfitting + NNLS) and OT (true transforms).
## Scenarios and size
M1 independent, M2 correlated, M3 mixed truth, M7 time-varying with spend chasing; 100 markets each (400 markets), K = 3. Metrics: total contribution bias %, mean per-channel |bias|, paired D minus W of |bias| with 2-SE rule, truth RSSD (how far the true effect shares are from spend shares: if large, the RSSD objective penalises the truth).
## Expectations (reported either way)
R1 The search procedure adds error relative to the grid arms. R2 Daily beats weekly in M1 and M3 under SO, by less than with the grid. R3 M2 ties. R4 MO with the rssd rule is worse than the nrmse rule, and the gap grows with truth RSSD. R5 In M7 weekly is better.
## Note (before the full run)
One market (M1, market 0) was run at budgets 300 and 2,000 to time the engine and check that it behaves (lambda_hp converges to 0, i.e. ridge not binding; biases of about -50% in that single market for both frequencies; the rssd rule collapses the effect). No other results were seen. Nothing was changed after that look.
