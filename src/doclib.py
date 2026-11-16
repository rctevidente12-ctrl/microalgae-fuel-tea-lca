import os as _os; ROOT = _os.environ.get("ALGAE_HOME", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
"""Small document-spec builder: light markup -> JSON blocks for render_docx.js.
Markup inside text: [@k1,k2] numbered citation | **bold** | *italic* | «fig:ID» | «tab:ID» | «sec:BM|text» | <URL|text>.
Citations and figure/table numbers are resolved in order of first appearance when the spec is finalised."""
import re, json, subprocess, os
from PIL import Image
import sys
sys.path.insert(0, ROOT + "/src")
from refs import REFS

TOK = re.compile(r"(_\{[^}]+\}|\^\{[^}]+\}|\[@[^\]]+\]|\*\*[^*]+\*\*|\*[^*\s][^*]*\*|«fig:[^»]+»|«tab:[^»]+»|«sec:[^»]+»|<https?://[^>|]+\|[^>]+>)")

def parse(text):
    segs = []
    for part in TOK.split(text):
        if not part: continue
        if part.startswith("_{") and part.endswith("}"): segs.append({"t": part[2:-1], "sub": True})
        elif part.startswith("^{") and part.endswith("}"): segs.append({"t": part[2:-1], "sup": True})
        elif part.startswith("[@"): segs.append({"citek": [k.strip() for k in part[2:-1].split(",")]})
        elif part.startswith("**"): segs.append({"t": part[2:-2], "b": True})
        elif part.startswith("*") and part.endswith("*") and len(part) > 2: segs.append({"t": part[1:-1], "i": True})
        elif part.startswith("«fig:"): segs.append({"figk": part[5:-1]})
        elif part.startswith("«tab:"): segs.append({"tabk": part[5:-1]})
        elif part.startswith("«sec:"): bm, t = part[5:-1].split("|", 1); segs.append({"xref": bm, "t": t})
        elif part.startswith("<http"): u, t = part[1:-1].split("|", 1); segs.append({"link": u, "t": t})
        else: segs.append(part)
    return segs

class Doc:
    def __init__(self, figreg, title="", footer=""):
        self.b = []; self.figreg = figreg; self.title = title; self.footer = footer
    # ---- text blocks
    def add(self, k, text=None, **kw):
        d = {"k": k, **kw}
        if text is not None: d["s"] = parse(text) if isinstance(text, str) else text
        self.b.append(d); return d
    def p(self, t): return self.add("p", t)
    def h1(self, t, bm=None, pb=False): return self.add("h1", t, bm=bm, pb=pb)
    def h2(self, t, bm=None): return self.add("h2", t, bm=bm)
    def h3(self, t): return self.add("h3", t)
    def bullets(self, items):
        for t in items: self.add("bullet", t)
    def nums(self, items):
        for t in items: self.add("num", t)
    def small(self, t): return self.add("small", t)
    def eq(self, t, n): return self.add("eq", t, n=n)
    def pb(self): self.b.append({"k": "pb"})
    # ---- figure from registry
    def fig(self, fid, w=None, extra_cap="", title=None, label=None, notitle=False):
        f = self.figreg[fid]; im = Image.open(f["path"]); ratio = im.height / im.width
        if w is None: w = 640 if ratio < 0.75 else (560 if ratio < 1.0 else (600 if ratio > 1.6 else 470))
        w = int(min(w, 820 / ratio))
        cap = (f"{f['caption']}" if notitle else f"{title or f['title']}. {f['caption']}") + (f" {extra_cap}" if extra_cap else "")
        self.b.append({"k": "fig", "fid": fid, "path": f["path"], "ratio": ratio, "w": w, "bm": "fig_" + fid.split("_")[0], "cap": parse(cap), "fixlabel": label})
    def table(self, tid, cap, head, rows, widths=None, align=None, note=None, size=16):
        widths = widths or [1] * len(head)
        self.b.append({"k": "table", "tid": tid, "bm": "tab_" + tid, "cap": parse(cap), "head": [parse(str(h)) for h in head],
                       "rows": [[parse(str(c)) for c in r] for r in rows], "widths": widths, "align": align, "note": parse(note) if note else None, "size": size})
    # ---- resolve numbering
    def finalise(self, ref_heading="References", fig_word="Figure", tab_word="Table"):
        refnum = {}; fignum = {}; tabnum = {}
        for blk in self.b:
            if blk["k"] == "fig" and not blk.get("fixlabel"): fignum[blk["fid"]] = len(fignum) + 1
            if blk["k"] == "table": tabnum[blk["tid"]] = len(tabnum) + 1
        def walk(segs):
            out = []
            for s in segs:
                if isinstance(s, dict) and "citek" in s:
                    ns = []
                    for k in s["citek"]:
                        if k not in REFS: raise KeyError("unknown ref " + k)
                        if k not in refnum: refnum[k] = len(refnum) + 1
                        ns.append(refnum[k])
                    out.append({"cite": sorted(set(ns))})
                elif isinstance(s, dict) and "figk" in s:
                    k = s["figk"]
                    if k not in fignum: raise KeyError("figure not placed " + k)
                    out.append({"xref": "fig_" + k.split("_")[0], "t": f"{fig_word} {fignum[k]}"})
                elif isinstance(s, dict) and "tabk" in s:
                    k = s["tabk"]
                    if k not in tabnum: raise KeyError("table not placed " + k)
                    out.append({"xref": "tab_" + k, "t": f"{tab_word} {tabnum[k]}"})
                else: out.append(s)
            return out
        for blk in self.b:
            for key in ("s", "cap", "note"):
                if blk.get(key): blk[key] = walk(blk[key])
            if blk["k"] == "table":
                blk["head"] = [walk(c) for c in blk["head"]]; blk["rows"] = [[walk(c) for c in r] for r in blk["rows"]]
            if blk["k"] == "fig": blk["label"] = blk.get("fixlabel") or f"{fig_word} {fignum[blk['fid']]}"
            if blk["k"] == "table": blk["label"] = f"{tab_word} {tabnum[blk['tid']]}"
        self.refnum = refnum; self.fignum = fignum; self.tabnum = tabnum
        return refnum
    def references(self, heading="References", bm="sec_refs", insert_at=None):
        blocks = [{"k": "h1", "s": [heading], "bm": bm, "pb": True}]
        for k, n in sorted(self.refnum.items(), key=lambda kv: kv[1]):
            apa, url = REFS[k]
            segs = [apa + " "]
            if url:
                if url.startswith("10."): url = "https://doi.org/" + url
                segs.append({"link": url, "t": url})
            blocks.append({"k": "ref", "n": n, "s": segs})
        if insert_at is None: self.b.extend(blocks)
        else: self.b[insert_at:insert_at] = blocks
    def write(self, path_json, path_docx, creator="", description="", renderer="render_docx.js"):
        spec = {"title": self.title, "creator": creator, "description": description, "footer": self.footer, "blocks": self.b}
        json.dump(spec, open(path_json, "w"), ensure_ascii=False)
        r = subprocess.run(["node", ROOT + "/src/" + renderer, path_json, path_docx], capture_output=True, text=True,
                           env={**os.environ, "NODE_PATH": subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()})
        print(r.stdout, r.stderr[-2000:])

def f0(x): return f"{x:,.0f}"
def f1(x): return f"{x:,.1f}"
def f2(x): return f"{x:,.2f}"
def pct(x, d=0): return f"{100 * x:.{d}f}%"
