# The Frequency Trap: ALL follow-up results in ONE file (updated 4 Nov 2026, controlled real-Robyn experiment added)

How this file is organised. PART 1 is a short update you can paste to another AI. PART 2 holds the new studies (decision-level, sample length, multichannel shallow saturation, real Robyn single-channel, and NEW the controlled real-Robyn experiment in 2.5). PART 3 holds the earlier follow-ups (weekday seasonality, shallow-saturation recovery, Robyn-type engine). PART 4 lists what is still not done and what I would do next. Every number comes from a saved result file; nothing was tuned after looking, and each study had a design file written before the full run (DESIGN_DOW2.md, DESIGN_RECOVERY.md, DESIGN_ROBYN.md, DESIGN_ROBYN_REAL.md, DESIGN_DECISION.md, DESIGN_ROBYN_CONTROLLED.md).

How to read the numbers. "Bias" is the error of the estimated total media contribution in % of the true contribution; "|bias|" is its absolute value averaged over simulated markets. W is the weekly transform (adstock and saturation on weekly totals), D is the daily transform (on daily spend, summed to weeks; a weekly KPI is all that is observed), S1 selects the frequency inside the fit, OF uses the true frequency, OT uses the true transforms (only coefficients estimated; the ceiling). A difference counts as real only if it exceeds 2 standard errors, otherwise it is a tie.

---------------------------------------------------------------------------------------------------

# PART 1. Short update to paste to another AI

Since the earlier briefing, these further studies were run (designs written before the runs; all cells reported; failures reported as failures). Please factor them in and challenge them.

1. Weekday seasonality (57,600 simulated markets). A weekday pattern in the baseline cancels exactly in weekly totals. A weekday pattern in the media RESPONSE does not cancel. The paper's daily transform (no weekday term) beat weekly in 346 of 576 cells, tied in 83 and lost in 147; with a weekend-spike profile and weekday-only spend it had 39-47% mean absolute contribution error versus about 20% for weekly. A weekday-aware daily transform (profile assumed KNOWN) had 9.5-15.9% and beat weekly in 476 of 576 cells. The weekday profile cannot be seen in a weekly KPI.
2. Shallow saturation, single channel (10,800 markets). The paper's grid cannot represent a nearly linear curve (daily error 41-42% versus 13% with an extended grid). Total contribution can look right while the curve is not identified: among markets with total error under 10%, the share with an error above 25% at twice the spend rises from 0.5% (clearly curved) to about 31% (shallow).
3. Robyn-type engine (my own equivalent of Robyn's loop, 400 multichannel markets). The search adds 11-20 points of error; the daily advantage is small with a single-objective search and absent or reversed when the DECOMP.RSSD objective is in the selection (pooled weekly minus daily: grid +3.5, SE 1.4; single objective +3.0, SE 2.3; NRMSE rule -2.0, SE 1.7; RSSD rule -5.3, SE 1.8).
4. Decision-level study (3,000 multichannel markets, 10 scenarios, 156 weeks). Total contribution error stays about 23% for W, D and S1 (pooled |bias| 23.7, 23.4, 22.9; 6.1 with true transforms), but budget DECISIONS are much less affected. Following the estimated optimum with budget moves allowed between half and double of current spend gives up 1.5% (W), 1.3% (D), 1.25% (S1) of true media contribution, against an attainable gain of 8-21% (true-transform ceiling 0.29%). For moves of -20% to +25% the loss is 0.45%, 0.38%, 0.37%. The estimated optimum captures a median of 98-99% of the attainable gain. Daily is better than weekly on decision loss in 4 of 10 scenarios and never worse (pooled gap 0.21 points, SE 0.05). The exception is scenario M7 (a time-varying effect that moves with spend): loss 4.4%, capture only 63-70%, and in about 30% of markets the recommended move is worse than leaving the budget alone, for every frequency choice. Marginal ROI at observed spend: median relative error 9-25% for D (98% in M7; 5-12% with true transforms); the best channel is identified in 85% of markets (94% with true transforms), the full ordering in 67% (85%).
5. Sample length (78, 156, 260 weeks; 1,500 markets each). The weekly-versus-daily picture does not depend on 156 weeks. Single channel: daily better at every length (gap 12.7, 7.6, 10.6 points). Multichannel: mostly ties. Weekly is better in M7 at 78 and 260 weeks. Bias of the estimated arms hardly falls with more weeks (pooled over M1, M2, M3, M7: 25-26% at 78 weeks, about 20% at 156, 17-18% at 260), while the true-transform ceiling falls from 6.2% to 3.2%. So most of the error is structural, not sampling noise.
6. Multichannel shallow saturation (600 markets). With nearly linear curves the paper's grid gives 34-36% total error; an extended grid (which contains the truth, so it is flattered) gives 19-23%. Among good-looking markets (error under 10%) the share with an error above 25% at twice the spend is 48% (D) and 63% (W) with the paper's grid, and 8% (DX) and 23% (WX) with the extended grid. On the control (curved) markets the extended grid is WORSE for extrapolation (17.6% vs 11.4%). Decisions are not hurt much: loss 3.3% (D) and 4.4% (W) with the paper's grid, 1.1% with the extended grid, because with near-linear curves the best move is simply to push towards the best channel.
7. Real Robyn 3.12.1 (Meta's code, one stand-in for a helper package), 12 single-channel markets with daily truth, 1,000 iterations and one trial, weekly data versus daily data (daily KPI and Robyn's weekday term, so the daily arm also has 7x the observations). Mean |bias|: weekly 37.3%, daily 20.2%; paired gap 17.1 (SE 5.7); daily better in 11 of 12 markets; weekly Robyn underestimates on average (-37%), daily is close to unbiased on average (-0.3%) but with a wide spread (+52% to -69%). Same-seed repeats do NOT reproduce each other (within-cell SD of the bias about 15 points).
8. NEW, and it cuts against the paper: controlled real-Robyn experiment (DESIGN_ROBYN_CONTROLLED.md, fixed before the run). 16 simulated three-channel markets (8 independent, 4 correlated, 4 with one weekly-truth channel), 156 weeks, signal R2 0.85, no weekday effect, Robyn 3.12.1 at its recommended 2,000 iterations x 5 trials, 40 runs on a laptop. Arm A: standard weekly Robyn. Arm B: the same weekly KPI and weekly model, but each channel's adstock and Hill saturation are computed on DAILY spend and then summed to weeks (a patched Robyn). A and B are two complete frequency-specific transformation workflows, not a pure change of the aggregation point: theta is a per-week decay in A and a per-day decay in B with the same numeric bounds, and Robyn's saturation inflexion is gamma times the weekly maximum in A and the daily maximum in B. Arm C: standard daily Robyn on a daily KPI (confounded with 7x the observations; markets 0-7 only). Result on the pre-declared primary rule (lowest Robyn error score among Pareto-1 models): mean |total bias| A 43.2%, B 50.5%, C 45.7%; ALL 16 markets for A and B and all 8 for C are underestimates (signed bias equals minus |bias|). Paired A minus B = -7.3 points (SE 4.6): the daily-transform arm was worse in 11 of 16 markets, so the data do not show a daily-transform advantage and rule out one larger than about 2 points. Under the secondary rule (lowest validation NRMSE) A 41.3, B 47.0, C 39.1; A minus B = -5.7 (SE 2.7), B better in 1 of 16 markets. The aggregation effect seen in my grid and engine studies is NOT visible in real Robyn with this workflow contrast: Robyn's own errors (about 40-50% underestimation) are much larger. The earlier single-channel result (daily Robyn about unbiased) does not carry over to three channels (daily Robyn -46%).

Net effect on my claims: aggregation bias is real but conditional (independent or sub-daily channels, curved response, no unmodelled weekday response). It is large for the reported contribution and for marginal-ROI levels, but small for budget reallocation decisions except when the effect varies over time with spend. With real Robyn, evidence is now mixed to negative for the paper's practical claim: single-channel weekly-versus-daily KPI favoured daily, but the controlled three-channel experiment that isolates the transformation frequency shows no benefit from daily transforms, because the package's own estimation error (strong underestimation) dominates. The honest framing is that the paper identifies a mechanism in the model class it studies (grid-search regression with the frequency of the transform as the only change), and that it does not show that moving Robyn's transforms to daily frequency repairs Robyn.

Questions for you: (1) Is it defensible to say that contribution bias matters for reporting and ROI levels but much less for reallocation, and does that weaken or strengthen the paper for JAR? (2) Given the controlled Robyn result (no daily-transform benefit, 40-50% underestimation in every arm), how should the Robyn reviewer point be answered: concede that the estimation procedure dominates, and keep the aggregation claim for the model class studied? (3) How should the weekday finding be handled given that the profile is not observable from a weekly KPI? (4) What would a reviewer still insist on?

---------------------------------------------------------------------------------------------------

# PART 2. New studies

## 2.1 Decision-level study: does the bias change what a manager would do?
Files: DESIGN_DECISION.md, dec_run.py, an_dec.py, results/DEC_main_156.csv, results/DEC_main_156_analysis.txt. 3,000 markets (10 scenarios M1-M10 from DESIGN_MULTI.md, 300 each, fresh seeds, 156 weeks). Before the run the new code reproduced the earlier multichannel engine exactly (21 markets, 5 arms, 0 mismatches) and the truth function matched the simulated truth to 1e-12. The budget optimiser was checked against 3,000 random feasible allocations on 64 cases and was never beaten.

How it works. Each fitted model gives a response curve per channel. Changing a channel's budget means multiplying its whole daily spend series by a factor s; the same factor is applied to the TRUE response. The total budget stays fixed. For every arm I find the allocation that maximises the fitted model, then score it with the truth. LOSS is the percentage of true media contribution given up compared with the true optimum. CAPTURE is the share of the attainable gain obtained. HARM is the share of markets where the recommended move is worse than leaving the budget alone. Primary bounds: each channel between 0.5x and 2x its current spend; secondary bounds: 0.8x to 1.25x.

Mean |total bias| %, by scenario:

| scen | W | D | S1 | OF | OT |
|---|---|---|---|---|---|
| M1 | 23.9 | 20.9 | 21.4 | 20.9 | 4.3 |
| M2 | 16.2 | 16.9 | 16.0 | 16.9 | 4.1 |
| M3 | 22.9 | 23.0 | 19.9 | 19.0 | 4.5 |
| M4 | 20.4 | 20.6 | 19.9 | 19.8 | 5.3 |
| M5 | 29.6 | 28.5 | 29.6 | 28.5 | 14.3 |
| M6 | 27.5 | 21.5 | 21.3 | 21.5 | 4.6 |
| M7 | 18.2 | 20.8 | 21.0 | 20.8 | 3.8 |
| M8 | 28.5 | 31.4 | 30.8 | 29.0 | 9.6 |
| M9 | 21.2 | 22.1 | 19.8 | 20.1 | 5.8 |
| M10 | 28.7 | 27.9 | 28.9 | 27.9 | 4.7 |
| pooled | 23.7 | 23.4 | 22.9 | 22.4 | 6.1 |

Paired weekly minus daily on |total bias|: daily better only in M6 (+6.0, SE 1.5); all other scenarios are ties (M1 +3.1, SE 1.6; M7 -2.6, SE 1.7).

Decision LOSS, primary bounds (% of true media contribution given up; lower is better):

| scen | W | D | S1 | OF | OT | attainable gain G* |
|---|---|---|---|---|---|---|
| M1 | 0.67 | 0.30 | 0.34 | 0.30 | 0.11 | 21.4 |
| M2 | 1.14 | 0.67 | 0.65 | 0.67 | 0.17 | 10.3 |
| M3 | 0.77 | 0.90 | 0.57 | 0.49 | 0.14 | 17.1 |
| M4 | 2.01 | 1.60 | 1.48 | 1.19 | 0.36 | 20.5 |
| M5 | 2.26 | 1.62 | 1.80 | 1.62 | 0.72 | 9.6 |
| M6 | 0.63 | 0.35 | 0.44 | 0.35 | 0.07 | 20.8 |
| M7 | 4.38 | 4.45 | 4.33 | 4.45 | 0.48 | 7.9 |
| M8 | 1.84 | 1.61 | 1.50 | 1.29 | 0.43 | 17.7 |
| M9 | 1.14 | 1.23 | 0.97 | 0.78 | 0.36 | 20.2 |
| M10 | 0.40 | 0.46 | 0.44 | 0.46 | 0.07 | 21.2 |
| pooled | 1.52 | 1.32 | 1.25 | 1.16 | 0.29 | |

Secondary bounds (0.8x to 1.25x), pooled loss: W 0.45, D 0.38, S1 0.37, OF 0.33, OT 0.10 (attainable gain 3.5-8.8% by scenario).

Daily versus weekly on decision loss (paired, 2-SE rule): daily has the lower loss in M1, M2, M5 and M6 under both bound sets; all other scenarios are ties; weekly is never better. Pooled gap W minus D: 0.21 points (SE 0.05) primary, 0.07 (SE 0.02) secondary. S1 has a lower loss than W in M1-M6 (ties in the rest) and a lower loss than D only in M3 (D beats S1 in M6).

Capture and harm (non-flat markets; flat markets with attainable gain under 1% are 5.0% of primary and 7.1% of secondary): median share of attainable gain captured, primary bounds, pooled W 0.982, D 0.988, S1 0.989, OF 0.990, OT 0.999. Harm share, primary, pooled: W 6.9%, D 5.9%, S1 5.7%, OF 5.4%, OT 0.9%. Scenario M7 stands out: capture 0.63 (W) and 0.70 (D, S1, OF) and harm about 30% for every estimated arm (OT 1.9%); M5 harm 9-13%.

Marginal ROI at observed spend, median relative error (D arm by scenario): M1 9%, M2 14%, M3 17%, M4 23%, M5 21%, M6 11%, M7 98%, M8 25%, M9 21%, M10 22% (OT 5-12%). Best channel identified, pooled: W 83.8%, D 85.3%, S1 86.4%, OF 87.0%, OT 94.4%. Full channel ordering right, pooled: W 64.0%, D 67.2%, S1 67.7%, OF 69.3%, OT 85.2%.

What this means. (1) The 20-25% error in total contribution does not translate into poor budget moves in most scenarios: the fitted models still point in the right direction, and even large moves give up only 1-2% of media contribution. (2) The fitted models are clearly worse than the ceiling in decisions (0.3% with true transforms), and daily is modestly better than weekly, never worse. (3) The place where decisions go wrong is not aggregation: it is an effect that varies over time together with spend (M7), where every arm gives about 4.4% loss and a one-in-three chance of a harmful move. (4) The honest paper message becomes: aggregation matters for how much is credited to each channel and for marginal ROI levels (9-25% median error, best channel found 85% of the time), much less for the direction of a budget shift. Limits: simulated markets in which the truth is inside the model family; reallocation limited to level changes within bounds (no timing changes); three or five channels; no holidays or paydays; flat markets treated separately.

## 2.2 Sample length (78, 156 and 260 weeks)
Files: dec_run.py (mode len), results/DEC_len_78.csv, DEC_len_156.csv, DEC_len_260.csv, results/DEC_length_summary.csv. Scenarios V (single channel), M1, M2, M3, M7, 300 markets each (the 156-week M1, M2, M3, M7 markets are identical to the main run; checked: maximum difference 0.0). Mean |total bias| % (W / D / S1 / OF / OT) and paired weekly minus daily (W-D, positive = daily better):

| scen | weeks | W | D | S1 | OF | OT | W-D (SE) |
|---|---|---|---|---|---|---|---|
| V | 78 | 29.1 | 16.4 | 16.2 | 16.4 | 4.0 | +12.7 (2.0), daily |
| V | 156 | 23.1 | 15.4 | 15.4 | 15.4 | 2.6 | +7.6 (1.7), daily |
| V | 260 | 24.2 | 13.6 | 13.6 | 13.6 | 2.2 | +10.6 (1.8), daily |
| M1 | 78 | 28.1 | 23.4 | 23.8 | 23.4 | 6.0 | +4.7 (1.7), daily |
| M1 | 156 | 23.9 | 20.9 | 21.4 | 20.9 | 4.3 | +3.1 (1.6), tie |
| M1 | 260 | 23.3 | 20.0 | 19.6 | 20.0 | 3.3 | +3.3 (1.7), tie |
| M2 | 78 | 23.0 | 22.9 | 23.9 | 22.9 | 6.2 | +0.1 (1.8), tie |
| M2 | 156 | 16.2 | 16.9 | 16.0 | 16.9 | 4.1 | -0.7 (1.3), tie |
| M2 | 260 | 13.5 | 13.3 | 13.0 | 13.3 | 3.1 | +0.2 (0.7), tie |
| M3 | 78 | 24.7 | 23.0 | 22.3 | 21.6 | 6.8 | +1.7 (1.4), tie |
| M3 | 156 | 22.9 | 23.0 | 19.9 | 19.0 | 4.5 | -0.1 (1.8), tie |
| M3 | 260 | 21.1 | 18.9 | 16.3 | 16.2 | 3.3 | +2.2 (1.5), tie |
| M7 | 78 | 24.1 | 36.0 | 34.6 | 36.0 | 5.8 | -11.9 (3.6), weekly |
| M7 | 156 | 18.2 | 20.8 | 21.1 | 20.8 | 3.8 | -2.6 (1.7), tie |
| M7 | 260 | 13.9 | 16.9 | 16.9 | 16.9 | 3.0 | -3.0 (1.0), weekly |

Decision loss, primary bounds, pooled over M1, M2, M3, M7 (W / D / S1 / OF / OT): 78 weeks 2.28 / 1.86 / 1.89 / 1.73 / 0.45; 156 weeks 1.74 / 1.58 / 1.47 / 1.48 / 0.22; 260 weeks 1.40 / 1.33 / 1.21 / 1.20 / 0.15. Daily has the lower decision loss in M1 and M2 at all three lengths; M3 and M7 are ties at all lengths.

Reading. The single-channel result (daily clearly better) holds at every length. The multichannel result (mostly ties, weekly better in M7) also holds at every length. With more data the estimated arms improve only a little (pooled |bias| 26% to 17% for D), whereas the true-transform ceiling falls from 6.2% to 3.2%: the gap between estimated and true transforms is mainly a model-identification problem, not a lack of weeks. M7 at 78 weeks is the weakest case for daily (36% versus 24%).

## 2.3 Multichannel shallow saturation (optional item, now done)
Files: DESIGN_DECISION.md Part 3, dec_shallow.py, an_dsh.py, results/DSH_main.csv, results/DSH_main_analysis.txt. 600 markets: 300 SHALLOW (three independent daily channels, each with half-saturation point at 1, 3 or 10 times the channel's maximum adstocked spend) and 300 CONTROL (same code, curved depths mild/med/deep). Arms: W and D on the paper's grid, WX and DX on an extended grid that includes gamma at 1, 3, 10 and 30 times the maximum (this contains the truth in the shallow cells, so it is flattered), and OT.

| | W | D | WX | DX | OT |
|---|---|---|---|---|---|
| SHALLOW: mean abs total bias % | 36.4 | 34.1 | 22.9 | 18.8 | 4.2 |
| SHALLOW: mean abs error of gain from doubling all spend % | 34.6 | 31.3 | 19.6 | 13.3 | 4.3 |
| SHALLOW: share with total error under 10% | 0.16 | 0.16 | 0.39 | 0.47 | 0.93 |
| SHALLOW: of those, share with doubling-spend error above 25% | 0.63 | 0.48 | 0.23 | 0.08 | 0.00 |
| SHALLOW: decision loss, primary bounds % | 4.38 | 3.30 | 1.32 | 1.07 | 0.22 |
| SHALLOW: decision loss, secondary bounds % | 0.24 | 0.27 | 0.14 | 0.07 | 0.02 |
| SHALLOW: marginal-ROI median rel. error | 0.12 | 0.13 | 0.10 | 0.07 | 0.05 |
| CONTROL: mean abs total bias % | 26.8 | 20.8 | 27.5 | 21.3 | 4.3 |
| CONTROL: mean abs doubling-spend error % | 12.6 | 11.4 | 23.2 | 17.6 | 4.6 |
| CONTROL: decision loss, primary % | 0.67 | 0.36 | 0.78 | 0.53 | 0.05 |

Attainable gain from reallocation is very large in the shallow markets (mean 94% of media contribution with the 0.5x-2x bounds, 23% with the narrow bounds), because with nearly linear curves the best move is to push spend towards the channel with the best return; the median capture is 1.0 for every arm and harm is about 0%. Paired comparisons: daily versus weekly on total bias with the paper's grid +2.3 (SE 2.3, tie), with the extended grid +4.2 (SE 1.5, daily better); daily with the paper's grid minus extended grid +15.4 (SE 2.0), so the grid choice matters more than the frequency; on decision loss W minus D +1.1 (SE 0.4). On the CONTROL markets the extended grid gives no help and adds extrapolation error (17.6% versus 11.4% for D).
Reading. The single-channel finding carries over to several channels: with shallow curves the total can look fine while the response to a doubling of spend is wrong (63% of good-looking weekly fits and 48% of good-looking daily fits on the paper's grid). Marginal ROI at observed spend and the direction of a budget move are still found well. A wider grid helps in shallow markets but is not free: it hurts when the curve is not shallow, so it should be a sensitivity analysis, not a default. Caveat: the extended grid knows where the truth is.

## 2.4 Real Robyn package, 12 single-channel markets
Files: DESIGN_ROBYN_REAL.md, run_robyn_real.R, run_robyn_all.sh, export_robyn_markets.py, an_rbreal.py, results/RBREAL_1000_full.csv (main run), results/RBREAL_1000.csv (first attempt, 7 runs), results/RBREAL_analysis.txt.
Setup. Robyn 3.12.1 R code from Meta's GitHub source, R 4.3.3, glmnet 4.1-8, prophet 1.0, Nevergrad TwoPointsDE; only the helper package lares is replaced by a stand-in (printing and clustering; clustering off). Markets: single channel, daily truth (geometric adstock, Hill), signal R2 0.85, 156 weeks, decay 0.15/0.50/0.85, shape 1.0/2.2, bursty or real spend, 12 markets. Robyn is run twice per market: on the weekly data (weekly KPI, Prophet trend and season) and on the daily data (daily KPI, Prophet trend, season and weekday). Held constant: market, hyperparameter bounds, time-series validation, seed argument, 1,000 iterations, 1 trial, search algorithm, ridge by glmnet, Pareto step. NOT held constant: the daily run has 7x the observations and a weekday term, and the meaning of theta differs by frequency. Estimate: contribution of the model with the lowest validation NRMSE among Pareto-1 models, scored against the true total.

Results (bias % of true contribution; main run):

| market | decay | shape | spend | weekly Robyn | daily Robyn |
|---|---|---|---|---|---|
| 0 | 0.15 | 1.0 | bursty | -49.2 | -24.8 |
| 4 | 0.15 | 1.0 | real | -35.3 | -2.5 |
| 6 | 0.15 | 2.2 | bursty | -37.6 | +24.8 |
| 10 | 0.15 | 2.2 | real | -40.0 | +1.6 |
| 12 | 0.50 | 1.0 | bursty | -35.6 | +4.8 |
| 16 | 0.50 | 1.0 | real | -19.1 | +11.9 |
| 18 | 0.50 | 2.2 | bursty | -50.5 | -17.5 |
| 22 | 0.50 | 2.2 | real | -17.3 | +14.3 |
| 24 | 0.85 | 1.0 | bursty | -86.3 | -69.2 |
| 28 | 0.85 | 1.0 | real | -28.9 | +9.4 |
| 30 | 0.85 | 2.2 | bursty | -31.2 | -9.0 |
| 34 | 0.85 | 2.2 | real | -16.5 | +52.3 |

Mean |bias| weekly 37.3%, daily 20.2%; paired gap 17.1 points (SE 5.7); daily better in 11 of 12 markets. Mean signed bias: weekly -37.3%, daily -0.3%. By decay: 0.15 weekly 40.5 / daily 13.4; 0.50 weekly 30.6 / daily 12.1; 0.85 weekly 40.7 / daily 35.0 (the slow-decay bursty market 24 is badly wrong in both). By spend pattern: bursty weekly 48.4 / daily 25.0; real weekly 26.2 / daily 15.3.
Run-to-run noise. The first attempt (same code and settings; 7 runs) and the main run give seven repeated (market, frequency) cells. Same-seed repeats differ: for example market 0 weekly -25.1 versus -49.2, market 6 weekly +0.2 versus -37.6. The median within-cell SD of the bias is 15.4 points. So each single number above carries about +/-15 points of search noise; the 12-market averages (SE about 4-6 points) are more stable than any single market.
End-to-end check of my Robyn-type engine against the real package, same weekly markets (engine: weekly transform, single objective, 1,000 iterations, 5 repeat searches per market, trend and sine/cosine controls in place of Prophet): mean bias engine -22.5% versus -37.3% for real Robyn; the across-market correlation is only 0.34; the engine's own run-to-run SD is 13-68 points in most markets. Same direction in 10 of 12 markets, but not a replica: the engine is less biased and noisier. This is why every Robyn-type engine result in the paper must be labelled as an equivalent, not as Robyn.
Reading. In these single-channel markets, real Robyn on weekly data underestimates the true contribution by about 37% on average, while Robyn on daily data is close to unbiased on average but widely scattered (mean |bias| 20%). The comparison mixes frequency with the 7x larger sample and the weekday term, so it describes what a practitioner gets by choosing the daily KPI when one exists, and does not isolate transformation frequency by itself. Limits: 12 markets, one run each, 1,000 iterations and one trial (Robyn recommends 2,000 x 5), clustering off, lares stand-in, single channel only. The controlled three-channel experiment in 2.5 was run to remove these limits.

## 2.5 NEW: Controlled real-Robyn experiment, 16 three-channel markets (finished 4 Nov 2026)
Files: DESIGN_ROBYN_CONTROLLED.md (written before the run), export_robyn_mc.py (makes the markets), patched_transformation.R (Robyn with the daily-transform option), run_robyn_mc.R, run_everything.R, an_rxm.py (pre-declared analysis), results/RXM_laptop.csv (the 80 result rows = 40 runs x 2 selection rules), results/RXM_analysis_output.txt, robyn_mc/truth_mc.csv (true contributions).

Purpose. Reviewer 1 asked what happens with the real Robyn package. The 12-market run in 2.4 compared weekly Robyn with daily Robyn, which changes three things at once (transform frequency, number of observations, weekday term). This experiment keeps the KPI, the weekly model rows, the ridge, the validation split, the objectives, the search and the scoring identical, and changes only the frequency at which the media transformation is computed in arm B. It is still not a pure test of aggregation alone, because the parameters mean different things at the two frequencies (see Arms).

Setup. 16 simulated three-channel markets, each with a daily version and a weekly version of the SAME data (the weekly KPI is the exact sum of the seven daily values; daily noise has no weekday pattern). Types: 8 independent channels (market ids with id mod 4 = 0 or 1), 4 correlated channels (kappa 1), 4 mixed markets in which one channel has a WEEKLY true response and two are daily. Truth: geometric adstock and Hill; signal R2 0.85; 156 weeks. Hyperparameter bounds were the same in every arm (alpha 0.5-3, gamma 0.05-1, theta 0.01-0.95, train_size 0.5-0.9), time-series validation on, Robyn 3.12.1, 2,000 iterations x 5 trials (Robyn's recommended setting), 15 cores, seed 1, clustering off (so models are chosen by explicit rules).
Arms. A: standard weekly Robyn (weekly KPI, weekly transforms). B: patched Robyn; same weekly KPI and same weekly model, but each channel's adstock and saturation are computed on the DAILY spend series and summed to weeks inside Robyn's own transformation function (validated: with the patch switched off the output is identical, difference 0.0). C: standard daily Robyn on the daily KPI with Prophet trend, season and weekday (confounded with 7x observations and the weekday term). C was deliberately limited to markets 0-7 in the design file, before any run, to save compute (a C run takes about twice as long); no C run failed, and the results file has exactly 16 + 16 + 8 runs. Interpretation of A versus B: the two arms use the same numeric bounds (theta 0.01-0.95, gamma 0.05-1) but theta is a per-week decay in A and a per-day decay in B, and the saturation inflexion is gamma times the maximum of the adstocked series within the window, a weekly maximum in A and a daily maximum in B. A versus B therefore compares two complete frequency-specific workflows and must not be described as isolating aggregation alone.
Selection rules. PRIMARY: lowest Robyn error score among Pareto-front-1 models (Robyn's combined NRMSE and DECOMP.RSSD score). SECONDARY: lowest validation NRMSE among the same models. Estimate = Robyn's xDecompAgg summed over the three channels, scored against the true total contribution. Paired differences use the 2-SE rule.

Result 1 (primary rule, error score). Mean |total bias| %, by market type:

| type | A weekly | B daily-transform | C daily Robyn | markets (A, B / C) |
|---|---|---|---|---|
| independent | 49.1 | 53.2 | 57.2 | 8 / 4 |
| correlated | 34.2 | 39.8 | 43.2 | 4 / 2 |
| mixed (one weekly channel) | 40.4 | 55.7 | 25.1 | 4 / 2 |
| all | 43.2 | 50.5 | 45.7 | 16 / 8 |

Mean |channel-level bias| (average over the three channels): A 55.1, B 52.7, C 42.5. Every run is an underestimate: the signed bias equals minus the absolute bias for all arms (A range -2% to -88%, B -4% to -81%, C -16% to -74%). Median |bias|: A 48.5, B 63.3, C 49.0.
Paired A minus B (positive = B better): -7.26, SE 4.59, n = 16; B better in 5 of 16 markets. Rough 95% interval (2 SE) for the advantage of B: from -16.4 to +1.9 points, so the data rule out a daily-transform advantage larger than about 2 points. By type: independent -4.1 (SE 6.3), correlated -5.5 (SE 7.4), mixed -15.3 (SE 12.3; B better in 1 of 4). Paired A minus C (8 markets): -22.8 (SE 7.3), C better in only 2 of 8; B minus C: -12.0 (SE 8.5). On the 8 markets that have all three arms: A 22.9, B 33.7, C 45.7 (A is the best arm there). Paired A minus B on channel-level |bias|: +2.4 (SE 3.4), a tie.

Result 2 (secondary rule, validation NRMSE). Mean |total bias| %: A 41.3, B 47.0, C 39.1 (by type: independent A 41.1, B 49.2, C 35.2; correlated 37.4, 37.1, 39.8; mixed 45.3, 52.4, 46.2). Paired A minus B -5.7 (SE 2.7, B better in only 1 of 16; by 2-SE rule weekly is slightly better); A minus C -9.7 (SE 6.8); B minus C +0.9 (SE 5.7). Channel-level |bias|: A 48.7, B 52.6, C 37.6. All 16 markets are underestimates in A and B, all 8 in C.

Per-market bias % of the true total (primary rule):

| market | type | A | B | C |
|---|---|---|---|---|
| 0 | independent | -9.7 | -25.3 | -45.3 |
| 1 | independent | -30.6 | -64.0 | -55.7 |
| 2 | correlated | -19.6 | -4.0 | -52.7 |
| 3 | mixed | -16.5 | -21.8 | -16.3 |
| 4 | independent | -87.8 | -63.8 | -73.6 |
| 5 | independent | -4.6 | -11.2 | -54.3 |
| 6 | correlated | -12.7 | -27.7 | -33.7 |
| 7 | mixed | -1.5 | -51.7 | -34.0 |
| 8 | independent | -65.4 | -53.2 | |
| 9 | independent | -78.0 | -72.7 | |
| 10 | correlated | -46.1 | -62.9 | |
| 11 | mixed | -87.3 | -80.8 | |
| 12 | independent | -50.9 | -65.2 | |
| 13 | independent | -66.1 | -70.4 | |
| 14 | correlated | -58.6 | -64.5 | |
| 15 | mixed | -56.2 | -68.4 | |

Per-channel signed bias (mean over markets, primary rule): channel 1 A -25.3, B -29.4, C -24.3; channel 2 A +4.8, B -2.2, C -18.2; channel 3 A -32.4, B -40.5, C -20.8. In the four mixed markets the weekly-truth channel is wrongly estimated in both A and B (A +38, +69, -95, -70; B +31, -28, -93, -78), so neither the weekly nor the daily transform recovers a weekly-true channel in real Robyn.

Convergence and effort. Robyn reports two separate convergence checks for each run (the 5 trials together), one for NRMSE and one for DECOMP.RSSD; they are not interchangeable and neither describes the selected model alone. Outcomes of the 40 runs at 2,000 x 5: both converged 10; NRMSE converged but DECOMP.RSSD not 18; DECOMP.RSSD converged but NRMSE not 6; neither 6 (by arm A / B / C: both 2/5/3, NRMSE only 9/6/3, RSSD only 2/3/1, neither 3/2/1). So at least one check failed in 30 of 40 runs (75%), which is NOT the same as 75% of models failing. DECOMP.RSSD not converged in 12 of 16 A runs, 8 of 16 B runs, 4 of 8 C runs; NRMSE not converged in 5 of 16, 5 of 16 and 2 of 8. Because the primary selection rule uses the error score (which contains DECOMP.RSSD), the weaker criterion matters for the primary rule. A stability check is designed (Part 4). Median number of Pareto-1 models 15 (A), 19 (B), 17.5 (C); median time per run about 15 minutes for A and B and about 29 minutes for C on the laptop (one C run, market 5, shows 136,076 seconds because the laptop slept; the result is not affected). The two selection rules pick the same model (identical total estimate) in only 2 of 40 runs, so the choice of rule matters.

Reading. (1) The transformation-frequency effect I measured with grid-search regression is NOT visible in real Robyn: moving Robyn's transforms to daily frequency (arm B) did not reduce the bias; on the primary rule it was 7 points worse (1.6 SE, not significant), and it was worse in 11 of 16 markets. (2) What dominates is Robyn's own error: every one of the 40 runs under-estimates the total media contribution, on average by 40-50%, with a range from almost 0 to about 90%, in all three arms and in both selection rules. This is much larger than the 3-5 point aggregation effect seen with the paper's grid in these scenario types, and it is the same size as the Robyn-type engine finding that the search procedure adds 11-20 points. (3) The earlier single-channel finding (daily Robyn about unbiased, weekly Robyn -37%) does not carry over: with three channels daily Robyn is -46% (primary) and -39% (secondary), no better than weekly Robyn. (4) I cannot say WHY Robyn under-estimates here. Candidate causes are ridge shrinkage of the media coefficients, the Prophet trend and season absorbing part of the media signal, the error-score objective (which includes DECOMP.RSSD and favours effect shares equal to spend shares), and the hyperparameter bounds; none was isolated in this experiment, so this is a hypothesis, not a finding. Because estimate and truth are on the total contribution, the result says nothing about whether the RANK of channels or the direction of budget moves is right in Robyn (the decision-level study in 2.1 used my own estimators, not Robyn).

Limits (honest list). 16 markets, one run per market and arm and rule (the pre-planned noise-check repeats for markets 0, 2 and 3 were not run; the single-channel runs had a within-cell SD of about 15 points, so a single market-level difference means little, and the paired mean over 16 markets has a standard error of 4.6 points which already includes that noise). Arm C is confounded with 7x the observations and the weekday term. Simulated data in which the truth is inside the model family and no weekday effect exists. Robyn clustering switched off (the helper package lares is a stand-in) and a single seed. Both selection rules are reported, and they disagree by several points; neither is "Robyn's official choice" because Robyn's default needs clustering. The patched transform (arm B) was validated against the unpatched code but is my implementation, not Meta's.

What it means for the paper. The paper can say: (a) in the model class it studies (grid-search regression with the transform frequency as the only change) daily transforms reduce bias when the truth is daily, in single-channel markets, and the effect is smaller or tied in several-channel markets; (b) in real Robyn the frequency of the transformation workflow is not the main source of error: a controlled test at the recommended settings found no benefit from daily transforms and large underestimation in every arm; (c) it should therefore NOT claim that switching Robyn to a daily-transform workflow improves practitioners' estimates. This is a concession to Reviewer 1's Robyn point, and it is better made by us than discovered by the reviewer.

---------------------------------------------------------------------------------------------------

# PART 3. Earlier follow-up studies (finished earlier on 24 Oct 2026)

## A. Weekday seasonality (reviewer point 1B, second round)
Files: DESIGN_DOW2.md, s2b_dow_targeted.py, an_s2b.py, results/S2b_full.csv. 57,600 simulated markets (576 cells x 100 repetitions; truth daily; 156 weeks; signal R2 0.85).

### A1. What the first test (S2) showed, stated precisely
S2 used one weekday profile (Mon..Sun: -0.4, -0.4, -0.2, 0, 0.8, 1.0, -0.8), strengths 0.3 and 0.6, four spend alignments, weekly KPI, truth daily, 360 cells per comparison. The daily-transform arm beat weekly in 297 of 360 cells; it did not change with strength when the weekday pattern was only in the baseline, and rose by about 3-4 points at strength 0.6 when it also multiplied the media response. It did not test stronger strengths, weekday-only or weekend-heavy spend, a second profile, or a weekday-aware estimator. Saying "weekday patterns do not matter" overstated it.

### A2. Analytic argument
Let p_d be the weekday profile (sum over the week zero), s the strength, b_w a baseline constant within the week, r_d the daily media response.
1. Baseline: sum over d of (b_w/7)(1 + s p_d) = b_w. A weekday pattern in the baseline cancels exactly in any weekly total. If the baseline also trends within the week by g per day, the leftover is s g times sum of p_d (d - 4): about 0.19 s KPI units for the S2 profile and the paper's trend, below 1% of the baseline standard deviation.
2. Media response multiplied by the profile: sum over d of r_d (1 + s p_d) = sum of r_d + s sum of p_d r_d. The second term is 7 s times the within-week covariance of profile and response. It is zero in expectation only if spend is not aligned with the weekday pattern.
3. So weekday seasonality is not an aggregation effect. It creates a misspecification that affects the weekly arm and the paper's daily arm alike, because neither has a weekday term.
4. Because the weekly KPI is linear in b and b s, a weekday-aware daily transform is a two-regressor weekly regression: KPI_w = base + b sum r_d + (b s) sum p_d r_d. The weekly-transform arm has no equivalent, because it never sees the daily response.

### A3. Simulation S2b
Factors: strength s in {0.3, 0.6, 0.9}; profile A (the S2 profile) and profile B (weekdays -0.6, Saturday and Sunday +1.5); alignment in {neutral, weekday-only spend, weekend-heavy, peak (Fri/Sat), anti-peak}; decay {0.15, 0.50, 0.85}; shape {1.0, 2.2}; spend pattern {bursty, smooth, real}; media saturation depth medium. Control cells with s = 0. Arms: weekly, dailyT (paper's daily arm), dailyT_dow (daily with the two-regressor weekday term, profile taken as known), oracle (true response).

Control (s = 0): weekly 25.3 / 25.6, dailyT 13.9 / 14.2, dailyT_dow 14.1 / 14.3, oracle 2.7 (profile A / B). This reproduces the paper (weekly about 24-25, daily about 14-15).

Share of weekly media signal that is the weekday term, mean: profile A 2.2-8.2%; profile B 4.2-21.6% (grows with s).

Mean |bias| % by profile, strength, alignment (weekly / dailyT / dailyT_dow):
- Profile A, s 0.3: neutral 24.4 / 14.8 / 13.8; weekday-only 20.3 / 21.9 / 14.0; weekend-heavy 27.9 / 11.2 / 9.7; peak 23.4 / 12.2 / 9.7; anti-peak 23.7 / 14.4 / 12.5.
- Profile A, s 0.6: neutral 24.9 / 16.9 / 14.1; weekday-only 20.5 / 36.3 / 14.1; weekend-heavy 27.3 / 14.0 / 9.7; peak 23.8 / 16.1 / 10.0; anti-peak 23.3 / 17.4 / 12.6.
- Profile A, s 0.9: neutral 25.0 / 19.2 / 13.5; weekday-only 20.7 / 59.0 / 15.0; weekend-heavy 25.9 / 16.6 / 9.5; peak 22.7 / 19.7 / 10.0; anti-peak 24.4 / 19.8 / 13.2.
- Profile B, s 0.3: neutral 23.7 / 18.4 / 14.5; weekday-only 20.2 / 23.5 / 15.9; weekend-heavy 25.4 / 17.8 / 10.8; peak 22.4 / 17.5 / 11.0; anti-peak 23.3 / 19.9 / 12.9.
- Profile B, s 0.6: neutral 21.7 / 23.0 / 14.5; weekday-only 20.1 / 45.9 / 14.1; weekend-heavy 23.0 / 25.4 / 11.5; peak 21.5 / 23.2 / 11.9; anti-peak 23.6 / 30.0 / 12.9.
- Profile B, s 0.9: neutral 22.1 / 25.1 / 15.9; weekday-only 19.2 / 71.5 / 15.2; weekend-heavy 23.2 / 30.9 / 12.4; peak 20.8 / 29.0 / 13.6; anti-peak 24.0 / 35.8 / 12.5.
Pooled over s > 0: profile A weekly 23.9, dailyT 20.6, dailyT_dow 12.1; profile B weekly 22.3, dailyT 29.1, dailyT_dow 13.3. Weekday-only spend pooled: dailyT 39.1 (A) and 47.0 (B) versus weekly 20.5 and 19.9.

Cell-level verdicts (576 cells, 2-SE rule):
- dailyT versus weekly: dailyT better 346, tie 83, weekly better 147. The weekly-better cells concentrate in profile B with s >= 0.6 (for s = 0.9 under profile B, weekly is better in 7-13 of 18 cells depending on alignment) and in weekday-only spend with profile A at s = 0.9 (8 of 18). Worst cells (smooth spend, S-shaped response, weekday-only): the paired gap reaches 200-430 points.
- dailyT_dow versus weekly: dailyT_dow better 476, tie 46, weekly better 54.
- dailyT_dow versus dailyT: dailyT_dow is better in most cells with s >= 0.6.

### A4. Conclusions and limits
- Statement the paper can make: weekly totals absorb weekday seasonality in the baseline exactly; weekday seasonality in the media response is a real misspecification that can make an unadjusted daily-transform model worse than weekly, mainly when spend avoids high-response weekdays or the pattern is strong (an extreme weekend spike); a weekday term in the daily transform removes it.
- Limits: the weekday profile was assumed known for dailyT_dow; with a weekly KPI alone it is not observable, and estimating it from a weekly KPI was not tested. Holidays, paydays and other irregular day effects were not tested (they do not cancel in weekly sums). The same profile was applied to every channel and to the baseline.

---------------------------------------------------------------------------------------------------

## B. Shallow saturation: parameter and response-curve recovery (reviewer point 3)
Files: DESIGN_RECOVERY.md, rec_run.py, an_rec.py, results/REC_full.csv. 10,800 simulated markets (180 cells x 60 repetitions), truth daily. Three estimators at both frequencies: G (the paper's grid: 12 decays x half-saturation at the 5th-95th percentile of adstock x shape in {1, 1.6, 2.2}), X (G plus half-saturation at 1, 3, 10, 30 times the maximum adstock), C (continuous fit of decay, half-saturation and shape by Nelder-Mead).
True depth: med (half-saturation at the median of adstock, the paper's reference), mild (90th percentile), x1, x3, x10 (1, 3, 10 times the maximum adstock; the curve is nearly a straight line over the observed range). Shapes 1.0 and 2.2, decays 0.15 / 0.50 / 0.85, patterns bursty / smooth / real, signal R2 0.85 and 0.5.
Four outputs per market: total contribution bias; response-curve recovery (spend scaled by 0.5, 1.5, 2, 3 with fitted parameters held fixed, error as % of the true contribution at the observed spend); marginal ROI bias (finite difference for spend from 0.9 to 1.1); parameter recovery (daily arm).

### B1. The paper's grid cannot represent shallow truth (expectation E1: supported)
Mean |total bias| %, daily transform: G 18.8 (med), 18.6 (mild), 32.7 (x1), 41.0 (x3), 42.2 (x10); X 18.8, 19.4, 16.7, 12.9, 12.9. Weekly transform: G 29.0, 24.8, 35.9, 43.7, 45.5; X 29.1, 26.2, 24.4, 21.0, 21.3. The paper's depth range (mild to deep) sits inside its grid, so published results stand; a grid that cannot reach above the observed adstock fails when saturation is shallow.
Medians (more robust): daily G 9.5, 10.2, 26.7, 36.6, 35.1; daily X 10.2, 11.1, 9.3, 6.4, 6.3.

### B2. Total contribution can look right while the curve is not identified (E2: supported)
Daily, X: share of markets with |total bias| < 10%: 49.7%, 45.9%, 52.1%, 63.1%, 64.7% (med ... x10). Among those, the share with |error at twice the spend| > 25%: 0.5%, 3.4%, 17.1%, 30.8%, 23.6%. Weekly: 1.8%, 7.2%, 44.4%, 39.3%, 30.1%.
Median |error| when spend is doubled (daily X): 10.9, 12.5, 17.8, 18.3, 17.9; tripled: 11.3, 15.0, 27.1, 43.1, 41.5. Median |marginal ROI error| stays 4-5% (daily) and 6-9% (weekly) because the local slope at observed spend is well identified; the curve away from the observed range is not.
By shape and signal (daily X, median |error at 2x|): shape 1.0 about 8-10% at R2 0.85 and 17-19% at R2 0.5; shape 2.2 about 5-24% at R2 0.85 (worse when shallow) and 15-40% at R2 0.5.

### B3. Parameters (E4: supported for the half-saturation point)
Daily decay is recovered well at every depth (median |error| 0.04). Share of markets where the estimated half-saturation is off by more than a factor of 2: X 11.0% (med), 12.3%, 41.6%, 65.7%, 88.6% (x10); the paper's grid G 5.7%, 3.2%, 67.9%, 100%, 100%. The grids contain the true shape values (1.0, 2.2), so grid shape recovery is flattering; the continuous fit has median |shape error| 0.5 (med) falling to 0.2 (x10).
Identification width (X, daily): about 12-14 candidates have SSE within (1 + 6/n) of the best; the best curved fit improves on the best straight-line-in-adstock fit by a median 26% at med depth and only 2.5% at x10. Weekly: wider sets (23 candidates at med).

### B4. Does the daily-versus-weekly gap shrink with shallow saturation? (E3: not supported)
Paired weekly minus daily mean |bias| with X: shape 1.0: 7.4, 3.6, 4.1, 6.6, 6.8 points (SE 0.5-0.7); shape 2.2: 13.2, 9.9, 11.2, 9.6, 10.0 (SE 0.8-1.3). Daily is better at every depth including the nearly linear x10.
Interpretation (a hypothesis supported by a small calculation, not a theorem): aggregation error has a second source besides curvature, the timing of carryover. For a LINEAR response and 100 draws per cell, a weekly adstock of weekly totals cannot reproduce 0.6% (decay 0.15), 7% (0.50) and 14-16% (0.85) of the variance of the weekly sum of daily adstock.
Signed bias (X): shape 1.0 negative (daily -4.7 to -11.8, weekly -0.6 to -14.6); shape 2.2 positive (daily +6.7 to +15.2, weekly +17.7 to +25.0).

### B5. The continuous fit is not a safe fix
It sometimes lands on an almost constant transformed series. Weekly mean |bias| ranges from 92% (x10) to 25,378% (mild) because of such outliers; medians are 17.5-31.6%. Daily C: median 11-16%, mean 19-39%. Bounds on the half-saturation point (as in Robyn) are needed.

### B6. Limits
At x1, x3 and x10 the extension multipliers (1, 3, 10 times the maximum) coincide with the true half-saturation point in the matching decay candidate, so X is flattered in exactly those cells; C does not have this advantage. Single channel, truth daily, 156 weeks, geometric adstock and Hill only.

---------------------------------------------------------------------------------------------------

## C. Controlled comparison with Robyn (reviewer point 2, second round)
### C1. What could and could not be done
- The R package servers used for installing R packages are not reachable from the workspace, but the operating system's R and its package-manager packages are. I downloaded Robyn 3.12.1 source files from Meta's GitHub (raw files) and installed it from source with R 4.3.3, glmnet 4.1-8, prophet 1.0, reticulate 1.35, Nevergrad 1.0.12 (numpy 1.26). The helper package lares (printing, plotting, string helpers, clustering) is replaced by a minimal stand-in; the modelling code is unmodified. Clustering is therefore switched off and models are selected by explicit rules. Details: docs_extra/ROBYN_SETUP_NOTES.md. (The 2.5 experiment was run on the user's laptop with R 4.6.1 and the same Robyn version; clustering also switched off.)
- Checks: adstock and Hill transformations of my Robyn-type engine against Meta's Python code (difference 0 and 2e-16 over 50 random draws); ridge scaling against glmnet (a user-supplied lambda acts as lambda / sd(y); my first engine missed this and its run was discarded, results/RB_full_DISCARDED_ridge_scaling_bug.csv, NOT used).

### C2. Robyn-type engine, multichannel (400 markets, corrected run; DESIGN_ROBYN.md)
Four scenarios from the multichannel study (M1 independent, M2 correlated, M3 mixed daily/weekly truth, M7 time-varying effect with spend chasing), 100 markets each, 3 channels, new seeds. Held constant between the weekly and daily arm: markets, controls, hyperparameter bounds (theta 0.01-0.95, alpha 0.5-3, half-saturation fraction 0.05-1, lambda 0-1), search algorithm (TwoPointsDE), budget (2,000 evaluations, one trial), optimiser seed, ridge, sign constraints, 60/20/20 time-series validation. Not held constant (by construction): in the real package a daily model uses a daily KPI, here the KPI stays weekly; Prophet decomposition replaced by fixed controls; theta means different things at the two frequencies; one trial of 2,000 instead of Robyn's recommended 5 x 2,000.
Arms: gridW, gridD (the paper's grid + backfitting + non-negative least squares), OT (true transforms), and Robyn-type searches: SO (single objective, validation NRMSE), MO (NRMSE and DECOMP.RSSD, Pareto set over all evaluated models, three selection rules: lowest NRMSE, lowest RSSD, balanced).

Mean |total bias| %:

| scen | gridW | gridD | OT | SO W | SO D | MO-nrmse W | MO-nrmse D | MO-bal W | MO-bal D | MO-rssd W | MO-rssd D |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | 27.0 | 21.6 | 3.8 | 41.8 | 37.7 | 38.1 | 35.6 | 42.4 | 45.2 | 59.5 | 60.1 |
| M2 | 16.9 | 15.1 | 4.0 | 35.2 | 27.9 | 30.3 | 30.0 | 39.5 | 38.7 | 59.4 | 65.4 |
| M3 | 21.7 | 18.4 | 4.2 | 36.4 | 38.9 | 32.7 | 41.3 | 38.0 | 43.5 | 54.0 | 63.2 |
| M7 | 19.7 | 21.3 | 4.1 | 36.2 | 32.5 | 27.4 | 25.5 | 32.1 | 30.5 | 44.5 | 47.5 |

Signed mean bias % (underestimation dominates): SO W/D: M1 -13.7 / -5.4, M2 -7.8 / -10.9, M3 -14.6 / -6.6, M7 +21.2 / +12.2. MO-nrmse W/D: -24.4 / -24.5, -8.8 / -11.3, -16.4 / -22.7, +12.4 / +9.2. MO-rssd W/D: -49.7 / -53.0, -47.9 / -59.5, -41.6 / -56.7, -14.9 / -31.3.

Findings:
1. The search procedure adds error: Robyn-type SO minus grid, same frequency, +14.8 / +16.1 (M1, W / D), +18.3 / +12.8 (M2), +14.7 / +20.5 (M3), +16.5 / +11.2 (M7).
2. Daily versus weekly (weekly minus daily |bias|, positive = daily better; per scenario 100 markets, 2-SE rule): grid +5.4, +1.7, +3.4, -1.6 (all ties at this sample size); SO +4.1, +7.3 (daily better), -2.5, +3.8; MO-nrmse +2.5, +0.3, -8.7 (weekly better in M3), +2.0; MO-rssd -0.6, -5.9, -9.2 (weekly better in M3), -3.0. Pooled M1+M2+M3 (300 markets): grid +3.5 (SE 1.4), SO +3.0 (SE 2.3), MO-nrmse -2.0 (SE 1.7), MO-bal -2.5 (SE 1.4), MO-rssd -5.3 (SE 1.8).
So, with Robyn-type estimation, the daily advantage is small and uncertain with the single-objective search, and absent or reversed once the RSSD objective is in the selection.
3. DECOMP.RSSD hurts here. The true effect shares are far from spend shares (RSSD of the truth 0.38-0.49 on average, up to 0.94), so an objective that rewards agreement between effect share and spend share selects against the truth. Mean |bias| by selection rule: lowest NRMSE about 29-36%, lowest RSSD about 49-63%. Per-channel |bias| is larger still (balanced rule 71-143%).
4. Per-channel mean |bias| %: grid 30-39 (M1-M3), Robyn-type SO 44-73.

### C3. The real Robyn package
Real Robyn results: Part 2.4 (12 single-channel markets, weekly KPI versus daily KPI) and Part 2.5 (16 three-channel markets, controlled, at 2,000 x 5; arm B changes only the frequency of the transformation workflow, with the parameter-meaning differences listed in 2.5).

### C4. What this lets the paper say about Robyn
The strongest honest statement combines three results. (a) With my Robyn-type engine in multichannel markets, the aggregation effect measured with a grid search persists but is small relative to the error introduced by the search and selection procedure; with the RSSD objective in the loop, daily-versus-weekly is dominated by the selection rule. (b) With the real package in 12 single-channel markets, weekly data gave a clearly lower (more biased) contribution than daily data (mean |bias| 37% versus 20%), but with large run-to-run noise and with the daily arm also having 7x the observations. (c) With the real package in 16 three-channel markets at the recommended settings, moving the transformation workflow to daily frequency gave no improvement (B minus A: 7 points worse on the primary rule, not significant) and every arm underestimated by 40-50%. What none of this shows: how real Robyn behaves with clustering of Pareto models, with real (not simulated) data, or why it underestimates; the engine is an approximate equivalent of Robyn (end-to-end check in Part 2.4: same direction, correlation 0.34).


---------------------------------------------------------------------------------------------------

# PART 4. What is still not done, and what I would do next

Not done, and why:
1. Real Robyn: the planned noise-check repeats of the controlled experiment (markets 0, 2, 3 run twice more for arms A and B) were not run; they are replaced by a better-designed stability experiment, DESIGN_ROBYN_STABILITY.md (written 4 Nov 2026, NOT yet run): markets 0, 2, 4, 7, 11, 13, arms A and B, one repeat at 2,000 x 5 (noise) and one run at 4,000 x 5 (budget effect), 24 runs, about 9 hours, full Pareto sets and both convergence criteria saved, first-experiment results untouched; no convergence check at 4,000 iterations; no run with Robyn's clustering (needs the real lares package); no explanation of the 40-50% underestimation (ridge shrinkage vs Prophet absorbing media vs the error-score objective vs bounds were not separated). A cheap follow-up that would answer "why" without new markets: re-run a few markets with a fixed small ridge penalty or with Prophet switched off, and compare. Optional and probably not needed for the revision; needed only if a reviewer asks why Robyn is so biased.
2. Estimating the weekday profile from a weekly KPI. This cannot be done by a better estimator: a weekly KPI only contains weekly totals, so the weekday on which the response happens is not identified. The honest handling is a stated limitation plus a practical rule: if a daily KPI (or any daily proxy such as web visits or footfall) exists, estimate the weekday profile from it and use the weekday-aware daily transform; if only weekly KPI exists, report both the weekly and the daily model and treat the gap as part of the uncertainty. Holidays, paydays and other irregular day effects are not tested and are stated as limitations.
3. Real-Robyn decision-level metrics (budget reallocation, channel ranking) were not computed; the decision study uses my own estimators on multichannel markets. The Robyn output files of the 40 runs contain only the totals per channel, so ranking could be checked from the saved channel estimates (est_ch1..3 in results/RXM_laptop.csv) if wanted.
4. Daily-KPI estimation (as in the Robyn daily arm) was not studied separately in the grid framework, so the 7x observation effect is not separated from the transformation effect (arm B in 2.5 addresses this for Robyn only).

Still to do for the paper (no new simulation needed): apply the 11 verified manuscript edits; rewrite the abstract, introduction and conclusion around conditional claims, including the concession that in real Robyn the transform frequency is not the main error source; add the multichannel, weekday, shallow-saturation, sample-length, decision-level and Robyn sections (Robyn: Parts 2.4 and 2.5 together); rebuild the decision table; draft the response letter; read and cite Dew, Padilla and Shchetkina (2026); update the Zenodo replication package (include DESIGN_ROBYN_CONTROLLED.md, the patched transformation file and the 80-row results file); consider an OSF timestamp for the design files; include a "things that did not work" note (spend-only screens, Fourier index).

No guarantee of acceptance: these results make the paper more honest and more defensible, and they narrow the headline claim. The decision-level result moves the message from "aggregation leads to wrong budget decisions" to "aggregation biases attribution and marginal-ROI levels; direction of budget moves is mostly robust except when effects vary over time with spend". The controlled Robyn result narrows it further: the paper identifies a mechanism in a model class, and does not show that daily transforms repair Robyn.
