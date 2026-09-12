#!/usr/bin/env python3
"""Canonicalize visible claims and report evidence-backed site-internal conflicts."""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
from typing import Iterable

CLAIMS={"founded":r"\b(?:founded|established|since)\s+(?:in\s+)?((?:18|19|20)\d{2})\b","employees":r"\b(\d[\d,]*)\s+(?:employees|people)\b","price":r"(?:price\s*[:=]?\s*)?([$€£]\s*\d[\d,.]*)"}
def visible(html:str)->str:return re.sub(r"\s+"," ",re.sub(r"<(?:script|style)\b.*?</(?:script|style)>","",html,flags=re.I|re.S))
def canonical(key:str,value:str)->str:
    value=value.lower().replace(",","").replace(" ","")
    return value if key=="price" else value
def pages(root:Path)->dict[str,str]:return {"/"+p.relative_to(root).as_posix():p.read_text(encoding="utf-8") for p in sorted(root.rglob("*.html"))}
def analyse(root:Path,extended:bool=False)->dict[str,object]:
    source=pages(root); groups={}; findings=[]; facts=[]
    for url,html in source.items():
        text=visible(html)
        for key,pattern in CLAIMS.items():
            for m in re.finditer(pattern,text,re.I):groups.setdefault(key,[]).append((canonical(key,m.group(1)),url,m.group(0)))
    for key,items in sorted(groups.items()):
        values=sorted({x[0] for x in items}); primary=values[0]; urls=sorted({x[1] for x in items if x[0]==primary}); conflict=[{"url":u,"value":v} for v,u,_ in items if v!=primary]
        facts.append({"key":key,"value":primary,"source_urls":urls,"consistent":not conflict,"contradicted_by":sorted(conflict,key=lambda x:(x['url'],x['value'])),"quoteable":key in {"founded","price"},"check_id":"TF-001"})
        if conflict: findings.append({"check_id":"TF-001","title":f"Conflicting {key} claims","severity":"high","chain_link":"trust","impact_area":"discoverability","evidence":f"{len(values)}/{len(items)} canonical {key} values across {len(set(x[1] for x in items))} pages; sample: {items[0][1]}={items[0][0]}","suggested_action":"Choose one authoritative statement and remove or redirect conflicting copies."})
        elif len(urls)==1: findings.append({"check_id":"TF-003","title":f"{key} is a single-point-of-truth fact","severity":"low","chain_link":"verify","impact_area":"discoverability","evidence":f"1/{len(source)} sampled pages state {key}; source: {urls[0]}","suggested_action":"Maintain a canonical facts page and reference it from relevant pages."})
    numeric=[]
    for url,html in source.items():
        for phrase in re.findall(r"\b\d[\d,]*(?:%|\s+(?:customers|users|teams))\b",visible(html),re.I):
            if not re.search(r"(?:source|study|report|according to)",visible(html),re.I):numeric.append((url,phrase))
    if numeric: findings.append({"check_id":"TF-004","title":"Numeric claims lack a stated source","severity":"low","chain_link":"trust","impact_area":"discoverability","evidence":f"{len(numeric)}/{len(source)} sampled pages contain unsourced numeric claims; sample: {numeric[0][0]}={numeric[0][1]}","suggested_action":"State a first-party source, methodology, or dated reference next to material numeric claims."})
    insuff=[] if extended else [{"check":"TF-005 cross-web corroboration","reason":"--extended not enabled; default audit is self-contained and makes no external requests"}]
    patch={"facts":facts,"quoteable_facts":sum(x["quoteable"] for x in facts),"gaps":{"confidently_known":[],"ambiguous":[],"contradicted":sorted(x["key"] for x in facts if not x["consistent"])},"check_execution":{"checked_and_clean":[],"insufficient_evidence":insuff}}
    return {"twin_patch":patch,"findings":sorted(findings,key=lambda x:(x["check_id"],x["title"]))}
def main(argv:Iterable[str]|None=None)->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("html_dir",type=Path);p.add_argument("--extended",action="store_true");a=p.parse_args(argv)
 if not a.html_dir.is_dir():print("usage error: html_dir must be directory",file=sys.stderr);return 2
 json.dump(analyse(a.html_dir,a.extended),sys.stdout,sort_keys=True);sys.stdout.write("\n");return 0
if __name__=="__main__":raise SystemExit(main())
