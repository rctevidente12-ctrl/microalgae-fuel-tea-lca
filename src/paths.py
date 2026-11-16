"""Folder layout used by the ecoinvent engine scripts in src/engine/.
Set ALGAE_HOME to the repository root if the scripts are run from elsewhere."""
import os, pathlib
ROOT = pathlib.Path(os.environ.get("ALGAE_HOME", pathlib.Path(__file__).resolve().parents[1]))
ENGINE = ROOT / "engine"      # ecoinvent-derived matrices (licensed; not distributed)
PARSED = ROOT / "parsed"      # compact extracts of the ecoinvent 3.12 cut-off ecoSpold2 files (licensed; not distributed)
RESULTS = ROOT / "results"; FIGURES = ROOT / "figs"; DATA = ROOT / "data"
MODEL = ANALYSIS = ROOT / "src"
for _p in (ENGINE, PARSED, RESULTS, FIGURES): _p.mkdir(parents=True, exist_ok=True)
