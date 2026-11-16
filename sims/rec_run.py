"""Shallow-saturation recovery study. Design: DESIGN_RECOVERY.md (written before running)."""
import sys, os, time, numpy as np, pandas as pd
from joblib import Parallel, delayed
from scipy.optimize import minimize
from lib import *

NW = 156; ND = NW*7
DEPTHS = ["med", "mild", "x1", "x3", "x10"]
SMULT = [0.5, 1.5, 2.0, 3.0]
PREFIX = os.environ.get("RECPREFIX", "REC")

def true_gamma(ad, depth):
    if depth == "med": return np.percentile(ad[ad > 0], 50)
    if depth == "mild": return np.percentile(ad[ad > 0], 90)
    return {"x1": 1.0, "x3": 3.0, "x10": 10.0}[depth]*ad.max()

def sim(delta, depth, shape, pattern, r2, rep):
    rng = np.random.default_rng(seed_of(PREFIX, delta, depth, shape, pattern, r2, rep))
    spend = gen_spend(pattern, rng, ND)
    ad = adstock(spend, delta); g = true_gamma(ad, depth)
    resp = lambda s: hill(adstock(s, delta), g, shape).reshape(NW, 7).sum(1)
    wk = resp(spend)
    t = np.arange(NW); base = 800 + .5*t + 30*np.sin(2*np.pi*t/52)
    c = base.std()/(wk.std() + 1e-9)
    wk_true = c*wk
    noise = np.sqrt(wk_true.var()*(1/r2 - 1) + 1e-9)
    y = base + wk_true + rng.normal(0, noise, NW)
    truth = {s: c*resp(spend*s).sum() for s in [0.9, 1.0, 1.1] + SMULT}
    return spend, y, wk_true, dict(delta=delta, gamma=g, shape=shape, c=c, truth=truth, maxad=ad.max())

def transform(freq, spend, d, g, h):
    if freq == "W":
        a = adstock(spend.reshape(NW, 7).sum(1), d); return hill(a, g, h)
    a = adstock(spend, d); return hill(a, g, h).reshape(NW, 7).sum(1)

def cand_grid(freq, spend, ext):
    cols, meta = [], []
    for d in DEC_GRID:
        a = adstock(spend.reshape(NW, 7).sum(1), d) if freq == "W" else adstock(spend, d)
        gs = list(pct_nz(a, GAMMA_PCTS))
        if ext: gs += [m*max(a.max(), 1e-9) for m in (1, 3, 10, 30)]
        for g in gs:
            for h in H_GRID:
                m = hill(a, g, h); cols.append(m if freq == "W" else m.reshape(NW, 7).sum(1)); meta.append((d, g, h))
    return np.array(cols), meta

def sse_all(yr, Q, cols):
    Mr = cols - (cols@Q)@Q.T; num = Mr@yr; den = (Mr*Mr).sum(1)
    den = np.where(den < 1e-12, np.inf, den)
    beta = num/den; sse = yr@yr - num**2/den
    sse = np.where(beta > 0, sse, yr@yr)     # non-negative coefficient
    return sse, beta

def fit_continuous(freq, spend, yr, Q, start, maxad_w):
    # parameters: logit delta, ln gamma, ln h
    def unpack(p):
        d = 0.01 + 0.98/(1 + np.exp(-p[0])); g = np.exp(np.clip(p[1], np.log(maxad_w*0.02), np.log(maxad_w*100))); h = np.exp(np.clip(p[2], np.log(.5), np.log(4)))
        return d, g, h
    def f(p):
        d, g, h = unpack(p); m = transform(freq, spend, d, g, h)
        mr = m - (m@Q)@Q.T; den = mr@mr
        mc = m - m.mean()
        if den < 1e-12 or den < 1e-3*(mc@mc): return yr@yr     # numerical guard: column indistinguishable from the controls
        b = (mr@yr)/den
        return yr@yr - (mr@yr)**2/den if b > 0 else yr@yr
    best = None
    d0, g0, h0 = start
    starts = [np.array([np.log((d0 - .01)/(.99 - d0)), np.log(g0), np.log(h0)])]
    starts.append(np.array([0.0, np.log(maxad_w*0.5), np.log(1.5)])); starts.append(np.array([1.0, np.log(maxad_w*3), np.log(1.0)]))
    for s in starts:
        r = minimize(f, s, method="Nelder-Mead", options=dict(xatol=1e-3, fatol=1e-6*max(yr@yr, 1), maxiter=200))
        if best is None or r.fun < best.fun: best = r
    return unpack(best.x), best.fun

def est_arm(freq, est, spend, y, Q, proj, info):
    yr = y - (y@Q)@Q.T
    cols, meta = cand_grid(freq, spend, ext=(est != "G"))
    sse, beta = sse_all(yr, Q, cols)
    k = int(np.argmin(sse)); d, g, h = meta[k]
    out = dict(sse_best_grid=float(sse[k]))
    if est == "C":
        maxw = max(adstock(spend.reshape(NW, 7).sum(1), d).max(), adstock(spend, d).max())
        (d, g, h), s_ = fit_continuous(freq, spend, yr, Q, (d, g, h), maxw)
    m = transform(freq, spend, d, g, h); mr = m - (m@Q)@Q.T; den = mr@mr
    b = max((mr@yr)/den, 0.0) if den > 1e-12 else 0.0
    def contrib(s_mult):
        return b*transform(freq, spend*s_mult, d, g, h).sum()
    C1 = contrib(1.0); tr = info["truth"]
    out.update(bias=100*(C1 - tr[1.0])/tr[1.0],
               mroi_bias=100*((contrib(1.1) - contrib(0.9)) - (tr[1.1] - tr[0.9]))/(tr[1.1] - tr[0.9]),
               **{f"err_s{s}": 100*(contrib(s) - tr[s])/tr[1.0] for s in SMULT})
    if freq == "D":
        out.update(d_err=d - info["delta"], lng_err=np.log(g/info["gamma"]), h_err=h - info["shape"])
    if est == "X":
        n = NW; ok = sse <= sse.min()*(1 + 6/n) ; out["set_size"] = int(ok.sum())
        idx = np.where(ok)[0]; vals = []
        for i in idx[:60]:
            dd, gg, hh = meta[i]; bi = max(beta[i], 0)
            # beta from residualised regression applies to the raw column too (partialled-out)
            vals.append(bi*transform(freq, spend*2.0, dd, gg, hh).sum())
        vals = np.array(vals)/tr[2.0]
        out["set_lo2"] = float(vals.min()); out["set_hi2"] = float(vals.max())
        lin = sse_all(yr, Q, spend_lin_cols(freq, spend))[0].min()
        out["lin_gain"] = float((lin - sse.min())/max(lin, 1e-12))
    return out

def spend_lin_cols(freq, spend):
    cols = []
    for d in DEC_GRID:
        a = adstock(spend.reshape(NW, 7).sum(1), d) if freq == "W" else adstock(spend, d)
        cols.append(a if freq == "W" else a.reshape(NW, 7).sum(1))
    return np.array(cols)

def one(delta, depth, shape, pattern, r2, rep, ests=("G", "X", "C")):
    spend, y, wk_true, info = sim(delta, depth, shape, pattern, r2, rep)
    C = controls(NW); Q, _ = np.linalg.qr(C); proj = None
    rows = []
    for freq in ("W", "D"):
        for est in ests:
            r = est_arm(freq, est, spend, y, Q, proj, info)
            r.update(delta=delta, depth=depth, shape=shape, pattern=pattern, r2=r2, rep=rep, freq=freq, est=est)
            rows.append(r)
    return rows

def cells(reps):
    return [(d, dp, sh, p, r2, r) for dp in DEPTHS for sh in (1.0, 2.2) for d in (0.15, 0.5, 0.85)
            for p in ("bursty", "smooth", "real") for r2 in (0.85, 0.5) for r in range(reps)]

if __name__ == "__main__":
    mode = sys.argv[1]; reps = {"smoke": 1, "time": 1, "full": 60}[mode]
    cs = cells(reps)
    if mode == "smoke": cs = cs[::17]
    if mode == "time": cs = cs[::7][:12]
    print("markets", len(cs), flush=True); t0 = time.time()
    res = Parallel(n_jobs=int(os.environ.get("NJOBS", "2")), batch_size=4, verbose=5)(delayed(one)(*c) for c in cs)
    df = pd.DataFrame([r for rows in res for r in rows]); df.to_csv(f"results/REC_{mode}.csv", index=False)
    print("done", round(time.time() - t0), "s", len(df), "rows")
