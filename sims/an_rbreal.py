"""Analysis of real-Robyn runs (DESIGN_ROBYN_REAL.md). All files with RBREAL in results/ are used; repeats are kept and flagged."""
import glob, numpy as np, pandas as pd
pd.set_option("display.width", 220)
tr = pd.read_csv("robyn_markets/truth.csv").set_index("market")
fs = ["results/RBREAL_1000.csv"] + sorted(glob.glob("results/RBREAL_1000_full.csv")) + sorted(glob.glob("results/RBREAL_rep*.csv"))
rows = []
for f in fs:
    d = pd.read_csv(f); d["file"] = f.split("/")[-1]; rows.append(d)
d = pd.concat(rows, ignore_index=True)
d["true"] = d.market.map(tr.true_total); d["bias"] = 100*(d.est_nrmse - d.true)/d.true; d["abias"] = d.bias.abs()
d["delta"] = d.market.map(tr.delta); d["shape"] = d.market.map(tr["shape"]); d["pattern"] = d.market.map(tr.pattern)
print("ALL RUNS (bias % of true contribution; estimate = model with lowest validation NRMSE)")
print(d[["file", "market", "interval", "est_nrmse", "true", "bias", "secs"]].round(1).to_string(index=False))
main = d[d.file == "RBREAL_1000_full.csv"]
p = main.pivot_table(index="market", columns="interval", values="abias"); p = p.dropna()
diff = (p["week"] - p["day"])
print(f"\nMAIN RUN (one run per market and frequency), n markets = {len(p)}")
print("mean |bias| weekly %.1f, daily %.1f; paired weekly-minus-daily %.1f (SE %.1f); daily better in %d of %d markets" % (p.week.mean(), p.day.mean(), diff.mean(), diff.std(ddof=1)/np.sqrt(len(diff)), (diff > 0).sum(), len(diff)))
sb = main.pivot_table(index="market", columns="interval", values="bias")
print("mean signed bias weekly %.1f, daily %.1f" % (sb.week.mean(), sb.day.mean()))
# run-to-run noise: markets with repeats at same frequency
rep = d.groupby(["market", "interval"]).bias.agg(["count", "mean", "std", "min", "max"]).query("count>1")
print("\nRUN-TO-RUN VARIATION (same market, same frequency, same seed argument, repeated runs):"); print(rep.round(1).to_string())
if len(rep): print("median within-cell SD of bias (points): %.1f" % rep["std"].median())
