#!/usr/bin/env python3
"""Schema and evidence validation for AURA reports."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
SCHEMA=Path(__file__).resolve().parents[1]/'references'/'report-schema.json'
REQUIRED={'site','audited_at','summary','coverage','ai_brand_twin','findings','checked_and_clean','insufficient_evidence','report_version','limitations'}
FINDING={'id','check_id','title','severity','evidence_status','chain_link','evidence','mechanism','why_it_matters','affected','suggested_action'}
def validate(report):
 missing=REQUIRED-set(report)
 if missing: raise ValueError('report: missing '+', '.join(sorted(missing)))
 if report['report_version']!='2.0': raise ValueError('report.report_version: expected 2.0')
 for index,finding in enumerate(report['findings']):
  missing=FINDING-set(finding)
  if missing: raise ValueError(f'findings[{index}]: missing '+', '.join(sorted(missing)))
  if finding['severity'] not in {'critical','high','medium','low','informational'}: raise ValueError(f"findings[{index}].severity: invalid enum")
  if finding['evidence_status'] not in {'confirmed','requires_confirmation'}: raise ValueError(f"findings[{index}].evidence_status: invalid enum")
  if finding['suggested_action'].get('owner') not in {'content','dev','seo','design'}: raise ValueError(f"findings[{index}].suggested_action.owner: invalid enum")
  if not re.search(r'(?:https?://|/[\w.-]+|#[\w.-]+)',finding['evidence']) or not re.search(r'\d',finding['evidence']): raise ValueError(f'findings[{index}].evidence: missing locator or count')
  if len(finding['suggested_action'].get('how',[]))<2: raise ValueError(f'findings[{index}].suggested_action.how: requires two steps')
 try:
  import jsonschema
  jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text())).validate(report)
 except ImportError: pass
 return True
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);a=p.parse_args()
 try:validate(json.loads(a.report.read_text(encoding='utf-8')));print('valid')
 except (ValueError,json.JSONDecodeError) as exc:print('invalid: '+str(exc));raise SystemExit(1)
