"""Figures from the deterministic analyses (core.pkl)."""
import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import sys, pickle, numpy as np
sys.path.insert(0, ROOT + "/src")
from figstyle import *
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import registry as REG
R = pickle.load(open(ROOT + "/results/core.pkl", "rb"))
B = R["base"]; H, F = B["HTL"], B["FAME"]; CME = R["cme_ldeq"]; DSL = REG.BASE["p_diesel"]
# ---------------------------------------------------------------- F01 flowsheet
def box(ax, x, y, w, h, t, c, tc=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=c, ec="none")); ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=7.6, color=tc, wrap=True)
def arrow(ax, x1, y1, x2, y2, c=INK2):
    ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color=c, lw=1.2, shrinkA=2, shrinkB=2))
# ---------------------------------------------------------------- F02 productivity reality check
fig, ax = plt.subplots(figsize=(8, 3.6))
vals = [("Original design: 80 t/d on 10.36 ha (96 ponds)", 772, RED), ("Original design: on layout pond area (3.98 ha)", 2008, RED), ("UPLB 1,000 L pilot (Matanguihan et al., 2020)", 63.2, MUTED),
        ("PNNL/NREL design target (Davis et al., 2016)", 25, BLUE), ("Hawaii hybrid PBR + pond, best case (Huntley et al., 2015)", 20.5, BLUE), ("Lundquist et al. (2010)", 20, BLUE),
        ("NREL measured SOT 2023 (Klein et al., 2024)", 16.7, BLUE), ("Korea, 675 m2 raceways (Jo et al., 2020)", 9.9, BLUE), ("This study, base (range 10-30)", 20, ORANGE)]
y = np.arange(len(vals))[::-1]
ax.barh(y, [v[1] for v in vals], color=[v[2] for v in vals], height=0.55); ax.set_xscale("log"); ax.set_yticks(y); ax.set_yticklabels([v[0] for v in vals])
for yi, v in zip(y, vals): ax.text(v[1] * 1.08, yi, f"{v[1]:,.0f}" if v[1] >= 30 else f"{v[1]:.1f}", va="center", fontsize=7.5, color=INK)
ax.axvspan(10, 30, color=BLUE, alpha=0.07); ax.set_xlabel("Annual areal productivity, g AFDW m$^{-2}$ d$^{-1}$ (log scale)"); ax.set_xlim(5, 5000)
save(fig, "F02_productivity_check", "Implied versus published raceway productivity", "The original design requires 772-2,008 g/m2/d. Measured outdoor productivities lie between about 9 and 21 g/m2/d (the 20.5 is a best case from a hybrid photobioreactor-pond system), with design targets of 25; the shaded band is the 10-30 range used in this study. The 63.2 g/m2/d of the UPLB 1,000 L pilot is a short-batch value and is not used as a design basis.",
     data=[dict(source=v[0], g_m2_d=v[1]) for v in vals], section="Verification")
# ---------------------------------------------------------------- F03 verification: inherited / recomputed
V = R["verify"]
Q = [(2, "Implied productivity (772 vs 20 g/m2/d)", 772 / 20), (3, "Biodiesel per hectare (8,712 vs 141 t/yr)", 8712 / 141), (11, "Belt-press power (773 vs 29 kW)", 773.33 / 29),
     (8, "Carbon in HTL aqueous phase (121 vs 41.1 t/d)", 121.063 / 41.1), (17, "Total project cost, highest vs lowest version", 1047.99 / 468.53), (4, "HTL TG+DG out vs lipid in", 30.5617 / 17.6),
     (21, "Biodiesel revenue, two versions", 801.06 / 614.81), (13, "Methanol make-up (120 vs 100-130 kg/t)", 120 / 115), (12, "Transesterification yield (29.07 vs 29.03 t/d)", 29.0706 / 29.03),
     (9, "HTL mass closure (out 581 vs in 613 t/d)", 581.214 / 613.333), (7, "HTL slurry pumping (138 vs 184 kW)", 138.16 / 184), (16, "Paddlewheel power (9.7 vs 20.7 kW)", 9.737 / 20.7),
     (14, "Nitrogen supplied vs needed (34 vs 5,200 kg/d)", 33.59 / 5200), (15, "CO2 supplied vs needed (656 vs 146,400 kg/d)", 656.45 / 146400), (6, "HTL heat duty (0 vs 7.5 MW)", 1e-3)]
verd = {c["no"]: c["verdict"] for c in V}
fig, axs = plt.subplots(1, 2, figsize=(11, 5.2), gridspec_kw=dict(width_ratios=[3, 1.2]))
ax = axs[0]; y = np.arange(len(Q))[::-1]
ax.axvline(1, color=INK2, lw=0.8)
for yi, (no, lab, r) in zip(y, Q):
    col = GREEN if verd[no] == "Pass" else RED
    ax.plot([1, r], [yi, yi], color=col, lw=1.2, alpha=0.6); ax.scatter([r], [yi], color=col, s=36, zorder=3)
    if no == 6: ax.text(r * 1.6, yi + 0.32, "0 kW reported", va="center", ha="left", fontsize=7.2, color=INK)
    else: ax.text(r * (1.25 if r >= 1 else 0.8), yi, f"{r:.3g}x", va="center", ha="left" if r >= 1 else "right", fontsize=7.2, color=INK)
ax.set_xscale("log"); ax.set_xlim(3e-4, 400); ax.set_yticks(y); ax.set_yticklabels([f"#{q[0]} {q[1]}" for q in Q], fontsize=7.4)
ax.set_xlabel("Inherited value / recomputed or required value (log scale; 1 = agreement)")
ax2 = axs[1]; sev = ["High", "Medium", "Low"]
for i, s_ in enumerate(sev):
    nf = sum(1 for c in V if c["severity"] == s_ and c["verdict"] == "Fail"); npass = sum(1 for c in V if c["severity"] == s_ and c["verdict"] == "Pass")
    ax2.barh(i, nf, color=RED, height=0.55); ax2.barh(i, npass, left=nf, color=GREEN, height=0.55)
    ax2.text(nf + npass + 0.2, i, f"{nf} fail, {npass} pass", va="center", fontsize=7.5)
ax2.set_yticks(range(3)); ax2.set_yticklabels(sev); ax2.invert_yaxis(); ax2.set_xlim(0, 16); ax2.set_xlabel("Number of checks by severity")
save(fig, "F03_verification", "Verification of the inherited design", f"Left: ratio of the inherited value to the value recomputed from first principles, the workbooks or the literature, for the 15 quantitative checks (red: fail; green: pass; verdicts use quantity-specific tolerances, e.g. 5% for mass closure and 30% for equipment power). The HTL heat duty, reported as zero, is plotted at 0.001. Right: all {len(V)} checks by severity; {sum(c['verdict']=='Pass' for c in V)} pass. Details in database sheet 04_Verification.",
     data=[dict(no=no, check=lab, ratio=r, verdict=verd[no]) for no, lab, r in Q], section="Verification")
# ---------------------------------------------------------------- F04 bridge waterfall
br = R["bridge"]; fig, ax = plt.subplots(figsize=(9, 4.2))
labels = ["As reported\n(2026 WP)", "Original basis\non this engine", "+ bottom-up\ncapital", "+ grow the\nbiomass", "+ HTL heat\nduty", "+ hydro-\ntreating", "+ N, P, CO2\nsupplied"]
vals = [b["mfsp"] for b in br]
for i, v in enumerate(vals):
    if i in (0, 1) or i == len(vals) - 1: ax.bar(i, v, color=BLUE if i < len(vals) - 1 else ORANGE, width=0.6)
    else:
        d = v - vals[i - 1]; ax.bar(i, d, bottom=vals[i - 1], color=RED if d > 0 else GREEN, width=0.6)
    ax.text(i, v + 0.08, f"{v:.2f}", ha="center", fontsize=8)
ax.axhline(CME, color=VIOLET, lw=1.2, ls="--"); ax.text(6.45, CME + 0.06, f"CME 2026 (energy basis): {CME:.2f}", color=VIOLET, fontsize=7.5, ha="right")
ax.axhline(DSL, color=INK2, lw=1.2, ls=":"); ax.text(6.45, DSL + 0.06, f"Diesel ex-tax: {DSL:.2f}", color=INK2, fontsize=7.5, ha="right")
ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, fontsize=7.5); ax.set_ylabel("Minimum fuel selling price, USD per litre diesel-eq.")
save(fig, "F04_bridge", "Bridge from the reported cost to the corrected design", "Each bar adds one correction to the bar on its left (HTL route, 24,000 t/yr AFDW entering conversion; 390 ha in the corrected steps). The bottom-up capital and growing the biomass explain most of the gap.",
     data=[dict(step=b["step"], mfsp_usd_ldeq=b["mfsp"], gwp_g_mj=b.get("gwp"), pond_ha=b["area"], tci_usd=b["tci"]) for b in br], section="Verification")
# ---------------------------------------------------------------- F05 energy balance
fig, axs = plt.subplots(1, 2, figsize=(9.5, 3.6))
for ax, o, nm in ((axs[0], H, "HTL"), (axs[1], F, "FAME")):
    el = {k: v / 1e6 for k, v in o["el"].items() if v > 0}; ks = list(el)
    ax.barh(range(len(ks)), [el[k] for k in ks], color=BLUE, height=0.55); ax.set_yticks(range(len(ks))); ax.set_yticklabels([k.replace("_", " ") for k in ks])
    for i, k in enumerate(ks): ax.text(el[k] + 0.1, i, f"{el[k]:.2f}", va="center", fontsize=7.5)
    ax.set_title(f"{nm}: electricity demand {o['el_dem']/1e6:.1f} GWh/yr", loc="left"); ax.set_xlabel("GWh/yr")
    note(ax, f"CHP generation {o['chp_el']/1e6:.1f} GWh; heat net {o['heat_net']/1e6:.1f} TJ")
save(fig, "F05_energy_balance", "Annual electricity balance by use", "Paddlewheel mixing and dewatering dominate. In the FAME route anaerobic-digestion CHP covers the plant and exports a surplus.",
     data=[dict(route=nm, use=k, GWh=v / 1e6) for nm, o in (("HTL", H), ("FAME", F)) for k, v in o["el"].items()], section="Process")
# ---------------------------------------------------------------- F06 mass & nutrient balance (HTL)
fig, ax = plt.subplots(figsize=(9, 3.4))
items = [("Biomass grown (AFDW)", H["grown"]), ("Harvested AFDW", H["afdw"]), ("Biocrude", H["biocrude"]), ("Renewable diesel", H["prod"]["rd"]), ("Naphtha", H["prod"]["naph"]),
         ("CO2 delivered", H["co2_need"]), ("N demand", H["N_need"]), ("Urea bought", H["urea"]), ("DAP bought", H["dap"]), ("H2", H["h2"])]
ax.bar(range(len(items)), [v for _, v in items], color=[GREEN] * 5 + [BLUE] * 4 + [ORANGE], width=0.6); ax.set_yscale("log")
ax.set_xticks(range(len(items))); ax.set_xticklabels([k for k, _ in items], rotation=30, ha="right", fontsize=7.5); ax.set_ylabel("t/yr (log)")
for i, (_, v) in enumerate(items): ax.text(i, v * 1.1, f"{v:,.0f}", ha="center", fontsize=7)
save(fig, "F06_mass_balance", "Annual mass balance, HTL base design", "Main flows of the corrected HTL design (400 ha). CO2 delivered exceeds biomass by the 1.83 kg/kg fixation ratio divided by 66% utilisation.",
     data=[dict(flow=k, t_per_yr=v) for k, v in items], section="Process")
# ---------------------------------------------------------------- F07 capital
fig, ax = plt.subplots(figsize=(8, 3.8))
keys = sorted(set(H["capf"]) | set(H["capi"]) | set(F["capf"]) | set(F["capi"]))
cols = {k: C[i % 8] for i, k in enumerate(keys)}
for j, (o, nm) in enumerate(((H, "HTL"), (F, "FAME"))):
    left = 0
    for k in keys:
        v = (o["capf"].get(k, 0) * REG.BASE["tci_farm"] + o["capi"].get(k, 0) * REG.BASE["tci_conv"]) / 1e6
        if v > 0: ax.barh(j, v, left=left, color=cols[k], height=0.5, edgecolor="white", linewidth=2, label=k if j == 0 or k not in H["capi"] and k not in H["capf"] else None); left += v
    ax.text(left + 2, j, f"TCI {o['tci']/1e6:.0f} M", va="center", fontsize=8)
ax.set_yticks([0, 1]); ax.set_yticklabels(["HTL", "FAME"]); ax.set_xlabel("Fixed capital (installed x TCI factor), USD million 2025"); ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.2))
save(fig, "F07_capital", "Capital investment by area", "Bottom-up capital (NREL farm and PNNL/NREL conversion areas scaled with exponents, CEPCI 2025 = 813, location factor 1.12). The farm is 78% (HTL) and 84% (FAME) of fixed capital.",
     data=[dict(route=nm, area=k, installed_usd=o["capf"].get(k, o["capi"].get(k, 0))) for o, nm in ((H, "HTL"), (F, "FAME")) for k in list(o["capf"]) + list(o["capi"])], section="TEA")
# ---------------------------------------------------------------- F08 operating cost
fig, ax = plt.subplots(figsize=(8, 3.8)); ks = [k for k in H["cost"] if H["cost"][k] > 0 or F["cost"][k] > 0]
x = np.arange(len(ks)); ax.bar(x - 0.2, [H["cost"][k] / 1e6 for k in ks], 0.38, color=BLUE, label="HTL"); ax.bar(x + 0.2, [F["cost"][k] / 1e6 for k in ks], 0.38, color=ORANGE, label="FAME")
ax.set_xticks(x); ax.set_xticklabels(ks, rotation=35, ha="right", fontsize=7.5); ax.set_ylabel("USD million/yr"); ax.legend()
save(fig, "F08_opex", "Annual operating cost by item", "Fixed charges on capital (maintenance, insurance and local tax) exceed any single input; electricity, nutrients and hydrogen lead the variable costs.",
     data=[dict(item=k, HTL=H["cost"][k], FAME=F["cost"][k]) for k in ks], section="TEA")
# ---------------------------------------------------------------- F09 cash flow
fig, ax = plt.subplots(figsize=(8, 3.4))
for o, nm, c in ((H, "HTL", BLUE), (F, "FAME", ORANGE)):
    disc = o["cf"] / (1 + REG.BASE["r"]) ** o["cf_years"]; ax.plot(o["cf_years"], np.cumsum(disc) / 1e6, color=c, label=f"{nm} at CME price")
ax.axhline(0, color=MUTED, lw=1); ax.set_xlabel("Year"); ax.set_ylabel("Cumulative discounted cash flow, USD M"); ax.legend()
save(fig, "F09_cashflow", "Cumulative discounted cash flow", "Real, unlevered cash flows at 10% when fuel is sold at the 2026 CME price (USD 2.22/L FAME). Neither base design recovers its investment.",
     data=[dict(route=nm, year=int(y), cf_usd=float(c)) for o, nm in ((H, "HTL"), (F, "FAME")) for y, c in zip(o["cf_years"], o["cf"])], section="TEA")
# ---------------------------------------------------------------- F10 MFSP benchmark
fig, ax = plt.subplots(figsize=(8, 3.6))
bars = [("Fossil diesel, ex-tax (Oct 2026)", DSL, MUTED), ("Fossil diesel, ex-tax (Feb 2026, pre-war)", 0.73, MUTED), ("Coconut methyl ester (Aug 2026)", CME, VIOLET),
        ("HTL base (this study)", H["mfsp_ldeq"], BLUE), ("HTL, 2,000 ha", R["scen"]["S15"]["mfsp_ldeq"], BLUE), ("HTL, NZ pathway 2050", R["scen"]["S54"]["mfsp_ldeq"], AQUA),
        ("FAME base (this study)", F["mfsp_ldeq"], ORANGE), ("Original design (as reported)", R["bridge"][0]["mfsp"], RED)]
y = np.arange(len(bars))[::-1]; ax.barh(y, [b[1] for b in bars], color=[b[2] for b in bars], height=0.55)
for yi, b in zip(y, bars): ax.text(b[1] + 0.1, yi, f"{b[1]:.2f}", va="center", fontsize=7.5)
ax.set_yticks(y); ax.set_yticklabels([b[0] for b in bars]); ax.set_xlabel("USD per litre diesel-equivalent (35.9 MJ)")
save(fig, "F10_mfsp_benchmark", "Minimum fuel selling price against market benchmarks", "MFSP at a 10% real discount rate, 30-year life, Philippine 2026 prices.", data=[dict(item=b[0], usd_ldeq=b[1]) for b in bars], section="TEA")
# ---------------------------------------------------------------- F11 GWP contributions
cases = [("S01 HTL, Visayas grid", R["scen"]["S01"]), ("S27 HTL, biomass PPA", R["scen"]["S27"]), ("S32 HTL, clean utilities", R["scen"]["S32"]), ("S02 FAME base", R["scen"]["S02"]),
         ("S54 HTL, NZ 2050", R["scen"]["S54"])]
groups = ["Electricity", "Hydrogen", "Nutrients", "Heat", "Pond N2O", "AD methane slip", "Infrastructure", "Logistics", "Chemicals", "Combustion CH4/N2O"]
fig, ax = plt.subplots(figsize=(9, 3.9))
for i, (nm, o) in enumerate(cases):
    left = 0
    for j, g in enumerate(groups):
        v = o["contrib"].get(g, 0.0)
        if v > 0: ax.barh(i, v, left=left, color=C[j % 8] if j < 8 else (MUTED if j == 8 else "#b5b4ae"), height=0.55, edgecolor="white", linewidth=1.5, label=g); left += v
    ax.text(left + 1, i, f"{o['gwp']:.1f}", va="center", fontsize=8)
ax.axvline(94, color=INK2, ls=":", lw=1.2); ax.text(94, 4.55, "fossil diesel 94", fontsize=7.5, color=INK2, ha="center")
ax.axvline(32.9, color=VIOLET, ls="--", lw=1.2); ax.text(32.9, 4.55, "65% saving", fontsize=7.5, color=VIOLET, ha="center")
ax.set_yticks(range(len(cases))); ax.set_yticklabels([c[0] for c in cases]); ax.invert_yaxis(); ax.set_xlabel("g CO2e per MJ fuel (IPCC 2021 GWP100)")
h, l = ax.get_legend_handles_labels(); u = dict(zip(l, h)); ax.legend(list(u.values()), list(u.keys()), ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.2))
save(fig, "F11_gwp_contrib", "Climate-change contributions", "Grid electricity is half the HTL footprint on the Visayas grid; with a biomass PPA, nutrients and hydrogen dominate.",
     data=[dict(case=nm, group=g, g_mj=o["contrib"].get(g, 0.0)) for nm, o in cases for g in groups], section="LCA")
# ---------------------------------------------------------------- F12 multi-indicator heatmap (EF 3.0 adapted)
import ei
efc = [(k, c[1]) for k, c in enumerate(ei.cats) if c[0] == "EF 3.0 Method (adapted)"][:28]
names = [c for _, c in efc]; idx = [k for k, _ in efc]
cs = [("S01", "HTL grid"), ("S27", "HTL bio-PPA"), ("S32", "HTL clean"), ("S02", "FAME"), ("S54", "HTL NZ 2050")]
M = np.array([[R["scen"][s]["per_mj"][k] for s, _ in cs] for k in idx]); Mr = M / np.where(M[:, [0]] == 0, 1, M[:, [0]])
keep = [i for i, n in enumerate(names) if not any(t in n.lower() for t in (" - ", "inorganics", "organics", "metals", "climate change"))][:16]
fig, ax = plt.subplots(figsize=(7, 6)); im = ax.imshow(np.log2(np.clip(Mr[keep], 1 / 8, 8)), cmap=DIV, vmin=-3, vmax=3, aspect="auto")
ax.set_xticks(range(len(cs))); ax.set_xticklabels([c[1] for c in cs], rotation=20); ax.set_yticks(range(len(keep))); ax.set_yticklabels([names[i] for i in keep], fontsize=7.5); ax.grid(False)
for i, r in enumerate(keep):
    for j in range(len(cs)): ax.text(j, i, f"{Mr[r, j]:.2f}", ha="center", va="center", fontsize=6.8, color=INK)
cb = fig.colorbar(im, ax=ax, shrink=0.7); cb.set_label("log2 ratio to S01 HTL grid")
save(fig, "F12_ef_heatmap", "EF 3.0 supply-chain indicators relative to the HTL base", f"Ratio of each design to S01 per MJ fuel for {len(keep)} EF 3.0 indicators (ecoinvent 3.12, EF 3.0 as implemented). The vectors cover background supply chains; direct foreground emissions (pond N2O, methane slip, combustion) are counted only in the GWP (climate change is therefore shown in the GWP figure, not here). For the 2050 design only electricity, hydrogen and fertiliser are prospective. FAME raises land and water use per MJ; the biomass PPA cuts fossil use, acidification and freshwater eutrophication but raises particulate matter and toxicity through bagasse combustion.",
     data=[dict(indicator=names[r], **{c[1]: float(M[r, j]) for j, c in enumerate(cs)}) for r in keep], section="LCA")
# ---------------------------------------------------------------- F13 scenarios: MFSP and GWP
S = R["scen"]; sd = {s["id"]: s for s in R["scen_def"]}; ids = list(S)
gcol = {g: C[i] for i, g in enumerate(sorted(set(s["group"] for s in R["scen_def"])))}
fig, axs = plt.subplots(1, 2, figsize=(11, 9.5), sharey=True)
y = np.arange(len(ids))[::-1]
for ax, key, lab in ((axs[0], "mfsp_ldeq", "MFSP, USD/L diesel-eq. (log)"), (axs[1], "gwp", "GWP, g CO2e/MJ")):
    v = [S[i][key] for i in ids]; ax.scatter(v, y, c=[gcol[sd[i]["group"]] for i in ids], s=28, zorder=3)
    ax.set_xlabel(lab)
    if key == "mfsp_ldeq":
        from matplotlib.ticker import FixedLocator, NullLocator
        ax.set_xscale("log"); ax.xaxis.set_major_locator(FixedLocator([1, 1.5, 2, 3, 5, 7, 10, 15, 20, 30])); ax.xaxis.set_minor_locator(NullLocator()); ax.set_xticklabels(["1", "1.5", "2", "3", "5", "7", "10", "15", "20", "30"])
        ax.axvline(CME, color=VIOLET, ls="--", lw=1); ax.axvline(DSL, color=INK2, ls=":", lw=1)
    else: ax.axvline(94, color=INK2, ls=":", lw=1); ax.axvline(32.9, color=VIOLET, ls="--", lw=1)
axs[0].set_yticks(y); axs[0].set_yticklabels([f"{i} {sd[i]['name'][:46]}" for i in ids], fontsize=6.5)
axs[1].legend(handles=[mpatches.Patch(color=c, label=g) for g, c in gcol.items()], loc="lower right", fontsize=7)
save(fig, "F13_scenarios", "Sixty scenarios: cost and climate", "Each dot is one scenario (database sheet 13_Scenarios). Dashed: CME price / 65% saving; dotted: diesel ex-tax / fossil comparator.",
     data=[dict(id=i, name=sd[i]["name"], group=sd[i]["group"], mfsp_usd_ldeq=S[i]["mfsp_ldeq"], gwp_g_mj=S[i]["gwp"], npv_usd=S[i]["npv"], tci_usd=S[i]["tci"], output_Ldeq=S[i]["ldeq"]) for i in ids], section="Scenarios")
fig, ax = plt.subplots(figsize=(7.5, 5))
for i in ids:
    ax.scatter(S[i]["gwp"], S[i]["mfsp_ldeq"], color=gcol[sd[i]["group"]], s=30, zorder=3)
    if i in ("S01", "S02", "S27", "S32", "S54", "S56", "S59", "S15", "S21", "S10", "S58"): ax.annotate(i, (S[i]["gwp"], S[i]["mfsp_ldeq"]), fontsize=7, xytext=(4, 3), textcoords="offset points")
ax.set_yscale("log"); ax.axhline(CME, color=VIOLET, ls="--", lw=1); ax.axhline(DSL, color=INK2, ls=":", lw=1); ax.axvline(94, color=INK2, ls=":", lw=1); ax.axvline(32.9, color=VIOLET, ls="--", lw=1)
ax.set_xlabel("GWP, g CO2e/MJ"); ax.set_ylabel("MFSP, USD/L diesel-eq. (log)"); ax.legend(handles=[mpatches.Patch(color=c, label=g) for g, c in gcol.items()], fontsize=7)
save(fig, "F14_scenario_map", "Cost-climate map of the scenarios", "Only prospective scenarios with clean electricity reach the lower-left quadrant (below the CME price and near the 65% saving line).", section="Scenarios")
# ---------------------------------------------------------------- F15-17 tornado plots
def tornado(route, key, fid, title, unit):
    rows = [r for r in R["oat"] if r["route"] == route]
    rows = sorted(rows, key=lambda r: -r[f"{key}_swing"])[:15][::-1]
    base = rows[0][f"{key}_base"]; fig, ax = plt.subplots(figsize=(8, 5))
    for i, r in enumerate(rows):
        lo, hi = r[f"{key}_lo"], r[f"{key}_hi"]
        ax.barh(i, lo - base, left=base, color=BLUE, height=0.6); ax.barh(i, hi - base, left=base, color=ORANGE, height=0.6)
        for out, val in ((lo, r["low"]), (hi, r["high"])):
            lab = f"{val:,.3g}" if abs(val) < 1e5 else f"{val/1e6:,.1f}M"
            ax.text(out, i, (f" {lab}" if out >= base else f"{lab} "), ha="left" if out >= base else "right", va="center", fontsize=6.5, color=INK2)
    ax.axvline(base, color=INK, lw=1); ax.set_yticks(range(len(rows))); ax.set_yticklabels([r["name"][:48] for r in rows], fontsize=7.2); ax.set_xlabel(unit)
    ax.legend(handles=[mpatches.Patch(color=BLUE, label="parameter at low value"), mpatches.Patch(color=ORANGE, label="parameter at high value")], loc="lower right")
    save(fig, fid, title, f"One-at-a-time sensitivity (registry low/high), {route} base; base = {base:.2f}.",
         data=[dict(parameter=r["name"], low=r["low"], high=r["high"], out_low=r[f"{key}_lo"], out_high=r[f"{key}_hi"]) for r in rows[::-1]], section="Sensitivity")
tornado("HTL", "mfsp", "F15_tornado_htl_mfsp", "Tornado: HTL minimum fuel selling price", "MFSP, USD/L diesel-eq.")
tornado("HTL", "gwp", "F16_tornado_htl_gwp", "Tornado: HTL climate change", "GWP, g CO2e/MJ")
tornado("FAME", "mfsp", "F17_tornado_fame_mfsp", "Tornado: FAME minimum fuel selling price", "MFSP, USD/L diesel-eq.")
tornado("FAME", "gwp", "F18_tornado_fame_gwp", "Tornado: FAME climate change", "GWP, g CO2e/MJ")
# ---------------------------------------------------------------- F19 spider
from model import evaluate, BASE_HTL
P0 = dict(REG.BASE); sel = ["prod", "htl_y", "loc_f", "r", "ef_grid", "p_el", "co2_util", "p_h2"]; pct = np.linspace(-0.4, 0.4, 9)
fig, axs = plt.subplots(1, 2, figsize=(10, 3.8)); sp = []
for j, k in enumerate(sel):
    m, g = [], []
    for q in pct:
        P = dict(P0); P[k] = P0[k] * (1 + q)
        if k == "co2_util": P[k] = min(P[k], 1.0)
        o = evaluate(P, BASE_HTL); m.append(o["mfsp_ldeq"]); g.append(o["gwp"]); sp.append(dict(param=k, change=q, mfsp=o["mfsp_ldeq"], gwp=o["gwp"]))
    axs[0].plot(pct * 100, m, color=C[j], label=REG.P[k]["name"][:30]); axs[1].plot(pct * 100, g, color=C[j])
axs[0].set_xlabel("Change from base, %"); axs[1].set_xlabel("Change from base, %"); axs[0].set_ylabel("MFSP, USD/L deq"); axs[1].set_ylabel("GWP, g CO2e/MJ")
axs[0].legend(fontsize=6.8, ncol=2, loc="upper center", bbox_to_anchor=(1.1, -0.18))
save(fig, "F19_spider", "Spider plot of the eight leading parameters (HTL)", "Response of MFSP and GWP to +-40% changes in each parameter, others at base.", data=sp, section="Sensitivity")
# ---------------------------------------------------------------- F20-21 break-even maps
mp = R["map_prod_area"]; fig, ax = plt.subplots(figsize=(7, 4.6))
cs_ = ax.contourf(mp["area"], mp["prod"], np.log10(mp["mfsp"]), levels=20, cmap=SEQ.reversed())
cl = ax.contour(mp["area"], mp["prod"], mp["mfsp"], levels=[DSL, CME, 3, 4, 6, 10], colors=[INK, VIOLET, INK2, INK2, INK2, INK2], linewidths=[1.6, 1.6, .8, .8, .8, .8])
ax.clabel(cl, fmt=lambda v: f"{v:.2f}", fontsize=7); ax.set_xscale("log"); ax.set_xlabel("Pond area, ha (log)"); ax.set_ylabel("Productivity, g/m2/d")
ax.scatter([400], [20], color=RED, zorder=4); ax.annotate("base", (400, 20), xytext=(5, 5), textcoords="offset points", fontsize=8)
cb = fig.colorbar(cs_, ax=ax); cb.set_label("log10 MFSP, USD/L deq")
save(fig, "F20_breakeven_prod_area", "Break-even map: productivity and scale", f"Iso-lines of MFSP (HTL, 2026 base). Black: diesel ex-tax ({DSL:.2f} USD/L); violet: CME ({CME:.2f} USD/L deq). Sustained outdoor productivities are 10-21 g/m2/d.",
     data=[dict(prod=float(p), area=float(a), mfsp=float(mp["mfsp"][i, j])) for i, p in enumerate(mp["prod"]) for j, a in enumerate(mp["area"])], section="Break-even")
me = R["map_ef_yield"]; fig, ax = plt.subplots(figsize=(7, 4.4))
cs_ = ax.contourf(me["ef"], me["y"], me["gwp"], levels=20, cmap=SEQ); cl = ax.contour(me["ef"], me["y"], me["gwp"], levels=[32.9, 47.0, 94.0], colors=[VIOLET, BLUE, INK], linewidths=1.6)
ax.clabel(cl, fmt={32.9: "65% saving", 47.0: "50% saving", 94.0: "= diesel"}, fontsize=7); ax.set_xlabel("Electricity GWP, kg CO2e/kWh"); ax.set_ylabel("HTL biocrude yield, kg/kg AFDW")
ax.axvline(1.137, color=RED, lw=1); ax.text(1.12, 0.31, "Visayas 2024", rotation=90, color=RED, fontsize=7, ha="right"); cb = fig.colorbar(cs_, ax=ax); cb.set_label("GWP, g CO2e/MJ")
save(fig, "F21_breakeven_ef_yield", "Break-even map: electricity carbon intensity and yield", "The 65% saving requires both low-carbon electricity and yields near the PNNL design case; on the 2024 Visayas grid no yield reaches 50%.",
     data=[dict(ef=float(e), yield_=float(yy), gwp=float(me["gwp"][i, j])) for i, yy in enumerate(me["y"]) for j, e in enumerate(me["ef"])], section="Break-even")
# ---------------------------------------------------------------- F22 prospective
fig, axs = plt.subplots(1, 2, figsize=(10.5, 3.8)); pc = {"REF": MUTED, "CES1": BLUE, "CES2": AQUA, "NZ": GREEN}; pdata = []
for path in ("REF", "CES1", "CES2", "NZ"):
    rows = R["prospective"][("HTL", path)]; yrs = [r["year"] for r in rows]
    axs[0].plot(yrs, [r["mfsp"] for r in rows], color=pc[path], label=path); axs[1].plot(yrs, [r["gwp"] for r in rows], color=pc[path], label=path)
    pdata += [dict(route="HTL", path=path, **{k: r[k] for k in ("year", "mfsp", "gwp", "ef_el", "prod", "tci", "out", "npv")}) for r in rows]
    rows = R["prospective"][("FAME", path)]; pdata += [dict(route="FAME", path=path, **{k: r[k] for k in ("year", "mfsp", "gwp", "ef_el", "prod", "tci", "out", "npv")}) for r in rows]
axs[0].axhline(CME, color=VIOLET, ls="--", lw=1); axs[0].axhline(DSL, color=INK2, ls=":", lw=1); axs[1].axhline(94, color=INK2, ls=":", lw=1); axs[1].axhline(32.9, color=VIOLET, ls="--", lw=1)
axs[0].set_ylabel("MFSP, USD/L deq"); axs[1].set_ylabel("GWP, g CO2e/MJ"); axs[0].legend(title="Pathway"); [a.set_xlabel("Year") for a in axs]
save(fig, "F22_prospective", "Prospective trajectories 2026-2050 (HTL)", "Pathways combine the Philippine Energy Plan grid (ph-grid model), productivity and yield learning, capital learning (13% per doubling) and hydrogen decarbonisation.",
     data=pdata, section="Prospective")
# ---------------------------------------------------------------- F23 logistics
LG = R["logistics"]; fig, axs = plt.subplots(1, 2, figsize=(10, 3.2))
yl = np.arange(len(LG))[::-1]
axs[0].barh(yl, [l["cost"] / 1e3 for l in LG], color=BLUE, height=0.55); axs[1].barh(yl, [l["gwp_log"] for l in LG], color=ORANGE, height=0.55)
axs[0].set_yticks(yl); axs[0].set_yticklabels([l["config"] for l in LG], fontsize=7.2); axs[1].set_yticks(yl); axs[1].set_yticklabels([])
axs[0].set_xlabel("Logistics cost, thousand USD/yr"); axs[1].set_xlabel("Logistics GWP, g CO2e/MJ")
save(fig, "F23_logistics", "Logistics configurations", "Product distribution by road, RoRo and coastal tanker, imported chemicals, and biocrude shipment to a refinery. Logistics is below 2% of cost and 1.2 g CO2e/MJ in every configuration.",
     data=LG, section="Process")
# ---------------------------------------------------------------- F24 registry confidence
grp = {}
for r in REG.R: grp.setdefault(r["group"], {"A": 0, "B": 0, "C": 0, "D": 0}); grp[r["group"]][r["conf"]] += 1
fig, ax = plt.subplots(figsize=(8, 3.4)); gs = list(grp)
left = np.zeros(len(gs))
for j, c in enumerate("ABCD"):
    v = np.array([grp[g][c] for g in gs]); ax.barh(range(len(gs)), v, left=left, color=[GREEN, BLUE, YELLOW, RED][j], height=0.55, label=f"{c}", edgecolor="white", linewidth=1.5); left += v
ax.set_yticks(range(len(gs))); ax.set_yticklabels(gs); ax.invert_yaxis(); ax.set_xlabel("Number of parameters"); ax.legend(title="Confidence", ncol=4)
save(fig, "F24_registry_confidence", "Parameter registry by confidence rating", f"{len(REG.R)} parameters; A measured/official, B peer-reviewed or reputable secondary, C estimate or derived, D assumption (flagged).",
     data=[dict(group=g, **grp[g]) for g in gs], section="Registry")
# ---------------------------------------------------------------- F25 validation
VA = R["validate"]; fig, ax = plt.subplots(figsize=(7, 2.8))
for i, v in enumerate(VA):
    ax.scatter([v["published"]], [i], color=INK, marker="|", s=300, zorder=3); ax.scatter([v["model"]], [i], color=ORANGE, s=60, zorder=4)
    ax.text(max(v["published"], v["model"]) * 1.05, i, f"{100*(v['model']/v['published']-1):+.0f}%", va="center", fontsize=8)
ax.set_xscale("log"); ax.set_yticks(range(len(VA))); ax.set_yticklabels([f"{v['case']}\n({v['unit']})" for v in VA], fontsize=7.5); ax.set_xlabel("Value (log); black bar = published, dot = this model")
save(fig, "F25_validation", "Model validation against published design cases", "The engine, run with each study's inputs, reproduces the NREL farm cost (-8%), the PNNL HTL selling price (-9%) and the ANL life cycle GHG (+8%).", data=VA, section="Verification")
print("core figures done")
