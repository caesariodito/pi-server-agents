#!/usr/bin/env python3
"""Build one self-contained technical-spec HTML page.

Usage: python3 build.py technical-spec.json technical-spec.html
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from urllib.parse import urlsplit

from render_template import render
ROOT=Path(__file__).resolve().parent.parent; ASSETS=ROOT/"assets"
STATUSES={"draft","in-review","active","done"}; OTHER="__other"
def die(m): raise ValueError(m)
def req(o,f,w):
    if f not in o or o[f] is None or o[f]=="": die(f"{w}: missing or empty '{f}'")
    return o[f]
def url(v,w):
    value=str(v); parts=urlsplit(value)
    if parts.scheme.lower() not in {"","http","https","file"} or value.startswith("//"): die(f"{w}: unsafe URL {value!r}")
    return value
def options(item,w):
    opts=item.get("options")
    if opts is None:return
    if not isinstance(opts,list) or not 2<=len(opts)<=4:die(f"{w}: options must contain 2–4 choices")
    vals=[]; rec=0
    for i,o in enumerate(opts,1):
        vals.append(str(req(o,"value",f"{w} option {i}")));req(o,"title",f"{w} option {i}");rec+=bool(o.get("recommended"))
        if vals[-1]==OTHER:die(f"{w}: reserved option value")
    if len(vals)!=len(set(vals)):die(f"{w}: duplicate option values")
    if rec not in ({0,1} if item.get("recommendation_optional") else {1}):die(f"{w}: expected exactly one recommended option")
def validate_diagram(d,w,ids):
    did=str(req(d,"id",w));kind=str(req(d,"kind",did));req(d,"title",did);req(d,"tldr",did)
    if not re.fullmatch(r"TS-[0-9]{2,}",did):die(f"{w}: invalid ID {did!r}")
    ids.append(did)
    if kind=="flowchart":
        for i,s in enumerate(req(d,"steps",did),1):req(s,"actor",f"{did} step {i}");req(s,"action",f"{did} step {i}")
    elif kind=="sequence":
        ps=req(d,"participants",did);ms=req(d,"messages",did)
        if len(ps)<2 or len(ps)!=len(set(ps)):die(f"{did}: participants must be unique")
        for i,m in enumerate(ms,1):
            a=req(m,"from",f"{did} message {i}");b=req(m,"to",f"{did} message {i}");req(m,"label",f"{did} message {i}")
            if a not in ps or b not in ps:die(f"{did}: endpoint is not a participant")
    elif kind=="data-flow":
        for i,s in enumerate(req(d,"stages",did),1):
            for f in ("name","input","process","output"):req(s,f,f"{did} stage {i}")
    else:die(f"{did}: unsupported kind {kind!r}")
def validate(s):
    top=("title","doc_type","status","version","updated","owner","reviewers","links","tagline","overview","flows","architecture","contracts","data_model","processing_rules","examples","reliability","security_privacy","verification","decisions","open_questions","change_log")
    for f in top:req(s,f,"spec")
    if s["doc_type"]!="technical-spec":die("spec: doc_type must be 'technical-spec'")
    if s["status"] not in STATUSES:die("spec: invalid status")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",str(s["updated"])):die("spec: updated must use YYYY-MM-DD")
    for k,v in s["links"].items():url(v,f"link {k}")
    o=s["overview"]
    for f in ("purpose","context","boundaries","principles"):req(o,f,"overview")
    ids=[]
    if not s["flows"]:die("flows: at least one diagram required")
    for i,d in enumerate(s["flows"],1):validate_diagram(d,f"flow {i}",ids)
    a=s["architecture"];req(a,"tldr","architecture")
    component_ids=[]
    for i,c in enumerate(req(a,"components","architecture"),1):
        cid=str(req(c,"id",f"component {i}"));component_ids.append(cid);ids.append(cid)
        if not re.fullmatch(r"C[1-9][0-9]*",cid):die(f"component {i}: invalid ID {cid!r}")
        for f in ("name","responsibility","depends_on"):req(c,f,cid)
    if len(component_ids)!=len(set(component_ids)):die("architecture: duplicate component IDs")
    for i,p in enumerate(req(a,"ports","architecture"),1):
        for f in ("name","direction","operations","implemented_by"):req(p,f,f"port {i}")
        if p["direction"] not in {"in","out"}:die(f"port {i}: direction must be in or out")
    req(a,"constraints","architecture")
    for i,c in enumerate(s["contracts"],1):
        cid=str(req(c,"id",f"contract {i}"));ids.append(cid)
        if not re.fullmatch(r"CT-[0-9]{2,}",cid):die(f"contract {i}: invalid ID")
        for f in ("title","tldr","type","source","inputs","outputs","errors"):req(c,f,cid)
        for j,x in enumerate(c["inputs"],1):
            for f in ("field","type","required","authority","rule"):
                if f not in x:die(f"{cid} input {j}: missing '{f}'")
        for j,x in enumerate(c["errors"],1):req(x,"condition",f"{cid} error {j}");req(x,"outcome",f"{cid} error {j}")
    dm=s["data_model"];req(dm,"tldr","data_model");names=[]
    for i,e in enumerate(req(dm,"entities","data_model"),1):
        name=str(req(e,"name",f"entity {i}"));names.append(name)
        for j,fld in enumerate(req(e,"fields",name),1):req(fld,"name",f"{name} field {j}");req(fld,"type",f"{name} field {j}")
    if len(names)!=len(set(names)):die("data_model: duplicate entity names")
    for i,r in enumerate(req(dm,"relationships","data_model"),1):
        a=req(r,"from",f"relationship {i}");b=req(r,"to",f"relationship {i}");req(r,"label",f"relationship {i}")
        if a not in names or b not in names:die(f"relationship {i}: unknown entity")
    req(dm,"invariants","data_model")
    for i,r in enumerate(s["processing_rules"],1):
        rid=str(req(r,"id",f"rule {i}"));ids.append(rid)
        if not re.fullmatch(r"PR-[0-9]{2,}",rid):die(f"rule {i}: invalid ID")
        for f in ("title","tldr","inputs","steps","output","failure","tests"):req(r,f,rid)
    for i,e in enumerate(s["examples"],1):
        eid=str(req(e,"id",f"example {i}"));ids.append(eid)
        if not re.fullmatch(r"EX-[0-9]{2,}",eid):die(f"example {i}: invalid ID")
        for f in ("title","tldr","input","columns","rows"):req(e,f,eid)
        for j,row in enumerate(e["rows"],1):
            if len(row)!=len(e["columns"]):die(f"{eid} row {j}: wrong cell count")
    rel=s["reliability"]
    for f in ("tldr","failure_modes","concurrency","recovery","limits"):req(rel,f,"reliability")
    sec=s["security_privacy"]
    for f in ("tldr","trust_boundaries","sensitive_data","secrets","abuse_cases"):req(sec,f,"security_privacy")
    ver=s["verification"]
    for f in ("tests","metrics","fixtures","gates"):req(ver,f,"verification")
    for i,d in enumerate(s["decisions"],1):
        did=str(req(d,"id",f"decision {i}"));ids.append(did)
        if not re.fullmatch(r"TD-[0-9]{2,}",did):die(f"decision {i}: invalid ID")
        for f in ("title","tldr","status","affects"):req(d,f,did)
        if d["status"] not in {"Proposed","Accepted"} and not re.fullmatch(r"Superseded \(by TD-[0-9]{2,}\)",d["status"]):die(f"{did}: invalid status")
        options(d,did)
    for i,q in enumerate(s["open_questions"],1):
        qid=str(req(q,"id",f"question {i}"));ids.append(qid)
        if not re.fullmatch(r"TQ[1-9][0-9]*",qid):die(f"question {i}: invalid ID")
        for f in ("question","owner","due","blocks"):req(q,f,qid)
        options(q,qid)
    if len(ids)!=len(set(ids)):die("duplicate stable IDs")
    if not s["change_log"]:die("change_log required")
def main(argv):
    if len(argv)!=3:sys.exit(__doc__)
    try:
        s=json.loads(Path(argv[1]).read_text());validate(s);out=Path(argv[2]);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(render(s, ASSETS))
    except (OSError,json.JSONDecodeError,ValueError,KeyError,TypeError) as e:sys.exit(f"build.py: {e}")
    print(f"{out} — {len(s['contracts'])} contract(s), {len(s['processing_rules'])} rule(s), {len(s['decisions'])+len(s['open_questions'])} review item(s)")
if __name__=="__main__":main(sys.argv)
