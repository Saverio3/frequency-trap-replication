# The Frequency Trap — replication repository

Code, pre-registered designs, results and run instructions for
**"The Frequency Trap: Temporal Aggregation and Disaggregation Bias in Nonlinear Marketing Mix Models"**
(major revision, Journal of Advertising Research).

Everything here is meant to be read top to bottom: first *what we claim and what we found*, then *how to re-run each piece*, then *what is and is not in the repo*.

> **Honest status in one paragraph.** All code that was in the project is here, plus the scripts recovered from the working sessions. Every Python study was smoke-tested and the exports reproduce **byte-for-byte** (see `docs/SMOKE_TEST_LOG.md`). Full result files exist for the original paper, the real-data application, the single-channel real-Robyn run, and the controlled real-Robyn experiment (40 runs). The large raw per-market CSVs of the later Python studies were lost when the cloud workspace was wiped; the numbers are in `docs/`, and the files are re-created by the commands below. The stability experiment (24 Robyn runs, ~9 h) is **built and tested on mock data but has not been run yet**; its slot is `robyn_experiment/stability/`.

---

## 1. The one-page summary (what the results say)

Full detail: **`docs/RESULTS_ALL_v3.md`** (one consolidated file). Short version:

1. **Weekly aggregation of media transforms biases contribution estimates when the true response is daily.** In the paper's own world, mean |bias| is about 24% (weekly) vs 15% (daily transform) vs 3% (oracle).
2. **The effect is conditional, not universal.** With correlated channels, seasonal confounding, time-varying effects, noisy KPIs or weekly-true processes, daily is no better and can be worse (multichannel study).
3. **Knowing the right frequency does not fix the total error.** In multichannel markets error is 15–30% for every arm, even with the true frequency known; the dominant error is estimating decay/saturation/shape.
4. **A practical check exists for the single-channel case.** The Vuong sign rule classifies "weekly-true vs daily-true" with balanced accuracy ≈ 0.976 on fresh seeds. It does **not** give a 95%-accurate "which arm is closer to the truth in *this* market" (ceiling ≈ 75–84%), and it fails the pre-registered bar per channel in multichannel models (0.83 pooled).
5. **Real Robyn (Meta, v3.12.1):** in the controlled experiment (16 markets, 3 channels, same data, same model, only the transform frequency changed), the daily transform arm was **not** better than the weekly arm (mean |total bias| A 43.2, B 50.5, C 45.7) and **every arm underestimates by about 40–50%**. The paper must concede this. Robyn's optimiser is not reproducible under the same seed, and its own convergence check failed on at least one criterion in 30 of 40 runs.
6. **Stability of that Robyn result** (is the A-vs-B difference bigger than run-to-run noise, and does doubling the optimisation budget matter?) is the pre-registered experiment in `robyn_experiment/stability/` — **pending**.

Every study had a design file written **before** the full run (`sims/DESIGN*.md`); failures are reported as failures.

---

## 2. Repository map

```
README.md                      <- you are here
requirements.txt               Python dependencies
docs/
  RESULTS_ALL_v3.md            ONE consolidated results file (Parts 1-4)
  results_by_study/            the separate write-ups per study
  phase1_design_freeze.md      original design freeze + deviation log (Aug 2026)
  SMOKE_TEST_LOG.md            what was run to verify this repo, and the outcome
  STATUS.md                    table: result present / must be regenerated / missing
sims/                          all Python simulation studies (flat on purpose, run from this folder)
  lib.py                       shared engine (data generators, estimators, seeds)
  DESIGN*.md                   pre-registered designs
  results/                     result files that exist (see STATUS.md)
  robyn_mc/                    the 16 simulated markets (daily + weekly CSV) + truth for the controlled Robyn experiment
  *.R / *.sh                   Robyn runners (R)
original_paper/                the original submission engine, real-data application, figures, tables
robyn_experiment/
  patch/                       the ONE change made to Meta's Robyn (patch file + full patched file)
  laptop_kit/                  one-command runner and README used on the Windows laptop
  stability/                   slot for the pending 24-run stability experiment
data_notes/DATA.md             data sources and licence flags
```

Why `sims/` is flat: the scripts import each other (`from lib import *`) and read/write `results/` and `robyn_mc/` relative to the folder they are run from. Always `cd sims` first.

---

## 3. Quick start (10 minutes, no Robyn needed)

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd sims
mkdir -p results

# 1. Re-create the controlled-Robyn markets and check they are IDENTICAL to the committed ones
python export_robyn_mc.py
git diff --stat robyn_mc            # should print nothing

# 2. Re-run the pre-declared analysis of the 40 real-Robyn runs (prints the A/B/C table)
python an_rxm.py results/RXM_laptop.csv       # should match results/RXM_analysis_output.txt exactly

# 3. Engine validation: single-channel limit must give ~weekly 24.6 / daily 15.5 / oracle 2.6
python mc_run.py valid
```
Every study also has a `smoke` mode that finishes in seconds (see table below).

---

## 4. Every study: design -> code -> command -> result

Run all commands from `sims/`. "Smoke" = seconds. Full runs use `joblib` on all cores; times depend on your machine (the multichannel engine ran at about 0.05 s per market and the selector engine at about 0.025 s per market on one core in the cloud runs).

| # | Study (paper / reviewer point) | Design (pre-registered) | Code | Run | Analysis | Result write-up |
|---|---|---|---|---|---|---|
| 0 | **Original paper**: media aggregation (Part A) + covariate disaggregation (Part B) | `docs/phase1_design_freeze.md` | `original_paper/paper_engine.py` | `cd original_paper && python download_datasets.py && python paper_engine.py` (full = about a day; set `SMOKE=True` in the file for minutes) | writes `results/*.csv` and 6 figures | `original_paper/results/` (included) |
| 0b | **Real-data application** (UK covariates, Kaggle media spends, Dunnhumby, Robyn demo) | `docs/phase1_design_freeze.md` | `original_paper/real_data_application.py`, `ridge_check.py` | `python real_data_application.py`, `python ridge_check.py` (from `original_paper/`) | writes `results_phase4/` | `original_paper/results_phase4/` (included) |
| 1 | Reviewer 1: time-varying effect, weekday, Robyn-style search; Reviewer 3: sub-daily, alternative DGPs | `DESIGN.md` | `s1_timevarying.py`, `s2_dow.py`, `s3_robynlike.py`, `s4_reviewer3.py` | `python s1_timevarying.py` / `python s2_dow.py` / `python s3_robynlike.py full` / `python s4_reviewer3.py 4a` and `4b` | CSV in `results/` | `docs/results_by_study/reviewer_response_simulation_results.md` |
| 2 | Shallow-saturation recovery | `DESIGN_RECOVERY.md` | `rec_run.py` | `python rec_run.py full` | (analysis script `an_rec.py` not recovered, see STATUS) | `docs/results_by_study/recovery_and_weekday_results.md` Part 1 |
| 3 | Targeted weekday test | `DESIGN_DOW2.md` | `s2b_dow_targeted.py` | `python s2b_dow_targeted.py full` | (`an_s2b.py` not recovered) | `recovery_and_weekday_results.md` Part 2 |
| 4 | Robyn-type engine (emulation of Robyn's search) | `DESIGN_ROBYN.md` | `rb_multi.py`, `rb_e2e_check.py` | `RBBUDGET=... python rb_multi.py full` | (`an_rb.py` not recovered) | `docs/RESULTS_ALL_v3.md` |
| 5 | **Selector study** (can a practitioner pick the frequency?) | `DESIGN_SELECTOR.md` | `sel_run.py`; `an_sel.py`, `an_sel2.py` | `python sel_run.py full` then `python sel_run.py conf`; `python an_sel.py`; `python an_sel2.py` | | `selector_study_results.md` |
| 6 | **Tests for the frequency** (T1-T5, Vuong, J, permutation) | `DESIGN_TESTS.md` | `sel_tests.py`, `an_tests.py`, `an_confirm.py`, `oracle_bound.py`, `freq_check.py` | `SELPREFIX=SELT python sel_tests.py full`; `SELPREFIX=SELU python sel_tests.py full`; `python an_tests.py results/TEST_SELT_full.csv results/TEST_SELU_full.csv`; `python an_confirm.py` | | `frequency_test_results.md` |
| 7 | **Multichannel study** (10 scenarios, stages A, B, C) | `DESIGN_MULTI.md` | `mc_run.py`, `mc_stageC.py`, `mc_oracle.py`, `an_mc.py` | `python mc_run.py A`; `python mc_run.py B`; `python mc_stageC.py C`; `python mc_oracle.py oracle`; `python mc_oracle.py sens`; `python an_mc.py A` (and B, C) | | `multichannel_study_results.md` |
| 8 | **Decision level** (budget reallocation, marginal ROI), sample length, multichannel shallow saturation | `DESIGN_DECISION.md` | `dec_run.py`, `dec_shallow.py`, `verify_dec.py`, `an_dec.py`, `an_dsh.py` | `python dec_run.py main <n_weeks> <n_markets>`; `python dec_run.py len <n_weeks> <n_markets>`; `python dec_shallow.py main 300`; `run_len.sh`, `run_len2.sh` queue them | | `docs/RESULTS_ALL_v3.md` Part 2 |
| 9 | **Real Robyn, 12 single-channel markets** | `DESIGN_ROBYN_REAL.md` | `export_robyn_markets.py`, `run_robyn_real.R`, `run_robyn_all.sh`, `an_rbreal.py` | needs Robyn (section 5) | `python an_rbreal.py` | `docs/RESULTS_ALL_v3.md` section 2.4; data `results/RBREAL_1000_full.csv` (included) |
| 10 | **Controlled real Robyn** (A weekly, B daily-transform-then-weekly, C daily) | `DESIGN_ROBYN_CONTROLLED.md` | `export_robyn_mc.py`, `run_robyn_mc.R`, `run_mc_queue.sh`, `an_rxm.py`, `test_patch_equiv.R` | needs Robyn (section 5) | `python an_rxm.py results/RXM_laptop.csv` | `docs/RESULTS_ALL_v3.md` section 2.5; data `results/RXM_laptop.csv` (included, 80 rows) |
| 11 | **Robyn stability** (noise vs budget effect) - **pending** | `DESIGN_ROBYN_STABILITY.md` | `run_stability.R`, `run_robyn_stab.R`, `stab_extract.R`, `an_stab.py` | `Rscript run_stability.R` (about 9 h) | `python an_stab.py results/RXM_laptop.csv results/RXM_stability.csv robyn_mc/truth_mc.csv` | not yet run |

Seeds are deterministic (`lib.seed_of`, md5 of the cell name), so a re-run reproduces the same simulated markets. **Robyn runs are the exception**: Nevergrad's search does not obey Robyn's seed, so re-runs differ slightly. That is itself a finding (section 2.5 of the results file).

---

## 5. Real-Robyn experiments (R)

What is Robyn here: Meta's open-source **Robyn 3.12.1** R code. The only change for the experiment is one switch inside `run_transformations` (Arm B). It is inactive unless the environment variable `ROBYN_DAILY_SPEND_FILE` is set, and with it unset Meta's code runs unchanged. The exact change is `robyn_experiment/patch/frequency_trap_arm_B.patch` (a pure addition, 67-line diff). `test_patch_equiv.R` is the equivalence test (block size 1 must reproduce standard Robyn exactly).

Build the patched library (about 10 minutes):

```bash
git clone https://github.com/facebookexperimental/Robyn.git robyn_src
cd robyn_src && git log -1 --format=%H     # the version used reports DESCRIPTION Version: 3.12.1
cp ../robyn_experiment/patch/transformation_patched_full.R R/R/transformation.R
cd .. && mkdir rlibB && R CMD INSTALL --no-docs -l rlibB robyn_src/R
```
Then follow `robyn_experiment/laptop_kit/README_LAPTOP.md` (it was written for the Windows laptop run; it says `RobynPatched`, which is the `robyn_src/R` folder above). In one command: copy `sims/` files next to `run_everything.R` and run `Rscript run_everything.R`.

Settings that were identical for every run (from `run_robyn_mc.R`): 3 channels, hyperparameter bounds alpha 0.5-3, gamma 0.05-1, theta 0.01-0.95, train size 0.5-0.9, validation on, TwoPointsDE, clustering off, Pareto front "auto", 2,000 iterations x 5 trials.

Things the reader must know (also in the design files):
- A vs B is a comparison of **two complete frequency-specific workflows** (theta per week vs per day, gamma relative to the weekly vs daily maximum, same numeric bounds). It does **not** isolate temporal aggregation alone.
- Robyn's convergence message describes the 5-trial run, not the selected model, and its two criteria (NRMSE, DECOMP.RSSD) are separate.
- The cloud runs used a minimal stand-in for Robyn's helper package `lares` (clustering off); the laptop kit installs the real `lares` from CRAN. Modelling code is unchanged either way.

### The pending stability experiment (24 runs, ~9 h)

Drop the output here: `sims/results/RXM_stability.csv` (+ `results/stab_pareto/`, `results/stab_manifest.csv`, session text file), then:

```bash
cd sims && python an_stab.py results/RXM_laptop.csv results/RXM_stability.csv robyn_mc/truth_mc.csv > results/RXM_stability_analysis.txt
```
Decision rule (fixed before running): median |budget shift| <= median |noise| = no material budget effect; median |shift| > 1.5 x median |noise| and |mean shift| > 2 SE = stability problem; otherwise inconclusive. Original results are never overwritten.

---

## 6. Reproducibility notes

- Python scripts were tested with Python 3.13, numpy 2.5, scipy 1.18, pandas 3.0, scikit-learn 1.9 (see `docs/SMOKE_TEST_LOG.md`).
- Metric everywhere: contribution bias % = 100 x (estimated - true) / true; "better" = paired mean difference > 2 Monte-Carlo SE.
- Not tuned after looking: thresholds and rules in `DESIGN_*.md` were fixed first; later changes are declared in the file itself (the notes added before or after a stage).
- Limits: simulated worlds are the author's constructions; one grid estimator for most studies; 156 weeks mostly; Robyn results are on 16 markets.

## 7. Not in this repo (on purpose)

The manuscript, section drafts and title page (confidential), the Dunnhumby data and PDF user guide (licence), and any API tokens.
