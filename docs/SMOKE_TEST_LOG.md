# Smoke-test log (run 16 Nov 2026, 2-core cloud container)

Python 3.13.18, numpy 2.5.3, scipy 1.18.1, pandas 3.0.5, scikit-learn 1.9.1.
Each command was run from a scratch copy of `sims/` (so this repo was not changed by the test). "smoke" modes are tiny runs: they prove the code runs end to end, **not** that the full results were re-obtained.

| Command | Result | Time |
|---|---|---|
| `python export_robyn_mc.py` | PASS | 1s |
| `python export_robyn_markets.py` | PASS | 2s |
| `python mc_run.py smoke` | PASS | 4s |
| `python mc_run.py valid` | PASS | 3s |
| `python dec_run.py valid` | PASS | 6s |
| `python dec_run.py smoke` | PASS | 3s |
| `python dec_shallow.py smoke` | PASS | 2s |
| `python rec_run.py smoke` | PASS | 3s |
| `python s2b_dow_targeted.py smoke` | PASS | 2s |
| `python sel_run.py smoke` | PASS | 4s |
| `python sel_tests.py smoke` | PASS | 6s |
| `python s1_timevarying.py smoke` | PASS | 5s |
| `python s2_dow.py smoke` | PASS | 6s |
| `python s4_reviewer3.py 4a smoke` | PASS | 4s |
| `python s4_reviewer3.py 4b smoke` | PASS | 3s |
| `python verify_dec.py` | PASS | 67s |
| `python an_rxm.py results/RXM_laptop.csv` | PASS | 1s |
| `python s3_robynlike.py smoke` (after `pip install nevergrad`) | PASS | 85s |
| `python rb_multi.py smoke` (after `pip install nevergrad`) | PASS | 47s |

## Reproducibility checks that compare against saved results
- `python export_robyn_mc.py` regenerated all 16 market pairs and `truth_mc.csv` **identical** to the committed files (`diff -r` empty). This also confirms the committed `lib.py` and `mc_run.py` are the ones that produced the data used in the laptop Robyn run.
- `python export_robyn_markets.py` regenerated 36 single-channel markets; the last rows of `truth.csv` equal those recorded in the session (market 33: 50136.493956148886, 34: 8308.740920797969, 35: 7582.918041266568).
- `python an_rxm.py results/RXM_laptop.csv` output is **identical** to the saved `RXM_analysis_output.txt`.
- `python mc_run.py valid` (100 single-channel markets): mean |bias| weekly **24.6**, daily **15.5**, oracle transform **2.6** - exactly the values recorded in `DESIGN_MULTI.md` (paper: 24.0 / 15.2 / 2.7). `python dec_run.py valid` also ran; `verify_dec.py`: 64 allocations checked, the SLSQP optimiser was never beaten by random search (max gap 0.0000%).

## Not tested here
R / Robyn scripts (no Robyn installed in this container; they were run on the author's laptop and in an earlier cloud workspace), `original_paper/paper_engine.py` full run (about a day), the stability scripts on real Robyn (tested on mock data only), and all full-size Python runs.
