"""Stage C: adds S3 (exhaustive assignment search). Declared in DESIGN_MULTI.md before running."""
import sys, os, itertools, time, numpy as np, pandas as pd
os.environ.setdefault("MCPREFIX", "MCC")
from joblib import Parallel, delayed
import mc_run as M
from mc_run import *
from mc_oracle import backfit_order, sse_final

def run_market_C(scen, m):
    cfg, spends, contrib, y, C = make_market(scen, m); K = cfg["K"]
    cands = {"w": [cand_set(spends[k], "w") for k in range(K)], "d": [cand_set(spends[k], "d") for k in range(K)]}
    truth_arm = ["w" if t == "WEEKLY" else "d" for t in cfg["truths"]]
    res, used = {}, {}
    res["W"] = contribs(y, C, backfit(y, C, cands, ["w"]*K)[1]); used["W"] = ["w"]*K
    res["D"] = contribs(y, C, backfit(y, C, cands, ["d"]*K)[1]); used["D"] = ["d"]*K
    a1, ch1 = backfit(y, C, cands, ["sel"]*K); res["S1"] = contribs(y, C, ch1); used["S1"] = a1
    a2 = screen_assign(y, C, spends, cands); res["S2"] = contribs(y, C, backfit(y, C, cands, a2)[1]); used["S2"] = a2
    best = None
    for assign in itertools.product(["d", "w"], repeat=K):     # daily first so ties go to daily
        ch = backfit_order(y, C, cands, list(assign), list(range(K)), 3); s = sse_final(y, C, ch)
        if best is None or s < best[0] - 1e-9: best = (s, list(assign), ch)
    res["S3"] = contribs(y, C, best[2]); used["S3"] = best[1]
    res["OF"] = contribs(y, C, backfit(y, C, cands, truth_arm)[1]); used["OF"] = truth_arm
    res["OT"] = contribs(y, C, list(contrib))
    wk = spends.reshape(K, NW, 7).sum(2); corr = np.corrcoef(wk) if K > 1 else np.array([[1.0]]); tt = contrib.sum()
    mrow = dict(scen=scen, m=m, K=K, r2=cfg["r2"], n_weekly=sum(t == "WEEKLY" for t in cfg["truths"]))
    for a, c in res.items(): mrow[f"bias_{a}"] = 100*(c.sum() - tt)/tt
    crow = []
    for k in range(K):
        off = np.abs(np.delete(corr[k], k)).max() if K > 1 else 0.0
        r = dict(scen=scen, m=m, k=k, pattern=cfg["pats"][k], truth=cfg["truths"][k], share=float(cfg["shares"][k]),
                 maxcorr=float(off), truth_arm=truth_arm[k])
        for a, c in res.items(): r[f"bias_{a}"] = 100*(c[k].sum() - contrib[k].sum())/(contrib[k].sum() + 1e-12)
        for a in ("S1", "S2", "S3"): r[f"chosen_{a}"] = used[a][k]
        crow.append(r)
    return mrow, crow

if __name__ == "__main__":
    mode = sys.argv[1]; n = {"smoke": 4, "C": 1000}[mode]
    jobs = [(s, m) for s in SCENS for m in range(n)]
    print("markets", len(jobs), flush=True); t0 = time.time()
    out = Parallel(n_jobs=2, batch_size=4, verbose=5)(delayed(run_market_C)(*j) for j in jobs)
    pd.DataFrame([o[0] for o in out]).to_csv(f"results/MC_{mode}_markets.csv", index=False)
    pd.DataFrame([c for o in out for c in o[1]]).to_csv(f"results/MC_{mode}_channels.csv", index=False)
    print("done", round(time.time() - t0), "s", flush=True)
