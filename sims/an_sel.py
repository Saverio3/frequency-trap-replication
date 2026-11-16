import numpy as np, pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 40)

df = pd.read_csv("results/SEL_full.csv")
df["aw"] = df.bias_w.abs(); df["ad"] = df.bias_d.abs(); df["ah"] = df.bias_h.abs()
df["gap"] = df.aw - df.ad   # >0 -> daily better
print("markets", len(df), df.groupby("world").size().to_dict())

# ---- tree training on core reps 0-49 only
FULL = ["WV", "ZS", "CV", "DEPTH", "dR2", "hgap"]; SCR = ["WV", "ZS", "CV", "DEPTH"]
tr = df[(df.world == "W1") & (df.rep < 50)].dropna(subset=FULL)
trees = {}
for name, feats in [("tree", FULL), ("tree_screen", SCR)]:
    t = DecisionTreeClassifier(max_depth=2, min_samples_leaf=200, random_state=0)
    t.fit(tr[feats], (tr.gap > 0).astype(int)); trees[name] = (t, feats)
    print("\n", name); print(export_text(t, feature_names=feats))

# ---- choices (True = daily)
ch = pd.DataFrame(index=df.index)
ch["weekly"] = False; ch["daily"] = True
ch["insample"] = df.sse_d <= df.sse_w
ch["holdout"] = df.rm_d <= df.rm_w
ch["both"] = ~((df.sse_w < df.sse_d) & (df.rm_w < df.rm_d))
for name, (t, feats) in trees.items():
    X = df[feats].fillna(0)
    ch[name] = t.predict(X).astype(bool)
cell_mean = df.groupby("cell")[["aw", "ad"]].transform("mean")
ch["cell_oracle"] = cell_mean.ad <= cell_mean.aw
ch["mkt_oracle"] = df.ad <= df.aw
loss = pd.DataFrame({k: np.where(v, df.ad, df.aw) for k, v in ch.items()}, index=df.index)
loss["hedge"] = df.ah
# evaluation mask: exclude training reps of core world
ev = ~((df.world == "W1") & (df.rep < 50))
L = loss[ev].copy(); L["world"] = df.world[ev]; L["sub"] = df["sub"][ev]
order = ["weekly", "daily", "insample", "holdout", "both", "hedge", "tree", "tree_screen", "cell_oracle", "mkt_oracle"]
byw = L.groupby("world")[order].mean().round(1)
byw.loc["MACRO"] = byw.mean().round(1)
print("\n=== mean |bias| by selector and world (eval set) ===\n", byw)
print("\n=== W2-W3 subworlds ===")
print(L[L.world.isin(["W2", "W3", "W6"])].groupby(["world", "sub"])[order].mean().round(1))

# ---- hit rate among material markets
D = df[ev].copy(); C = ch[ev]
mat = D["gap"].abs() > 5
rows = []
for w, g in D[mat].groupby("world"):
    r = {"world": w, "n_material": len(g), "share_material": round(len(g)/(D.world == w).sum(), 2),
         "daily_better_share": round((g["gap"] > 0).mean(), 2)}
    for s in ["insample", "holdout", "both", "tree", "tree_screen"]:
        hit = (C.loc[g.index, s] == (g["gap"] > 0)).mean()
        se = np.sqrt(hit*(1 - hit)/len(g))
        r[s] = f"{hit:.2f}"
        r[s + "_ci_lo"] = round(hit - 1.96*se, 2)
    rows.append(r)
H = pd.DataFrame(rows).set_index("world")
print("\n=== hit rate among material markets (|diff|>5 pts) ===\n", H[["n_material", "share_material", "daily_better_share", "insample", "holdout", "both", "tree", "tree_screen"]])
print(H[[c for c in H.columns if c.endswith("ci_lo")]])

# ---- disagreement flag
D["robust"] = D.D.abs() < 10
print("\n=== disagreement flag |D|<10 ===")
fl = D.groupby(["world", "robust"]).agg(n=("gap", "size"), mean_absdiff=("gap", lambda s: s.abs().mean()),
                                         p90_absdiff=("gap", lambda s: s.abs().quantile(.9)),
                                         mean_aw=("aw", "mean"), mean_ad=("ad", "mean")).round(1)
print(fl)
tot = D.groupby("robust").agg(n=("gap", "size"), mean_absdiff=("gap", lambda s: s.abs().mean()),
                              share_diff_gt5=("gap", lambda s: (s.abs() > 5).mean()), mean_aw=("aw", "mean"), mean_ad=("ad", "mean")).round(2)
print("\npooled\n", tot)

# ---- exploratory: reliability vs size of signals (labelled exploratory)
print("\n=== EXPLORATORY: hit rate of holdout / insample by size of signal (material markets, pooled) ===")
M = D[mat].copy(); M["hg"] = M.hgap.abs(); M["dr"] = M.dR2.abs()
M["hit_h"] = (C.loc[M.index, "holdout"] == (M["gap"] > 0)); M["hit_i"] = (C.loc[M.index, "insample"] == (M["gap"] > 0))
M["hg_bin"] = pd.qcut(M.hg, 5, duplicates="drop"); M["dr_bin"] = pd.qcut(M.dr, 5, duplicates="drop")
print(M.groupby("hg_bin", observed=True)[["hit_h"]].agg(["mean", "size"]).round(2))
print(M.groupby("dr_bin", observed=True)[["hit_i"]].agg(["mean", "size"]).round(2))

# ---- which direction does each world favour (cell level)
cm = df.groupby(["world", "cell"])[["aw", "ad"]].mean()
cm["se"] = df.groupby(["world", "cell"])["gap"].sem()
cm["verdict"] = np.where(cm.aw - cm.ad > 2*cm.se, "daily", np.where(cm.ad - cm.aw > 2*cm.se, "weekly", "tie"))
print("\n=== cell verdicts by world ===\n", cm.groupby(["world", "verdict"]).size().unstack(fill_value=0))
df.to_pickle("results/SEL_df.pkl"); ch.to_pickle("results/SEL_choices.pkl")
