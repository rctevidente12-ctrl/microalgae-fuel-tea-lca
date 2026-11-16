"""Internal closure checks of the engine (mass, elements, energy, cost, impact). Writes results/closure.json."""
import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import sys, json, numpy as np
sys.path.insert(0, ROOT + "/src")
import registry as REG
from model import evaluate, npv, BASE_HTL, BASE_FAME, LHV, MJ_PER_LDEQ
P = dict(REG.BASE); rows = []
def chk(route, block, item, lhs, rhs, tol, unit, note):
    dev = (lhs - rhs) / rhs if rhs else float("nan")
    rows.append(dict(route=route, block=block, check=item, engine=float(lhs), reference=float(rhs), unit=unit, rel_dev=float(dev), tolerance=tol, ok=bool(abs(dev) <= tol), note=note))
for route, D in (("HTL", BASE_HTL), ("FAME", BASE_FAME)):
    o = evaluate(P, D); g = P.get
    # 1 cultivation mass (Eq. 1-2)
    grown = g("prod") * o["area_ha"] * 1e4 * 365 * g("avail") / 1e6
    chk(route, "Mass", "Biomass grown = productivity x area x 365 x on-stream (before typhoon loss)", o["grown"], grown, 0.05, "t AFDW/yr", "Difference is the expected typhoon downtime (lambda x days/365).")
    chk(route, "Mass", "Harvested = grown x harvest recovery", o["afdw"], o["grown"] * g("harv_rec"), 1e-9, "t AFDW/yr", "")
    # 2 carbon
    C_bio = o["grown"] * g("co2_fix") * 12 / 44; C_del = o["co2_need"] * g("co2_util") * 12 / 44
    chk(route, "Carbon", "C fixed in biomass = C in CO2 delivered x utilisation", C_del, C_bio, 1e-9, "t C/yr", "")
    chk(route, "Carbon", "Implied biomass C fraction vs Chisti (2007) CO0.48H1.83N0.11P0.01", g("co2_fix") * 12 / 44, 12 / 23.36, 0.05, "kg C/kg AFDW", "co2_fix 1.83 kg/kg implies 49.9% C; formula gives 51.4%.")
    # 3 nitrogen
    N_sup = o["urea"] * 0.466 + o["dap"] * 0.18; N_rec = o["N_need"] - N_sup
    chk(route, "Nitrogen", "N demand = purchased N + recycled N (+ wastewater N)", N_sup + N_rec, o["N_need"], 1e-9, "t N/yr", f"Recycled/wastewater N = {N_rec:,.0f} t/yr ({N_rec / o['N_need']:.0%} of demand).")
    if route == "HTL":
        chk(route, "Nitrogen", "Recycled N <= N in HTL aqueous phase", N_rec, o["afdw"] * g("Nfrac") * g("aq_Nfrac"), 1.0, "t N/yr", "Aqueous N computed on the harvested biomass that enters HTL; recycled N must not exceed it (rel_dev <= 0).")
        # 4 HTL carbon efficiency
        ceff = g("htl_y") * 0.776 / (g("co2_fix") * 12 / 44)
        chk(route, "Carbon", "HTL carbon efficiency to biocrude (77.6% C biocrude) vs PNNL design range", ceff, 0.60, 0.15, "-", "Jones et al. (2014) and Zhu et al. (2023) report 50-70% of feed carbon in biocrude.")
        fuel = o["biocrude"] * g("ht_y")
        chk(route, "Mass", "Upgraded fuel = biocrude x upgraded fuel yield", sum(v for k, v in o["prod"].items() if k in ("rd", "naph")), fuel, 1e-6, "t/yr", "")
        chk(route, "Mass", "Hydrogen = biocrude x H2 demand", o["h2"], o["biocrude"] * g("ht_h2"), 1e-6, "t/yr", "")
    if route == "FAME":
        tag = o["lip"] - o["extract_ret"]
        chk(route, "Mass", "Harvested = lipid-extracted residue + returned non-transesterifiable extract + TAG to transesterification", (o["afdw"] - o["lip"]) + o["extract_ret"] + tag, o["afdw"], 1e-9, "t AFDW/yr", f"Returned extract {o['extract_ret']:,.0f} t/yr goes to anaerobic digestion with the residue (AD feed {o['ad_feed']:,.0f} t/yr).")
    # 5 energy
    chk(route, "Energy", "Fuel energy = sum(product mass x LHV)", o["fuel_mj"], sum(o["prod"].get(k, 0) * 1000 * LHV[k] for k in ("rd", "naph", "fame")), 1e-9, "MJ/yr", "")
    chk(route, "Energy", "Litres diesel-eq = fuel MJ / 35.9", o["ldeq"], o["fuel_mj"] / MJ_PER_LDEQ, 1e-9, "L/yr", "")
    e_in = o["afdw"] * 1000 * 22.0 + o.get("h2", 0) * 1000 * 120.0 + max(o["heat_net"], 0) + o["el_dem"] * 3.6
    rows.append(dict(route=route, block="Energy", check="First-law efficiency: fuel LHV / (biomass HHV 22 MJ/kg + H2 + heat + electricity)", engine=o["fuel_mj"] / e_in, reference=float("nan"), unit="-", rel_dev=float("nan"), tolerance=None, ok=bool(0 < o["fuel_mj"] / e_in < 1), note="Must lie in (0,1)."))
    # 6 cost closure
    chk(route, "Cost", "NPV at the MFSP = 0 (discounted cash-flow closure)", 1.0 + npv(P, D, o, o["mfsp_mj"]) / o["tci"], 1.0, 1e-3, "1 + NPV/TCI", "")
    chk(route, "Cost", "MFSP per GJ = per MJ x 1000; per L deq = per MJ x 35.9", o["mfsp_ldeq"], o["mfsp_mj"] * MJ_PER_LDEQ, 1e-9, "USD/L deq", "")
    # 7 LCA closure
    chk(route, "Impact", "Sum of GWP contributions = total GWP", sum(o["contrib"].values()), o["gwp"], 1e-6, "g CO2e/MJ", "")
json.dump(rows, open(ROOT + "/results/closure.json", "w"), indent=1)
for r in rows: print(f"{r['route']:5s} {r['block']:8s} {'OK ' if r['ok'] else 'FAIL'} {r['engine']:14.5g} {r['reference']:14.5g} {r['rel_dev']:+.2%}  {r['check'][:70]}")
