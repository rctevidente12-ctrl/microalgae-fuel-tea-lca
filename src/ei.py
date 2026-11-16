import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import pickle, numpy as np
_d=pickle.load(open(ROOT + "/engine/ei312_matrices.pkl","rb")); _cf=pickle.load(open(ROOT + "/engine/cf_312.pkl","rb"))
meta=_d["meta"]; cats=_cf["cats"]
U=(np.load(ROOT + "/engine/unit_scores.npy") if _os.path.exists(ROOT + "/engine/unit_scores.npy") else np.vstack([np.load(ROOT + f"/engine/unit_scores_{p}.npz")["U"] for p in "ab"]))  # unit_scores.npy is written by engine/solve.py
def find(act=None,prod=None,loc=None):
    return [m for m in meta if (act is None or act.lower() in m["activity"].lower()) and (prod is None or prod.lower() in m["product"].lower()) and (loc is None or m["location"]==loc)]
def cat(method,name):
    for k,c in enumerate(cats):
        if c[0]==method and name in c[1]: return k
    raise KeyError((method,name))
GWP=len(cats)-1
