"""Pareto and surrogate figures."""
import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import sys, pickle, numpy as np
sys.path.insert(0, ROOT + "/src")
from figstyle import *
import registry as REG
O = pickle.load(open(ROOT + "/results/opt.pkl", "rb")); CORE = pickle.load(open(ROOT + "/results/core.pkl", "rb")); CME = CORE["cme_ldeq"]
# ---------------- F37 Pareto fronts
fig, ax = plt.subplots(figsize=(8.5, 5.2))
cl = O["cloud"]; ax.scatter(cl[:, 1], cl[:, 0], s=4, color="#c9c8c2", label="random designs (2026)", rasterized=True)
rows = []
for k, c, lab in (("2026", BLUE, "Pareto front 2026"), ("2040_CES2", AQUA, "Pareto front 2040 (CES2)"), ("2050_NZ", GREEN, "Pareto front 2050 (NZ)")):
    fr = sorted(O[k]["front"], key=lambda s: s["gwp"])
    nd = []; best = np.inf
    for s_ in fr:
        if s_["mfsp"] < best: nd.append(s_); best = s_["mfsp"]
    ax.plot([s_["gwp"] for s_ in nd], [s_["mfsp"] for s_ in nd], color=c, lw=1.6, drawstyle="steps-post", zorder=2)
    ax.scatter([s_["gwp"] for s_ in fr if s_ not in nd], [s_["mfsp"] for s_ in fr if s_ not in nd], s=12, facecolor="none", edgecolor=c, linewidth=0.8, zorder=2)
    sc = ax.scatter([s_["gwp"] for s_ in nd], [s_["mfsp"] for s_ in nd], c=[s_["tci"] for s_ in nd], cmap=SEQ, s=30, edgecolor=c, linewidth=1.0, label=lab, zorder=3, vmin=0, vmax=1300)
    rows += [dict(front=k, mfsp=s["mfsp"], gwp=s["gwp"], tci_musd=s["tci"], output_Ldeq=s["out"], route=s["route"], area_ha=s["area"], **{f"opt_{a}": v for a, v in s["D"].items() if a not in ("route", "area_ha", "alloc")}) for s in fr]
from matplotlib.ticker import FixedLocator, NullLocator
ax.set_yscale("log"); ax.set_xscale("log")
ax.yaxis.set_major_locator(FixedLocator([1, 1.5, 2, 3, 5, 10, 20, 40])); ax.yaxis.set_minor_locator(NullLocator()); ax.set_yticklabels(["1", "1.5", "2", "3", "5", "10", "20", "40"])
ax.xaxis.set_major_locator(FixedLocator([10, 20, 33, 50, 94, 200, 500])); ax.xaxis.set_minor_locator(NullLocator()); ax.set_xticklabels(["10", "20", "33", "50", "94", "200", "500"])
ax.axhline(CME, color=VIOLET, ls="--", lw=1); ax.axvline(32.9, color=VIOLET, ls="--", lw=1); ax.axvline(94, color=INK2, ls=":", lw=1)
ax.set_xlabel("GWP, g CO2e/MJ (log)"); ax.set_ylabel("MFSP, USD/L deq (log)"); fig.colorbar(sc, ax=ax).set_label("Total capital investment, USD M"); ax.legend(fontsize=7, loc="upper left")
save(fig, "F37_pareto", "Pareto fronts: cost, climate and capital", "Lines: designs non-dominated in cost and climate (filled, coloured by capital); open circles: designs on the three-objective front that trade capital. NSGA-II (population 100, 80 generations) over route, pond area (50-3,000 ha), liners, aqueous treatment, upgrading, heat, electricity, nutrients, CO2 source and glycerol; objectives MFSP, GWP and TCI.",
     data=rows, section="Optimisation")
# ---------------- F38 decision frequencies on the 2026 front
fr = O["2026"]["front"]; opts = [("route", ["HTL", "FAME"]), ("heat", ["fossil", "biomass"]), ("elec", ["grid", "biomass_ppa", "solar_ppa"]), ("aq", ["recycle", "CHG", "AD"]), ("upgrade", ["onsite", "refinery"]), ("nutr", ["fert", "ww"]), ("co2", ["flue", "liquid"]), ("lined", [False, True])]
fig, ax = plt.subplots(figsize=(9, 3.6)); y = 0; tick = []; data = []
for name, vals in opts:
    left = 0
    for j, v in enumerate(vals):
        f = np.mean([s["D"][name] == v for s in fr]); ax.barh(y, f, left=left, color=C[j], height=0.6, edgecolor="white", linewidth=1.5)
        if f > 0.06: ax.text(left + f / 2, y, f"{v} {f:.0%}", ha="center", va="center", fontsize=7, color="white" if j in (0, 5, 6) else INK)
        left += f; data.append(dict(decision=name, option=str(v), share=f))
    tick.append(name); y += 1
ax.set_yticks(range(len(tick))); ax.set_yticklabels(tick); ax.invert_yaxis(); ax.set_xlabel("Share of Pareto-optimal designs (2026)"); ax.set_xlim(0, 1)
save(fig, "F38_pareto_decisions", "Design choices on the 2026 Pareto front", "Share of non-dominated designs taking each option.", data=data, section="Optimisation")
# ---------------- F39 convergence
fig, ax = plt.subplots(figsize=(6, 3.2))
for k, c in zip(O["hv"], C):
    hv = O["hv"][k]; ax.plot(np.arange(len(hv)) * 10, np.array(hv) / max(hv), color=c, marker="o", ms=4, label=k)
ax.set_xlabel("Generation"); ax.set_ylabel("Hypervolume (normalised)"); ax.legend(fontsize=7)
save(fig, "F39_hypervolume", "NSGA-II convergence", "Hypervolume of the MFSP-GWP projection (reference point 15 USD/L, 250 g/MJ) at every tenth generation.", data=[dict(run=k, gen=i * 10, hv=float(v)) for k in O["hv"] for i, v in enumerate(O["hv"][k])], section="Optimisation")
# ---------------- ML figures
try:
    M = pickle.load(open(ROOT + "/results/ml.pkl", "rb"))
except Exception:
    M = None
if M:
    feats = [f[0] for f in M["feat"]]; labels = [f[3] for f in M["feat"]]
    # F40 model comparison
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.6))
    for ax, route in zip(axs, ("HTL", "FAME")):
        res = M[route]["res"]; names = list(res); x = np.arange(len(names)); w = 0.2
        for j, out in enumerate(M["outs"]):
            ax.bar(x + (j - 1.5) * w, [res[n]["metrics"][j]["r2"] for n in names], w, color=C[j], label=out)
        ax.set_xticks(x); ax.set_xticklabels(names, rotation=20, ha="right", fontsize=7.5); ax.set_ylim(0.85, 1.0); ax.set_ylabel("Hold-out R2"); ax.set_title(route, loc="left")
    axs[0].legend(fontsize=7, ncol=4, loc="upper center", bbox_to_anchor=(1.1, -0.3))
    save(fig, "F40_surrogate_models", "Surrogate model comparison", "Hold-out R2 (20% test set) for five learners and four outputs; Gaussian process trained on 1,500 points.",
         data=[dict(route=r, model=n, output=m["out"], r2=m["r2"], rmse=m["rmse"], mape=m["mape"], fit_s=M[r]["res"][n]["fit_s"], pred_s=M[r]["res"][n]["pred_s"]) for r in ("HTL", "FAME") for n in M[r]["res"] for m in M[r]["res"][n]["metrics"]], section="Surrogate")
    # F41 parity
    fig, axs = plt.subplots(2, 2, figsize=(9, 8.6)); fig.subplots_adjust(hspace=0.42, wspace=0.3)
    for i, route in enumerate(("HTL", "FAME")):
        p = M[route]["parity_mlp"]
        for j, (out, lab) in enumerate(((0, "MFSP, USD/L deq"), (1, "GWP, g CO2e/MJ"))):
            ax = axs[i, j]; t, q = p["true"][:, out], p["pred"][:, out]; ax.scatter(t, q, s=3, alpha=0.3, color=C[i], rasterized=True)
            lo, hi = np.nanmin(t), np.nanmax(t); ax.plot([lo, hi], [lo, hi], color=INK, lw=1)
            if out == 0: ax.set_xscale("log"); ax.set_yscale("log")
            mm = M[route]["res"]["Neural network (MLP 64-64)"]["metrics"][out]
            ax.set_title(f"{route}: {lab}", loc="left"); ax.set_xlabel("Engine"); ax.set_ylabel("Surrogate (MLP)"); note(ax, f"R2 {mm['r2']:.4f}; MAPE {100*mm['mape']:.2f}%")
    save(fig, "F41_parity", "Surrogate validation: parity plots", "Neural-network surrogate against the full engine on the hold-out set.", section="Surrogate")
    # F42 learning curves + extrapolation
    fig, axs = plt.subplots(1, 2, figsize=(12, 3.8)); fig.subplots_adjust(wspace=0.75); dat = []
    for route, ls in (("HTL", "-"), ("FAME", "--")):
        for j, (n, pts) in enumerate(M[route]["lc"].items()):
            axs[0].plot([a for a, _ in pts], [b for _, b in pts], ls=ls, marker="o", ms=3, color=C[j], label=f"{route} {n}"); dat += [dict(route=route, model=n, n=a, r2=b) for a, b in pts]
    axs[0].set_xscale("log"); axs[0].set_xlabel("Training samples"); axs[0].set_ylabel("Hold-out R2 (MFSP)"); axs[0].legend(fontsize=6.5); axs[0].set_ylim(0.8, 1.0)
    ex = [(r, n, v) for r in ("HTL", "FAME") for n, v in M[r]["extrap"].items()]
    axs[1].barh(range(len(ex)), [100 * v["mape"] for _, _, v in ex], color=[C[0] if r == "HTL" else C[1] for r, _, _ in ex], height=0.6)
    axs[1].set_yticks(range(len(ex))); axs[1].set_yticklabels([f"{r} {n}" for r, n, _ in ex], fontsize=7); axs[1].set_xlabel("Extrapolation MAPE, % (train <25, test >30 g/m2/d)")
    save(fig, "F42_learning_extrap", "Learning curves and extrapolation test", "Accuracy versus training-set size, and error when the surrogate is asked to extrapolate in productivity.",
         data=dat + [dict(route=r, model=n, extrap_r2=v["r2"], extrap_mape=v["mape"]) for r, n, v in ex], section="Surrogate")
    # F43 permutation importance vs Sobol rank
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.2), sharey=True); pi = M["HTL"]["perm"]
    o = np.argsort(pi["mfsp_ldeq"] + pi["gwp"]);
    axs[0].barh(range(len(o)), pi["mfsp_ldeq"][o], color=BLUE, height=0.6); axs[1].barh(range(len(o)), pi["gwp"][o], color=ORANGE, height=0.6)
    axs[0].set_yticks(range(len(o))); axs[0].set_yticklabels([labels[i] for i in o], fontsize=7.2); axs[0].set_xlabel("Permutation importance (MFSP)"); axs[1].set_xlabel("Permutation importance (GWP)")
    save(fig, "F43_permutation", "What the surrogate learned (HTL)", "Permutation importance of the 17 calculator inputs; ranks agree with the Sobol total-order indices of the engine.",
         data=[dict(feature=labels[i], perm_mfsp=float(pi["mfsp_ldeq"][i]), perm_gwp=float(pi["gwp"][i])) for i in range(len(labels))], section="Surrogate")
print("opt/ml figures done")
