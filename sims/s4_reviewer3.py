"""S4: Reviewer 3 simulations. 4a sub-daily truth; 4b alternative DGPs. Design in DESIGN.md."""
import sys, time
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from lib import *

def common_outcome(wk_raw, rng, n_weeks, r2=0.85):
    t = np.arange(n_weeks)
    base = 800 + .5*t + 30*np.sin(2*np.pi*t/52)
    wk_true = wk_raw*(base.std()/(wk_raw.std() + 1e-9))
    noise_sd = np.sqrt(wk_true.var()*(1/r2 - 1) + 1e-9)
    return base + wk_true + rng.normal(0, noise_sd, n_weeks), wk_true

# ---------------------------- 4a: sub-daily truth ----------------------------
def one_4a(K, alpha, delta, shape, pattern, rep, depth="med", n_weeks=156):
    rng = np.random.default_rng(seed_of("S4a", K, alpha, delta, depth, shape, pattern, rep))
    nd = n_weeks*7
    spend_d = gen_spend(pattern, rng, nd)
    if alpha == "uniform":
        shares = np.full((nd, K), 1.0/K)
    else:
        shares = rng.dirichlet(np.full(K, float(alpha)), nd)
    spend_f = (spend_d[:, None]*shares).reshape(-1)
    d_f = delta**(1.0/K)
    ad = adstock(spend_f, d_f)
    g = np.percentile(ad[ad > 0], DEPTH_PCT[depth])
    resp = hill(ad, g, shape)
    wk = resp.reshape(n_weeks, 7*K).sum(1)
    y, true_c = common_outcome(wk, rng, n_weeks)
    C = controls(n_weeks); proj = Projector(C)
    arms = {}
    spend_w = spend_d.reshape(n_weeks, 7).sum(1)
    arms["weekly"] = grid_weekly(y, spend_w, DEC_GRID, proj)
    arms["daily"] = grid_daily(y, spend_d, n_weeks, DEC_GRID, proj)
    arms["native"] = grid_daily(y, spend_f, n_weeks, DEC_GRID**(1.0/K), proj, per=7*K)
    m_or = wk
    b = best_fit(y, m_or[None, :], [delta], proj)[0]
    arms["oracle"] = (b*m_or, delta)
    return [dict(scen="S4a", K=K, alpha=str(alpha), delta=delta, depth=depth, shape=shape,
                 pattern=pattern, rep=rep, arm=a, bias=bias_pct(est, true_c)) for a, (est, d) in arms.items()]

def cells_4a(reps):
    return [(K, a, d, sh, p, r) for K in [4, 24] for a in [0.3, 1.0, "uniform"]
            for d in [0.15, 0.50, 0.85] for sh in [1.0, 2.2] for p in ["bursty", "smooth", "real"]
            for r in range(reps)]

# ---------------------------- 4b: alternative DGPs ----------------------------
def one_4b(form, delta, depth, shape, pattern, rep, n_weeks=156):
    rng = np.random.default_rng(seed_of("S4b", form, delta, depth, shape, pattern, rep))
    nd = n_weeks*7
    spend = gen_spend(pattern, rng, nd)
    spend_w = spend.reshape(n_weeks, 7).sum(1)
    if form == "weekly_true":
        ad = adstock(spend_w, delta)
        g = np.percentile(ad[ad > 0], DEPTH_PCT[depth])
        wk = hill(ad, g, shape); m_or = wk
    else:
        if form == "twocomp":
            ad = 0.6*adstock(spend, 0.2) + 0.4*adstock(spend, 0.9)
        else:
            ad = adstock(spend, delta)
        nz = ad[ad > 0]
        g = np.percentile(nz, DEPTH_PCT[depth])
        if form in ("hill_ref", "twocomp"):
            r = hill(ad, g, shape)
        elif form == "linear":
            r = ad.copy()
        elif form == "log1p":
            r = np.log1p(ad/g)
        elif form == "power":
            r = ad**0.5
        elif form == "wearout":
            recent = lfilter(np.ones(28)/28, [1.0], ad)
            wear = 1.0/(1.0 + 0.5*recent/(recent.mean() + 1e-9))
            r = wear*hill(ad, g, shape)
        else:
            raise ValueError(form)
        wk = r.reshape(n_weeks, 7).sum(1); m_or = wk
    y, true_c = common_outcome(wk, rng, n_weeks)
    C = controls(n_weeks); proj = Projector(C)
    arms = standard_arms(y, spend, n_weeks, delta, C, proj, reg=False, ext=(form in ("linear", "power", "log1p")))
    b = best_fit(y, m_or[None, :], [delta], proj)[0]
    arms["oracle"] = (b*m_or, delta)
    return [dict(scen="S4b", form=form, delta=delta, depth=depth, shape=shape, pattern=pattern,
                 rep=rep, arm=a, bias=bias_pct(est, true_c)) for a, (est, d) in arms.items()]

def cells_4b(reps):
    out = []
    P = ["bursty", "smooth", "real"]
    for d in [0.15, 0.5, 0.85]:
        for p in P:
            for r in range(reps):
                for dp in ["mild", "med", "deep"]:
                    for sh in [1.0, 2.2]:
                        out.append(("weekly_true", d, dp, sh, p, r))
                    out.append(("log1p", d, dp, 1.0, p, r))
                out.append(("linear", d, "med", 1.0, p, r))
                out.append(("power", d, "med", 1.0, p, r))
                for sh in [1.0, 2.2]:
                    out.append(("wearout", d, "med", sh, p, r))
    for p in P:
        for sh in [1.0, 2.2]:
            for r in range(reps):
                out.append(("twocomp", 0.5, "med", sh, p, r))
    return out

if __name__ == "__main__":
    which = sys.argv[1]; smoke = len(sys.argv) > 2 and sys.argv[2] == "smoke"
    if which == "4a":
        cs = cells_4a(1 if smoke else 100); fn = one_4a
    else:
        cs = cells_4b(1 if smoke else 100); fn = one_4b
    print("runs", len(cs), flush=True)
    t0 = time.time()
    res = Parallel(n_jobs=2, batch_size=20, verbose=5)(delayed(fn)(*c) for c in cs)
    df = pd.DataFrame([x for rows in res for x in rows])
    df.to_csv(f"results/S{which}{'_smoke' if smoke else ''}.csv", index=False)
    print("done", round(time.time() - t0), "s", flush=True)
