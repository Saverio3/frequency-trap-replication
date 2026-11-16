# Multichannel study: results (10 Oct 2026)

Design: DESIGN_MULTI.md (fixed before running). Three fresh-seed batches of 10,000 markets (stage A, stage B, stage C), 10 scenarios x 1000 markets, K = 3 or 5 channels, 156 weeks. Engine validated on the single-channel limit (weekly 24.6, daily 15.5, oracle 2.6 vs paper 24.0, 15.2, 2.7).

## Headline
1. The aggregation bias is real but conditional. With independent channels (M1) daily beats weekly by 6.4 points (SE 0.9); with sub-daily truth (M6) by 4.2; with mixed truth (M3) by 2.0. With correlated channels (M2), five channels (M4), seasonal confounding (M5), boost-then-dip (M10), small channel (M9) it is a statistical tie, and when the effect varies over time together with spend (M7) weekly is better by 3.5 (SE 0.85). With noisy KPI (M8) weekly is better by 2.3.
2. In every multichannel scenario the total contribution error is 15-30% for every arm, even the oracle-frequency arm. Knowing the true frequency of every channel (OF) removes almost none of it (macro 22.4 vs daily 23.1), while knowing the true transform (OT) gives 6.0. The error is dominated by estimating decay, saturation and shape under overlap and collinearity, not by the aggregation level.
3. The per-channel frequency check fails the pre-registered bar. Pooled accuracy S1 0.833, S2 0.749, S3 0.834 (bar 0.90, 0.80 per scenario). It is good for big channels (share > 0.30: 0.90), mediocre for medium (0.81), poor for small (< 0.10: 0.62). By pattern: real-like and bursty 0.90, sporadic 0.85, smooth 0.80, pulsing 0.78, flighting 0.71. By max cross-channel correlation: <0.3 0.86, 0.3-0.6 0.78, >0.6 0.72.
4. An oracle likelihood-ratio classifier that knows all parameters reaches 0.968, so the information exists; no practical test tried here extracted it.
5. The workflow arms (S1 select inside the fit, S2 screen first, S3 exhaustive search) beat the better fixed arm only slightly at macro level (22.3 to 22.9 vs 23.1) and are up to 3.1 to 4.2 points worse in M7. C2 failed.

## Stage C table (total contribution mean |bias| %)
scen  W     D     S1    S2    S3    OF    OT
M1    27.3  21.0  21.1  21.8  21.2  21.0  4.5
M2    15.1  14.8  15.1  14.5  14.8  14.8  4.0
M3    23.0  21.0  19.7  20.0  19.8  19.4  4.2
M4    21.0  20.4  19.7  19.0  19.4  19.0  5.1
M5    29.6  30.2  31.1  29.4  31.3  30.2  13.7
M6    25.3  21.1  20.7  20.8  20.7  21.1  4.8
M7    17.5  21.1  21.6  20.6  21.7  21.1  3.6
M8    28.6  30.9  30.0  28.9  30.2  28.4  10.4
M9    22.5  21.9  20.3  19.7  20.3  19.9  5.4
M10   30.2  28.7  29.3  28.7  29.2  28.7  4.5
MACRO 24.0  23.1  22.9  22.3  22.9  22.4  6.0

## Per-channel (paired W minus D, mean |bias| points; positive = daily better)
M1 9.1 (SE 1.0), M2 5.6 (1.5), M3 -0.7, M4 -0.9, M5 4.3 (2.5), M6 7.6 (1.2), M7 3.7 (3.8), M8 0.7, M9 -5.4 (2.9), M10 4.4 (2.4). Small channels (share < 0.10) have |bias| around 196%, regardless of arm.

## Sensitivity to search effort (M1, M2, M3, M7; 250 markets)
3 sweeps vs best of 6 orders x 10 sweeps: W 28.1/28.1, 15.1/15.1, 21.8/21.9, 17.6/17.4; D 21.4/21.3, 15.8/14.8, 20.2/19.8, 19.9/20.1. Conclusions unchanged.

## What the paper can and cannot claim
Can: aggregation bias exists and is large when channels are independent or sub-daily; the direction of bias depends on the response curve; with correlated, seasonal or time-varying settings it can vanish or reverse; a per-channel check works for larger channels; the single-channel process check is accurate (97.6% balanced).
Cannot: that daily is always better; that a practical test identifies every channel's frequency at 90%+ in multichannel models; that fixing frequency fixes total bias.

## Limits
Simulation worlds are mine; truth is exactly daily, weekly or 6-hour; 156 weeks; one grid-search estimator (no Bayesian priors, as in Robyn/Meridian); hold-out and priors could change small-channel behaviour.
