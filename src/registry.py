"""Parameter registry. Every model input: base, low, high, distribution, confidence (A-D, pedigree-style), sources, notes.
Currency: USD (2026). PHP converted at FX = 60.75 PHP/USD (2026 YTD average). Capital in source-year USD escalated with CEPCI.
Confidence: A = measured at scale / official; B = peer-reviewed or reputable secondary; C = estimate, older or derived; D = weak / assumption."""
FX = 60.75  # PHP per USD, 2026 YTD average (psl2026)
CEPCI = {2005: 468.2, 2007: 525.4, 2010: 550.8, 2011: 585.7, 2014: 576.1, 2016: 541.7, 2017: 567.5, 2018: 603.1, 2019: 607.5,
         2020: 596.2, 2021: 708.8, 2022: 816.0, 2023: 797.9, 2025: 813.0}

R = []
def p(key, name, group, unit, base, low=None, high=None, dist="tri", conf="C", src=(), note="", use="TEA+LCA"):
    R.append(dict(key=key, name=name, group=group, unit=unit, base=base, low=base if low is None else low,
                  high=base if high is None else high, dist=dist if low is not None else "fixed", conf=conf, src=list(src), note=note, use=use))

# ---------------- CULTIVATION
G = "1 Cultivation"
p("prod", "Areal productivity, annual average", G, "g AFDW m-2 d-1", 20.0, 10.0, 30.0, "tri", "B",
  ["klein2024", "davislaurens2020", "davis2016", "lundquist2010", "huntley2015", "jo2020"],
  "Measured SOT 16.7 (AzCATI, 2023), design target 25, Lundquist 20, Hawaii 20.5. Tropical site has no winter trough; monsoon cloud cover lowers the summer peak. Shula's design implies 772-2,008.")
p("avail", "Cultivation on-stream factor (crashes, maintenance)", G, "-", 0.90, 0.85, 0.95, "tri", "C", ["davis2016", "mcgowen2023"], "NREL design 90% (330 d/yr); AzCATI crash MTTF 13-62 d in summer.")
p("harv_rec", "Harvest and dewatering biomass recovery", G, "-", 0.95, 0.90, 0.98, "tri", "B", ["davis2012", "davis2016"], "Settler-membrane-centrifuge train.")
p("ash", "Ash content of harvested biomass", G, "kg/kg DW", 0.13, 0.05, 0.20, "tri", "C", ["jones2014", "davis2016"], "Generic design value; no C. vulgaris wastewater value found.")
p("lipid", "Lipid content (extractable, AFDW)", G, "kg/kg AFDW", 0.20, 0.15, 0.27, "tri", "B", ["esteves2022", "safafar2016", "davis2016", "lundquist2010"], "Wastewater-grown C. vulgaris 15.8%; lipid-route designs assume 25-27%.")
p("Nfrac", "Biomass nitrogen content", G, "kg N/kg AFDW", 0.065, 0.048, 0.075, "tri", "C", ["chisti2007", "jones2014", "safafar2016"], "Chisti formula CO0.48H1.83N0.11P0.01 gives 6.6%.")
p("Pfrac", "Biomass phosphorus content", G, "kg P/kg AFDW", 0.010, 0.004, 0.013, "tri", "C", ["chisti2007", "davis2012"])
p("co2_fix", "CO2 fixed per kg biomass", G, "kg CO2/kg AFDW", 1.83, 1.80, 1.90, "tri", "B", ["chisti2007"])
p("co2_util", "CO2 utilisation in pond (flue-gas sparging)", G, "-", 0.66, 0.30, 0.90, "tri", "B", ["degodos2014", "eustance2020", "klein2023"], "Measured 66% of supplied C fixed with flue gas in a 100 m2 raceway; sparging 30-50%, membranes 54-79%; NREL assumes 90%.")
p("nut_eff", "Nutrient uptake efficiency", G, "-", 0.90, 0.75, 0.95, "tri", "C", ["davis2012"])
p("mix_kwh", "Paddlewheel mixing electricity", G, "kWh ha-1 d-1", 48.0, 24.0, 100.0, "tri", "A", ["davis2012", "pegallapati2015", "davis2016"])
p("dew_kwh", "Harvest + dewatering electricity", G, "kWh/t AFDW", 150.0, 80.0, 300.0, "tri", "C", ["davis2012", "deconinck2018", "clippinger2019"], "Calibrated so total farm power ~ NREL design 406 kWh/t (77.2 GWh/190 kt).")
p("circ_kwh", "Water circulation and make-up pumping", G, "kWh/t AFDW", 50.0, 25.0, 100.0, "tri", "C", ["clippinger2019"])
p("co2_kwh", "Flue-gas CO2 delivery electricity", G, "kWh/t CO2", 22.0, 5.6, 147.0, "tri", "B", ["zheng2016"], "80 MJ/t (direct sparging); 20-530 MJ/t range.")
p("makeup_mm", "Net make-up water (evaporation minus rainfall)", G, "mm/d", 0.9, 0.4, 3.0, "tri", "C", ["davis2016", "klein2023", "pagasa_dgte"], "NREL Gulf Coast design 0.87 mm/d, Florida 0.4 mm/d; Dumaguete rainfall 3.6 mm/d (PAGASA); upper bound covers the Feb-May dry season.")
p("n2o_frac", "Pond N2O-N emission per N supplied", G, "kg N2O-N/kg N", 0.001, 0.00003, 0.0045, "tri", "B", ["plouviez2017", "fagerstone2011", "guieysse2013"], "0.1-0.4% (synthetic media), 0.04-0.45% (wastewater HRAP), 0.003% oxic lab ponds.")
p("depth", "Pond depth", G, "m", 0.20, 0.10, 0.30, "tri", "A", ["davislaurens2020", "lundquist2010"], use="LCA")
p("earth_m3", "Earthworks per hectare of pond", G, "m3/ha", 1500.0, 1000.0, 3000.0, "tri", "C", ["davis2016"], "Derived: 15 cm overburden stripped, berms 61 cm, cut-and-fill; plus 30 m3/ha concrete and 253 m2/ha liner on turns.", use="LCA")
p("ww_N_kgd", "Municipal wastewater N available (San Carlos City)", G, "kg N/d", 400.0, 150.0, 800.0, "tri", "D", ["venckus2017"], "~10,000 m3/d at 40 mg N/L; scenario option only.")

# ---------------- CONVERSION: lipid (FAME) route
G = "2 Conversion: lipid/FAME"
p("ext_eff", "Wet hexane lipid extraction recovery", G, "-", 0.855, 0.75, 0.95, "tri", "A", ["davis2012", "davis2020"], "Harmonised 85.5%; fractionation design 95%.")
p("fame_frac", "FAME per unit extracted lipid", G, "-", 0.60, 0.31, 0.93, "tri", "B", ["laurens2012", "davis2014"], "C. vulgaris FAME/extract 30.9% (N-replete) to 93.3% (N-deplete); wastewater biomass is nutrient-replete.")
p("tx_conv", "Transesterification conversion", G, "-", 0.98, 0.95, 0.99, "tri", "B", ["freedman1984"])
p("ext_heat", "Extraction heat", G, "MJ/kg oil", 11.1, 5.0, 16.1, "tri", "C", ["davis2012"], "3.1 kWh/kg oil.")
p("ext_el", "Extraction electricity", G, "kWh/kg oil", 0.069, 0.05, 0.54, "tri", "C", ["davis2012"])
p("hex_loss", "Hexane make-up", G, "kg/t oil", 3.0, 1.0, 10.0, "tri", "D", ["davis2020"], ">99.7% recovery.")
p("meoh_bd", "Methanol use", G, "kg/t biodiesel", 110.0, 100.0, 130.0, "tri", "A", ["pradhan2012"])
p("cat_bd", "Catalyst (NaOH-equivalent) use", G, "kg/t biodiesel", 2.3, 2.0, 10.0, "tri", "B", ["pradhan2012"], "Algal FFA raise catalyst/soap; upper bound covers acid pre-esterification.")
p("acid_bd", "Neutralisation acid (H3PO4-equivalent)", G, "kg/t biodiesel", 0.6, 0.5, 3.0, "tri", "B", ["pradhan2012"])
p("steam_bd", "Transesterification heat", G, "MJ/t biodiesel", 300.0, 250.0, 500.0, "tri", "A", ["pradhan2012"], "141 kg steam/t at ~2.1 MJ/kg.")
p("el_bd", "Transesterification electricity", G, "kWh/t biodiesel", 51.0, 40.0, 70.0, "tri", "A", ["pradhan2012"])
p("glyc_yield", "Crude glycerol per biodiesel", G, "kg/kg", 0.10, 0.09, 0.11, "tri", "B", ["haas2006"])
p("ad_ch4", "AD methane yield, residual biomass", G, "m3 CH4/kg VS", 0.212, 0.14, 0.30, "tri", "B", ["ramos2014", "bohutskyi2015", "davis2012"])
p("chp_el", "Biogas CHP electrical efficiency", G, "-", 0.35, 0.30, 0.40, "tri", "C", ["davis2012"])
p("chp_th", "Biogas CHP useful heat efficiency", G, "-", 0.40, 0.30, 0.45, "tri", "C", ["davis2012"])
p("ch4_leak", "AD/CHP methane slip", G, "-", 0.02, 0.01, 0.05, "tri", "C", ["frank2013"])
p("dig_Nrec", "Digestate N recycled to ponds", G, "-", 0.50, 0.30, 0.75, "tri", "C", ["davis2012"])

# ---------------- CONVERSION: HTL route
G = "3 Conversion: HTL + upgrading"
p("htl_y", "HTL biocrude yield", G, "kg/kg AFDW", 0.41, 0.33, 0.59, "tri", "A", ["jones2014", "zhu2023"], "Chlorella run 41% AFDW at 348 C; design 59%; 2022 SOT 33%.")
p("htl_gas", "HTL gas yield", G, "kg/kg dry", 0.04, 0.01, 0.12, "tri", "C", ["jones2014", "zhu2023"])
p("htl_solids", "HTL feed solids", G, "kg/kg slurry", 0.20, 0.15, 0.25, "tri", "A", ["jones2014", "zhu2023"])
p("htl_hr", "HTL feed-effluent heat recovery", G, "-", 0.80, 0.70, 0.90, "tri", "B", ["anastasakis2018", "frank2013", "ong2018"], "Continuous pilot ~75% (80% at steady state); LCA design epsilon 0.85. Resulting trim heat 1.2 MJ/kg dry vs 1.5-2.0 in pilot and pinch studies.")
p("htl_dT", "HTL heating range (30 to 350 C)", G, "K", 320.0, 300.0, 330.0, "tri", "A", ["jones2014"])
p("htl_pump", "HTL slurry pump electricity", G, "kWh/m3 slurry", 8.0, 6.0, 11.0, "tri", "C", [], "V dP / eta at 20.9 MPa, eta 0.7 (derived).")
p("aq_Nfrac", "Feed N reporting to HTL aqueous phase", G, "-", 0.70, 0.50, 0.80, "tri", "C", ["jones2014", "zhu2019"])
p("aq_Nrec", "Aqueous-phase N recovered when recycled", G, "-", 0.60, 0.30, 0.80, "tri", "C", ["zhu2019"])
p("ht_h2", "Hydrotreating H2 consumption", G, "kg H2/kg biocrude", 0.043, 0.035, 0.07, "tri", "A", ["jones2014", "zhu2023"])
p("ht_y", "Upgraded fuel yield", G, "kg/kg biocrude", 0.78, 0.72, 0.85, "tri", "A", ["jones2014", "zhu2023"])
p("diesel_frac", "Diesel-range share of upgraded fuel", G, "-", 0.83, 0.62, 0.85, "tri", "A", ["jones2014", "zhu2023"], "Remainder naphtha.")
p("ht_el", "Upgrading electricity", G, "kWh/kg fuel", 0.10, 0.05, 0.20, "tri", "C", ["zhu2020"])

# ---------------- ENERGY CARRIERS & EMISSION FACTORS
G = "4 Energy & emission factors"
p("ef_grid", "Grid electricity GWP, Visayas 2024", G, "kg CO2e/kWh", 1.137, 0.955, 1.335, "tri", "B", ["evidente2026grid"], "Companion ph-grid model (manuscript under review; not independently verifiable from this package), IPCC 2021 GWP100, low-voltage mix used as a conservative proxy for the higher-voltage supply priced in the TEA (includes distribution losses); 95% interval.", use="LCA")
p("ef_heat_fossil", "Fossil process heat GWP (natural-gas/LPG furnace)", G, "kg CO2e/MJ", 0.0742, 0.065, 0.090, "tri", "B", ["ecoinvent312"], "Hybrid: GWP set to an LPG/natural-gas furnace factor; the other 182 indicators come from the ecoinvent natural-gas industrial furnace dataset.", use="LCA")
p("ef_bio_el", "Biomass (bagasse CHP) electricity GWP, delivered", G, "kg CO2e/kWh", 0.054, 0.022, 0.08, "tri", "B", ["ecoinvent312", "evidente2026grid"], "ecoinvent 3.12 bagasse CHP 0.020-0.048 kg/kWh, / (1-0.107) T&D losses.", use="LCA")
p("ef_pv_el", "Solar PV electricity GWP, delivered", G, "kg CO2e/kWh", 0.070, 0.045, 0.107, "tri", "B", ["ecoinvent312"], "ecoinvent 3.12 open-ground PV AU 0.062 kg/kWh / (1-0.107). PV only: battery manufacture, storage losses and backup supply are not included, so S28 is a PV-electricity LCA, not a full solar-plus-BESS LCA.", use="LCA")
p("ef_h2", "Grey hydrogen GWP", G, "kg CO2e/kg H2", 9.53, 9.0, 13.0, "tri", "B", ["ecoinvent312"], "Proxy: ecoinvent 3.12 RoW market for hydrogen, low pressure (other indicators from that dataset); the TEA prices on-site LPG reforming. Range covers SMR on natural gas to LPG.", use="LCA")
p("comb_nonco2", "Fuel combustion CH4+N2O", G, "g CO2e/MJ", 0.5, 0.2, 1.0, "tri", "C", ["pegallapati2015"], use="LCA")
p("diesel_cmp", "Fossil diesel comparator (well-to-wheel)", G, "g CO2e/MJ", 94.0, 83.8, 95.7, "tri", "A", ["red2", "magadia2025", "pegallapati2015"], use="LCA")

# ---------------- PRICES (USD 2026)
G = "5 Prices (USD 2026)"
p("fx", "Exchange rate", G, "PHP/USD", FX, 57.42, 63.21, "tri", "B", ["psl2026"])
p("p_diesel", "Fossil diesel, ex-tax", G, "USD/L", 1.289, 0.73, 1.50, "tri", "B", ["tribune2026a", "ra10963"], "Pump 94.40 PHP/L (Oct 2026) less 12% VAT and 6 PHP/L excise; pre-war Feb 2026 56.50 PHP/L.")
p("p_cme", "Coconut methyl ester (benchmark biodiesel)", G, "USD/L", 2.222, 1.60, 2.40, "tri", "B", ["mb2026"], "135 PHP/L, Aug 2026.")
p("p_glyc_crude", "Crude glycerol (80%)", G, "USD/kg", 0.77, 0.74, 0.83, "tri", "B", ["argus2025"], "CFR China 740-800, CIF India 780-830 USD/t (Oct 2025).")
p("p_glyc_ref", "Refined glycerol (99.7%)", G, "USD/kg", 1.185, 1.15, 1.38, "tri", "B", ["argus2025", "procres2026gly"], "FOB SE Asia bulk 1,150-1,220 USD/t; China FOB 1,383 (Aug 2026).")
p("p_meoh", "Methanol, delivered", G, "USD/t", 680.0, 350.0, 750.0, "tri", "B", ["echemi2026", "spglobal2026"], "618 USD/t CFR SE Asia + 10% delivery; pre-war 320.")
p("p_naoh", "Sodium hydroxide (100%)", G, "USD/t", 450.0, 350.0, 800.0, "tri", "C", ["intratec2026a"])
p("p_h3po4", "Phosphoric acid", G, "USD/t", 1090.0, 970.0, 1300.0, "tri", "C", ["intratec2026b"])
p("p_hexane", "Hexane", G, "USD/t", 1200.0, 1070.0, 1554.0, "tri", "B", ["imarc2026hex", "procres2026hex"], "China FOB 1,070-1,378; India 1,278-1,554 (Q2-Jul 2026).")
p("p_urea", "Urea, delivered", G, "USD/t", 469.0, 350.0, 600.0, "tri", "A", ["wb2026"], "408 USD/t (WB, Sep 2026) + 15% delivery.")
p("p_dap", "DAP, delivered", G, "USD/t", 921.0, 650.0, 1050.0, "tri", "A", ["wb2026"], "801 USD/t (WB, Sep 2026) + 15% delivery.")
p("p_co2liq", "Purchased liquid CO2", G, "USD/t", 150.0, 80.0, 250.0, "tri", "D", ["clippinger2019"], "Scenario option only.")
p("p_el", "Estimated industrial (higher-voltage) electricity tariff, NONECO", G, "USD/kWh", 0.181, 0.148, 0.23, "tri", "C", ["negrosnow2026", "noneco2021", "context2026"], "Estimate, not a quoted tariff: residential 13.96 PHP/kWh (Jul 2026) x higher-voltage/residential ratio 0.79 (NONECO Jul 2021) = 11.0 PHP/kWh.")
p("gea_bio", "Green Energy Auction biomass tariff (GEA-2 ceiling)", G, "PHP/kWh", 5.4024, 5.07, 6.27, "tri", "B", ["solarquarter2023", "matuwid2022"], "Lowest GEA-1 biomass bid 5.07 (Cotabato Sugar Central).")
p("gea_solar", "Green Energy Auction solar+BESS tariff (GEA-4 ceiling)", G, "PHP/kWh", 5.4028, 4.48, 6.00, "tri", "B", ["context2025gea"])
p("gen_vis", "Captive DU generation charge, Visayas", G, "PHP/kWh", 7.7093, 6.75, 8.5, "tri", "B", ["malaya2024rcoa"], "Replaced by the PPA price under retail competition.")
p("p_el_sell", "Electricity export price", G, "USD/kWh", 0.12, 0.08, 0.18, "tri", "C", ["context2026"])
p("p_heat", "Process heat (LPG-fired)", G, "USD/GJ", 25.0, 20.0, 35.0, "tri", "C", ["sunstar2026lpg", "philstar2026lpg"], "Derived: LPG import parity 744 USD/t (Sep 2026) = 16.2 USD/GJ + 30% terminal/distribution margin, boiler 85%.")
p("p_heat_bio", "Process heat (bagasse/cane-trash boiler)", G, "USD/GJ", 6.0, 3.0, 10.0, "tri", "C", ["irena2012", "eria2025"], "Bagasse 1.3-2.5 USD/GJ fuel (IRENA 2012); SE Asian residues 1.4-4 USD/GJ; boiler 80% + capital and O&M.")
p("p_h2", "Hydrogen, on-site small SMR on LPG", G, "USD/kg", 4.0, 2.5, 6.5, "tri", "C", ["dillich2012", "fletcher2006", "alrashed2021", "sunstar2026lpg"], "1.5 t/d forecourt SMR 1.74-3.0 USD/kg on US gas; LPG at 16 USD/GJ adds ~2 USD/kg; small conventional SMR 4.54 USD/kg.")
p("p_water", "Make-up water (bulk)", G, "USD/m3", 0.43, 0.10, 0.56, "tri", "B", ["baciwa2026", "intratec2023dm"], "BACIWA bulk 25.92 PHP/m3 excl. VAT (2026); demineralised water in PH 0.40-0.62 USD/m3.")
p("p_land", "Land cost (lease-equivalent)", G, "USD/ha/yr", 1500.0, 900.0, 3300.0, "tri", "D", ["bacolodprop2024", "ra3844"], "No published sugarcane lease in Negros; derived as 8% of agricultural land prices 0.55-2.0 M PHP/ha (2024 listings).")
p("w_op", "Operator wage (burdened)", G, "USD/yr", 7200.0, 5500.0, 9500.0, "tri", "B", ["vds2025", "psa2024ows"], "~25,000 PHP/month x 13 months x 1.35 benefits.")
p("w_eng", "Engineer/manager wage (burdened)", G, "USD/yr", 23000.0, 15000.0, 32000.0, "tri", "B", ["psa2024ows"], "~80,000 PHP/month x 13 x 1.35.")

# ---------------- CAPITAL
G = "6 Capital cost basis"
p("cap_farm_acre", "Farm installed capital (ponds, inoculum, water)", G, "USD2016/acre", 37257.0, 30000.0, 45000.0, "tri", "A", ["klein2024", "klein2023"], "(162.9+16.6+6.7) M / 5,000 acres, unlined.")
p("cap_liner_acre", "Additional cost of full liner", G, "USD2014/acre", 82000.0, 60000.0, 100000.0, "tri", "A", ["davis2016", "clippinger2019"], "Fully lined 114k vs ~32k USD/acre.")
p("cap_dew", "Dewatering + storage installed capital", G, "USD2016", 45.37e6, 40e6, 50e6, "tri", "A", ["klein2024"], "41.9 + 3.5 M at 108,862 t AFDW/yr; exponent 0.7.")
p("cap_co2", "CO2 delivery installed capital", G, "USD2016", 4.88e6, 4.0e6, 10.0e6, "tri", "A", ["klein2024"], "At ~240 kt CO2/yr; flue gas doubled for dilute gas handling.")
p("cap_htl", "HTL installed capital (excl. dryers)", G, "USD2011", 85.9e6, 70e6, 110e6, "tri", "A", ["jones2014"], "101.8 - 15.9 M at 1,339 t/d AFDW.")
p("cap_ht", "Hydrotreating + hydrocracking installed", G, "USD2011", 30.4e6, 25e6, 40e6, "tri", "A", ["jones2014"], "At 4,500 BPSD.")
p("toll", "Refinery co-processing tolling fee (incl. H2)", G, "USD/t biocrude", 150.0, 80.0, 250.0, "tri", "D", [], "Co-processing option; no published Philippine fee.")
p("cap_chg", "CHG aqueous treatment installed", G, "USD2011", 81.4e6, 70e6, 95e6, "tri", "A", ["jones2014"], "Scenario option.")
p("cap_bop_htl", "HTL steam cycle + balance of plant", G, "USD2011", 10.4e6, 8e6, 14e6, "tri", "A", ["jones2014"])
p("cap_ext", "Lipid extraction + purification installed", G, "USD2016", 23.9e6, 18e6, 30e6, "tri", "A", ["davis2020"], "At 548.2 t/d AFDW.")
p("cap_tx", "Transesterification plant (total capital)", G, "USD2005", 11.3e6, 9e6, 15e6, "tri", "B", ["haas2006"], "37.85 ML/yr; cost year assumed 2005.")
p("cap_glyc", "Glycerol refining (vacuum distillation)", G, "USD2010", 4.44e6, 3.5e6, 6.04e6, "tri", "B", ["bansod2025"], "1,000 kg/h crude glycerol; 96.9% purity.")
p("cap_ad", "Anaerobic digestion + CHP installed", G, "USD2016", 4.7e6, 3.4e6, 7.0e6, "tri", "A", ["davis2020cap"], "Residue of ~116 kt/yr algae biorefinery.")
p("exp_proc", "Scaling exponent, process units", G, "-", 0.70, 0.60, 0.80, "tri", "B", ["towler2022"])
p("exp_farm", "Scaling exponent, farm", G, "-", 0.95, 0.90, 1.00, "tri", "C", ["davis2016"], "Modular ponds; cutting 5,000 to 1,000 acres adds ~100 USD/t.")
p("loc_f", "Location factor (Philippines vs US Gulf Coast)", G, "-", 1.12, 0.85, 1.30, "tri", "B", ["towler2022"], "Proxy: Southeast Asia 1.12; no Philippines-specific factor found.")
p("tci_farm", "FCI / installed, farm", G, "-", 1.562, 1.43, 1.71, "tri", "B", ["klein2024", "klein2023"], "Derived: NREL farm TCI/installed = 388/236.4 = 1.64 (2022 SOT: 387.0/235.9); TCI includes working capital at 5% of FCI, so FCI/installed = 1.64/1.05 = 1.562. Working capital is added separately (wc).")
p("tci_conv", "FCI / installed, conversion", G, "-", 1.764, 1.55, 2.00, "tri", "A", ["jones2014"], "PNNL FCI/installed = (467.9 TCI - 22.3 working capital)/252.6 = 445.6/252.6 = 1.764. Working capital is added separately (wc).")
p("maint", "Maintenance", G, "fraction of installed/yr", 0.03, 0.02, 0.05, "tri", "C", ["jones2014", "towler2022"])
p("ins_tax", "Insurance and local taxes", G, "fraction of TCI/yr", 0.015, 0.007, 0.02, "tri", "C", ["jones2014", "gt2025"], "CREATE MORE local tax up to 2% of gross income approximated.")

# ---------------- FINANCE
G = "7 Finance & policy"
p("r", "Real discount rate", G, "-", 0.10, 0.06, 0.14, "tri", "B", ["davis2016", "jones2014", "sunstar2026"], "NREL/PNNL 10% IRR; BSP policy rate 5.00%, inflation 7.2% (Sep 2026).")
p("life", "Plant life", G, "yr", 30, 15, 30, "uni", "B", ["davis2016", "cereno2018"], "NREL/PNNL 30; original study 15.")
p("nolco_yr", "Net operating loss carry-over period (loss vintages expire after it)", G, "yr", 5, 3, 5, "uni", "A", ["firb2025", "ra8424"], "Enhanced NOLCO for registered enterprises: 5 yr (FIRB); NIRC standard 3 yr. Losses incurred during the ITH are not carried over (NIRC s.34(D)(3)).")
p("ith", "Income tax holiday", G, "yr", 6, 4, 7, "uni", "A", ["ra9367", "pwc2026"])
p("tax", "Corporate income tax (EDR regime)", G, "-", 0.20, 0.20, 0.25, "tri", "A", ["gt2025"])
p("dep_yr", "Tax depreciation period", G, "yr", 10, 5, 10, "uni", "C", ["pwc2026"])
p("wc", "Working capital", G, "fraction of FCI", 0.05, 0.03, 0.10, "tri", "B", ["jones2014"])

# ---------------- LOGISTICS
G = "8 Logistics"
p("d_road_prod", "Product road haul to depot (San Carlos-Bacolod)", G, "km", 80.0, 60.0, 120.0, "tri", "C", [], "Approximate road distance.")
p("d_sea_prod", "Product sea leg to Cebu/Batangas", G, "km", 300.0, 30.0, 700.0, "tri", "C", ["pamasahe2026"], "San Carlos-Toledo RoRo 28 km; Batangas ~650 km.")
p("d_sea_chem", "Imported chemicals sea leg", G, "km", 2500.0, 1500.0, 4000.0, "tri", "D", [], "Methanol/fertiliser from SE/NE Asia.")
p("c_road", "Road freight cost", G, "USD/t-km", 0.11, 0.08, 0.15, "tri", "B", ["suarez2022"], "9.7 US cents/t-km (2022) escalated.")
p("c_sea", "Domestic coastal tanker freight", G, "USD/t-km", 0.02, 0.01, 0.04, "tri", "C", ["jica2005", "llanto2010"], "JICA/MARINA 0.5-1.5 PHP/ton-mile (200-400 mi, 2005) escalated ~1.9x.")
p("d_co2_pipe", "Flue-gas line to San Carlos BioPower", G, "km", 2.0, 0.5, 5.0, "tri", "D", ["doe2025bio"], "Same ecozone.")
p("d_refinery", "Biocrude shipment to refinery (co-processing option)", G, "km", 750.0, 600.0, 900.0, "tri", "C", [], "San Carlos to Limay, Bataan by sea.")

# ---------------- STOCHASTIC
G = "9 Stochastic processes"
p("sig_price", "Fuel price volatility (log OU)", G, "1/sqrt(yr)", 0.25, 0.15, 0.40, "tri", "C", ["schwartz1997"], use="TEA")
p("kap_price", "Fuel price mean reversion", G, "1/yr", 0.5, 0.2, 1.0, "tri", "C", ["schwartz1997"], use="TEA")
p("cv_year", "Interannual productivity variability (CV)", G, "-", 0.07, 0.04, 0.15, "tri", "B", ["mcgowen2023"], "Between-year CV ~7% (AzCATI 2019-21).", use="TEA")
p("lam_typh", "Damaging typhoon rate at the site", G, "1/yr", 0.25, 0.10, 0.40, "tri", "D", ["cinco2016", "corporal2017", "sunstar2021odette"], "19.4 TCs/yr enter PAR, ~9 cross the Philippines; site-specific damaging rate not published (Haiyan 2013, Odette 2021 in Negros).", use="TEA")
p("typh_days", "Production days lost per typhoon", G, "d", 21.0, 10.0, 60.0, "tri", "D", ["lozada2013", "mcgowen2023"], "Proxy: ~3 weeks to reopen after Haiyan; pond re-inoculation 2-4 weeks.", use="TEA")
p("typh_cost", "Repair cost per typhoon", G, "fraction of farm capital", 0.02, 0.005, 0.05, "tri", "D", [], use="TEA")
p("season_amp", "Seasonal productivity amplitude (tropics)", G, "-", 0.16, 0.10, 0.35, "tri", "C", ["moody2014", "mcgowen2023"], "Modelled tropical min/max 0.72 (Trivandrum); Arizona summer:winter 1.9-4.2 as upper bound.", use="TEA")

P = {r["key"]: r for r in R}
BASE = {r["key"]: r["base"] for r in R}
