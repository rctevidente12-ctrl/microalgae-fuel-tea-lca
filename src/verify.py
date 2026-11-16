"""Independent verification of the inherited design (Cereno et al., 2018; Aviso et al., 2021) and its workbooks.
Every 'inherited' value is quoted with its location; every 'recomputed' value is derived here."""
FX = 60.75
# inherited values (location)
INH = dict(
    algae_in_tpd=(79.5, "MatBal 'Strm Sum' C7 (stream 1 algal biomass)"),
    algae_growth_tpd=(0.5, "Thesis App. C p.103 'Mass of Chlorella vulgaris (growth): 500 kg/day'"),
    algae_bought_kgyr=(10.0, "Thesis s.4.8.1 p.61; Financial 'Assumptions' B60 (Php 300/kg)"),
    biomass_tpd=(80.0, "MatBal 'Strm Sum' G7/I7 (streams 5, 7)"),
    ponds_thesis=(96, "Thesis Table 4-2 p.49 (96 open raceway ponds)"),
    pond_area_m2=(1079.0, "Thesis App. D Table 1 p.105 (surface area per pond)"),
    layout_pond_m2=(39831.0, "Plant Layout 'Process' C5 (cultivation ponds, total)"),
    db_biodiesel_t_ha_yr=(13.62, "MatBal 'DataB' C24 ('Chlorella vulgaris produce almost 13.62 t/ha.year biodiesel')"),
    biodiesel_tyr=(8711.5, "Financial 'Assumptions' B3"),
    lipid_in_tpd=(17.6, "MatBal 'Strm Sum' I11 (stream 7 lipids)"),
    tag_dag_out_tpd=(30.5617, "MatBal 'Strm Sum' L33:L35 (stream 10: 1,2-DG 0.722 + 1,3-DG 1.331 + TG 28.509)"),
    htl_in_tpd=(613.333, "MatBal 'Strm Sum' I47 (stream 7 total)"),
    htl_out_tpd=(8.0 + 542.652 + 30.562, "MatBal 'Strm Sum' J47+K47+L47 (gas, aqueous, oil)"),
    htl_toc_tpd=(121.063, "MatBal 'Strm Sum' K27 (stream 9 TOC)"),
    htl_q_kw=(0.0, "MatBal '(1) Cultiv - (3) Oil Extraction' S93 (Q = 0 kW)"),
    htl_el_kw=(138.16, "Thesis Table 4.4 p.62 (HTL reactor)"),
    slurry_kgh=(22222.2, "MatBal '(1) Cultiv - (3) Oil Extraction' W93 (mass flow, kg/h)"),
    press_kw=(773.33, "Thesis Table 4.4 p.62 (belt presser)"),
    press_feed_tpd=(800.0, "MatBal 'Strm Sum' G47 (stream 5, 880 t/d incl. pond water)"),
    cake_solids=(80.0 / 533.333, "MatBal 'Strm Sum' I7, I8 (stream 7: 80 t algae, 453 t water)"),
    text_moisture=(0.10, "Thesis s.4.2.1 p.45 ('reduces its water content from 90% to 10%')"),
    fame_tpd=(29.0706, "MatBal 'Strm Sum' V32"),
    meoh_fresh_tpd=(3.4977, "MatBal 'Strm Sum' M37 (stream 11)"),
    n_supplied_kgd=(148.68 * 14.007 / 62.004, "MatBal 'Strm Sum' E22 (stream 3 NO3-, as N)"),
    co2_supplied_kgd=(910.13 * 44.01 / 61.017, "MatBal 'Strm Sum' E21 (stream 3 HCO3-, as CO2)"),
    tpc_php=((468.53e6, 533.76e6, 1047.99e6), "Financial 'Cost Analysis Estimation' E5; MatBal 'Cost Analysis Estimation' E5; Financial 'TPC' C18"),
    disc=((0.12, 0.20, 0.05), "Financial 'Assumptions' B51 (12%); thesis s.7.3.1 (MARR 20%); Aviso et al. (5%)"),
    glyc_purity=((0.9264, 0.8014, 0.5779), "Thesis Table 4-4; thesis s.4.2.1; Aviso et al. Table 4"),
    bd_revenue_php=((801.06e6, 614.81e6), "Thesis Table 3.1; Aviso et al. Table 3 (both 80 t/d)"),
    noith_npv=("#ERROR!", "Financial 'Cash Flow(wo tax holiday)' C43:C46"),
    paddle_kw=(9.737, "MatBal 'O EBal' C57 (24 ponds)"),
)
def checks():
    C = []
    def add(n, qty, basis, inh, rec, verdict, sev="High"):
        C.append(dict(no=n, quantity=qty, basis=basis, inherited=inh, recomputed=rec, verdict=verdict, severity=sev))
    i = {k: v[0] for k, v in INH.items()}
    area_t = i["ponds_thesis"] * i["pond_area_m2"]
    add(1, "Origin of the algal biomass", "Mass balance: stream 1 versus growth", f"{i['algae_in_tpd']} t/d fed as 'starting culture'; growth {i['algae_growth_tpd']} t/d; {i['algae_bought_kgyr']:.0f} kg/yr bought",
        f"99.4% of the 80 t/d is an unpaid input; ponds grow 0.6%", "Fail")
    add(2, "Implied areal productivity", "80 t/d AFDW / pond area", "not stated",
        f"{80e6/area_t:,.0f} g/m2/d (96 ponds, {area_t/1e4:.2f} ha); {80e6/i['layout_pond_m2']:,.0f} g/m2/d (layout {i['layout_pond_m2']/1e4:.2f} ha); literature 10-30", "Fail")
    add(3, "Biodiesel per hectare", "Own database value x pond area", f"{i['biodiesel_tyr']:,.0f} t/yr",
        f"{i['db_biodiesel_t_ha_yr']} t/ha/yr x {area_t/1e4:.2f} ha = {i['db_biodiesel_t_ha_yr']*area_t/1e4:,.0f} t/yr ({i['biodiesel_tyr']/(i['db_biodiesel_t_ha_yr']*area_t/1e4):.0f}x lower)", "Fail")
    add(4, "HTL acylglyceride closure", "Tri- and diglycerides out <= lipid in (TG/DG cannot form from protein or carbohydrate; biocrude itself may exceed lipid mass)", f"lipid in {i['lipid_in_tpd']} t/d; TG+DG out {i['tag_dag_out_tpd']:.2f} t/d",
        f"{100*i['tag_dag_out_tpd']/i['lipid_in_tpd']:.0f}% of the lipid entering", "Fail")
    add(5, "HTL product chemistry", "HTL hydrolyses lipids; biocrude needs hydrotreating", "biocrude = 100% tri/diglycerides, transesterified to FAME",
        "biocrude is FFA, N-heterocycles, phenolics; route is hydrotreating to renewable diesel (PNNL-23227)", "Fail")
    q = i["slurry_kgh"] / 3600 * 3.8 * 320
    add(6, "HTL heat duty", "m cp dT, 30 to 350 C", f"{i['htl_q_kw']:.0f} kW", f"{q/1000:.1f} MW gross; {q*0.15/1000:.2f} MW net at 85% heat recovery", "Fail")
    pump = i["slurry_kgh"] / 1000 / 3600 * 20.9e6 / 0.7 / 1000
    add(7, "HTL slurry pumping", "V dP / eta (20.9 MPa, eta 0.7)", f"{i['htl_el_kw']} kW", f"{pump:.0f} kW", "Pass" if abs(pump / i['htl_el_kw'] - 1) < 0.4 else "Fail", "Low")
    add(8, "Carbon in HTL aqueous phase", "TOC <= carbon in feed (51.4% of AFDW)", f"{i['htl_toc_tpd']:.0f} t/d TOC", f"feed carbon {80*0.514:.1f} t/d; TOC is {i['htl_toc_tpd']/(80*0.514):.1f}x the feed carbon", "Fail")
    add(9, "HTL mass closure", "in = out", f"in {i['htl_in_tpd']:.1f}; out {i['htl_out_tpd']:.1f} t/d", f"{i['htl_in_tpd']-i['htl_out_tpd']:.1f} t/d ({100*(1-i['htl_out_tpd']/i['htl_in_tpd']):.1f}%) unaccounted", "Fail", "Medium")
    add(10, "Belt-press cake moisture", "text versus stream table", f"{100*i['text_moisture']:.0f}% moisture (text)", f"{100*(1-i['cake_solids']):.0f}% moisture in stream 7", "Fail", "Medium")
    pk = i["press_feed_tpd"] / 24 * 0.88
    add(11, "Belt-press power", "0.16-0.88 kWh/m3 x feed", f"{i['press_kw']} kW", f"<= {pk:.0f} kW at 0.88 kWh/m3 ({i['press_kw']/pk:.0f}x)", "Fail", "Medium")
    add(12, "Transesterification yield", "95% of (TG+DG), FAME/TG ~1.0", f"{i['fame_tpd']:.2f} t/d", f"{0.95*i['tag_dag_out_tpd']:.2f} t/d", "Pass", "Low")
    add(13, "Methanol make-up", "kg per t FAME vs 110 (Pradhan et al., 2012)", f"{i['meoh_fresh_tpd']*1000/i['fame_tpd']:.0f} kg/t", "100-130 kg/t", "Pass", "Low")
    nn = 80 * 0.065 * 1000
    add(14, "Nitrogen supply", "N demand = 6.5% of 80 t/d", f"{i['n_supplied_kgd']:.0f} kg N/d supplied", f"{nn:,.0f} kg N/d needed ({100*i['n_supplied_kgd']/nn:.1f}% supplied)", "Fail")
    cn = 80 * 1.83 * 1000
    add(15, "CO2 supply", "1.83 kg CO2/kg biomass", f"{i['co2_supplied_kgd']:.0f} kg CO2/d (as HCO3-)", f"{cn:,.0f} kg/d needed ({100*i['co2_supplied_kgd']/cn:.2f}% supplied)", "Fail")
    add(16, "Paddlewheel power", "Harmonised 48 kWh/ha/d (within 30%)", f"{i['paddle_kw']:.1f} kW (24 ponds)", f"{48*area_t/1e4/24:.1f} kW for {area_t/1e4:.1f} ha ({i['paddle_kw']/(48*area_t/1e4/24):.2f}x)", "Fail", "Low")
    t = i["tpc_php"]
    add(17, "Total project cost", "one value across workbooks", " / ".join(f"PHP {x/1e6:,.0f} M" for x in t), f"USD {t[0]/FX/1e6:.1f}-{t[2]/FX/1e6:.1f} M; three values, 2.2x apart", "Fail", "Medium")
    add(18, "Cash-flow treatment", "unlevered NPV", "loan and equity proceeds booked as year-0 inflows", "financing mixed with project value (also corrected in Cereno & Evidente, 2026)", "Fail", "Medium")
    d = i["disc"]
    add(19, "Discount rate", "one rate", f"{d[0]:.0%} (workbook), MARR {d[1]:.0%}, {d[2]:.0%} (2021)", "inconsistent; 10% real used here (NREL/PNNL convention)", "Fail", "Low")
    gp = i["glyc_purity"]
    add(20, "Glycerol purity and price", "one purity, price matched to purity", " / ".join(f"{x:.1%}" for x in gp), "crude glycerol sold at the refined-glycerol price (PHP 67.2/L)", "Fail", "Medium")
    br = i["bd_revenue_php"]
    add(21, "Biodiesel revenue", "same plant, same output", " vs ".join(f"PHP {x/1e6:,.0f} M" for x in br), f"{br[0]/br[1]:.2f}x apart at 80 t/d", "Fail", "Low")
    add(22, "No-tax-holiday case", "calculates", INH["noith_npv"][0], "NPV, IRR and payback cells return errors", "Fail", "Low")
    add(24, "Broken cell references", "every formula resolves", "MatBal 'Strm Sum' AG38, AQ38, AG47, AH47, AQ47; 'O EBal' AN121; 'O MatBal' BR14 (=#REF!*1000000/BQ11); Financial 'Cash Flow(wo tax holiday)' C7, D8:I8 and further rows",
        "#REF! errors: cell references lost when sheets or rows were deleted; the affected totals cannot be recalculated as built", "Fail", "Medium")
    add(23, "Fuel quality", "EN 14214 ester >= 96.5%", "99.8% FAME", "ester content meets the EN 14214 limit; full fuel-quality compliance is not shown by composition alone", "Pass", "Low")
    SRC = {1: ["algae_in_tpd", "algae_growth_tpd", "algae_bought_kgyr"], 2: ["biomass_tpd", "ponds_thesis", "pond_area_m2", "layout_pond_m2"],
           3: ["db_biodiesel_t_ha_yr", "biodiesel_tyr", "ponds_thesis", "pond_area_m2"], 4: ["lipid_in_tpd", "tag_dag_out_tpd"], 5: ["tag_dag_out_tpd", "fame_tpd"],
           6: ["htl_q_kw", "slurry_kgh"], 7: ["htl_el_kw", "slurry_kgh"], 8: ["htl_toc_tpd", "biomass_tpd"], 9: ["htl_in_tpd", "htl_out_tpd"], 10: ["text_moisture", "cake_solids"],
           11: ["press_kw", "press_feed_tpd"], 12: ["fame_tpd", "tag_dag_out_tpd"], 13: ["meoh_fresh_tpd", "fame_tpd"], 14: ["n_supplied_kgd"], 15: ["co2_supplied_kgd"],
           16: ["paddle_kw", "ponds_thesis", "pond_area_m2"], 17: ["tpc_php"], 18: [], 19: ["disc"], 20: ["glyc_purity"], 21: ["bd_revenue_php"], 22: ["noith_npv"], 23: ["fame_tpd"], 24: []}
    C.sort(key=lambda c: c["no"])
    for c in C:
        locs = [INH[k][1] for k in SRC[c["no"]]]
        if c["no"] == 24: locs = ["MatBal2020EBal.xlsx and Financial Analysis.xlsx as received (formula view)"]
        if c["no"] == 18: locs = ["Financial 'Cash Flow' sheet, year-0 rows (loan and equity proceeds); Aviso et al. (2021) cash-flow table"]
        c["source"] = "; ".join(dict.fromkeys(locs))
    return C
if __name__ == "__main__":
    cs = checks()
    for c in cs: print(c["no"], c["verdict"], c["quantity"], "|", c["inherited"], "|", c["recomputed"])
    print(sum(c["verdict"] == "Pass" for c in cs), "pass /", len(cs))
