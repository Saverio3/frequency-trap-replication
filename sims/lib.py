"""Fast re-implementation of the Frequency Trap engine (v1.2 DGP + arms).
Fits use partialled-out OLS over the same candidate grid and the same
tie-breaking (first minimum in d, gamma, h loop order) as the original."""
import hashlib, os
import numpy as np, pandas as pd
from scipy.signal import lfilter

DEC_GRID = np.linspace(.05, .95, 12)
GAMMA_PCTS = [5, 15, 30, 50, 70, 85, 95]
H_GRID = [1.0, 1.6, 2.2]
DEPTH_PCT = {"mild": 90, "med": 50, "deep": 25}
CLASS_RANGE = {0.15: (0.05, 0.35), 0.50: (0.30, 0.70), 0.85: (0.65, 0.95)}
HERE = os.path.dirname(os.path.abspath(__file__))

def seed_of(*cell):
    return int(hashlib.md5("|".join(map(str, cell)).encode()).hexdigest()[:8], 16)

def controls(n):
    t = np.arange(n)
    return np.column_stack([np.ones(n), t, np.sin(2*np.pi*t/52), np.cos(2*np.pi*t/52)])

def adstock(x, d):
    return lfilter([1.0], [1.0, -d], x, axis=-1)

def hill(x, g, h):
    x = np.maximum(x, 0.0)
    return x**h/(x**h + g**h)

_REAL = None
def real_shapes():
    global _REAL
    if _REAL is None:
        v = pd.read_csv(os.path.join(HERE, "fb.csv"))["spent"].values.astype(float)
        _REAL = v[v > 0]
    return _REAL

def gen_spend(pattern, rng, nd):
    if pattern == "bursty":
        return rng.lognormal(0, 1.0, nd)*(rng.random(nd) > .6)*40
    if pattern == "smooth":
        return rng.lognormal(0, .3, nd)*12
    if pattern == "real":
        return rng.choice(real_shapes(), nd)*(rng.random(nd) > .3)
    raise ValueError(pattern)

def pct_nz(a, pcts):
    nz = a[a > 0]
    if nz.size == 0:
        return np.ones(len(pcts))
    return np.percentile(nz, pcts)

class Projector:
    """Residualise on a control matrix once."""
    def __init__(self, C):
        self.Q, _ = np.linalg.qr(C)
    def res(self, A):
        return A - (A @ self.Q) @ self.Q.T

def best_fit(y, cand_cols, cand_meta, proj, yr=None):
    """cand_cols: (ncand, nobs) candidate transformed series aligned with y.
    Returns (coef, column, meta) of the min-SSE candidate (first on ties)."""
    if yr is None:
        yr = proj.res(y)
    Mr = proj.res(cand_cols)
    num = Mr @ yr
    den = (Mr*Mr).sum(1)
    den = np.where(den < 1e-12, np.inf, den)
    sse = yr @ yr - num**2/den
    k = int(np.argmin(sse))
    return num[k]/den[k], cand_cols[k], cand_meta[k]

def grid_weekly(y, spend_w, decs, proj, extra_mult=()):
    cols, meta = [], []
    for d in decs:
        a = adstock(spend_w, d)
        gs = np.concatenate([pct_nz(a, GAMMA_PCTS), [m*max(a.max(), 1e-9) for m in extra_mult]])
        for g in gs:
            for h in H_GRID:
                cols.append(hill(a, g, h)); meta.append(d)
    b, col, d = best_fit(y, np.array(cols), meta, proj)
    return b*col, d

def grid_daily(y, spend_d, n_weeks, decs, proj, per=7, extra_mult=()):
    cols, meta = [], []
    for d in decs:
        a = adstock(spend_d, d)
        gs = np.concatenate([pct_nz(a, GAMMA_PCTS), [m*max(a.max(), 1e-9) for m in extra_mult]])
        for g in gs:
            for h in H_GRID:
                cols.append(hill(a, g, h).reshape(n_weeks, per).sum(1)); meta.append(d)
    b, col, d = best_fit(y, np.array(cols), meta, proj)
    return b*col, d

def bias_pct(est, true):
    return 100*(est.sum() - true.sum())/true.sum()

def standard_arms(y, spend, n_weeks, delta, C, proj=None, reg=True, ext=False):
    """weekly, dailyT, dailyT_reg estimates on weekly KPI y."""
    proj = proj or Projector(C)
    spend_w = spend.reshape(n_weeks, 7).sum(1)
    out = {}
    out["weekly"] = grid_weekly(y, spend_w, DEC_GRID, proj)
    out["dailyT"] = grid_daily(y, spend, n_weeks, DEC_GRID, proj)
    if ext:  # near-linear candidates added (gamma = 5x and 20x the max adstock)
        out["weekly_ext"] = grid_weekly(y, spend_w, DEC_GRID, proj, extra_mult=(5, 20))
        out["dailyT_ext"] = grid_daily(y, spend, n_weeks, DEC_GRID, proj, extra_mult=(5, 20))
    if reg:
        lo, hi = CLASS_RANGE[delta]
        out["dailyT_reg"] = grid_daily(y, spend, n_weeks, np.linspace(lo, hi, 6), proj)
    return out

# ------------------------------------------------------------------
# Original paper DGP (verbatim logic of simA, core cell)
def simA_core(delta, depth, shape, pattern, rng, n_weeks=156, eff="med", r2=0.85):
    nd = n_weeks*7
    spend = gen_spend(pattern, rng, nd)
    ad = adstock(spend, delta)
    g = np.percentile(ad[ad > 0], DEPTH_PCT[depth])
    resp = hill(ad, g, shape)
    wk = resp.reshape(n_weeks, 7).sum(1)
    t = np.arange(n_weeks)
    base = 800 + .5*t + 30*np.sin(2*np.pi*t/52)
    eff_mult = {"low": .5, "med": 1.0, "high": 2.0}[eff]
    wk_true = wk*eff_mult*(base.std()/(wk.std() + 1e-9))
    noise_sd = np.sqrt(wk_true.var()*(1/r2 - 1) + 1e-9)
    y = base + wk_true + rng.normal(0, noise_sd, n_weeks)
    return spend, y, wk_true

def one_A_core(delta, depth, shape, pattern, rep, cell="core"):
    rng = np.random.default_rng(seed_of("A", delta, depth, shape, pattern, rep, cell))
    n_weeks = 156
    spend, y, true_c = simA_core(delta, depth, shape, pattern, rng)
    C = controls(n_weeks); proj = Projector(C)
    arms = standard_arms(y, spend, n_weeks, delta, C, proj)
    ad_t = adstock(spend, delta)
    g_t = np.percentile(ad_t[ad_t > 0], DEPTH_PCT[depth])
    m_or = hill(ad_t, g_t, shape).reshape(n_weeks, 7).sum(1)
    b = best_fit(y, m_or[None, :], [delta], proj)[0]
    arms["oracle"] = (b*m_or, delta)
    return {a: bias_pct(est, true_c) for a, (est, d) in arms.items()}, {a: d for a, (est, d) in arms.items()}
