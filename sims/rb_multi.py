"""Robyn-equivalent multichannel search, weekly vs daily transform. Design: DESIGN_ROBYN.md (written before running).
An EQUIVALENT of Robyn's modelling loop built from the definitions in Meta's published code (robynpy 0.3.6 and the R package
documentation): geometric adstock, Hill with gamma as a fraction of the min-max range of the adstocked series,
glmnet-style ridge on standardised inputs with lambda = lambda_min + (lambda_max - lambda_min) * lambda_hp, NRMSE on a time-series
validation split, DECOMP.RSSD against spend shares, TwoPointsDE in Nevergrad, Pareto set over all evaluated models.
It is NOT the Robyn package."""
import os, sys, time
os.environ.setdefault("MCPREFIX", "RB")
import numpy as np, pandas as pd, nevergrad as ng
from joblib import Parallel, delayed
from scipy.signal import lfilter
import mc_run as M
from mc_run import make_market, cand_set, backfit, contribs, NW, ND

BUDGET = int(os.environ.get("RBBUDGET", "2000"))
TH = (0.01, 0.95); AL = (0.5, 3.0); GA = (0.05, 1.0); LA = (0.0, 1.0)
NTR, NVA = int(0.6*NW), int(0.2*NW)

class Engine:
    def __init__(self, spends, y, C, freq):
        self.K = K = len(spends); self.freq = freq; self.y = y
        self.base = spends.reshape(K, NW, 7).sum(2) if freq == "W" else spends
        self.X0 = C[:, 1:]                                   # trend, season, price (intercept handled by ridge)
        self.spend_share = spends.sum(1)/spends.sum()
        self.tr = slice(0, NTR); self.va = slice(NTR, NTR + NVA)
    def decode(self, z):
        K = self.K; p = np.asarray(z).reshape(K, 3); lam = z[-1] if False else None
        return p
    def media(self, th, al, ga):
        cols = []
        for k in range(self.K):
            a = lfilter([1.0], [1.0, -th[k]], self.base[k])
            infl = a.min() + (a.max() - a.min())*ga[k]
            m = a**al[k]/(a**al[k] + max(infl, 1e-9)**al[k])
            cols.append(m if self.freq == "W" else m.reshape(NW, 7).sum(1))
        return np.array(cols)
    def fit(self, th, al, ga, lam_hp):
        m = self.media(th, al, ga)
        Z = np.column_stack([m.T, self.X0]); tr = self.tr
        Ztr = Z[tr]; mu = Ztr.mean(0); sd = Ztr.std(0); sd[sd < 1e-12] = np.inf
        Zs = (Z - mu)/sd; ytr = self.y[tr]; yc = ytr - ytr.mean(); n = len(ytr)
        Zt = Zs[tr]
        # lambda as in Robyn: lambda_max = max|X_s' y| / (0.001 n), sequence ratio 1e-4, then x 0.1; linear map by lambda_hp
        lmax = np.max(np.abs(Zt.T@yc))/(0.001*n)*0.1; lmin = lmax*1e-4
        lam = lmin + (lmax - lmin)*lam_hp
        K = self.K; act = np.ones(Z.shape[1], bool)
        for _ in range(K + 1):
            A = Zt[:, act].T@Zt[:, act]/n + lam*np.eye(act.sum()); b = np.zeros(Z.shape[1])
            b[act] = np.linalg.solve(A, Zt[:, act].T@yc/n)
            neg = (b[:K] < 0) & act[:K]
            if not neg.any(): break
            act[:K][neg] = False
        braw = b/sd; icpt = ytr.mean() - (mu/sd)@b if False else ytr.mean() - mu@braw
        pred = icpt + Z@braw
        return m, braw, pred
    def evaluate(self, x):
        K = self.K; th = TH[0] + x[:K]*(TH[1] - TH[0]); al = AL[0] + x[K:2*K]*(AL[1] - AL[0])
        ga = GA[0] + x[2*K:3*K]*(GA[1] - GA[0]); lam_hp = x[3*K]
        m, braw, pred = self.fit(th, al, ga, lam_hp)
        yv = self.y[self.va]; rmse = np.sqrt(np.mean((yv - pred[self.va])**2)); nrmse = rmse/max(yv.max() - yv.min(), 1e-9)
        eff = braw[:K]*m.sum(1); tot = eff.sum()
        if tot <= 1e-9: rssd = 10.0
        else:
            es = eff/tot; rssd = np.sqrt(np.sum((es - self.spend_share)**2))
            rssd *= 1 + np.mean(np.round(es, 4) == 0)           # rssd_zero_penalty
        return nrmse, rssd, eff
    def contribution(self, x):
        K = self.K; th = TH[0] + x[:K]*(TH[1] - TH[0]); al = AL[0] + x[K:2*K]*(AL[1] - AL[0])
        ga = GA[0] + x[2*K:3*K]*(GA[1] - GA[0]); m, braw, _ = self.fit(th, al, ga, x[3*K])
        return braw[:K, None]*m

def pareto_mask(F):
    n = len(F); keep = np.ones(n, bool)
    order = np.lexsort((F[:, 1], F[:, 0])); best2 = np.inf
    for i in order:
        if F[i, 1] < best2 - 1e-15: best2 = F[i, 1]
        else: keep[i] = False
    return keep

def search(eng, seed, multi):
    K = eng.K; dim = 3*K + 1
    p = ng.p.Array(init=0.5*np.ones(dim), lower=np.zeros(dim), upper=np.ones(dim)); p.random_state.seed(seed)
    opt = ng.optimizers.TwoPointsDE(parametrization=p, budget=BUDGET, num_workers=1)
    X, F = [], []
    for _ in range(BUDGET):
        c = opt.ask(); x = np.clip(c.value, 0, 1); nr, rs, _ = eng.evaluate(x)
        X.append(x); F.append((nr, rs))
        opt.tell(c, [nr, rs] if multi else nr)
    return np.array(X), np.array(F)

def select(X, F, rule):
    keep = pareto_mask(F); idx = np.where(keep)[0]; Fp = F[idx]
    if rule == "nrmse": j = idx[np.argmin(Fp[:, 0])]
    elif rule == "rssd": j = idx[np.argmin(Fp[:, 1])]
    else:
        n0 = (Fp[:, 0] - Fp[:, 0].min())/max(np.ptp(Fp[:, 0]), 1e-12); n1 = (Fp[:, 1] - Fp[:, 1].min())/max(np.ptp(Fp[:, 1]), 1e-12)
        j = idx[np.argmin(n0**2 + n1**2)]
    return j

def bias_rows(est, contrib):
    tot = 100*(est.sum() - contrib.sum())/contrib.sum()
    ch = 100*(est.sum(1) - contrib.sum(1))/(contrib.sum(1) + 1e-12)
    return tot, np.abs(ch).mean()

def one(scen, m):
    cfg, spends, contrib, y, C = make_market(scen, m); K = cfg["K"]
    row = dict(scen=scen, m=m, K=K, n_weekly=sum(t == "WEEKLY" for t in cfg["truths"]))
    chan = {}
    cands = {"w": [cand_set(spends[k], "w") for k in range(K)], "d": [cand_set(spends[k], "d") for k in range(K)]}
    for nm, assign in (("gridW", ["w"]*K), ("gridD", ["d"]*K)):
        est = contribs(y, C, backfit(y, C, cands, assign)[1]); row[f"bias_{nm}"], chan[nm] = bias_rows(est, contrib)
    est = contribs(y, C, list(contrib)); row["bias_OT"], chan["OT"] = bias_rows(est, contrib)
    ts = contrib.sum(1)/contrib.sum(); sp = spends.sum(1)/spends.sum()
    row["truth_rssd"] = float(np.sqrt(np.sum((ts - sp)**2)))
    seed = int(np.random.default_rng([abs(hash((scen, m))) % (2**31)]).integers(2**31)) if False else (m*7919 + len(scen)*104729 + sum(map(ord, scen))) % (2**31)
    for fr, fn in (("W", "W"), ("D", "D")):
        eng = Engine(spends, y, C, fr)
        # (a) single objective, validation NRMSE only
        X, F = search(eng, seed, multi=False); j = int(np.argmin(F[:, 0]))
        row[f"bias_rbSO_{fn}"], chan[f"rbSO_{fn}"] = bias_rows(eng.contribution(X[j]), contrib)
        # (b) multi-objective NRMSE + RSSD, three selection rules from the Pareto set
        X, F = search(eng, seed + 1, multi=True)
        for rule in ("nrmse", "rssd", "bal"):
            j = select(X, F, rule)
            row[f"bias_rbMO{rule}_{fn}"], chan[f"rbMO{rule}_{fn}"] = bias_rows(eng.contribution(X[j]), contrib)
    for k, v in chan.items(): row[f"chbias_{k}"] = v
    return row

if __name__ == "__main__":
    mode = sys.argv[1]; scens = ["M1", "M2", "M3", "M7"]
    n = {"time": 1, "smoke": 4, "full": 100}[mode]
    jobs = [(s, m) for s in scens for m in range(n)]
    print("markets", len(jobs), "budget", BUDGET, flush=True); t0 = time.time()
    res = Parallel(n_jobs=int(os.environ.get("NJOBS", "2")), batch_size=1, verbose=5)(delayed(one)(*j) for j in jobs)
    pd.DataFrame(res).to_csv(f"results/RB_{mode}.csv", index=False); print("done", round(time.time() - t0), "s")
