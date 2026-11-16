# Shallow-saturation recovery study (Reviewer 1, point 3). Design fixed BEFORE running (24 Oct 2026)

Question: when saturation is shallow (the curve is almost linear over the observed spend range), can an MMM recover (a) total contribution, (b) the parameters (decay, half-saturation gamma, shape), (c) the response curve itself (what happens if spend is moved), (d) marginal ROI? And does the daily-vs-weekly gap survive? A reviewer's concern: total contribution can look fine while the curve is not identified.

## Data-generating process
Paper core DGP (lib.simA_core logic): 156 weeks, daily spend (bursty / smooth / real), geometric adstock (delta 0.15, 0.50, 0.85), Hill response, weekly KPI = base + scaled sum of daily responses + noise. Media signal scaled to the baseline's standard deviation. Signal R2 in {0.85, 0.5}.
Saturation depth (true gamma), the factor of interest:
- med: gamma = P50 of adstock (paper's reference, clearly curved)
- mild: gamma = P90 of adstock (paper's mild)
- x1: gamma = 1 x max adstock (curve only just reaching half-saturation at the peak day)
- x3: gamma = 3 x max adstock (shallow)
- x10: gamma = 10 x max adstock (almost linear for h = 1; power-law-like for h = 2.2)
Shape h in {1.0, 2.2}. Truth is DAILY in every cell here (weekly-true is covered by earlier studies).
Cells: 5 depths x 2 shapes x 3 deltas x 3 patterns x 2 R2 = 180; 60 replications per cell (10,800 markets), seeds from the cell key, new prefix "REC".

## Estimators (applied at both frequencies: weekly-transform W and daily-transform D)
- G: the paper's grid (12 decays x gamma at percentiles 5..95 of adstock x h in {1, 1.6, 2.2}); best SSE; cannot represent gamma above the observed maximum.
- X: extended grid = G plus gamma at {1, 3, 10, 30} x max adstock.
- C: continuous variable-projection fit of (delta, ln gamma, h) by Nelder-Mead from the best X candidate and from two other starts (bounds delta 0.01-0.99, gamma 0.05-100 x max adstock, h 0.5-4); coefficient non-negative.
All use the same controls (intercept, trend, annual sine and cosine) partialled out, as the paper.

## Outputs per market and arm
1. Total contribution bias %.
2. Curve recovery: spend scaled by s in {0.5, 1.5, 2, 3} with the fitted coefficient and parameters held fixed, compared with the true contribution at the same s: relative error 100 (C_hat(s) - C(s)) / C(1). s = 2 and 3 are extrapolation.
3. Marginal ROI bias %: finite difference of total contribution for s from 0.9 to 1.1, estimated vs true.
4. Parameter recovery (D arm only, because W has no daily decay): estimated minus true delta; ln(gamma_hat / gamma_true); h_hat minus h_true.
5. Identification width (X grid, each frequency): number of candidates whose SSE is within (1 + 6/n) of the minimum (a likelihood-ratio style indistinguishable set, 2 parameters, 95%), and the min..max of the implied C_hat(2)/C(2) over that set.
6. Linear gain: (SSE of best linear-in-adstock fit - SSE of best X) / SSE of the linear fit: how much the data can tell curvature from a straight line.

## Pre-stated expectations (reported either way)
E1 With the paper's grid G, shallow-truth cells show grid-boundary bias; X and C reduce it.
E2 Total bias can be small in shallow cells while extrapolation error at s = 2 and 3 and mROI error are large. Define a MASKED failure as |total bias| < 10% and |error at s = 2| > 25%; report its share by depth, arm, estimator.
E3 The daily-vs-weekly gap shrinks as saturation gets shallower (the Jensen term vanishes as curvature vanishes); report the paired difference with 2-SE rule.
E4 Parameter recovery of gamma and h gets worse as truth gets shallower, and the indistinguishable-set width grows.
Nothing here is tuned after seeing results. If E1-E4 fail, the failure is reported.

## Note added after the smoke test and before the full run (no full-run results seen)
Smoke test showed the continuous fit C could converge to a degenerate column (gamma near its lower bound, so the transformed series is almost constant and collinear with the intercept), giving a huge coefficient (one weekly case at +3,797%). A numerical guard was added to C only: a candidate is rejected (treated as no media effect) if the part of its transformed series not explained by the controls is below 0.1% of its own variance. No other change.
