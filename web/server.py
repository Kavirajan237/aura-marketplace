#!/usr/bin/env python3
"""Local AURA Atlas dashboard; runs bounded read-only audit jobs."""
from __future__ import annotations
import argparse,json,subprocess,sys,threading,uuid
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1];WEB=Path(__file__).resolve().parent;RUNS=ROOT/'work'/'web-runs';JOBS={};LOCK=threading.Lock()
def reply(handler,status,payload):
 data=json.dumps(payload).encode('utf-8');handler.send_response(status);handler.send_header('Content-Type','application/json');handler.send_header('Content-Length',str(len(data)));handler.end_headers();handler.wfile.write(data)
def execute(job_id,url,pages):
 out=RUNS/job_id;cmd=[sys.executable,str(ROOT/'skills'/'audit-orchestrator'/'scripts'/'run_audit.py'),url,'--out',str(out),'--max-pages',str(pages),'--budget-seconds','240']
 with LOCK:JOBS[job_id]['state']='running';JOBS[job_id]['stage']='Reading the public surface…'
 result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);report_file=out/'report.json'
 with LOCK:JOBS[job_id].update({'state':'complete' if result.returncode==0 and report_file.exists() else 'failed','stage':'Complete' if result.returncode==0 else 'Audit stopped','stderr':result.stderr[-4000:],'report':json.loads(report_file.read_text()) if report_file.exists() else None})
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(WEB),**kwargs)
 def log_message(self,*args):pass
 def do_GET(self):
  if not self.path.startswith('/api/jobs/'):return super().do_GET()
  parts=self.path.split('/');job_id=parts[3] if len(parts)>3 else ''
  with LOCK:job=JOBS.get(job_id)
  if len(parts)>4 and parts[4] in {'report.json','report.md'}:
   file=RUNS/job_id/parts[4]
   if not job or not file.exists():return reply(self,404,{'error':'Report unavailable'})
   content=file.read_bytes();self.send_response(200);self.send_header('Content-Type','application/json' if file.suffix=='.json' else 'text/markdown');self.send_header('Content-Disposition',f'attachment; filename={file.name}');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content);return
  return reply(self,200,job) if job else reply(self,404,{'error':'Unknown audit'})
 def do_POST(self):
  if self.path!='/api/audits':return reply(self,404,{'error':'Not found'})
  try:
   body=json.loads(self.rfile.read(min(int(self.headers.get('Content-Length','0')),32768)));url=str(body.get('url','')).strip();pages=int(body.get('maxPages',10));parsed=urlparse(url)
   if parsed.scheme not in {'http','https'} or not parsed.netloc:raise ValueError('Enter a full public http(s) URL.')
   if not 1<=pages<=25:raise ValueError('Choose between 1 and 25 pages.')
  except (ValueError,json.JSONDecodeError) as exc:return reply(self,400,{'error':str(exc)})
  job_id=uuid.uuid4().hex[:12];RUNS.mkdir(parents=True,exist_ok=True)
  with LOCK:JOBS[job_id]={'id':job_id,'state':'queued','stage':'Preparing audit…','site':url,'report':None}
  threading.Thread(target=execute,args=(job_id,url,pages),daemon=True).start();reply(self,202,{'id':job_id})
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=8000);args=parser.parse_args();print(f'AURA Atlas running at http://127.0.0.1:{args.port}');ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
if __name__=='__main__':main()
