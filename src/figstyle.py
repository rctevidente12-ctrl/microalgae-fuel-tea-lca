"""Shared figure style (validated reference palette, light mode), figure registry for the database."""
import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import json, os
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]   # categorical, fixed order
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = C
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0", "#ffffff"
SEQ = LinearSegmentedColormap.from_list("seq", ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"])
DIV = LinearSegmentedColormap.from_list("div", ["#1c5cab", "#86b6ef", "#efeeea", "#f3a27f", "#b8461b"])
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold", "axes.labelsize": 9,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.6, "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
                     "legend.fontsize": 8, "figure.dpi": 110, "savefig.dpi": 220, "savefig.bbox": "tight", "lines.linewidth": 2.0, "text.color": INK,
                     "figure.facecolor": SURF, "axes.facecolor": SURF})
FIGDIR = ROOT + "/figs"; os.makedirs(FIGDIR, exist_ok=True)
REG_PATH = ROOT + "/results/figreg.json"
def _load():
    try: return json.load(open(REG_PATH))
    except Exception: return {}
def save(fig, fid, title, caption, data=None, section=""):
    """Save PNG and register figure (title, caption, data rows for the database)."""
    path = f"{FIGDIR}/{fid}.png"; fig.savefig(path); plt.close(fig)
    reg = _load(); reg[fid] = dict(id=fid, title=title, caption=caption, path=path, section=section,
                                   data=data if data is not None else [])
    json.dump(reg, open(REG_PATH, "w"), default=float)
    return path
def note(ax, text, xy=(0.99, 0.02), ha="right", va="bottom", size=7.5):
    ax.text(*xy, text, transform=ax.transAxes, ha=ha, va=va, fontsize=size, color=INK2)
