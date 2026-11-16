"""Builds the web calculator from the exported surrogate and checks it against the engine in Node and headless Chromium."""
import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import json, subprocess, sys
sys.path.insert(0, ROOT + "/src")
RES = ROOT + "/results"; WEB = ROOT + "/web"
m = json.load(open(f"{RES}/surrogate.json")); json.dump(m, open(f"{WEB}/model.json", "w"))
t = open(f"{WEB}/template.html").read().replace("__MODEL__", json.dumps(m))
open(f"{WEB}/calculator.html", "w").write(t); open(ROOT + "/out/calculator.html", "w").write(t)
# base-design point (same feature vector as the engine base) evaluated in Node with the exported weights
import registry as REG, numpy as np
B = REG.BASE
base = dict(prod=B["prod"], log_area=float(np.log10(400)), htl_y=B["htl_y"], lipid=B["lipid"], ef_el=B["ef_grid"], p_el=B["p_el"], p_h2=B["p_h2"], p_heat=B["p_heat"],
            loc_f=B["loc_f"], cap_mult=1.0, r=B["r"], life=B["life"], p_urea=B["p_urea"], mix_kwh=B["mix_kwh"], heat_bio=0, lined=0, ith=1)
js = """
const M = JSON.parse(require('fs').readFileSync('%s/model.json'));
function forward(net, xs) {
  let h = xs.map((v, i) => (v - net.mean[i]) / net.scale[i]);
  for (let l = 0; l < net.W.length; l++) {
    const W = net.W[l], b = net.b[l], o = new Array(b.length).fill(0);
    for (let j = 0; j < b.length; j++) { let s = b[j]; for (let i = 0; i < h.length; i++) s += h[i] * W[i][j]; o[j] = l < net.W.length - 1 ? Math.max(0, s) : s; }
    h = o;
  }
  return net.log ? Math.exp(h[0]) : h[0];
}
const x = %s; const xs = M.feat.map(f => x[f.name]); const out = {};
for (const r of ['HTL', 'FAME']) { out[r] = {}; for (const net of M[r]) out[r][net.out] = forward(net, xs);
  out[r].ldeq = M.out_coef[r] * x.prod * Math.pow(10, x.log_area) * (r === 'HTL' ? x.htl_y : x.lipid); }
console.log(JSON.stringify(out));
""" % (WEB, json.dumps(base))
open(ROOT + "/results/calc_check.js", "w").write(js)
out = json.loads(subprocess.check_output(["node", ROOT + "/results/calc_check.js"]).decode())
# browser timing (headless Chromium via Playwright): evaluate predict() for one route 2,000 times
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(); pg.goto("file://" + f"{WEB}/calculator.html")
        us = pg.evaluate("""() => { const t0 = performance.now(); let s = 0; for (let i = 0; i < 2000; i++) { s += predict('HTL', {...x, prod: 10 + (i % 30)}).mfsp_ldeq; } return (performance.now() - t0) / 2000 * 1000; }""")
        b.close()
except Exception as e:
    print("browser timing failed:", e); us = float("nan")
out["browser_us"] = us
json.dump(out, open(f"{RES}/calc_check.json", "w"), indent=1); print(out)
