# Design Freeze — "Temporal Aggregation and Disaggregation in Nonlinear Marketing Mix Models"
*Phase 1 document, v1.0 — 9 Aug 2026. Freeze this before any full runs; log every later deviation in §11.*

---

## 1. Research questions & pre-stated hypotheses

**RQ1 (media).** When the true advertising response operates at daily frequency with
carryover and saturation, what bias does the universal weekly practice
(sum → weekly adstock → weekly saturation) introduce, and under what conditions does
transforming at daily frequency remove it?

- H1a: Weekly practice understates media contribution, with bias increasing in
  saturation depth and decreasing in carryover speed (pilot: −51% worst case,
  fast-decay/deep-saturation).
- H1b: Daily transformation eliminates the bias for fast-decay channels.
- H1c: For slow-decay channels, naive daily estimation is weakly identified from
  weekly KPI and can overstate contribution (pilot: +22–80%); constrained/regularized
  daily estimation repairs this.
- H1d: MIDAS weighting adds no material benefit once transformations are daily
  (pre-stated null; pilot-confirmed).

**RQ2 (covariates).** For low-frequency covariates in a weekly model, how do common
treatments (hold-flat, rolling averages) compare with interpolation and formal
temporal-disaggregation methods (Kalman, Chow-Lin GLS, Denton, ML-based)?

- H2a: Rolling averages are dominated by every alternative (pilot: 26–45% bias),
  with bias increasing in window length (lag distortion mechanism).
- H2b: At monthly frequency, simple interpolation is near-optimal and indicator-based
  methods add indicator noise exceeding interpolation error.
- H2c: At quarterly frequency (sparse observations), indicator-based and ML methods
  overtake interpolation, most strongly for fast-moving or regime-breaking truths.
- H2d: Treatment ranking depends on variable type (smooth / step / crisis); a single
  universal prescription is wrong, motivating the decision table.

**RQ3 (practice).** On real public data, do the competing practices produce materially
different channel ROIs and covariate effects, and does the simulation-recommended
practice forecast held-out data better?

## 2. Part A design — media aggregation

**Data-generating process (daily):**
spend_d → geometric adstock(δ_daily) → saturation S(·; shape h, depth γ) → daily
response; weekly KPI = Σ(daily responses) + base + trend + seasonality + noise.

**Factors (full factorial core):**
| Factor | Levels |
|---|---|
| Daily carryover δ | 0.15 (search-like), 0.50, 0.85 (TV-like) |
| Saturation depth | mild (γ = P90 of adstock), medium (P50), deep (P25) |
| Saturation shape | concave (Hill h=1), S-shaped (h=2.2) |
| Spend pattern | bursty (flighted), smooth (always-on), REAL (semi-synthetic shapes from FB dataset) |
| Media effect size | media = 15% / 30% / 50% of KPI variance |
| Data length | 104, 156, 208 weeks |
| Noise | calibrated so model R² ∈ {0.75, 0.85, 0.95} |

Core grid = δ × depth × shape × pattern (3×3×2×3 = 54 cells) at medium effect,
156w, R²=0.85; remaining factors varied one-at-a-time from the base cell
(sensitivity analyses). 200 replications per core cell; 100 per sensitivity cell.

**Estimation arms:**
1. `weekly` — sum spend weekly; estimate weekly adstock + saturation (grid+NLS)
2. `dailyT` — estimate daily adstock + saturation; aggregate transformed; weekly OLS
3. `dailyT_reg` — as (2) with regularization: prior/penalty tying daily decay to
   channel-class ranges (the fix motivated by H1c)
4. `weekly_midas` — weekly practice + Almon within-week weights (robustness; H1d)
5. `oracle` — true transformations known (upper bound)

**Metrics (all arms, every replication):**
- Total contribution bias % (primary)
- mROI error at observed spend level (decision-relevant curvature error)
- Out-of-sample forecast MAPE (last 26 weeks)
- Decision-flip rate: does a 2-channel budget optimiser choose differently vs oracle?

## 3. Part B design — covariate disaggregation

**Truth processes (weekly latent):** smooth-slow (AR ρ=.97), smooth-fast (ρ=.85),
step (8 jumps, rate-style), crisis (one regime break + recovery), seasonal
(strong annual cycle + drift — retail-sales-type; tests whether interpolation
smears seasonality). Effect sizes
small/medium/large (covariate = 5% / 15% / 30% of KPI variance).

**Observation frequencies:** monthly (every 4w) AND quarterly (every 13w) — the
quarterly arm is where H2c gives indicator/ML methods their fair test.

**Indicator environment:** none | 1 indicator (ρ ∈ {0.5, 0.75, 0.9}) | 15 indicators
(3 informative at ρ={.75,.65,.55}, 12 noise).

**Arms:** hold-flat; roll-4/8/12; linear; cubic spline; Kalman local-level; Kalman
local-linear-trend; Chow-Lin (PROPER GLS with AR(1) residuals, via published
formulation); Denton-Cholette; ElasticNet-ML and GBM-ML (Jung-2025-style with
reconciliation); Lasso high-dimensional; oracle.
Excluded with reason: generative/diffusion disaggregation (compute; listed as
future work).

**Metrics:** |coefficient bias|% (primary); forecast MAPE; weekly-path RMSE;
month/quarter-consistency check (do disaggregated paths respect observed aggregates).

Replications: 200 per core cell (truth × frequency × arm at medium effect,
1-indicator ρ=.75); 100 per sensitivity cell.

## 4. Calibration protocol (anti-"toy world" defence)
- Spend distributions, burstiness, and channel correlations estimated from the
  Kaggle media-spends dataset and FB campaign daily shapes.
- Media effect sizes anchored to published advertising elasticity meta-analyses
  (Sethuraman-Tellis-Briesch range); document the mapping.
- Noise set so simulated R² matches the 0.7–0.9 band of reported real MMMs.
- Covariate truths calibrated to real series: confidence (smooth), BoE rate (step),
  2020 shock (crisis), CPI inflation (smooth-with-shocks), ONS retail sales index
  (seasonal). Cross-sector breadth: these five types cover the covariate lists of
  non-financial sectors too (types, not variables, are what the design tests).
- Decision-table rule zero (goes in §6 outputs): "check the variable's NATIVE
  frequency first — if a weekly/daily version exists (FX, fuel, market rates,
  weather, Trends), use it; disaggregate only what is truly low-frequency."
- Semi-synthetic arm: REAL daily spend series + planted synthetic response
  (X real, truth known).

## 5. Real-data applications (RQ3)
- Datasets: Kaggle media-spends (weekly, 8 channels); Dunnhumby Breakfast-at-the-Frat.
- For each: fit the practice-representative arms; report (i) spread of channel
  ROIs across arms (materiality), (ii) holdout (last 26w) forecast comparison,
  (iii) covariate treatments applied to real BoE rate + confidence series.
- No truth claims on real data; framed strictly as materiality + predictive check.

## 6. Analysis & reporting plan (decided now, before results)
- Primary tables: mean |bias| with Monte-Carlo standard errors, by cell.
- Money charts: (A) bias vs carryover speed by arm; (B) disaggregation ladder by
  frequency; (C) the practitioner decision table (variable type × recommended
  treatment × cost of common malpractice).
- ALL cells reported including those where hypotheses fail; no cell dropping.
- Effect threshold for "material": |bias| ≥ 10% (stated a priori).

## 7. Reproducibility
- Repo: /simulation /methods /experiments(config-YAML) /analysis /paper
- Global seed policy: seed = hash(cell, replication); logged per run.
- One-command reproduction: `make all` → every table/figure.
- Data: download_datasets.py fetches open data; Kaggle/Dunnhumby fetched by user
  under their licenses (no raw redistribution); processed simulation outputs +
  code archived on Zenodo with DOI at submission.
- Optional but recommended: post this document to OSF before Phase 2 (timestamped
  preregistration).

## 8. Compute plan
Grid ≈ (54 + sensitivity) × 200 reps × 5 arms (A) + B-grid × 13 arms; estimated
~400k model fits; all cheap (OLS/NLS/grid) → feasible on one machine over nights;
parallelize with joblib across cells.

## 9. Target venues (decided provisionally, revisit after results)
1. Journal of Advertising Research (ABS 3) — primary
2. International Journal of Research in Marketing (ABS 4) — stretch, only if
   results exceptionally clean
3. Journal of Marketing Analytics (ABS 2) — safety; topical fit proven (Franses 2021)
Preprint to arXiv (stat.AP) on submission day.

## 10. Co-author plan
Approach 1–2 UK marketing/econometrics academics AFTER this document + pilot
results exist (strongest pitch). Candidate profile: quantitative marketing or
applied econometrics, has published on advertising response or forecasting.

## 11. Deviation log
| Date | Change | Reason |
|---|---|---|
| 2026-08-09 | Added seasonal truth type; CPI + retail sales to calibration; native-frequency rule zero | Cross-sector coverage discussion (pre-Phase-2, before any full runs) |
| 2026-08-10 | Engine v1.1: fixed Part A bug (saturation was applied post-aggregation in dailyT arms); first full run's Part A superseded, rerun required. Added planned factor: saturation FAMILY (bounded Hill vs scale-preserving atan) after v1.1 verification showed family changes the daily-vs-weekly gap pattern. Seasonal truth type reclassified: reported as identification finding (oracle itself biased ~22% due to collinearity with seasonal controls), DGP to be redesigned before treatment-ranking claims. | Bug found by cell-level inspection of full-run output |
| 2026-08-10 | Final-run spec (engine v1.2): rolling windows unified to {4,8,12,24}w across monthly & quarterly, each as trailing SMA, centered SMA, and EMA; paired-difference tests with MC SEs added to all tables; sensitivity cells (data length 104/208, effect size low/high, noise levels) implemented per §2; finer transformation grids; Weibull adstock + atan saturation robustness cells; 4 additional figures (mechanism, rolling dose-response, signed-bias direction, decay-recovery diagnostic); 'real' spend cells must fail loudly if datasets absent. | Methodology closure discussion before final run |
| 2026-08-10 | v1.2.1: window set extended to {4,8,12,24,36}; added multichannel sensitivity cell (2 correlated correctly-specified nuisance channels) to answer the multicollinearity objection; frequency-units warning (δ_weekly = δ_daily^7) to appear as paper text box, no simulation arm needed (deterministic). Methodology declared CLOSED. | Final closure audit before the definitive run |
| 2026-08-11 | v1.2.2 (pre-final-run): Part B DGP gains a media channel whose spend correlates with the macro cycle; new metrics media_abs_bias / media_signed_bias measure MEDIA-ROI contamination caused by each covariate treatment. Reopens closure narrowly for this one addition; welds Part B to the paper's media thesis. | Part A/B coherence review — covariate mistreatment shown (verification run) to contaminate media ROI, gradient monotone in treatment quality |

## 12. Kill criteria (honesty safeguards)
- If Phase 2 core results contradict pilots (e.g., weekly-practice bias < 10%
  everywhere), the paper pivots to the null honestly or stops — no fishing.
- If Scholar sweep (Phase 0 §1) surfaces a 4/4 disqualifier at any point: stop,
  reassess against the backup board (spec-curve, PPI, optimisation).