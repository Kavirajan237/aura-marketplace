#!/usr/bin/env python3
"""Evidence-derived AURA priority formula."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from typing import Iterable
CATALOGUE=json.loads((Path(__file__).resolve().parents[1]/'references'/'check-catalogue.json').read_text())
def rank(items:list[dict])->list[dict]:
 out=[]
 for f in items:
  f=dict(f); spec=CATALOGUE[f['check_id']]; evidence=f.get('evidence','').lower(); reach=float(f.get('affected',{}).get('reach_share',0)); confidence=1.0 if (f['check_id'] in {'CG-003','TF-001'} or '.rendered.html' in evidence or 'present after render' in evidence) else (.6 if ('not confirmed' in evidence or 'renderer unavailable' in evidence) else .4); impact=min(5,int(spec['impact_default'])+int(reach>.5)); fix=min(5,int(spec['fixability_default'])+int(f.get('affected',{}).get('pages',0)>1)); f['priority_points']=round(impact*confidence*reach*fix);f['priority_factors']={'impact':impact,'confidence':confidence,'reach_share':reach,'fixability':fix};
  if confidence<.6:f['severity']='informational'
  out.append(f)
 return sorted(out,key=lambda x:(-x['priority_points'],x.get('check_id',''),x.get('evidence','')))
def main(argv:Iterable[str]|None=None)->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('findings',type=Path);a=p.parse_args(argv);json.dump(rank(json.loads(a.findings.read_text())),sys.stdout,sort_keys=True);sys.stdout.write('\n');return 0
if __name__=='__main__':raise SystemExit(main())
