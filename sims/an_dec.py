"""Analysis of the decision-level and sample-length studies (DESIGN_DECISION.md). Usage: python an_dec.py results/DEC_main_156.csv [more files]"""
import sys
import numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 50)
files = sys.argv[1:]
df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
df["abias"] = df["bias"].abs()
ARMS = ["W", "D", "S1", "OF", "OT"]

def paired(sub, col, a="W", b="D"):
    """a minus b on col; positive means b (second) is better when lower is better"""
    p = sub.pivot_table(index=["scen", "nw", "m"], columns="arm", values=col)
    d = (p[a] - p[b]).dropna()
    return d.mean(), d.std(ddof=1)/np.sqrt(len(d)), len(d)

def verdict(mu, se):
    return "second better" if mu > 2*se else ("first better" if mu < -2*se else "tie")

for nw in sorted(df.nw.unique()):
    sub_nw = df[df.nw == nw]
    print(f"\n================ NW = {nw} weeks ================")
    print("\n-- Mean |total bias| % by scenario and arm")
    t = sub_nw.pivot_table(index="scen", columns="arm", values="abias", aggfunc="mean")[ARMS]
    t.loc["pooled (mean of scen)"] = t.mean(); print(t.round(1).to_string())
    print("\n-- Paired W minus D, |total bias| (positive = daily better); 2-SE rule")
    rows = []
    for sc, g in sub_nw.groupby("scen"):
        mu, se, n = paired(g, "abias"); rows.append((sc, n, round(mu, 2), round(se, 2), verdict(mu, se).replace("second", "daily").replace("first", "weekly")))
    print(pd.DataFrame(rows, columns=["scen", "n", "W-D", "SE", "verdict"]).to_string(index=False))
    multi = sub_nw[sub_nw.K > 1]
    if len(multi) == 0: continue
    for bk, name in [("P", "PRIMARY bounds [0.5, 2.0]"), ("S", "SECONDARY bounds [0.8, 1.25]")]:
        print(f"\n-- DECISION LOSS, {name}: % of true media contribution given up (lower is better)")
        t = multi.pivot_table(index="scen", columns="arm", values=f"loss_{bk}", aggfunc="mean")[ARMS]
        t.loc["pooled (mean of scen)"] = t.mean(); print(t.round(2).to_string())
        gs = multi[multi.arm == "OT"].groupby("scen")[f"gstar_{bk}"].mean()
        print("   attainable gain G* (% of true media contribution), mean by scenario:", gs.round(2).to_dict())
        rows = []
        for sc, g in multi.groupby("scen"):
            for a, b in [("W", "D"), ("W", "S1"), ("D", "S1")]:
                mu, se, n = paired(g, f"loss_{bk}", a, b)
                rows.append((sc, f"{a}-{b}", n, round(mu, 2), round(se, 2), verdict(mu, se).replace("second", b).replace("first", a)))
        r = pd.DataFrame(rows, columns=["scen", "pair", "n", "diff", "SE", "better"])
        print("   paired loss differences (positive = second arm has lower loss):")
        print(r.pivot(index="scen", columns="pair", values="better").to_string())
        print(r[r.pair == "W-D"].to_string(index=False))
        # pooled paired W-D across scenarios: mean of scenario means, SE from scenario SEs
        sub = r[r.pair == "W-D"]; pm = sub["diff"].mean(); pse = np.sqrt((sub["SE"]**2).sum())/len(sub)
        print(f"   pooled W-D loss difference {pm:.2f} (SE {pse:.2f})")
        # non-flat markets
        nf = multi[(multi[f"gstar_{bk}"] >= 1.0)].copy()
        nf["cap"] = nf[f"gest_{bk}"]/nf[f"gstar_{bk}"]
        nf["harm"] = (nf[f"gest_{bk}"] < 0).astype(float)
        flat = 1 - len(nf[nf.arm == "OT"])/len(multi[multi.arm == "OT"])
        print(f"   share of markets that are flat (G* < 1%): {flat:.3f}")
        print("   share of attainable gain captured (median, non-flat), by arm and scenario:")
        print(nf.pivot_table(index="scen", columns="arm", values="cap", aggfunc="median")[ARMS].round(2).to_string())
        print("   pooled capture median by arm:", nf.groupby("arm")["cap"].median().reindex(ARMS).round(3).to_dict())
        print("   HARM share (recommended move worse than leaving budget alone), non-flat markets:")
        print(nf.pivot_table(index="scen", columns="arm", values="harm", aggfunc="mean")[ARMS].round(3).to_string())
        print("   pooled harm by arm:", nf.groupby("arm")["harm"].mean().reindex(ARMS).round(3).to_dict())
    print("\n-- Marginal ROI at observed spend: median relative error (median over markets of the market median over channels)")
    print(multi.pivot_table(index="scen", columns="arm", values="mroi_relerr_med", aggfunc="median")[ARMS].round(3).to_string())
    print("\n-- Top channel by true marginal ROI correctly identified (share of markets)")
    print(multi.pivot_table(index="scen", columns="arm", values="top_hit", aggfunc="mean")[ARMS].round(3).to_string())
    print("   pooled:", multi.groupby("arm")["top_hit"].mean().reindex(ARMS).round(3).to_dict())
    print("\n-- Full channel ordering by marginal ROI correct (share of markets)")
    print(multi.pivot_table(index="scen", columns="arm", values="order_ok", aggfunc="mean")[ARMS].round(3).to_string())
    print("   pooled:", multi.groupby("arm")["order_ok"].mean().reindex(ARMS).round(3).to_dict())
