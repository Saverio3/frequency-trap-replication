"""Headline tables for the studies whose own analysis scripts were lost (S1, S2b, S4a, S4b, REC, S3, RB).
Added 27 Nov 2026 to check the regenerated result files against the numbers in docs/. Run from sims/:
    python an_regen_check.py > results/REGEN_check_analysis.txt
Each block names the doc line it should be compared with."""
import pandas as pd

def ab(f):
    d = pd.read_csv(f"results/{f}.csv"); d["ab"] = d.bias.abs(); return d

print("== S1 time-varying: mean |bias| by form x arm  (doc: linear weekly 21.6, daily 20.4)")
print(ab("S1_timevarying").groupby(["form", "arm"]).ab.mean().round(1).unstack(), "\n")

print("== S4a sub-daily truth  (doc: weekly 23.7-25.1, daily 12.6-13.4, native 11.4-13.7)")
print(ab("S4a").groupby(["scen", "arm"]).ab.mean().round(1).unstack(), "\n")

print("== S4b alternative DGPs  (doc: weekly_true 16.5 vs 27.4; linear ext 10.3 vs 17.3; twocomp 13.9 vs 21.9)")
print(ab("S4b").groupby(["form", "arm"]).ab.mean().round(1).unstack(), "\n")

print("== S3 Robyn-style emulation  (doc: rbI 22.8 vs 31.5, rbV 35.9 vs 42.4)")
print(ab("S3_full").groupby("arm").ab.mean().round(1), "\n")

print("== S2b targeted weekday, strength > 0  (doc: A weekly 23.9 dailyT 20.6 dow 12.1; B 22.3 / 29.1 / 13.3)")
d = ab("S2b_full"); print(d[d.strength > 0].groupby(["profile", "arm"]).ab.mean().round(1).unstack(), "\n")

print("== REC shallow saturation: mean |total bias| by freq x estimator x depth  (doc: D/G 18.8 18.6 32.7 41.0 42.2; D/X 18.8 19.4 16.7 12.9 12.9)")
print(ab("REC_full").groupby(["freq", "est", "depth"]).ab.mean().round(1).unstack()[["med", "mild", "x1", "x3", "x10"]], "\n")

print("== RB Robyn-type engine (corrected ridge scaling): mean |total bias| by scenario  (doc: RESULTS_ALL_v3.md C2 table)")
r = pd.read_csv("results/RB_full.csv"); c = [x for x in r.columns if x.startswith("bias_")]
print(r[c].abs().groupby(r.scen).mean().round(1).to_string())
