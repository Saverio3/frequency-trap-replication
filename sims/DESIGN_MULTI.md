# Multichannel study (design fixed BEFORE running, 10 Oct 2026)

Why: all earlier simulations used one media channel. Reviewers will ask whether the aggregation result and the frequency check survive when several channels run together, are correlated, burst, stay always on, follow the season, or have different true frequencies.

## Fairness rules
1. New seeds (prefix "MC"), stage A (build) and stage B (fresh-seed confirmation, prefix "MCB"). Nothing is changed between A and B except what the criteria below allow.
2. Every scenario is reported. Scenarios that favour weekly and scenarios that break the check are included on purpose.
3. All arms use the same grid, same controls, same estimator and same metric. Estimators see only y, daily spend per channel and the controls (including the price control). No truth.
4. Randomised channel settings (decay, depth, shape, pattern, share) are drawn per market from fixed grids so no single hand-picked combination drives a result.

## Market (data-generating process)
- 156 weeks, daily spend per channel (K = 3 or 5), weekly KPI.
- Baseline: 800 + 0.5 t + 30 sin(2 pi t/52) + 40 * price_z, price_z a weekly AR(1) (phi 0.7) series observed and used as a control.
- Channel k: spend pattern, decay delta_k in {0.15, 0.50, 0.85}, depth in {mild, med, deep} (gamma at P90/P50/P25 of adstock), Hill shape in {1.0, 2.2}, share w_k of total media amplitude.
- True frequency of each channel: DAILY (adstock and Hill on daily spend, summed to weeks), WEEKLY (adstock and Hill on weekly totals), or SUB (6-hour process, Dirichlet(0.3) intra-day split).
- Total media signal scaled so its standard deviation equals the baseline's; KPI noise set so signal R2 = 0.85 unless stated.
- Spend patterns: bursty (lognormal bursts on 40% of days), smooth (always on), real (empirical Facebook spend values), flighting (2-5 week on blocks, 2-5 week off blocks), pulsing (weekdays only), sporadic (about 3% of days, large).
- Cross-channel correlation: spend_k multiplied by exp(kappa_k z_t), z a shared standardised factor (daily AR(1) phi 0.6 plus weekly AR(1) phi 0.8). Realised weekly spend correlations are recorded.

## Scenarios (1000 markets each, stage A and again in stage B)
- M1 independent: K=3, truth all DAILY, kappa 0.
- M2 correlated: K=3, truth all DAILY, kappa 1 for all channels.
- M3 mixed truth: K=3, one random channel WEEKLY, the others DAILY, kappa random in {0, 0.5}.
- M4 five channels: K=5, each channel WEEKLY with prob 0.25 else DAILY, kappa random in {0, 0.5, 1}, patterns drawn with repeats.
- M5 seasonal confounding: K=3, truth DAILY, spend multiplied by exp(1.0 * annual-season_t) (annual sine, daily).
- M6 sub-daily: K=3, each channel DAILY or SUB (prob 0.5), no WEEKLY.
- M7 time-varying effect: K=3, truth DAILY, shared multiplicative effect exp(0.5 z - 0.125) with the same z that tilts spend (kappa 1): the reviewer's mechanism.
- M8 noisy: K=3, mixed truth as M3, signal R2 = 0.5.
- M9 small channel: K=3, shares (0.70, 0.25, 0.05) randomly assigned, mixed truth as M3.
- M10 boost-then-dip: K=3, truth DAILY, two channels have response r_t - 0.3 * mean(r_{t-14..t-1}) (post-campaign dip), one standard.

## Arms (estimators; each runs a backfitting search: 3 sweeps, channel by channel, each channel picks its best of 252 candidates given the others)
- W: all channels weekly transform.
- D: all channels daily transform.
- S1 (select inside the fit): at every channel step both the best weekly and best daily candidate are found given the other channels; the Vuong z (daily minus weekly log-likelihood per week) decides; daily if z > 0.
- S2 (screen once, then fit): each channel is first screened alone with the controls plus the OTHER channels entered as plain weekly linear spend sums; Vuong sign decides; then the joint backfit runs with those assignments.
- OF (oracle frequency): true frequency per channel (SUB counted as daily), grid parameters estimated.
- OT (oracle transform): true transforms, only coefficients estimated.
- Final coefficients: non-negative least squares on media (controls unrestricted), contributions = coefficient x chosen transformed series.

## Metrics
- Total media contribution bias % = 100 (sum est - sum true)/sum true, per market; reported as mean |bias| and mean signed bias.
- Per channel bias % (|bias|).
- Frequency classification per channel (S1, S2): correct if the chosen frequency equals the truth (WEEKLY vs DAILY-or-finer).
- Differences between arms judged on paired markets: better only if the mean paired difference exceeds 2 standard errors.

## Success criteria (fixed now)
- C1 (aggregation claim, descriptive): D vs W on total bias per scenario; state where each wins.
- C2 (workflow): macro-average mean |bias| of S1 and of S2 is below both W and D; and in no scenario is S1/S2 more than 2.0 points worse than the better of W and D.
- C3 (identification): per-channel classification accuracy of S1 and S2, pooled over M1-M7 and M10 at least 0.90, and at least 0.80 in every scenario.
- C4: report channel-level accuracy by spend pattern and by share bin (share < 0.10, 0.10-0.30, > 0.30), and by realised correlation bin.
- If a criterion fails it is reported as failed and stated in the paper as a limitation.
Stage B must be run with the same code and criteria. Any change to the estimators after stage A is declared as a change and stage B is then also a test of the changed version only if declared before stage B runs.

## Note added before stage A (after validation and a timing test only)
Validation, single-channel limit (scenario V, 100 markets, same estimators, price control and NNLS added): mean |bias| weekly 24.4, daily 15.6, oracle transform 2.6, versus the paper's 24.0, 15.2, 2.7. The engine ran at about 0.05 s per market, so the number of markets per scenario was raised from 300 to 1000 (10,000 markets per stage). No scenario results had been looked at.

## Note 2 (before stage A, after an engine bug in the first launch, no results seen)
The first launch of stage A crashed (NaN in the Hill transform when the gamma percentile of a long adstock tail underflowed, which happens with flighting and sporadic spend). Fix applied to the multichannel engine only: gamma for the TRUE response uses the percentile of non-negligible adstock (> 1e-6 of the maximum), and the Hill function adds 1e-300 to its denominator. Single-channel validation re-run after the fix: weekly 24.6, daily 15.5, oracle 2.6. No scenario results were examined.

## Stage A and B outcome (recorded 10 Oct 2026, before stage C)
Stage A and stage B (fresh seeds) agree. Pre-registered criteria: C2 FAILED (macro average passes, but S1 and S2 are more than 2 points worse than the better fixed arm in some scenarios: B: S1 up to 4.1, S2 up to 3.2). C3 FAILED (per-channel frequency accuracy pooled S1 0.83, S2 0.75; lowest scenario 0.70 / 0.64). An oracle bound (known parameters of all channels) gives 0.968 pooled, so the information exists but the practical per-channel tests do not extract it.

## Stage C (declared before running): joint assignment search
New arm S3 = exhaustive search over all 2^K frequency assignments: for each assignment run the same 3-sweep backfit with the same grid, compute the final NNLS residual sum of squares, choose the assignment with the lowest SSE (all assignments have the same number of parameters, so SSE is a fair comparison; ties go to daily). Evaluated on fresh seeds (prefix MCC), 1000 markets per scenario, arms W, D, S1, S2, S3, OF, OT on the same markets. Criteria identical to C2 and C3 (S3 must have macro mean |bias| below both W and D, no scenario more than 2.0 points worse than the better of W and D, per-channel accuracy pooled >= 0.90 and >= 0.80 in every scenario). No change to S3 after stage C. If it fails, it is reported as failed.

## Stage C outcome (recorded 10 Oct 2026)
S3 (exhaustive assignment search), fresh seeds MCC, 1000 markets per scenario: C2 FAILED (macro 22.9 vs min(W,D) 23.1, but worst scenario gap vs best fixed arm 4.2 points, in M7), C3 FAILED (pooled per-channel accuracy 0.834, same as S1 0.833; S2 0.749). Estimator sensitivity (3 sweeps vs best of 6 orders x 10 sweeps, M1/M2/M3/M7 x 250 markets) changed no conclusion (e.g. M1 weekly 28.1 vs 28.1, daily 21.4 vs 21.3). No further estimator variants were run. These failures are stated as limitations.
