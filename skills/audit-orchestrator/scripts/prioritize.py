#!/usr/bin/env python3
"""Evidence-derived AURA priority formula."""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
from typing import Iterable
IMPACT={'critical':5,'high':4,'medium':3,'low':2,'informational':1}; FIX={'CG-002':5,'TF-001':4,'EG-001':4}
def rank(items:list[dict])->list[dict]:
 out=[]
 for f in items:
  evidence=f.get('evidence',''); count=bool(re.search(r'\d',evidence)) and bool(re.search(r'/(?:[\w.-]+)',evidence)); confidence=1.0 if count else 0.0; reach=f.get('affected',{}).get('reach_share',0); fix=FIX.get(f.get('check_id'),3); points=round(IMPACT.get(f.get('severity'),1)*confidence*reach*fix)
  f=dict(f);f['priority_points']=points;f['priority_factors']={'impact':IMPACT.get(f.get('severity'),1),'confidence':confidence,'reach_share':reach,'fixability':fix};out.append(f)
 return sorted(out,key=lambda x:(-x['priority_points'],x.get('check_id',''),x.get('evidence','')))
def main(argv:Iterable[str]|None=None)->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('findings',type=Path);a=p.parse_args(argv);json.dump(rank(json.loads(a.findings.read_text())),sys.stdout,sort_keys=True);sys.stdout.write('\n');return 0
if __name__=='__main__':raise SystemExit(main())
