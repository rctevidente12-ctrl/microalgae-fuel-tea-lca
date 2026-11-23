"""Convert the licensed ecoinvent 3.12 cut-off ecoSpold2 unit-process files into the compact extracts read by
build_matrix.py (parsed/chunk_*.jsonl.gz). Nothing leaves the computer on which it is run.

Usage:  python parse_ecospold.py "<folder with the ecoinvent 3.12 cut-off 'datasets' directory>"

Each output line holds one activity: file name, id, name, location, special activity type, its intermediate
exchanges (id, activity link, amount, output group, input group, name, unit, production volume) and its
elementary exchanges (id, amount, output group, input group). elementary.json.gz and lcia38.json.gz, also read
by the engine scripts, are compact copies of the ecoinvent master data and LCIA implementation files."""
import os, sys, json, gzip, time
from lxml import etree
ROOT = os.environ.get("ALGAE_HOME", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if len(sys.argv) < 2: raise SystemExit(__doc__)
D = os.path.join(sys.argv[1], "datasets") if os.path.isdir(os.path.join(sys.argv[1], "datasets")) else sys.argv[1]
O = os.path.join(ROOT, "parsed"); os.makedirs(O, exist_ok=True)
NS = "{http://www.EcoInvent.org/EcoSpold02}"
fs = sorted(f for f in os.listdir(D) if f.endswith(".spold")); N = len(fs); CH = 1000
log = open(os.path.join(O, "progress.log"), "a")
for c in range(0, N, CH):
    out = os.path.join(O, f"chunk_{c // CH:02d}.jsonl.gz")
    if os.path.exists(out): continue
    tmp = out + ".part"
    with gzip.open(tmp, "wt", compresslevel=5) as g:
        for f in fs[c:c + CH]:
            try:
                r = etree.parse(os.path.join(D, f)).getroot()
                ad = r.find(f".//{NS}activity"); geo = r.find(f".//{NS}geography/{NS}shortname")
                rec = {"f": f, "id": ad.get("id"), "n": ad.findtext(f"{NS}activityName"), "loc": geo.text if geo is not None else "",
                       "t": ad.get("specialActivityType"), "x": [], "b": []}
                for e in r.iter(f"{NS}intermediateExchange"):
                    rec["x"].append([e.get("intermediateExchangeId"), e.get("activityLinkId"), float(e.get("amount")), e.findtext(f"{NS}outputGroup"),
                                     e.findtext(f"{NS}inputGroup"), e.findtext(f"{NS}name"), e.findtext(f"{NS}unitName"), e.get("productionVolumeAmount")])
                for e in r.iter(f"{NS}elementaryExchange"):
                    rec["b"].append([e.get("elementaryExchangeId"), float(e.get("amount")), e.findtext(f"{NS}outputGroup"), e.findtext(f"{NS}inputGroup")])
                g.write(json.dumps(rec) + "\n")
            except Exception as ex:
                log.write(f"ERR {f} {ex}\n")
    os.rename(tmp, out); log.write(f"{time.ctime()} chunk {c // CH} done\n"); log.flush()
log.write("ALLDONE\n"); log.close()
