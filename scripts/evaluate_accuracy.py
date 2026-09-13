#!/usr/bin/env python3
"""Measure AURA against labelled fixtures; never claim an unsupported accuracy rate."""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixtures',nargs='+',default=['healthy-ssg','broken-spa','conflicting-facts']);a=p.parse_args();expected={'healthy-ssg':set(),'broken-spa':{'CG-002'},'conflicting-facts':{'TF-001'}};tp=fp=fn=0
 for name in a.fixtures:
  out=ROOT/'work'/'evaluation'/name;subprocess.run([sys.executable,'skills/audit-orchestrator/scripts/run_audit.py',f'fixtures/{name}','--out',str(out)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL);actual={x['check_id'] for x in json.loads((out/'report.json').read_text())['findings']};wanted=expected.get(name,set());tp+=len(actual&wanted);fp+=len(actual-wanted);fn+=len(wanted-actual);print(f'{name}: expected={sorted(wanted)} actual={sorted(actual)}')
 precision=tp/(tp+fp) if tp+fp else 1.0;recall=tp/(tp+fn) if tp+fn else 1.0;print(json.dumps({'fixtures':len(a.fixtures),'true_positive':tp,'false_positive':fp,'false_negative':fn,'precision':round(precision,3),'recall':round(recall,3)},sort_keys=True))
if __name__=='__main__':main()
