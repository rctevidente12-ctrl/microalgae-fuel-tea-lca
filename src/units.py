"""Units of the 183 LCIA indicators (per functional unit), by method and indicator name.
Units follow the method documentation as implemented in the openLCA ecoinvent LCIA package used to build the CF matrix
(ReCiPe 2016 v1.1 H; ReCiPe 2008 'ei' midpoints; CML-IA baseline / non-baseline 4.8; EF 3.0 (adapted); USEtox 2; CED; AWARE; IPCC)."""
import ei

def unit(method, name):
    n = name.lower()
    if method == "Environmental Prices": return "EUR2015"
    if method.startswith("Cumulative Energy Demand"): return "MJ"
    if method.startswith("IPCC"): return "kg CO2 eq"
    if method == "AWARE": return "m3 world eq deprived"
    if method.startswith("USEtox"): return "CTUh" if "human" in n else "CTUe"
    if method == "ReCiPe 2016 Midpoint (H)":
        M = {"land use": "m2a crop eq", "ionizing radiation": "kBq Co-60 eq", "ozone formation": "kg NOx eq", "terrestrial acidification": "kg SO2 eq",
             "stratospheric ozone": "kg CFC-11 eq", "fossil resource": "kg oil eq", "marine eutrophication": "kg N eq", "freshwater eutrophication": "kg P eq",
             "fine particulate": "kg PM2.5 eq", "water consumption": "m3", "global warming": "kg CO2 eq", "mineral resource": "kg Cu eq"}
        for k, v in M.items():
            if n.startswith(k): return v
        return "kg 1,4-DCB"                                      # toxicity and ecotoxicity
    if method == "ReCiPe 2016 Endpoint (H)":
        if "resource" in n: return "USD2013"
        if any(s in n for s in ("human", "fine particulate", "ionizing", "stratospheric")): return "DALY"
        return "species.yr"
    if method == "ei -  ReCiPe Midpoint (H)":
        M = {"NLTP": "m2", "ULOP": "m2a", "ALOP": "m2a", "FEP": "kg P eq", "MEP": "kg N eq", "ODP": "kg CFC-11 eq", "IRP": "kg U235 eq", "WDP": "m3", "MDP": "kg Fe eq",
             "POFP": "kg NMVOC", "FDP": "kg oil eq", "TAP": "kg SO2 eq", "PMFP": "kg PM10 eq", "GWP": "kg CO2 eq"}
        for k, v in M.items():
            if k in name: return v
        return "kg 1,4-DCB eq"                                   # HTP, METP, TETP, FETP
    if method.startswith("CML-IA"):
        if "photochem" in n: return "kg C2H4 eq"
        if "ozone layer" in n: return "kg CFC-11 eq"
        if "global warming" in n: return "kg CO2 eq"
        if "abiotic depletion (fossil" in n: return "MJ"
        if "abiotic depletion" in n: return "kg Sb eq"
        if "acidification" in n: return "kg SO2 eq"
        if "eutrophication" in n: return "kg PO4--- eq"
        if "malodorous" in n: return "m3 air"
        if "land competition" in n: return "m2a"
        if "ionising" in n: return "DALYs"
        return "kg 1,4-DB eq"                                    # toxicity and ecotoxicity
    if method == "EF 3.0 Method (adapted)":
        if "human toxicity" in n: return "CTUh"
        if "ecotoxicity" in n: return "CTUe"
        M = {"photochemical": "kg NMVOC eq", "climate change": "kg CO2 eq", "ionising": "kBq U-235 eq", "resource use, fossils": "MJ",
             "eutrophication, marine": "kg N eq", "eutrophication, terrestrial": "mol N eq", "eutrophication, freshwater": "kg P eq",
             "resource use, minerals": "kg Sb eq", "ozone depletion": "kg CFC-11 eq", "land use": "Pt (dimensionless)", "particulate": "disease incidence",
             "water use": "m3 world eq deprived", "acidification": "mol H+ eq"}
        for k, v in M.items():
            if n.startswith(k): return v
    raise KeyError((method, name))

UNITS = [unit(c[0], c[1]) for c in ei.cats]

if __name__ == "__main__":
    import collections
    print(len(UNITS), collections.Counter(UNITS).most_common())
