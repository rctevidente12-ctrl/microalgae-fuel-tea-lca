import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parents[1])); from paths import ENGINE, MODEL, ANALYSIS, RESULTS, FIGURES, DATA, PARSED, ROOT
"""Build ecoinvent 3.12 cut-off technosphere (A) and biosphere (B) matrices from compact ecoSpold2 extracts."""
import gzip, json, glob, numpy as np, scipy.sparse as sp, pickle, collections
P=str(PARSED)+"/"
acts=[]; 
for f in sorted(glob.glob(P+"chunk_*.jsonl.gz")):
    for line in gzip.open(f,"rt"):
        acts.append(json.loads(line))
print("activities", len(acts))
key2col={}; meta=[]
for j,a in enumerate(acts):
    aid,pid=a["f"].replace(".spold","").split("_")
    key2col[(aid,pid)]=j
    ref=[x for x in a["x"] if x[3]=="0"]
    assert len(ref)==1, a["f"]
    r=ref[0]
    meta.append(dict(col=j,file=a["f"],activity=a["n"],location=a["loc"],product=r[5],unit=r[6],ref_amount=r[2],type=a["t"],pv=r[7]))
elem=json.load(gzip.open(P+"elementary.json.gz","rt"))
e2row={e[0]:i for i,e in enumerate(elem)}
rows=[];cols=[];vals=[]; brow=[];bcol=[];bval=[]; unlinked=collections.Counter()
for j,a in enumerate(acts):
    for x in a["x"]:
        exid,link,amt,og,ig,name,unit,pv=x
        if og=="0":
            rows.append(j);cols.append(j);vals.append(amt)
        elif ig=="5":
            if amt==0: continue
            k=(link,exid)
            if k in key2col:
                rows.append(key2col[k]);cols.append(j);vals.append(-amt)
            else: unlinked[name]+=1
        # outputGroup 2 (by-products) / 1 / 4 for intermediates are zero in cut-off; ignore non-zero with warning
        elif og is not None and amt!=0:
            unlinked["OUT:"+str(og)+":"+name]+=1
    for b in a["b"]:
        fid,amt,og,ig=b
        if amt==0: continue
        brow.append(e2row[fid]);bcol.append(j);bval.append(amt)
n=len(acts)
A=sp.csc_matrix((vals,(rows,cols)),shape=(n,n))
B=sp.csc_matrix((bval,(brow,bcol)),shape=(len(elem),n))
print("A nnz",A.nnz,"B nnz",B.nnz,"unlinked",sum(unlinked.values()), unlinked.most_common(8))
pickle.dump(dict(A=A,B=B,meta=meta,elem=elem),open(ENGINE/"ei312_matrices.pkl","wb"))
