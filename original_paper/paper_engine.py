"""
paper_engine.py  v1.2 -- FINAL-RUN ENGINE
"Temporal Aggregation and Disaggregation in Nonlinear Marketing Mix Models"

Implements design freeze + logged amendments (2026-08-10):
- Part A: finer grids; est. decay recorded; sensitivity cells (length, effect,
  noise); robustness cells (atan saturation family; Weibull daily adstock DGP);
  'real' spend cells FAIL LOUDLY if datasets absent.
- Part B: GLS Chow-Lin (AR(1), ML rho); windows {4,8,12,24,36} x {SMA-trailing,
  SMA-centered, EMA} for monthly AND quarterly; redesigned seasonal DGP
  (amplitude/phase drift -> partially identified; identification note stands).
- Paired significance: per-cell paired differences vs `weekly` (A) / vs `linear`
  (B) with Monte-Carlo SEs.
- Six publication figures.

SMOKE=True  -> reduced everything, minutes (verify end-to-end)
SMOKE=False -> full design. NOTE: heavier than v1.1 -- expect roughly a full
              day on a typical machine. Run overnight+; progress prints per block.
"""

import os, itertools, hashlib, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from scipy.linalg import toeplitz
from scipy.interpolate import CubicSpline
from sklearn.linear_model import ElasticNetCV
from sklearn.ensemble import GradientBoostingRegressor
from joblib import Parallel, delayed
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ============================ CONFIG ==================================
SMOKE = False
RUN_PARTS = "AB"            # "A", "B", or "AB"
REPS_CORE = 4 if SMOKE else 200
REPS_SENS = 3 if SMOKE else 100
OUT = "results"; os.makedirs(OUT, exist_ok=True)

WINDOWS = [4, 8, 12, 24, 36]
DEC_GRID = np.linspace(.05, .95, 6 if SMOKE else 12)
GAMMA_PCTS = [10, 50, 90] if SMOKE else [5, 15, 30, 50, 70, 85, 95]
H_GRID = [1.0] if SMOKE else [1.0, 1.6, 2.2]

plt.rcParams.update({
    "font.family": "serif", "font.size": 11, "axes.titlesize": 12,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": .25, "figure.dpi": 300,
    "legend.frameon": False})
PAL = {"weekly": "#D55E00", "dailyT": "#0072B2", "dailyT_reg": "#009E73",
       "oracle": "#7F7F7F", "sma": "#D55E00", "cma": "#E69F00", "ema": "#56B4E9"}

def seed_of(*cell):
    return int(hashlib.md5("|".join(map(str, cell)).encode()).hexdigest()[:8], 16)

def controls(n):
    t = np.arange(n)
    return np.column_stack([np.ones(n), t, np.sin(2*np.pi*t/52), np.cos(2*np.pi*t/52)])

def ols(X, y):
    b, *_ = np.linalg.lstsq(X, y, rcond=None); return b

def mc_se(x): return x.std(ddof=1)/max(np.sqrt(len(x)), 1)

# ============================ PART A ==================================
def dadstock(x, d):
    o = np.zeros_like(x, float); c = 0.0
    for t in range(len(x)): c = x[t] + d*c; o[t] = c
    return o

def weibull_adstock(x, lam=4.0, k=2.0, L=21):
    w = np.exp(-((np.arange(L)/lam)**k)); w /= w.sum()
    return np.convolve(x, w)[:len(x)]

def hill(x, g, h):
    x = np.maximum(x, 0.0); return x**h/(x**h + g**h)

def atan_sat(x, g, h=None):
    return np.arctan(np.maximum(x, 0)/g)*g

DEPTH_PCT = {"mild": 90, "med": 50, "deep": 25}
CLASS_RANGE = {0.15: (0.05, 0.35), 0.50: (0.30, 0.70), 0.85: (0.65, 0.95)}

_REAL_CACHE = "unloaded"
def real_spend_shapes():
    global _REAL_CACHE
    if not (isinstance(_REAL_CACHE, str) and _REAL_CACHE == "unloaded"):
        return _REAL_CACHE
    p = "data/raw/kaggle_fb_campaign"
    if os.path.isdir(p):
        for f in os.listdir(p):
            if f.endswith(".csv"):
                df = pd.read_csv(os.path.join(p, f))
                col = next((c for c in df.columns if "spent" in c.lower()), None)
                if col is not None:
                    v = df[col].values.astype(float)
                    _REAL_CACHE = v[v > 0]; return _REAL_CACHE
    _REAL_CACHE = None
    return None

def simA(delta, depth, shape, pattern, rng, n_weeks=156, eff="med",
         r2=0.85, sat_family="hill", ad_family="geom", multichannel=False):
    nd = n_weeks*7
    if pattern == "bursty":
        spend = rng.lognormal(0, 1.0, nd)*(rng.random(nd) > .6)*40
    elif pattern == "smooth":
        spend = rng.lognormal(0, .3, nd)*12
    elif pattern == "real":
        shapes = real_spend_shapes()
        if shapes is None:
            raise RuntimeError(
                "FATAL: pattern='real' requires data/raw/kaggle_fb_campaign "
                "(run download_datasets.py first). Refusing silent fallback.")
        spend = rng.choice(shapes, nd)*(rng.random(nd) > .3)
    ad = dadstock(spend, delta) if ad_family == "geom" else weibull_adstock(spend)
    g = np.percentile(ad[ad > 0], DEPTH_PCT[depth])
    resp = hill(ad, g, shape) if sat_family == "hill" else atan_sat(ad, g)
    wk = resp.reshape(n_weeks, 7).sum(1)
    t = np.arange(n_weeks)
    base = 800 + .5*t + 30*np.sin(2*np.pi*t/52)
    eff_mult = {"low": .5, "med": 1.0, "high": 2.0}[eff]
    wk_true = wk * eff_mult * (base.std()/(wk.std()+1e-9))
    noise_sd = np.sqrt(wk_true.var()*(1/r2 - 1) + 1e-9)
    y = base + wk_true + rng.normal(0, noise_sd, n_weeks)
    nuis = None
    if multichannel:  # two correlated channels, correctly specified as controls
        cols = []
        for _ in range(2):
            sp2 = 0.5*spend + 0.5*(rng.lognormal(0, 1.0, nd)*(rng.random(nd) > .6)*40)
            ad2 = dadstock(sp2, 0.5)
            g2 = np.percentile(ad2[ad2 > 0], 50)
            c2 = hill(ad2, g2, 1.0).reshape(n_weeks, 7).sum(1)
            c2 = c2*(base.std()/(c2.std()+1e-9))*0.7
            y = y + c2
            cols.append(c2)
        nuis = np.column_stack(cols)
    return spend, y, wk_true, nuis

def gridfitA(y, builder, decs, C):
    best = None
    for d in decs:
        for gp in GAMMA_PCTS:
            for h in H_GRID:
                m = builder(d, gp, h)
                X = np.column_stack([C, m])
                b = ols(X, y)
                sse = np.sum((y - X@b)**2)
                if best is None or sse < best[0]:
                    best = (sse, b[-1]*m, d)
    return best[1], best[2]

def one_A(delta, depth, shape, pattern, rep, cell="core", **kw):
    rng = np.random.default_rng(seed_of("A", delta, depth, shape, pattern, rep, cell))
    n_weeks = kw.get("n_weeks", 156)
    spend, y, true_c, nuis = simA(delta, depth, shape, pattern, rng, **kw)
    C = controls(n_weeks)
    if nuis is not None:
        C = np.column_stack([C, nuis])
    spend_w = spend.reshape(n_weeks, 7).sum(1)
    res = {}
    def wk_b(d, gp, h):
        aw = dadstock(spend_w, d)
        g = np.percentile(aw[aw > 0], gp) if (aw > 0).any() else 1.
        return hill(aw, g, h)
    res["weekly"] = gridfitA(y, wk_b, DEC_GRID, C)
    def dy_b(d, gp, h):
        ad = dadstock(spend, d)
        g = np.percentile(ad[ad > 0], gp) if (ad > 0).any() else 1.
        return hill(ad, g, h).reshape(n_weeks, 7).sum(1)
    res["dailyT"] = gridfitA(y, dy_b, DEC_GRID, C)
    lo, hi = CLASS_RANGE[delta]
    res["dailyT_reg"] = gridfitA(y, dy_b, np.linspace(lo, hi, 6), C)
    # oracle
    ad_t = (dadstock(spend, delta) if kw.get("ad_family", "geom") == "geom"
            else weibull_adstock(spend))
    g_t = np.percentile(ad_t[ad_t > 0], DEPTH_PCT[depth])
    sat = hill if kw.get("sat_family", "hill") == "hill" else atan_sat
    m_or = (sat(ad_t, g_t, shape) if kw.get("sat_family", "hill") == "hill"
            else sat(ad_t, g_t)).reshape(n_weeks, 7).sum(1)
    b = ols(np.column_stack([C, m_or]), y)
    res["oracle"] = (b[-1]*m_or, delta)
    rows = []
    for arm, (est, dd) in res.items():
        rows.append(dict(part="A", cell=cell, delta=delta, depth=depth,
                         shape=shape, pattern=pattern, rep=rep, arm=arm,
                         est_decay=dd,
                         bias=100*(est.sum()-true_c.sum())/true_c.sum()))
    return rows

def build_A_cells():
    pats = ["bursty", "smooth"] + (["real"] if real_spend_shapes() is not None else [])
    if "real" not in pats and not SMOKE:
        print("WARNING: FB dataset absent -> 'real' pattern cells SKIPPED "
              "(design requires them for the final paper run).")
    core = [(d, dp, sh, p, r, "core", {})
            for d in [0.15, 0.50, 0.85] for dp in ["mild", "med", "deep"]
            for sh in ([1.0] if SMOKE else [1.0, 2.2]) for p in pats
            for r in range(REPS_CORE)]
    base = dict(delta=0.50, depth="med", shape=1.0, pattern="bursty")
    sens = []
    for tag, kw in [("len104", dict(n_weeks=104)), ("len208", dict(n_weeks=208)),
                    ("eff_low", dict(eff="low")), ("eff_high", dict(eff="high")),
                    ("noise_r2_75", dict(r2=.75)), ("noise_r2_95", dict(r2=.95)),
                    ("sat_atan", dict(sat_family="atan")),
                    ("ad_weibull", dict(ad_family="weibull")),
                    ("multichannel", dict(multichannel=True))]:
        for r in range(REPS_SENS):
            sens.append((base["delta"], base["depth"], base["shape"],
                         base["pattern"], r, tag, kw))
    return core + sens

# ============================ PART B ==================================
B_TRUTHS = ["smooth_slow", "smooth_fast", "step", "crisis", "seasonal"]
B_FREQS = [4] if SMOKE else [4, 13]

def simB_truth(kind, rng, n=156):
    t = np.arange(n)
    if kind in ("smooth_slow", "smooth_fast"):
        rho = .97 if kind == "smooth_slow" else .85
        m = np.zeros(n); e = rng.normal(0, 1, n)
        for i in range(1, n): m[i] = rho*m[i-1] + .3*e[i]
    elif kind == "step":
        m = np.zeros(n); lvl = 0.
        jumps = np.sort(rng.choice(np.arange(8, n-4), 8, replace=False))
        for i in range(n):
            if i in jumps: lvl += rng.choice([-1, 1])*rng.uniform(.5, 1.5)
            m[i] = lvl
    elif kind == "crisis":
        m = np.zeros(n); e = rng.normal(0, 1, n)
        for i in range(1, n): m[i] = .97*m[i-1] + .2*e[i]
        c0 = rng.integers(50, 110)
        m[c0:c0+10] -= np.linspace(0, 3, 10); m[c0+10:] -= 3
        m[c0+18:] += np.linspace(0, 2.2, n-c0-18)
    else:  # seasonal v2: amplitude + phase drift -> not collinear with sin/cos
        amp = 1.0 + .6*np.cumsum(rng.normal(0, .03, n))
        phase = rng.uniform(0, 2*np.pi) + np.cumsum(rng.normal(0, .01, n))
        m = amp*np.sin(2*np.pi*t/52 + phase) + .3*rng.normal(0, 1, n)
    return (m - m.mean())/(m.std() + 1e-9)

def kalman_ll(obs_idx, obs_val, n, r=1e-4):
    q = np.var(np.diff(obs_val))/4 + 1e-6
    xf = np.zeros(n); Pf = np.zeros(n); x, P = obs_val[0], 1.0
    obs = dict(zip(obs_idx, obs_val))
    for t in range(n):
        if t > 0: P += q
        if t in obs:
            K = P/(P+r); x += K*(obs[t]-x); P *= (1-K)
        xf[t], Pf[t] = x, P
    xs = xf.copy()
    for t in range(n-2, -1, -1):
        xs[t] = xf[t] + (Pf[t]/(Pf[t]+q))*(xs[t+1]-xf[t])
    return xs

def agg_matrix(midx, n):
    K = len(midx); Cm = np.zeros((K, n))
    for k, m0 in enumerate(midx):
        m1 = midx[k+1] if k+1 < K else n
        Cm[k, m0:m1] = 1.0/(m1-m0)
    return Cm

def denton(midx, mm, n):
    K = len(midx)
    D = np.diff(np.eye(n), axis=0)
    A = agg_matrix(midx, n)
    KKT = np.block([[2*D.T@D, A.T], [A, np.zeros((K, K))]])
    rhs = np.concatenate([np.zeros(n), mm])
    return np.linalg.lstsq(KKT, rhs, rcond=None)[0][:n]

def chowlin_gls(midx, mm, ind, n):
    """Proper Chow-Lin: X=[1,ind]; AR(1) residual cov; rho by ML grid;
    GLS beta; BLUE disaggregation  x = Xb + V C'(CVC')^-1 (mm - CXb)."""
    X = np.column_stack([np.ones(n), ind])
    Cm = agg_matrix(midx, n)
    Xc = Cm @ X
    best = None
    for rho in np.linspace(.05, .95, 10):
        V = toeplitz(rho**np.arange(n))/(1-rho**2)
        Vc = Cm @ V @ Cm.T
        Vci = np.linalg.inv(Vc)
        b = np.linalg.solve(Xc.T@Vci@Xc, Xc.T@Vci@mm)
        r = mm - Xc@b
        sign, ld = np.linalg.slogdet(Vc)
        ll = -.5*(ld + r@Vci@r)
        if best is None or ll > best[0]:
            best = (ll, b, V, Vc, r)
    _, b, V, Vc, r = best
    return X@b + V@Cm.T@np.linalg.solve(Vc, r)

def one_B(kind, freq, rep):
    rng = np.random.default_rng(seed_of("B", kind, freq, rep))
    n = 156; t = np.arange(n)
    m = simB_truth(kind, rng, n)
    ind = .75*m + np.sqrt(1-.75**2)*rng.normal(0, 1, n)
    IND3 = np.column_stack([ind,
                            .65*m + np.sqrt(1-.65**2)*rng.normal(0, 1, n),
                            .55*m + np.sqrt(1-.55**2)*rng.normal(0, 1, n)])
    beta = 60.0
    # media channel whose spend correlates with the macro cycle (realistic:
    # budgets rise in good times) -> mistreated covariates can contaminate it
    sp_w = rng.lognormal(0, .5, n) * (1 + .35*np.clip(m, -2, 2)) * 100
    ad_w = np.zeros(n); c = 0.0
    for i in range(n): c = sp_w[i] + .6*c; ad_w[i] = c
    g_w = np.percentile(ad_w, 50)
    med_x = ad_w/(ad_w + g_w)
    med_x = (med_x - med_x.mean())/(med_x.std() + 1e-9)
    beta_med = 50.0
    y = (500 + .5*t + 35*np.sin(2*np.pi*t/52) + beta*m + beta_med*med_x
         + rng.normal(0, 40, n))
    midx = np.arange(0, n, freq); mm = m[midx]
    hf = np.zeros(n)
    for k, m0 in enumerate(midx):
        m1 = midx[k+1] if k+1 < len(midx) else n
        hf[m0:m1] = mm[k]
    arms = {"holdflat": hf,
            "linear": np.interp(np.arange(n), midx, mm),
            "spline": CubicSpline(midx, mm)(np.arange(n)),
            "kalman": kalman_ll(midx, mm, n),
            "denton": denton(midx, mm, n),
            "chowlin_gls": chowlin_gls(midx, mm, ind, n)}
    s = pd.Series(hf)
    for w in WINDOWS:
        arms[f"sma{w}"] = s.rolling(w, min_periods=1).mean().values
        arms[f"cma{w}"] = s.rolling(w, center=True, min_periods=1).mean().values
        arms[f"ema{w}"] = s.ewm(span=w, adjust=False).mean().values
    Cm = agg_matrix(midx, n)
    Xm = Cm @ IND3
    try:
        en = ElasticNetCV(cv=3).fit(Xm, mm)
        pred = en.predict(IND3)
        arms["elasticnet"] = pred + kalman_ll(midx, mm - (Cm@pred), n)
    except Exception: pass
    try:
        gb = GradientBoostingRegressor(n_estimators=80, max_depth=2,
                                       learning_rate=.08, random_state=0).fit(Xm, mm)
        pred = gb.predict(IND3)
        arms["gbm"] = pred + kalman_ll(midx, mm - (Cm@pred), n)
    except Exception: pass
    arms["oracle"] = m
    C = controls(n); tr, te = slice(0, 130), slice(130, n)
    rows = []
    for arm, mx in arms.items():
        X = np.column_stack([C, med_x, mx])
        b = ols(X[tr], y[tr])
        bias = 100*(b[-1]*mx[tr].std() - beta*m[tr].std())/(beta*m[tr].std())
        med_bias = 100*(b[4] - beta_med)/beta_med
        rows.append(dict(part="B", kind=kind, freq=freq, rep=rep, arm=arm,
                         abs_bias=abs(bias), signed_bias=bias,
                         media_abs_bias=abs(med_bias), media_signed_bias=med_bias,
                         fc_mape=100*np.mean(np.abs(y[te]-X[te]@b)/y[te]),
                         path_rmse=float(np.sqrt(np.mean((mx-m)**2)))))
    return rows

# ====================== PAIRED SIGNIFICANCE ===========================
def paired_table(df, key_cols, val, arms_col, baseline):
    """Per cell: mean, MC-SE, paired diff vs baseline with its own MC-SE."""
    wide = df.pivot_table(index=key_cols+["rep"], columns=arms_col, values=val)
    out = []
    for cell, g in wide.groupby(level=key_cols):
        for arm in g.columns:
            d = (g[arm] - g[baseline]).dropna()
            out.append(dict(**dict(zip(key_cols, cell if isinstance(cell, tuple) else (cell,))),
                            arm=arm, mean=g[arm].mean(), se=mc_se(g[arm].dropna()),
                            diff_vs_base=d.mean(), diff_se=mc_se(d) if len(d) > 1 else np.nan))
    return pd.DataFrame(out).round(3)

# ============================ FIGURES =================================
def figures(dfA, dfB):
    # F1: media bias by channel speed
    if dfA is not None:
        a = (dfA.query("cell=='core' and shape==1.0 and pattern=='bursty'")
                .assign(ab=lambda d: d.bias.abs())
                .groupby(["delta", "depth", "arm"]).agg(m=("ab", "mean"), s=("ab", mc_se))
                .reset_index())
        fig, axes = plt.subplots(1, 3, figsize=(11, 3.8), sharey=True)
        for ax, dp in zip(axes, ["mild", "med", "deep"]):
            for arm in ["weekly", "dailyT", "dailyT_reg", "oracle"]:
                s = a.query("depth==@dp and arm==@arm").sort_values("delta")
                ax.errorbar(s.delta, s.m, yerr=1.96*s.s, marker="o", capsize=3,
                            label=arm, color=PAL[arm], lw=1.8)
            ax.axhline(10, color="#bbb", ls="--", lw=1)
            ax.set_title(f"{dp} saturation"); ax.set_xlabel("daily carryover δ")
        axes[0].set_ylabel("|contribution bias| (%)"); axes[0].legend(fontsize=9)
        fig.suptitle("Fig 1. Media aggregation bias by channel speed", y=1.03)
        plt.tight_layout(); plt.savefig(f"{OUT}/fig1_media_bias.png", bbox_inches="tight")

        # F2: signed bias (direction)
        sg = (dfA.query("cell=='core' and arm=='weekly'")
                 .groupby(["shape", "delta", "depth"]).bias.mean().reset_index())
        fig, ax = plt.subplots(figsize=(7, 4))
        for i, sh in enumerate(sorted(sg["shape"].unique())):
            sub = sg[sg["shape"] == sh]
            ax.bar(np.arange(len(sub)) + i*.4,
                   sub.bias, width=.38, label=f"saturation h={sh}",
                   color=["#D55E00", "#0072B2"][i % 2])
        ax.axhline(0, color="k", lw=.8)
        ax.set_xticks(np.arange(len(sub)) + .2)
        ax.set_xticklabels([f"δ={r.delta}\n{r.depth}" for r in sub.itertuples()],
                           fontsize=8)
        ax.set_ylabel("signed contribution bias (%)")
        ax.set_title("Fig 2. Direction of weekly-practice bias (negative = media understated)")
        ax.legend(); plt.tight_layout()
        plt.savefig(f"{OUT}/fig2_signed_bias.png", bbox_inches="tight")

        # F3: decay recovery diagnostic
        dr = (dfA.query("cell=='core' and arm in ['dailyT','dailyT_reg']")
                 .groupby(["delta", "arm"]).est_decay.mean().reset_index())
        fig, ax = plt.subplots(figsize=(5.5, 4))
        for arm in ["dailyT", "dailyT_reg"]:
            s = dr[dr.arm == arm]
            ax.plot(s.delta, s.est_decay, "o-", label=arm, color=PAL[arm])
        ax.plot([0, 1], [0, 1], "--", color="#999", label="perfect recovery")
        ax.set_xlabel("true daily decay δ"); ax.set_ylabel("mean estimated δ")
        ax.set_title("Fig 3. Daily-decay identification diagnostic")
        ax.legend(); plt.tight_layout()
        plt.savefig(f"{OUT}/fig3_decay_recovery.png", bbox_inches="tight")

    if dfB is not None:
        # F4: disaggregation ladder (monthly)
        core_arms = ["sma12", "holdflat", "denton", "chowlin_gls", "spline",
                     "linear", "kalman", "elasticnet", "gbm", "oracle"]
        b = (dfB.query("freq==4 and arm in @core_arms")
                .groupby(["kind", "arm"]).agg(m=("abs_bias", "mean"),
                                              s=("abs_bias", mc_se)).reset_index())
        kinds = [k for k in B_TRUTHS if k in b.kind.unique()]
        fig, axes = plt.subplots(1, len(kinds), figsize=(3.0*len(kinds), 4), sharey=True)
        for ax, kind in zip(np.atleast_1d(axes), kinds):
            sub = b.query("kind==@kind").sort_values("m")
            cols = ["#D55E00" if "sma" in a or "ema" in a or "cma" in a else
                    "#009E73" if a in ("linear", "kalman", "denton") else
                    "#0072B2" if a in ("chowlin_gls", "elasticnet", "gbm") else
                    "#7F7F7F" for a in sub.arm]
            ax.barh(sub.arm, sub.m, xerr=1.96*sub.s, color=cols, capsize=2)
            ax.axvline(10, color="#bbb", ls="--", lw=1)
            ax.set_title(kind); ax.set_xlabel("|coef bias| (%)")
        fig.suptitle("Fig 4. Covariate disaggregation ladder (monthly observation)", y=1.03)
        plt.tight_layout(); plt.savefig(f"{OUT}/fig4_ladder.png", bbox_inches="tight")

        # F5: rolling dose-response
        rows = []
        for w in WINDOWS:
            for fam in ["sma", "cma", "ema"]:
                sub = dfB.query("freq==4 and arm==@fam+@str(w)") if False else \
                      dfB[(dfB.freq == 4) & (dfB.arm == f"{fam}{w}")]
                if len(sub):
                    rows.append(dict(window=w, family=fam,
                                     m=sub.abs_bias.mean(), s=mc_se(sub.abs_bias)))
        dd = pd.DataFrame(rows)
        fig, ax = plt.subplots(figsize=(6, 4))
        for fam, lab in [("sma", "trailing SMA"), ("cma", "centered SMA"),
                         ("ema", "EMA")]:
            s = dd[dd.family == fam]
            ax.errorbar(s.window, s.m, yerr=1.96*s.s, marker="o", capsize=3,
                        label=lab, color=PAL[fam], lw=1.8)
        hl = dfB[(dfB.freq == 4) & (dfB.arm == "linear")].abs_bias.mean()
        ax.axhline(hl, color="#009E73", ls=":", lw=1.6, label="linear interpolation")
        ax.set_xlabel("smoothing window (weeks)"); ax.set_ylabel("|coef bias| (%)")
        ax.set_title("Fig 5. The cost of smoothing: bias vs window (all truth types pooled)")
        ax.legend(); plt.tight_layout()
        plt.savefig(f"{OUT}/fig5_rolling_dose.png", bbox_inches="tight")

    # F6: mechanism illustration (constructed, not from results)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    x = np.linspace(0, 100, 200); g, h = 30, 1.0
    axes[0].plot(x, hill(x, g, h), color="#0072B2", lw=2)
    for v, c, lab in [(70, "#D55E00", "one heavy day (70)"),
                      (10, "#009E73", "spread day (10 × 7)")]:
        axes[0].axvline(v, color=c, ls="--", lw=1.2)
    axes[0].set_title("Daily response curve")
    axes[0].set_xlabel("daily adstocked spend"); axes[0].set_ylabel("response")
    labels = ["burst week:\n70 in one day", "spread week:\n10 × 7 days",
              "weekly model\nsees both as 70"]
    vals = [hill(70, g, h), 7*hill(10, g, h), np.nan]
    axes[1].bar(labels[:2], vals[:2], color=["#D55E00", "#009E73"])
    axes[1].set_title("Same weekly total, different true response")
    axes[1].set_ylabel("total weekly response")
    fig.suptitle("Fig 6. Why weekly aggregation biases saturated responses", y=1.05)
    plt.tight_layout(); plt.savefig(f"{OUT}/fig6_mechanism.png", bbox_inches="tight")

# ============================ RUN =====================================
if __name__ == "__main__":
    print(f"engine v1.2 | SMOKE={SMOKE} | parts={RUN_PARTS} | reps={REPS_CORE}")
    dfA = dfB = None
    if "A" in RUN_PARTS:
        cells = build_A_cells()
        print(f"Part A: {len(cells)} runs ...")
        res = Parallel(n_jobs=-1, verbose=1)(
            delayed(one_A)(d, dp, sh, p, r, cell, **kw)
            for d, dp, sh, p, r, cell, kw in cells)
        dfA = pd.DataFrame([x for rows in res for x in rows])
        dfA.to_csv(f"{OUT}/partA_results.csv", index=False)
        tA = paired_table(dfA.query("cell=='core'").assign(ab=lambda d: d.bias.abs()),
                          ["delta", "depth", "shape", "pattern"], "ab", "arm", "weekly")
        tA.to_csv(f"{OUT}/tableA_paired.csv", index=False)
    if "B" in RUN_PARTS:
        cells = list(itertools.product(B_TRUTHS, B_FREQS, range(REPS_CORE)))
        print(f"Part B: {len(cells)} runs ...")
        res = Parallel(n_jobs=-1, verbose=1)(delayed(one_B)(*c) for c in cells)
        dfB = pd.DataFrame([x for rows in res for x in rows])
        dfB.to_csv(f"{OUT}/partB_results.csv", index=False)
        tB = paired_table(dfB, ["kind", "freq"], "abs_bias", "arm", "linear")
        tB.to_csv(f"{OUT}/tableB_paired.csv", index=False)
    figures(dfA, dfB)
    print("Done -> ./results/ (CSVs + 6 figures)")
    if dfA is not None:
        print(dfA.query("cell=='core'").assign(a=lambda d: d.bias.abs())
                 .groupby(["depth", "arm"]).a.mean().round(1).to_string())
    if dfB is not None:
        print(dfB.query("freq==4").groupby("arm").abs_bias.mean().round(1)
                 .sort_values().head(8).to_string())