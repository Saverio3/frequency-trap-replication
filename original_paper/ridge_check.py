"""
ridge_check.py -- ESTIMATOR ROBUSTNESS (reviewer attack #1)
Does the weekly-aggregation bias survive regularized estimation?
Ridge with CV-selected penalty (= what Robyn-style tools effectively do;
ridge = Bayesian MAP with a normal prior). Base scenario, 100 reps.
Run from the project folder:  python ridge_check.py
"""
import numpy as np, pandas as pd, os
from paper_engine import simA, dadstock, hill, controls, seed_of
os.makedirs("results_phase4", exist_ok=True)
DEC = np.linspace(.05,.95,12); GP=[5,15,30,50,70,85,95]
LAMS=[0.0,1e-4,1e-3,1e-2,1e-1]

def fit_cv(y,builder,C,tr,te):
    best=None
    for d in DEC:
        for gp in GP:
            m=builder(d,gp); Z=np.column_stack([C,m])
            k=Z.shape[1]; E=np.zeros((k,k)); E[-1,-1]=m.var()+1e-9
            for lam in LAMS:
                b=np.linalg.solve(Z[tr].T@Z[tr]+lam*len(y)*E, Z[tr].T@y[tr])
                hold=np.mean((y[te]-Z[te]@b)**2)
                if best is None or hold<best[0]: best=(hold,b[-1]*m,lam)
    return best[1],best[2]

def fit_ols(y,builder,C):
    best=None
    for d in DEC:
        for gp in GP:
            m=builder(d,gp); Z=np.column_stack([C,m])
            b,*_=np.linalg.lstsq(Z,y,rcond=None)
            sse=np.sum((y-Z@b)**2)
            if best is None or sse<best[0]: best=(sse,b[-1]*m)
    return best[1]

rows=[]
for rep in range(100):
    rng=np.random.default_rng(seed_of("ridge2",rep))
    spend,y,true_c,_=simA(0.5,"med",1.0,"bursty",rng)
    n=156;C=controls(n);tr,te=slice(0,130),slice(130,n)
    sw=spend.reshape(n,7).sum(1)
    wk=lambda d,gp:(lambda a:hill(a,np.percentile(a[a>0],gp),1.0))(dadstock(sw,d))
    dy=lambda d,gp:(lambda a:hill(a,np.percentile(a[a>0],gp),1.0).reshape(n,7).sum(1))(dadstock(spend,d))
    for arm,bl in [("weekly",wk),("dailyT",dy)]:
        rows.append(dict(estimator="ols",arm=arm,lam=0,
            bias=100*(fit_ols(y,bl,C).sum()-true_c.sum())/true_c.sum()))
        c,lam=fit_cv(y,bl,C,tr,te)
        rows.append(dict(estimator="cv_ridge",arm=arm,lam=lam,
            bias=100*(c.sum()-true_c.sum())/true_c.sum()))
df=pd.DataFrame(rows)
out=(df.assign(a=lambda d:d.bias.abs()).groupby(["estimator","arm"]).a.mean().round(1).unstack())
print("mean |contribution bias| %:")
print(out.to_string())
print("\ngap (weekly - dailyT) by estimator:")
print((out["weekly"]-out["dailyT"]).round(1).to_string())
df.to_csv("results_phase4/p4_ridge_check.csv",index=False)
print("-> results_phase4/p4_ridge_check.csv")