"""Graphical abstract for the manuscript."""
import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import sys
sys.path.insert(0, ROOT + "/src")
from figstyle import *
from ctx import *
fig = plt.figure(figsize=(13, 5.0))
fig.text(0.01, 0.965, "Microalgae fuel from San Carlos flue gas, Negros Occidental: one process balance drives TEA and LCA (ecoinvent 3.12)", fontsize=11.5, weight="bold", color=INK, va="top")
fig.text(0.01, 0.915, "60 scenarios  |  10,000-draw Monte Carlo with rank correlations  |  Sobol' indices  |  stochastic cash flows  |  NSGA-II Pareto fronts  |  neural-network surrogate and web calculator", fontsize=8.6, color=INK2, va="top")
# (a) bridge
ax = fig.add_axes([0.05, 0.14, 0.26, 0.64])
br = BR; lab = ["Reported", "Original\nbasis", "Bottom-up\ncapital", "Grow\nbiomass", "HTL\nheat", "Hydro-\ntreating", "Nutrients\n+ CO2"]
vals = [b["mfsp"] for b in br]
ax.bar(range(len(vals)), vals, color=[MUTED, MUTED, RED, RED, RED, RED, ORANGE], width=0.65)
for i, v in enumerate(vals): ax.text(i, v + 0.1, f"{v:.2f}", ha="center", fontsize=7.5)
ax.axhline(CME, color=VIOLET, ls="--", lw=1.2); ax.text(-0.4, CME + 0.12, f"CME {CME:.2f}", color=VIOLET, fontsize=7.5)
ax.set_xticks(range(len(vals))); ax.set_xticklabels(lab, fontsize=6.6); ax.set_ylabel("MFSP, USD/L diesel-eq."); ax.set_title("(a) Correcting the inherited balance", loc="left", fontsize=9.5)
# (b) cost-climate
ax = fig.add_axes([0.38, 0.14, 0.27, 0.64])
pts = [("S01", "HTL base 2026", BLUE), ("S02", "FAME base 2026", ORANGE), ("S27", "HTL + biomass PPA", AQUA), ("S32", "HTL clean utilities", YELLOW), ("S50", "HTL CES2 2040", MAGENTA), ("S54", "HTL net zero 2050", GREEN), ("S56", "2,000 ha NZ 2050", VIOLET)]
for sid, nm, c in pts:
    ax.scatter(S[sid]["gwp"], S[sid]["mfsp_ldeq"], s=60, color=c, edgecolor="white", linewidth=1.5, zorder=3, label=nm)
ax.set_yscale("log"); ax.axhline(CME, color=VIOLET, ls="--", lw=1); ax.axvline(94, color=INK2, ls=":", lw=1); ax.axvline(32.9, color=GREEN, ls="--", lw=1)
ax.text(60, CME * 1.05, f"CME {CME:.2f}", fontsize=7, color=VIOLET); ax.text(95, 1.25, "fossil\n94", fontsize=7, color=INK2); ax.text(33.5, 1.25, "65%\nsaving", fontsize=7, color=GREEN)
from matplotlib.ticker import FixedLocator, NullLocator
ax.yaxis.set_major_locator(FixedLocator([1.5, 2, 3, 5, 10, 15])); ax.yaxis.set_minor_locator(NullLocator()); ax.set_yticklabels(["1.5", "2", "3", "5", "10", "15"])
ax.set_xlabel("GWP, g CO2e/MJ"); ax.set_ylabel("MFSP, USD/L deq (log)"); ax.legend(fontsize=6.4, loc="upper left", ncol=1, frameon=False); ax.set_title("(b) Cost and climate of key designs", loc="left", fontsize=9.5)
ax.set_ylim(1.1, 20)
# (c) prospective
ax = fig.add_axes([0.72, 0.14, 0.26, 0.64]); pc = {"REF": MUTED, "CES1": BLUE, "CES2": AQUA, "NZ": GREEN}
for path in ("REF", "CES1", "CES2", "NZ"):
    rows = PROS[("HTL", path)]; ax.plot([r["year"] for r in rows], [r["mfsp"] for r in rows], color=pc[path], label=path)
ax.axhline(CME, color=VIOLET, ls="--", lw=1); ax.text(2026.3, CME + 0.08, "CME", color=VIOLET, fontsize=7.5)
ax.axhline(DSL, color=INK2, ls=":", lw=1); ax.text(2026.3, DSL + 0.08, "diesel ex-tax", color=INK2, fontsize=7.5)
ax.set_xlabel("Year"); ax.set_ylabel("HTL MFSP, USD/L deq"); ax.legend(title="PEP pathway", fontsize=7, title_fontsize=7); ax.set_title("(c) Prospective cost to 2050", loc="left", fontsize=9.5)
save(fig, "GA_graphical_abstract", "Graphical abstract", "Bridge from the reported to the corrected cost, cost and climate of key designs, and prospective MFSP to 2050.", data=[dict(step=b["step"], mfsp=b["mfsp"]) for b in br], section="Manuscript")
print("ga done")
