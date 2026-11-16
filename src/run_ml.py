"""Machine-learning surrogates of the process-TEA-LCA engine, validation, and export for the web calculator."""
import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import sys, pickle, time, json, numpy as np
from scipy.stats import qmc
sys.path.insert(0, ROOT + "/src")
import registry as REG
from model import evaluate, BASE_HTL, BASE_FAME
from sklearn.model_selection import train_test_split, KFold
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_percentage_error
rng = np.random.default_rng(11)
P0 = dict(REG.BASE)
FEAT = [("prod", 8, 40, "Productivity, g/m2/d"), ("log_area", np.log10(50), np.log10(3000), "log10 pond area, ha"), ("htl_y", 0.30, 0.60, "HTL biocrude yield"),
        ("lipid", 0.12, 0.35, "Lipid content"), ("ef_el", 0.0, 1.35, "Electricity GWP, kg/kWh"), ("p_el", 0.10, 0.30, "Electricity price, USD/kWh"),
        ("p_h2", 1.5, 7.0, "Hydrogen price, USD/kg"), ("p_heat", 5.0, 45.0, "Heat price, USD/GJ"), ("loc_f", 0.8, 1.4, "Location factor"),
        ("cap_mult", 0.6, 1.6, "Capital multiplier"), ("r", 0.04, 0.15, "Discount rate"), ("life", 15, 30, "Plant life, yr"),
        ("p_urea", 300, 700, "Urea price, USD/t"), ("mix_kwh", 20, 100, "Mixing energy, kWh/ha/d"), ("heat_bio", 0, 1, "Biomass heat (0/1)"),
        ("lined", 0, 1, "Lined ponds (0/1)"), ("ith", 0, 1, "Income tax holiday (0/1)")]
NAMES = [f[0] for f in FEAT]; LO = np.array([f[1] for f in FEAT]); HI = np.array([f[2] for f in FEAT])
BIN = {"heat_bio", "lined", "ith"}
OUTS = ["mfsp_ldeq", "gwp", "tci", "ldeq"]
def to_PD(x, route):
    v = dict(zip(NAMES, x)); P = dict(P0); D = dict(BASE_HTL if route == "HTL" else BASE_FAME)
    for k in ("prod", "htl_y", "lipid", "p_el", "p_h2", "p_heat", "loc_f", "r", "p_urea", "mix_kwh"): P[k] = float(v[k])
    P["life"] = int(round(v["life"])); P["p_heat_bio"] = P0["p_heat_bio"]
    P["tci_farm"] = P0["tci_farm"] * v["cap_mult"]; P["tci_conv"] = P0["tci_conv"] * v["cap_mult"]
    D["area_ha"] = float(10 ** v["log_area"]); D["ef_el"] = float(v["ef_el"]); D["scale_el_all"] = True
    D["heat"] = "biomass" if v["heat_bio"] > 0.5 else "fossil"; D["lined"] = v["lined"] > 0.5; D["ith"] = v["ith"] > 0.5
    return P, D
def gen(n, route, lo=LO, hi=HI):
    U = qmc.LatinHypercube(d=len(FEAT), seed=rng).random(n); X = lo + U * (hi - lo)
    for j, nm in enumerate(NAMES):
        if nm in BIN: X[:, j] = (U[:, j] > (0.5 if nm != "lined" else 0.8)).astype(float)
        if nm == "life": X[:, j] = np.round(X[:, j])
    Y = np.zeros((n, len(OUTS)))
    for i, x in enumerate(X):
        o = evaluate(*to_PD(x, route)); Y[i] = [o[k] for k in OUTS]
    return X, Y
def tf(Y):  # log for strictly positive, wide-range outputs
    Z = Y.copy(); Z[:, 0] = np.log(Y[:, 0]); Z[:, 2] = np.log(Y[:, 2]); Z[:, 3] = np.log(Y[:, 3]); return Z
def itf(Z):
    Y = Z.copy(); Y[:, 0] = np.exp(Z[:, 0]); Y[:, 2] = np.exp(Z[:, 2]); Y[:, 3] = np.exp(Z[:, 3]); return Y
def models():
    return {"Quadratic ridge": lambda: make_pipeline(StandardScaler(), PolynomialFeatures(2), RidgeCV(alphas=np.logspace(-6, 2, 20))),
            "Random forest": lambda: RandomForestRegressor(n_estimators=150, min_samples_leaf=2, n_jobs=-1, random_state=0),
            "Gradient boosting": lambda: HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06, max_leaf_nodes=31, random_state=0),
            "Neural network (MLP 64-64)": lambda: make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(64, 64), activation="relu", alpha=1e-4, learning_rate_init=2e-3, max_iter=1500, early_stopping=True, n_iter_no_change=40, random_state=0)),
            "Gaussian process": lambda: make_pipeline(StandardScaler(), GaussianProcessRegressor(ConstantKernel() * RBF(np.ones(len(FEAT))) + WhiteKernel(1e-4), normalize_y=True, random_state=0))}
def metrics(Ytrue, Ypred):
    return [dict(out=o, r2=r2_score(Ytrue[:, j], Ypred[:, j]), rmse=mean_squared_error(Ytrue[:, j], Ypred[:, j]) ** 0.5,
                 mape=mean_absolute_percentage_error(Ytrue[:, j], Ypred[:, j])) for j, o in enumerate(OUTS)]
if __name__ == "__main__":
    t = time.time(); R = {"feat": FEAT, "outs": OUTS}
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
    for route in ("HTL", "FAME"):
        X, Y = gen(N, route); print(route, "data", time.time() - t)
        ok = np.all(np.isfinite(Y), axis=1) & (Y[:, 0] > 0); X, Y = X[ok], Y[ok]
        Xtr, Xte, Ytr, Yte = train_test_split(X, Y, test_size=0.2, random_state=1)
        res = {}; fitted = {}
        for name, mk in models().items():
            ntr = 1500 if name == "Gaussian process" else len(Xtr)
            t0 = time.time(); ms = [mk().fit(Xtr[:ntr], tf(Ytr[:ntr])[:, j]) for j in range(len(OUTS))]; tfit = time.time() - t0
            t0 = time.time(); Zp = np.column_stack([m.predict(Xte) for m in ms]); tpred = (time.time() - t0) / len(Xte)
            res[name] = dict(metrics=metrics(Yte, itf(Zp)), fit_s=tfit, pred_s=tpred, ntrain=ntr); fitted[name] = ms
            print(route, name, [round(m["r2"], 4) for m in res[name]["metrics"]], round(tfit, 1), "s")
        best = max((n for n in res if n != "Gaussian process"), key=lambda n: res[n]["metrics"][0]["r2"] + res[n]["metrics"][1]["r2"])
        # engine speed for comparison
        t0 = time.time(); [evaluate(*to_PD(x, route)) for x in Xte[:300]]; t_engine = (time.time() - t0) / 300
        # 5-fold CV of the MLP and the best model on MFSP and GWP
        cv = {}
        for name in {best, "Neural network (MLP 64-64)"}:
            sc = []
            for tr, te in KFold(5, shuffle=True, random_state=3).split(X):
                ms = [models()[name]().fit(X[tr], tf(Y[tr])[:, j]) for j in (0, 1)]
                Zp = np.column_stack([ms[0].predict(X[te]), ms[1].predict(X[te])])
                sc.append((r2_score(Y[te, 0], np.exp(Zp[:, 0])), r2_score(Y[te, 1], Zp[:, 1])))
            cv[name] = np.array(sc)
        # learning curve (MLP and GB)
        lc = {}
        for name in ("Neural network (MLP 64-64)", "Gradient boosting"):
            pts = []
            for n in (250, 500, 1000, 2000, 4000, 8000, len(Xtr)):
                m = models()[name]().fit(Xtr[:n], tf(Ytr[:n])[:, 0]); pts.append((n, r2_score(Yte[:, 0], np.exp(m.predict(Xte)))))
            lc[name] = pts
        # extrapolation test: train on productivity < 25, test on > 30
        j = NAMES.index("prod"); tr = X[:, j] < 25; te = X[:, j] > 30; ex = {}
        for name in ("Neural network (MLP 64-64)", "Gradient boosting", "Quadratic ridge"):
            m = models()[name]().fit(X[tr], tf(Y[tr])[:, 0]); ex[name] = dict(r2=r2_score(Y[te, 0], np.exp(m.predict(X[te]))), mape=mean_absolute_percentage_error(Y[te, 0], np.exp(m.predict(X[te]))))
        # permutation importance (MLP) for MFSP and GWP
        mlp = fitted["Neural network (MLP 64-64)"]
        pi = {OUTS[k]: permutation_importance(mlp[k], Xte[:3000], tf(Yte[:3000])[:, k], n_repeats=5, random_state=0).importances_mean for k in (0, 1)}
        # parity data
        Zp = np.column_stack([m.predict(Xte) for m in mlp]); par = dict(true=Yte, pred=itf(Zp))
        Zb = np.column_stack([m.predict(Xte) for m in fitted[best]]); parb = dict(true=Yte, pred=itf(Zb))
        R[route] = dict(res=res, best=best, cv=cv, lc=lc, extrap=ex, perm=pi, parity_mlp=par, parity_best=parb, t_engine=t_engine, n=len(X))
        # export MLP weights for the web calculator
        exp = []
        for k, m in enumerate(mlp):
            sc, net = m.named_steps["standardscaler"], m.named_steps["mlpregressor"]
            exp.append(dict(out=OUTS[k], mean=sc.mean_.tolist(), scale=sc.scale_.tolist(), W=[w.tolist() for w in net.coefs_], b=[b.tolist() for b in net.intercepts_], log=OUTS[k] in ("mfsp_ldeq", "tci", "ldeq")))
        R[route]["export"] = exp
    # analytic output coefficient: output is linear in productivity x area x conversion yield (Eq. 1, 2, 8/10, 13)
    oc = {}
    for route, ykey in (("HTL", "htl_y"), ("FAME", "lipid")):
        x0 = np.array([(P0[n] if n in P0 else 0.0) for n in NAMES], float); x0[NAMES.index("log_area")] = np.log10(400.0); x0[NAMES.index("cap_mult")] = 1.0
        x0[NAMES.index("ef_el")] = P0["ef_grid"]; x0[NAMES.index("ith")] = 1.0; x0[NAMES.index("heat_bio")] = 0.0; x0[NAMES.index("lined")] = 0.0
        o = evaluate(*to_PD(x0, route)); oc[route] = o["ldeq"] / (P0["prod"] * 400.0 * P0[ykey])
        chk = []
        for _ in range(200):
            x = LO + rng.random(len(LO)) * (HI - LO); x[NAMES.index("heat_bio")] = 0; x[NAMES.index("lined")] = 0; x[NAMES.index("ith")] = 1; x[NAMES.index("life")] = round(x[NAMES.index("life")])
            o = evaluate(*to_PD(x, route)); a = oc[route] * x[NAMES.index("prod")] * 10 ** x[NAMES.index("log_area")] * x[NAMES.index(ykey)]
            chk.append(abs(a / o["ldeq"] - 1))
        print(route, "analytic output max rel. error", max(chk)); R[route]["out_exact_maxerr"] = max(chk)
    R["out_coef"] = oc
    json.dump({"out_coef": oc, "feat": [dict(name=f[0], lo=float(f[1]), hi=float(f[2]), label=f[3]) for f in FEAT], "HTL": R["HTL"]["export"], "FAME": R["FAME"]["export"],
               "metrics": {r: {o["out"]: o for o in R[r]["res"]["Neural network (MLP 64-64)"]["metrics"]} for r in ("HTL", "FAME")}},
              open(ROOT + "/results/surrogate.json", "w"))
    pickle.dump(R, open(ROOT + "/results/ml.pkl", "wb"))
    print("done", time.time() - t)
