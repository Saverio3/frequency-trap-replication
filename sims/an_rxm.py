"""Analysis of the controlled real-Robyn experiment (DESIGN_ROBYN_CONTROLLED.md). Usage: python an_rxm.py results/RXM_full.csv [more csv files]"""
import sys, numpy as np, pandas as pd
pd.set_option("display.width", 220)
d = pd.concat([pd.read_csv(f) for f in sys.argv[1:]], ignore_index=True)
tr = pd.read_csv("robyn_mc/truth_mc.csv").set_index("market")
d["true_total"] = d.market.map(tr.true_total); d["type"] = d.market.map(tr.type)
d["bias"] = 100*(d.est_total - d.true_total)/d.true_total; d["abias"] = d.bias.abs()
for k in (1, 2, 3):
    d[f"cb{k}"] = (100*(d[f"est_ch{k}"] - d.market.map(tr[f"true_ch{k}"]))/d.market.map(tr[f"true_ch{k}"])).abs()
d["chan_abias"] = d[["cb1", "cb2", "cb3"]].mean(axis=1)
# first run per (market, arm, rule) is the main run; later ones are repeats (noise)
d["rep"] = d.groupby(["market", "arm", "rule"]).cumcount()
main = d[d.rep == 0]
print("runs:", len(d), " main:", len(main), " repeats:", int((d.rep > 0).sum()), " iterations x trials:", sorted(set(zip(d.iterations, d.trials))))
for rule in ("errscore", "nrmse"):
    m = main[main.rule == rule]; print(f"\n================ selection rule: {rule} ({'PRIMARY' if rule=='errscore' else 'secondary'}) ================")
    print("mean |total bias| % by arm and market type (n markets in brackets):")
    t = m.pivot_table(index="type", columns="arm", values="abias", aggfunc=["mean", "count"]); print(t.round(1).to_string())
    print("overall mean |total bias|:", m.groupby("arm").abias.mean().round(1).to_dict(), " mean signed bias:", m.groupby("arm").bias.mean().round(1).to_dict(), " mean |channel bias|:", m.groupby("arm").chan_abias.mean().round(1).to_dict())
    p = m.pivot_table(index="market", columns="arm", values="abias")
    def pair(a, b, mask=None):
        q = p[[a, b]].dropna()
        if mask is not None: q = q[q.index.map(mask)]
        if len(q) < 2: return None
        df = q[a] - q[b]; return dict(n=len(q), diff=round(df.mean(), 2), se=round(df.std(ddof=1)/np.sqrt(len(q)), 2), b_better=int((df > 0).sum()))
    ty = lambda t_: (lambda mk: tr.type[mk] == t_)
    print("PRIMARY paired A minus B (positive = B, daily transform, better):", pair("A", "B"))
    for t_ in ("independent", "correlated", "mixed"): print("   ", t_, pair("A", "B", ty(t_)))
    if "C" in p.columns:
        print("SECONDARY paired A minus C (positive = daily Robyn better):", pair("A", "C"))
        print("   paired B minus C:", pair("B", "C"))
    pc = m.pivot_table(index="market", columns="arm", values="chan_abias")
    q = pc[["A", "B"]].dropna(); dd = q.A - q.B
    if len(q) > 1: print("paired A minus B on mean |channel bias|: n=%d diff %.2f se %.2f" % (len(q), dd.mean(), dd.std(ddof=1)/np.sqrt(len(q))))
print("\nPer-market table (errscore rule): bias % of total contribution")
print(main[main.rule == "errscore"].pivot_table(index=["market", "type"], columns="arm", values="bias").round(1).to_string())
rep = d[d.rule == "errscore"].groupby(["market", "arm"]).bias.agg(["count", "mean", "std", "min", "max"]); rep = rep[rep["count"] > 1]
if len(rep): print("\nRUN-TO-RUN VARIATION (same market and arm, repeated runs):"); print(rep.round(1).to_string()); print("median SD (points): %.1f" % rep["std"].median())
print("\nconvergence messages (first run per market/arm, errscore): share containing 'NOT converged':", round(main[main.rule == 'errscore'].converged_msg.astype(str).str.contains("NOT").mean(), 2))
print("secs per run median:", main.secs.median(), " n_pareto1 median:", main.n_pareto1.median())
