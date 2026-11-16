"""Evaluate candidate tests (design: DESIGN_TESTS.md). usage: python an_tests.py results/TEST_SELT_full.csv [results/TEST_SELU_full.csv]
Calibrate on SELT (leave-one-world-out) ; if a second file is given, calibrate on all SELT worlds and apply to SELU."""
import sys, numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 40)

def load(p):
    d = pd.read_csv(p)
    d["aw"] = d.bias_w.abs(); d["ad"] = d.bias_d.abs(); d["gap"] = d.aw - d.ad
    d["mat"] = d.gap.abs() > 5
    d["yB"] = (d.gap > 0).astype(int)
    d["yA"] = (~d.world.isin(["W2", "W8"])).astype(int)
    d["T5l"] = np.log1p(np.maximum(d.T5, 0)) ; d["T5c"] = d.T5.clip(-5, 20)
    for c in ["T2", "T3", "T4"]:
        d[c + "c"] = d[c].clip(-30, 30)
    return d

SETS = {"T1": ["T1"], "T2": ["T2c"], "T3": ["T3c"], "T4": ["T4c"], "T5": ["T5c"],
        "T1+T5": ["T1", "T5c"], "ALL_tests": ["T1", "T2c", "T3c", "T4c", "T5c"],
        "ALL+old": ["T1", "T2c", "T3c", "T4c", "T5c", "D", "dR2", "hgap", "WV", "ZS", "CV", "DEPTH"]}

def mk(): return make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=500))

def cutoff(p, y, target=0.95, minn=150):
    """smallest confidence cutoff whose training accuracy (conf >= cutoff) >= target."""
    conf = np.abs(p - .5)*2; order = np.argsort(-conf)
    c = conf[order]; ok = ((p[order] > .5) == y[order]).astype(float)
    cum = np.cumsum(ok)/np.arange(1, len(ok) + 1)
    good = np.where((cum >= target) & (np.arange(1, len(ok) + 1) >= minn))[0]
    return c[good.max()] if len(good) else 2.0   # 2.0 = never answer

def loo(d, label, feats, mask_col):
    rows = []
    for w in sorted(d.world.unique()):
        tr = d[(d.world != w) & d[mask_col]]; te = d[(d.world == w) & d[mask_col]]
        if label == "yA":   # world label: train on all markets of other worlds
            tr = d[d.world != w]; te = d[d.world == w]
        m = mk().fit(tr[feats], tr[label])
        ptr = m.predict_proba(tr[feats])[:, 1]; pte = m.predict_proba(te[feats])[:, 1]
        thr = cutoff(ptr, tr[label].values)
        ans = np.abs(pte - .5)*2 >= thr
        full = ((pte > .5) == te[label].values).mean()
        acc = ((pte > .5)[ans] == te[label].values[ans]).mean() if ans.any() else np.nan
        rows.append(dict(world=w, n=len(te), full_acc=full, coverage=ans.mean(), sel_acc=acc, thr=thr,
                         n_ans=int(ans.sum()), n_wrong=int((((pte > .5)[ans]) != te[label].values[ans]).sum())))
    return pd.DataFrame(rows).set_index("world")

def summarize(d, label, mask_col):
    out = {}
    for nm, f in SETS.items():
        r = loo(d, label, f, mask_col)
        tot_ans = r.n_ans.sum()
        pooled_sel = 1 - r.n_wrong.sum()/tot_ans if tot_ans else np.nan
        out[nm] = dict(full_acc=np.average(r.full_acc, weights=r.n), coverage=tot_ans/r.n.sum(),
                       sel_acc=pooled_sel, worst_world_sel=r.sel_acc.min())
    return pd.DataFrame(out).T.round(3)

if __name__ == "__main__":
    d = load(sys.argv[1])
    print("markets", len(d), "| material share", round(d.mat.mean(), 2))
    print("\n=== Label B (market-level better arm), material markets, leave-one-world-out ===")
    print(summarize(d, "yB", "mat"))
    print("\n=== Label A (truth is weekly vs daily-or-finer), all markets, leave-one-world-out ===")
    print(summarize(d, "yA", "mat"))
    # raw separation of the world label by T5 and T1
    from sklearn.metrics import roc_auc_score
    print("\nAUC for world label A:", {k: round(roc_auc_score(d.yA, d[k]), 3) for k in ["T1", "T2c", "T3c", "T4c", "T5c"]})
    dm = d[d.mat]
    print("AUC for market label B (material):", {k: round(roc_auc_score(dm.yB, dm[k]), 3) for k in ["T1", "T2c", "T3c", "T4c", "T5c"]})
    print("\nper-world detail, T5 only, label B:\n", loo(d, "yB", ["T5c"], "mat").round(3))
    print("\nper-world detail, ALL_tests, label B:\n", loo(d, "yB", SETS["ALL_tests"], "mat").round(3))
    print("\nper-world detail, ALL_tests, label A:\n", loo(d, "yA", SETS["ALL_tests"], "mat").round(3))
    # ceiling: gradient boosting LOWO on label B
    F = SETS["ALL+old"]; res = {}
    for w in sorted(d.world.unique()):
        tr = dm[dm.world != w]; te = dm[dm.world == w]
        g = HistGradientBoostingClassifier(max_depth=4, max_iter=200, learning_rate=.08, random_state=0).fit(tr[F], tr.yB)
        res[w] = round(((g.predict_proba(te[F])[:, 1] > .5) == te.yB).mean(), 3)
    print("\nGB ceiling label B, LOWO:", res)
    if len(sys.argv) > 2:
        print("\n\n########## CONFIRMATION on fresh batch ##########")
        e = load(sys.argv[2])
        for label, mask in (("yB", "mat"), ("yA", "mat")):
            for nm in ["T5", "ALL_tests", "ALL+old"]:
                f = SETS[nm]
                tr = d[d[mask]] if label == "yB" else d
                te = e[e[mask]] if label == "yB" else e
                m = mk().fit(tr[f], tr[label]); ptr = m.predict_proba(tr[f])[:, 1]; pte = m.predict_proba(te[f])[:, 1]
                thr = cutoff(ptr, tr[label].values); ans = np.abs(pte - .5)*2 >= thr
                full = ((pte > .5) == te[label].values).mean()
                sel = ((pte > .5)[ans] == te[label].values[ans]).mean() if ans.any() else np.nan
                print(label, nm, "full", round(full, 3), "coverage", round(ans.mean(), 3), "selective", round(sel, 3))
                tmp = te.assign(ans=ans, ok=((pte > .5) == te[label].values))
                print(tmp[tmp.ans].groupby("world").ok.agg(["mean", "size"]).round(3).T)
