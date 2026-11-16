"""S1: time-varying effectiveness (Reviewer 1, point 1A). Design in DESIGN.md."""
import sys, itertools, time
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from lib import *

def gen_z(kind, rng, n_weeks):
    nd = n_weeks*7
    if kind == "none":
        return np.zeros(nd)
    if kind == "daily":
        phi = 0.6
        e = rng.normal(0, 1, nd + 100)
        z = lfilter([np.sqrt(1 - phi**2)], [1, -phi], e)[100:]
    elif kind == "weekly":
        phi = 0.8
        e = rng.normal(0, 1, n_weeks + 50)
        zw = lfilter([np.sqrt(1 - phi**2)], [1, -phi], e)[50:]
        z = np.repeat(zw, 7)
    elif kind == "drift":
        t = np.arange(nd)
        slow = lfilter([np.sqrt(1 - .995**2)], [1, -.995], rng.normal(0, 1, nd + 200))[200:]
        z = 0.8*np.sin(2*np.pi*t/(104*7) + rng.uniform(0, 2*np.pi)) + 0.6*slow
    else:
        raise ValueError(kind)
    return (z - z.mean())/(z.std() + 1e-9)

def gen_spend_tilted(pattern, rng, nd, z, kappa):
    tilt = np.exp(kappa*z)
    if pattern == "bursty":
        ln = rng.lognormal(0, 1.0, nd); u = rng.random(nd)
        p = np.clip(0.4*tilt/tilt.mean(), 0, 0.95)
        return ln*(u > 1 - p)*40*tilt
    if pattern == "smooth":
        return rng.lognormal(0, .3, nd)*12*tilt
    if pattern == "real":
        v = rng.choice(real_shapes(), nd); u = rng.random(nd)
        p = np.clip(0.7*tilt/tilt.mean(), 0, 0.97)
        return v*(u > 1 - p)*tilt
    raise ValueError(pattern)

def one(form, tv, kappa, delta, pattern, shape, rep, n_weeks=156, r2=0.85, sig_e=0.5):
    tag = "S1" + form
    rng = np.random.default_rng(seed_of(tag, tv, kappa, delta, pattern, shape, rep))
    rz = np.random.default_rng(seed_of(tag + "z", tv, kappa, delta, pattern, shape, rep))
    nd = n_weeks*7
    z = gen_z(tv, rz, n_weeks)
    spend = gen_spend_tilted(pattern, rng, nd, z, kappa)
    ad = adstock(spend, delta)
    e = np.exp(sig_e*z - sig_e**2/2) if tv != "none" else np.ones(nd)
    if form == "linear":
        resp = e*ad
    else:
        g = np.percentile(ad[ad > 0], DEPTH_PCT["med"])
        resp = e*hill(ad, g, shape)
    wk = resp.reshape(n_weeks, 7).sum(1)
    t = np.arange(n_weeks)
    base = 800 + .5*t + 30*np.sin(2*np.pi*t/52)
    wk_true = wk*(base.std()/(wk.std() + 1e-9))
    noise_sd = np.sqrt(wk_true.var()*(1/r2 - 1) + 1e-9)
    y = base + wk_true + rng.normal(0, noise_sd, n_weeks)
    C = controls(n_weeks); proj = Projector(C)
    arms = standard_arms(y, spend, n_weeks, delta, C, proj, ext=(form == "linear"))
    if form == "linear":
        m_or = ad.reshape(n_weeks, 7).sum(1)
    else:
        m_or = hill(ad, g, shape).reshape(n_weeks, 7).sum(1)
    b = best_fit(y, m_or[None, :], [delta], proj)[0]
    arms["oracle"] = (b*m_or, delta)
    return [dict(scen="S1", form=form, tv=tv, kappa=kappa, delta=delta, pattern=pattern,
                 shape=shape, rep=rep, arm=a, est_decay=d, bias=bias_pct(est, wk_true))
            for a, (est, d) in arms.items()]

def cells_main(reps):
    out = []
    for tv, kappa in [("none", 0.0)] + [(tv, k) for tv in ["daily", "weekly", "drift"] for k in [0.0, 0.5, 1.0]]:
        for d in [0.15, 0.50, 0.85]:
            for p in ["bursty", "smooth", "real"]:
                for r in range(reps):
                    out.append(("linear", tv, kappa, d, p, 0.0, r))
    return out

def cells_hill(reps):
    out = []
    for kappa in [0.0, 1.0]:
        for sh in [1.0, 2.2]:
            for d in [0.15, 0.50, 0.85]:
                for p in ["bursty", "smooth", "real"]:
                    for r in range(reps):
                        out.append(("hill", "daily", kappa, d, p, sh, r))
    return out

if __name__ == "__main__":
    smoke = len(sys.argv) > 1 and sys.argv[1] == "smoke"
    cells = cells_main(2 if smoke else 200) + cells_hill(2 if smoke else 100)
    print("runs:", len(cells), flush=True)
    t0 = time.time()
    res = Parallel(n_jobs=2, batch_size=50, verbose=5)(delayed(one)(*c) for c in cells)
    df = pd.DataFrame([x for rows in res for x in rows])
    df.to_csv("results/S1_smoke.csv" if smoke else "results/S1_timevarying.csv", index=False)
    print("done in", round(time.time() - t0), "s", flush=True)
