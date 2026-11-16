# Reviewer-response simulations: results (run 10 Oct 2026)

Design was written first (DESIGN.md) and not changed after seeing results. About 82,900 new simulated markets.
Engine check: the fast re-implementation reproduces the published core cells exactly (max difference 1.5e-12 over 320 market-arm pairs, all four patterns), and the new day-of-week generator with weekday effects switched off matches the published weekly/daily means within sampling noise.
Metric: contribution bias %, as in the paper. "Better" = lower mean |bias| by more than 2 Monte-Carlo SE within a cell.

## Summary table

| Reviewer point | New result | Helps or hurts the paper |
|---|---|---|
| R1 1A time-varying effect | Mixed. Linear truth, 90 cells: daily better 37, weekly better 35, tie 18 (mean |bias| weekly 21.6, daily 20.4). Reviewer mechanism (day-level variation + spend follows effectiveness, kappa=1): weekly better in 9 of 9 cells with the paper's grid (11.9 vs 17.1). With near-linear candidates added: weekly 4, tie 3, daily 2. Saturating truth + time variation: daily better 16, tie 15, weekly better 5 of 36. | Partly hurts. Genuine boundary condition. |
| R1 1B day-of-week | Paper's daily arm (weekly KPI) is unaffected by weekday patterns: daily better in 297 of 360 cells, weekly better in 42, tie 21. Daily-KPI regression without weekday dummies fails badly (mean |bias| 25-59% at moderate, 36-119% at strong weekday effect). With weekday dummies it is best of all arms (5-16%). | Helps the paper's design; confirms the reviewer for daily-KPI models. |
| R1 2 Robyn comparison | Robyn-style search (emulation, not Robyn): daily vs weekly mean |bias| 22.8 vs 31.5 (in-sample objective), 35.9 vs 42.4 (validation objective). Search procedure adds 7-18 points at weekly level. | Helps on aggregation; concedes the estimation-procedure point. |
| R3 sub-daily truth | Truth at 6-hour and hourly: weekly 23.7-25.1, daily 12.6-13.4, native fine resolution 11.4-13.7. Daily better than weekly in 93 of 108 cells, worse in 4. Native vs daily: native better 31, daily better 12, tie 65. | Helps: daily is not an arbitrary unit; most of the gain comes from leaving weekly. Does not support "the bias keeps growing at finer levels". |
| R3 alternative DGPs | Weekly-true world: weekly better in 43 of 54 cells (16.5 vs 27.4). Linear: tie on paper grid, daily better with near-linear candidates (10.3 vs 17.3). Log response: daily better 21 of 27. Two-component adstock: daily better (13.9 vs 21.9). Endogenous wear-out: daily better 9, weekly 2, tie 7. Power 0.5 response: both about 30% off, no daily gain. | Mixed. Result is conditional on the truth being daily (or finer). |

## Key caveats
- S3 is a Robyn-style emulation (Nevergrad TwoPointsDE, Hill with Robyn-style gamma, ridge, trend+season), not the Robyn package.
- S1 and S2 parameter choices (sigma_e 0.5, kappa 0/0.5/1, weekday profile, x3 concentration) are mine; results show what happens at those values.
- In time-varying cells with budget correlation, even the oracle static model is 25-63% off, so bias there is mostly a static-model problem, not a frequency problem.
- The question of whether real advertising follows a daily process cannot be settled by simulation.
- Not done: real Robyn package run, parameter-recovery test for shallow saturation (R1 point 3), reading Dew, Padilla and Shchetkina (2026).
