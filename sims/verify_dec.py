"""Independent check of the optimiser used in the decision study: is the SLSQP optimum at least as good as the best of many random feasible allocations?"""
import numpy as np, dec_run as D
rng = np.random.default_rng(1); worse = 0; tot = 0; gaps = []
for scen in ["M1", "M2", "M4", "M7"]:
    for m in range(8):
        cfg, sp, contrib, y, C, chs, consts = D.make_market2(scen, m, 156, "DECCHK"); K = cfg["K"]
        S = sp.reshape(K, -1).sum(1); tf = D.make_true_fn(chs, consts)
        for bk, (lo, hi) in D.BOUNDS.items():
            s_opt = D.optimise(tf, K, S, lo, hi, 7); v_opt = sum(tf(k, s_opt[k]) for k in range(K))
            best = -1
            for _ in range(3000):
                s = rng.uniform(lo, hi, K); 
                # project to budget by scaling the free direction: s -> s*c (clip) iterate
                for _i in range(50):
                    s = np.clip(s*(S.sum()/(s@S)), lo, hi)
                if abs(s@S - S.sum())/S.sum() < 1e-3: best = max(best, sum(tf(k, s[k]) for k in range(K)))
            tot += 1; gap = 100*(best - v_opt)/v_opt; gaps.append(gap)
            if gap > 1e-3: worse += 1
print("checked", tot, "allocations; random search beat the optimiser (by >0.001%) in", worse, "cases; max gap %.4f%%" % max(gaps))
