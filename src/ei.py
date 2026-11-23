"""Interface to the life cycle background data.

Two modes, chosen automatically (or forced with ALGAE_EI_MODE=full|compact):

full     the licensed ecoinvent 3.12 matrices and unit scores are present in engine/ (built by src/engine/*.py).
         All 183 indicators are available.
compact  engine/ is absent. The GWP100 unit scores of the ecoinvent activities used by the model are read from
         data/unit_scores_gwp.json. Costs and GWP are identical to the full mode; the other 182 indicators
         are returned as NaN, because their unit scores cannot be redistributed under the ecoinvent licence."""
import os as _os, json as _json, pickle, numpy as np
ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_full_ok = _os.path.exists(ROOT + "/engine/ei312_matrices.pkl")
MODE = _os.environ.get("ALGAE_EI_MODE") or ("full" if _full_ok else "compact")
if MODE == "full":
    _d = pickle.load(open(ROOT + "/engine/ei312_matrices.pkl", "rb")); _cf = pickle.load(open(ROOT + "/engine/cf_312.pkl", "rb"))
    meta = _d["meta"]; cats = _cf["cats"]
    U = (np.load(ROOT + "/engine/unit_scores.npy") if _os.path.exists(ROOT + "/engine/unit_scores.npy")
         else np.vstack([np.load(ROOT + f"/engine/unit_scores_{p}.npz")["U"] for p in "ab"]))  # unit_scores.npy is written by engine/solve.py
else:
    _c = _json.load(open(ROOT + "/data/unit_scores_gwp.json"))
    cats = [tuple(c) for c in _c["indicators"]]
    meta = [dict(activity=a["activity"], location=a["location"], product=a["product"], col=j) for j, a in enumerate(_c["activities"])]
    U = np.full((len(cats), len(meta)), np.nan)
    U[len(cats) - 1, :] = [a["gwp100"] for a in _c["activities"]]
def find(act=None, prod=None, loc=None):
    return [m for m in meta if (act is None or act.lower() in m["activity"].lower()) and (prod is None or prod.lower() in m["product"].lower()) and (loc is None or m["location"] == loc)]
def cat(method, name):
    for k, c in enumerate(cats):
        if c[0] == method and name in c[1]: return k
    raise KeyError((method, name))
GWP = len(cats) - 1
