"""Loads every result once for the document builders, so that all numbers in the text come from the model outputs."""
import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import pickle, json, sys, numpy as np
sys.path.insert(0, ROOT + "/src")
import registry as REG
from refs import REFS
RES = ROOT + "/results"
CORE = pickle.load(open(f"{RES}/core.pkl", "rb")); UNC = pickle.load(open(f"{RES}/unc.pkl", "rb"))
OPT = pickle.load(open(f"{RES}/opt.pkl", "rb")); ML = pickle.load(open(f"{RES}/ml.pkl", "rb"))
FIG = json.load(open(f"{RES}/figreg.json")); CLOS = json.load(open(f"{RES}/closure.json"))
H = CORE["base"]["HTL"]; F = CORE["base"]["FAME"]; S = CORE["scen"]; SDEF = {d["id"]: d for d in CORE["scen_def"]}
CME = CORE["cme_ldeq"]; DSL = REG.BASE["p_diesel"]; B = REG.BASE; FX = REG.FX
RISK = UNC["risk"]; SOB = UNC["sobol"]; MOR = UNC["morris"]; ST = UNC["stoch"]
BR = CORE["bridge"]; BE = {r["item"]: r for r in CORE["breakeven"]}; VAL = CORE["validate"]; VER = CORE["verify"]; INH = CORE["verify_inh"]
LOG = CORE["logistics"]; PROS = CORE["prospective"]; OAT = CORE["oat"]
CALC_URL = "https://claude.ai/artifact/WM4YFxDZT5P5kMJq1AnZuF"
NMC = len(UNC["mc"]["S01 HTL base"]["mfsp_ldeq"])
def be(item): return BE[item]["value"]
def oat_top(route, key, n=8):
    return sorted([o for o in OAT if o["route"] == route], key=lambda o: -o[key + "_swing"])[:n]
def sob_top(route, j, n=6):
    s = SOB[route]; o = np.argsort(-s["ST"][:, j])[:n]
    return [(s["keys"][i], float(s["S1"][i, j]), float(s["ST"][i, j])) for i in o]
NAME = {r["key"]: r["name"] for r in REG.R}
# Monte Carlo convergence: change of P50/P95 and of P(MFSP<CME) between N/2 and N
def conv(design, out="mfsp_ldeq"):
    y = UNC["mc"][design][out]; y = y[np.isfinite(y)]; n = len(y); h = y[: n // 2]
    return dict(p50=abs(np.percentile(h, 50) / np.percentile(y, 50) - 1), p95=abs(np.percentile(h, 95) / np.percentile(y, 95) - 1))
CONV = {d: conv(d) for d in UNC["mc"]}
def se_p(p, n=NMC): return float(np.sqrt(p * (1 - p) / n))
def pr(d, k): return RISK[d][k]
# registry statistics
from collections import Counter
CONF = Counter(r["conf"] for r in REG.R); NPAR = len(REG.R)
DPAR = [r for r in REG.R if r["conf"] == "D"]
FRONT = {k: OPT[k]["front"] for k in ("2026", "2040_CES2", "2050_NZ")}
def fmin(k, key): return min(FRONT[k], key=lambda s: s[key])
MLM = {r: {n: {m["out"]: m for m in v["metrics"]} for n, v in ML[r]["res"].items()} for r in ("HTL", "FAME")}
# first year the prospective HTL MFSP falls below the fixed CME benchmark, by pathway (None = not by 2050)
XOVER = {}
for (rt, pw), rows in PROS.items():
    ys = [r["year"] for r in rows if r["mfsp"] < CME]; XOVER[(rt, pw)] = ys[0] if ys else None
def s1sum(route, j=0, n=2):
    t = sob_top(route, j, n); return sum(x[1] for x in t), sum(x[2] for x in t)
NCHK = len(CLOS); NVER = len(VER); NVFAIL = sum(v["verdict"] == "Fail" for v in VER)
# realised vs target rank correlations
_Cr = UNC["input_corr_realised"]; _K = UNC["keys"]
_dev = [(a, b, r - _Cr[_K.index(a), _K.index(b)]) for a, b, r in UNC["corr"]]
_dd = [x[2] for x in _dev if "p_diesel" in (x[0], x[1])]; _do = [abs(x[2]) for x in _dev if "p_diesel" not in (x[0], x[1])]
CORRDEV = dict(other=max(_do), dmin=min(_dd) if _dd else 0.0, dmax=max(_dd) if _dd else 0.0)
DES26 = [k for k in UNC["mc"] if "2040" not in k and "2050" not in k]
NHIT2026 = int(sum((UNC["mc"][k]["mfsp_ldeq"] < CME).sum() for k in DES26))
def loss_txt(k):
    v = ST[k]; n = len(v["npv"])
    return (f"no negative-NPV outcome was observed among {n:,} simulated paths under these assumptions" if v["p_loss"] == 0 else f"the probability of loss is {v['p_loss']*100:.1f}%")
ST_TXT = loss_txt("S54 HTL NZ 2050")
OUTERR = max(ML["HTL"].get("out_exact_maxerr", 0), ML["FAME"].get("out_exact_maxerr", 0))
try: CALC = json.load(open(f"{RES}/calc_check.json"))
except Exception: CALC = {"HTL": {"mfsp_ldeq": float("nan"), "gwp": float("nan")}, "FAME": {"mfsp_ldeq": float("nan"), "gwp": float("nan")}, "browser_us": float("nan")}
_tp = ML["HTL"]["res"]["Neural network (MLP 64-64)"]["pred_s"]
TIMING_TXT = (f"Timed in Python (scikit-learn, batch prediction averaged over the {int(ML['HTL']['n']*0.2):,} test samples on a two-core cloud container), one network prediction takes about {_tp*1e6:.0f} μs per sample and output, against about {ML['HTL']['t_engine']*1e3:.1f} ms for one engine evaluation; "
              + (f"in a headless Chromium browser the calculator's JavaScript evaluates all networks of one route in about {CALC['browser_us']:.0f} μs." if CALC.get("browser_us") == CALC.get("browser_us") else "browser timing was not measured."))
MLR2 = (min(MLM[r]["Neural network (MLP 64-64)"][o]["r2"] for r in ("HTL", "FAME") for o in ("mfsp_ldeq", "gwp")), max(MLM[r]["Neural network (MLP 64-64)"][o]["r2"] for r in ("HTL", "FAME") for o in ("mfsp_ldeq", "gwp")))
# Morris ranks (HTL): combined cost-and-climate score (as used to select the Sobol' set) and cost alone
_mm = MOR["HTL"]; _sc = _mm["mfsp_ldeq"]["mu_star"] / _mm["mfsp_ldeq"]["mu_star"].max() + _mm["gwp"]["mu_star"] / _mm["gwp"]["mu_star"].max()
_rk_c = {UNC["keys"][i]: n + 1 for n, i in enumerate(np.argsort(-_sc))}
_rk_m = {UNC["keys"][i]: n + 1 for n, i in enumerate(np.argsort(-_mm["mfsp_ldeq"]["mu_star"]))}
def mrank(k, cost_only=False): return (_rk_m if cost_only else _rk_c).get(k)
NMOR = len(UNC["keys"])
