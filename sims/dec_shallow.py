"""Multichannel shallow-saturation study (DESIGN_DECISION.md, Part 3)."""
import sys, os, time
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from scipy.signal import lfilter
from lib import *
import mc_run as M
import dec_run as D
from mc_run import hill_s, gpct, gen_pattern, shared_z, scenario_config

PREFIX = "DSH"
MULT = {"x1": 1.0, "x3": 3.0, "x10": 10.0}

class ChTruthS(D.ChTruth):
    def _resp(self, s, g):
        # DAILY truth only in this study; depth x-multiples use max adstock of the ORIGINAL spend
        nw = self.nw; sp = self.spend*s
        a = adstock(sp, self.delta)
        if g is None:
            if self.depth in MULT: g = MULT[self.depth]*float(adstock(self.spend, self.delta).max())
            else: g = gpct(a, DEPTH_PCT[self.depth])
        return hill_s(a, g, self.shape).reshape(nw, 7).sum(1), g

def make_market_s(scen, m, nw=156):
    D._setnw(nw); NW, ND = nw, nw*7
    rng = np.random.default_rng(seed_of(PREFIX, scen, m))
    cfg = scenario_config("M1", rng); K = cfg["K"]
    pool = ["x1", "x3", "x10"] if scen == "M11" else ["mild", "med", "deep"]
    cfg["depth"] = [str(rng.choice(pool)) for _ in range(K)]
    z = shared_z(rng)
    spends, resps, chs = [], [], []
    for k in range(K):
        s = gen_pattern(cfg["pats"][k], rng)
        ch = ChTruthS("DAILY", s, cfg["delta"][k], cfg["depth"][k], cfg["shape"][k], rng, None, False, nw)
        spends.append(s); chs.append(ch); resps.append(ch.resp(1.0))
    raw = np.array([cfg["shares"][k]*resps[k]/(resps[k].std() + 1e-9) for k in range(K)])
    t = np.arange(NW); base = 800 + .5*t + 30*np.sin(2*np.pi*t/52)
    c = base.std()/(raw.sum(0).std() + 1e-9); contrib = c*raw
    consts = np.array([c*cfg["shares"][k]/(resps[k].std() + 1e-9) for k in range(K)])
    price = lfilter([np.sqrt(1 - .49)], [1, -.7], rng.normal(size=NW + 50))[50:]; price = (price - price.mean())/price.std()
    sig = contrib.sum(0)
    y = base + 40*price + sig + rng.normal(0, np.sqrt(sig.var()*(1/cfg["r2"] - 1) + 1e-9), NW)
    C = np.column_stack([np.ones(NW), t, np.sin(2*np.pi*t/52), np.cos(2*np.pi*t/52), price])
    return cfg, np.array(spends), contrib, y, C, chs, consts

def cand_set_x(spend, arm, nw, ext):
    sw = spend.reshape(nw, 7).sum(1); cols, meta = [], []
    for d in DEC_GRID:
        a = adstock(sw if arm == "w" else spend, d)
        gs = list(pct_nz(a, GAMMA_PCTS))
        if ext: gs += [mu*max(float(a.max()), 1e-9) for mu in (1, 3, 10, 30)]
        for g in gs:
            for h in H_GRID:
                mm = hill_s(a, g, h); cols.append(mm if arm == "w" else mm.reshape(nw, 7).sum(1)); meta.append((float(d), float(g), float(h)))
    return np.array(cols), meta

def run_market_s(scen, m, nw=156):
    cfg, spends, contrib, y, C, chs, consts = make_market_s(scen, m, nw); K = cfg["K"]
    S = spends.reshape(K, -1).sum(1)
    tf = D.make_true_fn(chs, consts); T1 = sum(tf(k, 1.0) for k in range(K)); tt = contrib.sum()
    mt = D.mroi(tf, K, S); inc_true = sum(tf(k, 2.0) - tf(k, 1.0) for k in range(K))
    opt_t = {bk: D.optimise(tf, K, S, lo, hi, seed_of(PREFIX, scen, m, "t", bk)) for bk, (lo, hi) in D.BOUNDS.items()}
    models = {}
    for grid, ext in (("G", False), ("X", True)):
        cands = {"w": [cand_set_x(spends[k], "w", nw, ext) for k in range(K)], "d": [cand_set_x(spends[k], "d", nw, ext) for k in range(K)]}
        for fr in ("w", "d"):
            a, ch, ix = D.backfit2(y, C, cands, [fr]*K, nw); b = D.coefs(y, C, ch)
            name = ("W" if fr == "w" else "D") + ("" if grid == "G" else "X")
            models[name] = (D.make_est_fn(spends, a, ix, b, cands), (b[:, None]*np.array(ch)).sum(), [cands[a[k]][k][1][ix[k]] for k in range(K)], b)
    bOT = D.coefs(y, C, list(contrib))
    models["OT"] = (D.make_ot_fn(chs, consts, bOT), (bOT[:, None]*contrib).sum(), None, bOT)
    rows = []
    for arm, (ef, csum, meta, b) in models.items():
        r = dict(scen=scen, nw=nw, m=m, K=K, arm=arm, bias=100*(csum - tt)/tt)
        me = D.mroi(ef, K, S); rel = np.abs(me - mt)/(np.abs(mt) + 1e-9)
        r["mroi_relerr_med"] = float(np.median(rel)); r["top_hit"] = float(np.argmax(me) == np.argmax(mt))
        inc = sum(ef(k, 2.0) - ef(k, 1.0) for k in range(K)); r["extrap_err"] = 100*(inc - inc_true)/inc_true
        r["share_shallow"] = float(np.mean([d in MULT for d in cfg["depth"]]))
        for bk, (lo, hi) in D.BOUNDS.items():
            s_e = D.optimise(ef, K, S, lo, hi, seed_of(PREFIX, scen, m, arm, bk))
            Te = sum(tf(k, s_e[k]) for k in range(K)); Tt = sum(tf(k, opt_t[bk][k]) for k in range(K))
            r[f"loss_{bk}"] = 100*(Tt - Te)/T1; r[f"gstar_{bk}"] = 100*(Tt - T1)/T1; r[f"gest_{bk}"] = 100*(Te - T1)/T1
        rows.append(r)
    return rows

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "smoke":
        t0 = time.time()
        for sc in ["M11", "M11c"]:
            for m in range(3): rows = run_market_s(sc, m)
        print("s/market", (time.time() - t0)/6); print(pd.DataFrame(rows).round(2).T.to_string()); sys.exit(0)
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    jobs = [(s, m) for s in ["M11", "M11c"] for m in range(n)]
    print("markets", len(jobs), flush=True); t0 = time.time()
    out = Parallel(n_jobs=2, batch_size=4, verbose=5)(delayed(run_market_s)(*j) for j in jobs)
    pd.DataFrame([r for o in out for r in o]).to_csv("results/DSH_main.csv", index=False)
    print("done", round(time.time() - t0), "s", flush=True)
