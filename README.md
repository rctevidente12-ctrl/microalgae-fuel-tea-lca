# Flue-gas microalgae fuel: TEA–LCA model

Model code for Cereno, S.G.; Evidente, R.C.; Almendrala, M. "Flue-gas microalgae fuel against the Philippine biodiesel benchmark: an integrated techno-economic and life cycle assessment with uncertainty, multi-objective optimisation and machine-learning surrogates", submitted to *Sustainable Science and Innovation*.

## Environment

Python 3.13 with the package versions in `requirements.txt`:

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Reproducing the results

The code runs in two modes, chosen automatically by `src/ei.py`.

**Without ecoinvent (default in this repository).** `data/unit_scores_gwp.json` holds the IPCC 2021 GWP100 unit scores of the 36 ecoinvent 3.12 cut-off activities the model links to (the same values as the "GWP unit score" column of Supplementary Data S1, sheet 08_LCI, extended to all linked activities). With this file alone,

```
./run_all.sh
```

regenerates every cost result and every climate (GWP) result of the manuscript, including the Monte Carlo statistics, the Morris and Sobol' indices and their sums, the NSGA-II fronts and the surrogates. In this mode the other 182 impact indicators are returned as NaN, because their unit scores cannot be redistributed under the ecoinvent licence; the two figures that show them (midpoint comparison and normalised profile) are left blank.

**With a licensed copy of ecoinvent 3.12 (all 183 indicators).**

1. `python src/engine/parse_ecospold.py "<ecoinvent 3.12 cut-off ecoSpold2 folder>"` writes compact extracts of the unit processes to `parsed/`.
2. Place `elementary.json.gz` (the elementary-flow list of the ecoinvent master data) and `lcia38.json.gz` (the characterisation factors of the ecoinvent LCIA implementation as distributed with openLCA) in `parsed/`. These two files were prepared by hand from the licensed downloads and no script for them was kept; the fields the engine reads from them can be seen where `src/engine/build_matrix.py` and `src/engine/lcia.py` load them.
3. `python src/engine/build_matrix.py; python src/engine/lcia.py; python src/engine/solve.py` build the matrices and unit scores into `engine/`.
4. `./run_all.sh`. When `engine/` is present it is used automatically (`ALGAE_EI_MODE=compact` forces the mode without ecoinvent).

`python src/engine/export_compact.py` regenerates `data/unit_scores_gwp.json` from the licensed files. The two modes give identical cost and GWP results; this was checked for the base cases, the 60 scenarios, the Monte Carlo and the Sobol' analysis (sums of first-order indices 0.982 for MFSP and 0.979 for GWP, HTL route, in both modes).

Results are written to `results/` and figures to `figs/`.

## Random seeds

| Analysis | Script | Seed |
|---|---|---|
| Monte Carlo, Latin hypercube, Iman–Conover, Morris | `run_unc.py` | 20261016 |
| Sobol' (scrambled Sobol' sequence) | `run_unc.py`, function `sobol` | 7 |
| NSGA-II | `run_opt.py` | 42 |
| Surrogate training sample | `run_ml.py` | 11 |

## Where the reported numbers come from

- All inputs: `src/registry.py` (identical to Supplementary Data S1, sheet 01_Registry).
- Process, cost and life cycle engine: `src/model.py`.
- Sobol' indices (Section 3.5, Figure 10): `src/run_unc.py`, function `sobol` (Saltelli 2010 first-order and Jansen total-order estimators, N = 2,048 for HTL and 1,024 for FAME). `src/report_sobol_sums.py` prints the sums of the indices; the values in the manuscript are 0.982 (MFSP) and 0.979 (GWP) for HTL, as tabulated in Supplementary Data S1, sheet 22_GSA.

## Contents

| Path | Purpose |
|---|---|
| `src/registry.py`, `units.py`, `lcimap.py`, `refs.py` | parameters, units and impact categories, ecoinvent mapping, references |
| `src/model.py`, `scen.py`, `ei.py` | engine, scenario definitions, ecoinvent interface |
| `src/run_core.py`, `closure.py`, `verify.py`, `validate.py` | deterministic results and checks |
| `src/run_unc.py`, `run_opt.py`, `run_ml.py` | uncertainty and sensitivity, optimisation, surrogates |
| `src/figs_*.py`, `figstyle.py`, `ctx.py` | figures |
| `src/engine/` | ecoSpold2 parser, builders of the ecoinvent matrices and unit scores, export of the GWP unit scores |
| `data/unit_scores_gwp.json` | GWP100 unit scores of the linked ecoinvent activities (runs the model without ecoinvent) |
| `src/build_db.py` | writes the results database (Supplementary Data S1) |
| `src/build_report.py`, `build_ms.py`, `rep_a.py`, `rep_b.py`, `rep_c.py`, `doclib.py`, `render_docx.js`, `render_ms.js` | assemble the technical report and the manuscript draft (Node.js with the `docx` package) |
| `src/build_calc.py`, `src/web/template.html` | build the browser calculator from the surrogate model |
| `calculator/Algal-fuel-calculator.html` | the browser calculator (open in any browser) |

The full results database is submitted with the article as Supplementary Data S1.

## Declaration

The code was written with the assistance of an AI system (Claude, Anthropic) under the authors' direction, as declared in the manuscript.

## Version history

- **v1.1.0** — the model runs without ecoinvent (`data/unit_scores_gwp.json`, two-mode `src/ei.py`); the ecoSpold2 parser is included (`src/engine/parse_ecospold.py`); `validate.py` runs as a stand-alone script (its `__main__` block was placed before the definitions it calls). No change to any result.
- **v1.0.0** — first deposit.
