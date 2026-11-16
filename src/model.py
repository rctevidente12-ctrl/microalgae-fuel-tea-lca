import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
"""One process balance -> bottom-up TEA + attributional LCA (ecoinvent 3.12 cut-off unit scores, 183 indicators).
Routes: 'HTL' (whole-algae hydrothermal liquefaction + hydrotreating to renewable diesel/naphtha)
        'FAME' (wet lipid extraction + transesterification; residue to anaerobic digestion + CHP).
All money in USD 2026 (real). Equation numbers (Eq. n) refer to the report."""
import numpy as np, sys
sys.path.insert(0, ROOT + "/src")
import registry as REG
import ei
from lcimap import MAP

CE = REG.CEPCI; CE_NOW = CE[2025]
LHV = dict(fame=37.2, rd=43.1, naph=43.5, diesel=43.0, glyc=16.0, ch4=35.8)   # MJ/kg, MJ/m3 for CH4
RHO = dict(fame=0.88, rd=0.80, naph=0.70, diesel=0.835)                          # kg/L
MJ_PER_LDEQ = RHO["diesel"] * LHV["diesel"]                                      # 35.9 MJ per litre diesel-equivalent
ACRE_PER_HA = 2.47105

# ---------------- LCA vectors (183 categories)
_IDX = {}
for m in ei.meta: _IDX.setdefault((m["activity"], m["location"]), []).append(m["col"])
def _col(a, l): return _IDX[(a, l)][0]
COLS = {k: _col(*v) for k, v in MAP.items() if k != "tanker"}
COLS["tanker"] = _col("market for transport, freight, sea, tanker for liquid goods other than petroleum and liquefied natural gas, HFO", "GLO")
COLS["el_PH"] = _col("market for electricity, medium voltage", "PH")
COLS["heat_ng"] = _col("heat production, natural gas, at industrial furnace >100kW", "RoW")
COLS["el_bio"] = [m["col"] for m in ei.meta if m["activity"].startswith("treatment of bagasse, from sugarcane, in heat and power co-generation unit") and m["location"] == "IN-Eastern grid" and "electricity" in m["product"]][0]
COLS["el_pv"] = [m["col"] for m in ei.meta if m["activity"].startswith("electricity production, photovoltaic, 570kWp open ground installation") and m["location"] == "AU"][0]
COLS["heat_wood"] = [m["col"] for m in ei.meta if m["activity"] == "heat production, softwood chips from forest, at furnace 1000kW" and m["location"] == "RoW"][0]
U = ei.U; NC = U.shape[0]; GWP = ei.GWP
WASTE = {"ww_treat", "inert_waste"}            # cut-off waste-treatment markets carry negative reference amounts
CATS = ei.cats
GWP_CH4_BIO, GWP_N2O = 27.0, 273.0             # IPCC AR6 (forster2021)

def cepci(y): return CE_NOW / CE[y]

def evaluate(P, D):
    """P: parameter dict (registry keys); D: design switches. Returns dict of results."""
    g = P.get
    route = D.get("route", "HTL")
    # ------------------------------------------------ 1. Cultivation (Eq. 1-6)
    typh_avail = 1.0 - g("lam_typh") * g("typh_days") / 365.0
    if D.get("leg_area"):                        # original basis: 80 t/d AFDW x 300 d on 10.36 ha, regardless of productivity
        area_ha = 10.36; grown = 80.0 * 300.0 / g("harv_rec")   # 24,000 t/yr reaches conversion
    else:
        area_ha = D.get("area_ha", 400.0)
        grown = g("prod") * area_ha * 1e4 * 365.0 * g("avail") * typh_avail / 1e6          # t AFDW/yr grown (Eq. 1)
    afdw = grown * g("harv_rec")                                                           # t AFDW/yr harvested (Eq. 2)
    dw = afdw / (1.0 - g("ash"))
    acres = area_ha * ACRE_PER_HA
    co2_need = grown * g("co2_fix") / g("co2_util")                                       # t CO2 delivered (Eq. 3)
    N_need = grown * g("Nfrac") / g("nut_eff"); P_need = grown * g("Pfrac") / g("nut_eff")  # t/yr (Eq. 4)
    el = {}; heat_dem = 0.0; inv = {}; direct = np.zeros(NC); cost = {}; capi = {}; capf = {}
    if D.get("buy_biomass") is not None and D.get("afdw_tpd"):
        afdw = D["afdw_tpd"] * 330.0; grown = afdw / g("harv_rec"); dw = afdw / (1.0 - g("ash")); area_ha = 0.0; acres = 0.0
        co2_need = 0.0; N_need = 0.0; P_need = 0.0
    el["mixing"] = g("mix_kwh") * area_ha * 365.0
    el["dewatering"] = g("dew_kwh") * afdw
    el["water"] = g("circ_kwh") * afdw
    el["co2_delivery"] = g("co2_kwh") * co2_need if D.get("co2", "flue") == "flue" else 0.0
    if D.get("buy_biomass") is not None:
        for k in ("mixing", "dewatering", "water", "co2_delivery"): el[k] = 0.0
    water_m3 = g("makeup_mm") / 1000.0 * area_ha * 1e4 * 365.0                           # Eq. 5
    inv["tap_water"] = water_m3 * 1000.0 * 0.0     # raw water: abstraction only (no treatment) -> not in technosphere
    inv["excavation"] = g("earth_m3") * area_ha / 30.0                                     # amortised over 30 yr
    inv["concrete"] = 30.0 * area_ha / 30.0                                               # 30 m3/ha (davis2016), 30-yr life
    inv["hdpe"] = (1.57 * area_ha * 1e4 if D.get("lined") else 1.57 * 253.0 * area_ha) / 15.0  # full liner, or liner on turns only (253 m2/ha), 15-yr life
    # ------------------------------------------------ 2. Conversion
    N_rec = 0.0; prod = {}; credit_el = 0.0; ch4_slip = 0.0; lip = 0.0; extract_ret = 0.0; resid = 0.0
    if route == "HTL":
        feed_kg = dw * 1000.0
        slurry_t = dw / g("htl_solids")
        q_htl = 0.0 if D.get("leg_heat0") else slurry_t * 1000.0 * 3.8e-3 * g("htl_dT") * (1.0 - g("htl_hr"))   # MJ/yr (Eq. 7)
        heat_dem += q_htl
        el["htl_pump"] = slurry_t * g("htl_pump")                                          # ~1 m3/t slurry
        biocrude = afdw * g("htl_y")                                                       # t/yr (Eq. 8)
        N_aq = afdw * g("Nfrac") * g("aq_Nfrac")                                     # N in the biomass that enters HTL (Eq. 9)
        aq = D.get("aq", "recycle")
        if aq == "recycle": N_rec += N_aq * g("aq_Nrec")
        elif aq == "CHG":
            N_rec += N_aq * 0.8; heat_dem -= afdw * 1000.0 * 2.8 * 0.85                     # CHG CH4 2.8 MJ/kg AFDW (derived from jones2014), boiler 85%
        elif aq == "AD":
            N_rec += N_aq * 0.6; heat_dem -= afdw * 1000.0 * 1.9 * 0.85                     # AD CH4 1.9 MJ/kg AFDW (derived: fernandez2018, wang2021ad)
        if D.get("leg_tx"):                                                                # original: biocrude treated as TAG
            fame = biocrude * 0.95
            prod["fame"] = fame; prod["glyc_crude"] = fame * g("glyc_yield")
            inv["methanol"] = fame * g("meoh_bd") * 1000 / 1000.0
            inv["naoh"] = fame * g("cat_bd"); inv["h3po4"] = fame * g("acid_bd")
            heat_dem += fame * g("steam_bd"); el["upgrading"] = fame * g("el_bd")
            h2 = 0.0
        else:
            fuel = biocrude * g("ht_y")
            prod["rd"] = fuel * g("diesel_frac"); prod["naph"] = fuel * (1 - g("diesel_frac"))
            h2 = biocrude * g("ht_h2")                                                     # t H2 (Eq. 9)
            inv["h2"] = h2 * 1000.0
            el["upgrading"] = g("ht_el") * fuel * 1000.0 if D.get("upgrade", "onsite") == "onsite" else 0.0
        afdw_conv = afdw
    else:  # FAME
        lip = afdw * g("lipid") * g("ext_eff")                                             # t extracted lipid (Eq. 10)
        tag = lip * g("fame_frac")
        fame = tag * g("tx_conv")                                                          # t FAME (Eq. 11)
        prod["fame"] = fame
        glyc = fame * g("glyc_yield"); prod["glyc_crude"] = glyc
        heat_dem += lip * 1000 * g("ext_heat") + fame * g("steam_bd")
        el["extraction"] = lip * 1000 * g("ext_el"); el["transesterification"] = fame * g("el_bd")
        inv["hexane"] = lip * g("hex_loss"); inv["methanol"] = fame * g("meoh_bd")
        inv["naoh"] = fame * g("cat_bd"); inv["h3po4"] = fame * g("acid_bd")
        extract_ret = lip - tag                                                            # non-transesterifiable extract (polar lipids, pigments) returned to AD
        resid = (afdw - lip) + extract_ret                                                 # t VS to AD = lipid-extracted residue + returned extract (Eq. 11)
        ch4 = resid * 1000.0 * g("ad_ch4") * (1 - g("ch4_leak"))                           # m3/yr
        ch4_slip = resid * 1000.0 * g("ad_ch4") * g("ch4_leak") * 0.717                    # kg CH4
        e_ch4 = ch4 * LHV["ch4"]
        credit_el = e_ch4 * g("chp_el") / 3.6                                              # kWh generated
        heat_dem -= e_ch4 * g("chp_th")
        N_rec += afdw * g("Nfrac") * g("dig_Nrec")                                       # digestate N from the biomass that enters conversion
        if D.get("glyc") == "refined":
            prod["glyc_ref"] = glyc * 0.80; prod.pop("glyc_crude"); heat_dem += glyc * 2000.0
        h2 = 0.0; biocrude = 0.0; afdw_conv = afdw
    heat_net = max(heat_dem, 0.0); heat_surplus = max(-heat_dem, 0.0)
    # ------------------------------------------------ 3. Nutrients and CO2 (Eq. 13-14)
    N_ww = g("ww_N_kgd") * 365 / 1000.0 if D.get("nutr") == "ww" else 0.0
    if D.get("leg_freenut"):
        N_buy = 0.0; P_buy = 0.0
    else:
        P_buy = P_need
        dap = P_buy / 0.201                                                                 # t DAP
        N_buy = max(0.0, N_need - N_rec - N_ww - dap * 0.18)
    dap = P_buy / 0.201 if P_buy else 0.0
    urea = N_buy / 0.466
    inv["dap"] = dap * 1000; inv["urea"] = urea * 1000
    if D.get("co2", "flue") == "liquid": inv["co2_liquid"] = co2_need * 1000
    # ------------------------------------------------ 4. Energy balance
    el_dem = sum(el.values())
    el_import = max(el_dem - credit_el, 0.0); el_export = max(credit_el - el_dem, 0.0)
    for k in ("methanol", "naoh", "h3po4", "hexane"):
        inv.setdefault(k, 0.0)                                                             # all chemical flows already in kg
    # ------------------------------------------------ 5. Products, energy
    mj = {"rd": prod.get("rd", 0) * 1000 * LHV["rd"], "naph": prod.get("naph", 0) * 1000 * LHV["naph"], "fame": prod.get("fame", 0) * 1000 * LHV["fame"]}
    fuel_mj = sum(mj.values())
    glyc_kg = (prod.get("glyc_crude", 0) + prod.get("glyc_ref", 0)) * 1000
    ldeq = fuel_mj / MJ_PER_LDEQ
    # ------------------------------------------------ 6. Logistics (Eq. 16-17)
    prod_t = sum(prod.get(k, 0) for k in ("rd", "naph", "fame")) + glyc_kg / 1000
    chem_t = (inv["methanol"] + inv["naoh"] + inv["h3po4"] + inv["hexane"] + inv["urea"] + inv["dap"]) / 1000.0
    tkm_road = prod_t * g("d_road_prod") + chem_t * 100.0
    tkm_sea = prod_t * g("d_sea_prod") * 0.5 + chem_t * g("d_sea_chem")
    refinery = route == "HTL" and D.get("upgrade") == "refinery" and not D.get("leg_tx")
    if refinery: tkm_sea += biocrude * g("d_refinery")
    inv["lorry"] = tkm_road; inv["tanker"] = tkm_sea
    # ------------------------------------------------ 7. Capital (Eq. 18-22)
    sc = lambda base, x, ref, e: base * (x / ref) ** e if x > 0 else 0.0
    lf = g("loc_f")
    farm = D.get("buy_biomass") is None
    capf["Ponds, inoculum, water"] = g("cap_farm_acre") * acres * (max(acres, 1e-6) / 5000.0) ** (g("exp_farm") - 1) * cepci(2016)
    if D.get("lined"): capf["Pond liners"] = g("cap_liner_acre") * acres * cepci(2014)
    capf["Harvest & dewatering"] = sc(g("cap_dew"), afdw, 108862.0, g("exp_proc")) * cepci(2016)
    capf["CO2 delivery"] = (sc(g("cap_co2"), co2_need, 240000.0, g("exp_proc")) * 2.0 * cepci(2016) + 0.5e6 * g("d_co2_pipe")) if D.get("co2", "flue") == "flue" else sc(g("cap_co2"), co2_need, 240000.0, g("exp_proc")) * cepci(2016)
    tpd = afdw_conv / 330.0
    if route == "HTL":
        capi["HTL"] = sc(g("cap_htl"), tpd, 1339.0, g("exp_proc")) * cepci(2011)
        capi["Balance of plant"] = sc(g("cap_bop_htl"), tpd, 1339.0, g("exp_proc")) * cepci(2011)
        if D.get("leg_tx"):
            capi["Transesterification"] = sc(g("cap_tx"), prod["fame"] * 1000 / RHO["fame"] / 1e6, 37.85, 0.6) * cepci(2005)
        elif not refinery:
            capi["Hydrotreating"] = sc(g("cap_ht"), biocrude / 330 / 0.159 / 0.95, 4500.0, g("exp_proc")) * cepci(2011)
        aq = D.get("aq", "recycle")
        if aq == "CHG": capi["CHG"] = sc(g("cap_chg"), tpd, 1339.0, g("exp_proc")) * cepci(2011)
        if aq == "AD": capi["Aqueous AD"] = sc(g("cap_ad"), afdw, 116000.0, g("exp_proc")) * cepci(2016) * 1.5
    else:
        capi["Lipid extraction"] = sc(g("cap_ext"), tpd, 548.2, g("exp_proc")) * cepci(2016)
        capi["Transesterification"] = sc(g("cap_tx"), prod["fame"] * 1000 / RHO["fame"] / 1e6, 37.85, 0.6) * cepci(2005)
        capi["AD + CHP"] = sc(g("cap_ad"), afdw, 116000.0, g("exp_proc")) * cepci(2016)
        if D.get("glyc") == "refined": capi["Glycerol refining"] = sc(g("cap_glyc"), glyc_kg / 8000.0, 1000.0, 0.6) * cepci(2010)
    if not farm: capf = {}
    capf = {k: v * lf for k, v in capf.items()}; capi = {k: v * lf for k, v in capi.items()}
    inst_f, inst_c = sum(capf.values()), sum(capi.values())
    fci = inst_f * g("tci_farm") + inst_c * g("tci_conv")                                 # Eq. 21
    if D.get("leg_capex"): fci = 1047990466 * 0.63 / g("fx")                               # original FCI share of TPC
    wc = g("wc") * fci; tci = fci + wc
    # ------------------------------------------------ 8. Operating cost (Eq. 23-27)
    elec = D.get("elec", "grid")
    if elec == "biomass_ppa": pe = g("p_el") - (g("gen_vis") - g("gea_bio")) / g("fx")          # GEA tariff replaces the captive generation charge (Eq. 24)
    elif elec == "solar_ppa": pe = g("p_el") - (g("gen_vis") - g("gea_solar")) / g("fx")
    else: pe = g("p_el")
    cost["Electricity"] = el_import * pe
    cost["Heat"] = heat_net / 1000.0 * (g("p_heat_bio") if D.get("heat") == "biomass" else g("p_heat"))
    cost["Nutrients"] = urea * g("p_urea") + dap * g("p_dap")
    cost["CO2 (purchased)"] = co2_need * g("p_co2liq") if D.get("co2") == "liquid" else 0.0
    cost["Hydrogen"] = (inv.get("h2", 0) * g("p_h2")) if not refinery else 0.0
    cost["Refinery tolling"] = biocrude * g("toll") if refinery else 0.0
    cost["Chemicals"] = (inv["methanol"] * g("p_meoh") + inv["naoh"] * g("p_naoh") + inv["h3po4"] * g("p_h3po4") + inv["hexane"] * g("p_hexane")) / 1000.0
    if route == "HTL" and not D.get("leg_tx"):
        cost["Chemicals"] += (8.5e6 - 7.21e6) * (tpd / 1339.0) * cepci(2011)               # hydrotreating catalysts
        if D.get("aq") == "CHG": cost["Chemicals"] += 7.21e6 * (tpd / 1339.0) * cepci(2011)
    cost["Water"] = water_m3 * g("p_water")
    cost["Land lease"] = area_ha * 1.25 * g("p_land")
    staff_farm = 100.0 * (max(acres, 1.0) / 5000.0) ** 0.5
    staff_conv = (50.0 if route == "HTL" else 35.0) * (max(tpd, 1.0) / 1339.0) ** 0.25
    staff = staff_farm + staff_conv
    cost["Labour"] = staff * (0.85 * g("w_op") + 0.15 * g("w_eng"))
    cost["Maintenance"] = g("maint") * (inst_f + inst_c)
    cost["Insurance & local tax"] = g("ins_tax") * tci
    cost["Logistics"] = (prod_t * g("d_road_prod") * g("c_road") + prod_t * g("d_sea_prod") * 0.5 * g("c_sea")
                         + (biocrude * g("d_refinery") * g("c_sea") if refinery else 0.0))
    cost["Typhoon repairs (expected)"] = g("lam_typh") * g("typh_cost") * inst_f
    if not farm:
        cost["Biomass purchase"] = afdw * D["buy_biomass"]; cost["Land lease"] = 0.0; cost["Water"] = 0.0
        cost["Labour"] = staff_conv * (0.85 * g("w_op") + 0.15 * g("w_eng"))
    opex = sum(cost.values())
    # ------------------------------------------------ 9. Revenue (non-fuel) and LCA
    glyc_price = g("p_glyc_ref") if D.get("glyc") == "refined" else g("p_glyc_crude")
    rev_co = glyc_kg * glyc_price + el_export * g("p_el_sell")
    # LCA inventory -> impacts (Eq. 28-31); contributions kept by group
    GROUP = {"urea": "Nutrients", "dap": "Nutrients", "h2": "Hydrogen", "methanol": "Chemicals", "naoh": "Chemicals", "h3po4": "Chemicals",
             "hexane": "Chemicals", "lorry": "Logistics", "tanker": "Logistics", "excavation": "Infrastructure", "hdpe": "Infrastructure", "concrete": "Infrastructure", "co2_liquid": "CO2 (purchased)"}
    con = {}
    def add(grp, vec):
        con[grp] = con.get(grp, 0) + vec
    for k, amt in inv.items():
        if amt <= 0 or k not in COLS: continue
        add(GROUP.get(k, "Other"), (-amt if k in WASTE else amt) * U[:, COLS[k]])
    if elec in ("biomass_ppa", "solar_ppa"):
        ef_el = g("ef_bio_el") if elec == "biomass_ppa" else g("ef_pv_el")
        c = COLS["el_bio"] if elec == "biomass_ppa" else COLS["el_pv"]
        vel = U[:, c].copy(); vel = vel * (ef_el / vel[GWP])
    else:
        vel = U[:, COLS["el_PH"]].copy()
        ef_el = D.get("ef_el", g("ef_grid"))
        if D.get("scale_el_all"): vel = vel * (ef_el / vel[GWP])
    vel[GWP] = ef_el
    add("Electricity", el_import * vel)
    vh = U[:, COLS["heat_wood"] if D.get("heat") == "biomass" else COLS["heat_ng"]].copy()
    if D.get("heat") != "biomass": vh[GWP] = g("ef_heat_fossil")
    add("Heat", heat_net * vh)
    if "h2" in inv:
        v = np.zeros(NC); v[GWP] = inv["h2"] * (g("ef_h2") - U[GWP, COLS["h2"]]); add("Hydrogen", v)
    add("Infrastructure", (prod_t * 1000.0 / (5e7 * 50.0)) * U[:, COLS["chem_factory"]])
    v = np.zeros(NC); v[GWP] = (N_need) * 1000 * g("n2o_frac") * 44 / 28 * GWP_N2O; add("Pond N2O", v)
    v = np.zeros(NC); v[GWP] = ch4_slip * GWP_CH4_BIO; add("AD methane slip", v)
    v = np.zeros(NC); v[GWP] = fuel_mj * g("comb_nonco2") / 1000.0; add("Combustion CH4/N2O", v)
    if D.get("co2_fossil"):
        c_fuel = (prod.get("rd", 0) * 0.86 + prod.get("naph", 0) * 0.85 + prod.get("fame", 0) * 0.77) * 1000 * 44 / 12
        v = np.zeros(NC); v[GWP] = c_fuel; add("Fossil CO2 re-emitted", v)
    imp = sum(con.values())
    # allocation (energy, RED II) between fuels, glycerol and exported electricity
    e_tot = fuel_mj + glyc_kg * LHV["glyc"] + el_export * 3.6
    f_fuel = fuel_mj / e_tot if e_tot > 0 else 0.0
    if D.get("alloc") == "sysexp":                                                          # system expansion
        imp_fuel = imp - glyc_kg * U[:, COLS["glycerine"]] * (0.8 if D.get("glyc") != "refined" else 1.0) - el_export * vel
    else:
        imp_fuel = imp * f_fuel
    contrib = {k: (v * (f_fuel if D.get("alloc") != "sysexp" else 1.0))[GWP] * 1000.0 / fuel_mj if fuel_mj > 0 else 0.0 for k, v in con.items()}
    per_mj = imp_fuel / fuel_mj if fuel_mj > 0 else imp_fuel * np.nan
    gwp = per_mj[GWP] * 1000.0                                                             # g CO2e/MJ
    out = dict(route=route, area_ha=area_ha, grown=grown, afdw=afdw, dw=dw, co2_need=co2_need, N_need=N_need, N_buy=N_buy, urea=urea, dap=dap,
               biocrude=biocrude, prod=prod, mj=mj, fuel_mj=fuel_mj, ldeq=ldeq, glyc_kg=glyc_kg, heat_dem=heat_dem, heat_net=heat_net, el=el,
               el_dem=el_dem, lip=lip, extract_ret=extract_ret, ad_feed=resid, N_rec=N_rec, el_import=el_import, el_export=el_export, chp_el=credit_el, water_m3=water_m3, h2=h2, inv=inv,
               capf=capf, capi=capi, inst=inst_f + inst_c, fci=fci, tci=tci, wc=wc, cost=cost, opex=opex, rev_co=rev_co, staff=staff,
               imp=imp, imp_fuel=imp_fuel, contrib=contrib, per_mj=per_mj, gwp=gwp, f_fuel=f_fuel)
    fin = finance(P, D, out)
    out.update(fin)
    out["mbsp"] = mbsp(P, D, out)
    p_dsl = g("p_diesel") / MJ_PER_LDEQ
    dg = g("diesel_cmp") - gwp
    out["saving"] = dg / g("diesel_cmp")
    out["abatement"] = (out["mfsp_mj"] - p_dsl) / (dg / 1e6) if out["saving"] >= 0.01 else np.nan   # not meaningful below 1% saving        # USD/t CO2e (Eq. 36)
    out["land_m2_per_GJ"] = area_ha * 1.25 * 1e4 / (fuel_mj / 1000.0) if fuel_mj > 0 else np.nan
    out["water_L_per_MJ"] = water_m3 * 1000.0 / fuel_mj if fuel_mj > 0 else np.nan
    return out

def mbsp(P, D, o):
    """Farm-only minimum biomass selling price, USD/t AFDW (annuity method, Eq. 37) for validation against NREL."""
    g = P.get; r = g("r"); n = g("life"); crf = r * (1 + r) ** n / ((1 + r) ** n - 1)
    farm_tci = sum(o["capf"].values()) * g("tci_farm") * (1 + g("wc"))
    farm_el = sum(o["el"][k] for k in ("mixing", "dewatering", "water", "co2_delivery")) * g("p_el")
    farm_op = (farm_el + o["cost"]["Nutrients"] + o["cost"]["Water"] + o["cost"]["Land lease"] + o["cost"]["Typhoon repairs (expected)"]
               + 100.0 * (o["area_ha"] * ACRE_PER_HA / 5000.0) ** 0.5 * (0.85 * g("w_op") + 0.15 * g("w_eng"))
               + g("maint") * sum(o["capf"].values()) + g("ins_tax") * farm_tci)
    return (farm_tci * crf + farm_op) / o["afdw"]

def tax_nolco(taxable, opyr, ith, rate, carry_yrs, ith_loss_carry=False):
    """Corporate income tax with loss vintages (NOLCO). Losses carry forward FIFO and expire after carry_yrs.
    NIRC s.34(D)(3): a loss incurred while exempt (ITH) is not deductible -> dropped, unless ith_loss_carry (FIRB enhanced-NOLCO
    reading: usable within carry_yrs after the last ITH year). opyr = operating year index (<= 0 during construction)."""
    tax = np.zeros(len(taxable)); vint = []                      # [expiry year, remaining loss]
    for i, (ti, y) in enumerate(zip(taxable, opyr)):
        if y <= 0: continue
        vint = [v for v in vint if y <= v[0]]
        if ti < 0:
            if y > ith: vint.append([y + carry_yrs, -ti])
            elif ith_loss_carry: vint.append([ith + carry_yrs, -ti])
            continue
        if y <= ith: continue                                     # exempt year: income untaxed, carried losses untouched
        for v in vint:
            use = min(v[1], ti); v[1] -= use; ti -= use
            if ti <= 0: break
        vint = [v for v in vint if v[1] > 0]
        tax[i] = rate * ti
    return tax

def cashflows(P, D, o, price_mj):
    """Real, unlevered cash flows; years -2..life (Eq. 32-34)."""
    g = P.get; life = int(round(g("life"))); n = life + 3
    yrs = np.arange(-2, life + 1)
    capex = np.zeros(n); capex[0:3] = o["fci"] * np.array([0.08, 0.60, 0.32])
    wc = np.zeros(n); wc[2] = o["wc"]; wc[-1] = -o["wc"]
    op = np.zeros(n); op[3:] = 1.0; op[3] = 0.75                                            # start-up year at 75%
    rev = op * (o["fuel_mj"] * price_mj + o["rev_co"])
    var = op * o["opex"]
    ebitda = rev - var
    dep = np.zeros(n); nd = int(round(g("dep_yr"))); dep[3:3 + nd] = o["fci"] / nd
    taxable = ebitda - dep
    ith = int(round(g("ith"))) if D.get("ith", True) else 0
    tax = tax_nolco(taxable, yrs, ith, g("tax"), int(round(g("nolco_yr"))), D.get("ith_loss_carry", False))
    cf = ebitda - tax - capex - wc
    return yrs, cf, dict(rev=rev, opex=var, ebitda=ebitda, dep=dep, tax=tax, capex=capex, wc=wc, cf=cf)

def npv(P, D, o, price_mj, r=None):
    r = P["r"] if r is None else r
    yrs, cf, _ = cashflows(P, D, o, price_mj)
    return float(np.sum(cf / (1 + r) ** yrs))

def finance(P, D, o):
    if o["fuel_mj"] <= 0: return dict(mfsp_mj=np.nan, mfsp_ldeq=np.nan, npv=np.nan, irr=np.nan, payback=np.nan, price_mj=np.nan)
    lo, hi = -0.5, 2.0
    flo, fhi = npv(P, D, o, lo), npv(P, D, o, hi)
    while fhi < 0: hi *= 2; fhi = npv(P, D, o, hi)
    for _ in range(60):                                                                     # bisection for NPV = 0 (Eq. 35)
        mid = 0.5 * (lo + hi); fm = npv(P, D, o, mid)
        if fm > 0: hi = mid
        else: lo = mid
        if hi - lo < 1e-7: break
    mfsp = 0.5 * (lo + hi)
    price = D.get("price_mj", P["p_cme"] / (RHO["fame"] * LHV["fame"]))                   # benchmark: CME per MJ
    v = npv(P, D, o, price)
    yrs, cf, det = cashflows(P, D, o, price)
    irr = _irr(yrs, cf)
    cum = np.cumsum(cf); pb = np.nan
    idx = np.where(cum >= 0)[0]
    if len(idx): pb = float(yrs[idx[0]])
    return dict(mfsp_mj=mfsp, mfsp_ldeq=mfsp * MJ_PER_LDEQ, mfsp_gj=mfsp * 1000, npv=v, irr=irr, payback=pb, price_mj=price, cf_years=yrs, cf=cf, cf_detail=det)

def _irr(yrs, cf):
    f = lambda r: np.sum(cf / (1 + r) ** yrs)
    lo, hi = -0.9, 3.0
    if f(lo) * f(hi) > 0: return np.nan
    for _ in range(80):
        m = 0.5 * (lo + hi)
        if f(lo) * f(m) <= 0: hi = m
        else: lo = m
    return 0.5 * (lo + hi)

BASE_HTL = dict(route="HTL", area_ha=400.0, lined=False, co2="flue", nutr="fert", aq="recycle", upgrade="onsite", heat="fossil", elec="grid", alloc="energy")
BASE_FAME = dict(route="FAME", area_ha=400.0, lined=False, co2="flue", nutr="fert", glyc="crude", heat="fossil", elec="grid", alloc="energy")

if __name__ == "__main__":
    import time
    P = dict(REG.BASE)
    for D in (BASE_HTL, BASE_FAME):
        t = time.time(); o = evaluate(P, D); dt = time.time() - t
        print(D["route"], f"{dt*1000:.1f} ms")
        print(f"  AFDW {o['afdw']:,.0f} t/yr  fuel {o['ldeq']/1e6:.2f} ML deq/yr  TCI ${o['tci']/1e6:.1f}M  opex ${o['opex']/1e6:.1f}M/yr  co-rev ${o['rev_co']/1e6:.2f}M")
        print(f"  MBSP {o['mbsp']:.0f} USD/t  contrib", {k: round(v,1) for k,v in o["contrib"].items()})
        print(f"  MFSP {o['mfsp_ldeq']:.2f} USD/Ldeq ({o['mfsp_gj']:.1f} USD/GJ)  NPV@CME ${o['npv']/1e6:.1f}M  IRR {o['irr']}  GWP {o['gwp']:.1f} g/MJ  saving {o['saving']*100:.0f}%  abatement {o['abatement']:.0f} USD/t")
        print("  el kWh:", {k: f"{v/1e6:.2f}GWh" for k, v in o['el'].items()}, "import", f"{o['el_import']/1e6:.1f}", "export", f"{o['el_export']/1e6:.1f}")
        print("  heat net TJ", o['heat_net']/1e6, " cost:", {k: round(v/1e6, 2) for k, v in o['cost'].items()})
        print("  capex:", {k: round(v/1e6, 1) for k, v in {**o['capf'], **o['capi']}.items()}, "staff", round(o['staff']))
