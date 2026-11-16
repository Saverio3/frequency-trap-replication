"""Selector study: per-market observable diagnostics + arm biases across six worlds.
Design: DESIGN_SELECTOR.md (fixed before running)."""
import sys, time, os
PREFIX = os.environ.get("SELPREFIX", "SEL")
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from lib import *
from s1_timevarying import gen_z, gen_spend_tilted
from s2_dow import PROFILE, ALIGN
from s4_reviewer3 import common_outcome

NW = 156
NTR = 104

# ---------------------------------------------------------------- generators
def g_core(delta, depth, shape, pattern, rng, r2=0.85):
    spend, y, true_c = simA_core(delta, depth, shape, pattern, rng, r2=r2)
    return spend, y, true_c

def g_altform(form, delta, depth, shape, pattern, rng, r2=0.85):
    nd = NW*7
    spend = gen_spend(pattern, rng, nd)
    spend_w = spend.reshape(NW, 7).sum(1)
    if form == "weekly_true":
        ad = adstock(spend_w, delta)
        g = np.percentile(ad[ad > 0], DEPTH_PCT[depth])
        wk = hill(ad, g, shape)
    else:
        ad = 0.6*adstock(spend, 0.2) + 0.4*adstock(spend, 0.9) if form == "twocomp" else adstock(spend, delta)
        g = np.percentile(ad[ad > 0], DEPTH_PCT[depth])
        if form == "twocomp":
            r = hill(ad, g, shape)
        elif form == "linear":
            r = ad.copy()
        elif form == "log1p":
            r = np.log1p(ad/g)
        elif form == "power":
            r = ad**0.5
        elif form == "wearout":
            recent = lfilter(np.ones(28)/28, [1.0], ad)
            r = (1.0/(1.0 + 0.5*recent/(recent.mean() + 1e-9)))*hill(ad, g, shape)
        else:
            raise ValueError(form)
        wk = r.reshape(NW, 7).sum(1)
    y, true_c = common_outcome(wk, rng, NW, r2=r2)
    return spend, y, true_c

def g_tv(tv, kappa, delta, pattern, shape, rng, rz, sig_e=0.5):
    nd = NW*7
    z = gen_z(tv, rz, NW)
    spend = gen_spend_tilted(pattern, rng, nd, z, kappa)
    ad = adstock(spend, delta)
    e = np.exp(sig_e*z - sig_e**2/2)
    g = np.percentile(ad[ad > 0], DEPTH_PCT["med"])
    wk = (e*hill(ad, g, shape)).reshape(NW, 7).sum(1)
    t = np.arange(NW)
    base = 800 + .5*t + 30*np.sin(2*np.pi*t/52)
    wk_true = wk*(base.std()/(wk.std() + 1e-9))
    noise_sd = np.sqrt(wk_true.var()*(1/0.85 - 1) + 1e-9)
    y = base + wk_true + rng.normal(0, noise_sd, NW)
    return spend, y, wk_true

def g_sub(K, alpha, delta, shape, pattern, rng):
    nd = NW*7
    spend_d = gen_spend(pattern, rng, nd)
    shares = rng.dirichlet(np.full(K, float(alpha)), nd)
    spend_f = (spend_d[:, None]*shares).reshape(-1)
    ad = adstock(spend_f, delta**(1.0/K))
    g = np.percentile(ad[ad > 0], DEPTH_PCT["med"])
    wk = hill(ad, g, shape).reshape(NW, 7*K).sum(1)
    y, true_c = common_outcome(wk, rng, NW)
    return spend_d, y, true_c

def g_dow(align, delta, shape, pattern, rng, strength=0.6):
    nd = NW*7
    dow = np.tile(np.arange(7), NW)
    spend = gen_spend(pattern, rng, nd)*ALIGN[align][dow]
    dm = 1 + strength*PROFILE[dow]
    ad = adstock(spend, delta)
    g = np.percentile(ad[ad > 0], DEPTH_PCT["med"])
    r_day = hill(ad, g, shape)*dm
    wk_raw = r_day.reshape(NW, 7).sum(1)
    t = np.arange(NW)
    base = 800 + .5*t + 30*np.sin(2*np.pi*t/52)
    c = base.std()/(wk_raw.std() + 1e-9)
    wk_true = c*wk_raw
    noise_sd = np.sqrt(wk_true.var()*(1/0.85 - 1) + 1e-9)
    base_d = np.repeat(base/7, 7)*dm
    yd = base_d + c*r_day + rng.normal(0, noise_sd/np.sqrt(7), nd)
    return spend, yd.reshape(NW, 7).sum(1), wk_true

# ---------------------------------------------------------------- diagnostics
def cands(spend_d, arm):
    spend_w = spend_d.reshape(NW, 7).sum(1)
    cols, meta = [], []
    for d in DEC_GRID:
        a = adstock(spend_w if arm == "w" else spend_d, d)
        for g in pct_nz(a, GAMMA_PCTS):
            for h in H_GRID:
                m = hill(a, g, h)
                cols.append(m if arm == "w" else m.reshape(NW, 7).sum(1))
                meta.append((d, g, h))
    return np.array(cols), meta

def fit_full(y, cols, proj):
    yr = proj.res(y); Mr = proj.res(cols)
    num = Mr@yr; den = (Mr*Mr).sum(1)
    den = np.where(den < 1e-12, np.inf, den)
    sse = yr@yr - num**2/den
    k = int(np.argmin(sse))
    return num[k]/den[k]*cols[k], float(sse[k]), k, float(yr@yr)

def holdout_rmse(y, cols, C):
    Ctr = C[:NTR]; p = Projector(Ctr)
    yr = p.res(y[:NTR]); Mr = p.res(cols[:, :NTR])
    num = Mr@yr; den = (Mr*Mr).sum(1)
    den = np.where(den < 1e-12, np.inf, den)
    k = int(np.argmin(yr@yr - num**2/den))
    Ztr = np.column_stack([Ctr, cols[k, :NTR]])
    coef, *_ = np.linalg.lstsq(Ztr, y[:NTR], rcond=None)
    pred = np.column_stack([C[NTR:], cols[k, NTR:]])@coef
    return float(np.sqrt(np.mean((y[NTR:] - pred)**2)))

def diagnose(spend_d, y, true_c):
    C = controls(NW); proj = Projector(C)
    cw, mw = cands(spend_d, "w"); cd, md = cands(spend_d, "d")
    ew, sw, kw, yy = fit_full(y, cw, proj)
    ed, sd_, kd, _ = fit_full(y, cd, proj)
    rw = holdout_rmse(y, cw, C); rd = holdout_rmse(y, cd, C)
    # daily-arm depth
    d_hat, g_hat, h_hat = md[kd]
    a = adstock(spend_d, d_hat)
    act = spend_d > 0
    depth = float(np.mean(a[act] > g_hat)) if act.any() else np.nan
    # spend-only screens
    wm = spend_d.reshape(NW, 7).mean(1)
    tot = spend_d.var() + 1e-12
    WV = 1 - wm.var()/tot
    ZS = float(np.mean(spend_d == 0))
    CV = float(spend_d.std()/(spend_d.mean() + 1e-12))
    return dict(bias_w=bias_pct(ew, true_c), bias_d=bias_pct(ed, true_c),
                bias_h=bias_pct(0.5*(ew + ed), true_c),
                D=100*(ew.sum() - ed.sum())/(abs(ed.sum()) + 1e-9),
                dR2=(sw - sd_)/yy, hgap=(rw - rd)/rd, sse_w=sw, sse_d=sd_, rm_w=rw, rm_d=rd,
                dhat_w=mw[kw][0], dhat_d=d_hat, h_d=h_hat, DEPTH=depth, WV=WV, ZS=ZS, CV=CV)

# ---------------------------------------------------------------- cells
def make_cells(reps, stress=False):
    out = []
    P = ["bursty", "smooth", "real"]; DL = [0.15, 0.5, 0.85]
    for d in DL:
        for dp in DEPTH_PCT:
            for sh in [1.0, 2.2]:
                for p in P:
                    out.append(("W1", "core", dict(delta=d, depth=dp, shape=sh, pattern=p)))
                    out.append(("W2", "weekly_true", dict(delta=d, depth=dp, shape=sh, pattern=p)))
    for tv in ["daily", "weekly"]:
        for kp in [0.0, 1.0]:
            for sh in [1.0, 2.2]:
                for d in DL:
                    for p in P:
                        out.append(("W3", f"tv_{tv}", dict(tv=tv, kappa=kp, shape=sh, delta=d, pattern=p)))
    for K in [4, 24]:
        for al in [0.3, 1.0]:
            for sh in [1.0, 2.2]:
                for d in DL:
                    for p in P:
                        out.append(("W4", f"sub{K}", dict(K=K, alpha=al, shape=sh, delta=d, pattern=p)))
    for al in ALIGN:
        for sh in [1.0, 2.2]:
            for d in DL:
                for p in P:
                    out.append(("W5", f"dow_{al}", dict(align=al, shape=sh, delta=d, pattern=p)))
    for d in DL:
        for p in P:
            for dp in DEPTH_PCT:
                out.append(("W6", "log1p", dict(form="log1p", delta=d, depth=dp, shape=1.0, pattern=p)))
            out.append(("W6", "linear", dict(form="linear", delta=d, depth="med", shape=1.0, pattern=p)))
            out.append(("W6", "power", dict(form="power", delta=d, depth="med", shape=1.0, pattern=p)))
            for sh in [1.0, 2.2]:
                out.append(("W6", "wearout", dict(form="wearout", delta=d, depth="med", shape=sh, pattern=p)))
    for p in P:
        for sh in [1.0, 2.2]:
            out.append(("W6", "twocomp", dict(form="twocomp", delta=0.5, depth="med", shape=sh, pattern=p)))
    if stress:
        for r2 in [0.7, 0.5, 0.3]:
            for d in DL:
                for sh in [1.0, 2.2]:
                    for p in P:
                        out.append(("W7", f"core_r2_{r2}", dict(delta=d, depth="med", shape=sh, pattern=p, r2=r2)))
        for r2 in [0.7, 0.5]:
            for d in DL:
                for sh in [1.0, 2.2]:
                    for p in P:
                        out.append(("W8", f"wtrue_r2_{r2}", dict(delta=d, depth="med", shape=sh, pattern=p, r2=r2)))
    return [(w, s, pr, r) for (w, s, pr) in out for r in range(reps)]

def one(world, sub, pr, rep):
    key = (PREFIX, world, sub, tuple(sorted(pr.items())), rep)
    rng = np.random.default_rng(seed_of(*key))
    if world == "W1":
        spend, y, tc = g_core(pr["delta"], pr["depth"], pr["shape"], pr["pattern"], rng)
    elif world == "W7":
        spend, y, tc = g_core(pr["delta"], pr["depth"], pr["shape"], pr["pattern"], rng, r2=pr["r2"])
    elif world == "W8":
        spend, y, tc = g_altform("weekly_true", pr["delta"], pr["depth"], pr["shape"], pr["pattern"], rng, r2=pr["r2"])
    elif world == "W2":
        spend, y, tc = g_altform("weekly_true", pr["delta"], pr["depth"], pr["shape"], pr["pattern"], rng)
    elif world == "W3":
        rz = np.random.default_rng(seed_of(*key, "z"))
        spend, y, tc = g_tv(pr["tv"], pr["kappa"], pr["delta"], pr["pattern"], pr["shape"], rng, rz)
    elif world == "W4":
        spend, y, tc = g_sub(pr["K"], pr["alpha"], pr["delta"], pr["shape"], pr["pattern"], rng)
    elif world == "W5":
        spend, y, tc = g_dow(pr["align"], pr["delta"], pr["shape"], pr["pattern"], rng)
    else:
        spend, y, tc = g_altform(pr["form"], pr["delta"], pr["depth"], pr["shape"], pr["pattern"], rng)
    row = diagnose(spend, y, tc)
    cellid = f"{world}|{sub}|" + "|".join(f"{k}={v}" for k, v in sorted(pr.items()))
    return dict(world=world, sub=sub, cell=cellid, rep=rep, delta=pr.get("delta"), shape=pr.get("shape"),
                pattern=pr.get("pattern"), **row)

if __name__ == "__main__":
    mode = sys.argv[1]
    reps = {"smoke": 1, "full": 100, "conf": 100}[mode]
    cs = make_cells(reps, stress=(mode == "conf"))
    print("runs", len(cs), flush=True)
    t0 = time.time()
    res = Parallel(n_jobs=2, batch_size=20, verbose=5)(delayed(one)(*c) for c in cs)
    pd.DataFrame(res).to_csv(f"results/SEL_{mode}.csv", index=False)
    print("done", round(time.time() - t0), "s", flush=True)
