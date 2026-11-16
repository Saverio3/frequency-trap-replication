# Shallow-saturation recovery and targeted weekday test: results (run 24 Oct 2026)

Designs: DESIGN_RECOVERY.md and DESIGN_DOW2.md (both written before the full runs; one numerical guard added to the continuous fit after a smoke test and before the full run, recorded in the design file).

## Part 1. Shallow saturation: can the model recover the curve? (10,800 markets, 180 cells x 60 reps)
Truth is always daily. Depth = where the true half-saturation point sits relative to the observed spend: med (P50 of adstock, the paper's reference), mild (P90), x1, x3, x10 (1, 3, 10 times the maximum adstock, so the curve is almost a straight line). Estimators: G = paper's grid, X = grid extended with gamma at 1, 3, 10, 30 times the maximum, C = continuous fit (Nelder-Mead on delta, gamma, h).

### 1. The paper's own grid cannot represent shallow truth (expectation E1 supported)
Mean |total contribution bias| %, daily transform: G 18.8 (med), 18.6 (mild), 32.7 (x1), 41.0 (x3), 42.2 (x10). With the extended grid X: 18.8, 19.4, 16.7, 12.9, 12.9. Weekly transform: G 29.0, 24.8, 35.9, 43.7, 45.5; X 29.1, 26.2, 24.4, 21.0, 21.3. The paper's depth range (mild P90 to deep P25) sits inside the grid, so its published results are unaffected, but anyone using a grid whose gamma cannot exceed the observed adstock will be wrong when saturation is shallow.

### 2. Total contribution can look fine while the curve is not identified (E2 supported)
With X, daily: 50% of markets at med depth have |total bias| < 10%, and 63-65% at x3 and x10. Among those "good looking" markets, the share whose prediction at twice the spend is off by more than 25% of the true contribution is 0.5% (med), 3.4% (mild), 17% (x1), 31% (x3), 24% (x10). Weekly: 1.8%, 7.2%, 44%, 39%, 30%. Median |error| when spend is tripled, daily X: 11.3%, 15.0%, 27.1%, 43.1%, 41.5%. Median |marginal ROI error| stays small (4-5% daily, 6-9% weekly) at the observed spend level, because the local slope is well identified; what is not identified is the shape away from the observed range.

### 3. Parameters (E4 supported for gamma; shape needs care)
Daily decay is recovered well at every depth (median |error| 0.04). The half-saturation point is not: the share of markets where gamma_hat is off by more than a factor of 2 is, for X, 11% (med), 12% (mild), 42% (x1), 66% (x3), 89% (x10); for the paper's grid 100% at x3 and x10 (it cannot reach). Shape: the grids contain the true shape values (1.0, 2.2), so grid shape recovery is flattering; the continuous fit has median |h error| 0.2-0.5.
Identification width (X, daily): about 12-14 grid candidates are statistically indistinguishable from the best (SSE within 1 + 6/n); the best curved fit improves SSE over the best straight-line-in-adstock fit by a median 26% at med depth and only 2.5% at x10. Weekly arm: wider sets (23 candidates at med).

### 4. Does the daily-vs-weekly gap shrink with shallow saturation? No (E3 not supported)
Paired mean |bias| weekly minus daily with X: shape 1.0: 7.4, 3.6, 4.1, 6.6, 6.8 points (SE 0.5-0.7); shape 2.2: 13.2, 9.9, 11.2, 9.6, 10.0 (SE 0.8-1.3). Daily is better at every depth, including the almost linear x10. So curvature (the Jensen term) is not the only source of aggregation error. A second source is carryover timing: exploratory check with a linear response, 100 draws per cell: a weekly adstock of weekly totals cannot reproduce 0.6% (delta 0.15), 7% (0.50) and 14-16% (0.85) of the variance of the weekly sum of daily adstock. This is a hypothesis supported by a small calculation, not a tested theorem.
Signed bias with X: shape 1.0 is negative (daily -4.7 to -11.8, weekly -0.6 to -14.6); shape 2.2 positive (daily +6.7 to +15.2, weekly +17.7 to +25.0).

### 5. Continuous fit is not a safe fix
The unconstrained continuous fit sometimes lands on a nearly constant transformed series. Weekly mean |bias| reaches 92 (x10) to 25,378% (mild) because of such outliers; medians are 17.5-31.6%. Report medians for C. Daily C: median 11-16%, mean 19-39%. Bounds on gamma (as in Robyn) are needed.

### Caveats
- At x1, x3 and x10 the extension multipliers (1, 3, 10 times the maximum) coincide with the true gamma in the matching decay candidate, so X is flattered in exactly these cells; C does not have this advantage, which is why C is shown.
- Single channel, truth daily, 156 weeks, geometric adstock and Hill only.

## Part 2. Targeted weekday-seasonality test S2b (57,600 markets; 576 cells x 100 reps)
Truth daily; baseline and media response multiplied by (1 + s p_d); weekly KPI. Profiles A (S2 profile) and B (weekend spike). Alignments: neutral, weekday-only spend, weekend-heavy, peak, anti-peak. s = 0.3, 0.6, 0.9. Arms: weekly, dailyT (paper), dailyT_dow (two regressors, profile known), oracle.

### What this changes about the earlier S2 conclusion
The earlier statement that weekday patterns leave the daily arm unaffected was too strong. Precisely:
1. A weekday pattern in the BASELINE cancels exactly in a weekly KPI (analytic argument in DESIGN_DOW2.md); control cells reproduce the paper (weekly 25.3-25.6, dailyT 13.9-14.2).
2. A weekday pattern in the MEDIA RESPONSE does not cancel. The extra term is 2-22% of the weekly media signal (profile A: 2-8%; profile B: 4-22%).
3. The paper's daily arm (no weekday term) then loses ground: pooled over s > 0, mean |bias|: profile A weekly 23.9, dailyT 20.6, dailyT_dow 12.1; profile B weekly 22.3, dailyT 29.1, dailyT_dow 13.3. Across 576 cells dailyT beats weekly in 346, ties in 83, loses in 147. Under the strong profile B at s >= 0.6 it loses in many cells (for example s = 0.9: weekly better in 7-13 of 18 cells depending on alignment).
4. The worst case is weekday-only spend: dailyT mean |bias| 39% (profile A) and 47% (profile B) versus weekly 20%; in smooth, S-shaped cells the paired gap reaches 200-430 points. Spend that never runs on high-response days while carryover lands on them is where an unmodelled weekday response hurts most.
5. A weekday-aware daily transform fixes it: dailyT_dow mean |bias| 9.5-15.9 in every profile and alignment group, beats weekly in 476 of 576 cells, ties 46, loses 54. LIMIT: the profile was taken as known. The paper's setting (weekly KPI only) does not reveal it; it needs a daily KPI or a prior. Estimating it from a weekly KPI was not tested.
6. Weekly aggregation is robust to all of this (mean |bias| 19-28 in every alignment group): it pays for coarseness, not for weekday patterns.
