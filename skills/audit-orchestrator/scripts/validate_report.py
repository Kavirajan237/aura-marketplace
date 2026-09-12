#!/usr/bin/env python3
"""Strict required-field and evidence validation for AURA reports."""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
REQUIRED={'site','audited_at','summary','coverage','ai_brand_twin','findings','checked_and_clean','insufficient_evidence'}
def validate(r):
 missing=REQUIRED-set(r)
 if missing: raise ValueError('missing report keys: '+','.join(sorted(missing)))
 for f in r['findings']:
  if {'id','title','severity','evidence','suggested_action'}-set(f): raise ValueError('finding missing required fields')
  if not re.search(r'(?:/[^\s]+|#[\w.-]+)',f['evidence']) or not re.search(r'\d',f['evidence']): raise ValueError('finding evidence lacks locator or count')
 return True
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);a=p.parse_args()
 try:validate(json.loads(a.report.read_text()));print('valid',file=sys.stderr);raise SystemExit(0)
 except (ValueError,json.JSONDecodeError) as e:print('invalid: '+str(e),file=sys.stderr);raise SystemExit(1)
