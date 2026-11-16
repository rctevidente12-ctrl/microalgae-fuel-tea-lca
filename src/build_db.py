import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
"""Builds the single project database (.xlsx): registry, references, original data, verification, balances, LCI/LCIA,
TEA, scenarios, sensitivity, uncertainty, risk, GSA, Pareto, surrogate, logistics, and every figure with its data."""
import sys, json, numpy as np
sys.path.insert(0, ROOT + "/src")
from ctx import *
import registry as REG, ei, model
from lcimap import MAP
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
from PIL import Image as PImage

OUT = ROOT + "/out/Cereno_Evidente_2026_Microalgae_TEA_LCA_Database.xlsx"
RN = json.load(open(f"{RES}/report_numbering.json")); MN = json.load(open(f"{RES}/ms_numbering.json"))
REFCHK = json.load(open(ROOT + "/results/refs_check.json"))
HF = PatternFill("solid", fgColor="1C5CAB"); HFONT = Font(bold=True, color="FFFFFF", name="Calibri", size=10)
TFONT = Font(bold=True, size=14, name="Calibri", color="1C5CAB"); NOTE = Font(italic=True, size=9, color="52514E", name="Calibri")
LINK = Font(color="1C5CAB", underline="single", name="Calibri", size=10)
wb = Workbook(); wb.remove(wb.active)

def clean(v):
    if isinstance(v, (np.floating,)): v = float(v)
    if isinstance(v, (np.integer,)): v = int(v)
    if isinstance(v, (np.bool_,)): v = bool(v)
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))): return None
    if isinstance(v, (list, tuple, dict, np.ndarray)): return str(v if not isinstance(v, np.ndarray) else v.tolist())[:32000]
    return v

def sheet(name, title, note, head, rows, widths=None, fmt=None, start=4):
    ws = wb.create_sheet(name)
    ws["A1"] = title; ws["A1"].font = TFONT
    ws["A2"] = note; ws["A2"].font = NOTE
    ws["A3"].hyperlink = "#'00_README'!A1"; ws["A3"] = "← back to README"; ws["A3"].font = LINK
    for j, h in enumerate(head, 1):
        c = ws.cell(row=start, column=j, value=h); c.fill = HF; c.font = HFONT; c.alignment = Alignment(wrap_text=True, vertical="center")
    for i, r in enumerate(rows, start + 1):
        for j, v in enumerate(r, 1):
            c = ws.cell(row=i, column=j, value=clean(v))
            if fmt and j - 1 < len(fmt) and fmt[j - 1] and isinstance(c.value, (int, float)): c.number_format = fmt[j - 1]
    for j in range(1, len(head) + 1):
        ws.column_dimensions[get_column_letter(j)].width = (widths[j - 1] if widths and j - 1 < len(widths) else 14)
    ws.freeze_panes = ws.cell(row=start + 1, column=1)
    return ws

# ------------------------------------------------------------------ 00 README (filled at the end)
readme = wb.create_sheet("00_README")
# ------------------------------------------------------------------ 01 Registry
refkeys = {k: i for i, k in enumerate(REFS, 1)}
sheet("01_Registry", "Parameter registry", f"All {NPAR} model inputs. Confidence: A design/measured data for the same process; B published value for a related process, place or time; C derived/engineering estimate; D assumption without direct source. Sources: report reference numbers (sheet 02_References).",
      ["Key", "Parameter", "Group", "Unit", "Base", "Low", "High", "Distribution", "Confidence", "Source keys", "Report ref. no.", "Note", "Used in"],
      [[r["key"], r["name"], r["group"], r["unit"], r["base"], r["low"], r["high"], r["dist"], r["conf"], ", ".join(r["src"]), ", ".join(str(RN["refnum"].get(k, "")) for k in r["src"]), r["note"], r["use"]] for r in REG.R],
      widths=[14, 42, 26, 16, 11, 11, 11, 10, 10, 30, 12, 70, 10])
# ------------------------------------------------------------------ 02 References
ws = sheet("02_References", "References (APA 7) with DOIs", f"{len(REFS)} references. Report and manuscript numbers refer to the numbered citations in the two documents. Verification: checked against Crossref/publisher records in October 2026 (ok / fixed = corrected / unverifiable = internal or no public record).",
           ["Key", "Report no.", "Manuscript no.", "APA reference", "DOI / URL", "Verification", "Verification note"],
           [[k, RN["refnum"].get(k), MN["refnum"].get(k), a, ("https://doi.org/" + u if u.startswith("10.") else u), REFCHK.get(k, {}).get("status", "added"), REFCHK.get(k, {}).get("note", "")] for k, (a, u) in REFS.items()],
           widths=[18, 10, 12, 100, 50, 12, 60])
for i in range(5, 5 + len(REFS)):
    c = ws.cell(row=i, column=5)
    if c.value: c.hyperlink = c.value; c.font = LINK
# ------------------------------------------------------------------ 03 Original data
rows = [[k, (str(v) if isinstance(v, tuple) else v), s, "Cereno et al. (2018) thesis and workbooks"] for k, (v, s) in INH.items()]
rows += [["EgyE Alt. 1 biodiesel sales", "PHP 307,403,196", "Aviso et al. (2021) Table 6", "Aviso et al. (2021)"], ["EgyE Alt. 1 NPV", "PHP -2,025,411,686 (USD -33.3 M)", "Table 6", "Aviso et al. (2021)"], ["EgyE Alt. 1 payback / ROI / jobs", "-3.71 yr / -19.78% / 207", "Table 6", "Aviso et al. (2021)"],
         ["EgyE Alt. 2 biodiesel / glycerol sales", "PHP 614,812,406 / 8,017,387", "Table 6", "Aviso et al. (2021)"], ["EgyE Alt. 2 NPV", "PHP 668,271,436 (USD 11.0 M)", "Table 6", "Aviso et al. (2021)"], ["EgyE Alt. 2 payback / ROI / jobs", "9.35 yr / 11.04% / 209", "Table 6", "Aviso et al. (2021)"],
         ["EgyE Alt. 3 biodiesel / glycerol sales", "PHP 614,812,406 / 51,877,327", "Table 6", "Aviso et al. (2021)"], ["EgyE Alt. 3 NPV", "PHP 1,041,739,567 (USD 17.1 M)", "Table 6", "Aviso et al. (2021)"], ["EgyE Alt. 3 payback / ROI / jobs", "6.33 yr / 15.20% / 219", "Table 6", "Aviso et al. (2021)"],
         ["EgyE glycerol purity / price", "57.8% -> 99.6%; PHP 10.38 -> 67.19 per kg", "Section on glycerol purification", "Aviso et al. (2021)"], ["EgyE MADM result", "Alternative 3 has the highest weighted utility (1.0)", "Table 7", "Aviso et al. (2021)"],
         ["DIW WP volume", "8.71 million kg biodiesel = 10.01 ML/yr at 870 kg/m3", "Section 2", "Cereno & Evidente (2026)"], ["DIW WP implied price", "EUR 0.86 (PHP 61.4, USD 1.01) per litre", "Section 2", "Cereno & Evidente (2026)"],
         ["DIW WP LCOB Alt. 3", "EUR 0.67-0.74/L (USD 0.79-0.87/L) at 8%", "Table 1", "Cereno & Evidente (2026)"], ["DIW WP NPV Alt. 3", "EUR 14.0 / 7.3 M (USD 16.4 / 8.6 M); IRR 52% / 19%", "Table 1", "Cereno & Evidente (2026)"],
         ["DIW WP NPV Alt. 2", "EUR 9.7 / 3.0 M; IRR 40% / 13%; LCOB EUR 0.73-0.80/L", "Table 1", "Cereno & Evidente (2026)"], ["DIW WP tax holiday value", "EUR 2.5 M (Alt. 2), 3.4 M (Alt. 3)", "Table 1", "Cereno & Evidente (2026)"],
         ["DIW WP sensitivity", "NPV < 0 if price -22% or opex +28%", "Abstract", "Cereno & Evidente (2026)"], ["DIW WP Monte Carlo", "NPV > 0 in 88% of 20,000 draws", "Section 4", "Cereno & Evidente (2026)"], ["DIW WP FX", "EUR 1 = PHP 71.244 (ECB, 25 Sep 2026)", "Section 2", "Cereno & Evidente (2026)"]]
sheet("03_Original_Data", "Findings and inherited values of the original studies", "Values as reported, with their location in the thesis, workbooks and papers. PHP converted at 60.75 per USD where shown; EUR values of the working paper converted via PHP 71.244 per EUR.",
      ["Item", "Value", "Location", "Study"], rows, widths=[40, 60, 70, 34])
# ------------------------------------------------------------------ 04 Verification
sheet("04_Verification", "Verification of the inherited design", f"{NVER} checks recomputed from first principles; {NVER - NVFAIL} pass. Each check names the workbook sheet and cell or thesis page of the inherited value (records checked as received).", ["No.", "Quantity", "Basis", "Inherited", "Recomputed", "Verdict", "Severity", "Source (sheet, cell or page)"],
      [[c["no"], c["quantity"], c["basis"], c["inherited"], c["recomputed"], c["verdict"], c["severity"], c["source"]] for c in VER], widths=[6, 30, 36, 50, 60, 9, 9, 80])
# ------------------------------------------------------------------ 05 Validation
rows = [["Consistency check", c["route"], c["block"] + ": " + c["check"], c["engine"], c["reference"], c["unit"], c["rel_dev"], "Pass" if c["ok"] else "Fail", c["note"]] for c in CLOS]
rows += [["Benchmark", "", v["case"], v["model"], v["published"], v["unit"], v["model"] / v["published"] - 1, "", v["note"] + f" Source: {v['source']}"] for v in VAL]
sheet("05_Validation", "Engine implementation and consistency checks, and validation against published designs", f"{NCHK} implementation and consistency checks on both base designs (several reproduce definitions; they are not an element-by-element closure) and comparison with NREL, PNNL and ANL results.", ["Type", "Route", "Check / case", "Engine", "Reference", "Unit", "Relative deviation", "Result", "Note"],
      rows, widths=[11, 7, 70, 14, 14, 16, 12, 8, 70], fmt=[None, None, None, "#,##0.0000", "#,##0.0000", None, "0.00%"])
# ------------------------------------------------------------------ 06 Streams
for rt, fid in (("HTL", "F01b_pfd_htl"), ("FAME", "F01c_pfd_fame")):
    sheet(f"06_Streams_{rt}", f"Stream table, Route {'A (HTL)' if rt == 'HTL' else 'B (FAME)'}, 2026 base", "Annual flows; stream numbers as in the process flow diagram (sheet " + fid.split("_")[0] + ").",
          ["Stream", "Description", "Value", "Unit", "Note"], [[r["stream"], r["description"], r["value"], r["unit"], r.get("note", "")] for r in FIG[fid]["data"]], widths=[8, 50, 16, 14, 60], fmt=[None, None, "#,##0.###"])
# ------------------------------------------------------------------ 07 Balance
keys = [("area_ha", "Pond area", "ha"), ("grown", "Biomass grown", "t AFDW/yr"), ("afdw", "Biomass harvested", "t AFDW/yr"), ("dw", "Dry biomass incl. ash", "t/yr"), ("co2_need", "CO2 delivered", "t/yr"),
        ("N_need", "Nitrogen demand", "t N/yr"), ("N_buy", "Nitrogen purchased", "t N/yr"), ("urea", "Urea", "t/yr"), ("dap", "DAP", "t/yr"), ("biocrude", "Biocrude", "t/yr"), ("h2", "Hydrogen", "t/yr"),
        ("fuel_mj", "Fuel energy (LHV)", "MJ/yr"), ("ldeq", "Fuel output", "L diesel-eq/yr"), ("glyc_kg", "Glycerol", "kg/yr"), ("heat_dem", "Process heat demand (net of internal supply)", "MJ/yr"), ("heat_net", "Purchased heat", "MJ/yr"),
        ("el_dem", "Electricity demand", "kWh/yr"), ("el_import", "Electricity imported", "kWh/yr"), ("el_export", "Electricity exported", "kWh/yr"), ("chp_el", "CHP electricity", "kWh/yr"), ("water_m3", "Make-up water", "m3/yr"),
        ("staff", "Staff", "FTE"), ("land_m2_per_GJ", "Land occupation incl. 25% site allowance (500 ha)", "m2*yr/GJ"), ("water_L_per_MJ", "Net water", "L/MJ")]
rows = [[lab, u, H.get(k), F.get(k)] for k, lab, u in keys]
for k in sorted(set(H["prod"]) | set(F["prod"])): rows.append([f"Product: {k}", "t/yr", H["prod"].get(k, 0), F["prod"].get(k, 0)])
for k in sorted(set(H["el"]) | set(F["el"])): rows.append([f"Electricity: {k}", "kWh/yr", H["el"].get(k, 0), F["el"].get(k, 0)])
sheet("07_Balance", "Material and energy balance, 2026 base designs", "Annual totals computed by the engine (src/model.py).", ["Quantity", "Unit", "HTL", "FAME"], rows, widths=[46, 16, 18, 18], fmt=[None, None, "#,##0.00", "#,##0.00"])
# ------------------------------------------------------------------ 08 LCI
rows = []
for rt, o in (("HTL", H), ("FAME", F)):
    for k, amt in o["inv"].items():
        if k in MAP: act, loc = MAP[k]
        else: act, loc = ("", "")
        gw = float(ei.U[ei.GWP, model.COLS[k]]) if k in model.COLS else None
        rows.append([rt, k, act, loc, amt, amt / o["fuel_mj"] if o["fuel_mj"] else None, gw])
    rows.append([rt, "electricity (imported)", "Visayas low-voltage mix, ph-grid model (2024)", "PH-Visayas", o["el_import"], o["el_import"] / o["fuel_mj"], B["ef_grid"]])
    rows.append([rt, "process heat (purchased)", "heat production, natural gas, at industrial furnace >100kW (hybrid: GWP set to LPG/natural-gas furnace 0.0742 kg/MJ; other indicators natural gas)", "RoW", o["heat_net"], o["heat_net"] / o["fuel_mj"], B["ef_heat_fossil"]])
sheet("08_LCI", "Life cycle inventory: foreground flows linked to ecoinvent 3.12 cut-off", "Amounts per year and per MJ fuel; units as in ecoinvent (kg, t-km, m3, kWh, MJ). GWP unit score = cradle-to-gate IPCC 2021 GWP100 per unit.",
      ["Route", "Flow", "ecoinvent activity", "Location", "Amount per year", "Amount per MJ fuel", "GWP unit score, kg CO2e/unit"], rows, widths=[7, 24, 80, 12, 18, 18, 18], fmt=[None, None, None, None, "#,##0.0", "0.000E+00", "0.0000"])
# ------------------------------------------------------------------ 09 LCIA
from units import UNITS
rows = [[c[0], c[1], UNITS[i] + " per MJ fuel", H["per_mj"][i], F["per_mj"][i]] for i, c in enumerate(ei.cats)]
sheet("09_LCIA", "Life cycle impact assessment: all 183 indicators per MJ fuel (2026 base, energy allocation)", "Method, indicator and unit (per MJ fuel) as in the LCIA implementation used (openLCA ecoinvent LCIA package mapped to ecoinvent 3.12 flows; EF 3.0 adapted, ReCiPe 2016 H and ReCiPe 2008 H, CML-IA 4.8, USEtox 2, CED, AWARE, IPCC). Background vectors only; direct foreground emissions are added to climate change (IPCC 2021 GWP100, last row, kg CO2e/MJ).",
      ["Method", "Indicator", "Unit", "HTL per MJ", "FAME per MJ"], rows, widths=[40, 60, 20, 16, 16], fmt=[None, None, None, "0.000E+00", "0.000E+00"])
# ------------------------------------------------------------------ 10-12 TEA
rows = [["HTL", "Farm", k, v] for k, v in H["capf"].items()] + [["HTL", "Conversion", k, v] for k, v in H["capi"].items()] + [["FAME", "Farm", k, v] for k, v in F["capf"].items()] + [["FAME", "Conversion", k, v] for k, v in F["capi"].items()]
rows += [["HTL", "Total", "Installed cost", H["inst"]], ["HTL", "Total", "Fixed capital investment", H["fci"]], ["HTL", "Total", "Working capital", H["wc"]], ["HTL", "Total", "Total capital investment", H["tci"]],
         ["FAME", "Total", "Installed cost", F["inst"]], ["FAME", "Total", "Fixed capital investment", F["fci"]], ["FAME", "Total", "Working capital", F["wc"]], ["FAME", "Total", "Total capital investment", F["tci"]]]
sheet("10_TEA_Capital", "Capital cost (USD 2025, CEPCI 813, location factor 1.12)", f"Installed costs by area; FCI = installed x {B['tci_farm']} (farm; NREL 1.64 TCI/installed without 5% WC) / {B['tci_conv']} (conversion; PNNL (467.9-22.3)/252.6); WC = 5% FCI added once. Capital in USD 2025; operating costs at 2026 prices (mixed basis, no escalation).", ["Route", "Section", "Item", "USD"], rows, widths=[8, 12, 40, 18], fmt=[None, None, None, "#,##0"])
rows = [[k, H["cost"].get(k, 0), F["cost"].get(k, 0)] for k in H["cost"]] + [["Total operating cost", H["opex"], F["opex"]], ["Co-product revenue", H["rev_co"], F["rev_co"]], ["MFSP, USD/L diesel-eq", H["mfsp_ldeq"], F["mfsp_ldeq"]], ["MFSP, USD/GJ", H["mfsp_gj"], F["mfsp_gj"]],
                                                                       ["MBSP, USD/t AFDW", H["mbsp"], F["mbsp"]], ["NPV at CME price, USD", H["npv"], F["npv"]], ["IRR at CME price", H["irr"], F["irr"]]]
sheet("11_TEA_Opex", "Operating cost and economic results (USD per year)", "Base designs, 2026 prices; MFSP and NPV combine USD 2025 capital and 2026 operating prices (mixed basis).", ["Item", "HTL", "FAME"], rows, widths=[36, 18, 18], fmt=[None, "#,##0.00", "#,##0.00"])
rows = []
for rt, o in (("HTL", H), ("FAME", F)):
    cd = o["cf_detail"]
    for i, y in enumerate(o["cf_years"]): rows.append([rt, int(y)] + [float(cd[k][i]) for k in ("rev", "opex", "ebitda", "dep", "tax", "capex", "wc", "cf")])
sheet("12_Cashflow", "Annual cash flows at the CME benchmark price (real USD 2026)", "Construction years -2..0; start-up year 1 at 75%; 6-year income-tax holiday; 10-year straight-line depreciation. Cash flows at the MFSP are computed in the same way with price = MFSP.",
      ["Route", "Year", "Revenue", "Operating cost", "EBITDA", "Depreciation", "Tax", "Capital expenditure", "Working capital", "Net cash flow"], rows, widths=[8, 8] + [16] * 8, fmt=[None, None] + ["#,##0"] * 8)
# ------------------------------------------------------------------ 13 Scenarios
rows = []
for sid in sorted(S):
    s = S[sid]; df = SDEF[sid]
    rows.append([sid, df["group"], df["name"], json.dumps(df["D"]), json.dumps({k: float(v) for k, v in df["P"].items()}), str(df.get("pros") or ""), s["mfsp_ldeq"], s["mfsp_gj"], s["gwp"], s["saving"], s["tci"], s["opex"], s["ldeq"], s["npv"], s["irr"], s["area_ha"], s["el_dem"], s["mbsp"]])
sheet("13_Scenarios", "Sixty scenarios, each recalculated in full", "MFSP in USD/L diesel-eq and USD/GJ; GWP g CO2e/MJ; TCI and opex USD; output L deq/yr; NPV at CME price (USD).", ["ID", "Group", "Scenario", "Design switches", "Parameter overrides", "Prospective", "MFSP USD/Ldeq", "MFSP USD/GJ", "GWP g/MJ", "GHG saving", "TCI USD", "Opex USD/yr", "Output Ldeq/yr", "NPV USD", "IRR", "Area ha", "Electricity kWh/yr", "MBSP USD/t"],
      rows, widths=[6, 14, 50, 50, 30, 16, 12, 12, 10, 10, 14, 14, 14, 14, 8, 10, 14, 12], fmt=[None] * 6 + ["0.000", "0.0", "0.00", "0.0%", "#,##0", "#,##0", "#,##0", "#,##0", "0.0%", "#,##0", "#,##0", "#,##0"])
sheet("14_Bridge", "Bridge from the reported cost to the corrected design (HTL, 24,000 t AFDW/yr)", "Each step changes one thing.", ["Step", "MFSP USD/Ldeq", "GWP g/MJ", "Pond area ha", "Output Ldeq/yr", "TCI USD", "NPV USD"],
      [[b["step"], b["mfsp"], b["gwp"], b["area"], b["out"], b["tci"], b.get("npv")] for b in BR], widths=[90, 12, 10, 12, 16, 16, 16], fmt=[None, "0.000", "0.0", "#,##0.0", "#,##0", "#,##0", "#,##0"])
sheet("15_OAT_Tornado", "One-at-a-time sensitivity (registry low/high)", "Outputs at the low and high value of each parameter, others at base.", ["Route", "Key", "Parameter", "Group", "Low", "Base", "High", "MFSP @low", "MFSP @high", "MFSP swing", "GWP @low", "GWP @high", "GWP swing", "NPV @low", "NPV @high"],
      [[o["route"], o["key"], o["name"], o["group"], o["low"], o["base"], o["high"], o["mfsp_lo"], o["mfsp_hi"], o["mfsp_swing"], o["gwp_lo"], o["gwp_hi"], o["gwp_swing"], o["npv_lo"], o["npv_hi"]] for o in OAT], widths=[7, 14, 40, 24] + [11] * 11, fmt=[None] * 4 + ["0.####"] * 3 + ["0.000"] * 3 + ["0.00"] * 3 + ["#,##0"] * 2)
mp = CORE["map_prod_area"]; me = CORE["map_ef_yield"]
rows = [[r["item"], r["value"], r["unit"], r["target"]] for r in CORE["breakeven"]]
ws = sheet("16_Breakeven", "Break-even and crossover values; break-even maps", "Root-finding on the full engine. 'None' = not reached within physical bounds. Maps below.", ["Quantity", "Value", "Unit", "Target"], rows, widths=[60, 16, 16, 20], fmt=[None, "#,##0.000"])
r0 = len(rows) + 7; ws.cell(row=r0, column=1, value="MFSP map (USD/Ldeq): rows = productivity g/m2/d, columns = pond area ha").font = Font(bold=True)
for j, a in enumerate(mp["area"]): ws.cell(row=r0 + 1, column=j + 2, value=float(a))
for i, p in enumerate(mp["prod"]):
    ws.cell(row=r0 + 2 + i, column=1, value=float(p))
    for j in range(len(mp["area"])): ws.cell(row=r0 + 2 + i, column=j + 2, value=float(mp["mfsp"][i, j])).number_format = "0.00"
r1 = r0 + len(mp["prod"]) + 4; ws.cell(row=r1, column=1, value="GWP map (g CO2e/MJ): rows = HTL yield, columns = electricity EF kg/kWh").font = Font(bold=True)
for j, e in enumerate(me["ef"]): ws.cell(row=r1 + 1, column=j + 2, value=float(e))
for i, y in enumerate(me["y"]):
    ws.cell(row=r1 + 2 + i, column=1, value=float(y))
    for j in range(len(me["ef"])): ws.cell(row=r1 + 2 + i, column=j + 2, value=float(me["gwp"][i, j])).number_format = "0.0"
rows = [[rt, path] + [r[k] for k in ("year", "mfsp", "gwp", "ef_el", "prod", "tci", "out", "npv", "abatement")] for (rt, path), rr in PROS.items() for r in rr]
sheet("17_Prospective", "Prospective results 2026-2050 (annual)", "Four pathways: REF, CES1, CES2 (Philippine Energy Plan 2023-2050) and NZ (net-zero sensitivity). Grid EF = Visayas.", ["Route", "Pathway", "Year", "MFSP USD/Ldeq", "GWP g/MJ", "Grid EF kg/kWh", "Productivity g/m2/d", "TCI USD", "Output Ldeq/yr", "NPV USD", "Abatement USD/t"],
      rows, widths=[7, 8, 7, 12, 10, 12, 12, 14, 14, 14, 14], fmt=[None, None, None, "0.000", "0.00", "0.0000", "0.0", "#,##0", "#,##0", "#,##0", "#,##0"])
# ------------------------------------------------------------------ 18-23 uncertainty
rows = []
for dsg, y in UNC["mc"].items():
    for out in ("mfsp_ldeq", "gwp", "npv", "tci", "ldeq", "irr", "saving"):
        v = y[out][np.isfinite(y[out])]
        rows.append([dsg, out, len(v), float(np.mean(v)), float(np.std(v))] + [float(np.percentile(v, q)) for q in (5, 25, 50, 75, 95)])
sheet("18_MC_Summary", f"Monte Carlo summary ({NMC:,} draws, LHS, Iman-Conover dependencies, common random numbers)", "Units: MFSP USD/Ldeq; GWP g/MJ; NPV and TCI USD; output Ldeq/yr; IRR and saving as fractions.", ["Design", "Output", "N", "Mean", "SD", "P5", "P25", "P50", "P75", "P95"], rows, widths=[24, 12, 8] + [14] * 7, fmt=[None, None, None] + ["#,##0.000"] * 7)
X = UNC["X"]; K = UNC["keys"]; des = list(UNC["mc"])
head = ["Draw"] + K + [f"{d.split()[0]} {o}" for d in des for o in ("mfsp_ldeq", "gwp", "npv")]
ws = wb.create_sheet("19_MC_Draws"); ws["A1"] = f"Monte Carlo draws: all {len(K)} sampled inputs and the MFSP, GWP and NPV of six designs ({NMC:,} rows)"; ws["A1"].font = TFONT
ws["A2"] = "Same input row for all designs (common random numbers). Prospective designs (S50, S54) apply their pathway changes on top of these inputs."; ws["A2"].font = NOTE
ws["A3"] = "← back to README"; ws["A3"].hyperlink = "#'00_README'!A1"; ws["A3"].font = LINK
ws.append([]); ws.delete_rows(4)
for j, h in enumerate(head, 1):
    c = ws.cell(row=4, column=j, value=h); c.fill = HF; c.font = HFONT
OUTM = np.column_stack([UNC["mc"][d][o] for d in des for o in ("mfsp_ldeq", "gwp", "npv")])
for i in range(NMC):
    ws.append([i + 1] + [float(v) for v in X[i]] + [clean(float(v)) for v in OUTM[i]])
ws.freeze_panes = "B5"
sheet("20_Risk", "Risk metrics", "Probabilities over the Monte Carlo draws; VaR5/CVaR5 of NPV at the CME price (USD).", ["Design"] + list(next(iter(RISK.values())).keys()),
      [[d] + list(r.values()) for d, r in RISK.items()], widths=[24] + [13] * 16, fmt=[None] + ["0.000"] * 16)
Cr = UNC["input_corr_realised"]
rows = [["Input dependency", NAME.get(a, a), NAME.get(b, b), r, float(Cr[K.index(a), K.index(b)])] for a, b, r in UNC["corr"]]
for dsg, sp in UNC["spearman"].items():
    for j, k in enumerate(K): rows.append([f"Spearman, {dsg}", NAME.get(k, k), "MFSP / GWP / NPV", float(sp["mfsp_ldeq"][j]), float(sp["gwp"][j]), float(sp["npv"][j])])
for j, k in enumerate(K): rows.append(["PRCC, S01 HTL base", NAME.get(k, k), "MFSP / GWP", float(UNC["prcc_htl_mfsp"][j]), float(UNC["prcc_htl_gwp"][j])])
for dsg, v in UNC["outcorr"].items(): rows.append(["Output correlation MFSP-GWP", dsg, "", float(v)])
rows.append(["P(HTL cheaper than FAME), same draws", "", "", float(UNC["p_htl_beats_fame"]["mfsp"])]); rows.append(["P(HTL lower GWP than FAME), same draws", "", "", float(UNC["p_htl_beats_fame"]["gwp"])])
sheet("21_Correlation", "Correlation and dependency analysis", "Input rank correlations (target, realised); Spearman and partial rank correlation coefficients of outputs with inputs.", ["Analysis", "Parameter / design", "Second parameter / outputs", "Value 1", "Value 2", "Value 3"], rows, widths=[36, 46, 40, 12, 12, 12], fmt=[None] * 3 + ["0.000"] * 3)
rows = []
for rt in ("HTL", "FAME"):
    for j, k in enumerate(K): rows.append(["Morris", rt, k, NAME.get(k, k), float(MOR[rt]["mfsp_ldeq"]["mu_star"][j]), float(MOR[rt]["mfsp_ldeq"]["sigma"][j]), float(MOR[rt]["gwp"]["mu_star"][j]), float(MOR[rt]["gwp"]["sigma"][j]), None, None])
for rt in ("HTL", "FAME"):
    s = SOB[rt]
    for j, k in enumerate(s["keys"]): rows.append([f"Sobol (N={s['n']})", rt, k, NAME.get(k, k), float(s["S1"][j, 0]), float(s["ST"][j, 0]), float(s["S1"][j, 1]), float(s["ST"][j, 1]), float(s["S1ci"][j, 0]), float(s["STci"][j, 0])])
sheet("22_GSA", "Global sensitivity analysis", "Morris: mu*, sigma for MFSP then GWP (r=20, 4 levels). Sobol: S1, ST for MFSP then GWP; last two columns = 95% bootstrap half-widths for MFSP S1 and ST.", ["Method", "Route", "Key", "Parameter", "MFSP mu*/S1", "MFSP sigma/ST", "GWP mu*/S1", "GWP sigma/ST", "MFSP S1 CI", "MFSP ST CI"],
      rows, widths=[14, 7, 14, 44] + [13] * 6, fmt=[None] * 4 + ["0.0000"] * 6)
rows = [[k, v["p_loss"], v["median"], v["var5"], v["cvar5"]] + [float(np.percentile(v["npv"], q)) for q in (5, 25, 50, 75, 95)] + [float(np.mean(v["typhoons"]))] for k, v in ST.items()]
sheet("23_Stochastic", "Stochastic cash-flow simulation (5,000 paths per case)", "Log-OU fuel price (sigma 0.25, kappa 0.5), Poisson typhoons (0.25/yr, 21 d, 2% farm capital), interannual productivity CV 7%. NPV in USD.", ["Case", "P(NPV<0)", "Median NPV", "VaR5", "CVaR5", "P5", "P25", "P50", "P75", "P95", "Mean typhoons over life"],
      rows, widths=[30] + [14] * 10, fmt=[None, "0.0%"] + ["#,##0"] * 8 + ["0.0"])
rows = []
for k in ("2026", "2026_2obj", "2040_CES2", "2050_NZ"):
    for s in OPT[k]["front"]: rows.append([k, s["route"], s["area"], s["mfsp"], s["gwp"], s["tci"], s["out"]] + [str(s["D"].get(x, "")) for x in ("lined", "aq", "upgrade", "heat", "elec", "nutr", "co2", "glyc")])
for k, hv in OPT["hv"].items():
    for i, v in enumerate(hv): rows.append([f"hypervolume {k}", "", i * 10, float(v)])
sheet("24_Pareto", "NSGA-II Pareto fronts (population 100, 80 generations)", "Objectives: MFSP USD/Ldeq, GWP g/MJ, TCI USD M. Hypervolume rows: generation and value.", ["Run", "Route", "Area ha", "MFSP", "GWP", "TCI USD M", "Output Ldeq/yr", "Lined", "Aqueous", "Upgrading", "Heat", "Electricity", "Nutrients", "CO2", "Glycerol"],
      rows, widths=[16, 7, 10, 10, 10, 10, 14] + [11] * 8, fmt=[None, None, "#,##0", "0.000", "0.00", "#,##0.0", "#,##0"])
rows = [["Feature", f[0], f[3], float(f[1]), float(f[2])] for f in ML["feat"]]
for rt in ("HTL", "FAME"):
    for n, res in ML[rt]["res"].items():
        for m in res["metrics"]: rows.append(["Hold-out", rt, n, m["out"], float(m["r2"]), float(m["rmse"]), float(m["mape"]), float(res["fit_s"]), float(res["pred_s"])])
    for n, cv in ML[rt]["cv"].items():
        for i, r in enumerate(cv): rows.append(["5-fold CV", rt, n, f"fold {i + 1}", float(r[0]), float(r[1])])
    for n, pts in ML[rt]["lc"].items():
        for a, b in pts: rows.append(["Learning curve", rt, n, int(a), float(b)])
    for n, v in ML[rt]["extrap"].items(): rows.append(["Extrapolation", rt, n, "train <25, test >30 g/m2/d", float(v["r2"]), float(v["mape"])])
    for out, pi in ML[rt]["perm"].items():
        for j, f in enumerate(ML["feat"]): rows.append(["Permutation importance", rt, out, f[3], float(pi[j])])
sheet("25_Surrogate", "Machine-learning surrogates: features, validation, learning curves, extrapolation, importance", f"{ML['HTL']['n']:,} engine runs per route; 80/20 split; Gaussian process on 1,500 points. Hold-out columns: R2, RMSE, MAPE, fit s, predict s/sample. CV columns: R2 MFSP, R2 GWP.", ["Block", "Route / name", "Model / key", "Output / label", "Value 1", "Value 2", "Value 3", "Value 4", "Value 5"],
      rows, widths=[22, 26, 30, 30] + [12] * 5, fmt=[None] * 4 + ["0.0000"] * 5)
sheet("26_Logistics", "Logistics options (HTL, 2026 base)", "Cost USD/yr; GWP g CO2e/MJ.", ["Configuration", "Logistics cost USD/yr", "MFSP USD/Ldeq", "Logistics GWP", "Total GWP"], [[l["config"], l["cost"], l["mfsp"], l["gwp_log"], l["gwp"]] for l in LOG], widths=[60, 18, 14, 14, 12], fmt=[None, "#,##0", "0.000", "0.00", "0.00"])
# ------------------------------------------------------------------ figures
FIGS = json.load(open(f"{RES}/figreg.json"))
order = sorted(FIGS, key=lambda k: (k.startswith("GA"), k))
idx = []
for fid in order:
    f = FIGS[fid]; sn = fid.split("_")[0]
    ws = wb.create_sheet(sn); ws["A1"] = f["title"]; ws["A1"].font = TFONT
    ws["A2"] = f["caption"]; ws["A2"].font = NOTE; ws["A2"].alignment = Alignment(wrap_text=True, vertical="top"); ws.merge_cells("A2:L2"); ws.row_dimensions[2].height = 48
    ws["A3"] = "← back to figure index"; ws["A3"].hyperlink = "#'27_Figure_Index'!A1"; ws["A3"].font = LINK
    rep = RN["fignum"].get(fid); ms = MN["fignum"].get(fid)
    ws["E3"] = f"Report figure {rep}" if rep else ""; ws["H3"] = f"Manuscript figure {ms}" if ms else ""
    im = PImage.open(f["path"]); w = 1000; h = int(im.height * w / im.width)
    if h > 1100: h = 1100; w = int(im.width * h / im.height)
    xi = XLImage(f["path"]); xi.width, xi.height = w, h; ws.add_image(xi, "A5")
    rows_img = int(h / 20) + 7
    data = f.get("data") or []
    if data and isinstance(data, list) and isinstance(data[0], dict):
        cols = list(dict.fromkeys(k for r in data for k in r))
        ws.cell(row=rows_img, column=1, value="Data behind the figure").font = Font(bold=True, size=11)
        for j, c in enumerate(cols, 1):
            cc = ws.cell(row=rows_img + 1, column=j, value=c); cc.fill = HF; cc.font = HFONT
        for i, r in enumerate(data, rows_img + 2):
            for j, c in enumerate(cols, 1): ws.cell(row=i, column=j, value=clean(r.get(c)))
    else:
        ws.cell(row=rows_img, column=1, value="Data: the values behind this figure are in the sheet(s) named in the figure index.").font = NOTE
    for j in range(1, 13): ws.column_dimensions[get_column_letter(j)].width = 16
    idx.append([sn, f["title"], f["caption"], f.get("section", ""), rep, ms, len(data) if isinstance(data, list) else 0])
ws = sheet("27_Figure_Index", "Figure index", "Every figure of the report, manuscript and presentation is on its own sheet with the data behind it. Click a sheet name to open it.", ["Sheet", "Title", "Caption", "Section", "Report figure", "Manuscript figure", "Data rows"], idx, widths=[10, 50, 100, 16, 12, 14, 10])
for i in range(5, 5 + len(idx)):
    c = ws.cell(row=i, column=1); c.hyperlink = f"#'{c.value}'!A1"; c.font = LINK
# ------------------------------------------------------------------ README
r = readme
r["A1"] = "Re-assessing microalgae fuel against the Philippine biodiesel benchmark: project results database"; r["A1"].font = Font(bold=True, size=16, color="1C5CAB")
lines = [("Authors", "Shulamite G. Cereno (National Graduate School of Engineering, University of the Philippines Diliman) and Ralph Carlo Evidente (BRIGHT, Technical University of Denmark)"),
         ("Version", "1.1, 17 October 2026 (revised after internal review by S. G. Cereno). Companion to the internal report v1.1, the manuscript draft and the presentation. This is a results database: it holds exported values and contains no live spreadsheet formulas; the calculations are reproduced by the model code package."),
         ("Contribution", "S. G. Cereno: original plant design, balances and financial model (2018); techno-economic and multi-attribute evaluation (2021). R. C. Evidente: re-assessment, models, analyses and documentation."),
         ("AI-use declaration", "This database, the model code, the analyses, the figures, the web calculator and the drafts of the report, manuscript and presentation were produced with the assistance of an AI agent, Claude (Anthropic), working under the authors' direction. The authors checked the inputs, results and sources and are responsible for the content."),
         ("Scope", "Harmonised techno-economic and life cycle assessment of a flue-gas microalgae fuel plant at San Carlos BioPower, Negros Occidental: HTL + hydrotreating (Route A) and lipid extraction + FAME (Route B)."),
         ("Conventions", "Currency: US dollars on a mixed basis: capital in USD 2025 (CEPCI 2025 annual average 813) and operating prices at 2026 quotes (PHP 60.75/USD), without escalation between them. Functional unit: 1 MJ fuel (LHV) at plant gate; 35.9 MJ per litre diesel-equivalent (Ldeq). GWP: IPCC 2021 GWP100 (AR6). Background: ecoinvent 3.12 cut-off; Visayas grid from the ph-grid model. Allocation: one whole-system energy-allocation factor after the RED II principle (indicative, not a compliance calculation). LCIA units: sheet 09_LCIA."),
         ("Benchmarks", f"CME {B['p_cme']} USD/L (= {CME:.2f} USD/Ldeq, Aug 2026), used as an economic benchmark only (mandate eligibility of HTL renewable diesel is not assumed); diesel {DSL} USD/L ex-tax (Oct 2026); fossil comparator 94 g CO2e/MJ (RED II regulatory value); RED II thresholds 50% / 60% / 65% by installation start date. Risk sheet: P(MFSP<CME fixed) uses the fixed benchmark; P(MFSP<CME sampled) and P(NPV>0) use the CME price drawn in each draw."),
         ("Headline results", f"HTL base: MFSP {H['mfsp_ldeq']:.2f} USD/Ldeq, GWP {H['gwp']:.1f} g/MJ, TCI {H['tci']/1e6:.0f} M USD. FAME base: {F['mfsp_ldeq']:.2f} USD/Ldeq, {F['gwp']:.1f} g/MJ. NZ 2050 HTL: {S['S54']['mfsp_ldeq']:.2f} USD/Ldeq, {S['S54']['gwp']:.1f} g/MJ."),
         ("Web calculator", CALC_URL), ("Reproducibility", "Model code package Cereno_Evidente_2026_Microalgae_model_code.zip: registry.py (inputs), model.py (engine), scen.py, verify.py, validate.py, closure.py, run_core.py, run_unc.py, run_opt.py, run_ml.py, figure scripts and document builders, with README, requirements and random seeds. The ecoinvent 3.12 matrices are licensed and not included; the activities used are named in 08_LCI and the methods in 09_LCIA. Every figure sheet holds the data written by the script that drew it.")]
for i, (k, v) in enumerate(lines, 3):
    r.cell(row=i, column=1, value=k).font = Font(bold=True); c = r.cell(row=i, column=2, value=v); c.alignment = Alignment(wrap_text=True, vertical="top")
    r.row_dimensions[i].height = max(18, 15 * (len(v) // 110 + 1))
r.cell(row=12, column=2).hyperlink = CALC_URL; r.cell(row=12, column=2).font = LINK
r0 = 3 + len(lines) + 1
r.cell(row=r0, column=1, value="Contents").font = Font(bold=True, size=12, color="1C5CAB")
desc = {"01_Registry": "All model inputs with ranges, confidence and sources", "02_References": "APA references with DOIs and verification status", "03_Original_Data": "Inherited values and findings of the 2018, 2021 and 2026 studies",
        "04_Verification": "23 checks of the inherited design", "05_Validation": "Engine closure checks and benchmark validation", "06_Streams_HTL": "Stream table, Route A", "06_Streams_FAME": "Stream table, Route B", "07_Balance": "Material and energy balance",
        "08_LCI": "Inventory linked to ecoinvent 3.12", "09_LCIA": "183 impact indicators per MJ", "10_TEA_Capital": "Capital cost", "11_TEA_Opex": "Operating cost and economic results", "12_Cashflow": "Annual cash flows",
        "13_Scenarios": "60 scenarios", "14_Bridge": "Reported-to-corrected bridge", "15_OAT_Tornado": "One-at-a-time sensitivity", "16_Breakeven": "Break-even values and maps", "17_Prospective": "Annual results 2026-2050",
        "18_MC_Summary": "Monte Carlo percentiles", "19_MC_Draws": "All Monte Carlo draws", "20_Risk": "Risk probabilities, VaR, CVaR", "21_Correlation": "Dependencies, Spearman, PRCC", "22_GSA": "Morris and Sobol indices",
        "23_Stochastic": "Stochastic cash-flow simulation", "24_Pareto": "Pareto fronts and hypervolume", "25_Surrogate": "Surrogate models and validation", "26_Logistics": "Logistics options", "27_Figure_Index": "Index of figure sheets (F01a ... F44, GA)"}
for i, (k, v) in enumerate(desc.items(), r0 + 1):
    c = r.cell(row=i, column=1, value=k); c.hyperlink = f"#'{k}'!A1"; c.font = LINK; r.cell(row=i, column=2, value=v)
r.column_dimensions["A"].width = 22; r.column_dimensions["B"].width = 140
# order sheets: README, data sheets, index, figures
names = wb.sheetnames; data_sheets = [n for n in names if n[:2].isdigit()]; fig_sheets = [n for n in names if not n[:2].isdigit()]
wb._sheets = [wb[n] for n in sorted(data_sheets) + fig_sheets]
wb.properties.creator = "Shulamite G. Cereno; Ralph Carlo Evidente (prepared with Claude, Anthropic)"; wb.properties.title = "Microalgae TEA-LCA results database v1.1"
wb.save(OUT); print("saved", OUT, len(wb.sheetnames), "sheets")
