#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 subprocess.run([sys.executable,'-m','unittest','discover','-s','tests'],cwd=ROOT,check=True)
 out=ROOT/'work'/'selfcheck'; subprocess.run([sys.executable,'skills/audit-orchestrator/scripts/run_audit.py','fixtures/pass4-healthy','--out',str(out)],cwd=ROOT,check=True)
 subprocess.run([sys.executable,'skills/audit-orchestrator/scripts/validate_report.py',str(out/'report.json')],cwd=ROOT,check=True)
 print('selfcheck: OK')
if __name__=='__main__':main()
