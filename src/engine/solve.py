import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parents[1])); from paths import ENGINE, MODEL, ANALYSIS, RESULTS, FIGURES, DATA, PARSED, ROOT
import pickle,numpy as np,scipy.sparse as sp,scipy.sparse.linalg as spl,time
d=pickle.load(open(ENGINE/"ei312_matrices.pkl","rb")); cf=pickle.load(open(ENGINE/"cf_312.pkl","rb"))
A=d["A"].tocsc(); B=d["B"]; C=cf["C"]
t=time.time(); lu=spl.splu(A.T.tocsc()); print("LU",time.time()-t)
CB=(C@B).toarray()            # categories x activities: direct characterised emissions per activity
U=np.vstack([lu.solve(CB[k]) for k in range(CB.shape[0])])  # unit scores: cradle-to-gate per unit of reference product
print("solve",time.time()-t)
np.save(ENGINE/"unit_scores.npy",U)
