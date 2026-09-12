#!/usr/bin/env python3
"""Cluster same check/title/template findings, retaining deterministic reach evidence."""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
from typing import Iterable
def cluster(items:list[dict],pages:int)->list[dict]:
 groups={}
 for f in items:
  key=(f.get('check_id',''),f.get('title',''),re.sub(r'/[^\s,;]+','/{template}',f.get('evidence','')))
  groups.setdefault(key,[]).append(f)
 out=[]
 for key,fs in sorted(groups.items()):
  f=dict(sorted(fs,key=lambda x:x.get('evidence',''))[0]);f['affected']={'pages':len(fs),'reach_share':round(len(fs)/max(1,pages),3),'template':key[0]};out.append(f)
 return out
def main(argv:Iterable[str]|None=None)->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('findings',type=Path);p.add_argument('--pages',type=int,required=True);a=p.parse_args(argv);json.dump(cluster(json.loads(a.findings.read_text()),a.pages),sys.stdout,sort_keys=True);sys.stdout.write('\n');return 0
if __name__=='__main__':raise SystemExit(main())
