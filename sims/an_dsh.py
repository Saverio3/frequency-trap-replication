"""Analysis of the multichannel shallow-saturation study (DESIGN_DECISION.md Part 3)."""
import numpy as np, pandas as pd
pd.set_option("display.width", 250)
df = pd.read_csv("results/DSH_main.csv"); df["abias"] = df.bias.abs(); df["aext"] = df.extrap_err.abs()
ARMS = ["W", "D", "WX", "DX", "OT"]
df["masked"] = ((df.abias < 10) & (df.aext > 25)).astype(float)
df["good"] = (df.abias < 10).astype(float)
for sc in ["M11", "M11c"]:
    s = df[df.scen == sc]; print(f"\n================ {sc} ({'shallow x1/x3/x10' if sc=='M11' else 'control mild/med/deep'}), {s.m.nunique()} markets ================")
    print("mean |total bias| %:", s.groupby("arm").abias.mean().reindex(ARMS).round(1).to_dict())
    print("mean |extrapolation error| % (gain from doubling all spend):", s.groupby("arm").aext.mean().reindex(ARMS).round(1).to_dict())
    print("median |extrapolation error| %:", s.groupby("arm").aext.median().reindex(ARMS).round(1).to_dict())
    print("share with |bias|<10%:", s.groupby("arm").good.mean().reindex(ARMS).round(3).to_dict())
    print("masked failure share (|bias|<10% and |extrap|>25%), of all markets:", s.groupby("arm").masked.mean().reindex(ARMS).round(3).to_dict())
    g = s[s.good == 1]; print("   among good-looking markets, share with |extrap|>25%:", g.groupby("arm").apply(lambda x: (x.aext > 25).mean()).reindex(ARMS).round(3).to_dict())
    print("mROI median rel err:", s.groupby("arm").mroi_relerr_med.median().reindex(ARMS).round(3).to_dict(), " top-channel hit:", s.groupby("arm").top_hit.mean().reindex(ARMS).round(3).to_dict())
    for bk in ["P", "S"]:
        nf = s[s[f"gstar_{bk}"] >= 1]; nf = nf.assign(cap=nf[f"gest_{bk}"]/nf[f"gstar_{bk}"], harm=(nf[f"gest_{bk}"] < 0).astype(float))
        print(f"decision [{bk}] mean loss % of media contribution:", s.groupby("arm")[f"loss_{bk}"].mean().reindex(ARMS).round(2).to_dict(),
              "| capture median:", nf.groupby("arm").cap.median().reindex(ARMS).round(3).to_dict(), "| harm:", nf.groupby("arm").harm.mean().reindex(ARMS).round(3).to_dict(),
              "| G* mean:", round(s[s.arm=="OT"][f"gstar_{bk}"].mean(), 2))
    def pair(a, b, col):
        p = s.pivot_table(index="m", columns="arm", values=col); d = (p[a] - p[b]).dropna(); return round(d.mean(), 2), round(d.std(ddof=1)/np.sqrt(len(d)), 2)
    print("paired (first minus second; positive = second better): |bias| W-D", pair("W", "D", "abias"), " WX-DX", pair("WX", "DX", "abias"),
          " G vs X for daily D-DX", pair("D", "DX", "abias"), " extrap D-DX", pair("D", "DX", "aext"), " loss_P W-D", pair("W", "D", "loss_P"), " loss_P D-DX", pair("D", "DX", "loss_P"))
