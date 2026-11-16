"""Decision-level and sample-length study (design: DESIGN_DECISION.md, fixed before running).
Uses the multichannel generator of mc_run.py (same RNG call order) with the number of weeks as a parameter,
keeps the fitted transform parameters of every arm, and scores marginal ROI and budget reallocation against the truth."""
import sys, os, time
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from scipy.optimize import nnls, minimize
from scipy.signal import lfilter
from lib import *
import mc_run as M
from mc_run import hill_s, gpct, gen_pattern, shared_z, scenario_config, vuong, _best

PREFIX = os.environ.get("DECPREFIX", "DEC")
BOUNDS = {"P": (0.5, 2.0), "S": (0.8, 1.25)}

def _setnw(nw):
    M.NW = nw; M.ND = nw*7

# ------------------------------------------------------------ truth
class ChTruth:
    def __init__(self, truth, spend, delta, depth, shape, rng, e, dip, nw):
        self.truth, self.spend, self.delta, self.shape, self.e, self.dip, self.nw = truth, spend, delta, shape, e, dip, nw
        self.P = rng.dirichlet(np.full(4, 0.3), nw*7) if truth == "SUB" else None   # same single draw as mc_run.true_resp
        self.g = None
        self.depth = depth
        r, g = self._resp(1.0, None); self.g = g
    def _resp(self, s, g):
        nw = self.nw; sp = self.spend*s
        if self.truth == "WEEKLY":
            a = adstock(sp.reshape(nw, 7).sum(1), self.delta)
            g = gpct(a, DEPTH_PCT[self.depth]) if g is None else g
            return hill_s(a, g, self.shape), g
        if self.truth == "SUB":
            sf = (sp[:, None]*self.P).reshape(-1)
            a = adstock(sf, self.delta**(1.0/4)); g = gpct(a, DEPTH_PCT[self.depth]) if g is None else g
            return hill_s(a, g, self.shape).reshape(nw, 28).sum(1), g
        a = adstock(sp, self.delta); g = gpct(a, DEPTH_PCT[self.depth]) if g is None else g
        r = hill_s(a, g, self.shape)
        if self.e is not None: r = r*self.e
        if self.dip:
            ma = lfilter(np.ones(14)/14, [1.0], r); ma = np.concatenate([[0.0], ma[:-1]]); r = r - 0.3*ma
        return r.reshape(nw, 7).sum(1), g
    def resp(self, s):
        return self._resp(s, self.g)[0]

def make_market2(scen, m, nw, prefix):
    _setnw(nw); NW, ND = nw, nw*7
    rng = np.random.default_rng(seed_of(prefix, scen, m))
    cfg = scenario_config(scen, rng); K = cfg["K"]
    z = shared_z(rng)
    season_d = np.sin(2*np.pi*np.arange(ND)/(52*7))
    e = np.exp(0.5*z - 0.125) if cfg["tv"] else None
    spends, resps, chs = [], [], []
    for k in range(K):
        s = gen_pattern(cfg["pats"][k], rng)*np.exp(cfg["kappa"][k]*z + cfg["season"]*season_d)
        spends.append(s)
        ch = ChTruth(cfg["truths"][k], s, cfg["delta"][k], cfg["depth"][k], cfg["shape"][k], rng,
                     e if cfg["truths"][k] == "DAILY" else None, cfg["dip"][k], nw)
        chs.append(ch); resps.append(ch.resp(1.0))
    raw = np.array([cfg["shares"][k]*resps[k]/(resps[k].std() + 1e-9) for k in range(K)])
    t = np.arange(NW); base = 800 + .5*t + 30*np.sin(2*np.pi*t/52)
    c = base.std()/(raw.sum(0).std() + 1e-9)
    contrib = c*raw
    consts = np.array([c*cfg["shares"][k]/(resps[k].std() + 1e-9) for k in range(K)])
    price = lfilter([np.sqrt(1 - .49)], [1, -.7], rng.normal(size=NW + 50))[50:]; price = (price - price.mean())/price.std()
    sig = contrib.sum(0)
    y = base + 40*price + sig + rng.normal(0, np.sqrt(sig.var()*(1/cfg["r2"] - 1) + 1e-9), NW)
    C = np.column_stack([np.ones(NW), t, np.sin(2*np.pi*t/52), np.cos(2*np.pi*t/52), price])
    return cfg, np.array(spends), contrib, y, C, chs, consts

# ------------------------------------------------------------ estimators (with parameters kept)
def cand_set2(spend, arm, nw):
    sw = spend.reshape(nw, 7).sum(1); cols, meta = [], []
    for d in DEC_GRID:
        a = adstock(sw if arm == "w" else spend, d)
        for g in pct_nz(a, GAMMA_PCTS):
            for h in H_GRID:
                mm = hill_s(a, g, h); cols.append(mm if arm == "w" else mm.reshape(nw, 7).sum(1)); meta.append((float(d), float(g), float(h)))
    return np.array(cols), meta

def pick2(y, Z, cands, k, mode, nw):
    Q, _ = np.linalg.qr(Z); yr = y - Q@(Q.T@y); yy = yr@yr
    out = {}
    for arm in ("w", "d"):
        if mode in (arm, "sel"):
            Mx = cands[arm][k][0]; Mr = Mx - (Mx@Q)@Q.T
            kk, sse, res = _best(yr, Mr, yy); out[arm] = (kk, sse, res)
    if mode == "sel":
        z = vuong(out["w"][2], out["w"][1], out["d"][2], out["d"][1], nw); arm = "d" if z > 0 else "w"
    else:
        arm = mode
    return arm, cands[arm][k][0][out[arm][0]], out[arm][0]

def backfit2(y, C, cands, assign, nw, sweeps=3):
    K = len(assign); chosen = [None]*K; arms = list(assign); idx = [None]*K
    for s in range(sweeps + 1):
        for k in range(K):
            Z = np.column_stack([C] + [chosen[j] for j in range(K) if j != k and chosen[j] is not None])
            arms[k], chosen[k], idx[k] = pick2(y, Z, cands, k, assign[k], nw)
    return arms, chosen, idx

def coefs(y, C, cols):
    Q, _ = np.linalg.qr(C); yr = y - Q@(Q.T@y)
    Mx = np.array(cols); Mr = Mx - (Mx@Q)@Q.T
    b, _ = nnls(Mr.T, yr, maxiter=2000)
    return b

# ------------------------------------------------------------ counterfactual functions
def make_est_fn(spends, arms, idx, b, cands):
    K = len(arms)
    def f_k(k, s):
        if b[k] <= 0: return 0.0
        d, g, h = cands[arms[k]][k][1][idx[k]]
        sp = spends[k]*s
        if arms[k] == "w":
            a = adstock(sp.reshape(-1, 7).sum(1), d)
        else:
            a = adstock(sp, d)
        return float(b[k]*hill_s(a, g, h).sum())
    return f_k

def make_true_fn(chs, consts):
    def f_k(k, s):
        return float(consts[k]*chs[k].resp(s).sum())
    return f_k

def make_ot_fn(chs, consts, b):
    def f_k(k, s):   # OT: true transform columns were contrib = consts*resp; coefficient b multiplies that column
        return float(b[k]*consts[k]*chs[k].resp(s).sum())
    return f_k

def mroi(fk, K, S):
    out = []
    for k in range(K):
        out.append((fk(k, 1.01) - fk(k, 1.0))/(0.01*S[k]))
    return np.array(out)

def optimise(fk, K, S, lo, hi, seed):
    tot = S.sum(); base = sum(fk(k, 1.0) for k in range(K)); scale = base if base > 1e-9 else 1.0
    fun = lambda s: -sum(fk(k, s[k]) for k in range(K))/scale
    cons = [{"type": "eq", "fun": lambda s: (s@S - tot)/tot}]
    rng = np.random.default_rng(seed)
    starts = [np.ones(K)]
    for _ in range(1):
        v = rng.uniform(lo, hi, K) - 1.0; v = v - (v@S/(S@S))*S
        th = 1.0
        for i in range(K):
            if v[i] > 1e-12: th = min(th, (hi - 1)/v[i])
            if v[i] < -1e-12: th = min(th, (lo - 1)/v[i])
        starts.append(np.clip(1 + 0.9*th*v, lo, hi))
    best = None
    for x0 in starts:
        try:
            r = minimize(fun, x0, method="SLSQP", bounds=[(lo, hi)]*K, constraints=cons, options=dict(maxiter=60, ftol=1e-10, eps=1e-4))
        except Exception:
            continue
        s = np.clip(r.x, lo, hi)
        if abs(s@S - tot)/tot > 1e-4:   # infeasible result: project back by scaling toward 1
            continue
        val = -fun(s)
        if best is None or val > best[0]: best = (val, s)
    if best is None: return np.ones(K)
    return best[1]

# ------------------------------------------------------------ one market
def run_market(scen, m, nw, prefix=PREFIX):
    cfg, spends, contrib, y, C, chs, consts = make_market2(scen, m, nw, prefix); K = cfg["K"]
    cands = {"w": [cand_set2(spends[k], "w", nw) for k in range(K)], "d": [cand_set2(spends[k], "d", nw) for k in range(K)]}
    truth_arm = ["w" if t == "WEEKLY" else "d" for t in cfg["truths"]]
    fits = {}
    a, ch, ix = backfit2(y, C, cands, ["w"]*K, nw); fits["W"] = (a, ix, coefs(y, C, ch), ch)
    a, ch, ix = backfit2(y, C, cands, ["d"]*K, nw); fits["D"] = (a, ix, coefs(y, C, ch), ch)
    a, ch, ix = backfit2(y, C, cands, ["sel"]*K, nw); fits["S1"] = (a, ix, coefs(y, C, ch), ch)
    a, ch, ix = backfit2(y, C, cands, truth_arm, nw); fits["OF"] = (a, ix, coefs(y, C, ch), ch)
    bOT = coefs(y, C, list(contrib))
    S = spends.reshape(K, -1).sum(1)
    tf = make_true_fn(chs, consts)
    T1 = sum(tf(k, 1.0) for k in range(K)); tt = contrib.sum()
    mt = mroi(tf, K, S)
    opt_t = {}
    if K > 1:
        for bk, (lo, hi) in BOUNDS.items():
            opt_t[bk] = optimise(tf, K, S, lo, hi, seed_of(prefix, scen, m, "t", bk))
    rows = []
    for arm in ["W", "D", "S1", "OF", "OT"]:
        if arm == "OT":
            ef = make_ot_fn(chs, consts, bOT); tot_est = sum(ef(k, 1.0) for k in range(K)); arms_used = truth_arm
            cols_sum = (bOT[:, None]*contrib).sum()
        else:
            arms_used, ix, b, ch = fits[arm]
            ef = make_est_fn(spends, arms_used, ix, b, cands)
            cols_sum = (b[:, None]*np.array(ch)).sum()
        r = dict(scen=scen, nw=nw, m=m, K=K, arm=arm, bias=100*(cols_sum - tt)/tt, n_weekly=sum(t == "WEEKLY" for t in cfg["truths"]),
                 r2=cfg["r2"])
        me = mroi(ef, K, S)
        rel = np.abs(me - mt)/(np.abs(mt) + 1e-9)
        r["mroi_relerr_med"] = float(np.median(rel)); r["mroi_relerr_mean_capped"] = float(np.mean(np.minimum(rel, 5.0)))
        if K > 1:
            r["top_hit"] = float(np.argmax(me) == np.argmax(mt)); r["order_ok"] = float(np.array_equal(np.argsort(-me), np.argsort(-mt)))
            for bk, (lo, hi) in BOUNDS.items():
                s_e = optimise(ef, K, S, lo, hi, seed_of(prefix, scen, m, arm, bk))
                Te = sum(tf(k, s_e[k]) for k in range(K)); Tt = sum(tf(k, opt_t[bk][k]) for k in range(K))
                r[f"loss_{bk}"] = 100*(Tt - Te)/T1
                r[f"gstar_{bk}"] = 100*(Tt - T1)/T1
                r[f"gest_{bk}"] = 100*(Te - T1)/T1
                r[f"move_{bk}"] = float(np.abs(s_e - 1).mean())
        rows.append(r)
    return rows

LEN_SCENS = ["V", "M1", "M2", "M3", "M7"]
if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "valid":     # reproduce mc_run bias numbers for prefix MC (design rule 3)
        import mc_run
        mc_run.PREFIX = "MC"
        bad = 0
        for scen in ["M1", "M3", "M7"]:
            for m in range(7):
                ref, _ = mc_run.run_market(scen, m)
                rows = {r["arm"]: r for r in run_market(scen, m, 156, "MC")}
                for arm in ["W", "D", "S1", "OF", "OT"]:
                    d = abs(rows[arm]["bias"] - ref[f"bias_{arm}"])
                    if d > 1e-6: bad += 1; print("MISMATCH", scen, m, arm, rows[arm]["bias"], ref[f"bias_{arm}"])
        print("validation mismatches:", bad); sys.exit(0)
    if mode == "smoke":
        t0 = time.time(); n = 0
        for scen in ["M1", "M4", "M7", "M10"]:
            for m in range(3): run_market(scen, m, 156, "DECSMOKE"); n += 1
        print("smoke s/market", (time.time() - t0)/n); sys.exit(0)
    nw = int(sys.argv[2]) if len(sys.argv) > 2 else 156
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    scens = M.SCENS if mode == "main" else LEN_SCENS
    jobs = [(s, m, nw) for s in scens for m in range(n)]
    print("markets", len(jobs), "nw", nw, flush=True); t0 = time.time()
    out = Parallel(n_jobs=2, batch_size=4, verbose=5)(delayed(run_market)(*j) for j in jobs)
    pd.DataFrame([r for o in out for r in o]).to_csv(f"results/DEC_{mode}_{nw}.csv", index=False)
    print("done", round(time.time() - t0), "s", flush=True)
