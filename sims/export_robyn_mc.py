"""Export 16 simulated 3-channel markets (daily and weekly versions of the SAME data) for the controlled real-Robyn experiment.
Design: DESIGN_ROBYN_CONTROLLED.md. Daily KPI = baseline/7 + sum of channel daily responses + daily noise; weekly KPI = sum of 7 days exactly.
Writes robyn_mc/market_XX_daily.csv, _weekly.csv and truth_mc.csv."""
import os, numpy as np, pandas as pd
import mc_run as M
from mc_run import hill_s, gpct, gen_pattern, shared_z, scenario_config
from lib import seed_of, adstock, DEPTH_PCT
NW, ND = 156, 1092; os.makedirs("robyn_mc", exist_ok=True)
TYPES = {0: "M1", 1: "M1", 2: "M2", 3: "M3"}; rows = []
for i in range(16):
    scen = TYPES[i % 4]; rng = np.random.default_rng(seed_of("RXM", i)); cfg = scenario_config(scen, rng); K = cfg["K"]; z = shared_z(rng)
    spends, rdaily, rweek = [], [], []
    for k in range(K):
        s = gen_pattern(cfg["pats"][k], rng)*np.exp(cfg["kappa"][k]*z)
        if cfg["truths"][k] == "WEEKLY":
            a = adstock(s.reshape(NW, 7).sum(1), cfg["delta"][k]); g = gpct(a, DEPTH_PCT[cfg["depth"][k]]); rw = hill_s(a, g, cfg["shape"][k]); rd = np.repeat(rw/7, 7)
        else:
            a = adstock(s, cfg["delta"][k]); g = gpct(a, DEPTH_PCT[cfg["depth"][k]]); rd = hill_s(a, g, cfg["shape"][k]); rw = rd.reshape(NW, 7).sum(1)
        spends.append(s); rdaily.append(rd); rweek.append(rw)
    t = np.arange(NW); base = 800 + .5*t + 30*np.sin(2*np.pi*t/52)
    raw = np.array([cfg["shares"][k]*rweek[k]/(rweek[k].std() + 1e-9) for k in range(K)]); c = base.std()/(raw.sum(0).std() + 1e-9)
    cw = c*raw                                                                         # weekly contributions (K, NW)
    cd = np.array([c*cfg["shares"][k]*rdaily[k]/(rweek[k].std() + 1e-9) for k in range(K)])   # daily contributions (K, ND)
    assert np.allclose(cd.reshape(K, NW, 7).sum(2), cw)
    sig = cw.sum(0); sd_w = np.sqrt(sig.var()*(1/0.85 - 1))
    yd = np.repeat(base/7, 7) + cd.sum(0) + rng.normal(0, sd_w/np.sqrt(7), ND)
    dates = pd.date_range("2022-01-03", periods=ND)
    dd = pd.DataFrame({"DATE": dates.strftime("%Y-%m-%d"), "revenue": yd}); wk = pd.DataFrame({"DATE": dates[::7].strftime("%Y-%m-%d"), "revenue": yd.reshape(NW, 7).sum(1)})
    for k in range(K):
        dd[f"ch{k+1}"] = spends[k]; wk[f"ch{k+1}"] = spends[k].reshape(NW, 7).sum(1)
    dd.to_csv(f"robyn_mc/market_{i:02d}_daily.csv", index=False); wk.to_csv(f"robyn_mc/market_{i:02d}_weekly.csv", index=False)
    r = dict(market=i, type={"M1": "independent", "M2": "correlated", "M3": "mixed"}[scen])
    for k in range(K):
        r.update({f"true_ch{k+1}": float(cw[k].sum()), f"truth_ch{k+1}": cfg["truths"][k], f"pat_ch{k+1}": cfg["pats"][k], f"delta_ch{k+1}": cfg["delta"][k],
                  f"depth_ch{k+1}": cfg["depth"][k], f"shape_ch{k+1}": cfg["shape"][k], f"share_ch{k+1}": float(cfg["shares"][k])})
    r["true_total"] = float(cw.sum()); rows.append(r)
pd.DataFrame(rows).to_csv("robyn_mc/truth_mc.csv", index=False); print("markets", len(rows)); print(pd.DataFrame(rows)[["market", "type", "true_total", "truth_ch1", "truth_ch2", "truth_ch3"]].to_string())
