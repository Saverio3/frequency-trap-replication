# Decision-level study and sample-length study (design fixed BEFORE any result, 24 Oct 2026)

Why. A reviewer (and a JAR reader) will ask whether the contribution bias found in the earlier studies changes what a manager would DO with the budget. This study asks that directly, with the same multichannel markets as DESIGN_MULTI.md. The same engine, with the number of weeks changed, also answers "do the results depend on the 156-week design?".

## Fairness rules
1. Fresh seeds (prefix "DEC"). Nothing is tuned after looking at results. All scenarios and all arms are reported, including those where daily is not better.
2. Estimators see only y, daily spend per channel and the controls, exactly as in DESIGN_MULTI.md (same grids, same 3-sweep backfit, same NNLS). Truth is used only to score.
3. The market generator is the one in mc_run.py (same RNG call order). Check before the full run: for prefix "MC", the new code must reproduce mc_run.py's total bias for arms W, D and S1 on at least 20 markets (to within 1e-6), otherwise the study does not start.
4. Failures are reported as failures.

## Arms
W (all channels weekly transform), D (all daily), S1 (select inside the fit, Vuong z), OF (oracle frequency, grid parameters estimated), OT (true transforms, only coefficients estimated; the ceiling). S2 and S3 are not repeated (they were no better than S1 in the earlier studies; stated, not tested here).

## Counterfactual model for each arm
The fitted model for channel k is: contribution_k = b_k * T_k(spend_k), with T_k the chosen transform (frequency, decay, gamma, shape; gamma is a fixed number from the ORIGINAL spend, not recomputed when spend is rescaled). A budget change is a scale factor s_k applied to the whole daily spend series of channel k (shape over time kept; only the level changes). The same s is applied to the TRUE data-generating response (true decay, true gamma held at its original value, true frequency including the sub-daily split, the time-varying factor in M7, the post-campaign dip in M10, and the original scaling constant). For OT the fitted model is the true response times the estimated coefficient.

## Decision metrics (per market and arm; all scored against the truth)
1. Marginal ROI at the observed spend (s = 1): finite difference with +1% on one channel, per unit of spend, for every channel. Scored by the absolute relative error (estimated vs true marginal ROI), median over channels and markets; by whether the channel with the highest true marginal ROI is identified (top-channel hit rate); by whether the full ordering of channels is right.
2. Budget reallocation with the total budget fixed: choose s_1..s_K to maximise the model's total contribution subject to sum_k s_k * S_k = sum_k S_k (S_k = total spend of channel k over the sample) and bounds. PRIMARY bounds s_k in [0.5, 2.0] (large moves) and SECONDARY bounds [0.8, 1.25] (typical +/-20-25% moves). Solver: SLSQP, 3 starts (s = 1 and two random feasible starts), best kept, the same for fitted models and the truth.
   - T(s) = TRUE total media contribution at allocation s. T(1) = true contribution at the observed spend.
   - G* = T(s_true_opt) - T(1): the gain attainable with perfect knowledge. G_est = T(s_est_opt) - T(1).
   - LOSS = 100 * (T(s_true_opt) - T(s_est_opt)) / T(1): percentage of true media contribution given up by following the estimated optimum. Primary decision metric.
   - CAPTURE = G_est / G*: share of the attainable gain captured, only in markets that are not flat (G* >= 1% of T(1)). Flat markets (G* < 1% of T(1)) are counted and reported separately.
   - HARM = share of non-flat markets in which G_est < 0 (the recommended move makes the outcome worse than leaving the budget alone).
3. Total contribution bias (as before), for comparability.
Paired differences between arms on LOSS, by scenario and pooled (mean over scenarios of the scenario mean); an arm is better only if the paired difference exceeds 2 standard errors, otherwise a tie.

## Scenarios and size
All ten scenarios M1-M10 (definitions in DESIGN_MULTI.md), 300 markets each at 156 weeks (3,000 markets). If a smoke test shows the run takes more than 3 hours, markets per scenario are cut to 200 BEFORE the full run and the cut is recorded here. The pooled and per-scenario standard errors are reported so that thin results can be seen as thin.

## Sample-length study
Same code with the number of weeks NW in {78, 156, 260}. Scenarios V (single channel, validation scenario), M1, M2, M3, M7; 300 markets each at 78 and 260 weeks (156 comes from the main run, with the same scenarios). Outputs: mean |bias| and signed bias for W, D, S1, OF, OT, per NW; the daily-minus-weekly paired difference per NW; and the decision metrics above. Expectation (reported either way): with fewer weeks everything is noisier and the paired differences are less often significant; with more weeks the gap between OT and the estimated arms should shrink only if error is mainly estimation noise, and stay if it is structural.

## Not covered (stated in advance)
Holidays and payday effects; estimation of the weekday profile from a weekly KPI (not identifiable from weekly totals); time-varying coefficients other than M7; reallocation across time (flighting changes); budget changes outside the bounds above.

## Notes added during the run (24 Oct 2026)
1. Validation rule 3 passed before the main run: 21 markets (M1, M3, M7), arms W, D, S1, OF, OT, 0 mismatches against mc_run.py (tolerance 1e-6). The truth function reproduces the true contribution at s = 1 to 1e-12.
2. Main run (3,000 markets, 156 weeks) finished before the sample-length runs started; its results are in results/DEC_main_156.csv and results/DEC_main_156_analysis.txt. The design was not changed after seeing them.
3. The scenario V (single channel) is not part of the main run, so for the sample-length comparison V at 156 weeks is run separately with the same code and the same 300 markets (mode len, nw 156), declared here before it runs. V has no reallocation (K = 1), only total bias and marginal-ROI error.
4. Real-Robyn finding that affects interpretation (not a design change): re-running market 0 with the same seed gave different estimates (weekly 5,159 vs 7,601 earlier; daily 7,635 vs 10,334). At 1,000 iterations and one trial, real Robyn is not reproducible, so one run per market and arm is a noisy measurement.

## Part 3 (optional item): multichannel shallow-saturation study (declared 24 Oct 2026, before it runs)
Question: does the single-channel finding (shallow saturation is hard to identify; the paper's grid cannot represent it; total contribution can look right while the curve is wrong) hold with several channels, and does it change decisions?
Markets: K = 3 independent channels, truth all DAILY, kappa 0 (the M1 setting), 156 weeks, signal R2 0.85, patterns, decays, shapes and shares drawn as in M1. Two scenario variants, 300 markets each, fresh seeds (prefix "DSH"):
- M11 SHALLOW: each channel's true depth drawn from {x1, x3, x10}: Hill half-saturation gamma = 1, 3 or 10 times the maximum adstocked spend of that channel (curve almost linear over the observed range).
- M11c CONTROL: identical generator and code path, each channel's depth drawn from {mild, med, deep} (gamma at P90, P50, P25 of non-zero adstock).
Estimators (each with the same 3-sweep backfit and NNLS): W and D on the paper's grid G; WX and DX on the extended grid X = G plus gamma at {1, 3, 10, 30} times max adstock; OT (true transforms). X contains the true gamma in the x1, x3 and x10 cells, so X is flattered there (stated in advance; same caveat as in DESIGN_RECOVERY.md).
Metrics: total contribution bias; marginal-ROI relative error at observed spend and top-channel hit rate; budget-reallocation LOSS, CAPTURE and HARM under the two bound sets (as above); and EXTRAPOLATION error: the predicted gain from doubling the spend of all channels (sum over channels of f_k(2) - f_k(1)) against the true gain, in % of the true gain. Masked failure (declared): |total bias| < 10% and |extrapolation error| > 25%.
Comparison of interest: M11 versus M11c, G versus X, daily versus weekly, all paired by market. No success criterion; all cells reported.
