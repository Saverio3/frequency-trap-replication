"""Export simulated single-channel markets (daily and weekly versions of the SAME data) for a run of the real Robyn package.
Daily KPI = baseline/7 + scaled daily response + daily noise, so the weekly sum equals the weekly KPI exactly.
Writes robyn_markets/market_XX_daily.csv, _weekly.csv and truth.csv (true weekly media contribution total)."""
import os, numpy as np, pandas as pd
from lib import *
NW = 156; ND = NW*7; os.makedirs("robyn_markets", exist_ok=True)
rows = []; i = 0
for delta in (0.15, 0.5, 0.85):
    for shape in (1.0, 2.2):
        for pattern in ("bursty", "smooth", "real"):
            for rep in range(2):
                rng = np.random.default_rng(seed_of("RBX", delta, shape, pattern, rep))
                spend = gen_spend(pattern, rng, ND); ad = adstock(spend, delta); g = np.percentile(ad[ad > 0], 50)
                r_day = hill(ad, g, shape); wk_raw = r_day.reshape(NW, 7).sum(1)
                t = np.arange(NW); base = 800 + .5*t + 30*np.sin(2*np.pi*t/52); c = base.std()/(wk_raw.std() + 1e-9)
                noise_sd = np.sqrt((c*wk_raw).var()*(1/0.85 - 1))
                yd = np.repeat(base/7, 7) + c*r_day + rng.normal(0, noise_sd/np.sqrt(7), ND)
                dates = pd.date_range("2022-01-03", periods=ND)            # Monday start
                dd = pd.DataFrame({"DATE": dates.strftime("%Y-%m-%d"), "revenue": yd, "spend_ch": spend})
                wk = pd.DataFrame({"DATE": dates[::7].strftime("%Y-%m-%d"), "revenue": yd.reshape(NW, 7).sum(1), "spend_ch": spend.reshape(NW, 7).sum(1)})
                dd.to_csv(f"robyn_markets/market_{i:02d}_daily.csv", index=False); wk.to_csv(f"robyn_markets/market_{i:02d}_weekly.csv", index=False)
                rows.append(dict(market=i, delta=delta, shape=shape, pattern=pattern, rep=rep, true_total=float((c*wk_raw).sum())))
                i += 1
pd.DataFrame(rows).to_csv("robyn_markets/truth.csv", index=False); print("markets", i)
