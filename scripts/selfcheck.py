#!/usr/bin/env python3
"""Package-level deterministic checks for AURA."""
from __future__ import annotations
import json,re,shutil,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def check(name,fn):
 try: fn();print(f'[PASS] {name}');return True
 except Exception as exc:print(f'[FAIL] {name}: {exc}');return False
def manifest():
 data=json.loads((ROOT/'marketplace.json').read_text());skills=data['skills'];assert sum(bool(x.get('entrypoint')) for x in skills)==1;assert all((ROOT/x['path']).is_dir() for x in skills);assert {x['id'] for x in skills}=={p.name for p in (ROOT/'skills').iterdir() if p.is_dir()}
def frontmatter():
 for folder in (ROOT/'skills').iterdir():
  text=(folder/'SKILL.md').read_text();head=text.split('---',2)[1];assert re.search(r'^name:\s*'+re.escape(folder.name)+r'\s*$',head,re.M);assert re.search(r'^description:\s*\S',head,re.M);assert re.search(r'^license:\s*\S',head,re.M);assert 'allowed-tools:' in head
def tests():subprocess.run([sys.executable,'-m','unittest','discover','-s','tests'],cwd=ROOT,check=True)
def determinism():
 a=ROOT/'work'/'self-a';b=ROOT/'work'/'self-b';cmd=[sys.executable,'skills/audit-orchestrator/scripts/run_audit.py','fixtures/healthy-ssg','--out'];subprocess.run(cmd+[str(a)],cwd=ROOT,check=True);subprocess.run(cmd+[str(b)],cwd=ROOT,check=True);x=json.loads((a/'report.json').read_text());y=json.loads((b/'report.json').read_text());[z.pop('audited_at',None) for z in (x,y)];[z['coverage'].pop('elapsed_ms',None) for z in (x,y)];assert x==y
def readonly():
 text='\n'.join(p.read_text(errors='ignore') for p in list((ROOT/'skills').rglob('*.py'))+list((ROOT/'scripts').glob('*.py')));assert not re.search(r'method=["\'](?:POST|PUT|PATCH|DELETE)|urlopen\([^\n]*data=',text)
def archive():
 out=ROOT/'work'/'aura-marketplace.zip';
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for p in ROOT.rglob('*'):
   if p.is_file() and not any(x in p.parts for x in ('work','.git','__pycache__')):z.write(p,p.relative_to(ROOT))
 assert out.stat().st_size<50*1024*1024
def main():
 results=[check('marketplace manifest',manifest),check('skill frontmatter',frontmatter),check('test suite',tests),check('determinism',determinism),check('read-only scan',readonly),check('package zip',archive)]
 if not all(results):raise SystemExit(1)
 print('selfcheck: OK')
if __name__=='__main__':main()
