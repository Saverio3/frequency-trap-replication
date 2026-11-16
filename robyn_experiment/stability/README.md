# Stability experiment (pending)

Design (pre-registered, do not edit after running): `../../sims/DESIGN_ROBYN_STABILITY.md`.
Code: `sims/run_stability.R` (one command), `run_robyn_stab.R`, `stab_extract.R`, analysis `an_stab.py`.

24 runs = 6 markets (0, 2, 4, 7, 11, 13) x arms A and B x (12 repeats at 2,000 iterations x 5 trials + 12 at 4,000 x 5). About 9 hours on a laptop. Saves the full Pareto set, the selected model's rank, both convergence criteria separately, all configs and seeds. Never touches `RXM_laptop.csv`.

When the run finishes, put these here (or in `sims/results/`):
- `RXM_stability.csv`, `stab_manifest.csv`, `stab_pareto/`, the session text file
- the output of `python an_stab.py ...` (see top-level README section 5)
