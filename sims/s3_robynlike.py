"""S3: Robyn-style continuous search, weekly vs daily transformation (Reviewer 1, point 2).
EMULATION of Robyn's ingredients (Nevergrad TwoPointsDE, geometric adstock, Hill with
Robyn-style gamma on the range, ridge with searched lambda, trend+season controls).
It is NOT the Robyn package. Same search for both arms; only the aggregation level differs."""
import sys, time
import numpy as np, pandas as pd
import nevergrad as ng
from joblib import Parallel, delayed
from lib import *

BUDGET = 800
LO = np.array([0.01, 0.5, 0.05, 0.0])   # theta, alpha, gamma, lambda_u
HI = np.array([0.95, 3.0, 1.00, 1.0])

def robyn_hill(a, alpha, gamma):
    rng_ = a.max() - a.min()
    infl = a.min() + rng_*gamma
    return a**alpha/(a**alpha + max(infl, 1e-9)**alpha)

def make_objective(y, spend_d, n_weeks, arm, variant):
    nd = n_weeks*7
    spend_w = spend_d.reshape(n_weeks, 7).sum(1)
    t = np.arange(n_weeks)
    ctrl = np.column_stack([t, np.sin(2*np.pi*t/52), np.cos(2*np.pi*t/52)]).astype(float)
    ctrl = (ctrl - ctrl.mean(0))/ctrl.std(0)
    ys = (y - y.mean())/y.std()
    ntr = n_weeks if variant == "I" else int(0.6*n_weeks)
    nva = n_weeks - ntr if variant == "I" else int(0.2*n_weeks)
    tr = slice(0, ntr); va = slice(ntr, ntr + nva) if variant == "V" else slice(0, ntr)
    def transform(theta, alpha, gamma):
        if arm == "weekly":
            return robyn_hill(adstock(spend_w, theta), alpha, gamma)
        a = adstock(spend_d, theta)
        return robyn_hill(a, alpha, gamma).reshape(n_weeks, 7).sum(1)
    def fit(theta, alpha, gamma, lam_u):
        m = transform(theta, alpha, gamma)
        sd_m = m.std()
        if sd_m < 1e-9:
            return None
        mz = (m - m.mean())/sd_m
        Z = np.column_stack([mz, ctrl])
        Ztr, ytr = Z[tr], ys[tr]
        ytr_c = ytr - ytr.mean()
        Ztr_c = Ztr - Ztr.mean(0)
        n = len(ytr)
        lam_max = np.max(np.abs(Ztr_c.T@ytr_c))/(n*0.001)
        lam = lam_max*10**(-4*(1 - lam_u))
        A = Ztr_c.T@Ztr_c/n + lam*np.eye(Z.shape[1])
        b = np.linalg.solve(A, Ztr_c.T@ytr_c/n)
        if b[0] < 0:   # sign constraint on paid media
            Zc = Ztr_c[:, 1:]
            A2 = Zc.T@Zc/n + lam*np.eye(Zc.shape[1])
            b = np.concatenate([[0.0], np.linalg.solve(A2, Zc.T@ytr_c/n)])
        icpt = ytr.mean() - Ztr.mean(0)@b
        pred = icpt + Z@b
        return m, sd_m, b, pred
    def loss(x):
        theta, alpha, gamma, lam_u = x
        f = fit(theta, alpha, gamma, lam_u)
        if f is None:
            return 10.0
        pred = f[3]
        return float(np.sqrt(np.mean((ys[va] - pred[va])**2))/(ys.max() - ys.min()))
    def contribution(x):
        theta, alpha, gamma, lam_u = x
        m, sd_m, b, pred = fit(theta, alpha, gamma, lam_u)
        b_raw = b[0]*y.std()/sd_m
        return b_raw*m
    return loss, contribution

def search(y, spend_d, n_weeks, arm, variant, seed):
    loss, contrib = make_objective(y, spend_d, n_weeks, arm, variant)
    p = ng.p.Array(init=0.5*np.ones(4), lower=np.zeros(4), upper=np.ones(4))
    p.random_state.seed(seed)
    opt = ng.optimizers.TwoPointsDE(parametrization=p, budget=BUDGET, num_workers=1)
    for _ in range(BUDGET):
        z = opt.ask()
        opt.tell(z, loss(LO + z.value*(HI - LO)))
    best = opt.provide_recommendation().value
    x = LO + best*(HI - LO)
    return contrib(x), x

def one(delta, depth, shape, pattern, rep):
    rng = np.random.default_rng(seed_of("S3", delta, depth, shape, pattern, rep))
    n_weeks = 156
    spend, y, true_c = simA_core(delta, depth, shape, pattern, rng)
    C = controls(n_weeks); proj = Projector(C)
    arms = standard_arms(y, spend, n_weeks, delta, C, proj, reg=False)
    rows = []
    for a, (est, d) in arms.items():
        rows.append(dict(arm="grid_" + a, bias=bias_pct(est, true_c), theta=d))
    for variant in ["I", "V"]:
        for arm in ["weekly", "daily"]:
            seed = seed_of("S3ng", delta, depth, shape, pattern, rep, variant, arm) % (2**31)
            est, x = search(y, spend, n_weeks, arm, variant, seed)
            rows.append(dict(arm=f"rb{variant}_{arm}", bias=bias_pct(est, true_c), theta=x[0]))
    return [dict(scen="S3", delta=delta, depth=depth, shape=shape, pattern=pattern, rep=rep, **r) for r in rows]

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    reps = {"smoke": 2, "bench": 1, "full": 40}[mode]
    cells = [(d, dp, sh, p, r) for d in [0.15, 0.5, 0.85] for dp in ["mild", "med", "deep"]
             for sh in [1.0, 2.2] for p in ["bursty", "smooth", "real"] for r in range(reps)]
    if mode == "bench":
        cells = cells[:4]
    print("runs", len(cells), flush=True)
    t0 = time.time()
    res = Parallel(n_jobs=2, batch_size=2, verbose=5)(delayed(one)(*c) for c in cells)
    df = pd.DataFrame([x for rows in res for x in rows])
    df.to_csv(f"results/S3_{mode}.csv", index=False)
    print("done", round(time.time() - t0), "s", flush=True)
