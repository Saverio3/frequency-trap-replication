"""frequency_check: does the data say the media response acts at DAILY or WEEKLY resolution?
Inputs: y = weekly KPI (n_weeks,), spend_daily = daily spend (n_weeks*7,), controls = (n_weeks, k) matrix
(default: intercept, linear trend, annual sine and cosine).
Method (Vuong non-nested likelihood-ratio test):
  1. Fit the weekly-transform model and the daily-transform model on the same grid
     (12 decays x 7 gamma percentiles x 3 Hill shapes = 252 candidates each; best by SSE).
  2. Vuong z = mean(LR_t)/(sd(LR_t)/sqrt(n)), LR_t = weekly log-lik difference (daily minus weekly).
  3. Positive z -> daily transform describes the data better. Negative z -> weekly.
  4. R2fit = share of the KPI variance left after controls that the better model explains. It tells you how far to trust z.
Only numpy and scipy are needed."""
import numpy as np
from scipy.signal import lfilter

DECS = np.linspace(.05, .95, 12); PCTS = [5, 15, 30, 50, 70, 85, 95]; HS = [1.0, 1.6, 2.2]

def _controls(n):
    t = np.arange(n)
    return np.column_stack([np.ones(n), t, np.sin(2*np.pi*t/52), np.cos(2*np.pi*t/52)])

def _cands(spend_d, n, arm):
    sw = spend_d.reshape(n, 7).sum(1); cols = []
    for d in DECS:
        a = lfilter([1.0], [1.0, -d], sw if arm == "weekly" else spend_d)
        nz = a[a > 0]; gs = np.percentile(nz, PCTS) if nz.size else np.ones(len(PCTS))
        for g in gs:
            for h in HS:
                x = np.maximum(a, 0.0); m = x**h/(x**h + g**h)
                cols.append(m if arm == "weekly" else m.reshape(n, 7).sum(1))
    return np.array(cols)

def _best(yr, Q, cols):
    Mr = cols - (cols@Q)@Q.T; num = Mr@yr; den = (Mr*Mr).sum(1)
    den = np.where(den < 1e-12, np.inf, den); sse = yr@yr - num**2/den; k = int(np.argmin(sse))
    return dict(sse=float(sse[k]), resid=yr - num[k]/den[k]*Mr[k])

def frequency_check(y, spend_daily, controls=None):
    y = np.asarray(y, float); s = np.asarray(spend_daily, float); n = len(y)
    assert len(s) == 7*n, "spend_daily must have 7 values per KPI week"
    C = _controls(n) if controls is None else np.asarray(controls, float)
    Q, _ = np.linalg.qr(C); yr = y - (y@Q)@Q.T
    fw = _best(yr, Q, _cands(s, n, "weekly")); fd = _best(yr, Q, _cands(s, n, "daily"))
    sw, sd = fw["sse"]/n, fd["sse"]/n
    llw = -0.5*np.log(sw + 1e-300) - 0.5*fw["resid"]**2/(sw + 1e-300)
    lld = -0.5*np.log(sd + 1e-300) - 0.5*fd["resid"]**2/(sd + 1e-300)
    lr = lld - llw; z = float(lr.mean()/(lr.std(ddof=1)/np.sqrt(n))) if lr.std(ddof=1) > 1e-12 else 0.0
    r2 = float(1 - min(fw["sse"], fd["sse"])/(yr@yr))
    verdict = "DAILY" if z > 0 else "WEEKLY"
    trust = ("HIGH (about 97-99% in our simulations)" if r2 >= 0.5 else
             "MEDIUM (about 95-97%, fewer simulated cases)" if r2 >= 0.3 else
             "LOW: signal too weak, treat as undetermined and report both")
    trust += ". Caution: with time-varying effects or near-linear response the check can mislead (76-90% in our simulations)."
    return dict(verdict=verdict, vuong_z=round(z, 2), fit_gap_logratio=round(float(np.log(fw["sse"]/fd["sse"])), 3),
                R2fit=round(r2, 3), trust=trust)
