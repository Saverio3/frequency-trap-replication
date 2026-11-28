# Robyn stability follow-up: independent seeds 2 and 3

## Why this follow-up is needed

The first stability batch is retained in `robyn_experiment/RXM_stability.csv`, `robyn_experiment/stab_manifest.csv`, and `robyn_experiment/stability/`. It is not discarded.

The first batch used seed argument 1 for the original 2,000-iteration run, the repeat 2,000-iteration run, and the 4,000-iteration run. The 2,000-iteration repeat reproduces the original estimates exactly in the recorded summary. Therefore that comparison is a same-seed reproducibility check, not an estimate of run-to-run variation across independent seeds. The 4,000-iteration results remain informative as a budget-sensitivity comparison under seed 1.

This follow-up adds seeds 2 and 3, each at both 2,000 and 4,000 iterations, for the same six selected markets and arms A/B. This gives three seed settings in total (1, 2, 3) and permits descriptive estimates of seed sensitivity at each budget plus within-seed budget shifts.

## Fixed scope

- Markets: 0, 2, 4, 7, 11, 13 (same selected markets as the first batch; selection was outcome-informed, so this remains a targeted stability analysis).
- Arms: A and B.
- Seeds: 2 and 3 added; seed 1 is the already completed batch.
- Optimisation budgets: 2,000 and 4,000 iterations, each with 5 trials.
- Selection rules: primary Robyn `error_score`; secondary validation `nrmse`.
- Same weekly data, model configuration, hyperparameter bounds, patched Robyn 3.12.1, Prophet settings and transformation implementation as the original experiment.
- 48 additional model runs (6 markets x 2 arms x 2 budgets x 2 new seeds), each run in its own GitHub Actions job. Each run writes the two selection-rule rows, full model table, convergence diagnostics, session information and a manifest.

The seed argument is recorded exactly. Because Nevergrad's internal randomisation may not be controlled solely by Robyn's seed argument, the outputs must be checked empirically: if seeds 1, 2 and 3 still produce identical or nearly identical model populations, do not claim that the extension measured independent optimiser randomness. Report exactly what the software produced.

## Analysis

Run:

```bash
python sims/an_stab_multiseed.py \
  robyn_experiment/RXM_stability.csv \
  combined-newseeds/RXM_stability_newseeds.csv \
  sims/robyn_mc/truth_mc.csv \
  combined-newseeds
```

The analysis reports:

1. Signed total-contribution bias by market, arm, rule, budget and seed.
2. Across-seed dispersion at 2,000 and 4,000 iterations.
3. Within-seed change from 2,000 to 4,000 iterations.
4. Whether the A-versus-B absolute-bias comparison changes across seeds and budgets.
5. Robyn's NRMSE and DECOMP.RSSD convergence flags separately.

This is descriptive, not a formal hypothesis test: there are only six selected markets, and they were selected based on the first experiment's outcomes. Do not interpret the six markets as an independent random sample of the full market population. Do not pool arms A and B when assessing seed variation or budget shifts.

## GitHub Actions execution

Workflow: `.github/workflows/robyn-stability-seed2.yml` (workflow display name: **Robyn stability — independent seeds 2 and 3**).

It is manually dispatched and creates 48 separate jobs. Each job uses a GitHub-hosted Ubuntu runner, installs R/Python dependencies, installs Robyn 3.12.1 with the repository's Arm B patch, runs exactly one market/arm/budget/seed cell, and uploads the full outputs. A final collection job checks that all 48 runs and their associated files arrived, then uploads the consolidated artifact.

The workflow defaults to 8 parallel jobs. It does not modify the original seed-1 results. A job has a six-hour timeout; failed jobs are not silently treated as completed. The collector deliberately fails its completeness check if any required output is missing.

## Interpretation and limitations

- The first batch was not wasted: it establishes the seed-1 baseline and the budget-4,000 comparison.
- The added seeds allow a much better assessment of sensitivity to the seed argument, provided the outputs actually differ.
- More iterations do not automatically mean better estimates. Compare truth bias, Pareto spread, and convergence flags; do not infer improvement from a lower validation NRMSE alone.
- A seed argument is not proof of independent optimiser randomness. Inspect the run outputs and session manifests.
- GitHub-hosted runners are not the user's laptop. The R version, operating system, numerical libraries and runtime environment will differ. The manifest/session files must be reported, and the result should be described as a replication on the GitHub runner environment, not as bit-for-bit laptop replication.
- This workflow uses the public repository's GitHub-hosted runners. The run is not a persistent computer left running unattended: each matrix cell is an isolated job, outputs are saved as workflow artifacts, and the jobs stop when complete or when their six-hour timeout is reached.
