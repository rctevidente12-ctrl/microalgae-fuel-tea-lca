"""Figures for uncertainty, risk, GSA, stochastic, Pareto and surrogate analyses."""
import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import sys, pickle, numpy as np
sys.path.insert(0, ROOT + "/src")
from figstyle import *
import matplotlib.patches as mpatches
import registry as REG
U = pickle.load(open(ROOT + "/results/unc.pkl", "rb")); CORE = pickle.load(open(ROOT + "/results/core.pkl", "rb"))
CME = CORE["cme_ldeq"]; DSL = REG.BASE["p_diesel"]; KEYS = U["keys"]; NAME = {r["key"]: r["name"].split(" (")[0] for r in REG.R}
from matplotlib.ticker import FixedLocator, NullLocator
def logticks(axis, vals):
    axis.set_major_locator(FixedLocator(vals)); axis.set_minor_locator(NullLocator()); axis.set_ticklabels([f"{v:g}" for v in vals])
des = list(U["mc"]); dc = {d: C[i] for i, d in enumerate(des)}
# ---------------- F26 MC distributions
fig, axs = plt.subplots(1, 2, figsize=(11, 4))
for ax, key, lab in ((axs[0], "mfsp_ldeq", "MFSP, USD/L diesel-eq. (log)"), (axs[1], "gwp", "GWP, g CO2e/MJ")):
    data = [U["mc"][d][key][np.isfinite(U["mc"][d][key])] for d in des]
    bp = ax.boxplot(data, vert=False, whis=(5, 95), showfliers=False, patch_artist=True, widths=0.55, medianprops=dict(color=INK))
    for p, d in zip(bp["boxes"], des): p.set_facecolor(dc[d]); p.set_alpha(0.75); p.set_edgecolor("white")
    ax.set_yticks(range(1, len(des) + 1)); ax.set_yticklabels(des if ax is axs[0] else [""] * len(des)); ax.set_xlabel(lab)
    if key == "mfsp_ldeq": ax.set_xscale("log"); logticks(ax.xaxis, [1, 1.5, 2, 3, 5, 10, 20, 30]); ax.axvline(CME, color=VIOLET, ls="--", lw=1); ax.axvline(DSL, color=INK2, ls=":", lw=1)
    else: ax.axvline(94, color=INK2, ls=":", lw=1); ax.axvline(32.9, color=VIOLET, ls="--", lw=1)
save(fig, "F26_mc_box", "Monte Carlo distributions (10,000 draws, common random numbers)", "Boxes: interquartile range and median; whiskers: 5th-95th percentiles. Every design is evaluated in the same 10,000 sampled worlds (Latin hypercube, Iman-Conover dependencies).",
     data=[dict(design=d, out=k, p5=float(np.nanpercentile(U["mc"][d][k], 5)), p25=float(np.nanpercentile(U["mc"][d][k], 25)), p50=float(np.nanpercentile(U["mc"][d][k], 50)), p75=float(np.nanpercentile(U["mc"][d][k], 75)), p95=float(np.nanpercentile(U["mc"][d][k], 95))) for d in des for k in ("mfsp_ldeq", "gwp", "npv")], section="Uncertainty")
# ---------------- F27 joint cost-climate cloud
fig, ax = plt.subplots(figsize=(7.5, 5))
for d in ("S01 HTL base", "S27 HTL biomass PPA", "S32 HTL clean utilities", "S50 HTL CES2 2040", "S54 HTL NZ 2050"):
    y = U["mc"][d]; ax.scatter(y["gwp"][:2500], y["mfsp_ldeq"][:2500], s=4, alpha=0.35, color=dc[d], label=d, rasterized=True)
ax.set_yscale("log"); logticks(ax.yaxis, [1, 1.5, 2, 3, 4, 6, 10]); ax.axhline(CME, color=VIOLET, ls="--", lw=1); ax.axvline(32.9, color=VIOLET, ls="--", lw=1); ax.axvline(94, color=INK2, ls=":", lw=1)
ax.set_xlabel("GWP, g CO2e/MJ"); ax.set_ylabel("MFSP, USD/L deq (log)"); ax.legend(markerscale=4)
save(fig, "F27_mc_joint", "Joint distribution of cost and climate outcomes", "2,500 of 10,000 draws per design. Only the 2050 net-zero pathway places most draws below both the CME price and the 65% saving line.", section="Uncertainty")
# ---------------- F28 risk metrics
RK = U["risk"]; mets = [("p_lt_cme", "P(MFSP\n< CME)"), ("p_npv_pos", "P(NPV > 0\nat CME)"), ("p_save50", "P(GHG saving\n>= 50%)"), ("p_save65", "P(GHG saving\n>= 65%)"), ("p_below_diesel", "P(GWP <\nfossil diesel)")]
fig, ax = plt.subplots(figsize=(10, 3.8)); w = 0.8 / len(des); x = np.arange(len(mets))
for i, d in enumerate(des): ax.bar(x + (i - len(des) / 2 + 0.5) * w, [RK[d][m] * 100 for m, _ in mets], w, color=dc[d], label=d, edgecolor="white", linewidth=1)
ax.set_xticks(x); ax.set_xticklabels([l for _, l in mets]); ax.set_ylabel("Probability, %"); ax.legend(ncol=3, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.12))
save(fig, "F28_risk_probabilities", "Risk metrics across designs", "Probabilities over 10,000 Monte Carlo draws.", data=[dict(design=d, **{k: float(v) for k, v in RK[d].items()}) for d in des], section="Risk")
# ---------------- F29 NPV CDF with VaR/CVaR
fig, ax = plt.subplots(figsize=(8, 3.8))
for d in des:
    v = np.sort(U["mc"][d]["npv"]) / 1e6; ax.plot(v, np.linspace(0, 1, len(v)), color=dc[d], label=d)
    ax.scatter([RK[d]["var5"] / 1e6], [0.05], color=dc[d], s=18, zorder=3)
ax.axvline(0, color=INK2, lw=1); ax.axhline(0.05, color=MUTED, ls=":", lw=1); ax.text(ax.get_xlim()[0], 0.07, " 5% (VaR level)", fontsize=7, color=INK2)
ax.set_xlabel("NPV at the CME price, USD million"); ax.set_ylabel("Cumulative probability"); ax.legend(fontsize=7)
save(fig, "F29_npv_cdf", "NPV distributions and value at risk", "Cumulative distributions of NPV (10%, 30 yr) with the 5% value at risk marked.", data=[dict(design=d, var5=RK[d]["var5"], cvar5=RK[d]["cvar5"], npv_p50=RK[d]["npv_p50"]) for d in des], section="Risk")
# ---------------- F30 Spearman heatmap
SP = U["spearman"]; top = np.argsort(-np.abs(SP["S01 HTL base"]["mfsp_ldeq"]) - np.abs(SP["S01 HTL base"]["gwp"]))[:18]
cols = [(d, o) for d in SP for o in ("mfsp_ldeq", "gwp", "npv")]
M = np.array([[SP[d][o][j] for d, o in cols] for j in top])
fig, ax = plt.subplots(figsize=(9, 6.2)); im = ax.imshow(M, cmap=DIV, vmin=-1, vmax=1, aspect="auto"); ax.grid(False)
ax.set_yticks(range(len(top))); ax.set_yticklabels([NAME[KEYS[j]][:42] for j in top], fontsize=7.2)
ax.set_xticks(range(len(cols))); ax.set_xticklabels([f"{d.split()[0]} {o.replace('_ldeq','').upper()}" for d, o in cols], rotation=40, ha="right", fontsize=7.2)
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        if abs(M[i, j]) >= 0.1: ax.text(j, i, f"{M[i,j]:.2f}", ha="center", va="center", fontsize=6.3)
fig.colorbar(im, ax=ax, shrink=0.7).set_label("Spearman rank correlation")
save(fig, "F30_spearman", "Rank correlation between inputs and outputs", "Spearman coefficients over 10,000 draws for the eighteen most influential inputs.",
     data=[dict(parameter=NAME[KEYS[j]], **{f"{d}|{o}": float(SP[d][o][j]) for d, o in cols}) for j in range(len(KEYS))], section="Correlation")
# ---------------- F31 PRCC
fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.6), sharey=True)
top = np.argsort(-(np.abs(U["prcc_htl_mfsp"]) + np.abs(U["prcc_htl_gwp"])))[:15][::-1]
axs[0].barh(range(len(top)), U["prcc_htl_mfsp"][top], color=[ORANGE if v > 0 else BLUE for v in U["prcc_htl_mfsp"][top]], height=0.6)
axs[1].barh(range(len(top)), U["prcc_htl_gwp"][top], color=[ORANGE if v > 0 else BLUE for v in U["prcc_htl_gwp"][top]], height=0.6)
axs[0].set_yticks(range(len(top))); axs[0].set_yticklabels([NAME[KEYS[j]][:40] for j in top], fontsize=7.2); axs[0].set_xlabel("PRCC with MFSP"); axs[1].set_xlabel("PRCC with GWP")
save(fig, "F31_prcc", "Partial rank correlation coefficients (HTL base)", "PRCC removes the linear effect of all other inputs (4,000 draws).",
     data=[dict(parameter=NAME[KEYS[j]], prcc_mfsp=float(U["prcc_htl_mfsp"][j]), prcc_gwp=float(U["prcc_htl_gwp"][j])) for j in range(len(KEYS))], section="Correlation")
# ---------------- F32 dependency effect: correlated vs independent
fig, axs = plt.subplots(1, 2, figsize=(10, 3.4))
for ax, key, lab in ((axs[0], "mfsp_ldeq", "MFSP, USD/L deq"), (axs[1], "npv", "NPV, USD M")):
    a = np.sort(U["mc"]["S01 HTL base"][key]); b = np.sort(U["mc_indep"]["S01 HTL base"][key]); sc = 1e6 if key == "npv" else 1
    ax.plot(a / sc, np.linspace(0, 1, len(a)), color=BLUE, label="with dependencies (Iman-Conover)"); ax.plot(b / sc, np.linspace(0, 1, len(b)), color=ORANGE, ls="--", label="independent inputs")
    ax.set_xlabel(lab); ax.set_ylabel("Cumulative probability")
axs[0].legend(fontsize=7)
save(fig, "F32_dependency", "Effect of input dependencies", "Sixteen rank correlations (fuel, chemical and utility prices; capital factors; lipid-nitrogen) widen the NPV distribution and leave the MFSP median almost unchanged.",
     data=[dict(pair=f"{a}-{b}", spearman=r) for a, b, r in U["corr"]], section="Correlation")
# ---------------- F33 Morris
fig, axs = plt.subplots(1, 2, figsize=(11, 4.4))
for ax, out, lab in ((axs[0], "mfsp_ldeq", "MFSP"), (axs[1], "gwp", "GWP")):
    for route, c in (("HTL", BLUE), ("FAME", ORANGE)):
        m = U["morris"][route][out]; ax.scatter(m["mu_star"], m["sigma"], s=14, color=c, alpha=0.8, label=route)
        if route == "HTL":
            for r_, j in enumerate(np.argsort(-m["mu_star"])[:4]): ax.annotate(NAME.get(KEYS[j], KEYS[j]), (m["mu_star"][j], m["sigma"][j]), fontsize=6.5, xytext=(-8, -12 - 11 * r_), textcoords="offset points", ha="right", color=BLUE, arrowprops=dict(arrowstyle="-", color=BLUE, lw=0.5))
    ax.set_xlabel(f"mu* ({lab})"); ax.set_ylabel("sigma"); ax.set_xscale("symlog", linthresh=1e-3); ax.set_yscale("symlog", linthresh=1e-3)
axs[0].legend()
save(fig, "F33_morris", "Morris elementary-effects screening", "All 119 ranged parameters, r = 20 trajectories per route (4 levels). High mu*: important; high sigma: non-linear or interacting.",
     data=[dict(route=r, parameter=KEYS[j], **{f"{o}_mu_star": float(U["morris"][r][o]["mu_star"][j]) for o in ("mfsp_ldeq", "gwp")}, **{f"{o}_sigma": float(U["morris"][r][o]["sigma"][j]) for o in ("mfsp_ldeq", "gwp")}) for r in ("HTL", "FAME") for j in range(len(KEYS))], section="GSA")
# ---------------- F34-35 Sobol
for route in ("HTL", "FAME"):
    s = U["sobol"][route]; k = len(s["keys"]); fig, axs = plt.subplots(1, 2, figsize=(11, 5.6), sharey=True)
    order = np.argsort(s["ST"][:, 0] + s["ST"][:, 1])[::-1][:20][::-1]
    for ax, o, lab in ((axs[0], 0, "MFSP"), (axs[1], 1, "GWP")):
        y = np.arange(len(order))
        ax.barh(y + 0.18, s["ST"][order, o], 0.34, xerr=s["STci"][order, o], color=ORANGE, label="total-order ST", error_kw=dict(lw=0.8, ecolor=INK2))
        ax.barh(y - 0.18, np.clip(s["S1"][order, o], 0, None), 0.34, xerr=s["S1ci"][order, o], color=BLUE, label="first-order S1", error_kw=dict(lw=0.8, ecolor=INK2))
        ax.set_xlabel(f"Sobol index, {lab}")
    axs[0].set_yticks(range(len(order))); axs[0].set_yticklabels([NAME[s["keys"][j]][:42] for j in order], fontsize=7.2); axs[0].legend(loc="lower right")
    save(fig, f"F{34 if route=='HTL' else 35}_sobol_{route.lower()}", f"Sobol global sensitivity indices ({route})", f"Saltelli sampling scheme; Saltelli (2010) first-order and Jansen total-order estimators, N = {s['n']} ({s['runs']:,} runs), 30 parameters screened by Morris; bars: 95% bootstrap intervals.",
         data=[dict(parameter=NAME[s["keys"][j]], S1_mfsp=float(s["S1"][j, 0]), ST_mfsp=float(s["ST"][j, 0]), S1_gwp=float(s["S1"][j, 1]), ST_gwp=float(s["ST"][j, 1])) for j in range(k)], section="GSA")
# ---------------- F36 stochastic
ST = U["stoch"]; fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
pr = ST["S01 HTL base"]["prices"]; yrs = np.arange(1, pr.shape[1] + 1)
for q, a in ((5, 0.15), (25, 0.3)):
    axs[0].fill_between(yrs, np.percentile(pr, q, 0), np.percentile(pr, 100 - q, 0), color=BLUE, alpha=a, lw=0)
axs[0].plot(yrs, np.median(pr, 0), color=BLUE); [axs[0].plot(yrs, pr[i], color=MUTED, lw=0.5, alpha=0.6) for i in range(5)]
axs[0].axhline(CME, color=VIOLET, ls="--", lw=1); axs[0].set_xlabel("Operating year"); axs[0].set_ylabel("Fuel price, USD/L deq")
for k_, c in zip(["S01 HTL base", "S01 no typhoons", "S54 HTL NZ 2050", "S54 sold at diesel parity", "S54 diesel parity + floor"], C):
    v = ST[k_]["npv"] / 1e6; axs[1].hist(v, bins=60, histtype="step", color=c, lw=1.6, label=f"{k_} (P loss {100*ST[k_]['p_loss']:.0f}%)")
axs[1].axvline(0, color=INK2, lw=1); axs[1].set_xlabel("NPV, USD million"); axs[1].set_ylabel("Paths"); axs[1].legend(fontsize=6.6)
save(fig, "F36_stochastic", "Stochastic cash flows: price paths and typhoons", "Left: 5,000 Ornstein-Uhlenbeck log-price paths around the CME benchmark (bands 5-95% and 25-75%). Right: NPV distributions with Poisson typhoons and interannual productivity noise.",
     data=[dict(case=k_, p_loss=float(v["p_loss"]), var5=float(v["var5"]), cvar5=float(v["cvar5"]), median=float(v["median"])) for k_, v in ST.items()], section="Risk")
print("unc figures done")
