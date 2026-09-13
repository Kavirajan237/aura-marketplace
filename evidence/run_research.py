#!/usr/bin/env python3
"""Run reproducible public-site AURA samples and write a site-by-check matrix."""
from __future__ import annotations
import argparse,csv,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; ENTRY=ROOT/'skills'/'audit-orchestrator'/'scripts'/'run_audit.py'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('urls',type=Path,help='One public URL per line');p.add_argument('--out',type=Path,default=ROOT/'work'/'research');p.add_argument('--max-pages',type=int,default=3);a=p.parse_args();urls=[x.strip() for x in a.urls.read_text().splitlines() if x.strip() and not x.startswith('#')];rows=[]
 for index,url in enumerate(urls,1):
  out=a.out/f'site-{index:02d}';existing=out/'report.json';run=subprocess.CompletedProcess([],0) if existing.exists() else subprocess.run([sys.executable,str(ENTRY),url,'--out',str(out),'--max-pages',str(a.max_pages),'--timeout','10'],cwd=ROOT,capture_output=True,text=True)
  row={'site':url,'exit_code':run.returncode,'pages':0,'checks':''}
  if run.returncode==0 and (out/'report.json').exists():
   report=json.loads((out/'report.json').read_text());row['pages']=report['coverage']['pages_sampled'];row['checks']=';'.join(sorted({f['check_id'] for f in report['findings']}))
  rows.append(row);print(json.dumps(row,sort_keys=True))
 a.out.mkdir(parents=True,exist_ok=True)
 with (a.out/'matrix.csv').open('w',newline='',encoding='utf-8') as handle:
  writer=csv.DictWriter(handle,fieldnames=['site','exit_code','pages','checks']);writer.writeheader();writer.writerows(rows)
 return 0
if __name__=='__main__':raise SystemExit(main())
