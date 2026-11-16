# Data used, where it came from, and licence flags

| File(s) | Source | Used by | Can it be public? |
|---|---|---|---|
| `original_paper/data/raw/kaggle_fb_campaign/fb_campaign.csv` (= `sims/fb.csv`) | Kaggle "Facebook Ad Campaign" (madislemsalu) | real-spend shapes in every simulation (`lib.real_shapes()` reads `sims/fb.csv`) | **CHECK the Kaggle dataset licence before making the repo public.** Keep the repo private until checked. |
| `original_paper/data/raw/kaggle_media_spends/Sample_Media_Spend_Data.csv` | Kaggle "Sample Media Spends Data" (yugagrawal95) | `real_data_application.py` module 2 | Check licence (same warning). |
| `original_paper/data/raw/robyn_dt_simulated_weekly.csv` | Meta Robyn demo data (MIT licence repo) | module 4 | Yes (cite Meta Robyn). |
| `boe_bank_rate.csv`, `ons_uk_*.csv`, `oecd_uk_consumer_confidence.csv` | Bank of England, ONS, OECD open data | module 1 | Yes (cite the publishers). |
| `gtrends_*.csv` | Google Trends exports | module 1 indicator | Check Google Trends terms; small files. |
| `data_notes/bike_sales_data.csv` | in the project; **not used by any script in this repo** | none | Unknown origin. Remove before going public unless you know where it is from. |
| Dunnhumby "Breakfast at the Frat" | dunnhumby (free, registration) | `real_data_application.py` module 3 | **Not included** (licence). Download it yourself from dunnhumby.com/source-files and unzip into `original_paper/data/raw/dunnhumby_batf/`. The `p4_batf_*.csv` results in `original_paper/results_phase4/` came from it. |

`original_paper/download_datasets.py` re-fetches the open files and the Kaggle files (needs a Kaggle API token).
