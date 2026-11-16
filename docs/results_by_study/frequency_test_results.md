# Can any test identify the better aggregation with 95%+ accuracy? (run 10 Oct 2026)

Design: DESIGN_TESTS.md (stage 1 before running SELT; stage 2 rule written after SELT and before running the fresh batch SELU).
Scale: SELT 9,660 markets (calibration), SELU 9,660 fresh markets (confirmation), 483 cells in eight worlds, 20 reps per cell. Each market runs 252 weekly candidates, 252 daily candidates and 39 within-week permutations.

## Short answer
- Against "which arm is closer to the truth in THIS market": no. The ceiling is about 82-84% even on the 2-10% of markets where the tests are most confident. A rule that knows the exact simulated world scores only 75% on material markets, because part of the answer is random noise in each market. 95% is not reachable on this question.
- Against "is the true process weekly or daily-or-finer?": yes, in a defined zone. The Vuong test (a standard non-nested likelihood-ratio test from econometrics) classifies the process correctly 99% of the time when the observable fit R2 is at least 0.80 (60% of the simulated markets), and 97-98% across all markets, on fresh seeds.


## CORRECTION (10 Oct 2026, added after a follow-up check)
Earlier text in this file and in the chat said the test fails in noisy weekly-true markets. That was an artefact of my calibration, not of the test. The leave-one-world-out logistic cutoff had no noisy weekly-true example to learn from when W8 was held out, so it put the cutoff in the wrong place.
The plain Vuong SIGN rule (daily if z > 0, weekly otherwise, nothing tuned) pooled over both batches (19,320 markets):
- balanced accuracy 0.976 (SELT 0.976, SELU 0.977); daily-true 0.959, weekly-true 0.994.
- by observable fit R2, weekly-true: 0.969-1.000 in every bin from 0.3 up. Daily-true: 0.953-0.978 from 0.3 up, 0.74 below 0.3 (only 5 weekly-true markets there).
- Genuine weak spots: time-varying effects (tv weekly 76%, tv daily 90%) and near-linear response (77.5%). In those worlds the label "daily" is a mechanical label from the generator and the weekly model can legitimately fit as well or better, so the check can mislead there.
Oracle bound (oracle_bound.py): a likelihood-ratio classifier that KNOWS the true decay, depth, shape and baseline separates weekly-true from daily-true worlds almost perfectly even at signal R2 = 0.3 (balanced 0.996 at 156 weeks, 0.989 at 104 weeks, 0.999 at 312 weeks). So noise is not a fundamental barrier at these sample sizes, and the headroom above the Vuong sign rule is small (it gets 0.95-0.97 at R2 0.3-0.5).
The fit-R2 "zones" in the sections above are superseded by this: the zone restriction is not needed for R2 >= 0.3.

## Tests compared (all use only the weekly KPI and daily spend)
| Test | Source field | AUC, world label | AUC, market label |
|---|---|---|---|
| T1 fit gap log(SSE_w/SSE_d) | model selection | 0.998 | 0.727 |
| T2 J / encompassing test | econometrics (Davidson-MacKinnon) | 0.998 | 0.726 |
| T3 Vuong test | econometrics (non-nested likelihood ratio) | 0.998 | 0.724 |
| T4 Jensen-gap (concentration-residual), new | my own, from Proposition 1 | 0.83 | 0.67 |
| T5 within-week permutation (surrogate data), new use | nonlinear physics (Theiler et al.) | 0.96 | 0.69 |

The classical tests won. The two new tests were weaker and added nothing when stacked with T1-T3. Other fields searched (pharmacokinetic model discrimination, system-identification residual tests, Bayes factors in astronomy) use the same ideas as T1-T3: compare the fit of competing models, penalise complexity, test residuals. Both arms here have the same complexity, so they reduce to the fit gap or the Vuong test.

## Label A (world): leave-one-world-out on SELT, then fresh seeds on SELU
- SELT leave-one-world-out balanced accuracy (the pre-registered metric): T3 0.933, T2 0.928, T1 0.906, stack 0.924. The 0.95 bar was NOT met. The failures were noisy weekly-true markets (R2 0.5: 51% correct) and the weak cases (time-varying weekly effects 86%, linear response 84%, where the aggregation barely matters).
- Accuracy depends on the observable fit R2 (SELT, exploratory): above 0.8 about 99% for both classes; 0.7-0.8 about 91% when truth is weekly and 98% when daily; below 0.7 weekly truth is mostly not identified.
- Rule Q, written before SELU: restrict to markets with fit R2 >= 0.80 and classify with the stack trained on SELT.
  - SELU result in the zone (5,788 markets, 60% of the total): balanced accuracy 0.995, daily TPR 0.993, weekly TNR 0.996. All pre-registered criteria passed.
  - Outside the zone (3,872 markets): balanced 0.952.
  - All markets: balanced 0.975.
- Simplest version (no fitted parameters): call DAILY if Vuong z > 0, WEEKLY otherwise.
  - SELU, zone: balanced 0.990 (daily TPR 0.980, weekly TNR 1.000). SELU, all markets: 0.977. SELT, zone 0.988, all 0.976.
  - Daily-true markets have mean z of +4.1, weekly-true markets -3.8.
  - This sign rule was examined after seeing SELU results (exploratory), but it has no tuned parameter and gives the same answer on SELT.
- Decision value inside the zone (SELU): mean |bias| always weekly 22.6, always daily 18.6, call the process then pick 16.6.

## Label B (the single market): why 95% is impossible
- Cell-oracle hit rate on material markets 75% (67-82% by world). Gradient boosting on every feature, leave-one-world-out: 65-78%. Selective accuracy against coverage plateaus at 82-84%. Protocol P's CLEAR tier (earlier study) gave 80%.
- Inside the zone, calling the process correctly (99%) still picks the arm that is closer in the single market only 71% of the time (material markets).

## Caveats (must go in the paper)
- The label is by construction: the simulated truth is exactly weekly or exactly daily-or-finer. Real processes can be neither (mixtures, multi-day delivery lags, channel-specific timing). The tests find which of the two candidate models fits better, which equals the truth only when the truth is one of the two.
- Fit R2 here is the media model's share of the KPI variance left after trend and seasonality. The simulations set it near 0.85 by construction. In real MMMs with many other drivers, noise and collinearity, it will often be lower, so many real cases would land in the weaker zone.
- Only 156 weeks, one grid, 7-day weeks. Shorter samples, other grids and multi-channel models are untested.
- Identifying the process does not remove the bias in your estimate. Mean |bias| in the zone is still 12-22% in most worlds.
- The linear-response world (84%) shows the limit: when response is near linear, aggregation barely matters and the label is meaningless.
- The worlds are my constructions. Whether they represent real advertising cannot be settled by simulation.

## Tool
freq_check.py: frequency_check(y, spend_daily) returns Vuong z, fit-gap, R2fit, a DAILY/WEEKLY verdict, and a trust level from R2fit. Verified to reproduce the batch statistics exactly on seven markets.
