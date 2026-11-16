"""S2b targeted weekday-seasonality test. Design: DESIGN_DOW2.md (written before running)."""
import sys, os, time, numpy as np, pandas as pd
from joblib import Parallel, delayed
from lib import *

NW = 156; ND = NW*7
PROFILES = {"A": np.array([-.4, -.4, -.2, 0.0, .8, 1.0, -.8]),
            "B": np.array([-.6, -.6, -.6, -.6, -.6, 1.5, 1.5])}
ALIGNS = {"A": {"neutral": [1]*7, "weekday_only": [1,1,1,1,1,0,0], "weekend_heavy": [1,1,1,1,1,3,3], "peak": [1,1,1,1,3,3,1], "anti_peak": [3,3,1,1,1,1,1]},
          "B": {"neutral": [1]*7, "weekday_only": [1,1,1,1,1,0,0], "weekend_heavy": [1,1,1,1,1,3,3], "peak": [1,1,1,1,3,3,1], "anti_peak": [3,3,3,1,1,1,1]}}
PREFIX = os.environ.get("DOWPREFIX", "DOW2")

def fit_two(yr, Q, cols1, cols2):
    """best candidate for KPI = b*col1 + b2*col2 (partialled out); returns (index, coefs, sse). b >= 0 enforced via fallback to col1 only."""
    M1 = cols1 - (cols1@Q)@Q.T; M2 = cols2 - (cols2@Q)@Q.T
    a11 = (M1*M1).sum(1); a22 = (M2*M2).sum(1); a12 = (M1*M2).sum(1)
    r1 = M1@yr; r2 = M2@yr
    det = a11*a22 - a12**2
    ok = det > 1e-10*np.maximum(a11*a22, 1e-12)
    b1 = np.where(ok, (r1*a22 - r2*a12)/np.where(ok, det, 1), 0.0)
    b2 = np.where(ok, (a11*r2 - a12*r1)/np.where(ok, det, 1), 0.0)
    sse2 = yr@yr - (b1*r1 + b2*r2)
    # fallback single column
    den1 = np.where(a11 < 1e-12, np.inf, a11); sse1 = yr@yr - r1**2/den1
    use2 = ok & (b1 > 0)
    sse = np.where(use2, sse2, np.where(r1 > 0, sse1, yr@yr))
    k = int(np.argmin(sse))
    if use2[k]: return k, (b1[k], b2[k]), sse[k]
    return k, (r1[k]/den1[k], 0.0), sse[k]

def one(strength, profile, align, delta, shape, pattern, rep, r2=0.85):
    rng = np.random.default_rng(seed_of(PREFIX, strength, profile, align, delta, shape, pattern, rep))
    p = PROFILES[profile]; dow = np.tile(np.arange(7), NW)
    spend = gen_spend(pattern, rng, ND)*np.array(ALIGNS[profile][align], float)[dow]
    if spend.sum() <= 0: spend = gen_spend(pattern, rng, ND)
    dm = 1 + strength*p[dow]
    ad = adstock(spend, delta); g = np.percentile(ad[ad > 0], DEPTH_PCT["med"])
    resp = hill(ad, g, shape); r_day = resp*dm
    wk_raw = r_day.reshape(NW, 7).sum(1)
    t = np.arange(NW); base = 800 + .5*t + 30*np.sin(2*np.pi*t/52)
    c = base.std()/(wk_raw.std() + 1e-9); wk_true = c*wk_raw
    noise = np.sqrt(wk_true.var()*(1/r2 - 1) + 1e-9)
    y = np.repeat(base/7, 7)*dm; y = y.reshape(NW, 7).sum(1) + wk_true + rng.normal(0, noise, NW)
    extra = strength*(resp*p[dow]).reshape(NW, 7).sum(1)           # s * sum p_d r_d
    share = float(np.mean(np.abs(extra))/np.mean(resp.reshape(NW, 7).sum(1)))
    C = controls(NW); Q, _ = np.linalg.qr(C); proj = Projector(C)
    spend_w = spend.reshape(NW, 7).sum(1)
    arms = {}
    arms["weekly"] = grid_weekly(y, spend_w, DEC_GRID, proj)
    arms["dailyT"] = grid_daily(y, spend, NW, DEC_GRID, proj)
    # weekday-aware daily transform: two columns per candidate
    c1, c2, meta = [], [], []
    for d in DEC_GRID:
        a = adstock(spend, d); gs = pct_nz(a, GAMMA_PCTS)
        for gg in gs:
            for h in H_GRID:
                m = hill(a, gg, h); c1.append(m.reshape(NW, 7).sum(1)); c2.append((m*p[dow]).reshape(NW, 7).sum(1))
    yr = y - (y@Q)@Q.T
    k, (b1, b2), _ = fit_two(yr, Q, np.array(c1), np.array(c2))
    arms["dailyT_dow"] = (b1*np.array(c1)[k] + b2*np.array(c2)[k], None)
    arms["oracle"] = (best_fit(y, wk_raw[None, :], [delta], proj)[0]*wk_raw, delta)
    rows = [dict(strength=strength, profile=profile, align=align, delta=delta, shape=shape, pattern=pattern, rep=rep,
                 arm=a, bias=bias_pct(est, wk_true), extra_share=share) for a, (est, d) in arms.items()]
    return rows

def cells(reps):
    out = []
    for prof in ("A", "B"):
        for al in ALIGNS[prof]:
            for s in (0.3, 0.6, 0.9):
                for d in (0.15, 0.5, 0.85):
                    for sh in (1.0, 2.2):
                        for pat in ("bursty", "smooth", "real"):
                            for r in range(reps): out.append((s, prof, al, d, sh, pat, r))
    for prof in ("A", "B"):         # control (s = 0)
        for d in (0.15, 0.5, 0.85):
            for sh in (1.0, 2.2):
                for pat in ("bursty", "smooth", "real"):
                    for r in range(reps): out.append((0.0, prof, "neutral", d, sh, pat, r))
    return out

if __name__ == "__main__":
    mode = sys.argv[1]; reps = {"smoke": 1, "full": 100}[mode]
    cs = cells(reps)
    if mode == "smoke": cs = cs[::37]
    print("runs", len(cs), flush=True); t0 = time.time()
    res = Parallel(n_jobs=int(os.environ.get("NJOBS", "2")), batch_size=50, verbose=5)(delayed(one)(*c) for c in cs)
    df = pd.DataFrame([r for rows in res for r in rows]); df.to_csv(f"results/S2b_{mode}.csv", index=False)
    print("done", round(time.time() - t0), "s")
