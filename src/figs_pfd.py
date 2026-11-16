"""Process flow diagrams with numbered streams and the LCA system boundary."""
import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import sys, pickle, json, numpy as np
sys.path.insert(0, ROOT + "/src")
from figstyle import *
from matplotlib.patches import FancyBboxPatch, Rectangle
import registry as REG
R = pickle.load(open(ROOT + "/results/core.pkl", "rb")); H, F = R["base"]["HTL"], R["base"]["FAME"]; P = REG.BASE
CUL, CONV, UTIL, PROD, BG, LINE = "#cde2fb", "#fde1d3", "#d5f2e7", "#fdf0cc", "#efeeea", "#3a3a38"
def box(ax, x, y, w, h, t, c, fs=7.4, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.0,rounding_size=0.12", fc=c, ec="#9a9994", lw=0.8))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, color=INK, weight="bold" if bold else "normal", linespacing=1.15)
def path(ax, pts, sid=None, lab_at=0, c=LINE, dash=False):
    """Orthogonal polyline with an arrowhead at the end and a stream-number tag."""
    xs, ys = zip(*pts)
    ax.plot(xs[:-1] + (xs[-1],), ys, color=c, lw=1.2, ls="--" if dash else "-", solid_capstyle="butt", zorder=1)
    ax.annotate("", xy=pts[-1], xytext=pts[-2], arrowprops=dict(arrowstyle="-|>", color=c, lw=1.2, mutation_scale=11, shrinkA=0, shrinkB=0), zorder=2)
    if sid is not None:
        (x1, y1), (x2, y2) = pts[lab_at], pts[lab_at + 1]
        ax.text((x1 + x2) / 2, (y1 + y2) / 2, str(sid), ha="center", va="center", fontsize=6.6, color="white", weight="bold",
                bbox=dict(boxstyle="circle,pad=0.18", fc=ORANGE, ec="none"), zorder=4)
def boundary(ax, x, y, w, h, label, where="top"):
    ax.add_patch(Rectangle((x, y), w, h, fill=False, ls=(0, (6, 3)), lw=1.4, ec=GREEN))
    if where == "top": ax.text(x + 0.15, y + h - 0.12, label, fontsize=7.5, color=GREEN, weight="bold", va="top")
    else: ax.text(x + 0.05, y - 0.15, label, fontsize=7.5, color=GREEN, weight="bold", va="top", ha="left")
# =========================================================== F01a  System boundary
fig, ax = plt.subplots(figsize=(11, 6.6)); ax.set_xlim(0, 22); ax.set_ylim(0, 13); ax.axis("off")
boundary(ax, 4.6, 2.3, 12.6, 9.4, "FOREGROUND SYSTEM: San Carlos Ecozone, Negros Occidental")
box(ax, 5.2, 7.2, 3.0, 2.6, "Cultivation:\nopen raceway\nponds\n(C. vulgaris)", CUL, 8, True)
box(ax, 8.7, 7.2, 2.8, 2.6, "Harvest &\ndewatering\n(to 20%\nsolids)", CUL, 8, True)
box(ax, 12.0, 8.6, 4.9, 1.6, "Route A:\nHTL + hydrotreating", CONV, 8, True)
box(ax, 12.0, 6.6, 4.9, 1.6, "Route B: extraction + FAME\n+ anaerobic digestion, CHP", CONV, 8, True)
box(ax, 5.2, 3.0, 11.7, 1.5, "On-site utilities: process heat (LPG or biomass boiler), electricity distribution,\nwater circulation, aqueous-phase and digestate nitrogen recycle to the ponds", UTIL, 7.6)
for y, t in ((10.6, "Flue-gas CO2\n(San Carlos BioPower)"), (9.1, "Fertiliser\n(urea, DAP)"), (7.6, "Make-up water"), (6.1, "Chemicals\n(MeOH, NaOH, H3PO4,\nhexane, H2)"), (4.4, "Electricity\n(grid / GEA PPA)"), (2.9, "Heat fuel\n(LPG / bagasse)")):
    box(ax, 0.3, y - 0.6, 3.2, 1.2, t, BG, 7)
    path(ax, [(3.5, y), (4.6, y)])
for y, t in ((9.4, "Renewable diesel\n+ naphtha"), (7.4, "FAME + glycerol"), (5.6, "Surplus electricity\n(FAME route)")):
    box(ax, 18.6, y - 0.6, 3.1, 1.2, t, PROD, 7.5, True); path(ax, [(17.2, y), (18.6, y)])
box(ax, 18.6, 3.0, 3.1, 1.6, "Emissions to air/water\n(N2O, CH4 slip,\ntreated effluent)", BG, 7); path(ax, [(17.2, 3.8), (18.6, 3.8)])
path(ax, [(8.2, 8.5), (8.7, 8.5)]); path(ax, [(11.5, 8.9), (12.0, 9.4)]); path(ax, [(11.5, 8.1), (12.0, 7.4)])
ax.text(11.0, 1.55, "BACKGROUND (ecoinvent 3.12 cut-off; Philippine grid from the ph-grid model): production of every input crossing the boundary, transport, infrastructure (ponds, chemical plant).", ha="center", fontsize=7.3, color=INK2)
ax.text(11.0, 0.95, "EXCLUDED: fuel distribution beyond the depot, vehicle use (except combustion CH4/N2O), land-use change (site is existing ecozone/cane land), end-of-life of the plant.", ha="center", fontsize=7.3, color=INK2)
ax.text(11.0, 0.35, "Functional unit: 1 MJ (LHV) of fuel at the plant gate. Co-products: energy allocation (RED II); system expansion as sensitivity. Flue-gas CO2 enters burden-free (cut-off).", ha="center", fontsize=7.3, color=INK2)
ax.text(11.0, 12.55, "System boundary of the assessment (cradle-to-gate, plus combustion CH4 and N2O)", ha="center", fontsize=10, weight="bold")
save(fig, "F01a_system_boundary", "System boundary", "Foreground units modelled in this study (inside the dashed line), background supply chains from ecoinvent 3.12 cut-off and the Philippine grid model, products and emissions crossing the boundary, and excluded stages.", section="Process")
# =========================================================== F01b  PFD, HTL route
def T(v, unit="t/yr"): return f"{v:,.0f} {unit}"
fig, ax = plt.subplots(figsize=(12.5, 7.8)); ax.set_xlim(0, 25); ax.set_ylim(0, 14.6); ax.axis("off")
BT = 10.3
boundary(ax, 0.6, 3.0, 23.8, BT - 3.0, "Foreground system boundary (Route A, base design: 400 ha of ponds)", where="bottom")
Y = 6.6; hb = 1.8
units = [(1.4, 3.2, "Raceway ponds\n400 ha, 0.20 m\npaddlewheels\n20 g/m2/d", CUL), (5.6, 2.4, "Gravity\nsettlers\n0.05 to 1%", CUL), (8.8, 2.4, "Hollow-fibre\nmembranes\n1 to 13%", CUL),
         (12.0, 2.4, "Disc-stack\ncentrifuge\n13 to 20%", CUL), (15.2, 2.6, "HTL reactor\n350 C, 20.9 MPa\nfeed-effluent HX", CONV), (18.6, 2.4, "Three-phase\nseparator", CONV), (21.8, 2.2, "Hydrotreater\n+ fractionator", CONV)]
for x, w, t, c in units: box(ax, x, Y, w, hb, t, c, 7.2, False)
mid = Y + hb / 2
for x1, x2, sid in [(4.6, 5.6, 5), (8.0, 8.8, 6), (11.2, 12.0, 7), (14.4, 15.2, 8), (17.8, 18.6, 9), (21.0, 21.8, 10)]: path(ax, [(x1, mid), (x2, mid)], sid)
IY = 11.0
box(ax, 0.9, IY, 2.4, 1.0, "Flue-gas CO2\n(San Carlos BioPower)", BG, 6.8); path(ax, [(2.1, IY), (2.1, Y + hb)], 1)
box(ax, 3.6, IY, 2.4, 1.0, "Urea + DAP", BG, 7); path(ax, [(4.8, IY), (4.8, 9.4), (3.9, 9.4), (3.9, Y + hb)], 2, lab_at=0)
box(ax, 6.3, IY, 2.4, 1.0, "Make-up water", BG, 7); path(ax, [(7.5, IY), (7.5, 9.0), (4.2, 9.0), (4.2, Y + hb)], 3, lab_at=1)
box(ax, 9.3, IY, 4.0, 1.0, "Electricity (Visayas grid or\nGEA PPA) to all units", BG, 6.8); path(ax, [(11.3, IY), (11.3, BT - 0.05)], 12)
box(ax, 14.4, IY, 3.0, 1.0, "Heat fuel (LPG or\nbagasse) to boiler", BG, 6.8); path(ax, [(15.9, IY), (15.9, Y + hb)], 11)
box(ax, 18.0, IY, 2.6, 1.0, "Off-gas (CO2-rich)\nto stack", BG, 6.8); path(ax, [(19.8, Y + hb), (19.8, IY)], 14)
box(ax, 21.6, IY, 2.6, 1.0, "Hydrogen\n(small SMR, LPG)", BG, 6.8); path(ax, [(22.9, IY), (22.9, Y + hb)], 15)
box(ax, 20.3, 1.6, 2.0, 1.0, "Renewable\ndiesel", PROD, 7, True); box(ax, 22.6, 1.6, 1.6, 1.0, "Naphtha", PROD, 7, True)
path(ax, [(22.4, Y), (22.4, 4.6), (21.3, 4.6), (21.3, 2.6)], 16, lab_at=1); path(ax, [(23.4, Y), (23.4, 2.6)], 17)
path(ax, [(6.8, Y), (6.8, 5.0), (2.6, 5.0), (2.6, Y)], 4, lab_at=1, c=BLUE, dash=True)
ax.plot([10.0, 10.0, 6.8], [Y, 5.0, 5.0], color=BLUE, lw=1.2, ls="--"); ax.plot([13.2, 13.2, 10.0], [Y, 5.0, 5.0], color=BLUE, lw=1.2, ls="--")
ax.text(4.7, 4.65, "clarified water recycled to ponds", fontsize=6.8, color=BLUE, ha="center")
path(ax, [(13.2, 5.0), (15.6, 5.0), (15.6, Y)], "8a", lab_at=0, c=BLUE, dash=True)
ax.text(14.4, 5.25, "dilution water", fontsize=6.4, color=BLUE, ha="center")
path(ax, [(19.4, Y), (19.4, 3.8), (1.9, 3.8), (1.9, Y)], 13, lab_at=1, c=GREEN, dash=True)
ax.text(10.6, 3.42, "HTL aqueous phase (N, P, organics) recycled to ponds as nutrient source", fontsize=6.8, color=GREEN, ha="center")
ax.text(12.5, 14.1, "Process flow diagram: Route A (hydrothermal liquefaction + hydrotreating)", ha="center", fontsize=10, weight="bold")
ax.text(1.0, 12.6, "INPUTS FROM THE BACKGROUND (ecoinvent 3.12 / ph-grid model)", fontsize=7.3, color=INK2, weight="bold")
ax.text(19.9, 2.1, "PRODUCTS LEAVING THE BOUNDARY (plant gate)  -->", fontsize=7.3, color=INK2, weight="bold", va="center", ha="right")
ax.text(12.5, 0.75, "Numbered circles = stream numbers (stream table: database sheet 06_Streams_HTL). Solid: process streams; dashed: recycles inside the boundary.", ha="center", fontsize=7.2, color=INK2)
ax.text(12.5, 0.25, "Cultivation and dewatering after Davis et al. (2016) and Klein et al. (2024); HTL and upgrading after Jones et al. (2014).", ha="center", fontsize=7.2, color=INK2)
broth = H["afdw"] / 0.0005
SH = [(1, "Flue-gas CO2 delivered to sumps", H["co2_need"], "t CO2/yr", "Biogenic CO2; 1.83 kg/kg fixed / 66% utilisation"), (2, "Urea + DAP", H["urea"] + H["dap"], "t/yr", f"urea {H['urea']:,.0f}; DAP {H['dap']:,.0f}"),
      (3, "Make-up water (net of rain)", H["water_m3"], "m3/yr", "0.9 mm/d net"), (4, "Clarified water recycle", broth * 0.95, "m3/yr (approx.)", "settler overflow + membrane permeate + centrate"),
      (5, "Culture to settlers", broth, "m3/yr", f"{H['afdw']:,.0f} t AFDW harvested at 0.5 g/L"), (6, "Settler underflow (1% AFDW)", H["afdw"] / 0.01, "t/yr", ""),
      (7, "Membrane retentate (13% AFDW)", H["afdw"] / 0.13, "t/yr wet", ""), (8, "Centrifuge cake (20% AFDW = 23% total dry solids)", H["afdw"] / 0.20, "t/yr wet", f"{H['afdw']:,.0f} t AFDW + {H['dw'] - H['afdw']:,.0f} t ash = {H['dw']:,.0f} t total dry solids"),
      ("8a", "Dilution water (clarified recycle) to HTL feed", H["dw"] / P["htl_solids"] - H["afdw"] / 0.20, "t/yr", "brings the slurry from 23% to 20% total dry solids (PNNL basis)"),
      (9, "HTL feed slurry = HTL effluent (20% total dry solids)", H["dw"] / P["htl_solids"], "t/yr wet", "stream 8 + stream 8a; total dry solids include ash"), (10, "Biocrude", H["biocrude"], "t/yr", "41% of AFDW"),
      (11, "Process heat to HTL (net)", H["heat_net"] / 1e3, "GJ/yr", "after 80% feed-effluent recovery"), (12, "Electricity, total", H["el_dem"], "kWh/yr", ""),
      (13, "HTL aqueous phase recycle", H["dw"] / P["htl_solids"] - H["biocrude"] - H["dw"] * P["htl_gas"], "t/yr", "N recovered 60% of aqueous N"),
      (14, "HTL off-gas", H["dw"] * P["htl_gas"], "t/yr", "4% of dry feed"), (15, "Hydrogen", H["h2"], "t H2/yr", "0.043 kg/kg biocrude"),
      (16, "Renewable diesel", H["prod"]["rd"], "t/yr", f"{H['prod']['rd']*1000/0.80/1e6:.2f} ML/yr"), (17, "Naphtha", H["prod"]["naph"], "t/yr", "")]
y0 = 2.85
save(fig, "F01b_pfd_htl", "Process flow diagram, Route A (HTL)", "Process flow diagram of the base design with numbered streams; stream values are in the accompanying stream table.",
     data=[dict(stream=s, description=d, value=v, unit=u, note=n) for s, d, v, u, n in SH], section="Process")
# =========================================================== F01c  PFD, FAME route
fig, ax = plt.subplots(figsize=(12.5, 7.8)); ax.set_xlim(0, 25); ax.set_ylim(0, 14.6); ax.axis("off")
BT = 10.3; Y = 6.6; hb = 1.8; mid = Y + hb / 2; IY = 11.0
boundary(ax, 0.6, 3.0 - 0.6, 23.8, BT - 2.4, "Foreground system boundary (Route B, base design: 400 ha of ponds)", where="bottom")
units = [(1.4, 3.2, "Raceway ponds\n+ settlers, membranes,\ncentrifuge\n(as Route A)", CUL), (5.6, 2.6, "Wet hexane\nextraction\n(5:1 solvent)", CONV), (9.2, 2.4, "Solvent\nstripping\n(>99.7% recovery)", CONV),
         (12.6, 2.6, "Trans-\nesterification\nCSTR, NaOH, MeOH", CONV), (16.2, 2.4, "Methanol\nrecovery,\nwashing", CONV), (19.6, 2.4, "Glycerol\nneutralisation\n(H3PO4)", CONV)]
for x, w, t, c in units: box(ax, x, Y, w, hb, t, c, 7.2)
for x1, x2, sid in [(4.6, 5.6, 4), (8.2, 9.2, 5), (11.6, 12.6, 6), (15.2, 16.2, 7)]: path(ax, [(x1, mid), (x2, mid)], sid)
path(ax, [(18.6, mid - 0.4), (19.6, mid - 0.4)], 18)
box(ax, 0.9, IY, 2.4, 1.0, "Flue-gas CO2", BG, 7); path(ax, [(2.1, IY), (2.1, Y + hb)], 1)
box(ax, 3.6, IY, 2.4, 1.0, "Urea + DAP", BG, 7); path(ax, [(4.8, IY), (4.8, 9.4), (3.9, 9.4), (3.9, Y + hb)], 2, lab_at=0)
box(ax, 6.3, IY, 2.4, 1.0, "Hexane make-up", BG, 7); path(ax, [(7.5, IY), (7.5, Y + hb)], 8)
box(ax, 9.3, IY, 2.4, 1.0, "Grid electricity\n(back-up)", BG, 6.8); path(ax, [(10.5, IY), (10.5, BT - 0.05)], 3)
box(ax, 12.2, IY, 3.0, 1.0, "Methanol, NaOH", BG, 7); path(ax, [(13.9, IY), (13.9, Y + hb)], 9)
box(ax, 19.8, IY, 2.4, 1.0, "H3PO4", BG, 7); path(ax, [(20.8, IY), (20.8, Y + hb)], 10)
box(ax, 16.3, IY, 2.2, 1.0, "FAME", PROD, 7.5, True); path(ax, [(17.4, Y + hb), (17.4, IY)], 11)
box(ax, 20.6, 1.0, 2.8, 1.0, "Crude glycerol", PROD, 7, True); path(ax, [(22.0, Y), (22.0, 2.0)], 12)
box(ax, 5.6, 3.6, 3.4, 1.4, "Anaerobic digestion\nof residual biomass", UTIL, 7.2); path(ax, [(6.9, Y), (6.9, 5.0)], 13)
box(ax, 10.6, 3.6, 3.0, 1.4, "Biogas CHP\n(35% el, 40% heat)", UTIL, 7.2); path(ax, [(9.0, 4.3), (10.6, 4.3)], 14)
box(ax, 15.2, 3.6, 3.0, 1.4, "Electricity & heat\nto plant units", UTIL, 7.2); path(ax, [(13.6, 4.3), (15.2, 4.3)], 15)
box(ax, 15.6, 1.0, 3.2, 1.0, "Surplus electricity\n(export)", PROD, 7, True); path(ax, [(16.7, 3.6), (16.7, 2.0)], 17)
path(ax, [(10.4, Y), (10.4, 5.4), (8.6, 5.4), (8.6, 5.0)], 19, lab_at=1, c=ORANGE, dash=True); ax.text(10.6, 5.65, "non-esterifiable extract", fontsize=6.4, color=ORANGE, ha="left")
path(ax, [(6.0, 3.6), (6.0, 3.1), (2.6, 3.1), (2.6, Y)], 16, lab_at=1, c=GREEN, dash=True); ax.text(4.3, 2.75, "digestate N recycle", fontsize=6.8, color=GREEN, ha="center")
ax.text(12.5, 14.1, "Process flow diagram: Route B (lipid extraction + transesterification to FAME)", ha="center", fontsize=10, weight="bold")
ax.text(1.0, 12.6, "INPUTS FROM THE BACKGROUND (ecoinvent 3.12 / ph-grid model)", fontsize=7.3, color=INK2, weight="bold")
ax.text(12.5, 0.25, "Numbered circles = stream numbers (database sheet 06_Streams_FAME). Extraction after Davis et al. (2012, 2020); transesterification after Pradhan et al. (2012).", ha="center", fontsize=7.2, color=INK2)
SF = [(1, "Flue-gas CO2", F["co2_need"], "t CO2/yr", ""), (2, "Urea + DAP", F["urea"] + F["dap"], "t/yr", ""), (4, "Dewatered biomass (20% AFDW)", F["afdw"] / 0.2, "t/yr", f"{F['afdw']:,.0f} t AFDW"),
      (5, "Extract + hexane", F["lip"], "t lipid/yr", "85.5% recovery"), (6, "Transesterifiable lipid (TAG) to transesterification", F["lip"] - F["extract_ret"], "t/yr", f"{P['fame_frac']:.0%} of the extract; the rest is stream 19"),
      (7, "Crude ester phase", F["prod"]["fame"], "t/yr", ""), (8, "Hexane make-up", F["inv"]["hexane"] / 1000, "t/yr", ""), (9, "Methanol + NaOH", (F["inv"]["methanol"] + F["inv"]["naoh"]) / 1000, "t/yr", ""),
      (10, "H3PO4", F["inv"]["h3po4"] / 1000, "t/yr", ""), (11, "FAME", F["prod"]["fame"], "t/yr", f"{F['prod']['fame']*1000/0.88/1e6:.2f} ML/yr"), (12, "Crude glycerol (80%)", F["glyc_kg"] / 1000, "t/yr", ""),
      (13, "Lipid-extracted residue to AD", F["afdw"] - F["lip"], "t VS/yr", "AFDW minus extracted lipid"), (19, "Non-transesterifiable extract returned to AD", F["extract_ret"], "t/yr", f"{1 - P['fame_frac']:.0%} of the extract (polar lipids, pigments)"),
      (14, "Biogas (CH4), from streams 13 + 19", F["ad_feed"] * 1000 * P["ad_ch4"] * (1 - P["ch4_leak"]), "m3 CH4/yr", f"0.212 m3/kg VS on {F['ad_feed']:,.0f} t VS; net of 2% slip"),
      (15, "CHP electricity", F["chp_el"], "kWh/yr", ""), (16, "Digestate N recycled", F["afdw"] * P["Nfrac"] * P["dig_Nrec"], "t N/yr", "50% of the N in harvested biomass"),
      (17, "Surplus electricity exported", F["el_export"], "kWh/yr", ""), (18, "Glycerol phase to neutralisation", F["glyc_kg"] / 1000, "t/yr", ""), (3, "Grid electricity (back-up)", F["el_import"], "kWh/yr", "zero in the base case")]
save(fig, "F01c_pfd_fame", "Process flow diagram, Route B (FAME)", "Process flow diagram of the lipid route with numbered streams; values in the stream table.",
     data=[dict(stream=s, description=d, value=v, unit=u, note=n) for s, d, v, u, n in SF], section="Process")
print("pfd done")
