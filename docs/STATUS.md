# What exists, what was regenerated, what is still to run

Updated 27 Nov 2026. Legend: **IN (original)** = file from the original runs, unchanged. **IN (regenerated 27 Nov)** = re-created with the committed code and fixed seeds on a 2-core container and checked against the numbers in `docs/`. **PENDING** = not run; needs Robyn or a long run on the author's machine.

## 1. Original results, unchanged
| Result | Where |
|---|---|
| Original paper: `partA_results.csv`, `partB_results.csv`, `tableA/B_paired.csv`, 6 figures | `original_paper/results/` |
| Real-data application `p4_*.csv`, 2 figures | `original_paper/results_phase4/` |
| Controlled real Robyn: `RXM_laptop.csv` (80 rows), `RXM_truth_mc.csv`, `RXM_analysis_output.txt` | `sims/results/` (reproduced exactly by `an_rxm.py`) |
| Real Robyn single-channel: `RBREAL_1000_full.csv` | `sims/results/` |
| 16 controlled-Robyn markets + `truth_mc.csv` | `sims/robyn_mc/` |

## 2. Regenerated 27 Nov 2026 (all in `sims/results/`)
| Study | Files | Check against docs |
|---|---|---|
| S1 time-varying | `S1_timevarying.csv` | matches (linear: weekly 21.6, daily 20.4) |
| S2 day-of-week | `S2_dow.csv` | no summary script; per-cell counts not re-checked |
| S3 Robyn-style emulation | `S3_full.csv` | matches (22.8 vs 31.5; 35.9 vs 42.4) |
| S4a / S4b Reviewer 3 | `S4a.csv`, `S4b.csv` | matches (e.g. weekly-true 16.5 vs 27.4) |
| S2b targeted weekday | `S2b_full.csv` | matches (A 23.9/20.6/12.1, B 22.3/29.1/13.3) |
| REC shallow saturation | `REC_full.csv` | matches (all G and X cells) |
| Selector | `SEL_full.csv`, `SEL_conf.csv` + `_analysis.txt` | analysis saved |
| Frequency tests | `TEST_SELT_full.csv`, `TEST_SELU_full.csv`, `TEST_analysis.txt`, `TEST_confirm_analysis.txt` | matches (zone 0.995, all markets 0.975) |
| Oracle bound | `ORACLE_bound_analysis.txt` | matches (0.996 / 0.989 / 0.999) |
| Multichannel A, B, C | `MC_{A,B,C}_markets.csv`, `MC_{A,B,C}_channels.csv`, `_analysis.txt` | C matches the doc table exactly; B matches (S1 up to 4.1, S2 up to 3.2) |
| Multichannel oracle, search sensitivity | `MC_oracle.csv`, `MC_sens.csv` + `_analysis.txt` | matches (0.968; sensitivity table) |
| Decision level | `DEC_main_156.csv`, `DEC_len_{78,156,260}.csv` + `_analysis.txt` | main table matches |
| Multichannel shallow saturation | `DSH_main.csv`, `DSH_main_analysis.txt` | analysis saved |
| Robyn-type engine (corrected) | `RB_full.csv`, `RB_e2e_check.csv` + `_analysis.txt` | matches the C2 table exactly; e2e -22.5 vs -37.3, corr 0.34 |
| Robyn-type engine, ridge bug (NOT used) | `RB_full_DISCARDED_ridge_scaling_bug.csv` | kept only as the record of the discarded run |
| Headline tables for studies without their own analysis script | `REGEN_check_analysis.txt` (from `an_regen_check.py`) | |

Two fixes made while regenerating:
- `rb_multi.py` in the repo was the version BEFORE the ridge-scaling fix (it reproduced the discarded run). The fix (`lambda / sd(y)`, as glmnet treats a user-supplied lambda) was re-applied; the corrected run reproduces the documented table to the decimal.
- README: stage B of the multichannel study must be run with `MCPREFIX=MCB`; without it, B is an exact copy of A.

## 2b. Robyn stability experiment, run 27-28 Nov 2026 on the author's laptop
`robyn_experiment/RXM_stability.csv`, `stab_manifest.csv`, `stability/` (24 runs x models, convergence, session), analysis `RXM_stability_analysis.txt` (`an_stab.py`).
Finding that breaks the pre-registered design: with seed 1 the 2,000-iteration repeat reproduces the original run EXACTLY (all 24 rows), so Robyn IS reproducible under a fixed seed and the noise unit N is 0. The pre-registered reading is therefore undefined (reported as INCONCLUSIVE). Run-to-run noise needs a repeat with different seeds.

## 3. Pending (run on the author's machine)
| Result | Why not run here |
|---|---|
| Full re-run of `original_paper/paper_engine.py` | about a day; results already IN, no re-run needed |
| Re-running any real-Robyn experiment (`run_robyn_real.R`, `run_robyn_mc.R`) | needs R + Robyn; results already IN |

## 4. Still missing (lost, not re-creatable from this repo)
`RBREAL_1000.csv`, `RBREAL_analysis.txt` (superseded by the `_full` run); helper scripts `an_rec.py`, `an_s2b.py`, `an_rb.py`, `rb_equivalence.py`, `an_s1.py` to `an_s4.py`, `an_tests2.py`, `ceiling.py`, `glmnet_scaling_check.R/.py`, `docs_extra/ROBYN_SETUP_NOTES.md`, `check_my_data.py`, `demo_check.py`. `an_regen_check.py` covers the headline tables of the first group.

## Verified
`docs/SMOKE_TEST_LOG.md` (16 Nov smoke tests) and the checks in section 2 above.
