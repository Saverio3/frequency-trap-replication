# Selector study: can a practitioner identify the better aggregation? (run 10 Oct 2026)

Design: DESIGN_SELECTOR.md (stage 1 written before running; stage 2 written after stage 1, before running, on fresh seeds).
Scale: stage 1 = 39,300 simulated markets, stage 2 (confirmation) = 48,300 markets. Engine validated earlier against the published core cells; stage 1 and 2 core means agree (weekly 24.0-24.1, daily 15.4-15.6). Spot re-runs reproduce exactly.

## Short answer
No rule identifies the best aggregation in every market. A simple rule identifies it correctly about 80% of the time in the roughly one third of markets where the evidence is clear, and flags the rest as undetermined. Averaged over all worlds it is better than always-daily and always-weekly, and it is never more than 0.7 points worse than the best fixed choice in any world.

## What failed
- Spend-only screening (within-week variance share, share of zero days, CV, saturation depth): the pre-registered decision tree collapsed to "always daily" (no split flipped the majority in the training data). Spend patterns alone do not tell you which frequency wins.
- Holdout test (train 104 weeks, test 52): no better than the in-sample fit comparison (macro mean |bias| 18.1 vs 18.0). Not needed.
- My earlier guess that the holdout would be too weak to help was about the wrong tool: the plain in-sample fit gap carries the signal.

## What worked: Protocol P (fixed before the confirmation run)
1. Fit both transformations (weekly and daily-then-sum) with the same grid. Compute D = 100*(C_weekly - C_daily)/C_daily and the fit gap dR2 = (SSE_weekly - SSE_daily)/SSE_of_y_after_controls.
2. |D| < 10: ROBUST. The choice barely matters for the estimate (arms differ by about 4 points on average; 33% of markets still differ by more than 5). Use either.
3. Otherwise |dR2| >= 0.10: CLEAR. Use the arm with the lower SSE.
4. Otherwise UNDETERMINED. Report the average of the two as the point estimate and both as the range.

### Fresh-seed results (mean |bias| %)
| World | Always weekly | Always daily | Protocol P | % CLEAR / ROBUST / UNDET |
|---|---|---|---|---|
| W1 core (paper DGP) | 24.0 | 15.6 | 15.5 | 40 / 33 / 27 |
| W2 weekly-true | 16.3 | 27.2 | 17.0 | 48 / 24 / 28 |
| W3 time-varying effect | 27.4 | 23.1 | 22.7 | 15 / 44 / 41 |
| W4 sub-daily truth | 24.9 | 13.2 | 13.0 | 52 / 35 / 13 |
| W5 day-of-week | 23.1 | 17.0 | 16.1 | 44 / 32 / 24 |
| W6 other response forms | 25.4 | 22.0 | 20.7 | 30 / 39 / 31 |
| W7 noisy KPI (R2 0.7/0.5/0.3) | 32.1 | 24.0 | 24.1 | 28 / 28 / 44 |
| W8 weekly-true, noisy (R2 0.7/0.5) | 22.7 | 29.4 | 22.6 | 26 / 25 / 49 |
| Macro W1-W6 | 23.5 | 19.7 | 17.5 | |
| Macro all 8 | 24.5 | 21.4 | 19.0 | |

Standard errors for these world means are roughly 0.3 points, so the 0.7-point deficit in W2 is about two SE.

### Pre-registered criteria
- (a) CLEAR-tier hit rate on material markets (arms differ by more than 5 points): pooled 0.80 (bar 0.75), lowest world 0.695 (W6; bar 0.65). Passed.
- (b) Macro mean |bias| below both fixed arms: 17.5 vs 23.5 and 19.7. Passed.
- (c) UNDETERMINED tier, mean |bias|: average of the two 27.1, always daily 30.4, always weekly 32.7, in-sample pick 28.9. The average wins pooled and in 6 of 8 worlds (worse than picking in W2, where the weekly truth makes picking right).
- (d) Noisy KPI: CLEAR hit rate 0.78 (W7) and 0.77 (W8). The rule survives noise, but the CLEAR tier shrinks: at R2 = 0.3 only 13% of markets are CLEAR and 62% are UNDETERMINED.

### Hit rate by world in the CLEAR tier (material markets)
W1 0.78, W2 0.84, W3 0.77, W4 0.86, W5 0.79, W6 0.70, W7 0.78, W8 0.77.

## Caveats (must go in the paper)
- The rule picks the aggregation; it does not remove the bias. Inside the CLEAR tier the chosen arm still has mean |bias| 10-30% depending on the world. Inside the ROBUST tier both arms agree but are still 12-22% off (agreement is not accuracy).
- Wrong picks still happen: in 11-26% of markets the protocol is more than 10 points worse than the better arm.
- The two-arm range in the UNDETERMINED tier brackets the truth in only 41% of markets. Do not call it an interval.
- Only 156 weeks and a 252-candidate grid for both arms were tested; shorter samples, other grids (Robyn, Meridian) and more than two frequencies were not.
- The 0.10 and 10% thresholds were set from stage 1 (exploratory), then tested once on fresh seeds. They are not tuned further.
- The worlds are my constructions. Real advertising may not look like any of them.
- Three scripts: sel_run.py (generator and diagnostics), an_sel.py (stage 1 analysis), an_sel2.py (stage 2 analysis). Results CSVs are local and re-creatable (seeded).
