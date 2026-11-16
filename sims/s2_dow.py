"""S2: day-of-week seasonality (Reviewer 1, point 1B). Design in DESIGN.md."""
import sys, time
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from lib import *

PROFILE = np.array([-.4, -.4, -.2, 0.0, .8, 1.0, -.8])   # Mon..Sun, sums to 0
ALIGN = {"neutral": np.array([1, 1, 1, 1, 1, 1, 1.]),
         "thursday": np.array([1, 1, 1, 3, 1, 1, 1.]),
         "peak": np.array([1, 1, 1, 1, 3, 3, 1.]),
         "offpeak": np.array([3, 3, 1, 1, 1, 1, 1.])}

def grid_daily_kpi(yd, spend_d, decs, proj):
    cols, meta = [], []
    for d in decs:
        a = adstock(spend_d, d)
        gs = pct_nz(a, GAMMA_PCTS)
        for g in gs:
            for h in H_GRID:
                cols.append(hill(a, g, h)); meta.append(d)
    b, col, d = best_fit(yd, np.array(cols), meta, proj)
    return b*col, d

def one(strength, align, form, delta, pattern, shape, rep, n_weeks=156, r2=0.85):
    rng = np.random.default_rng(seed_of("S2", strength, align, form, delta, pattern, shape, rep))
    nd = n_weeks*7
    dow = np.tile(np.arange(7), n_weeks)
    spend = gen_spend(pattern, rng, nd)*ALIGN[align][dow]
    dm = 1 + strength*PROFILE[dow]
    ad = adstock(spend, delta)
    g = np.percentile(ad[ad > 0], DEPTH_PCT["med"])
    resp = hill(ad, g, shape)
    r_day = resp*(dm if form == "mult" else 1.0)
    wk_raw = r_day.reshape(n_weeks, 7).sum(1)
    t = np.arange(n_weeks)
    base = 800 + .5*t + 30*np.sin(2*np.pi*t/52)
    c = base.std()/(wk_raw.std() + 1e-9)
    wk_true = c*wk_raw
    noise_sd = np.sqrt(wk_true.var()*(1/r2 - 1) + 1e-9)
    base_d = np.repeat(base/7, 7)*dm
    yd = base_d + c*r_day + rng.normal(0, noise_sd/np.sqrt(7), nd)
    y = yd.reshape(n_weeks, 7).sum(1)
    C = controls(n_weeks); proj = Projector(C)
    arms = standard_arms(y, spend, n_weeks, delta, C, proj, reg=False)
    td = np.arange(nd)/7.0
    Cd = np.column_stack([np.ones(nd), td, np.sin(2*np.pi*td/52), np.cos(2*np.pi*td/52)])
    arms["dailyKPI_noDOW"] = grid_daily_kpi(yd, spend, DEC_GRID, Projector(Cd))
    D = np.column_stack([(dow == k).astype(float) for k in range(6)])
    arms["dailyKPI_DOW"] = grid_daily_kpi(yd, spend, DEC_GRID, Projector(np.column_stack([Cd, D])))
    m_or = r_day.reshape(n_weeks, 7).sum(1)
    b = best_fit(y, m_or[None, :], [delta], proj)[0]
    arms["oracle"] = (b*m_or, delta)
    return [dict(scen="S2", strength=strength, align=align, form=form, delta=delta, pattern=pattern,
                 shape=shape, rep=rep, arm=a, est_decay=d, bias=bias_pct(est, wk_true))
            for a, (est, d) in arms.items()]

def cells(reps):
    combos = [(0.0, a, "add") for a in ALIGN] + \
             [(s, a, f) for s in [0.3, 0.6] for a in ALIGN for f in ["add", "mult"]]
    out = []
    for (s, a, f) in combos:
        for d in [0.15, 0.50, 0.85]:
            for sh in [1.0, 2.2]:
                for p in ["bursty", "smooth", "real"]:
                    for r in range(reps):
                        out.append((s, a, f, d, p, sh, r))
    return out

if __name__ == "__main__":
    smoke = len(sys.argv) > 1 and sys.argv[1] == "smoke"
    cs = cells(1 if smoke else 100)
    print("runs:", len(cs), flush=True)
    t0 = time.time()
    res = Parallel(n_jobs=2, batch_size=50, verbose=5)(delayed(one)(*c) for c in cs)
    df = pd.DataFrame([x for rows in res for x in rows])
    df.to_csv("results/S2_smoke.csv" if smoke else "results/S2_dow.csv", index=False)
    print("done in", round(time.time() - t0), "s", flush=True)
