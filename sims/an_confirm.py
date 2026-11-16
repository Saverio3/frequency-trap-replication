"""Confirmation of Rule Q on fresh batch SELU. Trained on all SELT markets."""
import numpy as np, pandas as pd
from an_tests import *
a = load("results/TEST_SELT_full.csv"); e = load("results/TEST_SELU_full.csv")
def r2fit(d):
    sw = d.dR2/(1 - np.exp(-d.T1).replace(0, np.nan)); sd = sw*np.exp(-d.T1)
    return 1 - np.minimum(sw, sd)
a["R2fit"] = r2fit(a); e["R2fit"] = r2fit(e)
for nm in ["T3", "ALL_tests"]:
    f = SETS[nm]; m = mk().fit(a[f], a.yA)
    e["p"] = m.predict_proba(e[f])[:, 1]; e["pred"] = (e.p > .5).astype(int); e["ok"] = e.pred == e.yA
    z = e[e.R2fit >= 0.80]
    tpr = (z.pred[z.yA == 1] == 1).mean(); tnr = (z.pred[z.yA == 0] == 0).mean()
    print(f"\n##### {nm}: zone R2fit>=0.80: share of markets {len(z)/len(e):.2f}, n={len(z)}")
    print(f"balanced {(tpr+tnr)/2:.3f} | daily TPR {tpr:.3f} | weekly TNR {tnr:.3f}")
    print("zone by world: share in zone / accuracy");
    print(pd.DataFrame({"share_in_zone": (e.R2fit >= .8).groupby(e.world).mean().round(2),
                        "acc_in_zone": z.groupby("world").ok.mean().round(3), "n": z.groupby("world").size()}).T)
    sub = z.groupby(["world", "sub"]).ok.agg(["mean", "size"]); print("sub-worlds below 0.95 (n>=30):\n", sub[(sub["mean"] < .95) & (sub["size"] >= 30)].round(3))
    out = e[e.R2fit < 0.80]
    tpr2 = (out.pred[out.yA == 1] == 1).mean(); tnr2 = (out.pred[out.yA == 0] == 0).mean()
    print(f"outside zone: n={len(out)}, daily TPR {tpr2:.3f}, weekly TNR {tnr2:.3f}, balanced {(tpr2+tnr2)/2:.3f}")
    print("all markets balanced:", round(((e.pred[e.yA == 1] == 1).mean() + (e.pred[e.yA == 0] == 0).mean())/2, 3))
# what decision quality does the world-level call give vs fixed arms (mean |bias|), zone only
f = SETS["ALL_tests"]; m = mk().fit(a[f], a.yA); e["p"] = m.predict_proba(e[f])[:, 1]
e["pickd"] = e.p > .5; e["chosen"] = np.where(e.pickd, e.ad, e.aw)
z = e[e.R2fit >= .8]
print("\nmean |bias| in zone: weekly", round(z.aw.mean(), 1), "daily", round(z.ad.mean(), 1), "world-call pick", round(z.chosen.mean(), 1))
print(z.groupby("world")[["aw", "ad", "chosen"]].mean().round(1))
# label B in zone for completeness
zm = z[z.mat]; print("label B (better arm in the single market) hit rate in zone, material:", round((zm.pickd.astype(int) == zm.yB).mean(), 3), "n", len(zm))
