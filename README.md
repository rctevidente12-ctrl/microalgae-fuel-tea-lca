# Flue-gas microalgae fuel: TEA–LCA model

Model code for Cereno, S.G.; Evidente, R.C.; Almendrala, M. "Flue-gas microalgae fuel against the Philippine biodiesel benchmark: an integrated techno-economic and life cycle assessment with uncertainty, multi-objective optimisation and machine-learning surrogates", submitted to *Sustainable Science and Innovation*.

## Environment

Python 3.13 with the package versions in `requirements.txt`:

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Reproducing the results

1. **ecoinvent 3.12 (licensed, not included).** The life cycle part needs the ecoinvent 3.12 cut-off database and the ecoinvent 3.8 LCIA method package. `src/engine/build_matrix.py`, `src/engine/lcia.py` and `src/engine/solve.py` build the technosphere and biosphere matrices, the characterisation matrix and the unit scores into `engine/` from compact extracts placed in `parsed/` (`chunk_*.jsonl.gz`, `elementary.json.gz`, `lcia38.json.gz`). The ecoinvent activities used are listed in `src/lcimap.py` and in Supplementary Data S1 (sheet 08_LCI); the impact methods in `src/units.py` and sheet 09_LCIA.
   The script that converted the licensed ecoSpold2 files into these compact extracts is not yet part of this repository.
2. **Run** `./run_all.sh` from the repository root. Results are written to `results/` and figures to `figs/`.

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
| `src/engine/` | builds the ecoinvent matrices and unit scores |

Scripts that only assembled the report, manuscript, database workbook and web calculator are not included.

## Declaration

The code was written with the assistance of an AI system (Claude, Anthropic) under the authors' direction, as declared in the manuscript.
