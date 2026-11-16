import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parents[1])); from paths import ENGINE, MODEL, ANALYSIS, RESULTS, FIGURES, DATA, PARSED, ROOT
"""Characterisation: map openLCA (ecoinvent 3.8 LCIA package) CFs to ecoinvent 3.12 elementary flows by name+compartment; add IPCC 2021 (AR6) GWP100."""
import pickle,gzip,json,collections,numpy as np,scipy.sparse as sp, re
COMP={("air","unspecified"):"Emission to air/unspecified",("air","non-urban air or from high stacks"):"Emission to air/low population density",
("air","urban air close to ground"):"Emission to air/high population density",("air","low population density, long-term"):"Emission to air/low population density, long-term",
("air","lower stratosphere + upper troposphere"):"Emission to air/lower stratosphere + upper troposphere",("water","unspecified"):"Emission to water/unspecified",
("water","surface water"):"Emission to water/surface water",("water","ground-"):"Emission to water/ground water",("water","ground-, long-term"):"Emission to water/ground water, long-term",
("water","ocean"):"Emission to water/ocean",("water","fossil well"):"Emission to water/fossil-",("soil","agricultural"):"Emission to soil/agricultural",("soil","forestry"):"Emission to soil/forestry",
("soil","industrial"):"Emission to soil/industrial",("soil","unspecified"):"Emission to soil/unspecified",("natural resource","in ground"):"Resource/in ground",
("natural resource","land"):"Resource/land",("natural resource","in water"):"Resource/in water",("natural resource","in air"):"Resource/in air",("natural resource","biotic"):"Resource/biotic",("natural resource","fossil well"):"Resource/in ground"}
FALLBACK={"Emission to water/surface water":["Emission to water/river","Emission to water/unspecified"],"Emission to water/ground water":["Emission to water/unspecified"]}
def norm(s): return re.sub(r"\s+"," ",(s or "").strip().lower())
def build(elem):
    L=json.load(gzip.open(str(PARSED/"lcia38.json.gz"),"rt"))
    ids={e[0]:i for i,e in enumerate(elem)}
    cats=[];C=[];stats=[]
    for cid,c in L["cats"].items():
        byid={};byname={}
        for fid,fname,fcat,val,unit,refu in c["cf"]:
            byid[fid]=val; byname[(norm(fname),(fcat or "").replace("Elementary flows/",""))]=val
        row=np.zeros(len(elem)); hit=0
        for i,e in enumerate(elem):
            v=byid.get(e[0])
            if v is None:
                oc=COMP.get((e[2],e[3]))
                if oc:
                    v=byname.get((norm(e[1]),oc))
                    if v is None:
                        for fb in FALLBACK.get(oc,[]):
                            v=byname.get((norm(e[1]),fb))
                            if v is not None: break
            if v is not None: row[i]=v; hit+=1
        cats.append((c["method"],c["name"],c["unit"])); C.append(row); stats.append(hit)
    # IPCC 2021 GWP100 (AR6 WG1 Table 7.SM.7) built on IPCC 2013 flow set, AR6 values for main gases
    AR6={"carbon dioxide, fossil":1,"carbon dioxide, from soil or biomass stock":1,"carbon dioxide, to soil or biomass stock":-1,"methane, fossil":29.8,"methane, non-fossil":27.0,"methane, from soil or biomass stock":27.0,
         "dinitrogen monoxide":273,"sulfur hexafluoride":25200,"nitrogen fluoride":17400,"ethane, 1,1,1,2-tetrafluoro-, hfc-134a":1530,"methane, trifluoro-, hfc-23":14600,"methane, difluoro-, hfc-32":771,
         "ethane, pentafluoro-, hfc-125":3740,"ethane, 1,1,1-trifluoro-, hfc-143a":5810,"methane, tetrafluoro-, r-14":7380,"ethane, hexafluoro-, hfc-116":12400,"methane, dichlorodifluoro-, cfc-12":12500,
         "methane, chlorodifluoro-, hcfc-22":1960,"ethane, 1,1-difluoro-, hfc-152a":164,"carbon monoxide, fossil":0,"carbon monoxide, non-fossil":0,"carbon monoxide, from soil or biomass stock":0}
    i13=[k for k,c in enumerate(cats) if c[0]=="IPCC 2013 GWP 100a"][0]
    row=C[i13].copy()
    for i,e in enumerate(elem):
        n=norm(e[1])
        if n in AR6 and e[2]!="natural resource": row[i]=AR6[n]
        if n=="carbon dioxide, in air" and e[2]=="natural resource": row[i]=0.0
    cats.append(("IPCC 2021 GWP100 (AR6)","climate change: GWP100","kg CO2-Eq")); C.append(row); stats.append(int((row!=0).sum()))
    return cats, sp.csr_matrix(np.vstack(C)), stats
if __name__=="__main__":
    d=pickle.load(open(ENGINE/"ei312_matrices.pkl","rb"))
    cats,C,stats=build(d["elem"])
    pickle.dump(dict(cats=cats,C=C),open(ENGINE/"cf_312.pkl","wb"))
    for c,s in zip(cats,stats):
        if c[0] in ("IPCC 2013 GWP 100a","CML-IA baseline","AWARE","IPCC 2021 GWP100 (AR6)"): print(c,s)
