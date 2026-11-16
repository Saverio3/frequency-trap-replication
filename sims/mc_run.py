"""Multichannel study (design: DESIGN_MULTI.md, fixed before running)."""
import sys, time, os
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from scipy.optimize import nnls
from scipy.signal import lfilter
from lib import *

NW = 156; ND = NW*7
PREFIX = os.environ.get("MCPREFIX", "MC")
PATTERNS = ["bursty", "smooth", "real", "flighting", "pulsing", "sporadic"]
DELTAS = [0.15, 0.50, 0.85]; DEPTHS = ["mild", "med", "deep"]; SHAPES = [1.0, 2.2]

def hill_s(x, g, h):
    x = np.maximum(x, 0.0); xh = x**h
    return xh/(xh + g**h + 1e-300)

def gpct(a, p):
    """gamma at percentile p of non-negligible adstock (> 1e-6 of max); avoids degenerate tails for flighting/sporadic"""
    nz = a[a > 1e-6*max(a.max(), 1e-300)]
    return float(np.percentile(nz, p)) if nz.size else 1.0

# ------------------------------------------------------------ generators
def gen_pattern(kind, rng):
    if kind in ("bursty", "smooth", "real"):
        return gen_spend(kind, rng, ND)
    if kind == "flighting":
        on = np.zeros(NW, bool); t = 0; state = bool(rng.integers(2))
        while t < NW:
            L = int(rng.integers(2, 6)); on[t:t + L] = state; t += L; state = not state
        return rng.lognormal(0, 0.4, ND)*12*np.repeat(on, 7)
    if kind == "pulsing":
        return rng.lognormal(0, 0.4, ND)*14*(np.tile(np.arange(7), NW) < 5)
    if kind == "sporadic":
        return rng.lognormal(0, 0.7, ND)*80*(rng.random(ND) > 0.97)
    raise ValueError(kind)

def shared_z(rng):
    zd = lfilter([np.sqrt(1 - .36)], [1, -.6], rng.normal(size=ND + 100))[100:]
    zw = np.repeat(lfilter([np.sqrt(1 - .64)], [1, -.8], rng.normal(size=NW + 50))[50:], 7)
    z = zd + zw
    return (z - z.mean())/z.std()

def true_resp(truth, spend, delta, depth, shape, rng, e=None, dip=False):
    """weekly true response series (NW,)"""
    if truth == "WEEKLY":
        a = adstock(spend.reshape(NW, 7).sum(1), delta)
        g = gpct(a, DEPTH_PCT[depth])
        return hill_s(a, g, shape)
    if truth == "SUB":
        Kk = 4
        sf = (spend[:, None]*rng.dirichlet(np.full(Kk, 0.3), ND)).reshape(-1)
        a = adstock(sf, delta**(1.0/Kk)); g = gpct(a, DEPTH_PCT[depth])
        return hill_s(a, g, shape).reshape(NW, 7*Kk).sum(1)
    a = adstock(spend, delta); g = gpct(a, DEPTH_PCT[depth])
    r = hill_s(a, g, shape)
    if e is not None:
        r = r*e
    if dip:
        ma = lfilter(np.ones(14)/14, [1.0], r); ma = np.concatenate([[0.0], ma[:-1]]); r = r - 0.3*ma
    return r.reshape(NW, 7).sum(1)

def scenario_config(scen, rng):
    P = list(PATTERNS)
    cfg = dict(K=3, truths=["DAILY"]*3, kappa=[0.0]*3, r2=0.85, season=0.0, tv=False, dip=[False]*3, shares=None, pats=None)
    if scen == "V":
        cfg.update(K=1, truths=["DAILY"]); cfg["pats"] = [str(rng.choice(["bursty", "smooth", "real"]))]
    elif scen == "M1":
        pass
    elif scen == "M2":
        cfg["kappa"] = [1.0]*3
    elif scen in ("M3", "M8", "M9"):
        cfg["kappa"] = [float(rng.choice([0.0, 0.5])) for _ in range(3)]
        w = int(rng.integers(3)); cfg["truths"] = ["WEEKLY" if i == w else "DAILY" for i in range(3)]
        if scen == "M8": cfg["r2"] = 0.5
        if scen == "M9":
            s = np.array([0.70, 0.25, 0.05]); rng.shuffle(s); cfg["shares"] = s
    elif scen == "M4":
        cfg.update(K=5); cfg["truths"] = ["WEEKLY" if rng.random() < 0.25 else "DAILY" for _ in range(5)]
        cfg["kappa"] = [float(rng.choice([0.0, 0.5, 1.0])) for _ in range(5)]
        cfg["pats"] = [str(rng.choice(P)) for _ in range(5)]
        cfg["shares"] = rng.dirichlet(np.full(5, 1.5))
    elif scen == "M5":
        cfg["season"] = 1.0
    elif scen == "M6":
        cfg["truths"] = ["SUB" if rng.random() < 0.5 else "DAILY" for _ in range(3)]
    elif scen == "M7":
        cfg["kappa"] = [1.0]*3; cfg["tv"] = True
    elif scen == "M10":
        d = [True, True, False]; rng.shuffle(d); cfg["dip"] = d
    else:
        raise ValueError(scen)
    K = cfg["K"]
    if len(cfg["dip"]) != K: cfg["dip"] = [False]*K
    if len(cfg["kappa"]) != K: cfg["kappa"] = [0.0]*K
    if cfg["pats"] is None:
        cfg["pats"] = [str(x) for x in rng.choice(P, size=K, replace=False)]
    if cfg["shares"] is None:
        cfg["shares"] = rng.dirichlet(np.full(K, 2.0)) if K > 1 else np.array([1.0])
    cfg["delta"] = [float(rng.choice(DELTAS)) for _ in range(K)]
    cfg["depth"] = [str(rng.choice(DEPTHS)) for _ in range(K)]
    cfg["shape"] = [float(rng.choice(SHAPES)) for _ in range(K)]
    return cfg

def make_market(scen, m):
    rng = np.random.default_rng(seed_of(PREFIX, scen, m))
    cfg = scenario_config(scen, rng); K = cfg["K"]
    z = shared_z(rng)
    season_d = np.sin(2*np.pi*np.arange(ND)/(52*7))
    e = np.exp(0.5*z - 0.125) if cfg["tv"] else None
    spends, resps = [], []
    for k in range(K):
        s = gen_pattern(cfg["pats"][k], rng)*np.exp(cfg["kappa"][k]*z + cfg["season"]*season_d)
        spends.append(s)
        resps.append(true_resp(cfg["truths"][k], s, cfg["delta"][k], cfg["depth"][k], cfg["shape"][k], rng,
                               e=e if cfg["truths"][k] == "DAILY" else None, dip=cfg["dip"][k]))
    raw = np.array([cfg["shares"][k]*resps[k]/(resps[k].std() + 1e-9) for k in range(K)])
    t = np.arange(NW); base = 800 + .5*t + 30*np.sin(2*np.pi*t/52)
    c = base.std()/(raw.sum(0).std() + 1e-9)
    contrib = c*raw
    price = lfilter([np.sqrt(1 - .49)], [1, -.7], rng.normal(size=NW + 50))[50:]; price = (price - price.mean())/price.std()
    sig = contrib.sum(0)
    y = base + 40*price + sig + rng.normal(0, np.sqrt(sig.var()*(1/cfg["r2"] - 1) + 1e-9), NW)
    C = np.column_stack([np.ones(NW), t, np.sin(2*np.pi*t/52), np.cos(2*np.pi*t/52), price])
    return cfg, np.array(spends), contrib, y, C

# ------------------------------------------------------------ estimators
def cand_set(spend, arm):
    sw = spend.reshape(NW, 7).sum(1); cols = []
    for d in DEC_GRID:
        a = adstock(sw if arm == "w" else spend, d)
        for g in pct_nz(a, GAMMA_PCTS):
            for h in H_GRID:
                m = hill_s(a, g, h); cols.append(m if arm == "w" else m.reshape(NW, 7).sum(1))
    return np.array(cols)

def _best(yr, Mr, yy):
    num = Mr@yr; den = (Mr*Mr).sum(1); den = np.where(den < 1e-12, np.inf, den)
    sse = yy - num**2/den
    sc = np.where(num > 0, sse, np.inf)
    if not np.isfinite(sc).any(): sc = sse
    k = int(np.argmin(sc)); return k, float(sse[k]), yr - (num[k]/den[k])*Mr[k]

def vuong(rw, sw, rd, sd, n):
    s2w, s2d = sw/n, sd/n
    lr = (-0.5*np.log(s2d + 1e-300) - 0.5*rd**2/(s2d + 1e-300)) - (-0.5*np.log(s2w + 1e-300) - 0.5*rw**2/(s2w + 1e-300))
    s = lr.std(ddof=1)
    return float(lr.mean()/(s/np.sqrt(n))) if s > 1e-12 else 0.0

def pick(y, Z, cands, k, mode):
    Q, _ = np.linalg.qr(Z); yr = y - Q@(Q.T@y); yy = yr@yr
    out = {}
    for arm in ("w", "d"):
        if mode in (arm, "sel"):
            M = cands[arm][k]; Mr = M - (M@Q)@Q.T
            kk, sse, res = _best(yr, Mr, yy); out[arm] = (kk, sse, res)
    if mode == "sel":
        z = vuong(out["w"][2], out["w"][1], out["d"][2], out["d"][1], NW); arm = "d" if z > 0 else "w"
    else:
        arm = mode
    return arm, cands[arm][k][out[arm][0]]

def backfit(y, C, cands, assign, sweeps=3):
    K = len(assign); chosen = [None]*K; arms = list(assign)
    for s in range(sweeps + 1):   # sweep 0 = initialisation
        for k in range(K):
            Z = np.column_stack([C] + [chosen[j] for j in range(K) if j != k and chosen[j] is not None])
            arms[k], chosen[k] = pick(y, Z, cands, k, assign[k])
    return arms, chosen

def contribs(y, C, cols):
    Q, _ = np.linalg.qr(C); yr = y - Q@(Q.T@y)
    M = np.array(cols); Mr = M - (M@Q)@Q.T
    b, _ = nnls(Mr.T, yr, maxiter=2000)
    return b[:, None]*M

def screen_assign(y, C, spends, cands):
    K = len(spends); wk = spends.reshape(K, NW, 7).sum(2); out = []
    for k in range(K):
        Z = np.column_stack([C] + [wk[j] for j in range(K) if j != k])
        out.append(pick(y, Z, cands, k, "sel")[0])
    return out

def run_market(scen, m):
    cfg, spends, contrib, y, C = make_market(scen, m); K = cfg["K"]
    cands = {"w": [cand_set(spends[k], "w") for k in range(K)], "d": [cand_set(spends[k], "d") for k in range(K)]}
    truth_arm = ["w" if t == "WEEKLY" else "d" for t in cfg["truths"]]
    res = {}; arms_used = {}
    res["W"] = contribs(y, C, backfit(y, C, cands, ["w"]*K)[1]); arms_used["W"] = ["w"]*K
    res["D"] = contribs(y, C, backfit(y, C, cands, ["d"]*K)[1]); arms_used["D"] = ["d"]*K
    a1, ch1 = backfit(y, C, cands, ["sel"]*K); res["S1"] = contribs(y, C, ch1); arms_used["S1"] = a1
    a2 = screen_assign(y, C, spends, cands); res["S2"] = contribs(y, C, backfit(y, C, cands, a2)[1]); arms_used["S2"] = a2
    res["OF"] = contribs(y, C, backfit(y, C, cands, truth_arm)[1]); arms_used["OF"] = truth_arm
    res["OT"] = contribs(y, C, list(contrib))   # true transforms (scale irrelevant under NNLS)
    wk = spends.reshape(K, NW, 7).sum(2)
    corr = np.corrcoef(wk) if K > 1 else np.array([[1.0]])
    tt = contrib.sum()
    mrow = dict(scen=scen, m=m, K=K, r2=cfg["r2"], n_weekly=sum(t == "WEEKLY" for t in cfg["truths"]))
    for a, c in res.items():
        mrow[f"bias_{a}"] = 100*(c.sum() - tt)/tt
    crow = []
    for k in range(K):
        off = np.abs(np.delete(corr[k], k)).max() if K > 1 else 0.0
        r = dict(scen=scen, m=m, k=k, pattern=cfg["pats"][k], truth=cfg["truths"][k], share=float(cfg["shares"][k]),
                 delta=cfg["delta"][k], shape=cfg["shape"][k], depth=cfg["depth"][k], maxcorr=float(off), dip=cfg["dip"][k])
        for a, c in res.items():
            r[f"bias_{a}"] = 100*(c[k].sum() - contrib[k].sum())/(contrib[k].sum() + 1e-12)
        for a in ("S1", "S2"):
            r[f"chosen_{a}"] = arms_used[a][k]
        r["truth_arm"] = truth_arm[k]
        crow.append(r)
    return mrow, crow

SCENS = ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10"]
if __name__ == "__main__":
    mode = sys.argv[1]
    n = {"valid": 100, "smoke": 6, "A": 1000, "B": 1000}[mode]
    scens = ["V"] if mode == "valid" else SCENS
    jobs = [(s, m) for s in scens for m in range(n)]
    print("markets", len(jobs), "prefix", PREFIX, flush=True); t0 = time.time()
    out = Parallel(n_jobs=2, batch_size=6, verbose=5)(delayed(run_market)(*j) for j in jobs)
    pd.DataFrame([o[0] for o in out]).to_csv(f"results/MC_{mode}_markets.csv", index=False)
    pd.DataFrame([c for o in out for c in o[1]]).to_csv(f"results/MC_{mode}_channels.csv", index=False)
    print("done", round(time.time() - t0), "s", flush=True)
