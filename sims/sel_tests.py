"""Candidate tests T1-T5 per market (design: DESIGN_TESTS.md)."""
import sys, time, os
import numpy as np, pandas as pd
from joblib import Parallel, delayed
os.environ.setdefault("SELPREFIX", "SELT")
import sel_run as SR
from sel_run import *
PREFIX = os.environ["SELPREFIX"]
B = 39

def gen(world, sub, pr, rep):
    key = (PREFIX, world, sub, tuple(sorted(pr.items())), rep)
    rng = np.random.default_rng(seed_of(*key))
    if world == "W1": return SR.g_core(pr["delta"], pr["depth"], pr["shape"], pr["pattern"], rng), key
    if world == "W7": return SR.g_core(pr["delta"], pr["depth"], pr["shape"], pr["pattern"], rng, r2=pr["r2"]), key
    if world == "W8": return SR.g_altform("weekly_true", pr["delta"], pr["depth"], pr["shape"], pr["pattern"], rng, r2=pr["r2"]), key
    if world == "W2": return SR.g_altform("weekly_true", pr["delta"], pr["depth"], pr["shape"], pr["pattern"], rng), key
    if world == "W3":
        rz = np.random.default_rng(seed_of(*key, "z"))
        return SR.g_tv(pr["tv"], pr["kappa"], pr["delta"], pr["pattern"], pr["shape"], rng, rz), key
    if world == "W4": return SR.g_sub(pr["K"], pr["alpha"], pr["delta"], pr["shape"], pr["pattern"], rng), key
    if world == "W5": return SR.g_dow(pr["align"], pr["delta"], pr["shape"], pr["pattern"], rng), key
    return SR.g_altform(pr["form"], pr["delta"], pr["depth"], pr["shape"], pr["pattern"], rng), key

def tstat(x, e):
    """t-stat of slope of e on x (x already residualised on controls)."""
    sxx = x@x
    if sxx < 1e-12: return 0.0
    b = (x@e)/sxx; r = e - b*x
    s2 = r@r/(len(e) - 2)
    return float(b/np.sqrt(s2/sxx + 1e-300))

def tests(spend_d, y, tc, rng):
    C = controls(NW); proj = Projector(C)
    cw, mw = cands(spend_d, "w"); cd, md = cands(spend_d, "d")
    yr = proj.res(y)
    out = {}
    fits = {}
    for nm, cols in (("w", cw), ("d", cd)):
        Mr = proj.res(cols); num = Mr@yr; den = (Mr*Mr).sum(1)
        den = np.where(den < 1e-12, np.inf, den)
        sse = yr@yr - num**2/den; k = int(np.argmin(sse))
        fits[nm] = dict(k=k, sse=float(sse[k]), mr=Mr[k], b=num[k]/den[k], col=cols[k])
    fw, fd = fits["w"], fits["d"]
    ew = yr - fw["b"]*fw["mr"]; ed = yr - fd["b"]*fd["mr"]
    out["bias_w"] = bias_pct(fw["b"]*fw["col"], tc); out["bias_d"] = bias_pct(fd["b"]*fd["col"], tc)
    n = len(y)
    # T1
    out["T1"] = float(np.log(fw["sse"]/max(fd["sse"], 1e-12)))
    # T2 J / encompassing
    X = np.column_stack([fw["mr"], fd["mr"]])
    try:
        coef, *_ = np.linalg.lstsq(X, yr, rcond=None)
        r = yr - X@coef; s2 = r@r/(n - 2)
        cov = s2*np.linalg.pinv(X.T@X)
        t = coef/np.sqrt(np.maximum(np.diag(cov), 1e-300))
        out["T2"] = float(t[1] - t[0])
    except Exception:
        out["T2"] = 0.0
    # T3 Vuong
    s2w = fw["sse"]/n; s2d = fd["sse"]/n
    llw = -0.5*np.log(s2w + 1e-300) - 0.5*ew**2/(s2w + 1e-300)
    lld = -0.5*np.log(s2d + 1e-300) - 0.5*ed**2/(s2d + 1e-300)
    lr = lld - llw; sd = lr.std(ddof=1)
    out["T3"] = float(lr.mean()/(sd/np.sqrt(n))) if sd > 1e-12 else 0.0
    # T4 Jensen-gap
    X7 = spend_d.reshape(NW, 7); S = X7.sum(1)
    H = np.where(S > 0, ((X7/np.where(S > 0, S, 1)[:, None])**2).sum(1), np.nan)
    H = np.where(np.isnan(H), np.nanmean(H), H)
    Hr = proj.res(H[None, :])[0]
    out["T4"] = abs(tstat(Hr, ew)) - abs(tstat(Hr, ed))
    # T5 permutation
    perm = []
    for _ in range(B):
        sp = rng.permuted(X7, axis=1).reshape(-1)
        cp, _m = cands(sp, "d")
        Mr = proj.res(cp); num = Mr@yr; den = (Mr*Mr).sum(1)
        den = np.where(den < 1e-12, np.inf, den)
        perm.append(float((yr@yr - num**2/den).min()))
    perm = np.array(perm)
    out["T5"] = float((perm.mean() - fd["sse"])/(perm.std() + 1e-9))
    out["T5p"] = float((np.sum(perm <= fd["sse"]) + 1)/(B + 1))
    # earlier features
    base = diagnose(spend_d, y, tc)
    for k in ("D", "dR2", "hgap", "WV", "ZS", "CV", "DEPTH"):
        out[k] = base[k]
    return out

def one(world, sub, pr, rep):
    (spend, y, tc), key = gen(world, sub, pr, rep)
    rng = np.random.default_rng(seed_of(*key, "perm"))
    row = tests(spend, y, tc, rng)
    cellid = f"{world}|{sub}|" + "|".join(f"{k}={v}" for k, v in sorted(pr.items()))
    return dict(world=world, sub=sub, cell=cellid, rep=rep, **row)

if __name__ == "__main__":
    mode = sys.argv[1]; reps = {"smoke": 1, "full": 20}[mode]
    cs = make_cells(reps, stress=True)
    if mode == "smoke": cs = cs[::15]
    print("runs", len(cs), flush=True); t0 = time.time()
    res = Parallel(n_jobs=2, batch_size=4, verbose=5)(delayed(one)(*c) for c in cs)
    pd.DataFrame(res).to_csv(f"results/TEST_{PREFIX}_{mode}.csv", index=False)
    print("done", round(time.time() - t0), "s", flush=True)
