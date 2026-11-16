"""Builds the integrated report (.docx) from the model outputs."""
import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import sys, json
sys.path.insert(0, ROOT + "/src")
from ctx import *
from doclib import Doc
import rep_a, rep_b, rep_c
d = Doc(FIG, title=rep_a.TITLE, footer="Cereno & Evidente (2026). Microalgae fuel for the Philippine biodiesel mandate. Internal report v1.1")
rep_a.front(d); rep_a.nomen(d); rep_a.intro(d); rep_a.system(d); rep_a.registry_sec(d); rep_a.process(d)
rep_b.vv(d); rep_b.tea(d); rep_b.lca(d); rep_b.scenarios(d); rep_b.sensitivity(d); rep_b.breakeven(d); rep_b.prospective(d)
rep_c.uncertainty(d); rep_c.correlation(d); rep_c.risk(d); rep_c.gsa(d); rep_c.pareto(d); rep_c.surrogate(d); rep_c.surrogate_val(d); rep_c.calculator(d)
rep_c.discussion(d); rep_c.conclusions(d); rep_c.documentation(d)
at = len(d.b)
rep_c.appendices(d); rep_c.app_equations(d); rep_c.app_revision(d)
d.finalise()
d.references(insert_at=at)
json.dump({"refnum": d.refnum, "fignum": d.fignum, "tabnum": d.tabnum}, open(ROOT + "/results/report_numbering.json", "w"), indent=1)
d.write(ROOT + "/out/report_spec.json", ROOT + "/out/Cereno_Evidente_2026_Microalgae_TEA_LCA_Report_v1.0.docx", creator="Shulamite G. Cereno; Ralph Carlo Evidente",
        description="Integrated TEA-LCA report. Prepared with the assistance of an AI agent (Claude, Anthropic).")
print(len(d.refnum), "refs;", len(d.fignum), "figures;", len(d.tabnum), "tables")
unused = [k for k in FIG if k not in d.fignum]; print("figures not placed:", unused)
