"""Print the sums of first-order and total-order Sobol' indices reported in the manuscript (Section 3.5).
Run after run_unc.py has written results/unc.pkl."""
import os, pickle
ROOT = os.environ.get("ALGAE_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = pickle.load(open(os.path.join(ROOT, "results", "unc.pkl"), "rb"))
for route, s in R["sobol"].items():
    S1, ST = s["S1"].sum(0), s["ST"].sum(0)
    print(f"{route}: N = {s['n']}, {len(s['keys'])} parameters, {s['runs']} runs")
    print(f"  sum S1: MFSP {S1[0]:.3f}, GWP {S1[1]:.3f}   sum ST: MFSP {ST[0]:.3f}, GWP {ST[1]:.3f}")
