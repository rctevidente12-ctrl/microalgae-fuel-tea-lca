"""Scenario set (60) and prospective pathways to 2050."""
import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import copy, numpy as np, sys
sys.path.insert(0, ROOT + "/src")
import registry as REG
from model import BASE_HTL, BASE_FAME, evaluate

# Philippine grid GWP (kg CO2e/kWh), national pseudo-grid, from the ph-grid model (evidente2026grid): S26 (2024), S33-S47 (PEP), S55 (net zero)
GRID_NAT = {"REF": {2024: 1.1094, 2030: 0.8624, 2035: 0.6653, 2040: 0.5670, 2045: 0.5112, 2050: 0.4520},
            "CES1": {2024: 1.1094, 2030: 0.7427, 2035: 0.6141, 2040: 0.4485, 2045: 0.3669, 2050: 0.2905},
            "CES2": {2024: 1.1094, 2030: 0.6972, 2035: 0.5537, 2040: 0.3798, 2045: 0.2839, 2050: 0.2138},
            "NZ":   {2024: 1.1094, 2030: 0.6972, 2035: 0.4000, 2040: 0.2500, 2045: 0.1200, 2050: 0.0466}}   # NZ 2035-2045 interpolated to S55
VIS_RATIO = 1.1367 / 1.1094          # Visayas / national in 2024, held constant
def grid_ef(path, year):
    t = dict(GRID_NAT[path]); t[2026] = t[2024]; ys = sorted(t)          # 2024 mix assumed to hold to 2026
    return float(np.interp(year, ys, [t[y] for y in ys])) * VIS_RATIO

# Prospective technology/price trajectories (assumptions documented in the registry sheet "Prospective")
PROS = {  # value at 2026, 2030, 2040, 2050
    "prod":      {"REF": (20, 21, 23, 24), "CES1": (20, 22, 25, 27), "CES2": (20, 23, 27, 29), "NZ": (20, 25, 28, 30)},       # g/m2/d (BETO 25 by 2030 as stretch)
    "doublings": {"REF": (0, 0.5, 1.5, 2.5), "CES1": (0, 1, 3, 4), "CES2": (0, 1, 3, 5), "NZ": (0, 1.5, 4, 6)},              # cumulative capacity doublings
    "htl_y":     {"REF": (0.41, 0.42, 0.45, 0.47), "CES1": (0.41, 0.43, 0.48, 0.52), "CES2": (0.41, 0.44, 0.50, 0.55), "NZ": (0.41, 0.45, 0.52, 0.56)},
    "ef_h2":     {"REF": (9.53, 9.5, 9.0, 8.5), "CES1": (9.53, 9.0, 6.0, 4.0), "CES2": (9.53, 8.5, 4.0, 2.0), "NZ": (9.53, 8.0, 3.0, 1.0)},
    "p_h2":      {"REF": (4.0, 4.0, 3.8, 3.6), "CES1": (4.0, 3.8, 3.3, 3.0), "CES2": (4.0, 3.7, 3.0, 2.6), "NZ": (4.0, 3.6, 2.8, 2.3)},
    "ef_urea_mult": {"REF": (1, 1, 0.95, 0.9), "CES1": (1, 0.95, 0.8, 0.7), "CES2": (1, 0.95, 0.7, 0.55), "NZ": (1, 0.9, 0.6, 0.4)},
}
YEARS = (2026, 2030, 2040, 2050)
def traj(var, path, year): return float(np.interp(year, YEARS, PROS[var][path]))

def prospective(P, D, path, year, lr=0.13):
    P = dict(P); D = dict(D)
    if D.get("elec", "grid") == "grid":
        D["ef_el"] = grid_ef(path, year); D["scale_el_all"] = True
    P["prod"] = P["prod"] * traj("prod", path, year) / 20.0
    P["htl_y"] = min(0.59, P["htl_y"] * traj("htl_y", path, year) / 0.41)
    m = (1 - lr) ** traj("doublings", path, year)
    for k in ("cap_farm_acre", "cap_dew", "cap_co2", "cap_htl", "cap_ht", "cap_bop_htl", "cap_chg", "cap_ext", "cap_tx", "cap_ad", "cap_glyc"):
        P[k] = P[k] * m
    P["ef_h2"] = traj("ef_h2", path, year); P["p_h2"] = traj("p_h2", path, year)
    D["ef_urea_mult"] = traj("ef_urea_mult", path, year)
    return P, D

def S(sid, name, group, base, dov=None, pov=None, pros=None, desc=""):
    return dict(id=sid, name=name, group=group, D={**base, **(dov or {})}, P=pov or {}, pros=pros, desc=desc)

def scenario_list():
    L = []
    H, F = BASE_HTL, BASE_FAME
    # A. Base designs and design variants
    L += [S("S01", "HTL + hydrotreating, base (400 ha)", "A. Design", H),
          S("S02", "Lipid extraction + FAME, base (400 ha)", "A. Design", F),
          S("S03", "HTL, fully lined ponds", "A. Design", H, dict(lined=True)),
          S("S04", "FAME, fully lined ponds", "A. Design", F, dict(lined=True)),
          S("S05", "HTL, aqueous phase to CHG", "A. Design", H, dict(aq="CHG")),
          S("S06", "HTL, aqueous phase to AD", "A. Design", H, dict(aq="AD")),
          S("S07", "HTL, biocrude co-processed at refinery (Bataan)", "A. Design", H, dict(upgrade="refinery")),
          S("S08", "FAME, glycerol refined", "A. Design", F, dict(glyc="refined")),
          S("S09", "HTL, biomass-fired process heat", "A. Design", H, dict(heat="biomass")),
          S("S10", "HTL, purchased liquid CO2", "A. Design", H, dict(co2="liquid")),
          S("S11", "HTL, municipal wastewater nutrients", "A. Design", H, dict(nutr="ww")),
          S("S12", "HTL, original site area (10.4 ha)", "A. Design", H, dict(area_ha=10.36)),
          S("S13", "HTL, 100 ha", "A. Design", H, dict(area_ha=100.0)),
          S("S14", "HTL, 1,000 ha", "A. Design", H, dict(area_ha=1000.0)),
          S("S15", "HTL, ~2,000 ha (2,023 ha modelled; NREL farm scale)", "A. Design", H, dict(area_ha=2023.0)),
          S("S16", "FAME, ~2,000 ha (2,023 ha modelled)", "A. Design", F, dict(area_ha=2023.0))]
    # B. Biology and process performance
    L += [S("S17", "HTL, productivity 10 g/m2/d", "B. Biology", H, pov=dict(prod=10.0)),
          S("S18", "HTL, productivity 16.7 (NREL SOT 2023)", "B. Biology", H, pov=dict(prod=16.7)),
          S("S19", "HTL, productivity 25 (BETO 2030 target)", "B. Biology", H, pov=dict(prod=25.0)),
          S("S20", "HTL, productivity 30", "B. Biology", H, pov=dict(prod=30.0)),
          S("S21", "HTL, biocrude yield 59% (PNNL design)", "B. Biology", H, pov=dict(htl_y=0.59)),
          S("S22", "HTL, biocrude yield 33% (PNNL 2022 SOT)", "B. Biology", H, pov=dict(htl_y=0.33)),
          S("S23", "FAME, lipid 27%, 90% transesterifiable", "B. Biology", F, pov=dict(lipid=0.27, fame_frac=0.90)),
          S("S24", "FAME, lipid 15.8% (wastewater-grown)", "B. Biology", F, pov=dict(lipid=0.158)),
          S("S25", "HTL, heat recovery 92%", "B. Biology", H, pov=dict(htl_hr=0.92)),
          S("S26", "HTL, mixing energy halved", "B. Biology", H, pov=dict(mix_kwh=24.0))]
    # C. Energy supply
    L += [S("S27", "HTL, biomass power PPA (San Carlos BioPower, GEA tariff)", "C. Energy", H, dict(elec="biomass_ppa")),
          S("S28", "HTL, solar + BESS PPA (GEA-4 tariff; LCA uses PV only)", "C. Energy", H, dict(elec="solar_ppa")),
          S("S29", "FAME, CH4 slip 1% and digestate N recovery 75%", "C. Energy", F, pov=dict(ch4_leak=0.01, dig_Nrec=0.75)),
          S("S30", "HTL, electricity 0.148 USD/kWh", "C. Energy", H, pov=dict(p_el=0.148)),
          S("S31", "HTL, electricity 0.263 USD/kWh", "C. Energy", H, pov=dict(p_el=0.263)),
          S("S32", "HTL, biomass PPA + biomass heat + low-carbon H2 (1 kg CO2e/kg)", "C. Energy", H, dict(elec="biomass_ppa", heat="biomass"), pov=dict(ef_h2=1.0))]
    # D. Economics and policy
    L += [S("S33", "HTL, no income tax holiday", "D. Policy", H, dict(ith=False)),
          S("S34", "HTL, discount rate 6%", "D. Policy", H, pov=dict(r=0.06)),
          S("S35", "HTL, discount rate 14%", "D. Policy", H, pov=dict(r=0.14)),
          S("S36", "HTL, 15-year life (original study)", "D. Policy", H, pov=dict(life=15)),
          S("S37", "HTL, pre-war 2025 prices", "D. Policy", H, pov=dict(p_diesel=0.73, p_meoh=350, p_h2=3.5, p_el=0.17, p_cme=1.60, fx=57.5)),
          S("S38", "HTL, location factor 0.85", "D. Policy", H, pov=dict(loc_f=0.85)),
          S("S39", "HTL, location factor 1.30", "D. Policy", H, pov=dict(loc_f=1.30)),
          S("S40", "FAME, no income tax holiday", "D. Policy", F, dict(ith=False)),
          S("S41", "HTL, capital -30% (AACE Class 4 low bound)", "D. Policy", H, pov=dict(tci_farm=REG.BASE["tci_farm"] * 0.7, tci_conv=REG.BASE["tci_conv"] * 0.7)),
          S("S42", "HTL, capital +50% (AACE Class 4 high bound)", "D. Policy", H, pov=dict(tci_farm=REG.BASE["tci_farm"] * 1.5, tci_conv=REG.BASE["tci_conv"] * 1.5))]
    # E. Prospective 2030-2050
    n = 43
    for path in ("REF", "CES1", "CES2", "NZ"):
        for y in (2030, 2040, 2050):
            L.append(S(f"S{n:02d}", f"HTL, {path} pathway {y}", "E. Prospective", H, pros=(path, y))); n += 1
    L += [S("S55", "FAME, NZ pathway 2050", "E. Prospective", F, pros=("NZ", 2050)),
          S("S56", "HTL ~2,000 ha (2,023 ha), NZ pathway 2050 + biomass heat", "E. Prospective", H, dict(area_ha=2023.0, heat="biomass"), pros=("NZ", 2050))]
    # F. Accounting and legacy
    L += [S("S57", "HTL, system expansion instead of energy allocation", "F. Accounting", H, dict(alloc="sysexp")),
          S("S58", "HTL, CO2 from a fossil source (re-emitted at use)", "F. Accounting", H, dict(co2_fossil=True)),
          S("S59", "Original process basis (80 t/d on 10.4 ha, biocrude transesterified, no HTL heat, free nutrients) with bottom-up capital", "F. Accounting", H,
            dict(leg_area=True, leg_tx=True, leg_heat0=True, leg_freenut=True)),
          S("S60", "FAME, system expansion", "F. Accounting", F, dict(alloc="sysexp"))]
    return L

def run_scenario(s, P0=None):
    P = dict(REG.BASE if P0 is None else P0); P.update(s["P"]); D = dict(s["D"])
    if s.get("pros"): P, D = prospective(P, D, *s["pros"])
    if D.get("ef_urea_mult"): pass
    return evaluate(P, D)
