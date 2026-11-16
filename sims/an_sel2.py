import numpy as np, pandas as pd
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 40)
df = pd.read_csv("results/SEL_conf.csv")
df["aw"] = df.bias_w.abs(); df["ad"] = df.bias_d.abs(); df["ah"] = df.bias_h.abs(); df["gap"] = df.aw - df.ad
df["ins_daily"] = df.sse_d <= df.sse_w
df["tier"] = np.where(df.D.abs() < 10, "ROBUST", np.where(df.dR2.abs() >= 0.10, "CLEAR", "UNDET"))
df["ains"] = np.where(df.ins_daily, df.ad, df.aw)
df["prot"] = np.select([df.tier == "ROBUST", df.tier == "CLEAR"], [df.ad, df.ains], default=df.ah)
print("markets", len(df), df.groupby("world").size().to_dict())

# headline table
t = df.groupby("world")[["aw", "ad", "ains", "prot"]].mean().round(1)
t.columns = ["always_weekly", "always_daily", "insample_all", "protocol_P"]
sh = df.groupby(["world", "tier"]).size().unstack(fill_value=0)
sh = (sh.div(sh.sum(1), axis=0)*100).round(0)
t = t.join(sh.add_prefix("%"))
t.loc["MACRO W1-W6"] = t.loc[["W1", "W2", "W3", "W4", "W5", "W6"]].mean().round(1)
t.loc["MACRO all 8"] = t.loc[["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"]].mean().round(1)
print("\n=== mean |bias|, fresh seeds ===\n", t)

# CLEAR tier hit rate (material markets)
rows = []
for w, g in df[(df.tier == "CLEAR") & (df.gap.abs() > 5)].groupby("world"):
    h = (g.ins_daily == (g.gap > 0)).mean(); se = np.sqrt(h*(1 - h)/len(g))
    rows.append(dict(world=w, n=len(g), hit=round(h, 3), ci_lo=round(h - 1.96*se, 3)))
g = df[(df.tier == "CLEAR") & (df.gap.abs() > 5)]
h = (g.ins_daily == (g.gap > 0)).mean()
print("\n=== CLEAR tier hit rate, material markets ===\n", pd.DataFrame(rows).set_index("world"))
print("pooled", len(g), round(h, 3))
print("CLEAR tier: mean |bias| chosen vs weekly vs daily")
print(df[df.tier == "CLEAR"].groupby("world")[["aw", "ad", "ains"]].mean().round(1))

# UNDET tier
print("\n=== UNDETERMINED tier: mean |bias| by choice ===")
u = df[df.tier == "UNDET"].groupby("world")[["aw", "ad", "ains", "ah"]].agg("mean").round(1)
u["n"] = df[df.tier == "UNDET"].groupby("world").size()
print(u); print("pooled", df[df.tier == "UNDET"][["aw", "ad", "ains", "ah"]].mean().round(2).to_dict())
print("UNDET range-covers-truth share (min/max of the two signed biases straddles 0):")
df["cover"] = (np.minimum(df.bias_w, df.bias_d) <= 0) & (np.maximum(df.bias_w, df.bias_d) >= 0)
print(df.groupby("tier").cover.mean().round(2).to_dict())

# ROBUST tier
print("\n=== ROBUST tier: mean |bias| of either arm; share with arm gap >5 ===")
r = df[df.tier == "ROBUST"].groupby("world").agg(n=("gap", "size"), aw=("aw", "mean"), ad=("ad", "mean"),
                                                   gap5=("gap", lambda s: (s.abs() > 5).mean())).round(2)
print(r)

# worst-case: share of markets where protocol is worse than the better fixed arm by >10 points
df["worse10"] = df.prot - np.minimum(df.aw, df.ad) > 10
print("\nshare of markets where protocol is >10 pts worse than the better arm (market-level):", df.groupby("world").worse10.mean().round(2).to_dict())

# criteria
print("\n=== criteria ===")
print("(a) CLEAR pooled hit >=0.75:", round(h, 3), "| min world", pd.DataFrame(rows).hit.min())
m = t.loc["MACRO W1-W6"]; print("(b) macro protocol", m.protocol_P, "vs weekly", m.always_weekly, "daily", m.always_daily)
print("(d) noisy worlds hit:", [r_ for r_ in rows if r_["world"] in ("W7", "W8")])
# by sub-world of the noisy ones
print(df[df.world.isin(["W7", "W8"])].groupby(["world", "sub", "tier"]).size().unstack(fill_value=0))
print(df[df.world.isin(["W7", "W8"])].groupby(["world", "sub"])[["aw", "ad", "ains", "prot"]].mean().round(1))
