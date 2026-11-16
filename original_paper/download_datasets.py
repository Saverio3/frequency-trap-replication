"""
download_datasets.py -- Phase 0/1 data acquisition for the temporal aggregation paper.
Run once; downloads land in ./data/raw/. Re-runnable (skips existing files).

REQUIREMENTS:
  pip install kaggle kagglehub pyreadr pandas requests pytrends
  Kaggle: create API token at kaggle.com/settings -> place kaggle.json in ~/.kaggle/

NOTE ON LICENSES (for the paper's data-availability statement):
  - Kaggle datasets: check each dataset's license tab; most allow research use but
    NOT redistribution -> ship this script in your repo, not the raw files.
  - Dunnhumby Source Files: free but requires manual registration/click-through at
    https://www.dunnhumby.com/source-files/ -> cannot be scripted; instructions below.
  - BoE / ONS / OECD / Robyn: open data; safe to mirror processed derivatives.
"""

import os
import io
import requests
import pandas as pd

RAW = "data/raw"
os.makedirs(RAW, exist_ok=True)

def done(p): return os.path.exists(p) and os.path.getsize(p) > 0

# ----------------------------------------------------------------------
# 1. Kaggle: Sample Media Spends Data (weekly, 8 channels + sales, 113w)
#    https://www.kaggle.com/datasets/yugagrawal95/sample-media-spends-data
# 2. Kaggle: Facebook Ad Campaign (daily-ish campaign spend)
#    https://www.kaggle.com/datasets/madislemsalu/facebook-ad-campaign
# 3. Kaggle: MMM demo dataset
#    https://www.kaggle.com/datasets/mattwalentosky/mmmdemodataset
# ----------------------------------------------------------------------
KAGGLE_SETS = [
    ("yugagrawal95/sample-media-spends-data", "kaggle_media_spends"),
    ("madislemsalu/facebook-ad-campaign", "kaggle_fb_campaign"),
    ("mattwalentosky/mmmdemodataset", "kaggle_mmm_demo"),
]

def get_kaggle():
    try:
        import kagglehub
        for slug, name in KAGGLE_SETS:
            tgt = os.path.join(RAW, name)
            if os.path.isdir(tgt) and os.listdir(tgt):
                print(f"[skip] {name}"); continue
            path = kagglehub.dataset_download(slug)
            os.makedirs(tgt, exist_ok=True)
            # copy files over
            import shutil
            for f in os.listdir(path):
                shutil.copy(os.path.join(path, f), tgt)
            print(f"[ok]   {name} <- {slug}")
    except Exception as e:
        print(f"[kaggle] failed ({e}). Ensure kaggle.json is configured, or download "
              f"manually from the dataset pages listed in this script.")

# ----------------------------------------------------------------------
# 4. Robyn simulated weekly benchmark (open, direct from GitHub)
# ----------------------------------------------------------------------
ROBYN_URL = ("https://raw.githubusercontent.com/facebookexperimental/Robyn/"
             "main/R/data/dt_simulated_weekly.RData")

def get_robyn():
    tgt = os.path.join(RAW, "robyn_dt_simulated_weekly.csv")
    if done(tgt): print("[skip] robyn"); return
    try:
        import pyreadr, tempfile
        r = requests.get(ROBYN_URL, timeout=60); r.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".RData", delete=False) as f:
            f.write(r.content); tmp = f.name
        res = pyreadr.read_r(tmp)
        df = list(res.values())[0]
        df.to_csv(tgt, index=False)
        print(f"[ok]   robyn benchmark -> {tgt} ({len(df)} rows)")
    except Exception as e:
        print(f"[robyn] failed ({e}). Fallback: clone github.com/facebookexperimental/Robyn "
              f"and load R/data/dt_simulated_weekly.RData in R, write.csv it.")

# ----------------------------------------------------------------------
# 5. Bank of England Bank Rate history (STEP covariate) -- open data
# ----------------------------------------------------------------------
BOE_URL = ("https://www.bankofengland.co.uk/boeapps/database/Bank-Rate.asp")

def get_boe():
    tgt = os.path.join(RAW, "boe_bank_rate.csv")
    if done(tgt): print("[skip] boe"); return
    try:
        # The page serves an HTML table of all rate changes; parse it.
        r = requests.get(BOE_URL, timeout=60, headers={"User-Agent": "research-script"})
        r.raise_for_status()
        tables = pd.read_html(io.StringIO(r.text))
        df = tables[0]
        df.to_csv(tgt, index=False)
        print(f"[ok]   BoE bank rate -> {tgt} ({len(df)} changes)")
    except Exception as e:
        print(f"[boe] failed ({e}). Manual: bankofengland.co.uk -> Database -> "
              f"Bank Rate history -> download.")

# ----------------------------------------------------------------------
# 6. OECD monthly Consumer Confidence for the UK (SMOOTH covariate) -- open SDMX
# ----------------------------------------------------------------------
OECD_URL = ("https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_CLI,"
            "4.1/GBR.M.CCICP...AA...H?startPeriod=2015-01&format=csvfilewithlabels")

def get_oecd_cci():
    tgt = os.path.join(RAW, "oecd_uk_consumer_confidence.csv")
    if done(tgt): print("[skip] oecd cci"); return
    try:
        r = requests.get(OECD_URL, timeout=120); r.raise_for_status()
        open(tgt, "wb").write(r.content)
        print(f"[ok]   OECD UK consumer confidence -> {tgt}")
    except Exception as e:
        print(f"[oecd] failed ({e}). Manual: data-explorer.oecd.org -> search "
              f"'Composite consumer confidence' -> UK monthly -> export CSV.")

# ----------------------------------------------------------------------
# 7. ONS quarterly GDP (SPARSE covariate) -- open API
# ----------------------------------------------------------------------
ONS_URL = ("https://api.ons.gov.uk/timeseries/ihyq/dataset/qna/data")

def get_ons_gdp():
    tgt = os.path.join(RAW, "ons_uk_gdp_quarterly.csv")
    if done(tgt): print("[skip] ons gdp"); return
    try:
        r = requests.get(ONS_URL, timeout=60); r.raise_for_status()
        js = r.json()
        rows = [(o["date"], o["value"]) for o in js["quarters"]]
        pd.DataFrame(rows, columns=["quarter", "gdp_growth"]).to_csv(tgt, index=False)
        print(f"[ok]   ONS quarterly GDP -> {tgt} ({len(rows)} quarters)")
    except Exception as e:
        print(f"[ons] failed ({e}). Manual: ons.gov.uk -> series IHYQ -> download CSV.")

# ----------------------------------------------------------------------
# 8. Google Trends weekly indicators (for Chow-Lin/ML arms)
# ----------------------------------------------------------------------
def get_trends():
    tgt = os.path.join(RAW, "gtrends_uk_indicators.csv")
    if done(tgt): print("[skip] trends"); return
    try:
        from pytrends.request import TrendReq
        py = TrendReq(hl="en-GB", tz=0)
        kw = ["cost of living", "mortgage rates", "savings account"]
        py.build_payload(kw, timeframe="2018-01-01 2026-08-01", geo="GB")
        df = py.interest_over_time().drop(columns=["isPartial"], errors="ignore")
        df.to_csv(tgt)
        print(f"[ok]   Google Trends -> {tgt} ({len(df)} weeks)")
    except Exception as e:
        print(f"[trends] failed ({e}). Manual: trends.google.com, export each term, "
              f"or retry later (rate limits).")

# ----------------------------------------------------------------------
# 9. Dunnhumby -- MANUAL (registration click-through; cannot script)
# ----------------------------------------------------------------------
DUNNHUMBY_NOTE = """
[manual] Dunnhumby Source Files (free, registration required):
  1. Visit https://www.dunnhumby.com/source-files/
  2. Download 'Breakfast at the Frat' (weekly, 156w, price/promo/display)
  3. Download 'The Complete Journey' (household transactions -> daily KPI)
  4. Unzip into data/raw/dunnhumby_batf/ and data/raw/dunnhumby_cj/
"""

# ----------------------------------------------------------------------
# 10. ONS CPI annual rate (monthly, smooth-with-shocks) + Retail Sales
#     Index (monthly, seasonal) -- open API
# ----------------------------------------------------------------------
def _ons_series(series, dataset, fname, label):
    tgt = os.path.join(RAW, fname)
    if done(tgt): print(f"[skip] {label}"); return
    try:
        url = f"https://api.ons.gov.uk/timeseries/{series}/dataset/{dataset}/data"
        r = requests.get(url, timeout=60); r.raise_for_status()
        js = r.json()
        rows = [(o["date"], o["value"]) for o in js["months"]]
        pd.DataFrame(rows, columns=["month", "value"]).to_csv(tgt, index=False)
        print(f"[ok]   {label} -> {tgt} ({len(rows)} months)")
    except Exception as e:
        print(f"[{label}] failed ({e}). Manual: ons.gov.uk -> series {series}.")

def get_ons_cpi():   _ons_series("d7g7", "mm23", "ons_uk_cpi_monthly.csv", "ONS CPI")
def get_ons_retail(): _ons_series("j5ek", "drsi", "ons_uk_retail_sales_monthly.csv", "ONS retail sales")

if __name__ == "__main__":
    get_kaggle()
    get_robyn()
    get_boe()
    get_oecd_cci()
    get_ons_gdp()
    get_ons_cpi()
    get_ons_retail()
    get_trends()
    print(DUNNHUMBY_NOTE)
    print("Done. Verify each file opens and columns match phase0_report.md expectations.")