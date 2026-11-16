# Selector study: can a practitioner identify the better aggregation? (design fixed BEFORE running, 10 Oct 2026)

Question: with only observable information (weekly KPI, daily spend), can a simple rule choose weekly vs daily transformation, and can it do so across ALL worlds, including those that favour weekly?

## Fairness rules
1. New seeds (prefix "SEL"), independent of every earlier run. Same DGP code as the earlier scenario scripts, same estimators (paper grid: 12 decays x 7 gamma percentiles x 3 shapes = 252 candidates per arm), same metric (contribution bias %).
2. All worlds and all cells reported. Unfavourable worlds (weekly-true, time-varying with spend chasing effectiveness) are included on purpose.
3. A selector may use ONLY observable inputs: y (weekly KPI), daily spend, controls. No truth, no true decay, no true shape.
4. All thresholds, splits and rules below are fixed now. Nothing is tuned on the evaluation worlds.
5. The learned screening tree is trained ONLY on the core world (paper DGP, reps 0-49 of each cell) and evaluated on (a) core reps 50-99 and (b) every other world. Cross-world performance is the headline, not core performance.
6. Any selector that is not better than "always daily" or "always weekly" in a world is reported as not better.

## Worlds (reps per cell in brackets)
- W1 core (paper DGP, 54 cells) [100]
- W2 weekly-true (truth built on weekly totals, 54 cells: delta x depth x shape x pattern) [100]
- W3 time-varying Hill truth: tv in {daily AR1, weekly AR1}, kappa in {0, 1}, shape {1.0, 2.2}, delta x pattern, depth med (72 cells) [100]
- W4 sub-daily truth: K in {4, 24}, Dirichlet alpha {0.3, 1.0}, delta x shape x pattern, depth med (72 cells) [100]
- W5 day-of-week (strength 0.6, multiplicative, alignment neutral/thursday/peak/offpeak), weekly KPI, delta x shape x pattern (72 cells) [100]
- W6 alternative forms: log1p (27), linear (9), power 0.5 (9), two-component adstock (6), wear-out (18) = 69 cells [100]

## Per-market observables computed
- Both arms fitted on full sample (paper grid): contribution estimates, SSE, selected decay/gamma/shape.
- Fit gap: dR2 = (SSE_weekly - SSE_daily) / SSE_of_y_after_controls.
- Disagreement: D = 100*(C_weekly - C_daily)/C_daily, C = total estimated media contribution.
- Holdout: train weeks 1-104, test weeks 105-156. Each arm picks its candidate on training weeks only, coefficients and controls fitted on training weeks, RMSE on test weeks. Holdout gap = (RMSE_weekly - RMSE_daily)/RMSE_daily.
- Spend-only screens: WV = share of daily spend variance that is within-week; ZS = share of zero-spend days; CV = coefficient of variation of daily spend.
- Daily-arm depth: DEPTH = share of active days where daily adstock exceeds the fitted gamma.

## Selectors (all fixed)
- S_weekly: always weekly. S_daily: always daily.
- S_insample: pick the arm with lower full-sample SSE (tie -> daily).
- S_holdout: pick the arm with lower test RMSE (tie -> daily).
- S_both: daily unless BOTH in-sample and holdout prefer weekly.
- S_hedge: average of the two contribution estimates.
- S_tree: depth-2 decision tree (min leaf 200) on [WV, ZS, CV, DEPTH, dR2, holdout gap], target = daily has lower |bias|; trained on core reps 0-49 only.
- S_tree_screen: same tree but only spend-only + DEPTH features (no fit statistics).
- Oracles (bounds, not usable): market-oracle (picks lower |bias| each market, exploits noise); cell-oracle (picks the arm with lower mean |bias| in that cell).

## Metrics
- Mean |bias| of each selector, per world and macro-averaged across worlds (equal weight per world).
- Regret vs cell-oracle (points).
- Hit rate among MATERIAL markets (arms differ by > 5 points in |bias|): share where the selector picks the better arm. 50% = coin flip.
- Disagreement flag: |D| < 10 -> flagged "robust". Report share of markets flagged robust, and the mean |bias| difference between arms inside the robust group and the sensitive group. A useful flag has small arm differences when robust.

## Decision rule for what we claim
- "Selector works" only if it beats BOTH always-daily and always-weekly macro-averaged AND in the unfavourable worlds (W2, W3) and has hit rate clearly above 50% (95% CI excludes 50%) in material markets in at least 4 of 6 worlds.
- Otherwise we report what it does do (e.g. only flags materiality) and say it cannot identify the best aggregation.


## Note (added before the full run, after a timing test only)
Engine ran at 0.025 s per market, so reps were raised from 40 to 100 per cell (about 39,300 markets). No results had been looked at. Tree training reps changed to 0-49, evaluation core reps 50-99.

## Stage 2: confirmation run, pre-registered AFTER stage 1 results, BEFORE running (10 Oct 2026)
Stage 1 (39,300 markets) showed: the pre-registered trees collapsed to "always daily" (no split flipped the majority), the in-sample fit comparison was the best simple selector (macro mean |bias| 18.0 vs weekly 23.7, daily 19.7) and the holdout added nothing. Exploratory only: the hit rate rose with the size of the fit gap. Because that last point is a post-hoc look, it is tested on fresh seeds before any claim.

Protocol P (the practitioner rule, fixed now):
1. Fit both transformations with the same grid. Compute D (disagreement) and dR2 (fit gap, as defined above).
2. If |D| < 10: tier "ROBUST" -> report either (we use daily).
3. Else if |dR2| >= 0.10: tier "CLEAR" -> use the arm with the lower in-sample SSE.
4. Else: tier "UNDETERMINED" -> report the average of the two as the point estimate and the two as the range.
Fresh seeds (prefix "SELC"), 100 reps per cell, worlds W1 to W6 as before plus two stress worlds with a noisier KPI that stage 1 did not contain:
- W7: core DGP, KPI R2 in {0.7, 0.5, 0.3}, depth med, delta x shape x pattern (54 cells)
- W8: weekly-true DGP, KPI R2 in {0.7, 0.5}, depth med, delta x shape x pattern (36 cells)
Success criteria (fixed now): (a) in the CLEAR tier the pooled hit rate on material markets (arms differ by >5 points) is at least 0.75 and no world is below 0.65; (b) protocol P has lower macro mean |bias| than both always-daily and always-weekly; (c) in the UNDETERMINED tier, report which of daily / weekly / average has the lowest mean |bias| (no prior claim); (d) noisy worlds W7/W8 reported separately; if the CLEAR-tier hit rate falls below 0.65 there, we say the rule does not survive noisy KPIs.
If any criterion fails we report it as failed.
