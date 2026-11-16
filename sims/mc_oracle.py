"""(1) Oracle bound for per-channel frequency identification in the multichannel markets (known parameters, known other channels).
(2) Estimator-sensitivity check: more sweeps and restarts for fixed-assignment arms. Exploratory, declared as such."""
import sys, os, numpy as np, pandas as pd
from joblib import Parallel, delayed
from scipy.optimize import nnls
import mc_run as M
from mc_run import *

def market_ex(scen, m):
    rng = np.random.default_rng(seed_of(M.PREFIX, scen, m))
    cfg = scenario_config(scen, rng); K = cfg["K"]
    z = shared_z(rng); season_d = np.sin(2*np.pi*np.arange(ND)/(52*7))
    e = np.exp(0.5*z - 0.125) if cfg["tv"] else None
    spends, resps = [], []
    for k in range(K):
        s = gen_pattern(cfg["pats"][k], rng)*np.exp(cfg["kappa"][k]*z + cfg["season"]*season_d); spends.append(s)
        resps.append(true_resp(cfg["truths"][k], s, cfg["delta"][k], cfg["depth"][k], cfg["shape"][k], rng,
                               e=e if cfg["truths"][k] == "DAILY" else None, dip=cfg["dip"][k]))
    raw = np.array([cfg["shares"][k]*resps[k]/(resps[k].std() + 1e-9) for k in range(K)])
    t = np.arange(NW); base = 800 + .5*t + 30*np.sin(2*np.pi*t/52)
    c = base.std()/(raw.sum(0).std() + 1e-9); contrib = c*raw
    price = lfilter([np.sqrt(1 - .49)], [1, -.7], rng.normal(size=NW + 50))[50:]; price = (price - price.mean())/price.std()
    sig = contrib.sum(0); sd = np.sqrt(sig.var()*(1/cfg["r2"] - 1) + 1e-9)
    y = base + 40*price + sig + rng.normal(0, sd, NW)
    return cfg, np.array(spends), contrib, y, base + 40*price, c, sd, e

def oracle_rows(scen, m):
    cfg, spends, contrib, y, mu0, c, sd, e = market_ex(scen, m)
    ref = make_market(scen, m)
    assert np.allclose(ref[3], y) and np.allclose(ref[2], contrib)   # identical to the stage generator
    rng = np.random.default_rng(seed_of(M.PREFIX, "alt", scen, m)); K = cfg["K"]
    mu_true = mu0 + contrib.sum(0); rows = []
    for k in range(K):
        alt_truth = "DAILY" if cfg["truths"][k] == "WEEKLY" else "WEEKLY"
        ar = true_resp(alt_truth, spends[k], cfg["delta"][k], cfg["depth"][k], cfg["shape"][k], rng,
                       e=e if alt_truth == "DAILY" else None, dip=cfg["dip"][k])
        calt = c*cfg["shares"][k]*ar/(ar.std() + 1e-9)
        mu_alt = mu_true - contrib[k] + calt
        correct = ((y - mu_true)**2).sum() < ((y - mu_alt)**2).sum()
        rows.append(dict(scen=scen, m=m, k=k, truth=cfg["truths"][k], pattern=cfg["pats"][k], share=float(cfg["shares"][k]), oracle_ok=bool(correct)))
    return rows

# ---------------- sensitivity
def backfit_order(y, C, cands, assign, order, sweeps):
    K = len(assign); chosen = [None]*K
    for s in range(sweeps + 1):
        for k in order:
            Z = np.column_stack([C] + [chosen[j] for j in range(K) if j != k and chosen[j] is not None])
            _, chosen[k] = pick(y, Z, cands, k, assign[k])
    return chosen

def sse_final(y, C, cols):
    Q, _ = np.linalg.qr(C); yr = y - Q@(Q.T@y); A = np.array(cols); Ar = A - (A@Q)@Q.T
    b, _ = nnls(Ar.T, yr, maxiter=2000); r = yr - Ar.T@b; return float(r@r)

def sens_market(scen, m):
    cfg, spends, contrib, y, C = make_market(scen, m); K = cfg["K"]
    cands = {"w": [cand_set(spends[k], "w") for k in range(K)], "d": [cand_set(spends[k], "d") for k in range(K)]}
    truth_arm = ["w" if t == "WEEKLY" else "d" for t in cfg["truths"]]
    tt = contrib.sum(); out = dict(scen=scen, m=m)
    rng = np.random.default_rng(seed_of("sens", scen, m))
    for nm, assign in (("W", ["w"]*K), ("D", ["d"]*K), ("OF", truth_arm)):
        ch3 = backfit_order(y, C, cands, assign, list(range(K)), 3)
        out[f"{nm}_3"] = abs(100*(contribs(y, C, ch3).sum() - tt)/tt)
        best = None
        orders = [list(range(K)), list(range(K))[::-1]] + [list(rng.permutation(K)) for _ in range(3)]
        for o in orders:
            ch = backfit_order(y, C, cands, assign, o, 10); s = sse_final(y, C, ch)
            if best is None or s < best[0]: best = (s, ch)
        out[f"{nm}_best"] = abs(100*(contribs(y, C, best[1]).sum() - tt)/tt)
    return out

if __name__ == "__main__":
    which = sys.argv[1]
    if which == "oracle":
        jobs = [(s, m) for s in SCENS for m in range(1000)]
        res = Parallel(n_jobs=2, batch_size=20)(delayed(oracle_rows)(*j) for j in jobs)
        d = pd.DataFrame([r for rows in res for r in rows]); d.to_csv("results/MC_oracle.csv", index=False)
        print("oracle per-channel accuracy by scenario:\n", d.groupby("scen").oracle_ok.mean().round(3).loc[SCENS].to_dict())
        d["sbin"] = pd.cut(d.share, [0, .1, .3, 1.01])
        print("by share bin:", d.groupby("sbin", observed=True).oracle_ok.mean().round(3).to_dict())
        print("by pattern:", d.groupby("pattern").oracle_ok.mean().round(3).to_dict())
        print("pooled M1-M7,M10:", round(d[d.scen.isin(["M1","M2","M3","M4","M5","M6","M7","M10"])].oracle_ok.mean(), 3))
    else:
        jobs = [(s, m) for s in ["M1", "M2", "M3", "M7"] for m in range(250)]
        res = Parallel(n_jobs=2, batch_size=5, verbose=2)(delayed(sens_market)(*j) for j in jobs)
        d = pd.DataFrame(res); d.to_csv("results/MC_sens.csv", index=False)
        print(d.groupby("scen")[[c for c in d.columns if c not in ("scen", "m")]].mean().round(1))
