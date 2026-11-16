"""Model validation against published design cases (NREL farm SOT 2023; PNNL HTL design 2014)."""
import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import sys; sys.path.insert(0, ROOT + "/src")
import registry as REG
from model import evaluate, cepci, BASE_HTL, MJ_PER_LDEQ
US = dict(p_el=0.0682, w_op=26910 * 1.9, w_eng=80000 * 1.9, loc_f=1.0, p_land=0.0, lam_typh=0.0, makeup_mm=0.0, r=0.10, life=30,
          p_urea=0.4123 / 0.4536 * 1000 * 46 / 82 * 1.0, p_dap=0.3364 / 0.4536 * 1000, avail=1.0, wc=0.05, co2_util=0.90, htl_hr=0.85, p_water=0.0)
def nrel_farm():
    """2023 SOT: 5,000 acres, 16.7 g/m2/d (annual), unlined ponds; MBSP 654 USD2016/ton(short) AFDW."""
    P = dict(REG.BASE); P.update(US); P["prod"] = 16.7 * 330 / 365 * 1.0
    D = dict(BASE_HTL, area_ha=5000 / 2.47105)
    o = evaluate(P, D)
    mbsp_2016_per_short_ton = o["mbsp"] / cepci(2016) * 0.90718
    return dict(case="NREL algae farm, 2023 SOT", published=654.0, model=mbsp_2016_per_short_ton, unit="USD2016 per short ton AFDW",
                note=f"US prices and wages, location factor 1.0; published value is the unlined case on the alternative evaporation basis; against the base 2023 SOT value (740 USD/t) the engine is {100*(mbsp_2016_per_short_ton/740-1):+.0f}%.", source="klein2024")
def pnnl_htl():
    """PNNL-23227 design: 1,339 t/d AFDW at $430/ton (2011$), 59% biocrude yield; MFSP 4.49 USD2011/GGE."""
    P = dict(REG.BASE); P.update(US); P.update(htl_y=0.59, ht_y=0.80, diesel_frac=0.83, p_h2=1.6, ef_h2=9.5, life=30, p_heat=5.1 / 1.055 / 0.85)
    D = dict(BASE_HTL, aq="CHG", buy_biomass=430 / 0.90718 * cepci(2011), afdw_tpd=1339 * 0.90718)
    o = evaluate(P, D)
    gge_mj = 121.3   # MJ (LHV) per US gasoline gallon equivalent
    mfsp_2011_gge = o["mfsp_mj"] * gge_mj / cepci(2011)
    return dict(case="PNNL whole-algae HTL design", published=4.49, model=mfsp_2011_gge, unit="USD2011 per GGE",
                note="Biomass bought at $430/ton; aqueous phase to CHG; US prices; H2 bought at $1.60/kg instead of an on-site H2 plant.", source="jones2014")
if __name__ == "__main__":
    for f in VALID:
        r = f(); print(r, f"dev {100*(r['model']/r['published']-1):+.0f}%")

def anl_lca():
    """ANL supply-chain LCA of the PNNL HTL design: 35,700 g CO2e/MMBtu renewable diesel = 33.8 g/MJ."""
    import ei
    us = [m["col"] for m in ei.meta if m["activity"] == "market group for electricity, medium voltage" and m["location"] == "US"][0]
    P = dict(REG.BASE); P.update(US); P.update(htl_y=0.59, ht_y=0.80, diesel_frac=0.83, prod=25.0 * 330 / 365, n2o_frac=0.0)
    D = dict(BASE_HTL, aq="CHG", area_ha=5000 / 2.47105, ef_el=float(ei.U[ei.GWP, us]))
    o = evaluate(P, D)
    return dict(case="ANL LCA of PNNL HTL pathway", published=33.8, model=o["gwp"], unit="g CO2e/MJ", note=f"US grid {D['ef_el']:.3f} kg/kWh (ecoinvent 3.12); CHG; 59% yield; 25 g/m2/d.", source="pegallapati2015")
VALID = [nrel_farm, pnnl_htl, anl_lca]
