# Reviewer-response simulations: design fixed BEFORE running (2 Oct 2026 / session of 10 Oct)

Rules for fairness
1. Same DGP generator, seeds scheme, estimators, metric as the paper (signed contribution bias % = 100*(est_total - true_total)/true_total; |bias| for averages).
2. Every cell in each grid is reported. No cell is dropped after seeing results.
3. Scenarios that favour the weekly arm are included on purpose (weekly-true world, time-varying effects, day-of-week).
4. Monte-Carlo SEs reported. Differences smaller than 2 SE are called ties.
5. Engine is first validated against the published partA_results.csv core cells.
6. If a new scenario reverses the paper's ordering, it is reported as a boundary condition, not hidden.

Arms
- weekly: sum spend to weeks, adstock + Hill on weekly totals, grid search (paper arm).
- dailyT: adstock + Hill on daily spend, sum to weeks, regress weekly KPI, grid search (paper arm).
- dailyT_reg: dailyT with decay grid restricted to true class (paper arm), only where stated.
- oracle: true transforms, OLS (paper arm).

S1 (Reviewer 1, point 1A): time-varying effectiveness
- Truth: response_t = e_t * f(adstock_t); e_t = exp(0.5*z_t - 0.125).
- tv type: none | daily (AR1 phi=0.6 day level) | weekly (constant in week, AR1 phi=0.8 across weeks) | drift (smooth sinusoid+RW over sample).
- Budget tilt kappa in {0, 0.5, 1.0}: spend_t = base_spend_t * exp(kappa*z_t) (for bursty also the active-day probability is tilted).
- f linear (reviewer's time-varying linear model) for main grid: tv x kappa x delta{0.15,0.5,0.85} x pattern{bursty,smooth,real}, 200 reps.
- Robustness f = Hill (h 1.0 and 2.2, depth med) with tv=daily, kappa{0,1}, 100 reps.

S2 (Reviewer 1, point 1B): day-of-week
- Daily sales = base_week/7 * dow_mult + response (additive form) or response*dow_mult (multiplicative form) + daily noise (weekly-equivalent R2 0.85).
- dow strength {0 control, 0.3, 0.6}; profile Mon..Sun = [-.4,-.4,-.2,0,.8,1.0,-.8].
- Spend alignment: neutral | thursday (x3 on Thu) | peak (x3 Fri,Sat) | offpeak (x3 Mon,Tue).
- Arms: weekly, dailyT (weekly KPI), dailyKPI_noDOW (daily KPI regression, no weekday dummies), dailyKPI_DOW (with dummies), oracle.
- Truth Hill h{1.0,2.2} depth med; delta{0.15,0.5,0.85}; pattern{bursty,smooth,real}; 100 reps.

S3 (Reviewer 1, point 2): Robyn-style search isolation (emulation, NOT Robyn itself)
- Same continuous search (Nevergrad TwoPointsDE), same bounds, same ridge, same trend+season controls for both arms.
- Weekly arm transforms weekly totals; daily arm transforms daily then sums to weeks.
- Variant I: in-sample NRMSE objective. Variant V: Robyn-like train/validation split, objective validation NRMSE, coefficients from training window.

S4 (Reviewer 3)
- 4a sub-daily truth: truth at 6-hour (K=4) and hourly (K=24); intra-day split Dirichlet(alpha 0.3, 1.0); arms weekly, daily, native-fine, oracle.
- 4b alternative DGPs: weekly-true (truth built on weekly totals), linear response (placebo), log1p response, power 0.5 response, two-component adstock (fast+slow), endogenous wear-out.
