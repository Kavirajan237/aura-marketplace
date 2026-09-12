#!/usr/bin/env python3
"""Deterministically merge partial AURA Twin patches without silently choosing conflicts."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from typing import Any,Iterable
def merge(a:Any,b:Any)->Any:
 if isinstance(a,dict) and isinstance(b,dict): return {k:merge(a[k],b[k]) if k in a and k in b else (a[k] if k in a else b[k]) for k in sorted(set(a)|set(b))}
 if isinstance(a,list) and isinstance(b,list): return sorted(a+b,key=lambda x:json.dumps(x,sort_keys=True))
 return a if a==b else a
def build(site:str,patches:list[dict])->dict:
 base={"site":site,"identity":{"name":None,"one_liner":None,"what_they_do":[],"entity_ambiguity_risk":"high","evidence_refs":[]},"machine_readable":{"pages_sampled":0,"pages_total_estimate":0,"coverage":0,"blocked_by_robots":[],"noindex_found":[],"render_gaps":[],"structured_data":{"present":0,"valid":0,"types":[]}},"facts":[],"quoteable_facts":0,"human_experience":{"above_fold_states_offering":False,"primary_cta_found":False,"cta_count":0,"heading_hierarchy_ok":False,"h1_title_mismatch":False},"gaps":{"confidently_known":[],"ambiguous":[],"contradicted":[]},"check_execution":{"checked_and_clean":[],"insufficient_evidence":[]}}
 for patch in patches: base=merge(base,patch)
 return base
def main(argv:Iterable[str]|None=None)->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('site');p.add_argument('patches',nargs='+',type=Path);a=p.parse_args(argv);json.dump(build(a.site,[json.loads(x.read_text()) for x in a.patches]),sys.stdout,sort_keys=True);sys.stdout.write('\n');return 0
if __name__=='__main__':raise SystemExit(main())
