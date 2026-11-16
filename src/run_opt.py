"""Multi-objective optimisation (NSGA-II, Deb et al. 2002) over design choices; objectives: MFSP, GWP, TCI."""
import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import sys, pickle, time, numpy as np
sys.path.insert(0, ROOT + "/src")
import registry as REG, scen as SC
from model import evaluate
rng = np.random.default_rng(42)
P0 = dict(REG.BASE)
# genes in [0,1): route, log-area, lined, aq, upgrade, heat, electricity, nutrients, co2, glycerol
VARS = ["route", "area", "lined", "aq", "upgrade", "heat", "elec", "nutr", "co2", "glyc"]
def decode(x):
    D = dict(route="HTL" if x[0] < 0.5 else "FAME", area_ha=float(10 ** (np.log10(50) + x[1] * (np.log10(3000) - np.log10(50)))),
             lined=bool(x[2] >= 0.8), aq=["recycle", "CHG", "AD"][min(int(x[3] * 3), 2)], upgrade="onsite" if x[4] < 0.5 else "refinery",
             heat="fossil" if x[5] < 0.5 else "biomass", nutr="fert" if x[7] < 0.5 else "ww", co2="flue" if x[8] < 0.8 else "liquid",
             glyc="crude" if x[9] < 0.5 else "refined", alloc="energy")
    D["elec"] = ["grid", "biomass_ppa", "solar_ppa"][min(int(x[6] * 3), 2)]
    return D
def objectives(x, P, pros=None):
    D = decode(x); Pp = dict(P)
    if pros: Pp, D = SC.prospective(Pp, D, *pros)
    o = evaluate(Pp, D)
    return np.array([o["mfsp_ldeq"], o["gwp"], o["tci"] / 1e6]), o
def nondominated_sort(F):
    n = len(F); S = [[] for _ in range(n)]; nd = np.zeros(n, int); fronts = [[]]; rank = np.zeros(n, int)
    for p in range(n):
        for q in range(n):
            if np.all(F[p] <= F[q]) and np.any(F[p] < F[q]): S[p].append(q)
            elif np.all(F[q] <= F[p]) and np.any(F[q] < F[p]): nd[p] += 1
        if nd[p] == 0: rank[p] = 0; fronts[0].append(p)
    i = 0
    while fronts[i]:
        nxt = []
        for p in fronts[i]:
            for q in S[p]:
                nd[q] -= 1
                if nd[q] == 0: rank[q] = i + 1; nxt.append(q)
        i += 1; fronts.append(nxt)
    return fronts[:-1], rank
def crowding(F, idx):
    d = np.zeros(len(idx)); f = F[idx]
    for m in range(F.shape[1]):
        o = np.argsort(f[:, m]); d[o[0]] = d[o[-1]] = np.inf; rngm = f[o[-1], m] - f[o[0], m] or 1.0
        for k in range(1, len(idx) - 1): d[o[k]] += (f[o[k + 1], m] - f[o[k - 1], m]) / rngm
    return d
def nsga2(P, pros=None, pop=100, gen=80, nobj=3):
    X = rng.random((pop, len(VARS))); F = np.array([objectives(x, P, pros)[0][:nobj] for x in X]); hist = [(X.copy(), F.copy())]
    for g in range(gen):
        fr, rank = nondominated_sort(F); cd = np.zeros(pop)
        for f_ in fr: cd[f_] = crowding(F, f_)
        def tour():
            a, b = rng.integers(0, pop, 2)
            return a if (rank[a] < rank[b] or (rank[a] == rank[b] and cd[a] > cd[b])) else b
        kids = []
        for _ in range(pop // 2):
            p1, p2 = X[tour()], X[tour()]
            if rng.random() < 0.9:  # SBX crossover (eta 15)
                u = rng.random(len(VARS)); beta = np.where(u <= 0.5, (2 * u) ** (1 / 16), (1 / (2 * (1 - u))) ** (1 / 16))
                c1 = 0.5 * ((1 + beta) * p1 + (1 - beta) * p2); c2 = 0.5 * ((1 - beta) * p1 + (1 + beta) * p2)
            else: c1, c2 = p1.copy(), p2.copy()
            for c in (c1, c2):  # Gaussian mutation (sigma 0.15, rate 1/n)
                m = rng.random(len(VARS)) < 1 / len(VARS); c[m] += rng.normal(0, 0.15, m.sum()); kids.append(np.clip(c, 0, 0.9999))
        Xk = np.array(kids); Fk = np.array([objectives(x, P, pros)[0][:nobj] for x in Xk])
        XX = np.vstack([X, Xk]); FF = np.vstack([F, Fk]); fr, _ = nondominated_sort(FF); sel = []
        for f_ in fr:
            if len(sel) + len(f_) <= pop: sel += f_
            else:
                c = crowding(FF, f_); sel += [f_[i] for i in np.argsort(-c)[:pop - len(sel)]]; break
        X, F = XX[sel], FF[sel]
        if g % 10 == 9: hist.append((X.copy(), F.copy()))
    fr, _ = nondominated_sort(F)
    front = fr[0]
    sols = []
    for i in front:
        D = decode(X[i]); f, o = objectives(X[i], P, pros)
        sols.append(dict(D=D, mfsp=f[0], gwp=f[1], tci=f[2], out=o["ldeq"], area=D["area_ha"], route=D["route"]))
    return dict(front=sols, hist=hist, X=X, F=F)
def hypervolume2d(pts, ref):
    p = sorted([q for q in pts if q[0] < ref[0] and q[1] < ref[1]]); hv = 0.0; prev = ref[1]
    for x, y in p:
        if y < prev: hv += (ref[0] - x) * (prev - y); prev = y
    return hv
if __name__ == "__main__":
    t = time.time(); R = {}
    R["2026"] = nsga2(P0); print("2026", time.time() - t, len(R["2026"]["front"]))
    R["2026_2obj"] = nsga2(P0, nobj=2); print("2obj", time.time() - t)
    R["2050_NZ"] = nsga2(P0, pros=("NZ", 2050)); print("2050", time.time() - t)
    R["2040_CES2"] = nsga2(P0, pros=("CES2", 2040)); print("2040", time.time() - t)
    # convergence: hypervolume of the MFSP-GWP projection per stored generation
    ref = (15.0, 250.0)
    R["hv"] = {k: [hypervolume2d([tuple(f[:2]) for f in F], ref) for _, F in R[k]["hist"]] for k in ("2026", "2026_2obj", "2050_NZ", "2040_CES2")}
    # random-sampling cloud for context
    cloud = []
    for _ in range(3000):
        x = rng.random(len(VARS)); f, o = objectives(x, P0); cloud.append((*f, x[0] < 0.5))
    R["cloud"] = np.array(cloud)
    pickle.dump(R, open(ROOT + "/results/opt.pkl", "wb"))
    for k in ("2026", "2026_2obj", "2050_NZ"):
        fr = sorted(R[k]["front"], key=lambda s: s["mfsp"])
        print(k, [(round(s["mfsp"], 2), round(s["gwp"], 1), round(s["tci"]), s["route"], round(s["area"]), s["D"]["heat"], s["D"]["elec"]) for s in fr[:3] + fr[-2:]])
