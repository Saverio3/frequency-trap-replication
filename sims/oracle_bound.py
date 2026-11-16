"""Upper bound on ANY test: the likelihood-ratio classifier that KNOWS the true parameters (decay, depth, shape, baseline).
Compares weekly-true vs daily-true worlds on the same spend. Practitioners know less, so real tests cannot beat this."""
import numpy as np, pandas as pd
from lib import *
def build(delta, shape, pattern, nw, rng):
    nd = nw*7
    spend = gen_spend(pattern, rng, nd)
    ad = adstock(spend, delta); g = np.percentile(ad[ad > 0], 50)
    resp_d = hill(ad, g, shape).reshape(nw, 7).sum(1)
    sw = spend.reshape(nw, 7).sum(1); aw = adstock(sw, delta); gw = np.percentile(aw[aw > 0], 50)
    resp_w = hill(aw, gw, shape)
    t = np.arange(nw); base = 800 + .5*t + 30*np.sin(2*np.pi*t/52)
    sc = lambda r: r*(base.std()/(r.std() + 1e-9))
    return spend, base, sc(resp_d), sc(resp_w)
rows = []
for nw in [104, 156, 312]:
    for r2 in [0.85, 0.7, 0.5, 0.3]:
        correct = {"daily": [], "weekly": []}
        for delta in [0.15, 0.5, 0.85]:
            for shape in [1.0, 2.2]:
                for pattern in ["bursty", "smooth", "real"]:
                    for rep in range(60):
                        rng = np.random.default_rng(seed_of("ORB", nw, r2, delta, shape, pattern, rep))
                        spend, base, wd, ww = build(delta, shape, pattern, nw, rng)
                        sd_d = np.sqrt(wd.var()*(1/r2 - 1) + 1e-9); sd_w = np.sqrt(ww.var()*(1/r2 - 1) + 1e-9)
                        for truth in ["daily", "weekly"]:
                            mu_t, sd_t = (base + wd, sd_d) if truth == "daily" else (base + ww, sd_w)
                            y = mu_t + rng.normal(0, sd_t, nw)
                            ll = lambda mu, s: (-nw*np.log(s) - 0.5*((y - mu)**2).sum()/s**2)
                            pred = "daily" if ll(base + wd, sd_d) > ll(base + ww, sd_w) else "weekly"
                            correct[truth].append(pred == truth)
        tpr, tnr = np.mean(correct["daily"]), np.mean(correct["weekly"])
        rows.append(dict(weeks=nw, R2_signal=r2, oracle_daily_correct=round(tpr, 3), oracle_weekly_correct=round(tnr, 3), oracle_balanced=round((tpr + tnr)/2, 3)))
print(pd.DataFrame(rows).to_string(index=False))
