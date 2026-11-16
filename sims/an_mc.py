import sys, numpy as np, pandas as pd
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 40)
tag = sys.argv[1] if len(sys.argv) > 1 else "A"
mk = pd.read_csv(f"results/MC_{tag}_markets.csv"); ch = pd.read_csv(f"results/MC_{tag}_channels.csv")
SEL = ["S1", "S2", "S3"] if "bias_S3" in mk.columns else ["S1", "S2"]
ARMS = ["W", "D"] + SEL + ["OF", "OT"]
SC = ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10"]
print(f"stage {tag}: markets {len(mk)}, channels {len(ch)}")
ab = mk[[f"bias_{a}" for a in ARMS]].abs(); ab.columns = ARMS; ab["scen"] = mk.scen
T = ab.groupby("scen")[ARMS].mean().loc[SC].round(1)
T.loc["MACRO"] = T.mean().round(1)
print("\n=== TOTAL media contribution: mean |bias| % ===\n", T)
sg = mk.groupby("scen")[[f"bias_{a}" for a in ARMS]].mean().loc[SC].round(1); sg.columns = ARMS
print("\n=== mean SIGNED bias % ===\n", sg)
# paired comparisons
rows = []
for s in SC:
    d = ab[ab.scen == s]
    def pc(a, b):
        x = (d[a] - d[b]); se = x.std(ddof=1)/np.sqrt(len(x)); return x.mean(), se
    dw, sdw = pc("W", "D")
    best_fixed = np.minimum(d.W.mean(), d.D.mean())
    row = dict(scen=s, W_minus_D=round(dw, 1), se=round(sdw, 2),
               verdict_D_vs_W=("D better" if dw > 2*sdw else "W better" if dw < -2*sdw else "tie"),
               S1_minus_bestfixed=round(d.S1.mean() - best_fixed, 1), S2_minus_bestfixed=round(d.S2.mean() - best_fixed, 1),
               OF_minus_OT=round(d.OF.mean() - d.OT.mean(), 1))
    rows.append(row)
P = pd.DataFrame(rows).set_index("scen"); print("\n=== paired verdicts and C2 gaps ===\n", P)
m = T.loc["MACRO"]
print("\nC2: macro S1", m.S1, "S2", m.S2, "vs W", m.W, "D", m.D, "| min(W,D) =", min(m.W, m.D))
for a in SEL: print(f"C2 {a}: macro {m[a]}, worst scenario gap vs best fixed:", round(max(ab[ab.scen==s_][a].mean()-min(ab[ab.scen==s_].W.mean(), ab[ab.scen==s_].D.mean()) for s_ in SC),1))
# channel classification
for a in SEL:
    ch[f"ok_{a}"] = ch[f"chosen_{a}"] == ch.truth_arm
tab = ch.groupby("scen")[[f"ok_{a}" for a in SEL]].mean().loc[SC].round(3)
tab["n_ch"] = ch.groupby("scen").size()
print("\n=== per-channel frequency identification accuracy ===\n", tab)
core = ch[ch.scen.isin(["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M10"])]
print("C3 pooled (M1-M7, M10):", {a: round(core[f"ok_{a}"].mean(), 3) for a in SEL})
print("by true type (all scenarios):\n", ch.groupby("truth_arm")[[f"ok_{a}" for a in SEL]].mean().round(3))
print("\nby pattern:\n", ch.groupby("pattern")[[f"ok_{a}" for a in SEL]].mean().round(3))
ch["sbin"] = pd.cut(ch.share, [0, .1, .3, 1.01]); ch["cbin"] = pd.cut(ch.maxcorr, [-.01, .3, .6, 1.01])
print("\nby share:\n", ch.groupby("sbin", observed=True)[[f"ok_{a}" for a in SEL]].mean().round(3))
print("\nby max cross-channel weekly correlation:\n", ch.groupby("cbin", observed=True)[[f"ok_{a}" for a in SEL]].agg(["mean", "size"]).round(3))
# channel-level |bias|
cb = ch[[f"bias_{a}" for a in ARMS]].abs(); cb.columns = ARMS; cb["scen"] = ch.scen
print("\n=== per-CHANNEL mean |bias| % ===\n", cb.groupby("scen")[ARMS].mean().loc[SC].round(1))
print("by truth type:\n", cb.assign(t=ch.truth_arm).groupby("t")[ARMS].mean().round(1))
print("by share bin:\n", cb.assign(s=ch.sbin).groupby("s", observed=True)[ARMS].mean().round(1))
# hit-rate of the selector arms vs picking best fixed arm per market

# per-channel paired D vs W (channel-level |bias|)
rows=[]
for s_ in SC:
    d = cb[cb.scen==s_]; x = d.W - d.D; se = x.std(ddof=1)/np.sqrt(len(x))
    rows.append(dict(scen=s_, W_minus_D=round(x.mean(),1), se=round(se,2), verdict="D better" if x.mean()>2*se else "W better" if x.mean()<-2*se else "tie"))
print("\n=== per-channel paired W vs D ===\n", pd.DataFrame(rows).set_index("scen"))
