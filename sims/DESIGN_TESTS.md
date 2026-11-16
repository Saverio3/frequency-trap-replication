# Can any test identify the better aggregation with 95%+ accuracy? (design fixed BEFORE running, 10 Oct 2026)

## Ceiling facts already known (from stage 2 data, computed before designing the tests)
- Cell-oracle (knows the exact simulated world, only not the noise): hits the better arm in 75% of material markets (range 67-82% by world). The label "which arm has lower |bias| in this market" is partly noise, so no rule that only knows the world can reach 95%.
- Gradient boosting on the existing features, leave-one-world-out: 68-80% by world.
- Protocol P CLEAR tier: 80% on about 35% of markets.
So 95% on every market against the market-level label is very unlikely. The question is whether any test reaches 95% on a subset (selective accuracy) or on the world-level label (is the truth weekly or daily?).

## Two labels
- Label B (market): the arm with lower |bias| in this market. Evaluated on MATERIAL markets (arms differ by more than 5 points).
- Label A (world): truth is weekly (worlds W2, W8) vs truth acts at daily or finer resolution (all other worlds). Evaluated on all markets, reported as balanced accuracy.

## Candidate tests (positive = favours daily). Inputs: weekly KPI y, daily spend only.
- T1 fit gap: log(SSE_weekly/SSE_daily). (best-of-252 fit per arm)
- T2 J / encompassing test (Davidson-MacKinnon family, econometrics): regress y (after controls) on the best weekly and best daily transformed series together; statistic = t_daily - t_weekly.
- T3 Vuong test (non-nested likelihood ratio, econometrics): normal log-likelihood per week for each fitted arm; statistic = mean(LR)/(sd(LR)/sqrt(n)).
- T4 Jensen-gap (concentration-residual) test, new: weekly concentration H_t = sum over days of (daily share of week spend)^2. Regress each arm's residuals on H_t (after controls). Statistic = |t_H of weekly residuals| - |t_H of daily residuals|. Mechanism: if the truth is daily and nonlinear, a weekly model leaves residuals that depend on how concentrated the week's spend was.
- T5 Within-week permutation (surrogate-data) test, borrowed from nonlinear physics (Theiler et al.): shuffle the order of days inside each week (weekly totals unchanged, so the weekly arm is unchanged), refit the daily arm 39 times. Statistic z = (mean permuted SSE - actual SSE)/sd(permuted SSE). Large z = day order carries information the weekly total does not.
- T6 Stack: logistic regression on T1-T5 plus D and dR2 (from earlier), trained on other worlds only.
- Ceiling: gradient boosting on T1-T5 + earlier features, leave-one-world-out.

## Evaluation (fixed)
- Fresh seeds, prefix "SELT", 20 reps per cell, the 483 cells of stage 2 (W1-W8). Final candidate then confirmed on another fresh batch ("SELU").
- Leave-one-world-out calibration: for a held-out world, a logistic map from the statistic(s) to P(daily better) is fitted on the other worlds only. Confidence = |P - 0.5|. The abstention cutoff is the smallest confidence at which accuracy on the TRAINING worlds is at least 0.95. The rule is then applied to the held-out world. We report realized accuracy and coverage (share of markets answered).
- Also report full-coverage accuracy of each statistic.
## Claim rules
- "A 95% test exists" only if, pooled over held-out worlds on the confirmation batch, selective accuracy >= 0.95 and no held-out world is below 0.90, AND coverage is reported. Otherwise we report the best accuracy-coverage pairs achieved and say 95% was not reached.
- World-level label: report balanced accuracy; 95% claimed only if >= 0.95 in leave-one-world-out.
- No threshold or statistic is changed after seeing the results of the SELT batch except by being replaced on the confirmation batch by the SELT-calibrated version.

## Stage 2 (written after the SELT batch, before the confirmation batch SELU) - 10 Oct 2026
SELT results (pre-registered metrics): against the market-level label B no statistic or stack reached 95% selective accuracy on the training worlds (the cutoff search never found one), and the selective accuracy curve plateaus at 82-84% even at 2-10% coverage. Against the world-level label A, the fit gap (T1), J-test (T2) and Vuong (T3) separate weekly-true from daily-or-finer worlds with AUC 0.998, but pooled balanced accuracy was 0.91-0.93, below the 0.95 bar, with failures concentrated in noisy weekly-true markets (W8) and weak cases (time-varying weekly, linear response).
Exploratory (post hoc) observation: accuracy depends strongly on the observable fit R2 of the better arm after controls: >= 0.8 gave about 99% for both classes, 0.7-0.8 about 91% weekly-true / 98% daily-true, below 0.7 weekly-true is not identified.
Confirmation rule (fixed now): "Rule Q" = restrict to markets whose observable fit R2 (derived as 1 - min(SSE_w, SSE_d)/SSE_y_after_controls) is >= 0.80; classify with the ALL_tests logistic stack (T1,T2,T3,T4,T5) trained on all SELT markets. Fresh seeds prefix SELU, 20 reps, same 483 cells. Success: pooled balanced accuracy >= 0.95 inside the zone AND daily-world TPR >= 0.95 AND weekly-world TNR >= 0.90 AND every sub-world in the zone with n>=50 >= 0.85. Also report share of markets in the zone by world (coverage), and accuracy outside the zone. Label B stays at its stage-1 verdict (95% not reachable).
