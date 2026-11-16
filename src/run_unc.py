"""Uncertainty: Monte Carlo (CRN, Iman-Conover dependencies), risk metrics, Morris screening, Sobol indices, stochastic paths."""
import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import sys, pickle, time, numpy as np
from scipy import stats
from scipy.stats import qmc
sys.path.insert(0, ROOT + "/src")
import registry as REG, scen as SC
from model import evaluate, BASE_HTL, BASE_FAME, MJ_PER_LDEQ, RHO, LHV, cashflows, tax_nolco
rng = np.random.default_rng(20261016)
PR = [r for r in REG.R if r["low"] != r["high"]]
KEYS = [r["key"] for r in PR]; K = len(KEYS)
def ppf(r, u):
    a, b, c = r["low"], r["high"], r["base"]
    if r["dist"] == "uni":
        v = a + u * (b - a); return np.round(v) if r["key"] in ("life", "ith", "dep_yr", "nolco_yr") else v
    if b <= a: return np.full_like(u, c)
    c = min(max(c, a), b); m = (c - a) / (b - a)
    return stats.triang.ppf(u, m, loc=a, scale=b - a)
# ---- target rank correlations (dependencies)
CORR = [("p_diesel", "p_cme", 0.6), ("p_diesel", "p_meoh", 0.5), ("p_diesel", "p_heat", 0.7), ("p_diesel", "p_h2", 0.6), ("p_heat", "p_h2", 0.7),
        ("p_el", "p_heat", 0.4), ("p_el", "p_el_sell", 0.6), ("tci_farm", "tci_conv", 0.8), ("cap_farm_acre", "cap_dew", 0.5), ("lipid", "Nfrac", -0.5),
        ("htl_y", "ht_y", 0.3), ("prod", "avail", 0.3), ("p_urea", "p_dap", 0.7), ("p_urea", "p_diesel", 0.4), ("fx", "p_diesel", 0.3), ("w_op", "w_eng", 0.7)]
def iman_conover(U, C):
    n, k = U.shape
    S = stats.norm.ppf((np.argsort(np.argsort(rng.random((n, k)), axis=0), axis=0) + 0.5) / n)
    T = np.linalg.cholesky(C); Ecur = np.corrcoef(S, rowvar=False); Q = np.linalg.cholesky(Ecur)
    Sstar = S @ np.linalg.inv(Q).T @ T.T
    out = np.empty_like(U)
    for j in range(k):
        out[np.argsort(Sstar[:, j]), j] = np.sort(U[:, j])
    return out
def sample(n, correlated=True):
    U = qmc.LatinHypercube(d=K, seed=rng).random(n)
    if correlated:
        C = np.eye(K)
        for a, b, rho in CORR:
            i, j = KEYS.index(a), KEYS.index(b); C[i, j] = C[j, i] = 2 * np.sin(np.pi * rho / 6)   # Spearman -> Pearson
        w, v = np.linalg.eigh(C); C = v @ np.diag(np.maximum(w, 1e-6)) @ v.T; d = np.sqrt(np.diag(C)); C = C / np.outer(d, d)
        U = iman_conover(U, C)
    X = np.column_stack([ppf(PR[j], U[:, j]) for j in range(K)])
    return X
P0 = dict(REG.BASE)
def run(X, D, pros=None, outs=("mfsp_ldeq", "gwp", "npv", "tci", "ldeq", "irr", "abatement", "saving")):
    Y = {o: np.empty(len(X)) for o in outs}
    for i, x in enumerate(X):
        P = dict(P0); P.update(zip(KEYS, x)); Dd = dict(D)
        if pros: P, Dd = SC.prospective(P, Dd, *pros)
        o = evaluate(P, Dd)
        for k in outs: Y[k][i] = o[k]
    return Y
DES = {"S01 HTL base": (BASE_HTL, None), "S02 FAME base": (BASE_FAME, None), "S27 HTL biomass PPA": (dict(BASE_HTL, elec="biomass_ppa"), None),
       "S32 HTL clean utilities": (dict(BASE_HTL, elec="biomass_ppa", heat="biomass"), None), "S50 HTL CES2 2040": (BASE_HTL, ("CES2", 2040)),
       "S54 HTL NZ 2050": (BASE_HTL, ("NZ", 2050))}
R = {"keys": KEYS, "corr": CORR}
t = time.time(); N = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
X = sample(N, True); R["X"] = X
R["mc"] = {}
for name, (D, pros) in DES.items():
    Dd = dict(D)
    if name.startswith("S32"): pass
    R["mc"][name] = run(X, Dd, pros)
    if name.startswith("S32"):
        pass
print("MC", time.time() - t)
Xi = sample(N, False); R["Xi"] = Xi; R["mc_indep"] = {"S01 HTL base": run(Xi, BASE_HTL)}
# S32 includes green H2 in the scenario definition: rerun with ef_h2=1.0 on the same draws
Xg = X.copy(); Xg[:, KEYS.index("ef_h2")] = 1.0; R["mc"]["S32 HTL clean utilities"] = run(Xg, DES["S32 HTL clean utilities"][0])
# ---- risk metrics
cme = P0["p_cme"] / (RHO["fame"] * LHV["fame"]) * MJ_PER_LDEQ
RISK = {}
for name, Y in R["mc"].items():
    m, g, v = Y["mfsp_ldeq"], Y["gwp"], Y["npv"]
    q5 = np.percentile(v, 5)
    RISK[name] = dict(mfsp_p5=np.percentile(m, 5), mfsp_p50=np.median(m), mfsp_p95=np.percentile(m, 95), mfsp_mean=m.mean(),
                      gwp_p5=np.percentile(g, 5), gwp_p50=np.median(g), gwp_p95=np.percentile(g, 95),
                      p_lt_cme=(m < cme).mean(), p_lt_cme_sampled=(m < X[:, KEYS.index("p_cme")] / (RHO["fame"] * LHV["fame"]) * MJ_PER_LDEQ).mean() if "p_cme" in KEYS else np.nan, p_lt_diesel=(m < P0["p_diesel"]).mean(), p_npv_pos=(v > 0).mean(),
                      npv_p50=np.median(v), var5=q5, cvar5=v[v <= q5].mean(), p_save50=(g <= 47.0).mean(), p_save65=(g <= 32.9).mean(), p_below_diesel=(g < 94).mean())
R["risk"] = RISK
# pairwise: probability that HTL base beats FAME base in the same world (CRN)
R["p_htl_beats_fame"] = dict(mfsp=(R["mc"]["S01 HTL base"]["mfsp_ldeq"] < R["mc"]["S02 FAME base"]["mfsp_ldeq"]).mean(), gwp=(R["mc"]["S01 HTL base"]["gwp"] < R["mc"]["S02 FAME base"]["gwp"]).mean())
# ---- correlation / dependency: Spearman input-output, partial rank correlation, output-output
SP = {}
for name in ("S01 HTL base", "S02 FAME base", "S54 HTL NZ 2050"):
    Y = R["mc"][name]; SP[name] = {}
    for out in ("mfsp_ldeq", "gwp", "npv"):
        ok = np.isfinite(Y[out])
        SP[name][out] = np.array([stats.spearmanr(X[ok, j], Y[out][ok])[0] if np.std(X[ok, j]) > 0 else 0 for j in range(K)])
R["spearman"] = SP
def prcc(X, y):
    rx = np.argsort(np.argsort(X, axis=0), axis=0).astype(float); ry = np.argsort(np.argsort(y)).astype(float)
    out = np.zeros(X.shape[1]); A = np.column_stack([np.ones(len(y)), rx])
    for j in range(X.shape[1]):
        idx = [0] + [c + 1 for c in range(X.shape[1]) if c != j]
        Aj = A[:, idx]; b1 = np.linalg.lstsq(Aj, rx[:, j], rcond=None)[0]; b2 = np.linalg.lstsq(Aj, ry, rcond=None)[0]
        e1 = rx[:, j] - Aj @ b1; e2 = ry - Aj @ b2; out[j] = np.corrcoef(e1, e2)[0, 1]
    return out
Y = R["mc"]["S01 HTL base"]; ok = np.isfinite(Y["mfsp_ldeq"])
R["prcc_htl_mfsp"] = prcc(X[ok][:4000], Y["mfsp_ldeq"][ok][:4000]); R["prcc_htl_gwp"] = prcc(X[ok][:4000], Y["gwp"][ok][:4000])
R["input_corr_realised"] = stats.spearmanr(X).statistic
R["outcorr"] = {name: stats.spearmanr(R["mc"][name]["mfsp_ldeq"], R["mc"][name]["gwp"])[0] for name in R["mc"]}
print("risk/corr", time.time() - t)
# ---- Morris screening (all ranged parameters)
def morris(D, r=20, levels=4):
    delta = levels / (2 * (levels - 1)); EE = {o: np.zeros((r, K)) for o in ("mfsp_ldeq", "gwp")}
    for t_ in range(r):
        x = rng.integers(0, levels - 1, K) / (levels - 1)
        x = np.where(x + delta > 1, x - delta, x); order = rng.permutation(K)
        def f(u):
            P = dict(P0); P.update({KEYS[j]: float(ppf(PR[j], np.array([min(max(u[j], 1e-6), 1 - 1e-6)]))[0]) for j in range(K)}); o = evaluate(P, D); return o["mfsp_ldeq"], o["gwp"]
        y0 = f(x)
        for j in order:
            x2 = x.copy(); x2[j] += delta; y1 = f(x2)
            EE["mfsp_ldeq"][t_, j] = (y1[0] - y0[0]) / delta; EE["gwp"][t_, j] = (y1[1] - y0[1]) / delta
            x, y0 = x2, y1
    return {o: dict(mu_star=np.abs(E).mean(0), sigma=E.std(0)) for o, E in EE.items()}
R["morris"] = {"HTL": morris(BASE_HTL), "FAME": morris(BASE_FAME)}
print("morris", time.time() - t)
# ---- Sobol (Saltelli scheme, Jansen estimators), top parameters by Morris mu*
def sobol(D, n=2048, top=30):
    mm = R["morris"]["HTL" if D["route"] == "HTL" else "FAME"]
    score = mm["mfsp_ldeq"]["mu_star"] / mm["mfsp_ldeq"]["mu_star"].max() + mm["gwp"]["mu_star"] / mm["gwp"]["mu_star"].max()
    sel = list(np.argsort(-score)[:top]); k = len(sel)
    base = qmc.Sobol(d=2 * k, scramble=True, seed=7).random(n); A, B = base[:, :k], base[:, k:]
    def f(Um):
        out = np.empty((len(Um), 2))
        for i, u in enumerate(Um):
            P = dict(P0)
            for jj, j in enumerate(sel): P[KEYS[j]] = float(ppf(PR[j], np.array([min(max(u[jj], 1e-9), 1 - 1e-9)]))[0])
            o = evaluate(P, D); out[i] = (o["mfsp_ldeq"], o["gwp"])
        return out
    fA, fB = f(A), f(B); S1 = np.zeros((k, 2)); ST = np.zeros((k, 2)); S1ci = np.zeros((k, 2)); STci = np.zeros((k, 2))
    var = np.var(np.vstack([fA, fB]), axis=0)
    for jj in range(k):
        ABj = A.copy(); ABj[:, jj] = B[:, jj]; fAB = f(ABj)
        S1[jj] = np.mean(fB * (fAB - fA), axis=0) / var
        ST[jj] = 0.5 * np.mean((fA - fAB) ** 2, axis=0) / var
        bs1, bst = [], []
        for _ in range(200):
            ii = rng.integers(0, n, n)
            v = np.var(np.vstack([fA[ii], fB[ii]]), axis=0)
            bs1.append(np.mean(fB[ii] * (fAB[ii] - fA[ii]), axis=0) / v); bst.append(0.5 * np.mean((fA[ii] - fAB[ii]) ** 2, axis=0) / v)
        S1ci[jj] = 1.96 * np.std(bs1, axis=0); STci[jj] = 1.96 * np.std(bst, axis=0)
    return dict(keys=[KEYS[j] for j in sel], S1=S1, ST=ST, S1ci=S1ci, STci=STci, n=n, runs=n * (k + 2))
NS = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
R["sobol"] = {"HTL": sobol(BASE_HTL, NS), "FAME": sobol(BASE_FAME, max(NS // 2, 256))}
print("sobol", time.time() - t)
# ---- stochastic cash flows: OU log-price, Poisson typhoons, interannual productivity noise
def stochastic(D, npaths=5000, floor=None, typhoons=True, ref='cme'):
    o = evaluate(P0, D); life = int(P0["life"]); r = P0["r"]
    p_bar = P0["p_cme"] / (RHO["fame"] * LHV["fame"]) if ref == "cme" else P0["p_diesel"] / MJ_PER_LDEQ; sig, kap = P0["sig_price"], P0["kap_price"]
    var_share = sum(o["cost"][k] for k in ("Electricity", "Heat", "Nutrients", "Hydrogen", "Chemicals", "Logistics", "Water", "Refinery tolling", "CO2 (purchased)"))
    fixed = o["opex"] - var_share
    yrs = np.arange(1, life + 1); disc = (1 + r) ** -yrs
    capex_pv = sum(o["fci"] * w * (1 + r) ** k for w, k in ((0.08, 2), (0.60, 1), (0.32, 0)))
    NPV = np.empty(npaths); PRICES = np.empty((npaths, life)); EV = np.zeros(npaths)
    for i in range(npaths):
        x = 0.0; pr = np.empty(life)
        for t_ in range(life):
            x = x * np.exp(-kap) + sig * np.sqrt((1 - np.exp(-2 * kap)) / (2 * kap)) * rng.standard_normal(); pr[t_] = p_bar * np.exp(x - 0.5 * sig ** 2 / (2 * kap))
        if floor: pr = np.maximum(pr, floor)
        nt = rng.poisson(P0["lam_typh"], life) if typhoons else np.zeros(life, int)
        prodf = np.clip(1 + P0["cv_year"] * rng.standard_normal(life), 0.6, 1.3) * (1 - nt * P0["typh_days"] / 365) / (1 - P0["lam_typh"] * P0["typh_days"] / 365)
        prodf[0] *= 0.75
        rev = o["fuel_mj"] * prodf * pr + o["rev_co"] * prodf
        cost = fixed + var_share * prodf + nt * P0["typh_cost"] * sum(o["capf"].values()) - o["cost"]["Typhoon repairs (expected)"]
        ebitda = rev - cost; dep = np.where(yrs <= P0["dep_yr"], o["fci"] / P0["dep_yr"], 0)
        tax = tax_nolco(ebitda - dep, yrs, int(P0["ith"]), P0["tax"], int(P0["nolco_yr"]))
        NPV[i] = np.sum((ebitda - tax) * disc) - capex_pv - o["wc"] + o["wc"] * disc[-1]; PRICES[i] = pr * MJ_PER_LDEQ; EV[i] = nt.sum()
    return dict(npv=NPV, prices=PRICES[:300], typhoons=EV, p_loss=(NPV < 0).mean(), var5=np.percentile(NPV, 5), cvar5=NPV[NPV <= np.percentile(NPV, 5)].mean(), median=np.median(NPV))
R["stoch"] = {"S01 HTL base": stochastic(BASE_HTL), "S01 no typhoons": stochastic(BASE_HTL, typhoons=False),
              "S54 HTL NZ 2050": None}
Pn, Dn = SC.prospective(P0, BASE_HTL, "NZ", 2050)
_P0 = P0; P0 = Pn; R["stoch"]["S54 HTL NZ 2050"] = stochastic(Dn); R["stoch"]["S54 + price floor at diesel"] = stochastic(Dn, floor=_P0["p_diesel"] / MJ_PER_LDEQ)
R["stoch"]["S54 sold at diesel parity"] = stochastic(Dn, ref="diesel"); R["stoch"]["S54 diesel parity + floor"] = stochastic(Dn, ref="diesel", floor=_P0["p_diesel"] / MJ_PER_LDEQ); P0 = _P0
print("stochastic", time.time() - t)
pickle.dump(R, open(ROOT + "/results/unc.pkl", "wb"))
for k, v in RISK.items(): print(k, {a: round(float(b), 3) for a, b in v.items()})
print(R["p_htl_beats_fame"], {k: (round(v["p_loss"], 3), round(v["median"] / 1e6, 1)) for k, v in R["stoch"].items()})
