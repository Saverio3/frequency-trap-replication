"""End-to-end check: does the Robyn-type engine (rb_multi.Engine, weekly transform, single objective) reproduce the REAL Robyn weekly runs
on the SAME 12 single-channel markets? Controls: trend + annual sin/cos (stand-in for Prophet trend/season). 1000 iterations, 5 repeat searches per market."""
import os; os.environ["RBBUDGET"] = "1000"
import numpy as np, pandas as pd
import rb_multi as R
tr = pd.read_csv("robyn_markets/truth.csv").set_index("market")
real = pd.read_csv("results/RBREAL_1000_full.csv"); real["true"] = real.market.map(tr.true_total); real["bias"] = 100*(real.est_nrmse - real.true)/real.true
rows = []
for m in [0, 4, 6, 10, 12, 16, 18, 22, 24, 28, 30, 34]:
    dd = pd.read_csv(f"robyn_markets/market_{m:02d}_daily.csv"); ww = pd.read_csv(f"robyn_markets/market_{m:02d}_weekly.csv")
    sp = dd.spend_ch.values[None, :]; y = ww.revenue.values; t = np.arange(156)
    C = np.column_stack([np.ones(156), t, np.sin(2*np.pi*t/52), np.cos(2*np.pi*t/52)])
    for fr in ("W",):
        eng = R.Engine(sp, y, C, fr)
        for rep in range(5):
            X, F = R.search(eng, 1000 + rep, multi=False); j = int(np.argmin(F[:, 0]))
            est = eng.contribution(X[j]).sum()
            rows.append(dict(market=m, rep=rep, est=est, bias=100*(est - tr.true_total[m])/tr.true_total[m]))
d = pd.DataFrame(rows); s = d.groupby("market").bias.agg(["mean", "std"]).rename(columns={"mean": "engine_mean", "std": "engine_sd"})
rw = real[(real.interval == "week")].groupby("market").bias.mean().rename("real_robyn_weekly")
out = s.join(rw); print(out.round(1).to_string())
print("mean bias: engine %.1f, real Robyn %.1f; correlation across markets %.2f; mean |difference| %.1f" % (out.engine_mean.mean(), out.real_robyn_weekly.mean(), out.engine_mean.corr(out.real_robyn_weekly), (out.engine_mean - out.real_robyn_weekly).abs().mean()))
d.to_csv("results/RB_e2e_check.csv", index=False)
