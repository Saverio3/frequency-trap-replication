# What exists, what must be regenerated, what is missing

Legend: **IN** = file is in this repo. **REGEN** = re-create with the command in the README (deterministic seeds). **MISSING** = was lost when the cloud workspace was wiped; ask the author (these were also delivered to him earlier in `frequency_trap_pack`).

## Results files
| Result | Status |
|---|---|
| Original paper: `partA_results.csv`, `partB_results.csv`, `tableA/B_paired.csv`, 6 figures | IN (`original_paper/results/`) |
| Real-data application `p4_*.csv`, 2 figures | IN (`original_paper/results_phase4/`) |
| Controlled real Robyn: `RXM_laptop.csv` (80 rows), `RXM_truth_mc.csv`, `RXM_analysis_output.txt` | IN (`sims/results/`) and reproduced exactly by `an_rxm.py` |
| Real Robyn single-channel: `RBREAL_1000_full.csv` | IN |
| Real Robyn single-channel first attempt `RBREAL_1000.csv`, `RBREAL_analysis.txt` | MISSING (superseded by the `_full` run) |
| Per-market CSVs of the Python studies: `S1..S4`, `S2b_full`, `REC_full`, `SEL_*`, `TEST_SELT/SELU_full`, `MC_*`, `MC_sens`, `MC_oracle`, `DEC_*`, `DSH_main`, `RB_*` | REGEN (commands in README section 4) - the summary numbers are in `docs/` |
| Stability experiment `RXM_stability.csv`, `stab_pareto/`, `stab_manifest.csv` | **NOT RUN YET** |
| Consolidated numbers | IN: `docs/RESULTS_ALL_v3.md`, `docs/results_by_study/*.md` |

## Code lost from the workspace (analysis helpers and notes)
`an_rec.py`, `an_s2b.py`, `an_rb.py`, `rb_equivalence.py`, `an_s1.py` to `an_s4.py`, `an_tests2.py`, `ceiling.py`, `glmnet_scaling_check.R/.py`, `docs_extra/ROBYN_SETUP_NOTES.md`, `check_my_data.py`, `demo_check.py`. The simulation and analysis scripts for the headline claims are present; these are secondary analyses. If you have the earlier `frequency_trap_pack` zip, copy them into `sims/`.

## Verified
`docs/SMOKE_TEST_LOG.md`.
