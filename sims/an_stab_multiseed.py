"""Descriptive multi-seed follow-up for the Robyn stability experiment.

Usage:
  python sims/an_stab_multiseed.py \
    robyn_experiment/RXM_stability.csv \
    combined-newseeds/RXM_stability_newseeds.csv \
    sims/robyn_mc/truth_mc.csv \
    combined-newseeds
Seed 1 is the already completed original stability run. Seeds 2 and 3 are the
independent-seed extension. No files from the original run are overwritten.
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd

if len(sys.argv) < 4:
    raise SystemExit(__doc__)
seed1_path, new_path, truth_path = map(Path, sys.argv[1:4])
outdir = Path(sys.argv[4]) if len(sys.argv) > 4 else new_path.parent
outdir.mkdir(parents=True, exist_ok=True)

MARKETS = [0, 2, 4, 7, 11, 13]
ARMS = ["A", "B"]
RULES = ["errscore", "nrmse"]

s1 = pd.read_csv(seed1_path)
new = pd.read_csv(new_path)
truth = pd.read_csv(truth_path).set_index("market")
required = {"market", "arm", "tag", "rule", "est_total", "nrmse_converged", "rssd_converged"}
for label, frame in [("seed1", s1), ("new seeds", new)]:
    missing = required - set(frame.columns)
    if missing:
        raise SystemExit(f"{label} file missing columns: {sorted(missing)}")

s1 = s1[s1.market.isin(MARKETS) & s1.arm.isin(ARMS)].copy()
s1["seed"] = 1
s1["budget"] = s1["tag"].map({"rep2000": 2000, "inc4000": 4000})
new = new[new.market.isin(MARKETS) & new.arm.isin(ARMS)].copy()
new["seed"] = new["tag"].str.extract(r"seed(\\d+)_")[0].astype(int)
new["budget"] = new["tag"].str.extract(r"_(rep|inc)(\\d+)")[1].astype(float).astype("Int64")
d = pd.concat([s1, new], ignore_index=True)
d = d[d.budget.isin([2000, 4000])].copy()
d["true_total"] = d.market.map(truth.true_total)
if d.true_total.isna().any():
    raise SystemExit("Truth table is missing one or more selected markets.")
d["bias_pct"] = 100 * (d.est_total - d.true_total) / d.true_total
d["abs_bias_pct"] = d.bias_pct.abs()

keys = ["seed", "market", "arm", "budget", "rule"]
if d.duplicated(keys).any():
    raise SystemExit("Duplicate seed/market/arm/budget/rule rows detected.")
expected = len(MARKETS) * len(ARMS) * len(RULES) * 3 * 2
if len(d) != expected:
    raise SystemExit(f"Expected {expected} summary rows (3 seeds x 2 budgets x 6 markets x 2 arms x 2 rules); got {len(d)}.")
d.to_csv(outdir / "multiseed_bias_long.csv", index=False)

lines = []
def emit(s=""):
    print(s)
    lines.append(str(s))

emit("ROB YN MULTI-SEED STABILITY FOLLOW-UP".replace("ROB YN", "ROBYN"))
emit("Seeds 1, 2, 3; markets 0, 2, 4, 7, 11, 13; arms A/B; 2,000 and 4,000 iterations x 5 trials.")
emit("Descriptive analysis only: six selected markets, not a representative sample of all simulated markets.")
emit("")

for rule in RULES:
    x = d[d.rule == rule]
    emit(f"===== {rule.upper()} ({'PRIMARY' if rule == 'errscore' else 'SECONDARY'}) =====")
    for budget in [2000, 4000]:
        w = x[x.budget == budget].pivot_table(index=["market", "arm"], columns="seed", values="bias_pct")
        emit(f"\nSigned bias (%) at {budget:,} iterations; columns are seeds:")
        emit(w.reindex(columns=[1, 2, 3]).round(1).to_string())
        cell_sd = w.std(axis=1, ddof=1)
        emit(f"Across-seed SD of signed bias: median={cell_sd.median():.2f} pp; mean={cell_sd.mean():.2f} pp; max={cell_sd.max():.2f} pp.")
        seed_range = w.max(axis=1) - w.min(axis=1)
        emit(f"Across-seed range: median={seed_range.median():.2f} pp; max={seed_range.max():.2f} pp.")

    shifts = x.pivot_table(index=["seed", "market", "arm"], columns="budget", values="bias_pct")
    shifts["budget_shift_pp"] = shifts[4000] - shifts[2000]
    emit("\nWithin-seed budget shift = bias(4,000) minus bias(2,000), percentage points:")
    emit(shifts["budget_shift_pp"].unstack("seed").round(1).to_string())
    for seed, group in shifts.groupby(level="seed"):
        v = group.budget_shift_pp
        emit(f"Seed {seed}: median |budget shift|={v.abs().median():.2f} pp; mean signed shift={v.mean():+.2f} pp; max |shift|={v.abs().max():.2f} pp.")

    emit("\nA minus B in absolute bias (positive means B has lower absolute bias):")
    for seed in [1, 2, 3]:
        for budget in [2000, 4000]:
            z = x[(x.seed == seed) & (x.budget == budget)].pivot(index="market", columns="arm", values="abs_bias_pct")
            diff = z["A"] - z["B"]
            emit(f"Seed {seed}, {budget:,}: mean A-B={diff.mean():+.2f} pp; B better in {(diff > 0).sum()}/6 markets; market values {diff.round(1).to_dict()}")

    emit("\nConvergence counts (primary/secondary selected rows; each row records run-level flags):")
    conv = x.drop_duplicates(["seed", "market", "arm", "budget"])
    emit(pd.crosstab([conv.seed, conv.budget], [conv.nrmse_converged, conv.rssd_converged]).to_string())
    emit("")

analysis = "\n".join(lines) + "\n"
(outdir / "multiseed_analysis.txt").write_text(analysis, encoding="utf-8")
print(f"\nWrote {outdir / 'multiseed_bias_long.csv'} and {outdir / 'multiseed_analysis.txt'}")
