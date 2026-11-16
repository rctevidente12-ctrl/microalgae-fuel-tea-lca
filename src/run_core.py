"""Core deterministic analyses: base designs, 60 scenarios, bridge, OAT sensitivity, break-even/crossover, logistics, prospective annual."""
import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import sys, pickle, numpy as np, copy
sys.path.insert(0, ROOT + "/src")
import registry as REG, scen as SC, verify as VF, validate as VA
from model import evaluate, BASE_HTL, BASE_FAME, MJ_PER_LDEQ, RHO, LHV
P0 = dict(REG.BASE)
def ev(P=None, D=None, **kw):
    P = dict(P0 if P is None else P); D = dict(BASE_HTL if D is None else D); D.update(kw); return evaluate(P, D)
R = {}
# ---- base designs
R["base"] = {"HTL": ev(D=BASE_HTL), "FAME": ev(D=BASE_FAME)}
# ---- scenarios
SL = SC.scenario_list(); R["scen_def"] = [dict(id=s["id"], name=s["name"], group=s["group"], D=s["D"], P=s["P"], pros=s["pros"]) for s in SL]
R["scen"] = {s["id"]: SC.run_scenario(s) for s in SL}
# ---- verification + validation
R["verify"] = VF.checks(); R["verify_inh"] = VF.INH
R["validate"] = [f() for f in VA.VALID]
# ---- bridge (original basis -> corrected), HTL, same conversion feed 24,000 t/yr AFDW (after 95% harvest recovery)
P = dict(P0); typh = 1 - P["lam_typh"] * P["typh_days"] / 365
area80 = 24000e6 / (P["prod"] * 365 * P["avail"] * typh * P["harv_rec"]) / 1e4   # holds conversion feed at 24,000 t/yr AFDW
steps = [("Original basis on this engine (80 t/d on 10.4 ha; biocrude transesterified; no HTL heat; free nutrients/CO2; original capital)", dict(leg_area=True, leg_tx=True, leg_heat0=True, leg_freenut=True, leg_capex=True)),
         ("+ bottom-up capital (NREL/PNNL, CEPCI 2025, location factor)", dict(leg_area=True, leg_tx=True, leg_heat0=True, leg_freenut=True)),
         (f"+ biomass grown at 20 g/m2/d ({area80:.0f} ha of ponds deliver 24,000 t/yr to conversion)", dict(area_ha=area80, leg_tx=True, leg_heat0=True, leg_freenut=True)),
         ("+ HTL heat duty", dict(area_ha=area80, leg_tx=True, leg_freenut=True)),
         ("+ hydrotreating instead of transesterification", dict(area_ha=area80, leg_freenut=True)),
         ("+ nitrogen, phosphorus and CO2 supplied (corrected design)", dict(area_ha=area80))]
br = []
reported = 0.785 * MJ_PER_LDEQ / (RHO["fame"] * LHV["fame"])   # Cereno & Evidente (2026): EUR 0.67/L at PHP 71.244/EUR -> PHP 47.7/L -> USD 0.785/L FAME
br.append(dict(step="As reported (Cereno & Evidente, 2026 re-analysis of Aviso et al., 2021)", mfsp=reported, gwp=np.nan, area=10.36, out=10.01e6 * RHO["fame"] * LHV["fame"] / MJ_PER_LDEQ, tci=11.6e6 * 71.244 / 60.75))
for name, d in steps:
    o = ev(D=dict(BASE_HTL, **d)); br.append(dict(step=name, mfsp=o["mfsp_ldeq"], gwp=o["gwp"], area=o["area_ha"], out=o["ldeq"], tci=o["tci"], npv=o["npv"]))
R["bridge"] = br; R["area80"] = area80
# ---- OAT sensitivity (all registry parameters with a range)
oat = []
for route, D in (("HTL", BASE_HTL), ("FAME", BASE_FAME)):
    b = R["base"][route]
    for r in REG.R:
        if r["low"] == r["high"]: continue
        row = dict(route=route, key=r["key"], name=r["name"], group=r["group"], low=r["low"], high=r["high"], base=r["base"])
        for tag, v in (("lo", r["low"]), ("hi", r["high"])):
            Pp = dict(P0); Pp[r["key"]] = v; o = evaluate(Pp, D)
            row[f"mfsp_{tag}"] = o["mfsp_ldeq"]; row[f"gwp_{tag}"] = o["gwp"]; row[f"npv_{tag}"] = o["npv"]
        row["mfsp_swing"] = abs(row["mfsp_hi"] - row["mfsp_lo"]); row["gwp_swing"] = abs(row["gwp_hi"] - row["gwp_lo"])
        row["mfsp_base"] = b["mfsp_ldeq"]; row["gwp_base"] = b["gwp"]
        oat.append(row)
R["oat"] = oat
# ---- break-even and crossover
def solve(f, lo, hi, target, n=60):
    flo = f(lo) - target; fhi = f(hi) - target
    if flo * fhi > 0: return np.nan
    for _ in range(n):
        m = 0.5 * (lo + hi); fm = f(m) - target
        if flo * fm <= 0: hi = m
        else: lo, flo = m, fm
    return 0.5 * (lo + hi)
cme = P0["p_cme"] / (RHO["fame"] * LHV["fame"]) * MJ_PER_LDEQ     # USD/Ldeq
dsl = P0["p_diesel"]
def mf(key, route="HTL", **dk):
    D = dict(BASE_HTL if route == "HTL" else BASE_FAME, **dk)
    return lambda v: evaluate({**P0, key: v}, D)["mfsp_ldeq"]
def gw(key=None, route="HTL", dkey=None, **dk):
    D = dict(BASE_HTL if route == "HTL" else BASE_FAME, **dk)
    if dkey: return lambda v: evaluate(P0, {**D, dkey: v, "scale_el_all": True})["gwp"]
    return lambda v: evaluate({**P0, key: v}, D)["gwp"]
BE = []
BE.append(dict(item="Productivity for MFSP = CME price (HTL)", value=solve(mf("prod"), 5, 400, cme), unit="g/m2/d", target=f"{cme:.2f} USD/Ldeq"))
BE.append(dict(item="Productivity for MFSP = fossil diesel ex-tax (HTL)", value=solve(mf("prod"), 5, 2000, dsl), unit="g/m2/d", target=f"{dsl:.2f} USD/Ldeq"))
BE.append(dict(item="Productivity for MFSP = CME price (HTL, 2,000 ha)", value=solve(mf("prod", area_ha=2023.0), 5, 400, cme), unit="g/m2/d", target=f"{cme:.2f} USD/Ldeq"))
BE.append(dict(item="Productivity for MFSP = CME price (FAME)", value=solve(mf("prod", "FAME"), 5, 1000, cme), unit="g/m2/d", target=f"{cme:.2f} USD/Ldeq"))
BE.append(dict(item="Biocrude yield for MFSP = CME price (HTL)", value=solve(mf("htl_y"), 0.2, 2.0, cme), unit="kg/kg AFDW", target=f"{cme:.2f} USD/Ldeq"))
BE.append(dict(item="Lipid content for FAME MFSP = HTL MFSP (crossover)", value=solve(mf("lipid", "FAME"), 0.1, 2.0, R["base"]["HTL"]["mfsp_ldeq"]), unit="kg/kg AFDW", target=f"{R['base']['HTL']['mfsp_ldeq']:.2f} USD/Ldeq"))
BE.append(dict(item="Pond area for MFSP = CME price (HTL)", value=solve(lambda a: evaluate(P0, dict(BASE_HTL, area_ha=a))["mfsp_ldeq"], 10, 1e6, cme), unit="ha", target=f"{cme:.2f} USD/Ldeq"))
BE.append(dict(item="Grid GWP for 50% GHG saving (HTL)", value=solve(gw(dkey="ef_el"), 0.0, 1.5, 47.0), unit="kg CO2e/kWh", target="47 g CO2e/MJ"))
BE.append(dict(item="Grid GWP for 65% GHG saving (HTL, RED II new plants)", value=solve(gw(dkey="ef_el"), 0.0, 1.5, 32.9), unit="kg CO2e/kWh", target="32.9 g CO2e/MJ"))
BE.append(dict(item="Grid GWP for 65% saving with biomass heat (HTL)", value=solve(gw(dkey="ef_el", heat="biomass"), 0.0, 1.5, 32.9), unit="kg CO2e/kWh", target="32.9 g CO2e/MJ"))
BE.append(dict(item="Diesel price at which HTL base breaks even (= MFSP)", value=R["base"]["HTL"]["mfsp_ldeq"], unit="USD/Ldeq", target="NPV = 0"))
BE.append(dict(item="Carbon price closing the gap to diesel (HTL base)", value=R["base"]["HTL"]["abatement"], unit="USD/t CO2e", target="abatement cost"))
BE.append(dict(item="Carbon price closing the gap to diesel (HTL, solar PPA)", value=R["scen"]["S28"]["abatement"], unit="USD/t CO2e", target="abatement cost"))
BE.append(dict(item="Capital multiplier for MFSP = CME (HTL)", value=solve(lambda m: evaluate({**P0, "tci_farm": P0["tci_farm"] * m, "tci_conv": P0["tci_conv"] * m}, BASE_HTL)["mfsp_ldeq"], 0.01, 3, cme), unit="x base TCI", target=f"{cme:.2f} USD/Ldeq"))
R["breakeven"] = BE; R["cme_ldeq"] = cme
# 2-D break-even map: productivity x area (MFSP)
prods = np.unique(np.r_[np.linspace(8, 40, 17), np.linspace(45, 120, 16)]); areas = np.array([10, 25, 50, 100, 200, 400, 700, 1000, 1500, 2000, 3000, 4000])
R["map_prod_area"] = dict(prod=prods, area=areas, mfsp=np.array([[evaluate({**P0, "prod": pp}, dict(BASE_HTL, area_ha=aa))["mfsp_ldeq"] for aa in areas] for pp in prods]))
# 2-D: grid EF x biocrude yield (GWP)
efs = np.linspace(0.0, 1.3, 27); ys = np.linspace(0.30, 0.60, 13)
R["map_ef_yield"] = dict(ef=efs, y=ys, gwp=np.array([[evaluate({**P0, "htl_y": y}, dict(BASE_HTL, ef_el=e, scale_el_all=True))["gwp"] for e in efs] for y in ys]))
# ---- logistics configurations
LOG = []
for name, kw in [("Bacolod depot by road (80 km)", dict(d_road_prod=80, d_sea_prod=0)), ("Cebu via San Carlos-Toledo RoRo (28 km sea + 60 km road)", dict(d_road_prod=60, d_sea_prod=56)),
                 ("Batangas by coastal tanker (650 km)", dict(d_road_prod=10, d_sea_prod=1300)), ("Manila by coastal tanker (700 km)", dict(d_road_prod=10, d_sea_prod=1400)),
                 ("Imported chemicals from NE Asia (4,000 km)", dict(d_sea_chem=4000))]:
    o = evaluate({**P0, **kw}, BASE_HTL)
    LOG.append(dict(config=name, cost=o["cost"]["Logistics"], mfsp=o["mfsp_ldeq"], gwp_log=o["contrib"].get("Logistics", 0), gwp=o["gwp"]))
o = evaluate(P0, dict(BASE_HTL, upgrade="refinery")); LOG.append(dict(config="Biocrude by sea to Limay (Bataan) refinery, co-processed", cost=o["cost"]["Logistics"], mfsp=o["mfsp_ldeq"], gwp_log=o["contrib"].get("Logistics", 0), gwp=o["gwp"]))
R["logistics"] = LOG
# ---- prospective, annual 2026-2050
PRO = {}
for route, D in (("HTL", BASE_HTL), ("FAME", BASE_FAME)):
    for path in ("REF", "CES1", "CES2", "NZ"):
        rows = []
        for y in range(2026, 2051):
            Pp, Dp = SC.prospective(P0, D, path, y); o = evaluate(Pp, Dp)
            rows.append(dict(year=y, mfsp=o["mfsp_ldeq"], gwp=o["gwp"], ef_el=Dp["ef_el"], prod=Pp["prod"], tci=o["tci"], out=o["ldeq"], npv=o["npv"], abatement=o["abatement"]))
        PRO[(route, path)] = rows
R["prospective"] = PRO
pickle.dump(R, open(ROOT + "/results/core.pkl", "wb"))
print("bridge:"); [print(f"  {b['mfsp']:.2f}  {b['step']}") for b in br]
print("breakeven:"); [print(f"  {b['value']:.3g} {b['unit']}  {b['item']}") for b in BE]
print("logistics:"); [print(f"  {l['cost']/1e3:.0f} kUSD  {l['gwp_log']:.2f} g/MJ  {l['config']}") for l in LOG]
for k in [("HTL","REF"),("HTL","NZ")]: print(k, [(r["year"], round(r["mfsp"],2), round(r["gwp"],1)) for r in PRO[k] if r["year"] % 8 == 2])
