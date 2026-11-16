#!/usr/bin/env bash
# Reproduces every result of the manuscript, in order. Run from the repository root.
# Requires the ecoinvent-derived files in engine/ (see README, step 1).
set -euo pipefail
export ALGAE_HOME="$(pwd)"
cd src
python run_core.py           # base cases, 60 scenarios, cost bridge, one-at-a-time, break-even, prospective
python closure.py            # mass, energy, cost and LCA closure checks
python verify.py             # re-computation of the inherited 2018 balance (24 checks)
python validate.py           # comparison with independent published values
python run_unc.py 10000 2048 # Monte Carlo (seed 20261016), Morris, Sobol' (seed 7), stochastic cash flows
python report_sobol_sums.py  # prints the first- and total-order sums quoted in Section 3.5
python run_opt.py            # NSGA-II (seed 42)
python run_ml.py 16000       # surrogate models (seed 11)
python figs_core.py; python figs_unc.py; python figs_opt_ml.py; python figs_pfd.py
