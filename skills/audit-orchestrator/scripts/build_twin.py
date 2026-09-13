#!/usr/bin/env python3
"""Deterministically merge partial AURA Twin patches and retain leaf conflicts."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from typing import Any,Iterable
def merge(a:Any,b:Any,path:str="",conflicts:list[dict]|None=None,left:str="previous",right:str="patch")->Any:
 if isinstance(a,dict) and isinstance(b,dict): return {k:merge(a[k],b[k],f"{path}.{k}" if path else k,conflicts,left,right) if k in a and k in b else (a[k] if k in a else b[k]) for k in sorted(set(a)|set(b))}
 if isinstance(a,list) and isinstance(b,list): return sorted(a+b,key=lambda x:json.dumps(x,sort_keys=True))
 if a in (None,"",0,False): return b
 if a!=b and a not in (None,"",[],{}) and b not in (None,"",[],{}) and conflicts is not None: conflicts.append({"path":path,"values":[{"skill":left,"value":a},{"skill":right,"value":b}]})
 return a
def build(site:str,patches:list[dict])->dict:
 base={"site":site,"identity":{"name":None,"one_liner":None,"what_they_do":[],"entity_ambiguity_risk":"low","evidence_refs":[]},"machine_readable":{"pages_sampled":0,"pages_total_estimate":0,"coverage":0,"blocked_by_robots":[],"noindex_found":[],"render_gaps":[],"structured_data":{"present":0,"valid":0,"types":[]}},"facts":[],"quoteable_facts":0,"human_experience":{"above_fold_states_offering":False,"primary_cta_found":False,"cta_count":0,"heading_hierarchy_ok":False,"h1_title_mismatch":False},"gaps":{"confidently_known":[],"ambiguous":[],"contradicted":[]},"check_execution":{"checked_and_clean":[],"insufficient_evidence":[]},"merge_conflicts":[]}
 for index,patch in enumerate(patches): base=merge(base,patch,conflicts=base["merge_conflicts"],right=f"patch-{index+1}")
 base["merge_conflicts"]=sorted(base["merge_conflicts"],key=lambda x:(x["path"],json.dumps(x,sort_keys=True)))
 return base
def main(argv:Iterable[str]|None=None)->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('site');p.add_argument('patches',nargs='+',type=Path);a=p.parse_args(argv);json.dump(build(a.site,[json.loads(x.read_text()) for x in a.patches]),sys.stdout,sort_keys=True);sys.stdout.write('\n');return 0
if __name__=='__main__':raise SystemExit(main())
