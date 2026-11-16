"""
real_data_application.py -- PHASE 4: REAL-DATA APPLICATION
"Temporal Aggregation and Disaggregation in Nonlinear MMM"

Two modules, both on REAL data (no simulation):

MODULE 1 -- COVARIATE TREATMENTS ON REAL UK SERIES
  Takes the real BoE Bank Rate (step), ONS CPI (smooth-with-shocks),
  ONS Retail Sales (seasonal), ONS GDP (quarterly-sparse), OECD consumer
  confidence (smooth), applies every treatment from the paper (hold-flat,
  rolling 4/12, EMA, linear, spline, Kalman, Chow-Lin-GLS with a real
  Google-Trends weekly indicator) and reports:
    - how far the treated weekly paths diverge from each other (RMSE/corr)
    - the LAG each smoother introduces, measured on real data
  Output: p4_covariate_divergence.csv + fig_p4_covariate_paths.png

MODULE 2 -- REAL MMM: SPECIFICATION SPREAD + HOLDOUT
  Fits a standard weekly MMM on the real Kaggle media-spends dataset
  across a grid of defensible specifications (adstock decays x saturation
  settings), and reports:
    - the spread of each channel's contribution share across specs
      ("the choice moves the answer by X points" -- on real data)
    - holdout forecast accuracy (last 20% of weeks) per spec
  Output: p4_spec_spread.csv, p4_holdout.csv + fig_p4_spec_spread.png

Run from the project folder (same place as paper_engine.py):
    python real_data_application.py
Requires files in data/raw/ with the agreed names. Missing files are
reported and their module skipped -- nothing fails silently.
"""

import os, re, itertools
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAW = "data/raw"
OUT = "results_phase4"; os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.size": 11,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": .25, "figure.dpi": 300,
                     "legend.frameon": False})

# ======================================================================
# PARSERS for the real files (tested on the actual downloads)
# ======================================================================
def parse_ons(path):
    """ONS series CSVs stack annual/quarterly/monthly sections. Returns
    (monthly_df, quarterly_df) with columns [date, value]; either may be empty."""
    rows = pd.read_csv(path, header=None, names=["k", "v"], skip_blank_lines=True)
    mon, qtr = [], []
    for k, v in zip(rows.k.astype(str), rows.v):
        k = k.strip('" ')
        if re.fullmatch(r"\d{4} [A-Z]{3}", k):
            mon.append((pd.to_datetime(k, format="%Y %b"), float(v)))
        elif re.fullmatch(r"\d{4} Q[1-4]", k):
            y, q = k.split(" Q")
            qtr.append((pd.Timestamp(int(y), 3*int(q)-2, 1), float(v)))
    m = pd.DataFrame(mon, columns=["date", "value"])
    q = pd.DataFrame(qtr, columns=["date", "value"])
    return m.sort_values("date").reset_index(drop=True), \
           q.sort_values("date").reset_index(drop=True)

def parse_boe(path):
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    dcol = next(c for c in df.columns if "date" in c.lower())
    rcol = next(c for c in df.columns if "rate" in c.lower())
    df["date"] = pd.to_datetime(df[dcol], format="%d %b %y", errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    daily = (df.set_index("date")[rcol].astype(float)
               .reindex(pd.date_range(df.date.min(), pd.Timestamp.today(), freq="D"))
               .ffill())
    weekly = daily.resample("W-MON").last().dropna()
    return weekly.reset_index().rename(columns={"index": "date", rcol: "value"}) \
                 .rename(columns={weekly.name if weekly.name else 0: "value"})

def parse_trends(path):
    df = pd.read_csv(path, skiprows=1)
    wcol = df.columns[0]
    vcol = df.columns[1]
    df["date"] = pd.to_datetime(df[wcol])
    df["value"] = pd.to_numeric(df[vcol].astype(str).str.replace("<1", "0"),
                                errors="coerce")
    return df[["date", "value"]].dropna().reset_index(drop=True)

def load_media_spends():
    folder = os.path.join(RAW, "kaggle_media_spends")
    f = next((x for x in os.listdir(folder) if x.endswith(".csv")), None)
    df = pd.read_csv(os.path.join(folder, f))
    df.columns = [c.strip() for c in df.columns]
    sales = next(c for c in df.columns if "sale" in c.lower())
    num = df.select_dtypes("number").columns.tolist()
    media = [c for c in num if c != sales and
             not any(k in c.lower() for k in ("overall", "total", "all_"))]
    # if a division/group column exists, aggregate to one national weekly series
    grp = next((c for c in df.columns if c.lower() in
                ("division", "region", "market", "geo")), None)
    wk = next((c for c in df.columns if "week" in c.lower() or "date" in c.lower()),
              None)
    if grp is not None and wk is not None:
        df = df.groupby(wk, sort=True)[num].sum().reset_index()
    y = df[sales].astype(float).values
    X = df[media].astype(float)
    X = X.loc[:, X.std() > 0]
    return X, y, media

# ======================================================================
# treatments (same machinery as the engine)
# ======================================================================
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

def chowlin_gls(obs_idx, obs_val, ind, n):
    from scipy.linalg import toeplitz
    X = np.column_stack([np.ones(n), ind])
    K = len(obs_idx); Cm = np.zeros((K, n))
    for k, m0 in enumerate(obs_idx):
        m1 = obs_idx[k+1] if k+1 < K else n
        Cm[k, m0:m1] = 1.0/(m1-m0)
    Xc = Cm @ X
    best = None
    for rho in np.linspace(.05, .95, 10):
        V = toeplitz(rho**np.arange(n))/(1-rho**2)
        Vc = Cm @ V @ Cm.T
        Vci = np.linalg.inv(Vc)
        b = np.linalg.solve(Xc.T@Vci@Xc, Xc.T@Vci@obs_val)
        r_ = obs_val - Xc@b
        sign, ld = np.linalg.slogdet(Vc)
        ll = -.5*(ld + r_@Vci@r_)
        if best is None or ll > best[0]:
            best = (ll, b, V, Vc, r_)
    _, b, V, Vc, r_ = best
    return X@b + V@Cm.T@np.linalg.solve(Vc, r_)

def treatments_on(series_dates, series_vals, weekly_index, indicator=None):
    """Place low-freq observations on the weekly grid; build all treated paths."""
    n = len(weekly_index)
    obs_idx = [int(np.argmin(np.abs(weekly_index - d))) for d in series_dates]
    keep = pd.Series(obs_idx).drop_duplicates(keep="first").index
    obs_idx = [obs_idx[i] for i in keep]
    obs_val = np.asarray([series_vals[i] for i in keep], float)
    hf = np.zeros(n)
    for k, m0 in enumerate(obs_idx):
        m1 = obs_idx[k+1] if k+1 < len(obs_idx) else n
        hf[m0:m1] = obs_val[k]
    hf[:obs_idx[0]] = obs_val[0]
    s = pd.Series(hf)
    out = {"holdflat": hf,
           "linear": np.interp(np.arange(n), obs_idx, obs_val),
           "kalman": kalman_ll(obs_idx, obs_val, n)}
    for w in [4, 8, 12, 24, 36]:
        out[f"sma{w}"] = s.rolling(w, min_periods=1).mean().values
        out[f"cma{w}"] = s.rolling(w, center=True, min_periods=1).mean().values
        out[f"ema{w}"] = s.ewm(span=w, adjust=False).mean().values
    from scipy.interpolate import CubicSpline
    out["spline"] = CubicSpline(obs_idx, obs_val)(np.arange(n))
    if indicator is not None:
        try:
            out["chowlin_gls"] = chowlin_gls(obs_idx, obs_val, indicator, n)
        except Exception as e:
            print(f"   [chowlin skipped: {e}]")
    return out, obs_idx, obs_val

def lag_of(x, ref, maxlag=30):
    """Lag (weeks) at which x best matches ref -- measures smoother delay."""
    best, bl = -2, 0
    xr = (ref - np.mean(ref))/ (np.std(ref)+1e-9)
    for L in range(0, maxlag+1):
        xl = np.roll(x, -L)[:len(x)-maxlag]
        c = np.corrcoef(xl, xr[:len(xl)])[0, 1]
        if c > best: best, bl = c, L
    return bl

# ======================================================================
# MODULE 1
# ======================================================================
def module1():
    print("\n===== MODULE 1: covariate treatments on real UK series =====")
    files = {"CPI (monthly)":       ("ons_uk_cpi_monthly.csv", "ons_m"),
             "RetailSales (monthly)": ("ons_uk_retail_sales_monthly.csv", "ons_m"),
             "GDP (quarterly)":     ("ons_uk_gdp_quarterly.csv", "ons_q"),
             "BankRate (step)":     ("boe_bank_rate.csv", "boe"),
             "Confidence (monthly)": ("oecd_uk_consumer_confidence.csv", "oecd")}
    # weekly grid
    weekly_index = pd.date_range("2015-01-05", pd.Timestamp.today(), freq="W-MON")
    n = len(weekly_index)
    # indicator: average of available Trends series (weekly, from 2021)
    ind = None
    tr_paths = [f for f in os.listdir(RAW) if f.startswith("gtrends_")]
    if tr_paths:
        cols = []
        for f in tr_paths:
            t = parse_trends(os.path.join(RAW, f)).set_index("date")["value"]
            t = t.reindex(weekly_index, method="nearest", tolerance=pd.Timedelta("4D"))
            cols.append((t - t.mean())/(t.std()+1e-9))
        ind_full = pd.concat(cols, axis=1).mean(1)
        ind = ind_full.fillna(0).values   # zeros pre-2021: chowlin leans on obs there
        print(f"  Trends indicator built from {len(tr_paths)} series")
    rows, paths_for_fig = [], None
    for label, (fname, kind) in files.items():
        p = os.path.join(RAW, fname)
        if not os.path.exists(p):
            print(f"  [missing] {fname} -> skipped"); continue
        if kind == "ons_m":
            m, q = parse_ons(p); ser = m
        elif kind == "ons_q":
            m, q = parse_ons(p); ser = q
        elif kind == "boe":
            b = parse_boe(p); b.columns = ["date", "value"]; ser = b
        else:  # oecd csv-with-labels
            df = pd.read_csv(p)
            dcol = next((c for c in df.columns
                         if "time" in c.lower() or "period" in c.lower()), df.columns[0])
            vcol = next(c for c in df.columns if "value" in c.lower() or "obs" in c.lower())
            ser = pd.DataFrame({"date": pd.to_datetime(df[dcol], errors="coerce"),
                                "value": pd.to_numeric(df[vcol], errors="coerce")}
                               ).dropna().sort_values("date")
        ser = ser[(ser.date >= weekly_index[0]) & (ser.date <= weekly_index[-1])]
        if len(ser) < 6:
            print(f"  [too short] {label}"); continue
        arms, obs_idx, obs_val = treatments_on(ser.date.values, ser.value.values,
                                               weekly_index.values, indicator=ind)
        ref = arms["linear"]
        for arm, x in arms.items():
            rows.append(dict(series=label, treatment=arm,
                             rmse_vs_linear=float(np.sqrt(np.mean((x-ref)**2))),
                             corr_vs_linear=float(np.corrcoef(x, ref)[0, 1]),
                             lag_weeks=lag_of(x, ref)))
        print(f"  {label}: {len(obs_idx)} observations -> "
              f"sma12 lag = {lag_of(arms['sma12'], ref)}w, "
              f"rmse(sma12 vs linear) = {np.sqrt(np.mean((arms['sma12']-ref)**2)):.3f}")
        if label.startswith("CPI"):
            paths_for_fig = (weekly_index, arms, obs_idx, obs_val)
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/p4_covariate_divergence.csv", index=False)
    if paths_for_fig:
        wi, arms, oi, ov = paths_for_fig
        sl = slice(max(0, oi[0]), len(wi))
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(wi[sl], arms["linear"][sl], label="linear interpolation",
                color="#009E73", lw=1.8)
        ax.plot(wi[sl], arms["sma12"][sl], label="hold-flat + 12w rolling (practice)",
                color="#D55E00", lw=1.8)
        ax.plot(wi[sl], arms["kalman"][sl], label="Kalman", color="#0072B2",
                lw=1.2, ls="--")
        ax.scatter(wi[oi], ov, color="k", s=14, zorder=5, label="monthly observations")
        ax.set_title("Real UK CPI: what each treatment feeds the model")
        ax.set_ylabel("CPI annual rate (%)"); ax.legend(fontsize=9)
        plt.tight_layout(); plt.savefig(f"{OUT}/fig_p4_covariate_paths.png",
                                        bbox_inches="tight")
    print(f"  -> {OUT}/p4_covariate_divergence.csv")

# ======================================================================
# MODULE 2
# ======================================================================
def dadstock(x, d):
    o = np.zeros_like(x, float); c = 0.0
    for t in range(len(x)): c = x[t] + d*c; o[t] = c
    return o

def module2():
    print("\n===== MODULE 2: real MMM spec spread + holdout =====")
    try:
        X, y, names = load_media_spends()
    except Exception as e:
        print(f"  [cannot load media dataset: {e}] -> skipped"); return
    n = len(y); t = np.arange(n)
    C = np.column_stack([np.ones(n), t, np.sin(2*np.pi*t/52), np.cos(2*np.pi*t/52)])
    origins = [int(n*f) for f in (.6, .7, .8, .9)]   # rolling-origin CV
    specs = list(itertools.product([.1, .3, .5, .7, .9],      # adstock decay
                                   [30, 70],                  # gamma percentile
                                   ["hill", "atan"]))         # saturation family
    rows, hold = [], []
    for d, gp, fam in specs:
        M = []
        for c in X.columns:
            a = dadstock(X[c].values, d)
            g = np.percentile(a[a > 0], gp) if (a > 0).any() else 1.0
            m = a/(a+g) if fam == "hill" else np.arctan(a/g)*g
            M.append((m - m.mean())/(m.std()+1e-9))
        M = np.column_stack(M)
        Z = np.column_stack([C, M])
        mapes = []
        for o in origins:                          # rolling-origin validation
            b, *_ = np.linalg.lstsq(Z[:o], y[:o], rcond=None)
            h2 = min(o + max(8, n//10), n)
            mapes.append(100*np.mean(np.abs(y[o:h2] - Z[o:h2]@b)
                                     / np.maximum(y[o:h2], 1e-9)))
        b, *_ = np.linalg.lstsq(Z[:origins[-1]], y[:origins[-1]], rcond=None)
        contrib = np.abs(b[4:]) * M[:origins[-1]].std(0)
        share = 100*contrib/contrib.sum()
        yy = y[:origins[-1]]
        med_fit = M[:origins[-1]] @ b[4:]
        media_kpi_share = 100*np.std(med_fit)/max(np.std(yy), 1e-9)
        hold.append(dict(decay=d, gamma_pct=gp, family=fam,
                         holdout_mape=float(np.mean(mapes)),
                         media_kpi_share_pct=round(media_kpi_share, 1)))
        for c, s in zip(X.columns, share):
            rows.append(dict(decay=d, gamma_pct=gp, family=fam, channel=c, share=s))
    dfr = pd.DataFrame(rows); dfh = pd.DataFrame(hold)
    dfr.to_csv(f"{OUT}/p4_spec_spread.csv", index=False)
    dfh.to_csv(f"{OUT}/p4_holdout.csv", index=False)
    spread = (dfr.groupby("channel").share.agg(["min", "max", "mean"])
                 .assign(range=lambda d: d["max"]-d["min"])
                 .sort_values("range", ascending=False).round(1))
    print("  contribution share (%) across 20 defensible specs:")
    print(spread.to_string())
    print(f"  rolling-origin MAPE (4 origins): best {dfh.holdout_mape.min():.1f}%, "
          f"worst {dfh.holdout_mape.max():.1f}%")
    print(f"  media share of KPI (sanity): "
          f"{dfh.media_kpi_share_pct.min():.0f}%-{dfh.media_kpi_share_pct.max():.0f}%")
    fig, ax = plt.subplots(figsize=(8, 4))
    sp = spread.reset_index()
    ax.barh(sp.channel, sp["range"], color="#0072B2")
    ax.set_xlabel("contribution-share range across specs (percentage points)")
    ax.set_title("Real data: how much the specification choice moves each channel")
    plt.tight_layout(); plt.savefig(f"{OUT}/fig_p4_spec_spread.png",
                                    bbox_inches="tight")
    print(f"  -> {OUT}/p4_spec_spread.csv, p4_holdout.csv")



# ======================================================================
# MODULE 3 -- second real dataset: Dunnhumby Breakfast at the Frat
# ======================================================================
def module3():
    print("\n===== MODULE 3: Dunnhumby BatF (second real dataset) =====")
    folder = os.path.join(RAW, "dunnhumby_batf")
    if not os.path.isdir(folder):
        print("  [missing] data/raw/dunnhumby_batf/ -> register free at "
              "dunnhumby.com/source-files, download 'Breakfast at the Frat', "
              "unzip there. Skipped."); return
    f = next((x for x in os.listdir(folder)
              if x.lower().endswith((".csv", ".xlsx")) and "transact" in x.lower()),
             None) or next((x for x in os.listdir(folder)
              if x.lower().endswith((".csv", ".xlsx"))), None)
    p = os.path.join(folder, f)
    if p.lower().endswith(".xlsx"):
        xls = pd.ExcelFile(p)
        df = None
        for sh in xls.sheet_names:
            probe = pd.read_excel(p, sheet_name=sh, header=None, nrows=5)
            for hr in range(min(5, len(probe))):
                rowvals = [str(v).upper().strip() for v in probe.iloc[hr].values]
                if "WEEK_END_DATE" in rowvals and "UNITS" in rowvals:
                    df = pd.read_excel(p, sheet_name=sh, header=hr)
                    break
            if df is not None: break
        if df is None:
            print("  [no sheet with WEEK_END_DATE/UNITS header found] Skipped.")
            return
    else:
        df = pd.read_csv(p)
    df.columns = [str(c).upper().strip() for c in df.columns]
    need = {"WEEK_END_DATE", "UNITS", "PRICE", "BASE_PRICE"}
    if not need.issubset(df.columns):
        print(f"  [unexpected columns in {f}: {list(df.columns)[:8]}...] Skipped.")
        return
    df["DISC"] = ((df.BASE_PRICE - df.PRICE)/df.BASE_PRICE).clip(0, 1).fillna(0)
    g = df.groupby("WEEK_END_DATE").agg(
        UNITS=("UNITS", "sum"), DISC=("DISC", "mean"),
        FEATURE=("FEATURE", "mean") if "FEATURE" in df.columns else ("DISC", "mean"),
        DISPLAY=("DISPLAY", "mean") if "DISPLAY" in df.columns else ("DISC", "mean"),
    ).reset_index()
    y = g.UNITS.astype(float).values
    X = g[["DISC", "FEATURE", "DISPLAY"]].astype(float)
    n = len(y); t = np.arange(n)
    C = np.column_stack([np.ones(n), t, np.sin(2*np.pi*t/52), np.cos(2*np.pi*t/52)])
    origins = [int(n*f_) for f_ in (.6, .7, .8, .9)]
    rows, hold = [], []
    for d, gp, fam in itertools.product([.1, .3, .5, .7, .9], [30, 70],
                                        ["hill", "atan"]):
        M = []
        for c in X.columns:
            a = dadstock(X[c].values, d)
            gme = np.percentile(a[a > 0], gp) if (a > 0).any() else 1.0
            m = a/(a+gme) if fam == "hill" else np.arctan(a/gme)*gme
            M.append((m - m.mean())/(m.std()+1e-9))
        M = np.column_stack(M); Z = np.column_stack([C, M])
        mapes = []
        for o in origins:
            b, *_ = np.linalg.lstsq(Z[:o], y[:o], rcond=None)
            h2 = min(o + max(8, n//10), n)
            mapes.append(100*np.mean(np.abs(y[o:h2]-Z[o:h2]@b)/np.maximum(y[o:h2], 1)))
        b, *_ = np.linalg.lstsq(Z[:origins[-1]], y[:origins[-1]], rcond=None)
        contrib = np.abs(b[4:])*M[:origins[-1]].std(0)
        share = 100*contrib/contrib.sum()
        hold.append(dict(decay=d, gamma_pct=gp, family=fam,
                         holdout_mape=float(np.mean(mapes))))
        for c, s in zip(X.columns, share):
            rows.append(dict(decay=d, gamma_pct=gp, family=fam, channel=c, share=s))
    dfr = pd.DataFrame(rows)
    dfr.to_csv(f"{OUT}/p4_batf_spec_spread.csv", index=False)
    pd.DataFrame(hold).to_csv(f"{OUT}/p4_batf_holdout.csv", index=False)
    sp = (dfr.groupby("channel").share.agg(["min", "max"])
             .assign(range=lambda d_: d_["max"]-d_["min"]).round(1))
    print(sp.to_string())
    print(f"  -> {OUT}/p4_batf_spec_spread.csv")

# ======================================================================
# MODULE 4 -- Robyn simulated benchmark (comparability)
# ======================================================================
ROBYN_URL = ("https://raw.githubusercontent.com/facebookexperimental/Robyn/"
             "main/R/data/dt_simulated_weekly.RData")

def module4():
    print("\n===== MODULE 4: Robyn benchmark dataset =====")
    tgt = os.path.join(RAW, "robyn_dt_simulated_weekly.csv")
    if not os.path.exists(tgt):
        try:
            import requests, pyreadr, tempfile
            r = requests.get(ROBYN_URL, timeout=60); r.raise_for_status()
            with tempfile.NamedTemporaryFile(suffix=".RData", delete=False) as fh:
                fh.write(r.content); tmp = fh.name
            res = pyreadr.read_r(tmp)
            list(res.values())[0].to_csv(tgt, index=False)
            print("  fetched Robyn benchmark -> data/raw/")
        except Exception as e:
            print(f"  [could not fetch Robyn benchmark: {e}] "
                  "-> pip install pyreadr requests, or skip. Skipped."); return
    df = pd.read_csv(tgt)
    kpi = next((c for c in df.columns if "revenue" in c.lower()), None)
    media = [c for c in df.columns if c.endswith("_S") and
             pd.api.types.is_numeric_dtype(df[c])]
    if kpi is None or not media:
        print("  [unexpected Robyn schema] Skipped."); return
    y = df[kpi].astype(float).values; X = df[media].astype(float)
    n = len(y); t = np.arange(n)
    C = np.column_stack([np.ones(n), t, np.sin(2*np.pi*t/52), np.cos(2*np.pi*t/52)])
    origins = [int(n*f_) for f_ in (.6, .7, .8, .9)]
    rows = []
    for d, gp, fam in itertools.product([.1, .3, .5, .7, .9], [30, 70],
                                        ["hill", "atan"]):
        M = []
        for c in X.columns:
            a = dadstock(X[c].values, d)
            gme = np.percentile(a[a > 0], gp) if (a > 0).any() else 1.0
            m = a/(a+gme) if fam == "hill" else np.arctan(a/gme)*gme
            M.append((m - m.mean())/(m.std()+1e-9))
        M = np.column_stack(M); Z = np.column_stack([C, M])
        b, *_ = np.linalg.lstsq(Z[:origins[-1]], y[:origins[-1]], rcond=None)
        contrib = np.abs(b[4:])*M[:origins[-1]].std(0)
        share = 100*contrib/contrib.sum()
        for c, s in zip(X.columns, share):
            rows.append(dict(decay=d, gamma_pct=gp, family=fam, channel=c, share=s))
    dfr = pd.DataFrame(rows)
    dfr.to_csv(f"{OUT}/p4_robyn_spec_spread.csv", index=False)
    sp = (dfr.groupby("channel").share.agg(["min", "max"])
             .assign(range=lambda d_: d_["max"]-d_["min"]).round(1))
    print(sp.to_string())
    print(f"  -> {OUT}/p4_robyn_spec_spread.csv")

if __name__ == "__main__":
    module1()
    module2()
    module3()
    module4()
    print("\nPhase 4 outputs in ./results_phase4/")