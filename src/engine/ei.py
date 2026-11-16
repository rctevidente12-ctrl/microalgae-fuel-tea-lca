import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parents[1])); from paths import ENGINE, MODEL, ANALYSIS, RESULTS, FIGURES, DATA, PARSED, ROOT
import pickle,numpy as np
_d=pickle.load(open(str(ENGINE/"ei312_matrices.pkl"),"rb")); _cf=pickle.load(open(str(ENGINE/"cf_312.pkl"),"rb"))
A=_d["A"].tocsc(); B=_d["B"].tocsc(); meta=_d["meta"]; elem=_d["elem"]; cats=_cf["cats"]; C=_cf["C"]
U=(np.load(str(ENGINE/"unit_scores.npy")) if (ENGINE/"unit_scores.npy").exists() else np.vstack([np.load(str(ENGINE/f"unit_scores_{p}.npz"))["U"] for p in "ab"]))
IDX={(m["activity"],m["product"],m["location"]):m["col"] for m in meta}
def col(act,prod,loc):
    k=(act,prod,loc)
    if k in IDX: return IDX[k]
    raise KeyError(k)
def find(act=None,prod=None,loc=None):
    return [m for m in meta if (act is None or act in m["activity"]) and (prod is None or prod in m["product"]) and (loc is None or m["location"]==loc)]
def exchanges(j):
    a=A[:,j]; b=B[:,j]; out=[]
    for i,v in zip(a.indices,a.data):
        if i==j: continue
        m=meta[i]; out.append(("T",i,m["activity"],m["product"],m["location"],m["unit"],-v))
    for i,v in zip(b.indices,b.data):
        e=elem[i]; out.append(("B",i,e[1],e[2]+"/"+e[3],"",e[4],v))
    return out
def cat(method,name):
    for k,c in enumerate(cats):
        if c[0]==method and c[1]==name: return k
    raise KeyError((method,name))
GWP=len(cats)-1
