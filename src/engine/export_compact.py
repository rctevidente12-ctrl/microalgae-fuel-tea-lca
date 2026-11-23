"""Export the GWP100 unit scores of the ecoinvent 3.12 activities used by the model to data/unit_scores_gwp.json.

Run once with the licensed engine files in engine/ (see README). The exported file lets model.py run
without ecoinvent: cost results and GWP are identical; the other 182 indicators need the licensed files."""
import os, sys, json
ROOT = os.environ.get("ALGAE_HOME", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT + "/src")
os.environ["ALGAE_EI_MODE"] = "full"
import ei, model
cols = dict(model.COLS)
cols["el_US"] = [m["col"] for m in ei.meta if m["activity"] == "market group for electricity, medium voltage" and m["location"] == "US"][0]
rows = []
for key, c in sorted(cols.items()):
    m = ei.meta[c]
    rows.append(dict(key=key, activity=m["activity"], location=m["location"], product=m["product"], gwp100=float(ei.U[ei.GWP, c])))
out = dict(source="ecoinvent 3.12, allocation cut-off by classification; IPCC 2021 GWP100 (AR6), kg CO2-eq per unit of reference product",
           indicators=[list(c) for c in ei.cats], activities=rows)
os.makedirs(ROOT + "/data", exist_ok=True)
json.dump(out, open(ROOT + "/data/unit_scores_gwp.json", "w"), indent=1)
print(len(rows), "activities written")
