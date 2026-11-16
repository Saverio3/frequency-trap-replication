"""Pre-declared analysis of the Robyn stability experiment (DESIGN_ROBYN_STABILITY.md).
Usage: python an_stab.py results/RXM_laptop.csv results/RXM_stability.csv [robyn_mc/truth_mc.csv]"""
import sys, numpy as np, pandas as pd
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 50)
orig = pd.read_csv(sys.argv[1]); stab = pd.read_csv(sys.argv[2])
tr = pd.read_csv(sys.argv[3] if len(sys.argv) > 3 else "robyn_mc/truth_mc.csv").set_index("market")
MK = [0, 2, 4, 7, 11, 13]
orig = orig[orig.market.isin(MK) & orig.arm.isin(["A", "B"])].copy(); orig["tag"] = "orig2000"
d = pd.concat([orig, stab], ignore_index=True)
d["true_total"] = d.market.map(tr.true_total)
d["bias"] = 100*(d.est_total - d.true_total)/d.true_total
d["rssd_converged"] = d.get("rssd_converged"); 
def conv_from_msg(m, key):
    m = str(m)
    if key + " NOT converged" in m: return False
    if key + " converged" in m: return True
    return np.nan
if "conv_msg_rssd" not in d or d.conv_msg_rssd.isna().all():
    pass
d["rssd_ok"] = [r.rssd_converged if pd.notna(getattr(r, "rssd_converged", np.nan)) else conv_from_msg(r.converged_msg, "DECOMP.RSSD") for r in d.itertuples()]
d["nrmse_ok"] = [r.nrmse_converged if pd.notna(getattr(r, "nrmse_converged", np.nan)) else conv_from_msg(r.converged_msg, "NRMSE") for r in d.itertuples()]
d["conv"] = np.select([(d.rssd_ok == True) & (d.nrmse_ok == True), (d.nrmse_ok == True), (d.rssd_ok == True)], ["both", "NRMSE only", "RSSD only"], "neither")
print("runs per tag:", d.groupby("tag").size().div(2).to_dict(), "(2 rows per run)")
for rule in ("errscore", "nrmse"):
    x = d[d.rule == rule]; w = x.pivot_table(index=["market", "arm"], columns="tag", values="bias")
    w = w.reindex(columns=["orig2000", "rep2000", "inc4000"])
    print(f"\n=========== rule: {rule} ({'PRIMARY' if rule == 'errscore' else 'secondary'}) ===========")
    print("bias % of true total, by market, arm and run:"); print(w.round(1).to_string())
    N = (w.orig2000 - w.rep2000).abs(); S = w.inc4000 - w[["orig2000", "rep2000"]].mean(axis=1)
    ok = N.notna() & S.notna(); n = int(ok.sum())
    print(f"\ncells with all three runs: {n}")
    if n >= 2:
        mN, mS = N[ok].median(), S[ok].abs().median(); se = S[ok].std(ddof=1)/np.sqrt(n)
        print(f"noise N = |orig2000 - rep2000|: median {mN:.1f}, mean {N[ok].mean():.1f}, max {N[ok].max():.1f} points; implied single-run SD about {N[ok].mean()/1.128:.1f}")
        print(f"budget shift S = inc4000 - mean(2000 runs): median |S| {mS:.1f}, mean S {S[ok].mean():+.1f} (SE {se:.1f}), max |S| {S[ok].abs().max():.1f}")
        mat = (mS > 1.5*mN) and abs(S[ok].mean()) > 2*se
        verdict = "OPTIMISATION-STABILITY PROBLEM" if mat else ("NO MATERIAL BUDGET EFFECT" if mS <= mN else "INCONCLUSIVE")
        print("pre-declared reading:", verdict, f"(median|S|/median N = {mS/mN if mN > 0 else float('nan'):.2f})")
    # A - B on |bias|
    ab = w.abs().unstack("arm"); print("\nA minus B on |bias| (positive = B better), by market and run:")
    out = pd.DataFrame({t: ab[t]["A"] - ab[t]["B"] for t in ["orig2000", "rep2000", "inc4000"]}); print(out.round(1).to_string())
    print("mean over the six markets:", out.mean().round(1).to_dict(), " sign changes of A-B between runs (markets):", int(((np.sign(out).nunique(axis=1)) > 1).sum()), "of", len(out))
print("\n=========== Convergence outcomes (primary-rule rows; one row per run) ===========")
r = d[d.rule == "errscore"]
print(pd.crosstab(r.tag, r.conv)); print(pd.crosstab([r.tag, r.arm], r.conv))
print("\nNumber of Pareto-1 models (median per tag):", r.groupby("tag").n_pareto1.median().to_dict())
print("\n=========== Pareto-1 spread of total contribution vs run-to-run noise (new runs only) ===========")
if "p1_total_min" in d:
    s = d[(d.rule == "errscore") & d.p1_total_min.notna()].copy()
    s["spread_pts"] = 100*(s.p1_total_max - s.p1_total_min)/s.true_total; s["iqr_pts"] = 100*(s.p1_total_q75 - s.p1_total_q25)/s.true_total
    print(s.groupby("tag")[["spread_pts", "iqr_pts", "sel_rank_nrmse", "sel_rank_rssd", "sel_pct_nrmse", "sel_pct_rssd"]].median().round(2).to_string())
